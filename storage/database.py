"""
SQLite database for saved passwords (with AES-256-GCM field encryption)
"""
import sqlite3
import os
import sys
import ctypes
import datetime
from contextlib import closing
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
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


def _enc(text: str) -> str:
    """Encrypt password field. Fail closed instead of storing plaintext."""
    from security.encryption import encrypt
    return encrypt(text)


def _dec(text: str) -> str:
    """Decrypt password field for display."""
    try:
        from security.encryption import decrypt
        return decrypt(text)
    except Exception:
        return "[encrypted - unlock with master password]"


class PasswordDB:
    """Password vault database handler"""

    @classmethod
    def _get_connection(cls):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _hide_dir(CONFIG_DIR)
        conn = sqlite3.connect(DB_FILE)
        conn.text_factory = str
        conn.execute("PRAGMA encoding = 'UTF-8';")
        conn.execute("PRAGMA secure_delete = ON;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
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
        """Save an encrypted password to the vault."""
        with closing(cls._get_connection()) as conn:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO passwords (label, password, created) VALUES (?, ?, ?)",
                    (label[:200], _enc(password),
                     datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                return cursor.lastrowid

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """Get all saved passwords (decrypted)."""
        with closing(cls._get_connection()) as conn:
            rows = conn.execute(
                "SELECT id, label, password, created FROM passwords ORDER BY id DESC"
            ).fetchall()
        return [{"id": r[0], "label": r[1],
                 "password": _dec(r[2]), "created": r[3]} for r in rows]

    @classmethod
    def update(cls, row_id: int, label: str, password: str = None) -> None:
        """Update a password entry (re-encrypts with current key)."""
        with closing(cls._get_connection()) as conn:
            with conn:
                if password is not None:
                    conn.execute(
                        "UPDATE passwords SET label=?, password=? WHERE id=?",
                        (label[:200], _enc(password), row_id))
                else:
                    conn.execute("UPDATE passwords SET label=? WHERE id=?",
                                 (label[:200], row_id))

    @classmethod
    def delete(cls, row_id: int) -> None:
        """Delete a password entry."""
        with closing(cls._get_connection()) as conn:
            with conn:
                conn.execute("DELETE FROM passwords WHERE id=?", (row_id,))

    @classmethod
    def count(cls) -> int:
        """Get total number of saved passwords."""
        with closing(cls._get_connection()) as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM passwords").fetchone()[0]

    @classmethod
    def search(cls, query: str) -> List[Dict[str, Any]]:
        """Search passwords by label (decrypted passwords not searchable by design)."""
        query = query[:200]
        with closing(cls._get_connection()) as conn:
            rows = conn.execute(
                "SELECT id, label, password, created FROM passwords "
                "WHERE label LIKE ? ESCAPE '\\' ORDER BY id DESC",
                (f"%{query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')}%",)
            ).fetchall()
        return [{"id": r[0], "label": r[1],
                 "password": _dec(r[2]), "created": r[3]} for r in rows]
