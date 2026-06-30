"""
Core module - password generation logic

Модуль ядра - логика генерации паролей
Модуль ядра - логіка генерації паролів

FIXED: Added full type hints for all exports
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from core.generator import PasswordGenerator, StrengthCalculator

# ==================== EXPORTS ====================

__all__: List[str] = [
    'PasswordGenerator',
    'StrengthCalculator',
]

from core.app_settings import AppSettings, Key, settings  # noqa: F401
from core.config_manager import ConfigManager, Layer, config_manager  # noqa: F401
from core.validators import (
    validate, ValidationResult,
    sanitize_text, sanitize_label, sanitize_url, sanitize_notes,
    LabelValidator, PasswordValidator, URLValidator, EmailValidator,
    FilePathValidator, CategoryValidator, TagValidator,
    PasswordEntryValidator, MasterPasswordValidator,
)  # noqa: F401
