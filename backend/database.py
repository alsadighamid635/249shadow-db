import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "training.db"


from pathlib import Path as _Path
import os as _os
if "DB" in globals():
    if _os.environ.get("RENDER") or _Path(__file__).resolve().as_posix().startswith("/opt/render"):
        DB = "/tmp/249shadow.db"
    _Path(str(DB)).parent.mkdir(parents=True, exist_ok=True)

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def initialize():
    with connect() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS training_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            demo_value TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

if __name__ == "__main__":
    initialize()
    print("Database initialized:", DB)
