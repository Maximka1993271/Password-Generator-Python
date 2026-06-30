"""
Main application window - Helper methods (Mixin entry point)
Главное окно приложения - Вспомогательные методы (точка входа миксинов)
Головне вікно програми - Допоміжні методи (точка входу міксинів)

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

from gui.main_window_helpers_data import MainWindowDataMixin
from gui.main_window_helpers_ui import MainWindowUIMixin
from gui.main_window_helpers_lang import MainWindowLangMixin
from gui.main_window_helpers_2fa import MainWindow2FAMixin


class HelperMethods(
    MainWindowDataMixin,
    MainWindowUIMixin,
    MainWindowLangMixin,
    MainWindow2FAMixin
):
    """
    Helper methods for SecurePassPro.
    Вспомогательные методы для SecurePassPro.
    Допоміжні методи для SecurePassPro.
    """
    pass


__all__: List[str] = [
    'HelperMethods',
    'MainWindowDataMixin',
    'MainWindowUIMixin',
    'MainWindowLangMixin',
    'MainWindow2FAMixin',
]
