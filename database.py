import sqlite3
import datetime

DB_NAME = "mod.db"

# ======================
# CONEXIÓN
# ======================
db = sqlite3.connect(DB_NAME)
cursor = db.cursor()

# ======================
# TABLAS
# ======================
cursor.execute("""
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    timestamp TEXT NOT NULL
)
""")

db.commit()

# ======================
# HELPERS
# ======================
def add_case(guild_id: int, user_id: int, moderator_id: int, action: str, reason: str):
    cursor.execute(
        "INSERT INTO cases VALUES (NULL, ?, ?, ?, ?, ?)",
        (
            guild_id,
            user_id,
            moderator_id,
            action,
            reason,
            datetime.datetime.utcnow().isoformat()
        )
    )
    db.commit()

def get_cases(guild_id: int, user_id: int | None = None, limit: int = 10):
    if user_id:
        cursor.execute(
            "SELECT action, reason, timestamp FROM cases WHERE guild_id=? AND user_id=? ORDER BY id DESC LIMIT ?",
            (guild_id, user_id, limit)
        )
    else:
        cursor.execute(
            "SELECT action, user_id, reason, timestamp FROM cases WHERE guild_id=? ORDER BY id DESC LIMIT ?",
            (guild_id, limit)
        )
    return cursor.fetchall()

def clear_cases(guild_id: int, user_id: int):
    cursor.execute(
        "DELETE FROM cases WHERE guild_id=? AND user_id=?",
        (guild_id, user_id)
    )
    db.commit()
