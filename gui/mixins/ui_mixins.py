"""
UI-related mixins grouped together

Миксины, связанные с интерфейсом, сгруппированные вместе
Міксини, пов'язані з інтерфейсом, згруповані разом
"""
from __future__ import annotations
from gui.mixins.ui_setup_mixin import UISetupMixin
from gui.mixins.settings_mixin import SettingsMixin
from gui.mixins.settings_window_mixin import SettingsWindowMixin
from gui.mixins.dialogs_mixin import DialogsMixin

__all__ = [
    'UISetupMixin',
    'SettingsMixin',
    'SettingsWindowMixin',
    'DialogsMixin'
]