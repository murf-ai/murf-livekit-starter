import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "caller_data.db"
)


def init_db():
    """Initializes the SQLite database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: str):
    """Retrieves user details from the database by user_id."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, name, language_preference, facts, last_interaction FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        try:
            facts = json.loads(row[3])
        except Exception:
            facts = {}
        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }
    return None


def save_user(user_id: str, name: str, language_preference: str, facts: dict):
    """Saves or updates user details and facts in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    facts_str = json.dumps(facts)
    last_interaction = datetime.now().isoformat()
    cursor.execute(
        """
        INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
    """,
        (user_id, name, language_preference, facts_str, last_interaction),
    )
    conn.commit()
    conn.close()
    return {
        "user_id": user_id,
        "name": name,
        "language_preference": language_preference,
        "facts": facts,
        "last_interaction": last_interaction,
    }
