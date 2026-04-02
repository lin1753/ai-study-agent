import sqlalchemy
import json

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:251399@localhost/ai_study_agent"
engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URL)

def check():
    with engine.connect() as conn:
        res = conn.execute(sqlalchemy.text("SELECT space_id, roadmap_json FROM main_threads"))
        rows = res.fetchall()
        for row in rows:
            roadmap = json.loads(row[1] or "[]")
            print(f"Space ID: {row[0]}, Roadmap Chapters: {len(roadmap)}")
            if roadmap:
                print(f"First chapter title: {roadmap[0].get('title', 'N/A')}")
            print("-" * 20)

if __name__ == "__main__":
    check()
