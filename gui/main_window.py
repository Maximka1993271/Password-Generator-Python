"""
Main application window
Главное окно приложения
Головне вікно програми

FIXED #SPLIT: Split into multiple files for maintainability
- main_window_core.py - class skeleton and __init__
- main_window_ui.py - UI creation methods
- main_window_events.py - _generate, _copy, _save, _open
- main_window_helpers.py - helper methods (_update_*, _animate_*, etc.)
- main_window_cleanup.py - cleanup and shutdown methods

Исправлено #SPLIT: Разделено на несколько файлов для удобства сопровождения
Виправлено #SPLIT: Розділено на кілька файлів для зручності супроводу

FIXED: Added full type hints for all exports and constants
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast
from collections import deque
import os
import sys

from gui.main_window_core import SecurePassPro, validate_password_strength, sanitize_label

# ==================== CONSTANTS ====================

HISTORY_MAX: int = 50
UPD_URL: str = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

# ==================== EXPORTS ====================

__all__: List[str] = [
    'SecurePassPro',
    'CONFIG_FILE',
    'CONFIG_DIR',
    'BASE_DIR',
    'UPD_URL',
    'HISTORY_MAX',
    'validate_password_strength',
    'sanitize_label',
]

# ==================== RE-EXPORT CONSTANTS FROM CORE ====================

# Re-export constants from core module
# Re-экспорт констант из core модуля
# Re-експорт констант з core модуля
from gui.main_window_core import (
    CONFIG_FILE,
    CONFIG_DIR,
    BASE_DIR,
    UPD_URL as _UPD_URL,
    HISTORY_MAX as _HISTORY_MAX
)

# Ensure UPD_URL and HISTORY_MAX are available at module level
# Гарантируем, что UPD_URL и HISTORY_MAX доступны на уровне модуля
# Гарантуємо, що UPD_URL та HISTORY_MAX доступні на рівні модуля
UPD_URL = _UPD_URL
HISTORY_MAX = _HISTORY_MAX