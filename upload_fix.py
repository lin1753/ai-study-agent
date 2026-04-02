import re

file_path = "backend/services/upload_agent_tools.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_parse_document = '''    def parse_document(**kwargs):
        logger.info(f"[Tool] parse_document called.")
        
        merged_text = "\\n\\n".join([t for t in texts if t.strip()])
        if not merged_text:
            return json.dumps({"status": "success", "extracted_chapters": []})
            
        try:
            domain_analysis = llm.analyze_subject_domain(merged_text)
            chapters = llm.generate_roadmap(merged_text, user_config=None, domain_analysis=domain_analysis)
            
            for i, chapter in enumerate(chapters):
                chapter["id"] = f"chap_doc{record_id}_c{i}"
                if "points" not in chapter:
                    chapter["points"] = []
                for j, pt in enumerate(chapter["points"]):
                    pt["id"] = f"{chapter['id']}_p{j}"
                if "examples" not in chapter:
                    chapter["examples"] = []
                    
            return json.dumps({"status": "success", "extracted_chapters": chapters})
        except Exception as e:
            logger.error(f"[Tool][ERROR] Failed to parse document: {e}")
            return json.dumps({"status": "error", "message": str(e)})'''

# We need to replace the old parse_document definition.
# It starts at `    def parse_document(**kwargs):`
# and ends before `    def generate_exam(**kwargs):`

pattern = re.compile(r'    def parse_document\(\*\*kwargs\):.*?return json\.dumps\(\{"status": "success", "extracted_chapters": chapters\}\)', re.DOTALL)

new_content, count = pattern.subn(new_parse_document, content)

if count > 0:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully fixed `backend/services/upload_agent_tools.py`!")
else:
    print("Could not find the target code to replace.")
