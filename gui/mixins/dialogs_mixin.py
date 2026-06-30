"""
Dialogs mixin for SecurePassPro - FULLY FIXED VERSION with FULL 3-LANGUAGE SUPPORT
Исправлены: сохранение текущего пароля, экспорт данных, полная поддержка 3 языков
FIXED: Убраны все broad exceptions, добавлена корректная обработка ошибок

FIXED #C4, #H4: Replaced non-existent CTkInputDialog with local _input_dialog function
FIXED #EX: Replaced broad Exception with specific exceptions

FIXED #SPLIT: Split into multiple files for maintainability
- dialogs_helpers.py - helper functions
- dialogs_qr_mixin.py - QR dialog
- dialogs_history_mixin.py - History dialog
- dialogs_db_mixin.py - Database dialog
- dialogs_about_mixin.py - About dialog

This file is a wrapper that imports all dialog mixins.

Этот файл является обёрткой, которая импортирует все миксины диалогов.
Цей файл є обгорткою, яка імпортує всі міксини діалогів.
"""
from __future__ import annotations

from gui.mixins.dialogs_helpers import (
    _input_dialog,
        _get_actual_theme,
    _center_window_relative_to_parent,
    _setup_window_style,
    _set_topmost_false,
)

from gui.mixins.dialogs_qr_mixin import DialogsQRMixin
from gui.mixins.dialogs_history_mixin import DialogsHistoryMixin
from gui.mixins.dialogs_db_mixin import DialogsDBMixin
from gui.mixins.dialogs_about_mixin import DialogsAboutMixin


class DialogsMixin(
    DialogsQRMixin,
    DialogsHistoryMixin,
    DialogsDBMixin,
    DialogsAboutMixin
):
    """
    Mixin class for dialog windows (QR, History, Database, About)

    Класс-миксин для диалоговых окон (QR, История, База данных, О программе)
    Клас-міксин для діалогових вікон (QR, Історія, База даних, Про програму)
    """
    pass


__all__ = ['DialogsMixin', '_input_dialog']