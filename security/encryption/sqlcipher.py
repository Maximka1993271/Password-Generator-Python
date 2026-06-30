"""
SQLCipher key management.
Управление ключом SQLCipher.
Керування ключем SQLCipher.
"""
from __future__ import annotations
import os
from typing import Optional

from utils.logger import get_logger
from security.encryption.exceptions import KeyDerivationError
from security.encryption.constants import (
    SCRYPT_SQLCIPHER_N, SCRYPT_SQLCIPHER_R, SCRYPT_SQLCIPHER_P,
    PBKDF2_ITERATIONS_SQLCIPHER, DATA_DIR, SQLCIPHER_SALT_FILE,
)
from security.encryption.memory import secure_zero as _secure_zero

logger = get_logger("encryption.sqlcipher")

# ── SQLCipher availability ───────────────────────────────────
# ── SQLCipher availability probe ─────────────────────────────
# SQLCipher encrypts the *entire* SQLite database file at the page level
# (AES-256-CBC by default in SQLCipher 3, AES-256-CBC-HMAC-SHA512 in v4).
# This provides defence-in-depth on top of our field-level AES-256-GCM.
#
# If sqlcipher3 is not installed we fall back to standard sqlite3 so
# the application still works; field-level encryption still protects the data.
_sqlcipher_available = False
try:
    from sqlcipher3 import dbapi2 as sqlcipher      # type: ignore
    _sqlcipher_available = True
    logger.info("SQLCipher available")
except ImportError:
    try:
        import sqlite3 as sqlcipher                  # type: ignore
        logger.info("SQLCipher not available, using standard SQLite")
    except ImportError as _e:
        logger.error("SQLite import error: %s", _e)

# ── In-memory SQLCipher state ────────────────────────────────
_sqlcipher_key:     Optional[bytearray] = None
_sqlcipher_key_hex: Optional[str]       = None
_sqlcipher_salt:    Optional[bytes]     = None


def _get_sqlcipher_salt() -> bytes:
    """Get or create the SQLCipher salt.
    Получить или создать соль SQLCipher.
    Отримати або створити сіль SQLCipher."""
    if os.path.exists(SQLCIPHER_SALT_FILE):
        try:
            from utils.secure_file_ops import secure_read
            content = secure_read(SQLCIPHER_SALT_FILE)
            if content and len(content) == 32:
                return content
        except (OSError, IOError) as e:
            logger.debug("SQLCipher salt read error: %s", e)
    os.makedirs(DATA_DIR, exist_ok=True)
    salt = os.urandom(32)
    try:
        from utils.secure_file_ops import secure_write
        secure_write(SQLCIPHER_SALT_FILE, salt, make_hidden=True)
    except (OSError, IOError) as e:
        logger.error("Failed to save SQLCipher salt: %s", e)
    return salt


# ── SQLCipher key derivation ─────────────────────────────────
# A separate SCrypt-derived key is used for SQLCipher rather than reusing
# the field-encryption key.  This means an attacker who recovers the
# page-level key cannot directly decrypt individual fields (and vice versa).
# Lighter SCrypt parameters (N=16384) balance performance during DB I/O.
def set_sqlcipher_key(master_password: str, salt: Optional[bytes] = None) -> None:
    """Derive and store the SQLCipher key.
    Устанавливает ключ SQLCipher.
    Встановлює ключ SQLCipher."""
    global _sqlcipher_key, _sqlcipher_key_hex, _sqlcipher_salt
    if not _sqlcipher_available:
        logger.warning("SQLCipher not available, cannot set key")
        return
    if salt is None:
        _sqlcipher_salt = _get_sqlcipher_salt()
    else:
        _sqlcipher_salt = salt
    try:
        from security.encryption.key_management import _scrypt_derive, _pbkdf2
        key = _scrypt_derive(
            master_password.encode("utf-8"), _sqlcipher_salt,
            n=SCRYPT_SQLCIPHER_N, r=SCRYPT_SQLCIPHER_R, p=SCRYPT_SQLCIPHER_P,
        )
        if key is None:
            key = _pbkdf2(master_password.encode("utf-8"), _sqlcipher_salt,
                          iterations=PBKDF2_ITERATIONS_SQLCIPHER)
        _sqlcipher_key = bytearray(key)
        _sqlcipher_key_hex = None
        try:
            from storage.database import set_sqlcipher_key as _db_set
            _db_set(master_password)
        except ImportError:
            pass
    except (ValueError, TypeError, MemoryError, RuntimeError) as e:
        logger.error("Failed to set SQLCipher key: %s", e)
        raise KeyDerivationError(f"SQLCipher key derivation failed: {e}")


# Multi-pass wipe: random bytes first, then zeros.
# The random pass prevents the zeros from being a predictable "dead write"
# that an optimising linker might elide.
def clear_sqlcipher_key() -> None:
    """Wipe the SQLCipher key from memory.
    Очищает ключ SQLCipher из памяти.
    Очищує ключ SQLCipher з пам'яті."""
    global _sqlcipher_key, _sqlcipher_key_hex
    if _sqlcipher_key:
        try:
            for _ in range(3):
                for i in range(len(_sqlcipher_key)):
                    try:
                        _sqlcipher_key[i] = os.urandom(1)[0]
                    except (IndexError, OSError, TypeError):
                        pass
                for i in range(len(_sqlcipher_key)):
                    try:
                        _sqlcipher_key[i] = 0
                    except (IndexError, TypeError):
                        pass
                _secure_zero(_sqlcipher_key)
        except (TypeError, ValueError, AttributeError, MemoryError, OSError):
            try:
                _secure_zero(_sqlcipher_key)
            except (TypeError, ValueError, AttributeError):
                pass
        _sqlcipher_key = None
    _sqlcipher_key_hex = None


def get_sqlcipher_key() -> Optional[bytes]:
    """Return current SQLCipher key bytes (copy).
    Возвращает текущий ключ SQLCipher (копия).
    Повертає поточний ключ SQLCipher (копія)."""
    return bytes(_sqlcipher_key) if _sqlcipher_key is not None else None


def get_sqlcipher_key_hex() -> Optional[str]:
    """Return current SQLCipher key as hex string.
    Возвращает ключ SQLCipher в виде hex.
    Повертає ключ SQLCipher у вигляді hex."""
    return bytes(_sqlcipher_key).hex() if _sqlcipher_key is not None else None


def get_sqlcipher_salt() -> Optional[bytes]:
    """Return current SQLCipher salt.
    Возвращает текущую соль SQLCipher.
    Повертає поточну сіль SQLCipher."""
    return _sqlcipher_salt if _sqlcipher_salt else _get_sqlcipher_salt()


def is_sqlcipher_available() -> bool:
    """Return True if SQLCipher is available.
    Возвращает True, если SQLCipher доступен.
    Повертає True, якщо SQLCipher доступний."""
    return _sqlcipher_available
