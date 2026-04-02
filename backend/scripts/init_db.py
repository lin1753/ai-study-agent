# init_db.py
from sqlalchemy import text
from core.db import engine, Base
import models.database as models

def init_db():
    print("Dropping old tables...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS explanation_branches CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS knowledge_blocks CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS conversation_spaces CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS file_records CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS main_threads CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS branch_threads CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS messages CASCADE"))
        conn.commit()
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
