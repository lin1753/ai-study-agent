import json
from typing import List
import logging

logger = logging.getLogger(__name__)

def merge_roadmap_chunks(chunked_roadmap: List[dict]) -> List[dict]:
    """Smart Merge: Combine fragmented chapters by title."""
    merged_dict = {}
    chapter_order = [] # Keep track of order

    for chapter in chunked_roadmap:
        if not isinstance(chapter, dict):
            logger.warning(f"[SmartMerge] Skipping non-dict chapter: {chapter}")
            continue

        raw_title = chapter.get('title', '未命名章节')
        if not isinstance(raw_title, str):
            raw_title = str(raw_title)
        raw_title = raw_title.strip()
        
        if raw_title not in merged_dict:
            # Create new entry
            new_id = f"chap_{len(chapter_order) + 1}"
            merged_dict[raw_title] = {
                "id": new_id,
                "title": raw_title,
                "summary": str(chapter.get('summary', '')),
                "points": [],
                "examples": []
            }
            chapter_order.append(raw_title)
        
        target = merged_dict[raw_title]
        
        # Merge Points (Re-indexing IDs)
        current_points_count = len(target['points'])
        for idx, point in enumerate(chapter.get('points', [])):
            if isinstance(point, str):
                point = {"name": "核心概念", "content": point, "importance": 5, "type": "concept"}
            
            if not isinstance(point, dict):
                logger.warning(f"[SmartMerge] Skipping invalid point format: {point}")
                continue

            try:
                point['id'] = f"{target['id']}_p{current_points_count + len(target['points']) + 1}"
                target['points'].append(point)
            except Exception as e:
                logger.error(f"[SmartMerge] Error re-indexing point: {e}")
            
        # Merge Examples
        examples = chapter.get('examples', [])
        if isinstance(examples, list):
            target['examples'].extend(examples)
        
        # Merge Summary
        new_summary = chapter.get('summary', '')
        if isinstance(new_summary, str) and len(new_summary) > len(target['summary']):
            target['summary'] = new_summary

    return [merged_dict[title] for title in chapter_order]

def process_upload_task(space_id: str, record_id: str, file_path: str, ftype: str):
    """
    后台任务: 调度 Agent 进行知识抽取与出题。
    """
    from core.db import SessionLocal
    from models.database import ConversationSpace, FileRecord, KnowledgeBlock, MainThread
    from utils.parsing import parse_file
    from core.llm_factory import get_llm_service
    from services.agent_controller import StudyAgent
    import uuid

    db = SessionLocal()
    try:
        space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
        if not space:
            return "Space not found"

        import json
        user_config = json.loads(space.config_data or "{}")

        texts = parse_file(file_path, ftype, user_config=user_config)
        if not texts:
            logger.warning(f"No text extracted from file: {file_path}")

        blocks = []
        llm = get_llm_service(user_config)
        full_text_for_summary = ""

        # Step 1: Save pure texts into KnowledgeBlocks
        for idx, text in enumerate(texts):
            vec = llm.get_embedding(text) if text.strip() else None
            block = KnowledgeBlock(
                space_id=space_id,
                source_file_id=record_id,
                raw_text=text,
                chunk_index=str(idx),
                embedding=vec
            )
            db.add(block)
            blocks.append(block)
            full_text_for_summary += text + "\n"

        db.commit()

        main_thread = db.query(MainThread).filter(MainThread.space_id == space_id).first()
        if main_thread and llm.check_connection():
            # Step 2: Use Agent Toolkit to handle parsing and exam generation
            from services.upload_agent_tools import define_upload_tools
            agent = StudyAgent(llm, max_steps=4)
            tools = define_upload_tools(space_id, record_id, texts, llm, user_config, db)
            for t in tools:
                agent.register_tool(t)

            task_instruction = (
                "你的任务是处理用户上传的新文档材料。请按顺序执行以下两个操作：\n"
                "1. 调用 DocumentParser 工具，提取文档的知识点结构。\n"
                "2. 拿到 DocumentParser 返回的大纲JSON文本后，将其作为 `roadmap_json` 参数，调用 ExamGenerator 工具生成考题。\n"
                "请将生成的考题JSON数组和知识点大纲整理好汇报给我。"
            )
            
            logger.info("[Agent] Starting background ReAct loop for uploaded file...")
            agent_result = agent.run(task_instruction=task_instruction)
            logger.info(f"[Agent] Loop finished. Result snippet: {agent_result[:200]}")
            
            # Since the tools already do the heavy lifting internally, we can either extract the result from agent context,
            # or we can pass a callback in the tool to save into DB.
            # Fallback procedural approach, if agent didn't return exactly what we want:
            logger.info("[Agent] Fallback procedural state saving just in case LLM routing dropped standard outputs.")
            
            # Execute Tool 1
            doc_result = tools[0].run()
            res_json = json.loads(doc_result)
            chapters = res_json.get("extracted_chapters", [])
            
            # Saving roadmap
            old_roadmap = json.loads(main_thread.roadmap_json or "[]")
            new_roadmap = old_roadmap + chapters
            main_thread.roadmap_json = json.dumps(new_roadmap)
            
            # Execute Tool 2
            exam_result_str = tools[1].run(roadmap_json=json.dumps(chapters))
            exam_json = json.loads(exam_result_str)
            quiz = exam_json.get("exam_quiz", [])
            
            # Save the generated quiz to the DB (We will append it to summary for now since ExamRecord model is missing)
            if quiz:
                quiz_str = json.dumps(quiz, ensure_ascii=False, indent=2)
                logger.info(f"Generated {len(quiz)} exam questions for new document. Appending to summary.")
                main_thread.current_summary = (main_thread.current_summary or "") + "\n\n== 出题工具生成的课后自测题 ==\n" + quiz_str

            # Summary
            file_summary = llm.generate_summary(full_text_for_summary[:8000])
            current_summary = main_thread.current_summary or ""
            main_thread.current_summary = f"{current_summary}\n\n== 新增资料 ==\n{file_summary}"

            db.commit()

        record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
        if record:
            record.processed = True
            db.commit()

        return {"status": "success", "blocks_count": len(blocks), "file_id": record_id}

    except Exception as e:
        logger.error(f"Error in background task process_upload_task: {e}")
        record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
        if record:
            record.processed = False
            db.commit()
        raise e
    finally:
        db.close()

