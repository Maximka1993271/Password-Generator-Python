from __future__ import annotations
# security/master_auth_core.py
"""
Master auth core module for Secure Pass Pro.
Модуль Master auth core для Secure Pass Pro.
Модуль Master auth core для Secure Pass Pro.
"""
"""
Master auth core module for Secure Pass Pro.
Модуль Master auth core для Secure Pass Pro.
Модуль Master auth core для Secure Pass Pro.
"""
"""
Master password authentication - Core class with all methods
100% ORIGINAL CODE - DO NOT MODIFY (Split Version)

Модуль аутентификации мастер-пароля - Основной класс со всеми методами
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ (Разделенная версия)

Модуль аутентифікації майстер-пароля - Основний клас з усіма методами
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ (Розділена версія)
"""

import os
import sys
import hashlib
import hmac
import secrets
import time
import re
import base64
import binascii
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime

from security.master_auth_constants import (
    MASTER_FILE, CONFIG_DIR, PBKDF2_ITERATIONS, PBKDF2_SALT_SIZE,
    ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM, ARGON2_HASH_LEN,
    _ARGON2_OK, PASSWORD_HISTORY_MAX, PASSWORD_HISTORY_HASH_PREFIX,
    PASSWORD_HISTORY_HASH_ITERATIONS, PASSWORD_HISTORY_SALT_BYTES,
    AUDIT_LOG_MAX_ENTRIES, AUDIT_LOG_RETENTION_DAYS, SESSION_TIMEOUT_HOURS,
    MAX_TRUSTED_DEVICES, RECOVERY_CODES_COUNT, RECOVERY_CODE_LENGTH,
    LOCKOUT_FILE, AUDIT_LOG_FILE, PASSWORD_HISTORY_FILE,
    TRUSTED_DEVICES_FILE, RECOVERY_CODES_FILE, SESSIONS_FILE
)

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
except ImportError as e:
    PasswordHasher = None
    VerifyMismatchError = VerificationError = InvalidHashError = Exception

from utils.logger import get_logger

logger = get_logger("master_auth")

from security.master_auth_helpers import (
    _secure_write, _secure_read, _get_device_fingerprint, _get_ip_address,
    _hash_recovery_code, _verify_recovery_code_hash, _get_max_attempts_configurable
)

# Импорт вынесенных структур и исключений для обеспечения обратной совместимости
from security.master_auth_types import (
    AuditEvent, TrustedDevice, Session, RecoveryCode,
    MasterPasswordError, LockoutError, AuditError, SessionError,
    TrustedDeviceError, RecoveryCodeError
)

# Импорт примесей (Mixins)
from security.master_auth_crypto_mixin import MasterAuthCryptoMixin
from security.master_auth_features_mixin import MasterAuthFeaturesMixin


class MasterPassword(MasterAuthCryptoMixin, MasterAuthFeaturesMixin):
    """
    Master password manager with Argon2id hashing and rate limiting.
    
    Менеджер мастер-пароля с хешированием Argon2id и ограничением частоты попыток.
    Менеджер майстер-пароля з хешуванням Argon2id та обмеженням частоти спроб.
    """

    SALT_SIZE = PBKDF2_SALT_SIZE
    PBKDF2_ITERATIONS = PBKDF2_ITERATIONS
    USE_ARGON2 = _ARGON2_OK

    ARGON2_TIME_COST = ARGON2_TIME_COST
    ARGON2_MEMORY_COST = ARGON2_MEMORY_COST
    ARGON2_PARALLELISM = ARGON2_PARALLELISM

    _attempt_count = 0
    _last_attempt_time = 0
    _lockout_until = 0
    _is_permanently_locked = False
    _audit_log: List[Dict[str, Any]] = []

    _cached_config = None
    _skip_2fa_once = False
    _trusted_devices: List[Dict[str, Any]] = []
    _recovery_codes: List[Dict[str, Any]] = []
    _sessions: List[Dict[str, Any]] = []
    _current_session_id: Optional[str] = None

    _password_history: List[str] = []
    _password_history_max = PASSWORD_HISTORY_MAX

    # ==================== VERIFY METHODS ====================

    @classmethod
    def is_set(cls) -> bool:
        """Check if master password is set
        Проверить, установлен ли мастер-пароль
        Перевірити, чи встановлено майстер-пароль"""
        return os.path.exists(MASTER_FILE)

    @classmethod
    def verify(cls, password: str, record_attempt: bool = True, source: str = "unknown") -> bool:
        """Verify master password with rate limiting.
        Проверить мастер-пароль с ограничением частоты попыток.
        Перевірити майстер-пароль з обмеженням частоти спроб."""
        is_allowed, remaining = cls._apply_rate_limit()
        if not is_allowed:
            logger.warning(f"Rate limit applied, locked for {remaining} seconds / Применено ограничение частоты, блокировка на {remaining} секунд / Застосовано обмеження частоти, блокування на {remaining} секунд")
            return False

        if not cls.is_set():
            if record_attempt:
                cls._reset_attempts()
            return True

        try:
            content = _secure_read(MASTER_FILE)
            if content is None:
                logger.error("Failed to read master file / Не удалось прочитать файл мастер-пароля / Не вдалося прочитати файл майстер-пароля")
                if record_attempt:
                    cls._record_failed_attempt(source)
                return False

            version = content[:1]
            rest = content[1:]

            if version == b'\x02':
                stored_hash = rest.decode('utf-8')
                result = cls._verify_argon2(password, stored_hash)
            elif version == b'\x01':
                if len(rest) < cls.SALT_SIZE + 32:
                    logger.error("Invalid master file format / Неверный формат файла мастер-пароля / Невірний формат файлу майстер-пароля")
                    if record_attempt:
                        cls._record_failed_attempt(source)
                    return False
                salt = rest[:cls.SALT_SIZE]
                stored_hash = rest[cls.SALT_SIZE:]
                if len(salt) != cls.SALT_SIZE or len(stored_hash) != 32:
                    logger.error("Invalid salt or hash length / Неверная длина соли или хеша / Невірна довжина солі або хеша")
                    if record_attempt:
                        cls._record_failed_attempt(source)
                    return False
                derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
                result = hmac.compare_digest(derived, stored_hash)
            else:
                logger.error(f"Unknown master file version: {version} / Неизвестная версия файла мастер-пароля: {version} / Невідома версія файлу майстер-пароля: {version}")
                if record_attempt:
                    cls._record_failed_attempt(source)
                return False
        except (OSError, IOError, PermissionError, UnicodeDecodeError, ValueError, TypeError) as e:
            logger.error(f"Error reading master file / Ошибка чтения файла мастер-пароля / Помилка читання файлу майстер-пароля: {e}")
            if record_attempt:
                cls._record_failed_attempt(source)
            return False

        if result:
            if record_attempt:
                cls._reset_attempts()
                cls._log_audit_event("successful_auth", {
                    "source": source,
                    "device_fingerprint": _get_device_fingerprint(),
                    "ip_address": _get_ip_address()
                })
                cls._create_session(source)
        else:
            if record_attempt:
                cls._record_failed_attempt(source)

        return result

    @classmethod
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
            from security.master_auth_helpers import _hide_dir
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
                derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
                _secure_write(MASTER_FILE, b'\x01' + salt + derived)
        except (ValueError, TypeError, RuntimeError, OSError, IOError) as e:
            raise MasterPasswordError(f"Failed to set password / Ошибка установки пароля / Помилка встановлення пароля: {e}")

        cls._reset_attempts()
        cls._log_audit_event("password_set", {"method": "Argon2id" if cls.USE_ARGON2 else "PBKDF2"})

        cls.add_to_history(password_hash)

    @classmethod
    def change_password(cls, old_password: str, new_password: str) -> bool:
        """Change master password.
        Изменить мастер-пароль.
        Змінити майстер-пароль."""
        if not cls.verify(old_password, source="password_change"):
            logger.warning("Password change failed: invalid old password / Ошибка смены пароля: неверный старый пароль / Помилка зміни пароля: невірний старий пароль")
            cls._log_audit_event("failed_attempt", {"source": "password_change", "reason": "invalid_old"})
            return False

        if len(new_password) < 8:
            logger.warning("Password change failed: new password too short / Ошибка смены пароля: новый пароль слишком короткий / Помилка зміни пароля: новий пароль занадто короткий")
            return False

        if cls.is_password_reused(new_password):
            logger.warning("Password change failed: password reuse detected / Ошибка смены пароля: обнаружено повторное использование пароля / Помилка зміни пароля: виявлено повторне використання пароля")
            cls._log_audit_event("failed_attempt", {"source": "password_change", "reason": "password_reuse"})
            return False

        try:
            cls.set_password(new_password)
            logger.info("Password changed successfully / Пароль успешно изменён / Пароль успішно змінено")
            cls._log_audit_event("password_changed", {})
            return True
        except MasterPasswordError as e:
            logger.error(f"Password change error / Ошибка смены пароля / Помилка зміни пароля: {e}")
            return False

    @classmethod
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

        cls._log_audit_event("password_removed", {})

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