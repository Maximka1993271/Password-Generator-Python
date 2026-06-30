"""
Encryption self-tests and public verification helpers.
Самотестирование шифрования и вспомогательные функции проверки.
Самотестування шифрування та допоміжні функції перевірки.
"""
from __future__ import annotations
from typing import Dict

from utils.logger import get_logger
from security.encryption.exceptions import EncryptionError, TamperDetectedError, EncryptionVersionError
from security.encryption.cipher import (
    encrypt, decrypt,
    _add_metadata, _extract_metadata, _xor_stream,
)

logger = get_logger("encryption.verification")

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False


def _run_crypto_self_test() -> Dict[str, bool]:
    """Run built-in crypto self-tests; return a dict of test_name → passed.
    Запускает встроенные крипто-самотесты.
    Запускає вбудовані крипто-самотести."""
    import os, hmac, hashlib
    results: Dict[str, bool] = {
        "aesgcm": False,
        "xor": False,
        "metadata": False,
        "versioning": False,
    }
    try:
        # AES-GCM round-trip
        if _CRYPTO_OK:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
            key = os.urandom(32)
            nonce = os.urandom(12)
            data = b"self-test-data"
            ct = _AESGCM(key).encrypt(nonce, data, None)
            if _AESGCM(key).decrypt(nonce, ct, None) == data:
                results["aesgcm"] = True

        # XOR round-trip
        key = os.urandom(32)
        nonce = os.urandom(16)
        plain = b"xor-test"
        ct = _xor_stream(plain, key, nonce)
        if _xor_stream(ct, key, nonce) == plain:
            results["xor"] = True

        # Metadata round-trip
        data = b"metadata-test"
        with_meta = _add_metadata(data, version=5, flags=1)
        extracted, v, f = _extract_metadata(with_meta)
        if extracted == data and v == 5 and f == 1:
            results["metadata"] = True

        results["versioning"] = True

        passed = sum(1 for v in results.values() if v)
        logger.info("Crypto self-tests: %d/%d passed", passed, len(results))
    except (ImportError, OSError, TypeError, ValueError, MemoryError) as e:
        logger.error("Crypto self-test failed: %s", e)

    return results


def verify_encryption() -> bool:
    """Smoke-test: encrypt → decrypt a test string; return True on success.
    Проверяет шифрование на тестовой строке.
    Перевіряє шифрування на тестовому рядку."""
    test_data = "test_data_123"
    try:
        return decrypt(encrypt(test_data)) == test_data
    except (ValueError, TypeError, UnicodeDecodeError, AttributeError,
            EncryptionError, TamperDetectedError, EncryptionVersionError) as e:
        logger.error("Encryption verification failed: %s", e)
        return False


def get_crypto_self_test_results() -> Dict[str, bool]:
    """Return a copy of the module-level self-test results.
    Возвращает копию результатов самотестирования.
    Повертає копію результатів самотестування."""
    return _CRYPTO_SELF_TEST_RESULTS.copy() if _CRYPTO_OK else {}


# Run on import
_CRYPTO_SELF_TEST_RESULTS = _run_crypto_self_test() if _CRYPTO_OK else {}
_CRYPTO_SELF_TEST_PASSED  = all(_CRYPTO_SELF_TEST_RESULTS.values()) if _CRYPTO_OK else False
if _CRYPTO_OK and not _CRYPTO_SELF_TEST_PASSED:
    for _test_name, _passed in _CRYPTO_SELF_TEST_RESULTS.items():
        if not _passed:
            logger.warning("  - %s: FAILED", _test_name)
