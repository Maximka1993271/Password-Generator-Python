"""
Database queries module for SecurePassPro - CRUD operations with extended fields
Поддержка новых полей: url, username, email, favorite, category, sort_order

Модуль запросов к базе данных для SecurePassPro - CRUD операции с расширенными полями
Підтримка нових полів: url, username, email, favorite, category, sort_order
"""
from __future__ import annotations

import os
import sys
import sqlite3
import datetime
import threading
from typing import List, Dict, Any, Optional

from utils.logger import get_logger

logger = get_logger("database_queries")

# ==================== IMPORT FROM DATABASE_BASE ====================
# Use the SAME functions from database_base to avoid duplication
from storage.database_base import (
    get_db_path,
    get_connection,
    _db_lock,
    is_encrypted_value,
    encrypt_value_for_storage,
    decrypt_value_from_storage,
    decrypt_record
)


# ==================== CRUD OPERATIONS WITH NEW FIELDS ====================

# ── CRUD implementation ───────────────────────────────────────
# All field values that can contain user-supplied text are encrypted
# via security.encryption.encrypt() before being written to SQLite.
# The database itself may optionally use SQLCipher (page-level encryption)
# on top of field-level encryption for defence-in-depth.
#
# Pattern used throughout: encrypt on write, decrypt on read.
# IDs, timestamps, and booleans are stored plaintext (not sensitive).
# ── Input validation (applied before every write to the database) ──
from core.validators import (
    sanitize_label, sanitize_url, sanitize_notes, sanitize_text,
    LabelValidator, PasswordValidator, URLValidator, EmailValidator,
    CategoryValidator, MAX_LABEL_LEN, MAX_PASSWORD_LEN,
)
_label_v    = LabelValidator(required=True)
_password_v = PasswordValidator(required=True, min_length=1)
_url_v      = URLValidator(required=False)
_email_v    = EmailValidator(required=False)
_category_v = CategoryValidator(required=False)

def _save_password(label: str, password: str, notes: str = "", 
                   url: str = "", username: str = "", email: str = "",
                   category: str = "", favorite: int = 0,
                   lang: str = None, custom_fields: str = "[]",
                   tags: str = "[]") -> int:
    """
    Handle save password.
    Обработать save password.
    Обробити save password.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not label or label.strip() == "":
                if lang:
                    try:
                        from Langs.lang import LANGUAGES
                        label = LANGUAGES.get(lang, LANGUAGES["RU"]).get("db_no_label", "No label")
                    except ImportError:
                        label = "No label"
                else:
                    label = "No label"
            label = str(label)[:200]

            if notes and len(notes) > 500:
                notes = notes[:500]
            if url and len(url) > 500:
                url = url[:500]
            if username and len(username) > 100:
                username = username[:100]
            if email and len(email) > 100:
                email = email[:100]
            if category and len(category) > 100:
                category = category[:100]

            # ── Extended validation (blocking errors + advisory warnings) ──
            try:
                from core.validators import extended_validator
                _vr = extended_validator.validate(
                    label=label, password=str(password or ""),
                    url=url or "", email=email or "",
                    username=username or "", notes=notes or "",
                    category=category or "",
                    custom_fields=custom_fields or "[]",
                    warn_duplicate=True, warn_weak=True,
                )
                if not _vr.valid:
                    logger.warning("_save_password blocked: %s", _vr.errors)
                    return -1
                for w in _vr.warnings:
                    logger.info("[%s] %s", w.code, str(w.message)[:100])
            except ImportError:
                pass  # validator not available — continue without extended checks

            encrypted_label = encrypt_value_for_storage(label, "Label")
            encrypted_password = encrypt_value_for_storage(password, "Password")
            encrypted_notes = encrypt_value_for_storage(notes, "Notes") if notes else ""

            cursor.execute("""
                INSERT INTO passwords 
                (label, password, created, updated, notes, url, username, email,
                 category, favorite, sort_order, custom_fields, password_changed_at, tags) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                encrypted_label, encrypted_password, now, now, encrypted_notes,
                url, username, email, category, favorite, 0,
                custom_fields or "[]",
                now,
                tags or "[]"
            ))
            conn.commit()
            record_id = cursor.lastrowid
            logger.info(f"Password saved with ID: {record_id}")
            return record_id

        except (sqlite3.Error, ValueError, TypeError, OSError, IOError) as e:
            conn.rollback()
            logger.error(f"Failed to save password: {e}")
            raise ValueError(f"Error saving password: {e}")
        finally:
            conn.close()


def _get_all_passwords() -> List[Dict[str, Any]]:
    """
    Handle get all passwords.
    Обработать get all passwords.
    Обробити get all passwords.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes, 
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE deleted_at IS NULL ORDER BY favorite DESC, sort_order ASC, id DESC
            """)
            rows = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get passwords: {e}")
            return []
        finally:
            conn.close()


def _search_passwords(query: str) -> List[Dict[str, Any]]:
    """Search passwords with memory-efficient SQL pre-filtering."""
    query_text = (query or "").casefold()
    if not query_text:
        return _get_all_passwords()

    sql_like = f"%{query}%"
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords
                WHERE deleted_at IS NULL
                  AND (
                    url       LIKE ? COLLATE NOCASE OR
                    username  LIKE ? COLLATE NOCASE OR
                    email     LIKE ? COLLATE NOCASE OR
                    category  LIKE ? COLLATE NOCASE OR
                    created   LIKE ? COLLATE NOCASE OR
                    updated   LIKE ? COLLATE NOCASE OR
                    tags      LIKE ? COLLATE NOCASE OR
                    label     IS NOT NULL OR
                    notes     IS NOT NULL
                  )
                ORDER BY favorite DESC, sort_order ASC, id DESC
            """, (sql_like,) * 7)
            candidate_rows = cursor.fetchall()
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Search pre-filter failed: {e}")
            return _get_all_passwords()
        finally:
            conn.close()

    # Decrypt candidates and apply full-text match
    results = []
    for row in candidate_rows:
        record = decrypt_record(row)
        haystack_parts = [str(record.get(field, "")) for field in
                          ("label", "created", "updated", "notes",
                           "url", "username", "email", "category")]
        # Also search inside tags JSON array
        try:
            import json as _json
            tags = _json.loads(record.get("tags", "[]") or "[]")
            haystack_parts.extend(str(t) for t in tags)
        except (ValueError, TypeError):
            pass
        # Also search inside custom field names and values
        try:
            import json as _json
            cf = _json.loads(record.get("custom_fields", "[]") or "[]")
            for field in cf:
                haystack_parts.append(str(field.get("name", "")))
                if not field.get("hidden"):
                    haystack_parts.append(str(field.get("value", "")))
        except (ValueError, TypeError):
            pass

        haystack = " ".join(haystack_parts).casefold()
        if query_text in haystack:
            results.append(record)
    return results


def _get_password_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    """
    Handle get password by id.
    Обработать get password by id.
    Обробити get password by id.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE id = ?
            """, (record_id,))
            row = cursor.fetchone()
            return decrypt_record(row) if row else None
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get password by ID: {e}")
            return None
        finally:
            conn.close()


def _update_password(record_id: int, label: str, password: Optional[str] = None,
                     notes: Optional[str] = None, url: Optional[str] = None,
                     username: Optional[str] = None, email: Optional[str] = None,
                     category: Optional[str] = None, favorite: Optional[int] = None,
                     lang: str = None, custom_fields: Optional[str] = None,
                     tags: Optional[str] = None) -> bool:
    """Update an existing password record by *record_id*.

    Обновляет существующую запись по идентификатору.
    Оновлює існуючий запис за ідентифікатором.

    Args:
        record_id (int): Primary key of the record to update.
        label (str): New display name.
        password (Optional[str]): New plaintext password, or ``None`` to leave unchanged.
        notes (Optional[str]): New notes, or ``None`` to leave unchanged.
        url (Optional[str]): New URL, or ``None`` to leave unchanged.
        username (Optional[str]): New username, or ``None``.
        email (Optional[str]): New e-mail, or ``None``.
        category (Optional[str]): New category, or ``None``.
        favorite (Optional[int]): ``1`` / ``0``, or ``None``.
        lang (str | None): Language tag, or ``None``.
        custom_fields (Optional[str]): JSON list, or ``None``.
        tags (Optional[str]): JSON list, or ``None``.

    Returns:
        bool: True on success, False otherwise.
    Обработать update password.
    Обробити update password.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not label or label.strip() == "":
                if lang:
                    try:
                        from Langs.lang import LANGUAGES
                        label = LANGUAGES.get(lang, LANGUAGES["RU"]).get("db_no_label", "No label")
                    except ImportError:
                        label = "No label"
                else:
                    label = "No label"
            label = str(label)[:200]

            # ── Extended validation (blocking errors + advisory warnings) ──
            try:
                from core.validators import (
                    sanitize_url, sanitize_notes, sanitize_text,
                    validate_custom_fields, score_password, check_url_homograph,
                    URLValidator, EmailValidator, CategoryValidator,
                )
                if url      is not None: url      = sanitize_url(str(url))[:500]
                if notes    is not None: notes    = sanitize_notes(str(notes))[:500]
                if username is not None: username = sanitize_text(str(username), max_len=100)
                if email    is not None: email    = sanitize_text(str(email),    max_len=100)
                if category is not None: category = sanitize_text(str(category), max_len=100)

                _upd_errors = []
                if url:
                    _r = URLValidator(required=False).validate(url)
                    _upd_errors.extend(_r.errors)
                if email:
                    _r = EmailValidator(required=False).validate(email)
                    _upd_errors.extend(_r.errors)
                if category:
                    _r = CategoryValidator(required=False).validate(category)
                    _upd_errors.extend(_r.errors)
                if custom_fields is not None:
                    _cf_ok, _cf_err = validate_custom_fields(str(custom_fields))
                    if not _cf_ok:
                        _upd_errors.append(_cf_err)

                if _upd_errors:
                    logger.warning("_update_password blocked: %s", _upd_errors)
                    return False

                # Advisory only — does not block the update
                if password:
                    _sc = score_password(str(password))
                    if _sc["score"] < 30:
                        logger.info("_update_password: weak password score=%d entropy=%.1f",
                                    _sc["score"], _sc["entropy"])
                if url:
                    _hg = check_url_homograph(url)
                    if _hg:
                        logger.warning("_update_password: homograph URL: %s", str(_hg)[:80])
            except ImportError:
                pass  # validators module unavailable — proceed without extended checks

            encrypted_label = encrypt_value_for_storage(label, "Label")
            encrypted_password = encrypt_value_for_storage(password, "Password") if password is not None else None
            encrypted_notes = encrypt_value_for_storage(notes, "Notes") if notes is not None else None

            updates = ["label = ?", "updated = ?"]
            params = [encrypted_label, now]

            if encrypted_password is not None:
                # Save current password to history before updating
                try:
                    cursor.execute(
                        "SELECT password FROM passwords WHERE id = ?", (record_id,)
                    )
                    old_row = cursor.fetchone()
                    if old_row and old_row[0]:
                        cursor.execute(
                            "INSERT INTO password_history (record_id, password, changed_at) "
                            "VALUES (?, ?, ?)",
                            (record_id, old_row[0], now)
                        )
                except sqlite3.Error as e:
                    logger.debug(f"Password history save error: {e}")

                updates.append("password = ?")
                params.append(encrypted_password)
                updates.append("password_changed_at = ?")
                params.append(now)
            if encrypted_notes is not None:
                updates.append("notes = ?")
                params.append(encrypted_notes)
            if url is not None:
                updates.append("url = ?")
                params.append(url[:500] if url else "")
            if username is not None:
                updates.append("username = ?")
                params.append(username[:100] if username else "")
            if email is not None:
                updates.append("email = ?")
                params.append(email[:100] if email else "")
            if category is not None:
                updates.append("category = ?")
                params.append(category[:100] if category else "")
            if favorite is not None:
                updates.append("favorite = ?")
                params.append(1 if favorite else 0)
            if custom_fields is not None:
                updates.append("custom_fields = ?")
                params.append(custom_fields)
            if tags is not None:
                updates.append("tags = ?")
                params.append(tags)

            params.append(record_id)

            query = f"UPDATE passwords SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"Password updated with ID: {record_id}")
            return cursor.rowcount > 0

        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            conn.rollback()
            logger.error(f"Failed to update password: {e}")
            return False
        finally:
            conn.close()


def _delete_password(record_id: int) -> bool:
    """Hard-delete the record with *record_id*.

    Безвозвратно удаляет запись из базы данных.
    Безповоротно видаляє запис з бази даних.

    Args:
        record_id (int): Primary key of the record to delete.

    Returns:
        bool: True if the record was deleted, False otherwise.
    Обработать delete password.
    Обробити delete password.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM passwords WHERE id = ?", (record_id,))
            conn.commit()
            logger.info(f"Password deleted with ID: {record_id}")
            return cursor.rowcount > 0
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            conn.rollback()
            logger.error(f"Failed to delete password: {e}")
            return False
        finally:
            conn.close()


def _count_passwords() -> int:
    """
    Handle count passwords.
    Обработать count passwords.
    Обробити count passwords.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM passwords")
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Failed to count passwords: {e}")
            return 0
        finally:
            conn.close()


def _clear_all_passwords() -> bool:
    """
    Handle clear all passwords.
    Обработать clear all passwords.
    Обробити clear all passwords.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
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


def _soft_delete_password(record_id: int) -> bool:
    """Move record to trash (set deleted_at timestamp)."""
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE passwords SET deleted_at = ? WHERE id = ?", (now, record_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Soft delete failed id={record_id}: {e}")
            return False
        finally:
            conn.close()


def _restore_password(record_id: int) -> bool:
    """Restore record from trash (clear deleted_at)."""
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE passwords SET deleted_at = NULL WHERE id = ?", (record_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Restore failed id={record_id}: {e}")
            return False
        finally:
            conn.close()


def _get_trash() -> list:
    """Return all soft-deleted records ordered by deletion date desc."""
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC
            """)
            rows = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get trash: {e}")
            return []
        finally:
            conn.close()


def _empty_trash() -> int:
    """Permanently delete all trashed records. Returns count deleted."""
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM passwords WHERE deleted_at IS NOT NULL")
            count = cursor.rowcount
            conn.commit()
            return count
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Empty trash failed: {e}")
            return 0
        finally:
            conn.close()


def _pwd_age_days(date_str: str) -> int:
    """Days since date_str (YYYY-MM-DD HH:MM:SS). Returns 0 on any error."""
    if not date_str:
        return 0
    try:
        dt = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return max(0, (datetime.datetime.now() - dt).days)
    except (ValueError, TypeError):
        return 0


def _get_vault_stats() -> dict:
    """Compute vault statistics with minimal memory allocation."""
    import math as _math, string as _str, datetime as _dt

    with _db_lock:
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Counts that need no decryption
            cur.execute("SELECT COUNT(*) FROM passwords WHERE deleted_at IS NULL")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM passwords WHERE deleted_at IS NOT NULL")
            in_trash = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM passwords
                WHERE deleted_at IS NULL AND (url IS NULL OR TRIM(url) = '')
            """)
            no_url = cur.fetchone()[0]
            ninety_days_ago = (
                _dt.datetime.now() - _dt.timedelta(days=90)
            ).strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                SELECT COUNT(*) FROM passwords
                WHERE deleted_at IS NULL
                  AND (password_changed_at IS NULL
                       OR password_changed_at < ?)
            """, (ninety_days_ago,))
            old_pwd = cur.fetchone()[0]
            cur.execute("""
                SELECT COUNT(*) FROM passwords
                WHERE deleted_at IS NULL
                  AND tags IS NOT NULL AND tags != '[]' AND tags != ''
            """)
            with_tags = cur.fetchone()[0]

            if total == 0:
                return {"total": 0, "weak": 0, "duplicates": 0,
                        "no_url": no_url, "old_pwd": old_pwd,
                        "in_trash": in_trash, "with_tags": with_tags}

            # For weak/duplicate we must decrypt passwords
            cur.execute("""
                SELECT password FROM passwords WHERE deleted_at IS NULL
            """)
            enc_pwds = [row[0] for row in cur.fetchall()]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Vault stats query failed: {e}")
            return {"total": 0, "weak": 0, "duplicates": 0,
                    "no_url": 0, "old_pwd": 0, "in_trash": 0, "with_tags": 0}
        finally:
            conn.close()

    def _is_weak(pwd):
        if not pwd:
            return True
        pool = 0
        if any(c.islower() for c in pwd): pool += 26
        if any(c.isupper() for c in pwd): pool += 26
        if any(c.isdigit() for c in pwd): pool += 10
        if any(c in _str.punctuation for c in pwd): pool += 32
        pool = pool or 1
        return len(pwd) * _math.log2(pool) < 40

    plain_pwds = [decrypt_value_from_storage(p, "Password") for p in enc_pwds]
    weak = sum(1 for p in plain_pwds if _is_weak(p))
    duplicates = total - len(set(plain_pwds))
    # Cleanup
    for i in range(len(plain_pwds)):
        plain_pwds[i] = ""
    del plain_pwds

    return {"total": total, "weak": weak, "duplicates": duplicates,
            "no_url": no_url, "old_pwd": old_pwd, "in_trash": in_trash,
            "with_tags": with_tags}


def _toggle_favorite(record_id: int) -> bool:
    """
    Handle toggle favorite.
    Обработать toggle favorite.
    Обробити toggle favorite.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT favorite FROM passwords WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            if row is None:
                return False
            new_favorite = 0 if row[0] else 1
            cursor.execute("UPDATE passwords SET favorite = ?, updated = ? WHERE id = ?",
                          (new_favorite, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), record_id))
            conn.commit()
            logger.info(f"Toggled favorite for ID {record_id} to {new_favorite}")
            return True
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            conn.rollback()
            logger.error(f"Failed to toggle favorite: {e}")
            return False
        finally:
            conn.close()


def _get_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Handle get by category.
    Обработать get by category.
    Обробити get by category.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE category = ? AND deleted_at IS NULL ORDER BY favorite DESC, sort_order ASC
            """, (category,))
            rows = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get passwords by category: {e}")
            return []
        finally:
            conn.close()


def _get_categories() -> List[str]:
    """
    Handle get categories.
    Обработать get categories.
    Обробити get categories.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM passwords WHERE category != '' ORDER BY category")
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to get categories: {e}")
            return []
        finally:
            conn.close()


def _get_favorites() -> List[Dict[str, Any]]:
    """
    Handle get favorites.
    Обработать get favorites.
    Обробити get favorites.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE favorite = 1 AND deleted_at IS NULL ORDER BY sort_order ASC, id DESC
            """)
            rows = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get favorites: {e}")
            return []
        finally:
            conn.close()


def _get_sort_options() -> List[str]:
    """Get available sort options for UI"""
    return ["favorite_desc", "date_desc", "date_asc", "label_asc", "label_desc", "category_asc"]


def _get_passwords_sorted(sort_by: str = "favorite_desc") -> List[Dict[str, Any]]:
    """
    Handle get passwords sorted.
    Обработать get passwords sorted.
    Обробити get passwords sorted.
    """
    with _db_lock:
        conn = get_connection()
        try:
            cursor = conn.cursor()
            
            sort_map = {
                "favorite_desc":   "ORDER BY favorite DESC, sort_order ASC, id DESC",
                "date_desc":       "ORDER BY created DESC",
                "date_asc":        "ORDER BY created ASC",
                "label_asc":       "ORDER BY label ASC",
                "label_desc":      "ORDER BY label DESC",
                "category_asc":    "ORDER BY category ASC, label ASC",
                "fav_alpha":       "ORDER BY favorite DESC, label ASC",
                "updated_desc":    "ORDER BY updated DESC",
                "pwd_age_asc":     "ORDER BY password_changed_at ASC",
            }
            
            order_by = sort_map.get(sort_by, "ORDER BY favorite DESC, sort_order ASC, id DESC")
            
            cursor.execute(f"""
                SELECT id, label, password, created, updated, notes,
                       url, username, email, favorite, category, sort_order,
                       custom_fields, password_changed_at, deleted_at, tags
                FROM passwords WHERE deleted_at IS NULL {order_by}
            """)
            rows = cursor.fetchall()
            return [decrypt_record(row) for row in rows]
        except (sqlite3.Error, ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to get sorted passwords: {e}")
            return []
        finally:
            conn.close()


# ==================== CRUD OPERATIONS CLASS ====================

# ── Public aliases (without underscore prefix) ───────────────
# storage.database and other modules import these names directly.
save_password      = _save_password
get_all_passwords  = _get_all_passwords
search_passwords   = _search_passwords
get_password_by_id = _get_password_by_id
update_password    = _update_password
delete_password    = _delete_password
count_passwords    = _count_passwords
clear_all_passwords = _clear_all_passwords
soft_delete_password = _soft_delete_password
restore_password   = _restore_password
get_trash          = _get_trash
empty_trash        = _empty_trash
get_vault_stats    = _get_vault_stats
toggle_favorite    = _toggle_favorite
get_by_category    = _get_by_category
get_categories     = _get_categories
get_favorites      = _get_favorites
get_sort_options   = _get_sort_options
get_passwords_sorted = _get_passwords_sorted

class CRUDMixin:
    """Save / get_all / get_by_id / update / delete / trash / stats.
    Операции CRUD: сохранение, получение, обновление, удаление, корзина, статистика.
    CRUD операції: збереження, отримання, оновлення, видалення, кошик, статистика."""

    """Database CRUD operations class with extended fields support."""

    @staticmethod
    def save(label: str, password: str, notes: str = "",
             url: str = "", username: str = "", email: str = "",
             category: str = "", favorite: int = 0, lang: str = None,
             custom_fields: str = "[]", tags: str = "[]") -> int:
        """
        Handle save.
        Обработать save.
        Обробити save.
        """
        return _save_password(label, password, notes, url, username, email, category, favorite, lang, custom_fields, tags)

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """
        Return all.
        Возвращает all.
        Повертає all.
        """
        return _get_all_passwords()

