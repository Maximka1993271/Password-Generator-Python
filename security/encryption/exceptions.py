"""
Encryption exception classes.
Классы исключений шифрования.
Класи винятків шифрування.
"""
from __future__ import annotations


class CryptoUnavailableError(RuntimeError):
    """Encryption required but cryptography package unavailable.
    Шифрование требуется, но пакет cryptography недоступен.
    Шифрування потрібне, але пакет cryptography недоступний."""
    pass


class EncryptionError(Exception):
    """Error during encryption/decryption.
    Ошибка при шифровании/дешифровании.
    Помилка при шифруванні/дешифруванні."""
    pass


class TamperDetectedError(EncryptionError):
    """Tampering detected in encrypted data.
    Обнаружено вмешательство в зашифрованные данные.
    Виявлено втручання в зашифровані дані."""
    pass


class KeyDerivationError(EncryptionError):
    """Error during key derivation.
    Ошибка при выводе ключа.
    Помилка при виведенні ключа."""
    pass


class KeyRotationError(EncryptionError):
    """Error during key rotation.
    Ошибка при ротации ключа.
    Помилка при ротації ключа."""
    pass


class EncryptionVersionError(EncryptionError):
    """Error with encryption version.
    Ошибка с версией шифрования.
    Помилка з версією шифрування."""
    pass
