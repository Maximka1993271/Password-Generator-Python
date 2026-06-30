"""
Storage module - database and configuration

Модуль хранения - база данных и конфигурация
Модуль зберігання - база даних та конфігурація

FIXED: Added full type hints for all exports
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from storage.database import PasswordDB
from storage.config import Config

# ==================== EXPORTS ====================

__all__: List[str] = [
    'PasswordDB',
    'Config',
]

# Settings facade — centralised access point
from core.app_settings import AppSettings, Key, settings  # noqa: F401
from core.config_manager import ConfigManager, Layer  # noqa: F401
