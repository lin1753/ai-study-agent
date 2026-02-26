# teaching_judge.py
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3-vl:4b"


def judge_answers(question, goal, a, b):
    prompt = f"""
你是一位资深教学教研员。

【学生问题】
{question}

【本轮教学目标】
{goal}

【回答 A】
{a}

【回答 B】
{b}

请判断哪一个回答：
- 更贴合教学目标
- 更像真人老师
- 没有提前讲更高层级内容

只输出 JSON：
{{
  "better": "A 或 B",
  "reason": "一句话原因"
}}
"""

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=120,
    )
    resp.raise_for_status()

    return json.loads(resp.json()["response"])
