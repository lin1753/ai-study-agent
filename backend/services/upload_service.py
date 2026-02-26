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
    后台任务: 负责提取文本并调用 LLM 分析，更新知识库和大纲。
    """
    from db import SessionLocal
    from models import ConversationSpace, FileRecord, KnowledgeBlock, MainThread
    from parsing import parse_file
    from llm_service import get_llm_service
    
    db = SessionLocal()
    try:
        space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
        if not space:
            return "Space not found"
            
        user_config = json.loads(space.config_data or "{}")
        
        texts = parse_file(file_path, ftype, user_config=user_config)
        if not texts:
            logger.warning(f"No text extracted from file: {file_path}")
            
        blocks = []
        llm = get_llm_service(user_config)
        full_text_for_summary = ""
        
        for idx, text in enumerate(texts):
            # 获取文本的向量化表示 (Embedding)
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
            chapters = []
            current_chapter_title = ""
            current_chapter = None
            
            for i, page_text in enumerate(texts):
                if not page_text.strip():
                    continue
                try:
                    result = llm.analyze_page(page_text, current_chapter_title, user_config)
                    new_title = result.get("chapter_title", "").strip() or current_chapter_title or "核心提取内容"
                    
                    if not current_chapter or new_title != current_chapter_title:
                        current_chapter_title = new_title
                        current_chapter = {
                            "id": f"chap_doc{record_id}_c{len(chapters)}",
                            "title": current_chapter_title,
                            "summary": "",
                            "points": [],
                            "examples": []
                        }
                        chapters.append(current_chapter)
                    
                    for pt in result.get("points", []):
                        pt_copy = dict(pt)
                        pt_copy["id"] = f"{current_chapter['id']}_p{len(current_chapter['points'])}"
                        current_chapter["points"].append(pt_copy)
                        
                    for ex in result.get("examples", []):
                        current_chapter["examples"].append(ex)
                        
                except Exception as e:
                    logger.error(f"[ERROR] Failed to analyze page {i+1}: {e}")

            old_roadmap = json.loads(main_thread.roadmap_json or "[]")
            new_roadmap = old_roadmap + chapters
            main_thread.roadmap_json = json.dumps(new_roadmap)
            
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
            record.processed = False # keep false or set to a failed state if schema is updated
            db.commit()
        raise e
    finally:
        db.close()
