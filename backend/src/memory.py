import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "callers.sqlite3"


@dataclass(frozen=True)
class CallerMemory:
    user_id: str
    name: str
    language_preference: str
    facts: dict[str, Any]
    last_interaction: str


class CallerMemoryStore:
    """Persistent, consent-gated caller memory backed by SQLite."""

    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS caller_memory (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    language_preference TEXT NOT NULL,
                    facts_json TEXT NOT NULL,
                    last_interaction TEXT NOT NULL
                )
                """
            )

    def lookup(self, user_id: str) -> CallerMemory | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, name, language_preference, facts_json,
                       last_interaction
                FROM caller_memory
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            return None
        return CallerMemory(
            user_id=row["user_id"],
            name=row["name"],
            language_preference=row["language_preference"],
            facts=json.loads(row["facts_json"]),
            last_interaction=row["last_interaction"],
        )

    def save(
        self,
        *,
        user_id: str,
        name: str,
        language_preference: str,
        facts: dict[str, Any],
        consent_given: bool,
    ) -> bool:
        if not consent_given:
            return False
        user_id = user_id.strip()
        name = name.strip()
        if not user_id or not name:
            return False

        existing = self.lookup(user_id)
        merged_facts = dict(existing.facts) if existing else {}
        merged_facts.update({key: value for key, value in facts.items() if value})
        timestamp = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO caller_memory (
                    user_id, name, language_preference, facts_json,
                    last_interaction
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = excluded.name,
                    language_preference = excluded.language_preference,
                    facts_json = excluded.facts_json,
                    last_interaction = excluded.last_interaction
                """,
                (
                    user_id,
                    name,
                    language_preference.strip() or "unknown",
                    json.dumps(merged_facts, ensure_ascii=False),
                    timestamp,
                ),
            )
        return True

    def forget(self, user_id: str) -> bool:
        """Permanently delete one caller's saved record."""
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM caller_memory WHERE user_id = ?", (user_id.strip(),)
            )
        return cursor.rowcount > 0
