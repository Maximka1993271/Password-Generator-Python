"""
SQLite database for saved passwords
"""
import sqlite3
import os
import sys
import ctypes
import datetime
from typing import List, Dict, Any

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(BASE_DIR, "data")
DB_FILE = os.path.join(CONFIG_DIR, "passwords.db")
# =============================================================


def _hide_dir(path: str) -> None:
    """Скрывает папку на Windows (атрибут Hidden)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


class PasswordDB:
    """Password vault database handler"""

    @classmethod
    def _get_connection(cls):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _hide_dir(CONFIG_DIR)          # скрываем сразу после создания
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = str
        conn.execute("PRAGMA encoding = 'UTF-8';")
        conn.execute("PRAGMA secure_delete = ON;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                password TEXT NOT NULL,
                created TEXT NOT NULL
            )
        """)
        conn.commit()
        return conn

    @classmethod
    def save(cls, label: str, password: str) -> int:
        """Save a password to the vault"""
        conn = cls._get_connection()
        cursor = conn.execute(
            "INSERT INTO passwords (label, password, created) VALUES (?, ?, ?)",
            (label, password, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        row_id = cursor.lastrowid
        conn.close()
        return row_id

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Get all saved passwords"""
        conn = cls._get_connection()
        rows = conn.execute(
            "SELECT id, label, password, created FROM passwords ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "label": r[1], "password": r[2], "created": r[3]} for r in rows]

    @classmethod
    def update(cls, row_id: int, label: str, password: str = None) -> None:
        """Update a password entry"""
        conn = cls._get_connection()
        if password is not None:
            conn.execute("UPDATE passwords SET label=?, password=? WHERE id=?",
                         (label, password, row_id))
        else:
            conn.execute("UPDATE passwords SET label=? WHERE id=?", (label, row_id))
        conn.commit()
        conn.close()

    @classmethod
    def delete(cls, row_id: int) -> None:
        """Delete a password entry"""
        conn = cls._get_connection()
        conn.execute("DELETE FROM passwords WHERE id=?", (row_id,))
        conn.commit()
        conn.close()

    @classmethod
    def count(cls) -> int:
        """Get total number of saved passwords"""
        conn = cls._get_connection()
        count = conn.execute("SELECT COUNT(*) FROM passwords").fetchone()[0]
        conn.close()
        return count

    @classmethod
    def search(cls, query: str) -> List[Dict[str, Any]]:
        """Search passwords by label or password content"""
        conn = cls._get_connection()
        search_pattern = f"%{query}%"
        rows = conn.execute(
            "SELECT id, label, password, created FROM passwords WHERE label LIKE ? OR password LIKE ? ORDER BY id DESC",
            (search_pattern, search_pattern)
        ).fetchall()
        conn.close()
        return [{"id": r[0], "label": r[1], "password": r[2], "created": r[3]} for r in rows]
