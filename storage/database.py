"""
Password database storage with SQLite - Main wrapper module.
Обновлён для поддержки новых полей: url, username, email, favorite, category.

Модуль хранения паролей с SQLite - Главный модуль-обёртка.
Модуль зберігання паролів з SQLite - Головний модуль-обгортка.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import os
import sys
import sqlite3
import threading
from typing import List, Dict, Any, Optional, Tuple, Union, cast

from utils.logger import get_logger
from storage.database_base import (
    get_db_path,
    get_connection,
    _db_lock,
    is_encrypted_value,
    encrypt_value_for_storage,
    decrypt_value_from_storage,
    decrypt_record
)
from storage.database_crud import (
    save_password,
    get_all_passwords,
    search_passwords,
    get_password_by_id,
    update_password,
    delete_password
)

logger = get_logger("database")


# ==================== ADDITIONAL OPERATIONS ====================

def soft_delete_password(record_id: int) -> bool:
    """Move record to trash (set deleted_at timestamp)."""
    import datetime
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            now: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE passwords SET deleted_at = ? WHERE id = ?", (now, record_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Soft delete failed id={record_id}: {e}")
            return False
        finally:
            conn.close()


def restore_password(record_id: int) -> bool:
    """Restore record from trash (clear deleted_at)."""
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("UPDATE passwords SET deleted_at = NULL WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Restore failed id={record_id}: {e}")
            return False
        finally:
            conn.close()


def get_trash() -> List[Dict[str, Any]]:
    """Return all soft-deleted records ordered by deletion date desc."""
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC
            """)
            rows: List[sqlite3.Row] = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get trash: {e}")
            return []
        finally:
            conn.close()


def empty_trash() -> int:
    """Permanently delete all trashed records. Returns count deleted."""
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("DELETE FROM passwords WHERE deleted_at IS NOT NULL")
            count: int = cursor.rowcount
            conn.commit()
            return count
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Empty trash failed: {e}")
            return 0
        finally:
            conn.close()


def toggle_favorite(record_id: int) -> bool:
    """Toggle favorite status."""
    import datetime
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT favorite FROM passwords WHERE id = ?", (record_id,))
            row: Optional[sqlite3.Row] = cursor.fetchone()
            if row is None:
                return False
            new_favorite: int = 0 if row[0] else 1
            cursor.execute(
                "UPDATE passwords SET favorite = ?, updated = ? WHERE id = ?",
                (new_favorite, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record_id)
            )
            conn.commit()
            logger.info(f"Toggled favorite for ID {record_id} to {new_favorite}")
            return True
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            conn.rollback()
            logger.error(f"Failed to toggle favorite: {e}")
            return False
        finally:
            conn.close()


def get_categories() -> List[str]:
    """Get all categories."""
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM passwords WHERE category != '' ORDER BY category")
            rows: List[sqlite3.Row] = cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {e}")
            return []
        finally:
            conn.close()


def get_passwords_sorted(sort_by: str = "favorite_desc") -> List[Dict[str, Any]]:
    """Get passwords sorted by specified criteria."""
    with _db_lock:
        conn: sqlite3.Connection = get_connection()
        try:
            cursor: sqlite3.Cursor = conn.cursor()
            
            sort_map: Dict[str, str] = {
                "favorite_desc": "ORDER BY favorite DESC, sort_order ASC, id DESC",
                "date_desc": "ORDER BY created DESC",
                "date_asc": "ORDER BY created ASC",
                "label_asc": "ORDER BY label ASC",
                "label_desc": "ORDER BY label DESC",
                "category_asc": "ORDER BY category ASC, label ASC",
                "fav_alpha": "ORDER BY favorite DESC, label ASC",
                "updated_desc": "ORDER BY updated DESC",
                "pwd_age_asc": "ORDER BY password_changed_at ASC",
            }
            
            order_by: str = sort_map.get(sort_by, "ORDER BY favorite DESC, sort_order ASC, id DESC")
            
            cursor.execute(f"""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE deleted_at IS NULL {order_by}
            """)
            rows: List[sqlite3.Row] = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get sorted passwords: {e}")
            return []
        finally:
            conn.close()


# ==================== MAIN CLASS ====================

class PasswordDB:
    """Password database class with CRUD operations for GUI compatibility."""
    
    _initialized: bool = False
    _db_path: Optional[str] = None

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Handle ensure initialized.
        Обработать ensure initialized.
        Обробити ensure initialized.
        """
        if not cls._initialized:
            try:
                from storage.database_migrations import init_database_schema
                init_database_schema()
                cls._initialized = True
                logger.info("Database initialized successfully")
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as e:
                logger.error(f"Failed to initialize database: {e}")
                # Try to create tables directly
                cls._init_direct()

    @classmethod
    def _init_direct(cls) -> None:
        """Direct database initialization if migration fails."""
        try:
            db_path: str = get_db_path()
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            conn: sqlite3.Connection = sqlite3.connect(db_path)
            cursor: sqlite3.Cursor = conn.cursor()
            
            # Create passwords table
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON passwords(favorite)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON passwords(category)")
            
            # Create password_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    password TEXT NOT NULL,
                    changed_at TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_record ON password_history(record_id)")
            
            conn.commit()
            conn.close()
            cls._initialized = True
            logger.info("Database initialized directly")
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"Direct database initialization failed: {e}")
            raise

    # ==================== CRUD OPERATIONS ====================

    @classmethod
    def save(
        cls,
        label: str,
        password: str,
        notes: str = "",
        url: str = "",
        username: str = "",
        email: str = "",
        category: str = "",
        favorite: int = 0,
        lang: Optional[str] = None,
        custom_fields: str = "[]",
        tags: str = "[]"
    ) -> int:
        """
        Handle save.
        Обработать save.
        Обробити save.
        """
        cls._ensure_initialized()
        return save_password(label, password, notes, url, username, email, category, favorite, lang, custom_fields, tags)

    @classmethod
    def get_all(cls) -> List[Dict[str, Any]]:
        """
        Return all.
        Возвращает all.
        Повертає all.
        """
        cls._ensure_initialized()
        return get_all_passwords()

    @classmethod
    def search(cls, query: str) -> List[Dict[str, Any]]:
        """
        Handle search.
        Обработать search.
        Обробити search.
        """
        cls._ensure_initialized()
        return search_passwords(query)

    @classmethod
    def get_by_id(cls, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Return by id.
        Возвращает by id.
        Повертає by id.
        """
        cls._ensure_initialized()
        return get_password_by_id(record_id)

    @classmethod
    def update(
        cls,
        record_id: int,
        label: str,
        password: Optional[str] = None,
        notes: Optional[str] = None,
        url: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        category: Optional[str] = None,
        favorite: Optional[int] = None,
        lang: Optional[str] = None,
        custom_fields: Optional[str] = None,
        tags: Optional[str] = None
    ) -> bool:
        """
        Handle update.
        Обработать update.
        Обробити update.
        """
        cls._ensure_initialized()
        return update_password(
            record_id, label, password, notes, url, username, email,
            category, favorite, lang, custom_fields, tags
        )

    @classmethod
    def delete(cls, record_id: int) -> bool:
        """
        Handle delete.
        Обработать delete.
        Обробити delete.
        """
        cls._ensure_initialized()
        return delete_password(record_id)

    # ==================== TRASH OPERATIONS ====================

    @classmethod
    def soft_delete(cls, record_id: int) -> bool:
        """
        Handle soft delete.
        Обработать soft delete.
        Обробити soft delete.
        """
        cls._ensure_initialized()
        return soft_delete_password(record_id)

    @classmethod
    def restore(cls, record_id: int) -> bool:
        """
        Handle restore.
        Обработать restore.
        Обробити restore.
        """
        cls._ensure_initialized()
        return restore_password(record_id)

    @classmethod
    def get_trash(cls) -> List[Dict[str, Any]]:
        """
        Return trash.
        Возвращает trash.
        Повертає trash.
        """
        cls._ensure_initialized()
        return get_trash()

    @classmethod
    def empty_trash(cls) -> int:
        """
        Handle empty trash.
        Обработать empty trash.
        Обробити empty trash.
        """
        cls._ensure_initialized()
        return empty_trash()

    # ==================== SORTING AND FILTERING ====================

    @classmethod
    def toggle_favorite(cls, record_id: int) -> bool:
        """
        Handle toggle favorite.
        Обработать toggle favorite.
        Обробити toggle favorite.
        """
        cls._ensure_initialized()
        return toggle_favorite(record_id)

    @classmethod
    def get_categories(cls) -> List[str]:
        """
        Return categories.
        Возвращает categories.
        Повертає categories.
        """
        cls._ensure_initialized()
        return get_categories()

    @classmethod
    def get_sorted(cls, sort_by: str = "favorite_desc") -> List[Dict[str, Any]]:
        """
        Return sorted.
        Возвращает sorted.
        Повертає sorted.
        """
        cls._ensure_initialized()
        return get_passwords_sorted(sort_by)

    @classmethod
    def get_favorites(cls) -> List[Dict[str, Any]]:
        """
        Return favorites.
        Возвращает favorites.
        Повертає favorites.
        """
        cls._ensure_initialized()
        return get_passwords_sorted("favorite_desc")

    @classmethod
    def get_by_category(cls, category: str) -> List[Dict[str, Any]]:
        """
        Return by category.
        Возвращает by category.
        Повертає by category.
        """
        cls._ensure_initialized()
        all_passwords: List[Dict[str, Any]] = get_all_passwords()
        return [p for p in all_passwords if p.get("category") == category]

    # ==================== UTILITY ====================

    @classmethod
    def get_db_path(cls) -> str:
        """
        Return db path.
        Возвращает db path.
        Повертає db path.
        """
        return get_db_path()

    @classmethod
    def count(cls) -> int:
        """
        Handle count.
        Обработать count.
        Обробити count.
        """
        cls._ensure_initialized()
        with _db_lock:
            conn: sqlite3.Connection = get_connection()
            try:
                cursor: sqlite3.Cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM passwords WHERE deleted_at IS NULL")
                return cursor.fetchone()[0]
            except sqlite3.Error as e:
                logger.error(f"Failed to count passwords: {e}")
                return 0
            finally:
                conn.close()

    @classmethod
    def clear_all(cls) -> bool:
        """
        Clear all.
        Очистить all.
        Очистити all.
        """
        cls._ensure_initialized()
        with _db_lock:
            conn: sqlite3.Connection = get_connection()
            try:
                cursor: sqlite3.Cursor = conn.cursor()
                cursor.execute("DELETE FROM passwords")
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='passwords'")
                conn.commit()
                logger.info("All passwords cleared")
                return True
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Failed to clear passwords: {e}")
                return False
            finally:
                conn.close()

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        Return stats.
        Возвращает stats.
        Повертає stats.
        """
        cls._ensure_initialized()
        from storage.database_queries import _get_vault_stats
        return _get_vault_stats()

    @classmethod
    def get_sort_options(cls) -> List[str]:
        """
        Return sort options.
        Возвращает sort options.
        Повертає sort options.
        """
        return ["favorite_desc", "date_desc", "date_asc", "label_asc", "label_desc", "category_asc"]

    @classmethod
    def get_db_size(cls) -> int:
        """Get database file size in bytes."""
        try:
            db_path: str = get_db_path()
            if os.path.exists(db_path):
                return os.path.getsize(db_path)
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"Failed to get DB size: {e}")
        return 0

    @classmethod
    def get_db_size_mb(cls) -> float:
        """
        Return db size mb.
        Возвращает db size mb.
        Повертає db size mb.
        """
        return cls.get_db_size() / (1024 * 1024)

    @classmethod
    def close_connection(cls) -> None:
        """
        Handle close connection.
        Обработать close connection.
        Обробити close connection.
        """
        logger.debug("Database connection closed (no-op for SQLite)")

    @classmethod
    def close_all_connections(cls) -> None:
        """
        Handle close all connections.
        Обработать close all connections.
        Обробити close all connections.
        """
        logger.debug("All database connections closed")


# ==================== BACKWARD COMPATIBILITY ====================

Database = PasswordDB

# Initialize database schema on module load if not in test mode
if not __import__('core.config_manager', fromlist=['ConfigManager']).ConfigManager.instance().get('SKIP_DB_INIT', False):
    try:
        PasswordDB._ensure_initialized()
    except (sqlite3.Error, OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to initialize database on module load: {e}")
