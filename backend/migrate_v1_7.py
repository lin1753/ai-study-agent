from sqlalchemy import create_engine, text

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:251399@localhost/ai_study_agent"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

def migrate():
    print("Connecting to database...")
    with engine.connect() as conn:
        print("Checking for missing columns in main_threads...")
        # Use simple ALTER TABLE statements; simple 'ADD COLUMN' will fail if current exists, so we check first or ignore errors.
        # But 'ADD COLUMN IF NOT EXISTS' is supported in PG 9.6+.
        try:
            conn.execute(text("ALTER TABLE main_threads ADD COLUMN IF NOT EXISTS roadmap_json TEXT DEFAULT '[]'"))
            conn.execute(text("ALTER TABLE main_threads ADD COLUMN IF NOT EXISTS mastery_data TEXT DEFAULT '{}'"))
            conn.commit()
            print("Migration successful: Added roadmap_json and mastery_data columns.")
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
