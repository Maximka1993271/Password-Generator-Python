"""
Dialogs mixin - Database window (wrapper for backward compatibility)
Миксин диалогов - Окно базы данных (обертка для обратной совместимости)
Міксин діалогів - Вікно бази даних (обгортка для зворотної сумісності)

Объединяет все разделенные части в один класс для обратной совместимости.
"""
from __future__ import annotations

from gui.mixins.dialogs_db_core import DialogsDBCoreMixin
from gui.mixins.dialogs_db_actions import DialogsDBActionsMixin
from gui.mixins.dialogs_db_bulk import DialogsDBBulkMixin
from gui.mixins.dialogs_db_extra import DialogsDBExtraMixin


class DialogsDBMixin(
    DialogsDBCoreMixin,
    DialogsDBActionsMixin,
    DialogsDBBulkMixin,
    DialogsDBExtraMixin
):
    """
    Mixin class for database dialog window (unified from split modules)

    Класс-миксин для окна базы данных (объединенный из разделенных модулей)
    Клас-міксин для вікна бази даних (об'єднаний з розділених модулів)
    """
    pass


__all__ = ['DialogsDBMixin']
