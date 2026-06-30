"""
Database migrations module for SecurePassPro
Расширенная версия с поддержкой новых полей: url, username, email, favorite, category, sort_order

FIXED: Added migration for new fields without breaking existing data
"""
from __future__ import annotations

import os
import sys
import sqlite3
import datetime
import threading
from typing import Callable, Dict, Any, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger("database_migrations")

# ==================== PORTABLE PATHS LOGIC ====================

def _get_base_dir() -> str:
    """
    Handle get base dir.
    Обработать get base dir.
    Обробити get base dir.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _get_db_path() -> str:
    """
    Handle get db path.
    Обработать get db path.
    Обробити get db path.
    """
    base_dir = _get_base_dir()
    securepass_dir = os.path.join(base_dir, ".securepass")
    data_dir = os.path.join(securepass_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "passwords.db")

def get_db_path() -> str:
    """
    Return db path.
    Возвращает db path.
    Повертає db path.
    """
    return _get_db_path()

_db_lock = threading.RLock()

def _get_connection() -> sqlite3.Connection:
    """
    Handle get connection.
    Обработать get connection.
    Обробити get connection.
    """
    db_path = _get_db_path()
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== SCHEMA VERSION ====================

SCHEMA_VERSION = 8
SCHEMA_VERSION_TABLE = "schema_version"

class DatabaseMigration:
    """
    Databasemigration class.
    Класс DatabaseMigration.
    Клас DatabaseMigration.
    """
    _migration_callbacks: Dict[int, Callable[[sqlite3.Connection], bool]] = {}

    @classmethod
    def register_migration(cls, version: int, callback: Callable[[sqlite3.Connection], bool]) -> None:
        """
        Handle register migration.
        Обработать register migration.
        Обробити register migration.
        """
        cls._migration_callbacks[version] = callback

    @staticmethod
    def get_current_schema_version(db_path: str) -> int:
        """
        Return current schema version.
        Возвращает current schema version.
        Повертає current schema version.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            if not cursor.fetchone():
                conn.close()
                return 0
            cursor.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            conn.close()
            if result:
                return result[0]
            return 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get schema version: {e}")
            return 0

    @staticmethod
    def set_schema_version(db_path: str, version: int) -> bool:
        """
        Set schema version.
        Установить schema version.
        Встановити schema version.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )
            """)
            cursor.execute(
                "INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)",
                (version, datetime.datetime.now().isoformat(), f"Migrated to version {version}")
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to set schema version: {e}")
            return False

    @classmethod
    def migrate(cls, db_path: str, target_version: int = SCHEMA_VERSION) -> bool:
        """
        Handle migrate.
        Обработать migrate.
        Обробити migrate.
        """
        current_version = cls.get_current_schema_version(db_path)
        if current_version >= target_version:
            logger.info(f"Database schema is up to date (version {current_version})")
            return True

        logger.info(f"Migrating database from version {current_version} to {target_version}")

        for version in range(current_version + 1, target_version + 1):
            if version in cls._migration_callbacks:
                try:
                    conn = sqlite3.connect(db_path)
                    success = cls._migration_callbacks[version](conn)
                    conn.close()
                    if success:
                        cls.set_schema_version(db_path, version)
                        logger.info(f"Migration to version {version} completed")
                    else:
                        logger.error(f"Migration to version {version} failed")
                        return False
                except sqlite3.Error as e:
                    logger.error(f"Migration error at version {version}: {e}")
                    return False
        return True


# ==================== MIGRATION TO VERSION 3 (NEW FIELDS) ====================

def _migration_v3(conn: sqlite3.Connection) -> bool:
    """
    Migration to version 3: Add url, username, email, favorite, category, sort_order columns.
    This migration preserves all existing data and adds default values for new fields.
    """
    try:
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(passwords)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Add new columns if they don't exist
        new_columns = {
            'url': 'TEXT',
            'username': 'TEXT',
            'email': 'TEXT',
            'favorite': 'INTEGER DEFAULT 0',
            'category': 'TEXT DEFAULT ""',
            'sort_order': 'INTEGER DEFAULT 0'
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE passwords ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column: {col_name}")
                except sqlite3.Error as e:
                    logger.error(f"Failed to add column {col_name}: {e}")
                    return False
        
        # Create indexes for new columns for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON passwords(favorite)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON passwords(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON passwords(url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_username ON passwords(username)")
            logger.info("Created indexes for new columns")
        except sqlite3.Error as e:
            logger.warning(f"Index creation warning: {e}")
        
        conn.commit()
        logger.info("Migration to version 3 completed successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Migration to version 3 failed: {e}")
        conn.rollback()
        return False


# Register migration
DatabaseMigration.register_migration(3, _migration_v3)


# ==================== MIGRATION V4: CUSTOM FIELDS ====================

def _migration_v4(conn: sqlite3.Connection) -> bool:
    """Add custom_fields column (JSON array [{name, value, hidden}])."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        cols = [c[1] for c in cursor.fetchall()]
        if "custom_fields" not in cols:
            cursor.execute(
                "ALTER TABLE passwords ADD COLUMN custom_fields TEXT DEFAULT '[]'"
            )
            logger.info("Migration v4: added custom_fields column")
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Migration v4 failed: {e}")
        conn.rollback()
        return False


DatabaseMigration.register_migration(4, _migration_v4)


# ==================== MIGRATION V5: PASSWORD AGE ====================

def _migration_v5(conn: sqlite3.Connection) -> bool:
    """Add password_changed_at column; back-fill from created for existing rows."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        cols = [c[1] for c in cursor.fetchall()]
        if "password_changed_at" not in cols:
            cursor.execute(
                "ALTER TABLE passwords ADD COLUMN password_changed_at TEXT"
            )
            cursor.execute(
                "UPDATE passwords SET password_changed_at = created "
                "WHERE password_changed_at IS NULL"
            )
            logger.info("Migration v5: added password_changed_at, back-filled from created")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pwd_changed "
            "ON passwords(password_changed_at)"
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Migration v5 failed: {e}")
        conn.rollback()
        return False


DatabaseMigration.register_migration(5, _migration_v5)


# ==================== MIGRATION V6: TRASH (SOFT DELETE) ====================

def _migration_v6(conn: sqlite3.Connection) -> bool:
    """Add deleted_at column for soft-delete / trash functionality."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        cols = [c[1] for c in cursor.fetchall()]
        if "deleted_at" not in cols:
            cursor.execute("ALTER TABLE passwords ADD COLUMN deleted_at TEXT")
            logger.info("Migration v6: added deleted_at column")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deleted_at ON passwords(deleted_at)"
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Migration v6 failed: {e}")
        conn.rollback()
        return False


DatabaseMigration.register_migration(6, _migration_v6)


# ==================== MIGRATION V7: TAGS ====================

def _migration_v7(conn: sqlite3.Connection) -> bool:
    """Add tags column (JSON array of strings)."""
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        cols = [c[1] for c in cursor.fetchall()]
        if "tags" not in cols:
            cursor.execute("ALTER TABLE passwords ADD COLUMN tags TEXT DEFAULT '[]'")
            logger.info("Migration v7: added tags column")
        conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Migration v7 failed: {e}")
        conn.rollback()
        return False


DatabaseMigration.register_migration(7, _migration_v7)

# ==================== MIGRATION V8: PER-ENTRY PASSWORD HISTORY ====================

def _migration_v8(conn: sqlite3.Connection) -> bool:
    """
    Create password_history table to track old passwords per entry.
    Each time a password changes, the old one is saved here.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id   INTEGER NOT NULL REFERENCES passwords(id) ON DELETE CASCADE,
                password    TEXT NOT NULL,
                changed_at  TEXT NOT NULL
            )
        """)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_hist_record "
            "ON password_history(record_id)"
        )
        conn.commit()
        logger.info("Migration v8: created password_history table")
        return True
    except sqlite3.Error as e:
        logger.error(f"Migration v8 failed: {e}")
        conn.rollback()
        return False


DatabaseMigration.register_migration(8, _migration_v8)



# ==================== INITIALIZATION ====================

def init_database_schema() -> None:
    """Initialize database with latest schema"""
    db_path = _get_db_path()
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        
        # Create passwords table with all columns (if not exists)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                password TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT,
                notes TEXT,
                url TEXT,
                username TEXT,
                email TEXT,
                favorite INTEGER DEFAULT 0,
                category TEXT DEFAULT "",
                sort_order INTEGER DEFAULT 0,
                custom_fields TEXT DEFAULT '[]',
                password_changed_at TEXT,
                deleted_at TEXT,
                tags TEXT DEFAULT '[]'
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_label ON passwords(label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON passwords(created)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_updated ON passwords(updated)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON passwords(favorite)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON passwords(category)")
        
        conn.commit()
        
        # Run migrations if needed
        DatabaseMigration.migrate(db_path, SCHEMA_VERSION)
        
        logger.info(f"Database initialized at: {db_path}")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


__all__ = [
    'DatabaseMigration',
    'SCHEMA_VERSION',
    'SCHEMA_VERSION_TABLE',
    'init_database_schema',
    'get_db_path',
]