"""
AES-256-GCM field-level encryption for password storage.

Sub-modules
-----------
exceptions      — Custom exception hierarchy
constants       — Scrypt/PBKDF2 parameters, file paths
memory          — Secure memory-wiping helpers
dpapi           — Windows DPAPI wrapper
key_management  — Salt/UUID I/O, master and machine key derivation
sqlcipher       — SQLCipher key lifecycle
cipher          — encrypt() / decrypt() and their helpers
rotation        — reencrypt_all()
verification    — Self-tests and verify_encryption()

Submodule AES-256-GCM для хранения паролей.
Submodule AES-256-GCM для зберігання паролів.
"""
from __future__ import annotations

# ── Exceptions ────────────────────────────────────────────────
from security.encryption.exceptions import (
    CryptoUnavailableError,
    EncryptionError,
    TamperDetectedError,
    KeyDerivationError,
    KeyRotationError,
    EncryptionVersionError,
)

# ── Constants (public) ────────────────────────────────────────
from security.encryption.constants import (
    SCRYPT_N, SCRYPT_R, SCRYPT_P,
    SCRYPT_MASTER_N, SCRYPT_MASTER_R, SCRYPT_MASTER_P,
    SCRYPT_SQLCIPHER_N, SCRYPT_SQLCIPHER_R, SCRYPT_SQLCIPHER_P,
    PBKDF2_ITERATIONS, PBKDF2_ITERATIONS_SQLCIPHER,
    ENC_PREFIX, FALLBACK_PREFIX, DPAPI_PREFIX,
    ENC_VERSION, ENC_METADATA_SIZE,
    DATA_DIR, SALT_FILE, UUID_FILE,
    KEY_VERSION_FILE, KEY_ROTATION_LOG, SQLCIPHER_SALT_FILE,
)

# ── Memory utilities (public) ─────────────────────────────────
from security.encryption.memory import (
    zero, secure_zero, clear_bytes, clear_string, clear_bytearray, hide_dir,
    # legacy private aliases still accessible
    _zero, _secure_zero, _clear_bytes, _clear_string, _clear_bytearray, _hide_dir,
)

# ── DPAPI ─────────────────────────────────────────────────────
from security.encryption.dpapi import (
    _DPAPI_AVAILABLE,
    dpapi_encrypt, dpapi_decrypt,
    _dpapi_encrypt, _dpapi_decrypt,
)

# ── Key management ────────────────────────────────────────────
from security.encryption.key_management import (
    set_key_from_master,
    clear_master_key,
    has_active_master_key,
    active_key,
    _active_key,
    _get_salt,
    _get_machine_uuid,
    _get_machine_key,
    _pbkdf2,
    _scrypt_derive,
    _get_key_version,
    _set_key_version,
    _log_key_rotation,
)

# ── SQLCipher ─────────────────────────────────────────────────
from security.encryption.sqlcipher import (
    set_sqlcipher_key,
    clear_sqlcipher_key,
    get_sqlcipher_key,
    get_sqlcipher_key_hex,
    get_sqlcipher_salt,
    is_sqlcipher_available,
    _sqlcipher_available,
)

# ── Core cipher ───────────────────────────────────────────────
from security.encryption.cipher import (
    encrypt,
    decrypt,
    _add_metadata,
    _extract_metadata,
    _xor_stream,
    _encrypt_fallback,
    _decrypt_fallback,
    _encrypt_hardware,
    _decrypt_hardware,
    _ENC_PREFIX,
    _FALLBACK_PREFIX,
    _DPAPI_PREFIX,
)

# ── Key rotation ──────────────────────────────────────────────
from security.encryption.rotation import reencrypt_all

# ── Verification ─────────────────────────────────────────────
from security.encryption.verification import (
    verify_encryption,
    get_crypto_self_test_results,
    _run_crypto_self_test,
    _CRYPTO_SELF_TEST_RESULTS,
    _CRYPTO_SELF_TEST_PASSED,
)

# ── Public helpers (kept from original module) ────────────────
def get_key_version() -> int:
    """Get current key version.
    Возвращает текущую версию ключа.
    Повертає поточну версію ключа."""
    return _get_key_version()

def get_encryption_version() -> int:
    """Get current encryption format version.
    Возвращает текущую версию формата шифрования.
    Повертає поточну версію формату шифрування."""
    return ENC_VERSION

def is_dpapi_available() -> bool:
    """Return True if DPAPI is available.
    Возвращает True, если DPAPI доступен.
    Повертає True, якщо DPAPI доступний."""
    return _DPAPI_AVAILABLE

__all__ = [
    # Exceptions
    "CryptoUnavailableError", "EncryptionError", "TamperDetectedError",
    "KeyDerivationError", "KeyRotationError", "EncryptionVersionError",
    # Core API
    "encrypt", "decrypt", "reencrypt_all",
    "set_key_from_master", "clear_master_key", "has_active_master_key",
    # SQLCipher
    "set_sqlcipher_key", "clear_sqlcipher_key", "get_sqlcipher_key",
    "get_sqlcipher_key_hex", "get_sqlcipher_salt", "is_sqlcipher_available",
    # Verification
    "verify_encryption", "get_crypto_self_test_results",
    # Info
    "get_key_version", "get_encryption_version",
    "is_dpapi_available", "is_sqlcipher_available",
    # Memory
    "zero", "secure_zero", "clear_bytes", "clear_string", "clear_bytearray",
]
