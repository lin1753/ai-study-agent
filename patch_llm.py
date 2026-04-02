import re

with open('backend/llm_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update BaseLLMService
content = content.replace(
    "def analyze_page(self, page_text: str, previous_chapter: str, user_config: dict = None) -> dict:\n        pass",
    "def analyze_page(self, page_text: str, previous_chapter: str, user_config: dict = None) -> dict:\n        pass\n\n    @abstractmethod\n    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:\n        pass"
)

# 2. Add generate_exam_quiz to OllamaService before analyze_subject_domain
ollama_exam_code = '''
    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        url = f"{self.base_url}/api/generate"
        weight_context = self._build_config_context(user_config) if user_config else "默认出题均衡"
        
        prompt = f"""你是一个资深的考卷出题专家。请根据以下大纲知识点和用户指定的【考试题型权重】，出一套高还原度的课后测验题。
        
【用户考试题型偏好】:
{weight_context}

【知识点大纲】:
{roadmap_json}

请严格输出合法的 JSON 数组结构，每个元素是一道独立的题目，格式如下：
[
    {{ "type": "choice|blank|short|calc", "question": "题目内容", "options": ["选项A", "选项B"], "answer": "答案/解析" }}
]
注意：如果不是选择题，options字段填空数组[]。绝对禁止随附任何markdown标志或者多余文本。
"""
        payload = { "model": self.model, "prompt": prompt, "stream": False, "format": "json" }
        logger.debug("Generating independent exam quiz based on parsed knowledge...")
        try:
            import requests, json
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                res_text = response.json().get("response", "")
                try:
                    return json.loads(res_text)
                except:
                    import re
                    match = re.search(r'\[.*\]', res_text, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"[Ollama] Failed to generate exam quiz: {e}")
        return []
'''
content = content.replace(
    "def analyze_subject_domain(self, text: str) -> dict:",
    ollama_exam_code.strip() + "\n\n    def analyze_subject_domain(self, text: str) -> dict:"
)

# 3. Add to CloudAPIService
cloud_exam_code = '''
    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        import openai, json
        from openai import OpenAI
        
        api_key = "sk-xxxxxxxx" # fallback if needed, ideally we use initialized client
        if user_config and user_config.get("cloud_api_key"):
            api_key = user_config.get("cloud_api_key")
            
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        weight_context = self._build_config_context(user_config) if user_config else "默认出题均衡"
        
        prompt = f"""你是一个资深的考卷出题专家。请根据以下大纲知识点和用户指定的【考试题型权重】，出一套高还原度的课后测验题。
        
【用户考试题型偏好】:
{weight_context}

【知识点大纲】:
{roadmap_json}

请严格输出合法的 JSON 数组结构，每个元素是一道独立的题目，格式如下：
[
    {{ "type": "choice|blank|short|calc", "question": "题目内容", "options": ["选项A", "选项B"], "answer": "答案/解析" }}
]
注意：如果不是选择题，options字段填空数组[]。绝对禁止随附任何markdown标志或者多余文本。
"""
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                response_format={
                    "type": "json_object"
                }
            )
            res_text = response.choices[0].message.content
            return json.loads(res_text).get("quiz", json.loads(res_text)) 
        except Exception as e:
            logger.error(f"[CloudAPI] generate_exam_quiz error: {e}")
            return []
'''

content = content.replace(
    "def analyze_subject_domain(self, text: str, user_config: dict = None) -> dict:",
    cloud_exam_code.strip() + "\n\n    def analyze_subject_domain(self, text: str, user_config: dict = None) -> dict:"
)


with open('backend/llm_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success.')
