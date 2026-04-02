import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3-vl:4b"

def generate_explanation(text: str, branch_type: str) -> str:
    prompt = f"""
你是一个数学学习助手。
请针对以下知识点，给出【{branch_type}】类型的解释：

知识点：
{text}

要求：
- 中文
- 清晰、严谨
- 不要闲聊
"""

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    resp.raise_for_status()
    return resp.json()["response"]
