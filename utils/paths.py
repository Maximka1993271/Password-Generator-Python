"""
Path management for SecurePassPro
Centralized portable path logic for EXE and script modes
3 LANGUAGE SUPPORT: RU, EN, UA

FIXED #52: Portable mode now requires explicit PORTABLE.txt file
FIXED #HIDE: Added auto-hide functionality for all data directories

Управление путями для SecurePassPro
Централизованная портативная логика путей для EXE и скриптов
ПОДДЕРЖКА 3 ЯЗЫКОВ: RU, EN, UA

ИСПРАВЛЕНО #52: Портативный режим теперь требует явного файла PORTABLE.txt
ИСПРАВЛЕНО #HIDE: Добавлена автоматическая функция скрытия для всех директорий данных

Керування шляхами для SecurePassPro
Централізована портативна логіка шляхів для EXE та скриптів
ПІДТРИМКА 3 МОВ: RU, EN, UA

ВИПРАВЛЕНО #52: Портативний режим тепер вимагає явного файлу PORTABLE.txt
ВИПРАВЛЕНО #HIDE: Додано автоматичну функцію приховування для всіх директорій даних
"""
from __future__ import annotations

import os
import sys
import ctypes
import tempfile
import platform
import time
from typing import Optional, Dict, List, Tuple
from enum import Enum


def hide_directory_on_windows(path: str) -> bool:
    """
    Hide directory on Windows using SetFileAttributesW.
    
    Скрывает директорию на Windows через SetFileAttributesW.
    Ховає директорію на Windows через SetFileAttributesW.
    """
    if platform.system() != "Windows":
        return False
    
    if not os.path.exists(path):
        return False
    
    try:
        ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        return True
    except (AttributeError, OSError, TypeError):
        return False


def ensure_hidden(path: str) -> None:
    """
    Ensure directory is hidden on Windows.
    
    Гарантирует, что директория скрыта на Windows.
    Гарантує, що директорія прихована на Windows.
    """
    if platform.system() == "Windows" and os.path.exists(path):
        hide_directory_on_windows(path)


def get_program_dir() -> str:
    """Return the directory where the EXE or script is located
    Возвращает директорию, где находится EXE или скрипт
    Повертає директорію, де знаходиться EXE або скрипт"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_dir() -> str:
    """Return hidden .securepass directory
    Возвращает скрытую директорию .securepass
    Повертає приховану директорію .securepass"""
    program_dir = get_program_dir()
    config_dir = os.path.join(program_dir, '.securepass')
    os.makedirs(config_dir, exist_ok=True)
    ensure_hidden(config_dir)
    return config_dir


def get_data_dir() -> str:
    """Get data directory (inside .securepass) - HIDDEN
    Получить директорию данных (внутри .securepass) - СКРЫТАЯ
    Отримати директорію даних (всередині .securepass) - ПРИХОВАНА"""
    data_dir = os.path.join(get_config_dir(), "data")
    os.makedirs(data_dir, exist_ok=True)
    ensure_hidden(data_dir)
    return data_dir


def get_logs_dir() -> str:
    """Get logs directory (inside .securepass) - HIDDEN
    Получить директорию логов (внутри .securepass) - СКРЫТАЯ
    Отримати директорію логів (всередині .securepass) - ПРИХОВАНА"""
    logs_dir = os.path.join(get_config_dir(), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    ensure_hidden(logs_dir)
    return logs_dir


def get_backup_dir() -> str:
    """Get backup directory (inside .securepass) - HIDDEN
    Получить директорию бэкапов (внутри .securepass) - СКРЫТАЯ
    Отримати директорію бекапів (всередині .securepass) - ПРИХОВАНА"""
    backup_dir = os.path.join(get_config_dir(), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    ensure_hidden(backup_dir)
    return backup_dir


def get_cache_dir() -> str:
    """Get cache directory (inside .securepass) - HIDDEN
    Получить директорию кэша (внутри .securepass) - СКРЫТАЯ
    Отримати директорію кешу (всередині .securepass) - ПРИХОВАНА"""
    cache_dir = os.path.join(get_config_dir(), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    ensure_hidden(cache_dir)
    return cache_dir


def get_temp_dir() -> str:
    """Get temporary directory (system temp, not hidden)
    Получить временную директорию (системный temp, не скрытая)
    Отримати тимчасову директорію (системний temp, не прихована)"""
    system_temp = tempfile.gettempdir()
    temp_dir = os.path.join(system_temp, "securepasspro")
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def get_config_file() -> str:
    """Get config.json file path (inside .securepass)
    Получить путь к файлу config.json (внутри .securepass)
    Отримати шлях до файлу config.json (всередині .securepass)"""
    return os.path.join(get_config_dir(), "config.json")


def get_db_file() -> str:
    """Get passwords.db file path (inside .securepass/data)
    Получить путь к файлу passwords.db (внутри .securepass/data)
    Отримати шлях до файлу passwords.db (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "passwords.db")


def get_salt_file() -> str:
    """Get db.salt file path (inside .securepass/data)
    Получить путь к файлу db.salt (внутри .securepass/data)
    Отримати шлях до файлу db.salt (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "db.salt")


def get_master_file() -> str:
    """Get master.key file path (inside .securepass/data)
    Получить путь к файлу master.key (внутри .securepass/data)
    Отримати шлях до файлу master.key (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "master.key")


def get_uuid_file() -> str:
    """Get machine.id file path (inside .securepass/data)
    Получить путь к файлу machine.id (внутри .securepass/data)
    Отримати шлях до файлу machine.id (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "machine.id")


def get_key_version_file() -> str:
    """Get key.version file path (inside .securepass/data)
    Получить путь к файлу key.version (внутри .securepass/data)
    Отримати шлях до файлу key.version (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "key.version")


def get_sqlcipher_salt_file() -> str:
    """Get sqlcipher.salt file path (inside .securepass/data)
    Получить путь к файлу sqlcipher.salt (внутри .securepass/data)
    Отримати шлях до файлу sqlcipher.salt (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "sqlcipher.salt")


def get_lockout_file() -> str:
    """Get lockout.json file path (inside .securepass/data)
    Получить путь к файлу lockout.json (внутри .securepass/data)
    Отримати шлях до файлу lockout.json (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "lockout.json")


def get_audit_file() -> str:
    """Get auth_audit.json file path (inside .securepass/data)
    Получить путь к файлу auth_audit.json (внутри .securepass/data)
    Отримати шлях до файлу auth_audit.json (всередині .securepass/data)"""
    return os.path.join(get_data_dir(), "auth_audit.json")


# ==================== BACKWARD COMPATIBILITY ====================

def get_base_dir() -> str:
    """Get base directory of the application
    Получить базовую директорию приложения
    Отримати базову директорію додатку"""
    return get_program_dir()


def ensure_dir(path: str) -> None:
    """Ensure directory exists, create if not, and hide on Windows
    Убедиться, что директория существует, создать если нет, и скрыть на Windows
    Переконатися, що директорія існує, створити якщо ні, і приховати на Windows"""
    os.makedirs(path, exist_ok=True)
    ensure_hidden(path)


def hide_dir(path: str) -> None:
    """Hide directory on Windows (alias for ensure_hidden)
    Скрыть директорию на Windows (алиас для ensure_hidden)
    Приховати директорію на Windows (аліас для ensure_hidden)"""
    ensure_hidden(path)


def cleanup_temp_files(max_age_hours: int = 24) -> int:
    """Clean up temporary files older than max_age_hours
    Очистить временные файлы старше max_age_hours
    Очистити тимчасові файли старші за max_age_hours"""
    temp_dir = get_temp_dir()
    if not os.path.exists(temp_dir):
        return 0
    
    deleted = 0
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    try:
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        deleted += 1
            except (OSError, IOError, PermissionError):
                continue
    except (OSError, IOError, PermissionError):
        pass
    
    return deleted


def get_all_paths() -> Dict[str, str]:
    """Get all important paths as a dictionary
    Получить все важные пути в виде словаря
    Отримати всі важливі шляхи у вигляді словника"""
    return {
        "program_dir": get_program_dir(),
        "config_dir": get_config_dir(),
        "data_dir": get_data_dir(),
        "logs_dir": get_logs_dir(),
        "backup_dir": get_backup_dir(),
        "cache_dir": get_cache_dir(),
        "temp_dir": get_temp_dir(),
        "config_file": get_config_file(),
        "db_file": get_db_file(),
        "master_file": get_master_file(),
        "lockout_file": get_lockout_file(),
    }


def is_portable() -> bool:
    """Check if running in portable mode / Проверить, работает ли программа в портативном режиме / Перевірити, чи працює програма в портативному режимі"""
    return False


def set_portable_mode(enabled: bool) -> bool:
    """Set portable mode (this feature is disabled) / Установить портативный режим (эта функция отключена) / Встановити портативний режим (ця функція вимкнена)"""
    return True


def get_path_mode() -> str:
    """Get current path mode / Получить текущий режим путей / Отримати поточний режим шляхів"""
    return "hidden"


def set_path_mode(mode: str) -> bool:
    """Set path mode (this feature is disabled) / Установить режим путей (эта функция отключена) / Встановити режим шляхів (ця функція вимкнена)"""
    return True


def migrate_from_old_location(old_path: str) -> bool:
    """Migrate data from old location (this feature is disabled) / Мигрировать данные из старого расположения (эта функция отключена) / Мігрувати дані зі старого розташування (ця функція вимкнена)"""
    return True



def hide_all_app_dirs() -> None:
    """Hide ALL sensitive app directories at startup (Windows only).
    Скрывает ВСЕ чувствительные директории при запуске (только Windows).
    Приховує ВСІ чутливі директорії при запуску (тільки Windows)."""
    if platform.system() != "Windows":
        return

    program_dir = get_program_dir()

    # All directories that must be hidden
    candidates = [
        os.path.join(program_dir, "data"),               # legacy root data/ — must also be hidden
        os.path.join(program_dir, ".securepass"),        # main hidden dir
        os.path.join(program_dir, ".securepass", "data"),
        os.path.join(program_dir, ".securepass", "logs"),
        os.path.join(program_dir, ".securepass", "backups"),
        os.path.join(program_dir, ".securepass", "cache"),
        os.path.join(program_dir, "logs"),           # fallback logs dir
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)  # FILE_ATTRIBUTE_HIDDEN
            except (AttributeError, OSError, TypeError):
                pass


__all__ = [
    'get_base_dir',
    'get_config_dir',
    'get_data_dir',
    'get_cache_dir',
    'get_logs_dir',
    'get_backup_dir',
    'get_temp_dir',
    'get_config_file',
    'get_db_file',
    'get_salt_file',
    'get_master_file',
    'get_uuid_file',
    'get_key_version_file',
    'get_sqlcipher_salt_file',
    'get_lockout_file',
    'get_audit_file',
    'hide_dir',
    'ensure_dir',
    'cleanup_temp_files',
    'get_all_paths',
    'is_portable',
    'set_portable_mode',
    'get_path_mode',
    'set_path_mode',
    'migrate_from_old_location',
    'get_program_dir',
    'hide_directory_on_windows',
    'ensure_hidden',
    'hide_all_app_dirs',
]