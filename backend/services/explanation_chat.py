# explanation_chat.py
from sqlalchemy.orm import Session
from models.database import ExplanationBranch, BranchMessage
import requests
import json
import re
from datetime import datetime

from teaching_styles import get_style_prompt
from services.teaching_judge import judge_answers

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3-vl:4b"


# =========================
# 教学层级顺序
# =========================
CONFUSION_ORDER = [
    "symbol",
    "quantifier",
    "dependency",
    "proof_logic",
]


def extract_json(text: str):
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else None


def generate_answer(prompt_base: str, style: str) -> str:
    style_hint = get_style_prompt(style)

    prompt = f"""
{prompt_base}

【教学风格要求】
{style_hint}

⚠️ 只输出回答正文，不要 JSON。
"""

    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4},
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def branch_chat(
    db: Session,
    branch_id: str,
    user_input: str,
):
    # 1️⃣ 查分支
    branch = db.query(ExplanationBranch).filter_by(id=branch_id).first()
    if not branch:
        raise ValueError("Branch not found")

    # 2️⃣ 历史
    messages = (
        db.query(BranchMessage)
        .filter_by(branch_id=branch_id)
        .order_by(BranchMessage.id)
        .all()
    )

    history_text = ""
    for m in messages:
        role = "User" if m.role == "user" else "Assistant"
        history_text += f"{role}: {m.content}\n"

    turn_count = len(messages) // 2 + 1

    # 3️⃣ Prompt 基础体
    prompt_base = f"""
你是一位非常有教学经验的老师，
正在【第 {turn_count} 轮】与同一位学生讨论同一个知识点。

【当前教学层级】
{branch.confusion_type}

【分支解释】
{branch.content}

【历史对话】
{history_text}

【学生新问题】
{user_input}
"""

    # 4️⃣ 生成两个教学风格回答（A / B）
    answer_a = generate_answer(prompt_base, style="explain")
    answer_b = generate_answer(prompt_base, style="guide")

    # 5️⃣ 教学裁判（A3.1）
    judge = judge_answers(
        question=user_input,
        goal=branch.confusion_type,
        a=answer_a,
        b=answer_b,
    )

    if judge.get("better") == "B":
        final_answer = answer_b
        chosen = "guide"
    else:
        final_answer = answer_a
        chosen = "explain"

    # 6️⃣ 入库
    db.add(BranchMessage(
        branch_id=branch_id,
        role="user",
        content=user_input,
    ))
    db.add(BranchMessage(
        branch_id=branch_id,
        role="assistant",
        content=final_answer,
    ))

    db.commit()

    return {
        "confusion_type": branch.confusion_type,
        "teaching_style": chosen,
        "answer": final_answer,
    }
