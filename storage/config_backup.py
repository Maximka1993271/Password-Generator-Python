from __future__ import annotations
# storage/config_backup.py
"""
Config backup module for Secure Pass Pro.
Модуль Config backup для Secure Pass Pro.
Модуль Config backup для Secure Pass Pro.
"""
"""
Config backup module for Secure Pass Pro.
Модуль Config backup для Secure Pass Pro.
Модуль Config backup для Secure Pass Pro.
"""
"""
Configuration backup metadata class
Класс метаданных резервной копии конфигурации
Клас метаданих резервної копії конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ConfigBackup:
    """
    Configuration backup metadata

    Метаданные резервной копии конфига
    Метадані резервної копії конфігу
    """
    path: str
    timestamp: float
    version: int
    size: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


__all__ = [
    'ConfigBackup',

]
