"""
Database base operations - connection, encryption, decryption.
Базовые операции базы данных - подключение, шифрование, дешифрование.
Базові операції бази даних - підключення, шифрування, дешифрування.
"""
from __future__ import annotations
import os
import sys
import sqlite3
import threading
from typing import Dict, Any, Optional, List

from utils.logger import get_logger
from security.encryption import decrypt, encrypt

logger = get_logger("database_base")

# Database lock
_db_lock = threading.RLock()


def get_db_path() -> str:
    """Get database file path - SINGLE SOURCE OF TRUTH."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        # Get the project root directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Use .securepass/data directory
    data_dir = os.path.join(base_dir, ".securepass", "data")
    os.makedirs(data_dir, exist_ok=True)

    # Hide on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(data_dir, 0x02)
        except (ImportError, AttributeError, OSError):
            pass

    return os.path.join(data_dir, "passwords.db")


# ── Connection management ────────────────────────────────
# We use a per-thread sqlite3 connection (check_same_thread=False
# handled by a threading.Lock) rather than a pool to keep SQLite's
# WAL (Write-Ahead Log) mode working correctly.
#
# The lock ensures only one thread writes at a time — SQLite itself
# serialises writers but we wrap it for clearer ownership semantics.
def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    db_path = get_db_path()
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def is_encrypted_value(value: str) -> bool:
    """Check if value is encrypted."""
    return isinstance(value, str) and value.startswith(("enc1:", "enc2:", "enc3:"))


# ── Field-level encryption helpers ───────────────────────
# These thin wrappers centralise the call site so we can easily
# swap the encryption scheme in future without touching every query.
def encrypt_value_for_storage(value: str, field_name: str) -> str:
    """Encrypt value for storage."""
    if value is None:
        return ""
    if is_encrypted_value(value):
        return value
    try:
        return encrypt(str(value))
    except (ValueError, TypeError, MemoryError, RuntimeError, OSError) as e:
        logger.error(f"{field_name} encryption failed: {e}")
        raise


def decrypt_value_from_storage(value: str, field_name: str) -> str:
    """Decrypt value from storage."""
    if value is None:
        return ""
    try:
        return decrypt(str(value))
    except (ValueError, TypeError, UnicodeDecodeError, RuntimeError, OSError) as e:
        logger.error(f"{field_name} decryption failed: {e}")
        return "[decryption failed]"


def decrypt_record(row: sqlite3.Row) -> Dict[str, Any]:
    """Decrypt all encrypted fields in a record."""
    record = dict(row)
    record["label"] = decrypt_value_from_storage(record.get("label", ""), "Label")
    record["password"] = decrypt_value_from_storage(record.get("password", ""), "Password")
    record["notes"] = decrypt_value_from_storage(record.get("notes", ""), "Notes")

    # Plaintext fields
    record["url"] = record.get("url", "") or ""
    record["username"] = record.get("username", "") or ""
    record["email"] = record.get("email", "") or ""
    record["favorite"] = record.get("favorite", 0) or 0
    record["category"] = record.get("category", "") or ""
    record["sort_order"] = record.get("sort_order", 0) or 0
    record["custom_fields"] = record.get("custom_fields") or "[]"
    record["password_changed_at"] = (
        record.get("password_changed_at") or record.get("created") or ""
    )
    record["deleted_at"] = record.get("deleted_at") or ""
    record["tags"] = record.get("tags") or "[]"

    return record