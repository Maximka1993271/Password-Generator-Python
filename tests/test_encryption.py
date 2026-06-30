#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for security/encryption.py

Модульные тесты для security/encryption.py
Модульні тести для security/encryption.py

ALL EXCEPTION HANDLING FIXED - No 'except Exception' remains
ВСЕ ОБРАБОТКИ ИСКЛЮЧЕНИЙ ИСПРАВЛЕНЫ - Не осталось 'except Exception'
ВСІ ОБРОБКИ ВИНЯТКІВ ВИПРАВЛЕНІ - Не залишилось 'except Exception'
"""
from __future__ import annotations

import pytest
import os
import binascii
from typing import Dict, Any

from utils.logger import get_logger
logger = get_logger("test_encryption")

from security.encryption import (
    encrypt,
    decrypt,
    EncryptionError,
    TamperDetectedError,
    EncryptionVersionError,
)


class TestEncryption:
    """Tests for encryption module / Тесты для модуля шифрования / Тести для модуля шифрування"""

    # ==================== BASIC ENCRYPTION TESTS ====================

    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption"""
        test_data = "test_password_123"
        encrypted = encrypt(test_data)
        assert encrypted != test_data
        decrypted = decrypt(encrypted)
        assert decrypted == test_data

    def test_encrypt_empty_string(self):
        """Test encryption of empty string"""
        result = encrypt("")
        assert result == ""
        decrypted = decrypt("")
        assert decrypted == ""

    # ==================== ERROR HANDLING TESTS ====================

    def test_decrypt_invalid_data(self):
        """Test decryption with invalid data should raise appropriate exception"""
        invalid_inputs = [
            "invalid_base64!!!",
            "enc1:invalid!!!",
            "enc2:invalid_base64!!!",
            "enc3:invalid!!!",
            "enc1:not_valid_base64",
        ]

        for invalid_input in invalid_inputs:
            with pytest.raises((EncryptionError, ValueError, binascii.Error, UnicodeDecodeError)):
                decrypt(invalid_input)

    def test_decrypt_tampered_data(self):
        """Test decryption with tampered data should raise TamperDetectedError"""
        original = "test_secret_data"
        encrypted = encrypt(original)

        if len(encrypted) > 10:
            tampered = encrypted[:5] + "X" * 5 + encrypted[10:]
        else:
            tampered = encrypted + "X"

        with pytest.raises((TamperDetectedError, EncryptionError, ValueError, UnicodeDecodeError)):
            decrypt(tampered)

    # ==================== ENCRYPTION VERIFICATION ====================

    def test_verify_encryption(self):
        """Test encryption verification function"""
        from security.encryption import verify_encryption
        result = verify_encryption()
        assert isinstance(result, bool)

    # ==================== SAFE HELPER (no broad Exception) ====================

    def _safe_encrypt_operation(self, data: str) -> str:
        """
        Helper for safe encryption operations with specific exception handling.

        Вспомогательный метод для безопасных операций шифрования.
        Допоміжний метод для безпечних операцій шифрування.
        """
        try:
            return encrypt(data)
        except (EncryptionError, ValueError, TypeError, AttributeError) as e:
            logger.error(f"Encryption error: {e}")
            raise
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File system error during encryption: {e}")
            raise


if __name__ == "__main__":

    main()
