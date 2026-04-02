from sqlalchemy import create_engine, text

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:251399@localhost/ai_study_agent"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def check_summary():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, space_id, current_summary FROM main_threads"))
        rows = result.fetchall()
        for row in rows:
            print(f"Thread ID: {row[0]}")
            print(f"Space ID: {row[1]}")
            print(f"Summary Start: {row[2][:100]}...")
            print("-" * 20)

if __name__ == "__main__":
    check_summary()
