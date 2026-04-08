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
            update_progress("检测到图像文件，正在调用多模态Model/OCR识别图像提取...")
            with open(file_path, 'rb') as f:
                img_bytes = f.read()
            res = llm.ocr_image(img_bytes)
            if res:
                texts.append(res)
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
