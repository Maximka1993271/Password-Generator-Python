"""
Backward compatibility wrapper for lang.py
Оборачивает новые модули для обратной совместимости
Обгортає нові модулі для зворотної сумісності

FIXED: Added full type hints for all exports
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from .lang_manager import (
    LANGUAGES,
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    LanguageManager,
    get_text,
    set_language,
    set_fallback_language,
    get_current_language,
    get_fallback_language,
)

# ==================== EXPORTS ====================

__all__: List[str] = [
    'LANGUAGES',
    'DEFAULT_LANGUAGE',
    'SUPPORTED_LANGUAGES',
    'LanguageManager',
    'get_text',
    'set_language',
    'set_fallback_language',
    'get_current_language',
    'get_fallback_language',
]