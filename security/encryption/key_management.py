"""
Key derivation (SCrypt/PBKDF2), machine-key and master-key management.
Вывод ключа (SCrypt/PBKDF2), управление машинным и мастер-ключом.
Виведення ключа (SCrypt/PBKDF2), керування машинним та майстер-ключем.
"""
from __future__ import annotations
import os
import sys
import hashlib
import json
import platform
import uuid as _uuid_mod
from datetime import datetime
from typing import Optional, List, Dict, Any

from security.encryption.exceptions import KeyDerivationError

# Minimal file I/O — deliberately avoids importing utils package to prevent
# the circular import chain:
#   utils.__init__ → utils.importer → gui → storage → security.encryption
import logging as _logging
logger = _logging.getLogger("encryption.keys")


def _secure_read(path: str):
    """Read bytes from *path*, return None on error."""
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except (OSError, IOError):
        return None


def _secure_write(path: str, data: bytes, **_kw) -> bool:
    """Atomically write *data* to *path*."""
    import tempfile, os
    dir_ = os.path.dirname(path) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        os.replace(tmp, path)
        return True
    except (OSError, IOError) as e:
        logger.error("Secure write failed for %s: %s", path, e)
        return False
from security.encryption.constants import (
    SCRYPT_N, SCRYPT_R, SCRYPT_P,
    SCRYPT_MASTER_N, SCRYPT_MASTER_R, SCRYPT_MASTER_P,
    PBKDF2_ITERATIONS,
    DATA_DIR, SALT_FILE, UUID_FILE,
    KEY_VERSION_FILE, KEY_ROTATION_LOG,
)
from security.encryption.memory import zero as _zero, clear_string as _clear_string, hide_dir as _hide_dir

# Re-bind to proper logger once utils is safely available
try:
    from utils.logger import get_logger as _get_logger
    logger = _get_logger("encryption.keys")
except (ImportError, AttributeError):
    pass  # logger already set via stdlib logging above

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes as _hashes
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

# ── Module-level key state ────────────────────────────────────
_master_key:  Optional[bytearray] = None
_machine_key: Optional[bytearray] = None
_key_version: int = 1
_key_rotation_history: List[Dict[str, Any]] = []


def _ensure_data_dir() -> None:
    """Create data directory.
    Создаёт директорию данных.
    Створює директорію даних."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        _hide_dir(DATA_DIR)
    except (PermissionError, OSError) as e:
        logger.error("Failed to create data dir: %s", e)


def _secure_write_file(path: str, data: bytes) -> bool:
    """Write file securely.
    Безопасная запись файла.
    Безпечний запис файлу."""
    _ensure_data_dir()
    _secure_write(path, data, make_hidden=True)
    return True


def _get_key_version() -> int:
    """Get current key version.
    Получить текущую версию ключа.
    Отримати поточну версію ключа."""
    global _key_version
    if os.path.exists(KEY_VERSION_FILE):
        try:
            content = _secure_read(KEY_VERSION_FILE)
            if content:
                _key_version = int(content.decode("utf-8").strip())
        except (ValueError, OSError, UnicodeDecodeError) as e:
            logger.debug("Key version read error: %s", e)
    return _key_version


def _log_key_rotation(old_version: int, new_version: int, reason: str = "manual") -> None:
    """Log a key-rotation event.
    Логирует событие ротации ключа.
    Логує подію ротації ключа."""
    global _key_rotation_history
    try:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "old_version": old_version,
            "new_version": new_version,
            "reason": reason,
            "platform": platform.system(),
        }
        _key_rotation_history.append(entry)
        if len(_key_rotation_history) > 50:
            _key_rotation_history = _key_rotation_history[-50:]
        with open(KEY_ROTATION_LOG, "w", encoding="utf-8") as f:
            json.dump(_key_rotation_history, f, indent=2, ensure_ascii=False)
    except (OSError, TypeError, ValueError) as e:
        logger.debug("Failed to log key rotation: %s", e)


def _set_key_version(version: int) -> None:
    """Save key version.
    Сохраняет версию ключа.
    Зберігає версію ключа."""
    global _key_version
    old_version = _key_version
    _key_version = version
    try:
        _secure_write_file(KEY_VERSION_FILE, str(version).encode("utf-8"))
        _log_key_rotation(old_version, version, "update")
    except (OSError, PermissionError) as e:
        logger.error("Failed to save key version: %s", e)


def _get_salt() -> bytes:
    """Get or create encryption salt.
    Получить или создать соль шифрования.
    Отримати або створити сіль шифрування."""
    if os.path.exists(SALT_FILE):
        try:
            content = _secure_read(SALT_FILE)
            if content and len(content) == 32:
                return content
            raise ValueError("Invalid encryption salt length")
        except (OSError, ValueError) as e:
            logger.error("Error reading salt: %s", e)
            raise
    _ensure_data_dir()
    salt = os.urandom(32)
    _secure_write_file(SALT_FILE, salt)
    return salt


def _get_machine_uuid() -> str:
    """Get or create machine UUID.
    Получить или создать UUID машины.
    Отримати або створити UUID машини."""
    if os.path.exists(UUID_FILE):
        try:
            content = _secure_read(UUID_FILE)
            if content:
                value = content.decode("utf-8").strip()
                _uuid_mod.UUID(value)
                return value
        except (OSError, ValueError, UnicodeDecodeError) as e:
            logger.error("Error reading UUID: %s", e)
            raise
    _ensure_data_dir()
    new_uuid = str(_uuid_mod.uuid4())
    _secure_write_file(UUID_FILE, new_uuid.encode("utf-8"))
    return new_uuid


# ── Key-derivation functions ──────────────────────────────────
# SCrypt is the preferred KDF: it is memory-hard (fills ~32 MB at default
# settings) which makes GPU / ASIC brute-force attacks orders of magnitude
# more expensive than PBKDF2. PBKDF2 is the fallback when the cryptography
# wheel is unavailable. Both are deterministic given the same secret + salt.
def _pbkdf2(secret: bytes, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytearray:
    """PBKDF2-SHA256 key derivation.
    Вывод ключа PBKDF2-SHA256.
    Виведення ключа PBKDF2-SHA256."""
    try:
        if _CRYPTO_OK:
            kdf = PBKDF2HMAC(algorithm=_hashes.SHA256(), length=32, salt=salt, iterations=iterations)
            return bytearray(kdf.derive(secret))
        return bytearray(hashlib.pbkdf2_hmac("sha256", secret, salt, iterations, dklen=32))
    except (TypeError, ValueError, MemoryError, RuntimeError) as e:
        logger.error("PBKDF2 error: %s", e)
        raise KeyDerivationError(f"Key derivation failed: {e}")


def _scrypt_derive(
    secret: bytes, salt: bytes,
    n: int = SCRYPT_N, r: int = SCRYPT_R, p: int = SCRYPT_P,
) -> Optional[bytearray]:
    """SCrypt key derivation with configurable parameters.
    Вывод ключа SCrypt с настраиваемыми параметрами.
    Виведення ключа SCrypt з налаштовуваними параметрами."""
    if not _CRYPTO_OK:
        return None
    try:
        kdf = Scrypt(salt=salt, length=32, n=n, r=r, p=p)
        return bytearray(kdf.derive(secret))
    except (TypeError, ValueError, MemoryError, RuntimeError) as e:
        logger.debug("SCrypt failed, falling back to PBKDF2: %s", e)
        return None


# ── Machine key (fallback when master password is absent) ─────
# The machine key is derived from stable hardware identifiers:
# UUID + hostname + architecture + platform.  It ties encrypted values to
# this specific installation so they cannot trivially be copied to another
# machine.  It is NOT as strong as a user-supplied master password because
# the "secret" (system info) is not actually secret — use only for
# low-sensitivity data or as a bootstrap before the user logs in.
def _get_machine_key() -> bytearray:
    """Derive a machine-specific fallback key.
    Получить машинный ключ для fallback.
    Отримати машинний ключ для fallback."""
    global _machine_key
    if _machine_key is None:
        machine_str = (
            _get_machine_uuid() + "|"
            + platform.node() + "|"
            + platform.machine() + "|"
            + sys.platform
        )
        key = _scrypt_derive(machine_str.encode("utf-8", errors="replace"), _get_salt())
        if key is None:
            key = _pbkdf2(machine_str.encode("utf-8", errors="replace"), _get_salt())
        _machine_key = key
        _clear_string(machine_str)
    return _machine_key


def set_key_from_master(master_password: str) -> None:
    """Derive and store the master encryption key.

    Uses SCrypt (or PBKDF2 fallback). The plaintext *master_password*
    is zeroed in memory immediately after derivation.

    Устанавливает ключ из мастер-пароля.
    Встановлює ключ з майстер-пароля.

    Args:
        master_password (str): The user's plaintext master password.
            Zeroed in memory after key derivation.

    Raises:
        KeyDerivationError: If key derivation fails.
    """
    global _master_key
    # Zero out the previous key before writing the new one to avoid having
    # two copies of key material in memory simultaneously.
    _zero(_master_key)
    # Keep a plain-string copy to pass to SQLCipher AFTER the SCrypt
    # derivation below — SCrypt will zero-wipe master_password via _clear_string.
    sqlcipher_password = master_password
    try:
        salt = _get_salt()
        key = _scrypt_derive(
            master_password.encode("utf-8"), salt,
            n=SCRYPT_MASTER_N, r=SCRYPT_MASTER_R, p=SCRYPT_MASTER_P,
        )
        if key is None:
            # SCrypt unavailable: fall back to PBKDF2-SHA256 (600 000 rounds).
            # Acceptable security, just more vulnerable to hardware attacks.
            key = _pbkdf2(master_password.encode("utf-8"), salt)
        _master_key = key
    except KeyDerivationError:
        raise
    finally:
        _clear_string(master_password)
    if sqlcipher_password:
        from security.encryption.sqlcipher import set_sqlcipher_key
        set_sqlcipher_key(sqlcipher_password)
        _clear_string(sqlcipher_password)


def clear_master_key() -> None:
    """Wipe the master key from memory (three-pass overwrite).

    Safe to call even when no key is loaded. Also clears the SQLCipher session key.

    Очищает мастер-ключ из памяти.
    Очищує майстер-ключ з пам'яті.
    """
    global _master_key
    _zero(_master_key)
    _master_key = None
    from security.encryption.sqlcipher import clear_sqlcipher_key
    clear_sqlcipher_key()


def has_active_master_key() -> bool:
    """Return True when a master-derived key is held in memory.

    Возвращает True, когда мастер-ключ активен.
    Повертає True, коли майстер-ключ активний.

    Returns:
        bool: True if ``set_key_from_master()`` has been called
            and ``clear_master_key()`` has not been called since.
    """
    return _master_key is not None


def active_key() -> bytearray:
    """Return the active key (master if set, else machine fallback).
    Возвращает активный ключ.
    Повертає активний ключ."""
    return _master_key if _master_key is not None else _get_machine_key()

# Keep private alias for internal use
_active_key = active_key
