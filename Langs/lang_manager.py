"""
Language manager for Secure Pass Pro v4.0
Менеджер языков для Secure Pass Pro v4.0
Менеджер мов для Secure Pass Pro v4.0

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List, Tuple, Union, Callable, TypeVar, cast

from .lang_ru import RUSSIAN_DICT
from .lang_en import ENGLISH_DICT
from .lang_ua import UKRAINIAN_DICT

# ==================== CONSTANTS ====================

LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": RUSSIAN_DICT,
    "EN": ENGLISH_DICT,
    "UA": UKRAINIAN_DICT,
}

DEFAULT_LANGUAGE: str = "RU"
SUPPORTED_LANGUAGES: List[str] = ["RU", "EN", "UA"]


# ==================== LANGUAGE MANAGER CLASS ====================

class LanguageManager:
    """🌐 Language manager with fallback and missing key recovery"""

    _instance: Optional['LanguageManager'] = None
    _current_lang: str = DEFAULT_LANGUAGE
    _fallback_lang: str = DEFAULT_LANGUAGE

    def __new__(cls) -> 'LanguageManager':
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_language(cls, lang_code: str) -> bool:
        """🌐 Set current interface language"""
        if lang_code in SUPPORTED_LANGUAGES:
            cls._current_lang = lang_code
            from utils.logger import get_logger
            logger = get_logger("lang")
            logger.debug(f"🌐 Language set to: {lang_code}")
            return True
        from utils.logger import get_logger
        logger = get_logger("lang")
        logger.warning(f"⚠️ Unsupported language: {lang_code}")
        return False

    @classmethod
    def set_fallback(cls, lang_code: str) -> bool:
        """🔄 Set fallback language"""
        if lang_code in SUPPORTED_LANGUAGES:
            cls._fallback_lang = lang_code
            return True
        return False

    @classmethod
    def get_current_lang(cls) -> str:
        """🌐 Get current language code"""
        return cls._current_lang

    @classmethod
    def get_fallback_lang(cls) -> str:
        """🔄 Get fallback language code"""
        return cls._fallback_lang

    @classmethod
    def get(cls, key: str, default: Optional[str] = None, log_missing: bool = True) -> str:
        """🔍 Get translation by key with smart search"""
        # 1️⃣ Try primary language
        current_dict: Dict[str, str] = LANGUAGES.get(cls._current_lang, {})
        if key in current_dict and current_dict[key]:
            return current_dict[key]

        # 2️⃣ Try fallback language
        fallback_dict: Dict[str, str] = LANGUAGES.get(cls._fallback_lang, {})
        if key in fallback_dict and fallback_dict[key]:
            return fallback_dict[key]

        # 3️⃣ Try English as world standard
        en_dict: Dict[str, str] = LANGUAGES.get("EN", {})
        if key in en_dict and en_dict[key]:
            return en_dict[key]

        # 4️⃣ Return default or key itself
        if default is not None:
            return default
        return key


# ==================== CONVENIENCE FUNCTIONS ====================

def get_text(key: str, default: Optional[str] = None) -> str:
    """🔍 Get text by key"""
    return LanguageManager.get(key, default)


def set_language(lang_code: str) -> bool:
    """🌐 Change application language"""
    return LanguageManager.set_language(lang_code)


def set_fallback_language(lang_code: str) -> bool:
    """🔄 Change application fallback language"""
    return LanguageManager.set_fallback(lang_code)


def get_current_language() -> str:
    """🌐 Get current language"""
    return LanguageManager.get_current_lang()


def get_fallback_language() -> str:
    """🔄 Get fallback language"""
    return LanguageManager.get_fallback_lang()


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