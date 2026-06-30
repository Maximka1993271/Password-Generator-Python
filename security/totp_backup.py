"""
TOTP backup codes functionality
Резервные коды для TOTP
Резервні коди для TOTP

English:
- Recovery code generation
- PBKDF2 hashing for recovery codes
- Recovery code verification

Русский:
- Генерация резервных кодов
- Хеширование резервных кодов PBKDF2
- Проверка резервных кодов

Українська:
- Генерація резервних кодів
- Хешування резервних кодів PBKDF2
- Перевірка резервних кодів
"""
from __future__ import annotations

import secrets
import hashlib
import base64
import hmac
import binascii
from typing import List, Optional
from utils.logger import get_logger

logger = get_logger("totp")

# Recovery codes / Резервные коды / Резервні коди
RECOVERY_CODES_COUNT = 10
RECOVERY_CODE_LENGTH = 8
RECOVERY_CODE_HASH_PREFIX = "pbkdf2_sha256"
RECOVERY_CODE_HASH_ITERATIONS = 200000
RECOVERY_CODE_SALT_BYTES = 16


def get_backup_codes(self, count: int = RECOVERY_CODES_COUNT, length: int = RECOVERY_CODE_LENGTH) -> List[str]:
    """
    Generate backup codes for recovery.

    Генерирует резервные коды для восстановления.
    Генерує резервні коди для відновлення.
    """
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
    """
    Hash backup code for storage using salted PBKDF2.

    Хеширует резервный код для хранения с использованием PBKDF2.
    Хешує резервний код для зберігання з використанням PBKDF2.
    """
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
    """
    Verify backup code against PBKDF2 hash.

    Проверяет резервный код по хешу PBKDF2.
    Перевіряє резервний код за хешем PBKDF2.
    """
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

        # Legacy SHA256 support
        legacy_hash = hashlib.sha256(code_clean.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash.lower())

    except (TypeError, AttributeError, ValueError, binascii.Error) as e:
        logger.debug(f"Backup code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
        return False


# Add methods to TOTP class
def totp_get_backup_codes(self, count: int = RECOVERY_CODES_COUNT, length: int = RECOVERY_CODE_LENGTH) -> List[str]:
    """Get backup codes - wrapper for TOTP class
    Получить резервные коды - обёртка для класса TOTP
    Отримати резервні коди - обгортка для класу TOTP"""
    backup_codes = []
    for i in range(count):
        code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
        if length == 8:
            code = f"{code[:4]}-{code[4:]}"
        backup_codes.append(code)
    logger.debug(f"Generated {count} backup codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
    return backup_codes