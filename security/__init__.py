"""
Security module - master password, encryption, integrity, anti-debug and clipboard

Модуль безопасности - мастер-пароль, шифрование, целостность, анти-отладка и буфер обмена
Модуль безпеки - майстер-пароль, шифрування, цілісність, анти-відлагодження та буфер обміну

FIXED: Added full type hints for all exports
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from security.master import MasterPassword
from security.integrity import (
    verify_file_integrity,
    save_file_with_hash,
    IntegrityError,
    IntegrityCheckError,
    check_file_integrity,
    get_file_hash
)
from security.encryption import encrypt, decrypt, set_key_from_master, clear_master_key
from security.antidebug import init_anti_debug, is_debugger_present, is_vm_detected
from security.clipboard import SecureClipboard, FallbackClipboard, set_clipboard, clear_clipboard

# ==================== EXPORTS ====================

__all__: List[str] = [
    'MasterPassword',
    'verify_file_integrity',
    'save_file_with_hash',
    'IntegrityError',
    'IntegrityCheckError',
    'check_file_integrity',
    'get_file_hash',
    'encrypt',
    'decrypt',
    'set_key_from_master',
    'clear_master_key',
    'init_anti_debug',
    'is_debugger_present',
    'is_vm_detected',
    'SecureClipboard',
    'FallbackClipboard',
    'set_clipboard',
    'clear_clipboard'
]