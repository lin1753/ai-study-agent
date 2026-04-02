import re
import os

def patch_llm_service():
    path = "backend/llm_service.py"
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    
    # 1. 为 BaseLLMService 增加抽象方法
    if "def generate_raw(" not in code:
        code = code.replace(
            "    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:\n        pass",
            "    def generate_exam_quiz(self, roadmap_json: str, user_config: dict) -> list:\n        pass\n\n    @abstractmethod\n    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:\n        pass"
        )
    
    # 2. 为 OllamaService 添加具体实现
    if "def generate_raw(" not in code.split("class CloudAPIService(")[0]:
        ollama_method = """    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        try:
            import requests
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Error in generate_raw: {e}")
            return f"Error: {str(e)}"
"""
        code = code.replace(
            "    def generate_summary(self, text: str) -> str:",
            ollama_method + "\n    def generate_summary(self, text: str) -> str:"
        )

    # 3. 为 CloudAPIService 添加具体实现（兼容 OpenAI 消息结构）
    parts = code.split("class CloudAPIService(")
    if len(parts) > 1 and "def generate_raw(" not in parts[1]:
        cloud_method = """    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": temperature
        }
        try:
            import requests
            response = requests.post(url, json=payload, headers=self.headers, timeout=180)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in generate_raw (Cloud API): {e}")
            return f"Error: {str(e)}"
"""
        code = code.replace(
            "    def _generate_cloud(self, system_prompt: str, user_prompt: str) -> str:",
            cloud_method + "\n    def _generate_cloud(self, system_prompt: str, user_prompt: str) -> str:"
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("Patched backend/llm_service.py")

def patch_agent_controller():
    path = "backend/agent_controller.py"
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # 4. 去除老旧的手写逻辑，统一使用新的 self.llm.generate_raw
    replacement = '''    def _call_llm_raw(self, prompt: str) -> str:
        try:
            result = self.llm.generate_raw(prompt, temperature=0.3)
            if result.startswith("Error:"):
                return f"Final Answer: {result}"
            return result
        except Exception as e:
            return f"Final Answer: LLM completion failed: {e}"'''

    # Regex matches from def _call_llm_raw to the end of the return statement
    # The current one looks like:
    # def _call_llm_raw(self, prompt: str) -> str:
    #   ...
    #   return "Final Answer: Error."
    
    # Simple replace by splitting the file since the method is at the end or cleanly definable
    if "import requests" in code and "self.llm.model_name" in code:
        # Find the start of the method
        start_idx = code.find("    def _call_llm_raw(self, prompt: str) -> str:")
        if start_idx != -1:
            end_idx = code.find("    def run(", start_idx) 
            # Check if there is another method. If not, it goes to end.
            if end_idx == -1:
                code = code[:start_idx] + replacement + "\n"
            else:
                code = code[:start_idx] + replacement + "\n\n" + code[end_idx:]
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            print("Patched backend/agent_controller.py")
        else:
            print("Method _call_llm_raw not found in backend/agent_controller.py")
    else:
        print("agent_controller.py seems to be already patched or structurally diverged. Skipping.")

if __name__ == "__main__":
    patch_llm_service()
    patch_agent_controller()
    print("All patching operations completed.")
