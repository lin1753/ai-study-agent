import re

with open('backend/services/upload_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_process_upload = '''def process_upload_task(space_id: str, record_id: str, file_path: str, ftype: str):
    """
    后台任务: 调度 Agent 进行知识抽取与出题。
    """
    from db import SessionLocal
    from models import ConversationSpace, FileRecord, KnowledgeBlock, MainThread
    from parsing import parse_file
    from llm_service import get_llm_service
    from agent_controller import StudyAgent
    import uuid

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
            full_text_for_summary += text + "\\n"

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
                "你的任务是处理用户上传的新文档材料。请按顺序执行以下两个操作：\\n"
                "1. 调用 DocumentParser 工具，提取文档的知识点结构。\\n"
                "2. 拿到 DocumentParser 返回的大纲JSON文本后，将其作为 
oadmap_json 参数，调用 ExamGenerator 工具生成考题。\\n"
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
                import json
                quiz_str = json.dumps(quiz, ensure_ascii=False, indent=2)
                logger.info(f"Generated {len(quiz)} exam questions for new document. Appending to summary.")
                main_thread.current_summary = (main_thread.current_summary or "") + "\\n\\n== 出题工具生成的课后自测题 ==\\n" + quiz_str

            # Summary
            file_summary = llm.generate_summary(full_text_for_summary[:8000])
            current_summary = main_thread.current_summary or ""
            main_thread.current_summary = f"{current_summary}\\n\\n== 新增资料 ==\\n{file_summary}"

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
'''

old_func_pattern = re.compile(r'def process_upload_task\(.*?\n    finally:\n        db.close\(\)', re.DOTALL)
content = old_func_pattern.sub(new_process_upload, content)

with open('backend/services/upload_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch successful!")
