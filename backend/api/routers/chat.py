from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import logging
import re
import uuid

from core.db import get_db, SessionLocal
from models.database import ConversationSpace, MainThread, BranchThread, Message, RoleType
from models.schemas.chat import ChatRequest
from core.llm_factory import get_llm_service
from services.rag_service import search_related_blocks
from prompts.constants import MAIN_THREAD_SYSTEM_PROMPT, SOCRATES_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

def save_main_chat_and_mutate(thread_id: str, full_response: str):
    try:
        db_new = SessionLocal()
        ai_msg = Message(
            main_thread_id=thread_id,
            role=RoleType.ASSISTANT,
            content=full_response
        )
        db_new.add(ai_msg)
        
        actions = re.findall(r'<ACTION>(.*?)</ACTION>', full_response)
        if actions:
            main_thread_db = db_new.query(MainThread).filter(MainThread.id == thread_id).first()
            if main_thread_db:
                roadmap = json.loads(main_thread_db.roadmap_json or "[]")
                roadmap_modified = False
                
                for action_str in actions:
                    parts = [p.strip() for p in action_str.split('|')]
                    cmd = parts[0]
                    if cmd == "ADD_POINT" and len(parts) >= 4:
                        chap_id, p_name, p_content = parts[1], parts[2], parts[3]
                        for chap in roadmap:
                            if str(chap.get("id")) == chap_id:
                                chap.setdefault("points", []).append({
                                    "id": f"p_mut_{uuid.uuid4().hex[:6]}",
                                    "name": p_name,
                                    "content": p_content,
                                    "importance": 5,
                                    "type": "concept"
                                })
                                roadmap_modified = True
                    elif cmd == "DEL_POINT" and len(parts) >= 2:
                        pt_id = parts[1]
                        for chap in roadmap:
                            if "points" in chap:
                                chap["points"] = [p for p in chap["points"] if str(p.get("id")) != pt_id]
                                roadmap_modified = True
                    elif cmd == "MOD_TITLE" and len(parts) >= 3:
                        chap_id, new_title = parts[1], parts[2]
                        for chap in roadmap:
                            if str(chap.get("id")) == chap_id:
                                chap["title"] = new_title
                                roadmap_modified = True
                                
                if roadmap_modified:
                    main_thread_db.roadmap_json = json.dumps(roadmap)
                    logger.info(f"Successfully applied {len(actions)} mutations to roadmap.")
        
        db_new.commit()
    except Exception as e:
        logger.error(f"Error saving Main AI response or mutating roadmap: {e}")
    finally:
        db_new.close()

def save_branch_chat(thread_id: str, full_response: str):
    try:
        db_new = SessionLocal()
        ai_msg = Message(
            branch_thread_id=thread_id,
            role=RoleType.ASSISTANT,
            content=full_response
        )
        db_new.add(ai_msg)
        db_new.commit()
    except Exception as e:
        logger.error(f"Error saving branch AI response: {e}")
    finally:
        db_new.close()

@router.post("/main")
def chat_main_stream(payload: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """主线全局对话接口"""
    user_msg = Message(
        main_thread_id=payload.thread_id,
        role=RoleType.USER,
        content=payload.content
    )
    db.add(user_msg)
    db.commit()

    main_thread = db.query(MainThread).filter(MainThread.id == payload.thread_id).first()
    if not main_thread:
        raise HTTPException(404, "Main thread not found")
    
    roadmap_data = main_thread.roadmap_json or "[]"
    history = db.query(Message).filter(Message.main_thread_id == payload.thread_id).order_by(Message.created_at).all()
    
    system_prompt = MAIN_THREAD_SYSTEM_PROMPT.format(roadmap_data=roadmap_data)

    messages_for_llm = [{"role": "system", "content": system_prompt}]
    for m in history:
        messages_for_llm.append({"role": m.role.value, "content": m.content})

    space = db.query(ConversationSpace).filter(ConversationSpace.id == main_thread.space_id).first()
    user_config = json.loads(space.config_data or "{}") if space else {}

    # === RAG 检索介入 ===
    # 针对用户的最新问题，在知识库中检索出最相关的片段，来辅助主线回答
    rag_context = ""
    try:
        if space:
            related_blocks = search_related_blocks(db, space.id, payload.content, top_k=3, user_config=user_config)
            if related_blocks:
                rag_context = "【检索到的参考资料】\n" + "\n---\n".join(b.raw_text for b in related_blocks) + "\n\n"
    except Exception as e:
        logger.error(f"RAG Retrieval failed in main chat: {e}")
        
    system_prompt = MAIN_THREAD_SYSTEM_PROMPT.format(roadmap_data=roadmap_data)
    if rag_context:
        system_prompt += f"\n\n请参考以下检索内容的具体细节来回答用户问题（如果回答不需要则忽略）：\n{rag_context}"

    messages_for_llm = [{"role": "system", "content": system_prompt}]
    for m in history:
        messages_for_llm.append({"role": m.role.value, "content": m.content})

    def iter_response():
        llm = get_llm_service(user_config)
        full_response = ""
        for chunk in llm.chat_stream(messages_for_llm):
            full_response += chunk
            yield chunk
        
        # 安全地将其交由BackgroundTasks去落盘，不仅避免占坑还在生成完毕后立即响应
        background_tasks.add_task(save_main_chat_and_mutate, payload.thread_id, full_response)

    return StreamingResponse(iter_response(), media_type="text/event-stream")

@router.post("/stream")
def chat_stream(payload: ChatRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """流式对话接口"""
    user_msg = Message(
        branch_thread_id=payload.thread_id,
        role=RoleType.USER,
        content=payload.content
    )
    db.add(user_msg)
    db.commit()

    history = db.query(Message).filter(Message.branch_thread_id == payload.thread_id).order_by(Message.created_at).all()
    
    thread = db.query(BranchThread).filter(BranchThread.id == payload.thread_id).first()
    block_text = ""
    user_config = {}
    if thread and thread.source_block:
        block_text = f"关联知识点内容：\n{thread.source_block.raw_text}\n\n"
        space = db.query(ConversationSpace).filter(ConversationSpace.id == thread.space_id).first()
        if space:
            user_config = json.loads(space.config_data or "{}")

    system_prompt = SOCRATES_SYSTEM_PROMPT.format(block_text=block_text)
    
    messages_for_llm = [{"role": "system", "content": system_prompt}]
    for m in history:
        messages_for_llm.append({"role": m.role.value, "content": m.content})

    def iter_response():
        llm = get_llm_service(user_config)
        full_response = ""
        for chunk in llm.chat_stream(messages_for_llm):
            full_response += chunk
            yield chunk
        
        background_tasks.add_task(save_branch_chat, payload.thread_id, full_response)

    return StreamingResponse(iter_response(), media_type="text/event-stream")
