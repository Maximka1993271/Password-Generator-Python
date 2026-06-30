from __future__ import annotations
# storage/config_paths.py
"""
Config paths module for Secure Pass Pro.
Модуль Config paths для Secure Pass Pro.
Модуль Config paths для Secure Pass Pro.
"""
"""
Config paths module for Secure Pass Pro.
Модуль Config paths для Secure Pass Pro.
Модуль Config paths для Secure Pass Pro.
"""
"""
Portable path management for configuration
Управление портативными путями для конфигурации
Керування портативними шляхами для конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

import os
import sys


# ==================== PORTABLE PATHS (BUILT-IN) ====================

def get_program_dir() -> str:
    """
    Return the directory where the EXE or script is located

    Возвращает директорию, где находится EXE или скрипт
    Повертає директорію, де знаходиться EXE або скрипт
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_dir() -> str:
    """
    Return the directory for storing configs (hidden .securepass folder)

    Возвращает директорию для хранения конфигов (скрытая папка .securepass)
    Повертає директорію для зберігання конфігів (прихована папка .securepass)
    """
    program_dir = get_program_dir()
    config_dir = os.path.join(program_dir, '.securepass')
    os.makedirs(config_dir, exist_ok=True)
    
    # Hide on Windows
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(config_dir, 2)
        except (ImportError, AttributeError, OSError):
            pass
    
    return config_dir


def get_config_file() -> str:
    """
    Return the path to the configuration file

    Возвращает путь к файлу конфигурации
    Повертає шлях до файлу конфігурації
    """
    return os.path.join(get_config_dir(), 'config.json')


def hide_dir(directory: str) -> None:
    """
    Hide directory on Windows

    Скрывает директорию на Windows
    Ховає директорію на Windows
    """
    if sys.platform == 'win32' and os.path.exists(directory):
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(directory, 2)
        except (ImportError, AttributeError, OSError) as _:
            pass


__all__ = [
    'get_program_dir',
    'get_config_dir',
    'get_config_file',
    'hide_dir',

]
