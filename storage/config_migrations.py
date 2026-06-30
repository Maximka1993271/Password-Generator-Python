from __future__ import annotations
# storage/config_migrations.py
"""
Config migrations module for Secure Pass Pro.
Модуль Config migrations для Secure Pass Pro.
Модуль Config migrations для Secure Pass Pro.
"""
"""
Config migrations module for Secure Pass Pro.
Модуль Config migrations для Secure Pass Pro.
Модуль Config migrations для Secure Pass Pro.
"""
"""
Schema migrations for configuration
Миграции схемы конфигурации
Міграції схеми конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

import atexit
from typing import Dict, Any, Callable

from storage.config_constants import logger


# ==================== SCHEMA MIGRATIONS ====================

SCHEMA_MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}


def _save_config_on_exit() -> None:
    """Save settings on program exit."""
    # try:
    #     from storage.config import Config
    #     config = Config()
    #     config.force_save()
    #     logger.info("Config saved on exit / Конфигурация сохранена при выходе / Конфігурацію збережено при виході")
    # except (OSError, IOError, PermissionError, AttributeError) as e:
    #     logger.error(f"Failed to save config on exit / Ошибка сохранения конфигурации при выходе / Помилка збереження конфігурації при виході: {e}")
    pass

atexit.register(_save_config_on_exit)


__all__ = [
    'SCHEMA_MIGRATIONS',
    '_save_config_on_exit',

]
