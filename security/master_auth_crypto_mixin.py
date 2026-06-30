from __future__ import annotations
# security/master_auth_crypto_mixin.py
"""
Master auth crypto mixin module for Secure Pass Pro.
Модуль Master auth crypto mixin для Secure Pass Pro.
Модуль Master auth crypto mixin для Secure Pass Pro.
"""
"""
Master auth crypto mixin module for Secure Pass Pro.
Модуль Master auth crypto mixin для Secure Pass Pro.
Модуль Master auth crypto mixin для Secure Pass Pro.
"""
"""
Master password authentication - Crypto mixin (hashing, key derivation, password history)
Миксин криптографии для аутентификации мастер-пароля (хеширование, вывод ключей, история паролей)
Міксин криптографії для аутентифікації майстер-пароля (хешування, виведення ключів, історія паролів)
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
    MAX_TRUSTED_DEVICES, RECOVERY_CODES_COUNT, RECOVERY_CODE_LENGTH
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
    _get_device_fingerprint, _get_ip_address, _get_max_attempts_configurable
)
from security.master_auth_types import AuditEvent

class MasterAuthCryptoMixin:
    """Crypto methods for master password authentication
    Криптографические методы для аутентификации мастер-пароля
    Криптографічні методи для аутентифікації майстер-пароля"""

    @classmethod
    def get_max_attempts(cls) -> int:
        """Get configurable maximum attempts value.
        Получить настраиваемое значение максимальных попыток.
        Отримати налаштовуване значення максимальних спроб."""
        return _get_max_attempts_configurable()

    # ==================== PASSWORD HISTORY METHODS ====================

    @classmethod
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

    @classmethod
    def _verify_password_history_entry(cls, password: str, stored_hash: str) -> bool:
        """Verify a plaintext password against new and legacy history entries.
        Проверяет открытый пароль против новых и старых записей истории.
        Перевіряє відкритий пароль проти нових та старих записів історії."""
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

    @classmethod
    def add_to_history(cls, password_hash: str) -> None:
        """Add password hash to history
        Добавить хеш пароля в историю
        Додати хеш пароля в історію"""
        try:
            cls._password_history.append(password_hash)
            if len(cls._password_history) > cls._password_history_max:
                cls._password_history = cls._password_history[-cls._password_history_max:]
            from security.master_auth_history import _save_password_history
            _save_password_history(cls)
        except (TypeError, ValueError, OSError, AttributeError) as e:
            logger.debug(f"Failed to add to history / Ошибка добавления в историю / Помилка додавання в історію: {e}")

    @classmethod
    def is_password_reused(cls, password: str) -> bool:
        """Check if password was used before
        Проверить, использовался ли пароль ранее
        Перевірити, чи використовувався пароль раніше"""
        candidate = str(password)
        for stored_hash in cls._password_history:
            stored_hash = str(stored_hash)
            if hmac.compare_digest(candidate, stored_hash):
                return True
            if cls._verify_password_history_entry(candidate, stored_hash):
                return True
        return False

    @classmethod
    def clear_history(cls) -> None:
        """Clear password history
        Очистить историю паролей
        Очистити історію паролів"""
        cls._password_history = []
        from security.master_auth_history import _save_password_history
        _save_password_history(cls)
        logger.debug("Password history cleared / История паролей очищена / Історію паролів очищено")

    # ==================== KEY DERIVATION METHODS ====================

    @classmethod
    def _derive_key_pbkdf2(cls, password: bytes, salt: bytes) -> bytes:
        """Derive key using PBKDF2 / Выводит ключ с использованием PBKDF2 / Виводить ключ з використанням PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', password, salt, cls.PBKDF2_ITERATIONS, dklen=32)

    @classmethod
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

    @classmethod
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

    # ==================== LOCKOUT METHODS ====================

    @classmethod
    def _get_lockout_delay(cls, attempts: int) -> int:
        """Get lockout delay for given attempt count
        Получить задержку блокировки для данного количества попыток
        Отримати затримку блокування для даної кількості спроб"""
        from security.master_auth_constants import LOCKOUT_TIMES
        return LOCKOUT_TIMES.get(attempts, LOCKOUT_TIMES[min(attempts, max(LOCKOUT_TIMES.keys()))])

    @classmethod
    def _apply_rate_limit(cls) -> Tuple[bool, int]:
        """Apply rate limiting based on attempts
        Применить ограничение частоты на основе попыток
        Застосувати обмеження частоти на основі спроб"""
        current_time = time.time()
        max_attempts = cls.get_max_attempts()

        if cls._is_permanently_locked:
            return False, -1

        if cls._lockout_until > current_time:
            return False, int(cls._lockout_until - current_time)

        if current_time - cls._last_attempt_time > 600:
            cls._attempt_count = 0
            cls._lockout_until = 0
            from security.master_auth_lockout import _save_lockout_state
            _save_lockout_state(cls)

        return True, 0

    @classmethod
    def _record_failed_attempt(cls, source: str = "unknown") -> int:
        """Record a failed authentication attempt
        Записать неудачную попытку аутентификации
        Записати невдалу спробу аутентифікації"""
        max_attempts = cls.get_max_attempts()

        cls._attempt_count += 1
        cls._last_attempt_time = time.time()

        cls._log_audit_event("failed_attempt", {
            "attempts": cls._attempt_count,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "device_fingerprint": _get_device_fingerprint(),
            "ip_address": _get_ip_address()
        })

        if cls._attempt_count >= max_attempts:
            cls._is_permanently_locked = True
            from security.master_auth_lockout import _save_lockout_state
            _save_lockout_state(cls)
            logger.warning(f"Permanent lockout triggered after {cls._attempt_count} attempts / Постоянная блокировка после {cls._attempt_count} попыток / Постійне блокування після {cls._attempt_count} спроб")
            return -1

        delay = cls._get_lockout_delay(cls._attempt_count)
        if delay > 0:
            cls._lockout_until = cls._last_attempt_time + delay
            logger.warning(f"Lockout for {delay} seconds after {cls._attempt_count} attempts / Блокировка на {delay} секунд после {cls._attempt_count} попыток / Блокування на {delay} секунд після {cls._attempt_count} спроб")

        from security.master_auth_lockout import _save_lockout_state
        _save_lockout_state(cls)
        return delay

    @classmethod
    def _reset_attempts(cls) -> None:
        """Reset all attempt counters
        Сбросить все счетчики попыток
        Скинути всі лічильники спроб"""
        cls._attempt_count = 0
        cls._lockout_until = 0
        cls._is_permanently_locked = False
        cls._last_attempt_time = 0
        from security.master_auth_lockout import _save_lockout_state
        _save_lockout_state(cls)
        logger.debug("Attempts reset / Счётчики попыток сброшены / Лічильники спроб скинуто")

    @classmethod
    def get_remaining_lockout_time(cls) -> int:
        """Get remaining lockout time in seconds
        Получить оставшееся время блокировки в секундах
        Отримати час блокування в секундах"""
        if cls._is_permanently_locked:
            return -1
        if cls._lockout_until <= time.time():
            return 0
        return int(cls._lockout_until - time.time())

    @classmethod
    def get_attempts_remaining(cls) -> int:
        """Get number of remaining attempts before lockout
        Получить количество оставшихся попыток до блокировки
        Отримати кількість спроб до блокування"""
        max_attempts = cls.get_max_attempts()
        if cls._is_permanently_locked:
            return 0
        if cls._attempt_count >= max_attempts:
            return 0
        return max_attempts - cls._attempt_count

    @classmethod
    def is_permanently_locked(cls) -> bool:
        """Check if permanently locked
        Проверить, заблокирована ли программа навсегда
        Перевірити, чи заблоковано програму назавжди"""
        return cls._is_permanently_locked

    @classmethod
    def get_lockout_info(cls) -> dict:
        """Get detailed lockout information
        Получить подробную информацию о блокировке
        Отримати детальну інформацію про блокування"""
        remaining = cls.get_remaining_lockout_time()
        max_attempts = cls.get_max_attempts()
        return {
            'attempts': cls._attempt_count,
            'max_attempts': max_attempts,
            'remaining_attempts': cls.get_attempts_remaining(),
            'lockout_seconds': remaining if remaining > 0 else 0,
            'is_locked': remaining > 0,
            'is_permanently_locked': cls._is_permanently_locked
        }

    @classmethod
    def reset_lockout(cls) -> bool:
        """Reset lockout state (admin only)
        Сбросить состояние блокировки (только администратор)
        Скинути стан блокування (тільки адміністратор)"""
        if not cls.is_permanently_locked() and cls.get_remaining_lockout_time() == 0:
            return True

        cls._reset_attempts()
        cls._log_audit_event("lockout_reset", {"source": "admin"})
        logger.info("Lockout state reset / Состояние блокировки сброшено / Стан блокування скинуто")
        return True

    # ==================== AUDIT METHODS ====================

    @classmethod
    def _cleanup_audit_log(cls) -> None:
        """Clean old audit log entries
        Очистить старые записи аудита
        Очистити старі записи аудиту"""
        try:
            current_time = datetime.now()
            cutoff_time = current_time.timestamp() - (AUDIT_LOG_RETENTION_DAYS * 24 * 3600)

            filtered_log = []
            for entry in cls._audit_log:
                try:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00")).timestamp()
                    if entry_time > cutoff_time:
                        filtered_log.append(entry)
                except (ValueError, TypeError, KeyError) as e:
                    filtered_log.append(entry)

            if len(filtered_log) > AUDIT_LOG_MAX_ENTRIES:
                filtered_log = filtered_log[-AUDIT_LOG_MAX_ENTRIES:]

            cls._audit_log = filtered_log
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.debug(f"Audit log cleanup error / Ошибка очистки журнала аудита / Помилка очищення журналу аудиту: {e}")

    @classmethod
    def _log_audit_event(cls, event_type: str, details: Dict[str, Any]) -> None:
        """Log an audit event
        Записать событие аудита
        Записати подію аудиту"""
        try:
            event = {
                "event": event_type,
                "timestamp": datetime.now().isoformat(),
                "details": details.copy() if details else {}
            }
            cls._audit_log.append(event)

            if len(cls._audit_log) > AUDIT_LOG_MAX_ENTRIES:
                cls._audit_log = cls._audit_log[-AUDIT_LOG_MAX_ENTRIES:]

            from security.master_auth_audit import _save_audit_log
            try:
                _save_audit_log(cls)
            except (OSError, IOError, PermissionError) as e:
                logger.debug(f"Audit log save error / Ошибка сохранения журнала аудита / Помилка збереження журналу аудиту: {e}")
        except (TypeError, ValueError, KeyError, AttributeError) as e:
            logger.debug(f"Audit logging error / Ошибка записи аудита / Помилка запису аудиту: {e}")

    @classmethod
    def get_audit_log(cls) -> List[Dict[str, Any]]:
        """Get audit log entries
        Получить записи журнала аудита
        Отримати записи журналу аудиту"""
        return cls._audit_log.copy()

    @classmethod
    def clear_audit_log(cls) -> bool:
        """Clear audit log
        Очистить журнал аудита
        Очистити журнал аудиту"""
        try:
            cls._audit_log = []
            from security.master_auth_audit import _save_audit_log
            _save_audit_log(cls)
            logger.info("Audit log cleared / Журнал аудита очищен / Журнал аудиту очищено")
            return True
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to clear audit log / Ошибка очистки журнала аудита / Помилка очищення журналу аудиту: {e}")
            return False