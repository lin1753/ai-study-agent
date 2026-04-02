import os
from sqlalchemy.orm import Session
from core.db import SessionLocal
from models.database import ConversationSpace, FileRecord, KnowledgeBlock
from core.llm_factory import get_llm_service
from services.rag_service import search_related_blocks
import traceback

def test_rag_pipeline():
    print("=== 🚀 RAG 向量存取验证测试 ===")
    
    # 1. 验证 Ollama Embedding 服务
    print("\n[1/3] 测试本地 Ollama 生成向量...")
    llm = get_llm_service()
    
    test_text_1 = "苹果是一种常见的水果，富含维生素C，吃起来很脆甜。"
    test_text_2 = "广义相对论是爱因斯坦提出的一种物理学理论，解释了引力是时空弯曲的结果。"
    
    try:
        vec1 = llm.get_embedding(test_text_1)
        vec2 = llm.get_embedding(test_text_2)
        if not vec1 or len(vec1) != 768:
            print("❌ Embedding 生成失败！请确保本地 Ollama 已运行，并且已经拉取了模型：`ollama run nomic-embed-text`")
            return
        print(f"✅ 成功生成向量！向量维度: {len(vec1)}。")
    except Exception as e:
        print(f"❌ 请求 Ollama 发生异常: {e}")
        return

    # 2. 验证存入数据库
    print("\n[2/3] 测试数据存入 PostgreSQL (需准备好 pgvector)...")
    db = SessionLocal()
    space = None
    try:
        # 创建临时空间
        space = ConversationSpace(name="RAG_Test_Space")
        db.add(space)
        db.commit()
        
        file_rec = FileRecord(space_id=space.id, filename="dummy.txt", filepath="dummy/path", file_type="txt")
        db.add(file_rec)
        db.commit()
        
        # 存入带有向量的 Block
        block1 = KnowledgeBlock(
            space_id=space.id, source_file_id=file_rec.id, chunk_index="1",
            raw_text=test_text_1, embedding=vec1
        )
        block2 = KnowledgeBlock(
            space_id=space.id, source_file_id=file_rec.id, chunk_index="2",
            raw_text=test_text_2, embedding=vec2
        )
        db.add(block1)
        db.add(block2)
        db.commit()
        
        print("✅ 知识块和高维向量成功写入 PostgreSQL 数据库！")

        # 3. 验证相似度检索
        print("\n[3/3] 测试语义相似度检索...")
        query_text = "什么能吃，还能补充维他命？"
        print(f"用户查询: {query_text}")
        
        results = search_related_blocks(db=db, space_id=space.id, query=query_text, top_k=1)
        
        if results and len(results) > 0:
            print(f"✅ RAG 命中！")
            print(f"最匹配的原文: {results[0].raw_text}")
            if results[0].raw_text == test_text_1:
                print("🎯 结论：测试完美通过，RAG 管道畅通！")
            else:
                print("⚠️ 命中结果似乎不是预期的段落。")
        else:
            print("❌ 没有找到匹配文档。")
            
    except Exception as e:
        print("\n❌ 数据库写入/检索遭遇致命错误。")
        print("错误堆栈：")
        traceback.print_exc()
    finally:
        # 无论成功失败，测试结束后清理测试数据
        if space:
            try:
                db.delete(space)
                db.commit()
                print("\n[清理] 测试数据已删除。")
            except Exception:
                db.rollback()
        db.close()

if __name__ == "__main__":
    test_rag_pipeline()
