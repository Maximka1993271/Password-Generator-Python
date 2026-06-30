"""
Master password authentication - Password history
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List

from security.master_auth_constants import (
    PASSWORD_HISTORY_FILE, PASSWORD_HISTORY_MAX, PASSWORD_HISTORY_HASH_PREFIX,
    PASSWORD_HISTORY_HASH_ITERATIONS, PASSWORD_HISTORY_SALT_BYTES
)
from security.master_auth_helpers import _secure_write, _secure_read

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_password_history(cls) -> None:
    """Save password history / Сохранить историю паролей / Зберегти історію паролів"""
    try:
        history_data = {
            "entries": cls._password_history,
            "last_update": datetime.now().isoformat(),
            "max_entries": PASSWORD_HISTORY_MAX
        }
        _secure_write(PASSWORD_HISTORY_FILE, json.dumps(history_data, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save password history / Ошибка сохранения истории паролей / Помилка збереження історії паролів: {e}")


def _load_password_history(cls) -> None:
    """Load password history / Загрузить историю паролей / Завантажити історію паролів"""
    if not os.path.exists(PASSWORD_HISTORY_FILE):
        return

    try:
        content = _secure_read(PASSWORD_HISTORY_FILE)
        if content:
            history_data = json.loads(content.decode('utf-8'))
            entries = history_data.get("entries", [])
            if isinstance(entries, list):
                cls._password_history = entries[-PASSWORD_HISTORY_MAX:]
            logger.debug(f"Loaded {len(cls._password_history)} password history entries / Загружено {len(cls._password_history)} записей истории паролей / Завантажено {len(cls._password_history)} записів історії паролів")
    except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load password history / Ошибка загрузки истории паролей / Помилка завантаження історії паролів: {e}")


def _hash_password_for_history(cls, password: str) -> str:
    """Hash password for reuse history with a per-entry salt.
    Хеширует пароль для истории повторного использования с солью для каждой записи.
    Хешує пароль для історії повторного використання з сіллю для кожного запису."""
    salt = secrets.token_bytes(PASSWORD_HISTORY_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        str(password).encode('utf-8'),
        salt,
        PASSWORD_HISTORY_HASH_ITERATIONS,
        dklen=32
    )
    return (
        f"{PASSWORD_HISTORY_HASH_PREFIX}${PASSWORD_HISTORY_HASH_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def _verify_password_history_entry(cls, password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against new and legacy history entries.
    Проверяет открытый пароль против новых и старых записей истории.
    Перевіряє відкритий пароль проти нових та старих записів історії."""
    import base64
    import binascii
    try:
        stored_hash = str(stored_hash or "")
        if stored_hash.startswith(f"{PASSWORD_HISTORY_HASH_PREFIX}$"):
            _, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
            salt = base64.b64decode(salt_b64, validate=True)
            expected = base64.b64decode(digest_b64, validate=True)
            computed = hashlib.pbkdf2_hmac(
                'sha256',
                str(password).encode('utf-8'),
                salt,
                int(iterations),
                dklen=len(expected)
            )
            return hmac.compare_digest(computed, expected)

        legacy_salt = b"securepasspro_history_salt"
        legacy = hashlib.pbkdf2_hmac(
            'sha256',
            str(password).encode('utf-8'),
            legacy_salt,
            10000,
            dklen=32
        ).hex()
        return hmac.compare_digest(legacy, stored_hash.lower())
    except (TypeError, ValueError, binascii.Error, KeyError, IndexError) as e:
        logger.debug(f"Password history verification error / Ошибка проверки истории паролей / Помилка перевірки історії паролів: {e}")
        return False


def add_to_history(cls, password_hash: str) -> None:
    """Add password hash to history
    Добавить хеш пароля в историю
    Додати хеш пароля в історію"""
    try:
        cls._password_history.append(password_hash)
        if len(cls._password_history) > cls._password_history_max:
            cls._password_history = cls._password_history[-cls._password_history_max:]
        _save_password_history(cls)
    except (TypeError, ValueError, OSError, AttributeError) as e:
        logger.debug(f"Failed to add to history / Ошибка добавления в историю / Помилка додавання в історію: {e}")


def is_password_reused(cls, password: str) -> bool:
    """Check if password was used before
    Проверить, использовался ли пароль ранее
    Перевірити, чи використовувався пароль раніше"""
    candidate = str(password)
    for stored_hash in cls._password_history:
        stored_hash = str(stored_hash)
        if hmac.compare_digest(candidate, stored_hash):
            return True
        if _verify_password_history_entry(cls, candidate, stored_hash):
            return True
    return False


def clear_history(cls) -> None:
    """Clear password history
    Очистить историю паролей
    Очистити історію паролів"""
    cls._password_history = []
    _save_password_history(cls)
    logger.debug("Password history cleared / История паролей очищена / Історію паролів очищено")