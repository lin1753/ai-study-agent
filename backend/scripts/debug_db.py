from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:251399@localhost/ai_study_agent"

def debug_db():
    print("Connecting to DB...")
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        print("Session created.")
        
        res = db.execute(text("SELECT 1"))
        print(f"Query Result: {res.scalar()}")
        
        db.close()
        print("Success!")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    debug_db()
