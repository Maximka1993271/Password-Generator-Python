"""
Password database query interface — public API.
Интерфейс запросов к базе паролей — публичный API.
Інтерфейс запитів до бази паролів — публічний API.

Split layout
────────────
storage/database_crud.py    — CRUDMixin + all private implementation functions
storage/database_search.py  — SearchMixin (search / categories / favourites / sort)
storage/database_queries.py — DatabaseQueries class (inherits both mixins)
                              + re-exports all public functions for backward compat
"""
from __future__ import annotations

# ── Implementation modules (bring their module-level functions into scope) ──
from storage.database_crud import (   # noqa: F401
    # Connection / path helpers (originally in database_base, proxied here)
    get_db_path,
    get_connection,
    is_encrypted_value,
    encrypt_value_for_storage,
    decrypt_value_from_storage,
    decrypt_record,
    _db_lock,
    # Private CRUD functions (needed by legacy imports)
    _save_password,
    _get_all_passwords,
    _search_passwords,
    _get_password_by_id,
    _update_password,
    _delete_password,
    _count_passwords,
    _clear_all_passwords,
    _soft_delete_password,
    _restore_password,
    _get_trash,
    _empty_trash,
    _pwd_age_days,
    _get_vault_stats,
    _toggle_favorite,
    _get_by_category,
    _get_categories,
    _get_favorites,
    _get_sort_options,
    _get_passwords_sorted,
    # Mixin class
    CRUDMixin,
)

from storage.database_search import SearchMixin   # noqa: F401


class DatabaseQueries(CRUDMixin, SearchMixin):
    """Full password-database query interface.
    Полный интерфейс запросов к базе паролей.
    Повний інтерфейс запитів до бази паролів.

    File layout
    ───────────
    database_crud.py    — CRUDMixin   (save / get / update / delete / trash)
    database_search.py  — SearchMixin (search / categories / favourites / sort)
    database_queries.py — DatabaseQueries (this file) + re-exports all functions
    """
    pass
