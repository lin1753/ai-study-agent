import re

with open("backend/llm_service.py", "r", encoding="utf-8") as f:
    text = f.read()

new_methods = r'''    def check_connection(self) -> bool:
        """检查云端 API 连通性"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }
        try:
            import requests
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[Cloud] Connection check failed: {e}")
            return False

    def analyze_page(self, page_text: str, previous_chapter: str, user_config: dict = None) -> dict:
        """云端原生页面分析"""
        import json
        system_prompt = """你是一个阅读解析引擎专家。请分析给定页面提取结构化JSON数据。
严格返回JSON结构，例如：
{
    "chapter_title": "检测到的章节或继承的章节",
    "points": [
        {"name": "概念名称", "content": "详细的一句话解释", "importance": 3}
    ],
    "examples": [
        {"question": "例题题目", "solution": "详细解答"}
    ]
}
"""
        user_prompt = f"Previous chapter context: {previous_chapter}\n\nPage text to analyze:\n{page_text}"
        try:
            res_text = self._generate_cloud(system_prompt, user_prompt)
            import re
            res_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            match = re.search(r'(\{.*\})', res_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            return {"chapter_title": previous_chapter or "未分类", "points": [], "examples": []}
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[Cloud] analyze_page failed: {e}")
            return {"chapter_title": previous_chapter or "未分类", "points": [], "examples": []}

    def generate_summary(self, text: str) -> str:
        return self._generate_cloud("你是一个专业的助手。请总结以下内容的知识点，提取核心概念，保持简洁。", text)

    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:
        """云端导出测试题"""
        weight_context = self._build_config_context(user_config) if user_config else "默认出题均衡"
        system_prompt = "你是一个资深的考卷出题专家。请根据提供的知识大纲和用户考试题型偏好出题。必须返回JSON数组格式。"
        
        user_prompt = f"""【用户考试题型偏好】:
{weight_context}

【知识点大纲】:
{roadmap_json}

请严格输出合法的 JSON 数组结构：
[
    {{ "type": "choice|blank|short|calc", "question": "题目内容", "options": ["选项A", "选项B"], "answer": "答案/解析" }}
]"""
        try:
            res_text = self._generate_cloud(system_prompt, user_prompt)
            import re
            res_text = re.sub(r'<think>.*?</think>', '', res_text, flags=re.DOTALL)
            match = re.search(r'(\[.*\])', res_text, re.DOTALL)
            if match:
                res_text = match.group(1)
            import json
            return json.loads(res_text)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[Cloud] generate_exam_quiz failed: {e}")
            return []
'''

# Regex to safely replace from `def generate_summary` to the end of the file.
new_text = re.sub(r'    def generate_summary\(self, text: str\) -> str:.*', new_methods.strip('\n') + '\n', text, flags=re.DOTALL)

if new_text != text:
    with open("backend/llm_service.py", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("SUCCESS")
else:
    print("MATCH FAILED")
