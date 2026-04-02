from sqlalchemy import text
from core.db import engine

def migrate_to_vector():
    try:
        with engine.connect() as conn:
            print("1. 正在尝试激活 pgvector 插件...")
            # 必须作为超级用户或由具有相应权限的用户执行
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            print("2. 正在修改 knowledge_blocks 表的 embedding 字段为 VECTOR(768)...")
            # 通过 USING 子句完成从 Text (如果之前存的是 JSON 数组格式) 到 Vector 的转换
            conn.execute(text("""
                ALTER TABLE knowledge_blocks 
                ALTER COLUMN embedding TYPE vector(768) 
                USING embedding::vector;
            """))
            
            conn.commit()
            print("✅ 数据库向量化改造完成！字段已被设置为 pgvector 专属向量。")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        print("请确保 PostgreSQL 服务端已经安装了 pgvector 插件。")

if __name__ == "__main__":
    migrate_to_vector()
