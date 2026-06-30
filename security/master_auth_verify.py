"""
Master password authentication - Verify, set, change, remove methods
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import re
import secrets
import hashlib
import hmac
from typing import Optional, Tuple

from security.master_auth_constants import (
    MASTER_FILE, CONFIG_DIR, PBKDF2_ITERATIONS, PBKDF2_SALT_SIZE,
    ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM, ARGON2_HASH_LEN,
    _ARGON2_OK, LOCKOUT_FILE, AUDIT_LOG_FILE, PASSWORD_HISTORY_FILE,
    TRUSTED_DEVICES_FILE, RECOVERY_CODES_FILE, SESSIONS_FILE
)
from security.master_auth_helpers import (
    _secure_write, _secure_read, _hide_dir, _get_device_fingerprint,
    _get_ip_address
)
from security.master_auth_lockout import (
    _apply_rate_limit, _record_failed_attempt, _reset_attempts
)
from security.master_auth_audit import _log_audit_event
from security.master_auth_core import MasterPassword, MasterPasswordError

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
except ImportError as e:
    PasswordHasher = None
    VerifyMismatchError = VerificationError = InvalidHashError = Exception

from utils.logger import get_logger

logger = get_logger("master_auth")


def _derive_key_pbkdf2(cls, password: bytes, salt: bytes) -> bytes:
    """Derive key using PBKDF2 / Выводит ключ с использованием PBKDF2 / Виводить ключ з використанням PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', password, salt, cls.PBKDF2_ITERATIONS, dklen=32)


def _hash_argon2(cls, password: str) -> str:
    """Hash password using Argon2id / Хеширует пароль с использованием Argon2id / Хешує пароль з використанням Argon2id"""
    if not _ARGON2_OK:
        raise RuntimeError("Argon2 is not available / Argon2 недоступен / Argon2 недоступний")
    try:
        _ph = PasswordHasher(
            time_cost=cls.ARGON2_TIME_COST,
            memory_cost=cls.ARGON2_MEMORY_COST,
            parallelism=cls.ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN
        )
        return _ph.hash(password)
    except (ValueError, TypeError, RuntimeError) as e:
        logger.error(f"Argon2 hash error / Ошибка хеширования Argon2 / Помилка хешування Argon2: {e}")
        raise RuntimeError(f"Failed to hash password / Ошибка хеширования пароля / Помилка хешування пароля: {e}")


def _verify_argon2(cls, password: str, stored_hash: str) -> bool:
    """Verify password against Argon2id hash / Проверяет пароль по хешу Argon2id / Перевіряє пароль за хешем Argon2id"""
    try:
        if not _ARGON2_OK:
            return False
        _ph = PasswordHasher(
            time_cost=cls.ARGON2_TIME_COST,
            memory_cost=cls.ARGON2_MEMORY_COST,
            parallelism=cls.ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN
        )
        _ph.verify(stored_hash, password)
        if _ph.check_needs_rehash(stored_hash):
            logger.debug("Password hash needs rehash / Хеш пароля требует перехеширования / Хеш пароля потребує перехешування")
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError, TypeError, ValueError) as e:
        logger.debug(f"Argon2 verification failed / Ошибка верификации Argon2 / Помилка верифікації Argon2: {type(e).__name__}")
        return False


def is_set(cls) -> bool:
    """Check if master password is set
    Проверить, установлен ли мастер-пароль
    Перевірити, чи встановлено майстер-пароль"""
    return os.path.exists(MASTER_FILE)


def verify(cls, password: str, record_attempt: bool = True, source: str = "unknown") -> bool:
    """Verify master password with rate limiting.
    Проверить мастер-пароль с ограничением частоты попыток.
    Перевірити майстер-пароль з обмеженням частоти спроб."""
    is_allowed, remaining = _apply_rate_limit(cls)
    if not is_allowed:
        logger.warning(f"Rate limit applied, locked for {remaining} seconds / Применено ограничение частоты, блокировка на {remaining} секунд / Застосовано обмеження частоти, блокування на {remaining} секунд")
        return False

    if not is_set(cls):
        if record_attempt:
            _reset_attempts(cls)
        return True

    try:
        content = _secure_read(MASTER_FILE)
        if content is None:
            logger.error("Failed to read master file / Не удалось прочитать файл мастер-пароля / Не вдалося прочитати файл майстер-пароля")
            if record_attempt:
                _record_failed_attempt(cls, source)
            return False

        version = content[:1]
        rest = content[1:]

        if version == b'\x02':
            stored_hash = rest.decode('utf-8')
            result = _verify_argon2(cls, password, stored_hash)
        elif version == b'\x01':
            if len(rest) < cls.SALT_SIZE + 32:
                logger.error("Invalid master file format / Неверный формат файла мастер-пароля / Невірний формат файлу майстер-пароля")
                if record_attempt:
                    _record_failed_attempt(cls, source)
                return False
            salt = rest[:cls.SALT_SIZE]
            stored_hash = rest[cls.SALT_SIZE:]
            if len(salt) != cls.SALT_SIZE or len(stored_hash) != 32:
                logger.error("Invalid salt or hash length / Неверная длина соли или хеша / Невірна довжина солі або хеша")
                if record_attempt:
                    _record_failed_attempt(cls, source)
                return False
            derived = _derive_key_pbkdf2(cls, password.encode('utf-8'), salt)
            result = hmac.compare_digest(derived, stored_hash)
        else:
            logger.error(f"Unknown master file version: {version} / Неизвестная версия файла мастер-пароля: {version} / Невідома версія файлу майстер-пароля: {version}")
            if record_attempt:
                _record_failed_attempt(cls, source)
            return False
    except (OSError, IOError, PermissionError, UnicodeDecodeError, ValueError, TypeError) as e:
        logger.error(f"Error reading master file / Ошибка чтения файла мастер-пароля / Помилка читання файлу майстер-пароля: {e}")
        if record_attempt:
            _record_failed_attempt(cls, source)
        return False

    if result:
        if record_attempt:
            _reset_attempts(cls)
            _log_audit_event(cls, "successful_auth", {
                "source": source,
                "device_fingerprint": _get_device_fingerprint(),
                "ip_address": _get_ip_address()
            })
            cls._create_session(source)
    else:
        if record_attempt:
            _record_failed_attempt(cls, source)

    return result


def _create_session(cls, source: str) -> Optional[str]:
    """Create new session for successful authentication
    Создать новую сессию для успешной аутентификации
    Створити нову сесію для успішної аутентифікації"""
    from security.master_auth_constants import SESSION_TIMEOUT_HOURS
    from security.master_auth_core import Session
    from security.master_auth_session import _save_sessions
    from datetime import datetime
    
    try:
        session_id = secrets.token_hex(32)
        now = datetime.now()
        expires_at = now.timestamp() + (SESSION_TIMEOUT_HOURS * 3600)

        session = Session(
            session_id=session_id,
            created_at=now.isoformat(),
            expires_at=datetime.fromtimestamp(expires_at).isoformat(),
            device_id=_get_device_fingerprint(),
            ip_address=_get_ip_address()
        )

        cls._sessions.append(session.to_dict())
        cls._current_session_id = session_id
        _save_sessions(cls)

        logger.debug(f"Session created: {session_id[:16]}... / Сессия создана: {session_id[:16]}... / Сесію створено: {session_id[:16]}...")
        return session_id
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.debug(f"Session creation error / Ошибка создания сессии / Помилка створення сесії: {e}")
        return None


def set_password(cls, password: str) -> None:
    """Set a new master password.
    Установить новый мастер-пароль.
    Встановити новий майстер-пароль."""
    if not password:
        raise MasterPasswordError("Master password must not be empty / Мастер-пароль не должен быть пустым / Майстер-пароль не повинен бути порожнім")

    if len(password) < 8:
        raise MasterPasswordError("Password too short. Minimum 8 characters. / Пароль слишком короткий. Минимум 8 символов. / Пароль занадто короткий. Мінімум 8 символів.")

    if not re.search(r"[A-Za-z]", password):
        raise MasterPasswordError("Password too weak. Add a letter. / Пароль слишком простой. Добавьте букву. / Пароль занадто простий. Додайте літеру.")

    if not re.search(r"[0-9!@#$%^&*()_+=\[\]{};:,.<>/?@%-]", password):
        raise MasterPasswordError("Password too weak. Add a digit or special character. / Пароль слишком простой. Добавьте цифру или спецсимвол. / Пароль занадто простий. Додайте цифру або спецсимвол.")

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _hide_dir(CONFIG_DIR)
    except (PermissionError, OSError, IOError) as e:
        raise MasterPasswordError(f"Cannot create config directory / Не удалось создать директорию конфигурации / Не вдалося створити директорію конфігурації: {e}")

    if cls.is_password_reused(password):
        raise MasterPasswordError("Password was used before. Please choose a different password. / Пароль использовался ранее. Пожалуйста, выберите другой пароль. / Пароль використовувався раніше. Будь ласка, виберіть інший пароль.")
    password_hash = cls._hash_password_for_history(password)

    try:
        if cls.USE_ARGON2:
            _ph = PasswordHasher(
                time_cost=cls.ARGON2_TIME_COST,
                memory_cost=cls.ARGON2_MEMORY_COST,
                parallelism=cls.ARGON2_PARALLELISM,
                hash_len=ARGON2_HASH_LEN
            )
            hashed = _ph.hash(password)
            _secure_write(MASTER_FILE, b'\x02' + hashed.encode('utf-8'))
        else:
            salt = secrets.token_bytes(cls.SALT_SIZE)
            derived = _derive_key_pbkdf2(cls, password.encode('utf-8'), salt)
            _secure_write(MASTER_FILE, b'\x01' + salt + derived)
    except (ValueError, TypeError, RuntimeError, OSError, IOError) as e:
        raise MasterPasswordError(f"Failed to set password / Ошибка установки пароля / Помилка встановлення пароля: {e}")

    _reset_attempts(cls)
    _log_audit_event(cls, "password_set", {"method": "Argon2id" if cls.USE_ARGON2 else "PBKDF2"})

    cls.add_to_history(password_hash)


def change_password(cls, old_password: str, new_password: str) -> bool:
    """Change master password.
    Изменить мастер-пароль.
    Змінити майстер-пароль."""
    if not verify(cls, old_password, source="password_change"):
        logger.warning("Password change failed: invalid old password / Ошибка смены пароля: неверный старый пароль / Помилка зміни пароля: невірний старий пароль")
        _log_audit_event(cls, "failed_attempt", {"source": "password_change", "reason": "invalid_old"})
        return False

    if len(new_password) < 8:
        logger.warning("Password change failed: new password too short / Ошибка смены пароля: новый пароль слишком короткий / Помилка зміни пароля: новий пароль занадто короткий")
        return False

    if cls.is_password_reused(new_password):
        logger.warning("Password change failed: password reuse detected / Ошибка смены пароля: обнаружено повторное использование пароля / Помилка зміни пароля: виявлено повторне використання пароля")
        _log_audit_event(cls, "failed_attempt", {"source": "password_change", "reason": "password_reuse"})
        return False

    try:
        set_password(cls, new_password)
        logger.info("Password changed successfully / Пароль успешно изменён / Пароль успішно змінено")
        _log_audit_event(cls, "password_changed", {})
        return True
    except MasterPasswordError as e:
        logger.error(f"Password change error / Ошибка смены пароля / Помилка зміни пароля: {e}")
        return False


def remove(cls) -> None:
    """Remove master password and all related data
    Удалить мастер-пароль и все связанные данные
    Видалити майстер-пароль та всі пов'язані дані"""
    try:
        if os.path.exists(MASTER_FILE):
            os.remove(MASTER_FILE)
            logger.info("Master password file removed / Файл мастер-пароля удалён / Файл майстер-пароля видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to remove master file / Ошибка удаления файла мастер-пароля / Помилка видалення файлу майстер-пароля: {e}")

    try:
        if os.path.exists(LOCKOUT_FILE):
            os.remove(LOCKOUT_FILE)
            logger.info("Lockout file removed / Файл блокировки удалён / Файл блокування видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove lockout file / Ошибка удаления файла блокировки / Помилка видалення файлу блокування: {e}")

    try:
        if os.path.exists(AUDIT_LOG_FILE):
            os.remove(AUDIT_LOG_FILE)
            logger.info("Audit log file removed / Файл журнала аудита удалён / Файл журналу аудиту видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove audit log file / Ошибка удаления файла аудита / Помилка видалення файлу аудиту: {e}")

    try:
        if os.path.exists(PASSWORD_HISTORY_FILE):
            os.remove(PASSWORD_HISTORY_FILE)
            logger.info("Password history file removed / Файл истории паролей удалён / Файл історії паролів видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove password history / Ошибка удаления истории паролей / Помилка видалення історії паролів: {e}")

    try:
        if os.path.exists(TRUSTED_DEVICES_FILE):
            os.remove(TRUSTED_DEVICES_FILE)
            logger.info("Trusted devices file removed / Файл доверенных устройств удалён / Файл довірених пристроїв видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove trusted devices / Ошибка удаления доверенных устройств / Помилка видалення довірених пристроїв: {e}")

    try:
        if os.path.exists(RECOVERY_CODES_FILE):
            os.remove(RECOVERY_CODES_FILE)
            logger.info("Recovery codes file removed / Файл резервных кодов удалён / Файл резервних кодів видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove recovery codes / Ошибка удаления резервных кодов / Помилка видалення резервних кодів: {e}")

    try:
        if os.path.exists(SESSIONS_FILE):
            os.remove(SESSIONS_FILE)
            logger.info("Sessions file removed / Файл сессий удалён / Файл сесій видалено")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Failed to remove sessions / Ошибка удаления сессий / Помилка видалення сесій: {e}")

    cls._attempt_count = 0
    cls._lockout_until = 0
    cls._is_permanently_locked = False
    cls._last_attempt_time = 0
    cls._audit_log = []
    cls._password_history = []
    cls._trusted_devices = []
    cls._recovery_codes = []
    cls._sessions = []
    cls._current_session_id = None

    _log_audit_event(cls, "password_removed", {})

    try:
        if cls._cached_config:
            cls._cached_config.set_2fa_enabled(False)
            cls._cached_config.set_2fa_secret("")
            cls._cached_config.set_2fa_backup_hashes([])
            cls._cached_config.set_2fa_setup_completed(False)
            cls._cached_config.save()
            logger.info("2FA disabled in config / 2FA отключена в конфиге / 2FA вимкнено в конфігу")
    except (AttributeError, OSError, TypeError, ValueError) as e:
        logger.debug(f"Error disabling 2FA / Ошибка отключения 2FA / Помилка вимкнення 2FA: {e}")

    try:
        from security.totp import get_totp_manager
        manager = get_totp_manager()
        manager.disable_2fa()
        logger.info("2FA disabled via TOTP / 2FA отключена через TOTP / 2FA вимкнено через TOTP")
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.debug(f"TOTP disable error / Ошибка отключения TOTP / Помилка вимкнення TOTP: {e}")

    logger.info("Master password removed successfully / Мастер-пароль успешно удалён / Майстер-пароль успішно видалено")