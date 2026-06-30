"""
Settings window mixin for SecurePassPro - MODERN DESIGN like Microsoft Edge

Миксин окна настроек для SecurePassPro - СОВРЕМЕННЫЙ ДИЗАЙН как в Microsoft Edge
Міксин вікна налаштувань для SecurePassPro - СУЧАСНИЙ ДИЗАЙН як у Microsoft Edge

FIXED: Removed recursive _reopen_settings_window() to prevent freezing on theme switch
FIXED: Theme and language now update settings window in place
FIXED #C9: Added missing import for set_global_radius
FIXED #EX: Replaced broad Exception with specific exceptions

FIXED #SPLIT: Split into multiple files for maintainability
- settings_window_handlers.py - event handlers (_toggle_*, _update_*, _apply_*, _on_*)
- settings_window_profiles.py - profiles (save/load/reset)
- settings_window_cards.py - settings cards and search
- settings_window_ui.py - UI creation

This file is a wrapper that imports all settings window mixins.

Этот файл является обёрткой, которая импортирует все миксины окна настроек.
Цей файл є обгорткою, яка імпортує всі міксини вікна налаштувань.
"""
from __future__ import annotations

from gui.mixins.settings_window_handlers import SettingsWindowHandlersMixin
from gui.mixins.settings_window_profiles import SettingsWindowProfilesMixin
from gui.mixins.settings_window_cards import SettingsWindowCardsMixin
from gui.mixins.settings_window_ui import SettingsWindowUIMixin


class SettingsWindowMixin(
    SettingsWindowHandlersMixin,
    SettingsWindowProfilesMixin,
    SettingsWindowCardsMixin,
    SettingsWindowUIMixin
):
    """
    Mixin class for settings window - MODERN CARD DESIGN

    Класс-миксин для окна настроек - СОВРЕМЕННЫЙ КАРТОЧНЫЙ ДИЗАЙН
    Клас-міксин для вікна налаштувань - СУЧАСНИЙ КАРТКОВИЙ ДИЗАЙН
    """
    pass


__all__ = ['SettingsWindowMixin']