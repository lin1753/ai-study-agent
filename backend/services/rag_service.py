from sqlalchemy.orm import Session
from models import KnowledgeBlock
from llm_service import get_llm_service

def search_related_blocks(db: Session, space_id: str, query: str, top_k: int = 5, user_config: dict = None) -> list[KnowledgeBlock]:
    """
    RAG 核心检索：将用户的自然语言 query 转为向量，然后使用 pgvector 进行余弦相似度检索
    """
    llm = get_llm_service(user_config)
    query_vector = llm.get_embedding(query)
    
    if not query_vector:
        return []

    # 使用 sqlalchemy 与 pgvector 的余弦距离运算符 (<=>) ，距离越小越相似
    # 只检索当前 space_id 下的知识块
    results = db.query(KnowledgeBlock).filter(
        KnowledgeBlock.space_id == space_id,
        KnowledgeBlock.embedding != None
    ).order_by(
        KnowledgeBlock.embedding.cosine_distance(query_vector)
    ).limit(top_k).all()
    
    return results
