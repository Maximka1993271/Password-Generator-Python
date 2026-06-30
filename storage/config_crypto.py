from __future__ import annotations
# storage/config_crypto.py
"""
Config crypto module for Secure Pass Pro.
Модуль Config crypto для Secure Pass Pro.
Модуль Config crypto для Secure Pass Pro.
"""
"""
Config crypto module for Secure Pass Pro.
Модуль Config crypto для Secure Pass Pro.
Модуль Config crypto для Secure Pass Pro.
"""
"""
Encryption utilities for configuration values
Шифрование значений конфигурации
Шифрування значень конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

import os
import sys
import binascii
from typing import Optional

# Import from config_paths
from storage.config_paths import get_config_dir, hide_dir


# ==================== LOGGER (BUILT-IN) ====================

from utils.logger import get_logger  # unified logging

logger = get_logger("config")


def _get_config_encryption_key() -> bytes:
    """
    Get a device-specific key for config value encryption.

    Получить устройственно-специфичный ключ для шифрования значений конфига.
    Отримати пристрійно-специфічний ключ для шифрування значень конфіга.
    """
    try:
        from security.encryption import _get_machine_uuid
        machine_uuid = _get_machine_uuid()
    except (ImportError, AttributeError):
        key_file = os.path.join(get_config_dir(), ".config_key")
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read(32)
            except (OSError, IOError, PermissionError):
                pass

        import secrets
        new_key = secrets.token_bytes(32)
        try:
            with open(key_file, 'wb') as f:
                f.write(new_key)
            hide_dir(os.path.dirname(key_file))
        except (OSError, IOError, PermissionError):
            pass
        return new_key

    import hashlib
    return hashlib.sha256(machine_uuid.encode('utf-8')).digest()


def _encrypt_config_value(value: str) -> str:
    """
    Encrypt a config value with AES-256-GCM.

    Шифрует значение конфига с помощью AES-256-GCM.
    Шифрує значення конфіга за допомогою AES-256-GCM.
    """
    if not value:
        return ""

    try:
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag

        key = _get_config_encryption_key()
        nonce = os.urandom(12)
        ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), b"secure-pass-pro-config-v2")
        return "[enc2]" + base64.b64encode(nonce + ciphertext).decode("ascii")

    except (InvalidTag, ValueError, TypeError, binascii.Error) as e:
        logger.error(f"Failed to encrypt config value with AES-GCM / Ошибка шифрования значения конфига с помощью AES-GCM / Помилка шифрування значення конфіга за допомогою AES-GCM: {e}")
        raise
    except ImportError:
        logger.warning("cryptography is unavailable; using legacy config obfuscation / cryptography недоступен; используется устаревшее запутывание конфига / cryptography недоступний; використовується застаріле заплутування конфіга")

    try:
        key = _get_config_encryption_key()
        value_bytes = value.encode('utf-8')
        encrypted = bytearray()
        for i, b in enumerate(value_bytes):
            encrypted.append(b ^ key[i % len(key)])
        import base64
        return f"[enc]{base64.b64encode(encrypted).decode('ascii')}"

    except (ValueError, TypeError, OSError) as e:
        logger.error(f"Failed to encrypt config value / Ошибка шифрования значения конфига / Помилка шифрування значення конфіга: {e}")
        raise


def _decrypt_config_value(encrypted_value: str) -> str:
    """
    Decrypt a config value, supporting both AES-GCM [enc2] and legacy [enc] values.

    Дешифрует значение конфига, поддерживая как AES-GCM [enc2], так и legacy [enc] значения.
    Дешифрує значення конфіга, підтримуючи як AES-GCM [enc2], так і legacy [enc] значення.
    """
    if not encrypted_value or not encrypted_value.startswith("[enc"):
        return encrypted_value

    if encrypted_value.startswith("[enc2]"):
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            from cryptography.exceptions import InvalidTag

            raw = base64.b64decode(encrypted_value[6:], validate=True)
            if len(raw) < 29:
                raise ValueError("Encrypted config value is too short / Зашифрованное значение конфига слишком короткое / Зашифроване значення конфіга занадто коротке")
            nonce, ciphertext = raw[:12], raw[12:]
            plaintext = AESGCM(_get_config_encryption_key()).decrypt(
                nonce,
                ciphertext,
                b"secure-pass-pro-config-v2"
            )
            return plaintext.decode("utf-8")

        except (InvalidTag, ValueError, TypeError, binascii.Error) as e:
            logger.error(f"Failed to decrypt AES-GCM config value / Ошибка дешифрования значения конфига AES-GCM / Помилка дешифрування значення конфіга AES-GCM: {e}")
            return ""

    try:
        import base64
        encrypted_data = base64.b64decode(encrypted_value[5:])
        key = _get_config_encryption_key()
        decrypted = bytearray()
        for i, b in enumerate(encrypted_data):
            decrypted.append(b ^ key[i % len(key)])
        return decrypted.decode('utf-8')

    except (ValueError, TypeError, binascii.Error) as e:
        logger.error(f"Failed to decrypt legacy config value / Ошибка дешифрования устаревшего значения конфига / Помилка дешифрування застарілого значення конфіга: {e}")
        return ""


__all__ = [
    '_get_config_encryption_key',
    '_encrypt_config_value',
    '_decrypt_config_value',

]
