from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import logging

from db import get_db
from models import ConversationSpace, KnowledgeBlock, BranchThread, Message, RoleType, ThreadStatus, FileRecord
from schemas.chat import BranchCreate
from llm_service import get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/threads", tags=["Threads"])

@router.post("/branch")
def create_branch_thread(payload: BranchCreate, db: Session = Depends(get_db)):
    """从知识块或 Roadmap Point 创建新的分支对话（或恢复旧对话）"""
    
    space = db.query(ConversationSpace).filter(ConversationSpace.id == payload.space_id).first()
    if not space:
        raise HTTPException(404, "Space not found")
        
    user_config = json.loads(space.config_data or "{}")
    llm = get_llm_service(user_config)
    
    if not llm.check_connection():
        raise HTTPException(500, "LLM 服务未响应。如使用本地模型，请确保 Ollama 已启动 (11434)。")

    if payload.source_block_id:
        existing_thread = db.query(BranchThread).filter(BranchThread.source_block_id == payload.source_block_id).first()
        if existing_thread:
            return {"thread_id": existing_thread.id, "initial_message": "已恢复历史对话"}
            
    elif payload.context and payload.space_id:
        existing_block = db.query(KnowledgeBlock).filter(
            KnowledgeBlock.space_id == payload.space_id,
            KnowledgeBlock.raw_text == payload.context,
            KnowledgeBlock.chunk_index == "synthetic_roadmap_point"
        ).first()
        
        if existing_block:
            existing_thread = db.query(BranchThread).filter(BranchThread.source_block_id == existing_block.id).first()
            if existing_thread:
                return {"thread_id": existing_thread.id, "initial_message": "已恢复历史对话"}

    block = None
    if payload.source_block_id:
        block = db.query(KnowledgeBlock).filter(KnowledgeBlock.id == payload.source_block_id).first()
        if not block:
            raise HTTPException(404, "Block not found")
    elif payload.context and payload.space_id:
        file_record = db.query(FileRecord).filter(FileRecord.space_id == payload.space_id).first()
        if not file_record:
            raise HTTPException(400, "当前科目下找不到任何文件支撑分支对话，请先上传文件。")

        vec = llm.get_embedding(payload.context) if payload.context.strip() else None

        block = KnowledgeBlock(
            space_id=payload.space_id,
            source_file_id=file_record.id,
            raw_text=payload.context,
            chunk_index="synthetic_roadmap_point",
            embedding=vec
        )
        db.add(block)
        db.commit()
        db.refresh(block)
    else:
        raise HTTPException(400, "必须提供 source_block_id 或 context+space_id")
    
    intro_context = block.raw_text
    thread_title = payload.title if payload.title else (intro_context[:20] + "...")
    
    thread = BranchThread(
        space_id=block.space_id,
        source_block_id=block.id,
        title=thread_title,
        status=ThreadStatus.EXPLORING
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    try:
        summary = llm.generate_summary(intro_context)
    except Exception as e:
        logger.error(f"[Branch Creation] summary generation failed: {e}")
        summary = "我已准备好为你解答。"

    msg = Message(
        branch_thread_id=thread.id,
        role=RoleType.ASSISTANT,
        content=f"同学你好！我是你的专属私教。现在我们来专门攻克**【{thread_title}】**。\n\n它的核心内容如下：\n> {summary}\n\n为了让我更好地了解你的基础，在我们深入之前，你能用自己的话简单谈谈对它的初步理解，或者指出哪里最让你困惑吗？"
    )
    db.add(msg)
    db.commit()

    return {"thread_id": thread.id, "initial_message": msg.content}

@router.get("/{thread_id}/history")
def get_chat_history(thread_id: str, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(
        (Message.branch_thread_id == thread_id) | (Message.main_thread_id == thread_id)
    ).order_by(Message.created_at).all()
    
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in msgs
    ]
