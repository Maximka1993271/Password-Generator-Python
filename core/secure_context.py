"""
Secure in-memory string/context helpers: SecureString, SecurePasswordContext.
Безопасные строки и контекст в памяти: SecureString, SecurePasswordContext.
Безпечні рядки та контекст у пам'яті: SecureString, SecurePasswordContext.
"""
from __future__ import annotations
"""
Password generator and strength calculator with secure memory handling

Генератор паролей и калькулятор стойкости с безопасной работой с памятью
Генератор паролів та калькулятор стійкості з безпечною роботою з пам'яттю

FIXED #M1: Full EFF Diceware word list - now loaded from file
FIXED #EX: Replaced broad Exception with specific exceptions
FIXED: Added full type hints for all methods
"""

import secrets
import math
import string
import random
import ctypes
import os
import json
from typing import List, Optional, Tuple, Dict, Any, Union, Set, Callable, cast
from array import array

from utils.logger import get_logger
from utils.secure_memory import SecureBytes, SecurePassword, MemoryGuard, secure_zero_memory, secure_zero_string

logger = get_logger("generator")

# Try to import Argon2 for master password hashing
# Пытаемся импортировать Argon2 для хеширования мастер-пароля
# Намагаємося імпортувати Argon2 для хешування майстер-пароля
_ARGON2_OK: bool = False
PasswordHasher = None
VerifyMismatchError = VerificationError = InvalidHashError = Exception

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ARGON2_OK = True
except ImportError as e:
    logger.debug(f"Argon2 not available / Argon2 недоступен / Argon2 недоступний: {e}")

# Argon2id parameters for password hashing (OWASP 2024 recommendations)
# Параметры Argon2id для хеширования паролей (рекомендации OWASP 2024)
# Параметри Argon2id для хешування паролів (рекомендації OWASP 2024)
ARGON2_TIME_COST: int = 3
ARGON2_MEMORY_COST: int = 65536
ARGON2_PARALLELISM: int = 4
ARGON2_HASH_LEN: int = 32


# ==================== HELPER FUNCTIONS / ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ / ДОПОМІЖНІ ФУНКЦІЇ ====================

def _secure_zero_bytearray(data: Optional[bytearray]) -> None:
    """Safely zeroes a bytearray

    Безопасно обнуляет bytearray
    Безпечно обнуляє bytearray
    """
    if data is None:
        return
    try:
        length: int = len(data)
        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(data)), 0, length)
    except (TypeError, AttributeError, OSError) as e:
        logger.debug(f"Memory zeroing failed / Ошибка обнуления памяти / Помилка обнулення пам'яті: {e}")
        for i in range(len(data)):
            data[i] = 0


def _clear_string(s: str) -> None:
    """Attempts to clear string from memory

    Пытается очистить строку из памяти
    Намагається очистити рядок з пам'яті
    """
    if not s:
        return
    if s.startswith(('[encrypted', 'enc1:', 'enc2:', 'enc3:')):
        return
    try:
        ba: bytearray = bytearray(s.encode('utf-8'))
        _secure_zero_bytearray(ba)
    except (UnicodeEncodeError, TypeError, MemoryError) as e:
        logger.debug(f"String clearing failed / Ошибка очистки строки / Помилка очищення рядка: {e}")


def secure_compare(a: str, b: str) -> bool:
    """Secure string comparison resistant to timing attacks.

    Безопасное сравнение строк, устойчивое к атакам по времени.
    Безпечне порівняння рядків, стійке до атак за часом.
    """
    return secrets.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


# ==================== SECURE STRING / БЕЗОПАСНАЯ СТРОКА / БЕЗПЕЧНИЙ РЯДОК ====================

class SecureString(SecurePassword):
    """Secure string that is automatically cleared from memory.

    Безопасная строка, автоматически очищаемая из памяти.
    Безпечний рядок, що автоматично очищується з пам'яті.
    """

    def __init__(self, value: Optional[Union[str, bytes, bytearray]] = None) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(value)

    def get(self) -> str:
        """Get string value / Получить строку / Отримати рядок"""
        if self._data is None:
            return ""
        return self._data.decode('utf-8')

    def get_string(self) -> str:
        """Get string value (alias) / Получить строку (алиас) / Отримати рядок (аліас)"""
        return self.get()

    def __str__(self) -> str:
        """
        Return a human-readable string representation.
        Возвращает строковое представление для пользователей.
        Повертає рядкове представлення для користувачів.
        """
        return self.get()

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation.
        Возвращает строковое представление для разработчиков.
        Повертає рядкове представлення для розробників.
        """
        return f"<SecureString length={len(self)}>"


class SecurePasswordContext:
    """Context manager for secure password handling.

    Менеджер контекста для безопасной работы с паролями.
    Менеджер контексту для безпечної роботи з паролями.
    """

    def __init__(self) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self._password: Optional[SecurePassword] = None

    def set_password(self, password: Union[str, SecurePassword]) -> None:
        """Set password / Установить пароль / Встановити пароль"""
        if self._password:
            self._password.clear()
        if isinstance(password, SecurePassword):
            self._password = password
        else:
            self._password = SecurePassword(password)
            _clear_string(password)

    def get(self) -> Optional[str]:
        """Get password as string / Получить пароль как строку / Отримати пароль як рядок"""
        if self._password is None:
            return None
        return self._password.get_string()

    def get_secure(self) -> Optional[SecurePassword]:
        """Get secure password object / Получить безопасный объект пароля / Отримати безпечний об'єкт пароля"""
        return self._password

    def clear(self) -> None:
        """Clear password / Очистить пароль / Очистити пароль"""
        if self._password:
            self._password.clear()
            self._password = None

    def __enter__(self) -> 'SecurePasswordContext':
        """
        Enter the context manager.
        Войти в контекстный менеджер.
        Увійти в контекстний менеджер.
        """
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[object]) -> None:
        """
        Exit the context manager and clean up.
        Выйти из контекстного менеджера и освободить ресурсы.
        Вийти з контекстного менеджера та звільнити ресурси.
        """
        self.clear()


# ==================== PASSWORD GENERATOR / ГЕНЕРАТОР ПАРОЛЕЙ / ГЕНЕРАТОР ПАРОЛІВ ====================

