"""
Secure memory management for Python
Безопасная работа с чувствительными данными в памяти
Безпечна робота з чутливими даними в пам'яті

FIXED #50: Improved secure_zero_string with multiple strategies and clear warnings
FIXED #51: Added copy/pickle protection for SecureBytes and SecurePassword
FIXED #41: Centralized logging
FIXED #M5: Added __getitem__ method for SecureBytes and SecurePassword

FIXED #SPLIT: Split into multiple files for maintainability
- secure_memory_core.py - Core low-level functions
- secure_bytes.py - SecureBytes class
- secure_password.py - SecurePassword class
- memory_guard.py - MemoryGuard class and monitoring

This file is a wrapper that re-exports everything from the split modules
for backward compatibility.

Этот файл является обёрткой, которая ре-экспортирует всё из разделённых модулей
для обратной совместимости.

Цей файл є обгорткою, яка ре-експортує все з розділених модулів
для зворотної сумісності.
"""
from __future__ import annotations

from utils.secure_memory_core import (
    secure_zero_memory,
    secure_zero_string,
    secure_zero_dict,
    wipe_variable,
    is_memory_secure,
    get_memory_usage,
    force_memory_cleanup,
    init_secure_memory,
    get_secure_string_recommendation,
)

from utils.secure_bytes import SecureBytes

from utils.secure_password import SecurePassword

from utils.memory_guard import (
    MemoryGuard,
    start_memory_pressure_monitoring,
    stop_memory_pressure_monitoring,
)

# Export main classes and functions
__all__ = [
    'secure_zero_memory',
    'secure_zero_string',
    'secure_zero_dict',
    'SecureBytes',
    'SecurePassword',
    'MemoryGuard',
    'wipe_variable',
    'is_memory_secure',
    'init_secure_memory',
    'start_memory_pressure_monitoring',
    'stop_memory_pressure_monitoring',
    'get_memory_usage',
    'force_memory_cleanup',
    'get_secure_string_recommendation',
]