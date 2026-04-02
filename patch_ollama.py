import os

path = "backend/llm_service.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

parts = code.split("class CloudAPIService(")

ollama_part = parts[0]
cloud_part = parts[1]

if "    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:" in ollama_part:
    # check if it appears more than once (once for base class)
    if ollama_part.count("def generate_raw") < 2:
        ollama_method = '''    def generate_raw(self, prompt: str, temperature: float = 0.3) -> str:
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
            import logging
            logging.getLogger(__name__).error(f"Error in generate_raw: {e}")
            return f"Error: {str(e)}"
'''
        ollama_part = ollama_part.replace(
            "    def generate_summary(self, text: str) -> str:",
            ollama_method + "\n    def generate_summary(self, text: str) -> str:"
        )
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(ollama_part + "class CloudAPIService(" + cloud_part)
        print("Patched OllamaService!")
    else:
        print("OllamaService already patched")
