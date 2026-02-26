from models import ExplanationBranch, KnowledgeBlockORM, new_id
from embedding import embed_text
from llm import generate_explanation
from store import explanation_branches
from db import SessionLocal

def create_explanation_branch(kb_id: str, branch_type: str) -> ExplanationBranch:
    db = SessionLocal()
    try:
        # 获取 KB
        kb = db.query(KnowledgeBlockORM).filter(KnowledgeBlockORM.id == kb_id).first()
        if not kb:
            raise Exception("KnowledgeBlock not found")

        # 使用 LLM 生成解释内容
        content = generate_explanation(kb.text, branch_type)
        embedding = embed_text(content)  # 获取分支内容的 embedding

        # 创建分支并保存
        branch = ExplanationBranch(
            id=new_id(),
            kb_id=kb.id,
            type=branch_type,
            content=content,
            embedding=embedding
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)

        return branch
    finally:
        db.close()
