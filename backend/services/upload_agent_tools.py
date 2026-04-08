import json
import logging

from services.agent_controller import StudyAgent, Tool

logger = logging.getLogger(__name__)

def define_upload_tools(space_id, record_id, texts, llm, user_config, db):
    # Here we define the specialized tools
    
    def parse_document(**kwargs):
        logger.info(f"[Tool] parse_document called.")
        
        valid_texts = [t for t in texts if t.strip()]
        if not valid_texts:
            return json.dumps({"status": "success", "extracted_chapters": []})
            
        try:
            sample_text = "\n\n".join(valid_texts[:3])
            domain_analysis = llm.analyze_subject_domain(sample_text)
            
            all_chapters = []
            chunk_size = 3
            for start_idx in range(0, len(valid_texts), chunk_size):
                chunk_texts = valid_texts[start_idx : start_idx + chunk_size]
                chunk_merged = "\n\n".join(chunk_texts)
                logger.info(f"[Tool] Parsing chunk {start_idx}-{start_idx+len(chunk_texts)-1}...")
                
                chunk_chapters = llm.generate_roadmap(
                    chunk_merged, 
                    user_config=None, 
                    domain_analysis=domain_analysis
                )
                all_chapters.extend(chunk_chapters)
            
            for i, chapter in enumerate(all_chapters):
                chapter["id"] = f"chap_doc{record_id}_c{i}"
                if "points" not in chapter:
                    chapter["points"] = []
                for j, pt in enumerate(chapter["points"]):
                    pt["id"] = f"{chapter['id']}_p{j}"
                if "examples" not in chapter:
                    chapter["examples"] = []
                    
            return json.dumps({"status": "success", "extracted_chapters": all_chapters})
        except Exception as e:
            logger.error(f"[Tool][ERROR] Failed to parse document: {e}")
            return json.dumps({"status": "error", "message": str(e)})
        
    def generate_exam(**kwargs):
        # Extracts chapters from kwargs if possible, or we could just use the class state
        roadmap_json = kwargs.get("roadmap_json", "[]")
        logger.info(f"[Tool] generate_exam called. roadmap length: {len(roadmap_json)}")
        quiz = llm.generate_exam_quiz(roadmap_json, user_config)
        return json.dumps({"status": "success", "exam_quiz": quiz})

    t1 = Tool(
        name="DocumentParser", 
        description="按页解析原始文档的纯粹知识点大纲。不需要参数。执行完毕后会返回包含提取出来的章节(chapters)的JSON字符串。",
        func=parse_document
    )
    
    return [t1]
