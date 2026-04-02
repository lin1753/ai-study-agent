import os
import shutil

os.chdir(os.path.dirname(os.path.abspath(__file__)))

dirs = [
    "api/routers",
    "core",
    "services",
    "models/schemas",
    "worker",
    "utils",
    "scripts",
    "constants"
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

files_to_move = {
    "db.py": "core/db.py",
    "redis_client.py": "core/redis_client.py",
    "llm.py": "core/llm_legacy.py",
    "llm_service.py": "core/llm_factory.py",
    "models.py": "models/database.py",
    "schemas/chat.py": "models/schemas/chat.py",
    "schemas/roadmap.py": "models/schemas/roadmap.py",
    "schemas/space.py": "models/schemas/space.py",
    "routers/chat.py": "api/routers/chat.py",
    "routers/files.py": "api/routers/files.py",
    "routers/spaces.py": "api/routers/spaces.py",
    "routers/threads.py": "api/routers/threads.py",
    "worker.py": "worker/rq_worker.py",
    "run_worker.py": "worker/run_worker.py",
    "get_jobs.py": "worker/get_jobs.py",
    "parsing.py": "utils/parsing.py",
    "embedding.py": "utils/embedding.py",
    "agent_controller.py": "services/agent_controller.py",
    "explanation.py": "services/explanation.py",
    "explanation_chat.py": "services/explanation_chat.py",
    "teaching_judge.py": "services/teaching_judge.py",
    "teaching_styles.py": "constants/teaching_styles.py",
    "teaching_strategies.py": "constants/teaching_strategies.py",
    "teaching_transitions.py": "constants/teaching_transitions.py",
    "teaching_goals.py": "constants/teaching_goals.py",
    "store.py": "services/store.py",
    "init_db.py": "scripts/init_db.py",
    "migrate_v1_7.py": "scripts/migrate_v1_7.py",
    "migrate_to_pgvector.py": "scripts/migrate_to_pgvector.py",
    "check_db_pg.py": "scripts/check_db_pg.py",
    "check_db_v1_7.py": "scripts/check_db_v1_7.py",
    "debug_db.py": "scripts/debug_db.py",
    "debug_manage.py": "scripts/debug_manage.py",
    "debug_upload.py": "scripts/debug_upload.py",
    "sanitize_json_test.py": "scripts/sanitize_json_test.py",
    "test_rag.py": "scripts/test_rag.py",
    "test_summary_api.py": "scripts/test_summary_api.py",
    "test_vision.py": "scripts/test_vision.py",
    "confusion_guard.py": "services/confusion_guard.py",
    "confusion_rules.py": "services/confusion_rules.py"
}

for src, dst in files_to_move.items():
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)

def fix_imports_in_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    replacements = {
        "import db\\n": "from core import db\\n",
        "from db import": "from core.db import",
        "import redis_client\\n": "from core import redis_client\\n",
        "from redis_client import": "from core.redis_client import",
        "import models\\n": "import models.database as models\\n",
        "from models import": "from models.database import",
        "import llm\\n": "from core import llm_legacy as llm\\n",
        "from llm import": "from core.llm_legacy import",
        "import llm_service\\n": "from core import llm_factory as llm_service\\n",
        "from llm_service import": "from core.llm_factory import",
        "from routers import": "from api.routers import",
        "from schemas import": "from models.schemas import",
        "import schemas\\n": "from models import schemas\\n",
        "from schemas.": "from models.schemas.",
        "from parsing import": "from utils.parsing import",
        "from embedding import": "from utils.embedding import",
        "from agent_controller import": "from services.agent_controller import",
        "from explanation import": "from services.explanation import",
        "from explanation_chat import": "from services.explanation_chat import",
        "from teaching_judge import": "from services.teaching_judge import",
        "from store import": "from services.store import",
        "import confusion_guard\\n": "from services import confusion_guard\\n",
        "import confusion_rules\\n": "from services import confusion_rules\\n",
        "from worker import": "from worker.rq_worker import",
    }
    
    new_content = content
    for old, new in replacements.items():
        # Handle trailing commas, parentheses, etc if needed but exact match is safer
        new_content = new_content.replace(old.replace('\\n','\n'), new.replace('\\n','\n'))
        
    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated imports in {filepath}")

for root, _, files in os.walk("."):
    if ".venv" in root or "__pycache__" in root: continue
    for file in files:
        if file.endswith(".py") and file != "safe_refactor.py":
            fix_imports_in_file(os.path.join(root, file))

print("Refactor complete.")
