from __future__ import annotations
# storage/config_constants.py
"""
Config constants module for Secure Pass Pro.
Модуль Config constants для Secure Pass Pro.
Модуль Config constants для Secure Pass Pro.
"""
"""
Config constants module for Secure Pass Pro.
Модуль Config constants для Secure Pass Pro.
Модуль Config constants для Secure Pass Pro.
"""
"""
Configuration constants, schema and sensitive keys
Константы конфигурации, схема и чувствительные ключи
Константи конфігурації, схема та чутливі ключі

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

from typing import Dict, Any

# ==================== LOGGER (BUILT-IN) ====================

from utils.logger import get_logger  # unified logging

logger = get_logger("config")

SCHEMA_VERSION = 5

CONFIG_SCHEMA = {
    "THEME": {"type": str, "default": "Dark", "allowed": ["Dark", "Light", "System"]},
    "LANG": {"type": str, "default": "RU", "allowed": ["RU", "EN", "UA"]},
    "SOUND": {"type": bool, "default": True},
    "RGB": {"type": bool, "default": True},
    "RGB_SPEED": {"type": str, "default": "normal", "allowed": ["slow", "normal", "fast"]},
    "RGB_WIDTH": {"type": str, "default": "normal", "allowed": ["thin", "normal", "thick"]},
    "RADIUS": {"type": int, "default": 25, "min": 0, "max": 50},
    "font_size": {"type": int, "default": 14, "min": 10, "max": 28},
    "CLIP_TIMEOUT": {"type": int, "default": 60, "min": 5, "max": 300},
    "AUTO_LOCK": {"type": bool, "default": False},
    "AUTO_LOCK_TIMEOUT": {"type": int, "default": 5, "min": 1, "max": 30},
    "auto_save": {"type": bool, "default": False},
    "PDF_THEME": {"type": str, "default": "light", "allowed": ["light", "dark"]},
    "MAX_ATTEMPTS": {"type": int, "default": 5, "min": 3, "max": 10},
    "2fa_enabled": {"type": bool, "default": False},
    "2fa_secret": {"type": str, "default": "", "encrypted": True},
    "2fa_backup_hashes": {"type": list, "default": [], "sensitive": True},
    "2fa_account_name": {"type": str, "default": "SecurePassPro_User"},
    "2fa_setup_completed": {"type": bool, "default": False},
    "2fa_last_verified": {"type": str, "default": ""},
    # ── Dev / ops overrides (settable via SECUREPASS_* env vars) ──
    "SKIP_DB_INIT": {"type": bool, "default": False},
    "DEBUG_MODE":   {"type": bool, "default": False},
}

SENSITIVE_CONFIG_KEYS = {
    "2fa_secret",
    "2fa_backup_hashes",
}


def _is_sensitive_config_key(key: str) -> bool:
    """
    Check if key is sensitive

    Проверяет, является ли ключ чувствительным
    Перевіряє, чи є ключ чутливим
    """
    key_lower = str(key).lower()
    if key in SENSITIVE_CONFIG_KEYS:
        return True
    return any(marker in key_lower for marker in ("password", "secret", "token", "backup", "hash", "master"))


__all__ = [
    'logger',
    'SCHEMA_VERSION',
    'CONFIG_SCHEMA',
    'SENSITIVE_CONFIG_KEYS',
    '_is_sensitive_config_key',

]
