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
            # Step 2: Use procedural toolkit to handle layout parsing and roadmap extraction
            # According to Phase 5: Removed ExamGenerator and Agent ReAct loop from the main thread
            from services.upload_agent_tools import define_upload_tools
            tools = define_upload_tools(space_id, record_id, texts, llm, user_config, db)
            
            logger.info("[Process] Starting procedural extraction loop for uploaded file...")
            
            # Execute Tool 1 (DocumentParser) directly
            doc_result = tools[0].run()
            res_json = json.loads(doc_result)
            chapters = res_json.get("extracted_chapters", [])
            
            # Saving roadmap
            old_roadmap = json.loads(main_thread.roadmap_json or "[]")
            new_roadmap = old_roadmap + chapters
            main_thread.roadmap_json = json.dumps(new_roadmap)

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



def process_supplementary_upload_task(space_id: str, record_id: str, file_path: str, ftype: str):
    """处理碎片化补充水印上传(如长截图/网页)的后台任务：包含多模态OCR，写入 RAG 数据库"""
    import logging
    import json
    from core.db import SessionLocal
    from core.factories import get_llm_service
    from models.database import ConversationSpace, FileRecord, KnowledgeBlock
    from utils.parsing import parse_file
    from rq import get_current_job

    logger = logging.getLogger(__name__)
    job = get_current_job()

    def update_progress(msg: str):
        logger.info(f"[Worker Progress] {msg}")
        if job:
            job.meta['progress_message'] = msg
            job.save_meta()

    db = SessionLocal()
    try:
        update_progress("正在获取空间数据...")
        space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
        if not space:
            raise Exception(f"Space {space_id} not found.")
        
        user_config = json.loads(space.config_data or "{}")
        llm = get_llm_service(user_config)

        update_progress("正在提取文件文本...")
        texts = []
        if ftype in ['pdf', 'ppt', 'pptx']:
            texts = parse_file(file_path, ftype, user_config=user_config)
        elif ftype in ['jpg', 'jpeg', 'png', 'webp']:
            update_progress("检测到图像文件，正在调用本地 RapidOCR 提取文本...")
            try:
                from rapidocr_onnxruntime import RapidOCR
                ocr_engine = RapidOCR()
                res, _ = ocr_engine(file_path)
                if res:
                    extracted_text = "\n".join([line[1] for line in res if line[1]])
                    if extracted_text.strip():
                        texts.append(extracted_text)
                        logger.info(f"RapidOCR successful: {len(extracted_text)} chars extracted from {file_path}")
            except Exception as ocr_err:
                logger.error(f"RapidOCR failed on {file_path}: {ocr_err}")
        else:
            # Try text files as fallback
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                texts.append(f.read())

        if not texts:
            logger.warning(f"No text extracted from file: {file_path}")
            return {"status": "empty", "blocks_count": 0}

        update_progress("文本提取完毕，正在写入 RAG 数据库...")
        blocks = []
        for idx, text in enumerate(texts):
            vec = llm.get_embedding(text) if text.strip() else None
            block = KnowledgeBlock(
                space_id=space_id,
                source_file_id=record_id,
                raw_text=text,
                chunk_index=f"supp_{idx}",
                embedding=vec
            )
            db.add(block)
            blocks.append(block)

        db.commit()
        update_progress("碎片合并上传完毕！")
        
        record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
        if record:
            record.processed = True
            db.commit()
            
        return {"status": "success", "blocks_count": len(blocks), "file_id": record_id}

    except Exception as e:
        logger.error(f"Error in supplementary upload task: {e}")
        record = db.query(FileRecord).filter(FileRecord.id == record_id).first()
        if record:
            record.processed = False
            db.commit()
        raise e
    finally:
        db.close()
        import os
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as err:
            logger.error(f"Failed to clean up: {err}")
