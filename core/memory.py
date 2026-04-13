"""
core/memory.py — Conversation memory using SQLite.

Stores every user and assistant turn in a local SQLite database.
Supports loading the last N turns for LLM context.
"""

import sqlite3
import os
import datetime


class Memory:
    """Persistent conversation memory backed by SQLite."""

    def __init__(self, db_path=None):
        """
        Initialize the memory database.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to 'memory.db' in the project root.
        """
        if db_path is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            db_path = os.path.join(project_root, "memory.db")

        self.db_path = db_path
        self._init_db()
        print(f"[Memory] Database ready: {self.db_path}")

    def _init_db(self):
        """Create the conversations table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save_turn(self, role: str, content: str):
        """
        Save a conversation turn.

        Args:
            role: 'user' or 'assistant'
            content: The message content.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
            (role, content, timestamp),
        )
        conn.commit()
        conn.close()

    def get_last_turns(self, n: int = 10) -> list:
        """
        Retrieve the last N conversation turns.

        Args:
            n: Number of turns to retrieve (each turn = 1 message).
               Default is 10 (which means 5 user + 5 assistant exchanges).

        Returns:
            List of dicts: [{"role": "user", "content": "..."}, ...]
            Ordered oldest-first, suitable for LLM context.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
            (n,),
        )
        rows = cursor.fetchall()
        conn.close()

        # Reverse so oldest is first (chronological order for LLM)
        turns = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
        return turns

    def clear(self):
        """Delete all conversation history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations")
        conn.commit()
        conn.close()
        print("[Memory] Conversation history cleared.")

    def get_turn_count(self) -> int:
        """Return the total number of stored turns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        count = cursor.fetchone()[0]
        conn.close()
        return count
