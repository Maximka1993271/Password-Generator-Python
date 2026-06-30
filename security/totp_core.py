"""
TOTP (Time-based One-Time Password) core class for two-factor authentication
Compatible with Google Authenticator, Authy, Microsoft Authenticator and others

TOTP (Time-based One-Time Password) основной класс для двухфакторной аутентификации
Совместим с Google Authenticator, Authy, Microsoft Authenticator и другими

TOTP (Time-based One-Time Password) основний клас для двофакторної аутентифікації
Сумісний з Google Authenticator, Authy, Microsoft Authenticator та іншими

FIXED: Added missing imports (dataclass)
Исправлено: Добавлены недостающие импорты (dataclass)
Виправлено: Додано відсутні імпорти (dataclass)
"""
from __future__ import annotations

import os
import time
import base64
import hashlib
import hmac
import struct
import secrets
import binascii
import json
import threading
from typing import Optional, Tuple, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict

# ==================== LOGGER ====================

from utils.logger import get_logger

logger = get_logger("totp")

# ==================== CONSTANTS ====================

DEFAULT_INTERVAL = 30
DEFAULT_DIGITS = 6
DEFAULT_ALGORITHM = "SHA1"

MAX_VERIFY_ATTEMPTS = 5
VERIFY_ATTEMPT_WINDOW = 60

# Anti-replay cache size
ANTI_REPLAY_CACHE_SIZE = 100
ANTI_REPLAY_EXPIRY_SECONDS = 300

# Cleanup interval for cache
CACHE_CLEANUP_INTERVAL = 60

# Recovery codes
RECOVERY_CODES_COUNT = 10
RECOVERY_CODE_LENGTH = 8
RECOVERY_CODE_HASH_PREFIX = "pbkdf2_sha256"
RECOVERY_CODE_HASH_ITERATIONS = 200000
RECOVERY_CODE_SALT_BYTES = 16

# Trusted devices
TRUSTED_DEVICE_TOKEN_EXPIRY = 30 * 24 * 3600
MAX_TRUSTED_DEVICES = 5
TRUSTED_DEVICES_FILE = "trusted_devices.json"


class TOTPError(Exception):
    """TOTP error / Ошибка TOTP / Помилка TOTP"""
    pass


class TOTPInvalidSecretError(TOTPError):
    """Invalid TOTP secret / Неверный секрет TOTP / Невірний секрет TOTP"""
    pass


class TOTPRateLimitError(TOTPError):
    """Rate limit exceeded / Превышено ограничение частоты / Перевищено обмеження частоти"""
    pass


class TOTPReplayError(TOTPError):
    """Replay attack detected / Обнаружена атака повторного воспроизведения / Виявлено атаку повторного відтворення"""
    pass


@dataclass
class TrustedDeviceToken:
    """Trusted device token structure / Структура токена доверенного устройства / Структура токена довіреного пристрою"""
    device_id: str
    device_name: str
    token_hash: str
    created_at: str
    expires_at: str
    last_used: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustedDeviceToken':
        """
        Handle from dict.
        Обработать from dict.
        Обробити from dict.
        """
        return cls(**data)


@dataclass
class RecoveryCode:
    """Recovery code structure / Структура резервного кода / Структура резервного коду"""
    code_hash: str
    created_at: str
    used: bool = False
    used_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryCode':
        """
        Handle from dict.
        Обработать from dict.
        Обробити from dict.
        """
        return cls(**data)


class TOTP:
    """
    Time-based One-Time Password generator with anti-replay protection
    
    Генератор одноразовых паролей на основе времени с защитой от повторного воспроизведения
    Генератор одноразових паролів на основі часу із захистом від повторного відтворення
    """

    def __init__(self, secret: Optional[str] = None, digits: int = DEFAULT_DIGITS,
                 interval: int = DEFAULT_INTERVAL, algorithm: str = DEFAULT_ALGORITHM):
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.digits = digits
        self.interval = interval
        self.algorithm = algorithm.upper()

        # Anti-replay cache
        self._used_codes: Dict[str, float] = {}
        self._used_codes_lock = threading.RLock()

        # Rate limiting
        self._verify_attempts: Dict[str, List[float]] = {}
        self._verify_attempts_lock = threading.RLock()

        # Trusted devices
        self._trusted_devices: Dict[str, TrustedDeviceToken] = {}
        self._trusted_devices_lock = threading.RLock()
        self._trusted_devices_file: Optional[str] = None

        # Recovery codes
        self._recovery_codes: List[RecoveryCode] = []
        self._recovery_codes_lock = threading.RLock()

        # Track last cleanup time for automatic cache cleanup
        self._last_cache_cleanup = time.time()

        if secret is None:
            self.secret = self.generate_secret()
        else:
            self.secret = secret.upper().replace(" ", "").replace("-", "")
            logger.debug(f"Secret set (length: {len(self.secret)}) / Секрет установлен (длина: {len(self.secret)}) / Секрет встановлено (довжина: {len(self.secret)})")

        self._validate_secret()

    def _cleanup_expired_codes(self) -> int:
        """Clean up expired codes from anti-replay cache.
        Очищает просроченные коды из кэша защиты от повторного воспроизведения.
        Очищує прострочені коди з кешу захисту від повторного відтворення."""
        current_time = time.time()
        removed_count = 0

        with self._used_codes_lock:
            expired = []
            for code_hash, stored_time in self._used_codes.items():
                if current_time - stored_time > ANTI_REPLAY_EXPIRY_SECONDS:
                    expired.append(code_hash)

            for expired_hash in expired:
                del self._used_codes[expired_hash]
                removed_count += 1

            if len(self._used_codes) > ANTI_REPLAY_CACHE_SIZE:
                sorted_items = sorted(self._used_codes.items(), key=lambda x: x[1])
                to_remove = len(self._used_codes) - ANTI_REPLAY_CACHE_SIZE
                for i in range(to_remove):
                    if i < len(sorted_items):
                        del self._used_codes[sorted_items[i][0]]
                        removed_count += 1

        if removed_count > 0:
            logger.debug(f"Cleaned up {removed_count} expired codes from anti-replay cache / Очищено {removed_count} просроченных кодов из кэша защиты от повторного воспроизведения / Очищено {removed_count} прострочених кодів з кешу захисту від повторного відтворення")

        return removed_count

    def _auto_cleanup_if_needed(self) -> None:
        """Trigger automatic cleanup if interval passed
        Запускает автоматическую очистку, если интервал прошёл
        Запускає автоматичне очищення, якщо інтервал минув"""
        current_time = time.time()
        if current_time - self._last_cache_cleanup > CACHE_CLEANUP_INTERVAL:
            self._cleanup_expired_codes()
            self._last_cache_cleanup = current_time

    def _validate_secret(self) -> None:
        """Validate TOTP secret format / Проверяет формат секрета TOTP / Перевіряє формат секрету TOTP"""
        import re
        if not re.match(r'^[A-Z2-7]+$', self.secret):
            logger.warning("Invalid TOTP secret format - validation failed / Неверный формат секрета TOTP - проверка не пройдена / Невірний формат секрету TOTP - перевірку не пройдено")

    @staticmethod
    def generate_secret(length: int = 16) -> str:
        """Generate random secret key in base32
        Генерирует случайный секретный ключ в base32
        Генерує випадковий секретний ключ у base32"""
        try:
            random_bytes = secrets.token_bytes(length)
            secret = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
            logger.debug(f"Generated new TOTP secret (length: {len(secret)}) / Сгенерирован новый секрет TOTP (длина: {len(secret)}) / Згенеровано новий секрет TOTP (довжина: {len(secret)})")
            return secret
        except (ValueError, TypeError, binascii.Error) as e:
            logger.error(f"Failed to generate secret / Ошибка генерации секрета / Помилка генерації секрету: {e}")
            raise TOTPError(f"Secret generation failed / Ошибка генерации секрета / Помилка генерації секрету: {e}")

    @staticmethod
    def get_provisioning_uri(secret: str, account_name: str, issuer_name: str = "SecurePassPro") -> str:
        """Get provisioning URI for QR code
        Получить URI для подготовки QR-кода
        Отримати URI для підготовки QR-коду"""
        from urllib.parse import quote
        secret_clean = secret.upper().replace(" ", "").replace("-", "")
        uri = f"otpauth://totp/{quote(issuer_name)}:{quote(account_name)}?secret={secret_clean}&issuer={quote(issuer_name)}&period=30&digits=6"
        logger.debug(f"Generated provisioning URI for {account_name} / Сгенерирован URI подготовки для {account_name} / Згенеровано URI підготовки для {account_name}")
        return uri

    def _get_hotp_token(self, counter: int) -> str:
        """Generate HOTP token for given counter
        Генерирует HOTP токен для заданного счётчика
        Генерує HOTP токен для заданого лічильника"""
        try:
            clean_secret = self.secret.replace(" ", "").replace("-", "")
            padding = (8 - len(clean_secret) % 8) % 8
            secret_padded = clean_secret + '=' * padding
            key = base64.b32decode(secret_padded)
        except (binascii.Error, ValueError, TypeError) as e:
            logger.error(f"Failed to decode secret / Ошибка декодирования секрета / Помилка декодування секрету: {e}")
            raise TOTPInvalidSecretError(f"Secret decoding failed / Ошибка декодирования секрета / Помилка декодування секрету: {e}")

        counter_bytes = struct.pack(">Q", counter)

        try:
            if self.algorithm == "SHA1":
                h = hmac.new(key, counter_bytes, hashlib.sha1).digest()
            elif self.algorithm == "SHA256":
                h = hmac.new(key, counter_bytes, hashlib.sha256).digest()
            elif self.algorithm == "SHA512":
                h = hmac.new(key, counter_bytes, hashlib.sha512).digest()
            else:
                raise TOTPError(f"Unsupported algorithm: {self.algorithm} / Неподдерживаемый алгоритм: {self.algorithm} / Непідтримуваний алгоритм: {self.algorithm}")
        except (TypeError, ValueError) as e:
            logger.error(f"HMAC computation failed / Ошибка вычисления HMAC / Помилка обчислення HMAC: {e}")
            raise TOTPError(f"HMAC failed / Ошибка HMAC / Помилка HMAC: {e}")

        offset = h[-1] & 0x0F
        code = (
            ((h[offset] & 0x7F) << 24) |
            ((h[offset + 1] & 0xFF) << 16) |
            ((h[offset + 2] & 0xFF) << 8) |
            (h[offset + 3] & 0xFF)
        )

        code_str = str(code % (10 ** self.digits)).zfill(self.digits)
        return code_str

    def generate_code(self, timestamp: Optional[float] = None) -> str:
        """Generate TOTP code for given timestamp (or current time)
        Генерирует TOTP код для заданной метки времени (или текущего времени)
        Генерує TOTP код для заданої позначки часу (або поточного часу)"""
        if timestamp is None:
            timestamp = time.time()
        counter = int(timestamp // self.interval)
        return self._get_hotp_token(counter)

    def get_current_code(self) -> str:
        """Get current valid code / Получить текущий действующий код / Отримати поточний діючий код"""
        return self.generate_code()

    def _check_rate_limit(self, source: str) -> bool:
        """Check if rate limit is exceeded for source
        Проверяет, превышено ли ограничение частоты для источника
        Перевіряє, чи перевищено обмеження частоти для джерела"""
        self._auto_cleanup_if_needed()

        current_time = time.time()

        with self._verify_attempts_lock:
            if source in self._verify_attempts:
                self._verify_attempts[source] = [
                    t for t in self._verify_attempts[source]
                    if current_time - t < VERIFY_ATTEMPT_WINDOW
                ]
            attempts = len(self._verify_attempts.get(source, []))

        if attempts >= MAX_VERIFY_ATTEMPTS:
            logger.warning(f"Rate limit exceeded for source: {source[:20]}... / Превышено ограничение частоты для источника: {source[:20]}... / Перевищено обмеження частоти для джерела: {source[:20]}...")
            return False
        return True

    def _record_attempt(self, source: str) -> None:
        """Record verification attempt for rate limiting
        Записывает попытку верификации для ограничения частоты
        Записує спробу верифікації для обмеження частоти"""
        current_time = time.time()

        with self._verify_attempts_lock:
            if source not in self._verify_attempts:
                self._verify_attempts[source] = []
            self._verify_attempts[source].append(current_time)

            if len(self._verify_attempts[source]) > MAX_VERIFY_ATTEMPTS * 2:
                self._verify_attempts[source] = self._verify_attempts[source][-MAX_VERIFY_ATTEMPTS:]

    def _is_code_reused(self, code: str, timestamp: Optional[float] = None) -> bool:
        """Check if code was already used (anti-replay protection)
        Проверяет, использовался ли код ранее (защита от повторного воспроизведения)
        Перевіряє, чи використовувався код раніше (захист від повторного відтворення)"""
        if timestamp is None:
            timestamp = time.time()

        time_window = DEFAULT_INTERVAL * 2

        with self._used_codes_lock:
            code_hash = hashlib.sha256(code.encode()).hexdigest()

            if code_hash in self._used_codes:
                code_time = self._used_codes[code_hash]
                if timestamp - code_time <= time_window:
                    logger.warning(f"Replay attack detected: code already used / Обнаружена атака повторного воспроизведения: код уже использован / Виявлено атаку повторного відтворення: код вже використано")
                    return True

        return False

    def _mark_code_used(self, code: str, timestamp: Optional[float] = None) -> None:
        """Mark code as used (anti-replay protection)
        Отмечает код как использованный (защита от повторного воспроизведения)
        Позначає код як використаний (захист від повторного відтворення)"""
        if timestamp is None:
            timestamp = time.time()

        code_hash = hashlib.sha256(code.encode()).hexdigest()

        with self._used_codes_lock:
            self._used_codes[code_hash] = timestamp

            if len(self._used_codes) > ANTI_REPLAY_CACHE_SIZE:
                sorted_items = sorted(self._used_codes.items(), key=lambda x: x[1])
                to_remove = len(self._used_codes) - ANTI_REPLAY_CACHE_SIZE
                for i in range(to_remove):
                    if i < len(sorted_items):
                        del self._used_codes[sorted_items[i][0]]

    def verify(self, code: str, timestamp: Optional[float] = None,
               window: int = 2, source: str = "unknown") -> Tuple[bool, int]:
        """
        Verify TOTP code with time drift window and anti-replay protection.
        
        Проверяет TOTP код с учётом временного дрейфа и защитой от повторного воспроизведения.
        Перевіряє TOTP код з урахуванням часового дрейфу та захистом від повторного відтворення.
        """
        if not self._check_rate_limit(source):
            raise TOTPRateLimitError(f"Rate limit exceeded for {source[:20]} / Превышено ограничение частоты для {source[:20]} / Перевищено обмеження частоти для {source[:20]}")

        self._record_attempt(source)

        if timestamp is None:
            timestamp = time.time()

        try:
            code_clean = ''.join(filter(str.isdigit, str(code)))
        except (TypeError, AttributeError) as e:
            logger.debug(f"Code cleaning error / Ошибка очистки кода / Помилка очищення коду: {e}")
            return False, 0

        if len(code_clean) != self.digits:
            logger.warning(f"Invalid code length: expected {self.digits}, got {len(code_clean)} / Неверная длина кода: ожидалось {self.digits}, получено {len(code_clean)} / Невірна довжина коду: очікувалось {self.digits}, отримано {len(code_clean)}")
            return False, 0

        if self._is_code_reused(code_clean, timestamp):
            logger.warning(f"Replay attack detected from {source[:20]} / Обнаружена атака повторного воспроизведения от {source[:20]} / Виявлено атаку повторного відтворення від {source[:20]}")
            return False, 0

        for drift in range(-window, window + 1):
            test_timestamp = timestamp + (drift * self.interval)
            expected_code = self.generate_code(test_timestamp)
            if hmac.compare_digest(code_clean, expected_code):
                logger.debug(f"TOTP verification successful (drift={drift}) / Верификация TOTP успешна (дрейф={drift}) / Верифікацію TOTP успішно (дрейф={drift})")
                self._mark_code_used(code_clean, test_timestamp)
                return True, drift

        logger.warning(f"TOTP verification failed for source: {source[:20]} / Верификация TOTP не удалась для источника: {source[:20]} / Верифікацію TOTP не вдалося для джерела: {source[:20]}")
        return False, 0

    def get_time_remaining(self, timestamp: Optional[float] = None) -> int:
        """Get seconds remaining until code changes
        Получить секунд до смены кода
        Отримати секунд до зміни коду"""
        if timestamp is None:
            timestamp = time.time()
        return self.interval - int(timestamp) % self.interval

    def get_backup_codes(self, count: int = RECOVERY_CODES_COUNT, length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """Generate backup codes for recovery.
        Генерирует резервные коды для восстановления.
        Генерує резервні коди для відновлення."""
        backup_codes = []
        for i in range(count):
            code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
            if length == 8:
                code = f"{code[:4]}-{code[4:]}"
            backup_codes.append(code)
        logger.debug(f"Generated {count} backup codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
        return backup_codes

    @staticmethod
    def hash_backup_code(code: str) -> str:
        """Hash backup code for storage using salted PBKDF2.
        Хеширует резервный код для хранения с использованием PBKDF2.
        Хешує резервний код для зберігання з використанням PBKDF2."""
        try:
            code_clean = code.replace("-", "").replace(" ", "")
            salt = secrets.token_bytes(RECOVERY_CODE_SALT_BYTES)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                code_clean.encode("utf-8"),
                salt,
                RECOVERY_CODE_HASH_ITERATIONS,
                dklen=32,
            )
            return (
                f"{RECOVERY_CODE_HASH_PREFIX}${RECOVERY_CODE_HASH_ITERATIONS}$"
                f"{base64.b64encode(salt).decode('ascii')}$"
                f"{base64.b64encode(digest).decode('ascii')}"
            )
        except (TypeError, AttributeError, ValueError) as e:
            logger.error(f"Backup code hashing error / Ошибка хеширования резервного кода / Помилка хешування резервного коду: {e}")
            raise TOTPError(f"Failed to hash backup code / Ошибка хеширования резервного кода / Помилка хешування резервного коду: {e}")

    @staticmethod
    def verify_backup_code(code: str, stored_hash: str) -> bool:
        """Verify backup code against PBKDF2 hash.
        Проверяет резервный код по хешу PBKDF2.
        Перевіряє резервний код за хешем PBKDF2."""
        try:
            code_clean = code.replace("-", "").replace(" ", "")
            stored_hash = str(stored_hash or "")

            if stored_hash.startswith(f"{RECOVERY_CODE_HASH_PREFIX}$"):
                _, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
                salt = base64.b64decode(salt_b64, validate=True)
                expected = base64.b64decode(digest_b64, validate=True)
                computed = hashlib.pbkdf2_hmac(
                    "sha256",
                    code_clean.encode("utf-8"),
                    salt,
                    int(iterations),
                    dklen=len(expected),
                )
                return hmac.compare_digest(computed, expected)

            legacy_hash = hashlib.sha256(code_clean.encode("utf-8")).hexdigest()
            return hmac.compare_digest(legacy_hash, stored_hash.lower())

        except (TypeError, AttributeError, ValueError, binascii.Error) as e:
            logger.debug(f"Backup code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
            return False

    def reset_rate_limit(self, source: Optional[str] = None) -> None:
        """Reset rate limit for TOTP verification
        Сбросить ограничение частоты для верификации TOTP
        Скинути обмеження частоти для верифікації TOTP"""
        with self._verify_attempts_lock:
            if source is None:
                self._verify_attempts.clear()
            elif source in self._verify_attempts:
                del self._verify_attempts[source]
        logger.debug(f"Rate limit reset for source: {source or 'all'} / Ограничение частоты сброшено для источника: {source or 'all'} / Обмеження частоти скинуто для джерела: {source or 'all'}")

    def get_rate_limit_status(self, source: str) -> dict:
        """Get rate limit status for source
        Получить статус ограничения частоты для источника
        Отримати статус обмеження частоти для джерела"""
        with self._verify_attempts_lock:
            attempts = len(self._verify_attempts.get(source, []))
        return {
            "attempts": attempts,
            "max_attempts": MAX_VERIFY_ATTEMPTS,
            "remaining": max(0, MAX_VERIFY_ATTEMPTS - attempts),
            "window_seconds": VERIFY_ATTEMPT_WINDOW
        }

    def clear_used_codes_cache(self) -> None:
        """Clear anti-replay cache / Очистить кэш защиты от повторного воспроизведения / Очистити кеш захисту від повторного відтворення"""
        with self._used_codes_lock:
            self._used_codes.clear()
            self._last_cache_cleanup = time.time()
        logger.debug("Anti-replay cache cleared / Кэш защиты от повторного воспроизведения очищен / Кеш захисту від повторного відтворення очищено")

    def force_cleanup(self) -> int:
        """Force immediate anti-replay cache cleanup
        Принудительная немедленная очистка кэша защиты от повторного воспроизведения
        Примусове негайне очищення кешу захисту від повторного відтворення"""
        return self._cleanup_expired_codes()

    # ==================== TRUSTED DEVICES METHODS ====================

    def set_trusted_devices_file(self, file_path: str) -> None:
        """Set file path for trusted devices storage
        Установить путь к файлу для хранения доверенных устройств
        Встановити шлях до файлу для зберігання довірених пристроїв"""
        self._trusted_devices_file = file_path
        self._load_trusted_devices()

    def _load_trusted_devices(self) -> None:
        """Load trusted devices from file / Загрузить доверенные устройства из файла / Завантажити довірені пристрої з файлу"""
        if not self._trusted_devices_file or not os.path.exists(self._trusted_devices_file):
            return

        try:
            with open(self._trusted_devices_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._trusted_devices_lock:
                self._trusted_devices.clear()
                for device_data in data.get("devices", []):
                    device = TrustedDeviceToken.from_dict(device_data)
                    expiry_time = datetime.fromisoformat(device.expires_at).timestamp()
                    if expiry_time > time.time():
                        self._trusted_devices[device.device_id] = device
            logger.debug(f"Loaded {len(self._trusted_devices)} trusted devices / Загружено {len(self._trusted_devices)} доверенных устройств / Завантажено {len(self._trusted_devices)} довірених пристроїв")
        except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"Failed to load trusted devices / Ошибка загрузки доверенных устройств / Помилка завантаження довірених пристроїв: {e}")

    def _save_trusted_devices(self) -> None:
        """Save trusted devices to file / Сохранить доверенные устройства в файл / Зберегти довірені пристрої у файл"""
        if not self._trusted_devices_file:
            return

        try:
            with self._trusted_devices_lock:
                devices_data = {
                    "devices": [device.to_dict() for device in self._trusted_devices.values()],
                    "last_update": datetime.now().isoformat()
                }

            os.makedirs(os.path.dirname(self._trusted_devices_file), exist_ok=True)
            with open(self._trusted_devices_file, 'w', encoding='utf-8') as f:
                json.dump(devices_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self._trusted_devices)} trusted devices / Сохранено {len(self._trusted_devices)} доверенных устройств / Збережено {len(self._trusted_devices)} довірених пристроїв")
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save trusted devices / Ошибка сохранения доверенных устройств / Помилка збереження довірених пристроїв: {e}")

    def generate_trusted_device_token(self, device_id: str, device_name: str) -> Optional[str]:
        """Generate token for trusted device.
        Генерирует токен для доверенного устройства.
        Генерує токен для довіреного пристрою."""
        try:
            if len(self._trusted_devices) >= MAX_TRUSTED_DEVICES:
                logger.warning(f"Maximum trusted devices reached ({MAX_TRUSTED_DEVICES}) / Достигнуто максимальное количество доверенных устройств ({MAX_TRUSTED_DEVICES}) / Досягнуто максимальну кількість довірених пристроїв ({MAX_TRUSTED_DEVICES})")
                return None

            token = secrets.token_urlsafe(32)
            now = datetime.now()
            expires_at = now.timestamp() + TRUSTED_DEVICE_TOKEN_EXPIRY

            token_hash = hashlib.sha256(token.encode()).hexdigest()

            device = TrustedDeviceToken(
                device_id=device_id,
                device_name=device_name,
                token_hash=token_hash,
                created_at=now.isoformat(),
                expires_at=datetime.fromtimestamp(expires_at).isoformat(),
                last_used=now.isoformat()
            )

            with self._trusted_devices_lock:
                self._trusted_devices[device_id] = device
            self._save_trusted_devices()

            logger.info(f"Trusted device token generated for: {device_name} / Токен доверенного устройства сгенерирован для: {device_name} / Токен довіреного пристрою згенеровано для: {device_name}")
            return token
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to generate trusted device token / Ошибка генерации токена доверенного устройства / Помилка генерації токена довіреного пристрою: {e}")
            return None

    def verify_trusted_device_token(self, device_id: str, token: str) -> bool:
        """Verify trusted device token.
        Проверяет токен доверенного устройства.
        Перевіряє токен довіреного пристрою."""
        with self._trusted_devices_lock:
            device = self._trusted_devices.get(device_id)
            if not device:
                return False

            expiry_time = datetime.fromisoformat(device.expires_at).timestamp()
            if expiry_time <= time.time():
                del self._trusted_devices[device_id]
                self._save_trusted_devices()
                return False

            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if hmac.compare_digest(token_hash, device.token_hash):
                device.last_used = datetime.now().isoformat()
                self._save_trusted_devices()
                logger.debug(f"Trusted device token verified: {device_id[:16]}... / Токен доверенного устройства проверен: {device_id[:16]}... / Токен довіреного пристрою перевірено: {device_id[:16]}...")
                return True

        return False

    def remove_trusted_device(self, device_id: str) -> bool:
        """Remove trusted device.
        Удаляет доверенное устройство.
        Видаляє довірений пристрій."""
        with self._trusted_devices_lock:
            if device_id in self._trusted_devices:
                del self._trusted_devices[device_id]
                self._save_trusted_devices()
                logger.info(f"Trusted device removed: {device_id[:16]}... / Доверенное устройство удалено: {device_id[:16]}... / Довірений пристрій видалено: {device_id[:16]}...")
                return True
        return False

    def get_trusted_devices(self) -> List[Dict[str, Any]]:
        """Get list of trusted devices / Получить список доверенных устройств / Отримати список довірених пристроїв"""
        with self._trusted_devices_lock:
            return [device.to_dict() for device in self._trusted_devices.values()]

    # ==================== RECOVERY CODES METHODS ====================

    def generate_recovery_codes(self, count: int = RECOVERY_CODES_COUNT, length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """Generate new recovery codes.
        Генерирует новые резервные коды.
        Генерує нові резервні коди."""
        try:
            new_codes = []
            with self._recovery_codes_lock:
                self._recovery_codes.clear()

                for i in range(count):
                    code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
                    if length == 8:
                        code = f"{code[:4]}-{code[4:]}"

                    recovery_code = RecoveryCode(
                        code_hash=self.hash_backup_code(code),
                        created_at=datetime.now().isoformat(),
                        used=False
                    )
                    self._recovery_codes.append(recovery_code)
                    new_codes.append(code)

                self._save_recovery_codes()

            logger.info(f"Generated {count} recovery codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
            return new_codes
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to generate recovery codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")
            return []

    def verify_recovery_code(self, code: str) -> bool:
        """Verify and consume a recovery code.
        Проверяет и использует резервный код.
        Перевіряє та використовує резервний код."""
        try:
            code_clean = code.replace("-", "").replace(" ", "")

            with self._recovery_codes_lock:
                for rc in self._recovery_codes:
                    if not rc.used and self.verify_backup_code(code_clean, rc.code_hash):
                        rc.used = True
                        rc.used_at = datetime.now().isoformat()
                        self._save_recovery_codes()
                        logger.info("Recovery code used successfully / Резервный код успешно использован / Резервний код успішно використано")
                        return True

            logger.warning("Invalid or already used recovery code / Неверный или уже использованный резервный код / Невірний або вже використаний резервний код")
            return False
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Recovery code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
            return False

    def get_recovery_codes_status(self) -> Dict[str, Any]:
        """Get recovery codes status / Получить статус резервных кодов / Отримати статус резервних кодів"""
        with self._recovery_codes_lock:
            total = len(self._recovery_codes)
            used = sum(1 for rc in self._recovery_codes if rc.used)
            return {
                "total": total,
                "used": used,
                "available": total - used,
                "max_codes": RECOVERY_CODES_COUNT
            }

    def _save_recovery_codes(self) -> None:
        """Save recovery codes to file / Сохранить резервные коды в файл / Зберегти резервні коди у файл"""
        if not self._trusted_devices_file:
            return

        recovery_file = os.path.join(os.path.dirname(self._trusted_devices_file), "recovery_codes.json")
        try:
            with self._recovery_codes_lock:
                codes_data = {
                    "codes": [rc.to_dict() for rc in self._recovery_codes],
                    "last_update": datetime.now().isoformat()
                }

            with open(recovery_file, 'w', encoding='utf-8') as f:
                json.dump(codes_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self._recovery_codes)} recovery codes / Сохранено {len(self._recovery_codes)} резервных кодов / Збережено {len(self._recovery_codes)} резервних кодів")
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save recovery codes / Ошибка сохранения резервных кодов / Помилка збереження резервних кодів: {e}")