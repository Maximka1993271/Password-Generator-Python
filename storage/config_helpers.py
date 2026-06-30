from __future__ import annotations
# storage/config_helpers.py
"""
Config helpers module for Secure Pass Pro.
Модуль Config helpers для Secure Pass Pro.
Модуль Config helpers для Secure Pass Pro.
"""
"""
Config helpers module for Secure Pass Pro.
Модуль Config helpers для Secure Pass Pro.
Модуль Config helpers для Secure Pass Pro.
"""
"""
Helper functions for configuration management
Вспомогательные функции для управления конфигурацией
Допоміжні функції для керування конфігурацією

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

import os
import sys
import json
import time
import shutil
import copy
import tempfile
from typing import Dict, Any, List, Tuple, Optional

from storage.config_paths import get_config_dir, hide_dir
from storage.config_constants import (
    logger, SCHEMA_VERSION, CONFIG_SCHEMA, _is_sensitive_config_key
)
from storage.config_crypto import _encrypt_config_value, _decrypt_config_value
from storage.config_backup import ConfigBackup
from storage.config_exceptions import ConfigCorruptionError


# ==================== HELPER FUNCTIONS ====================

def _atomic_write_json(path: str, data: Dict[str, Any]) -> bool:
    """
    Atomic JSON write with integrity check

    Атомарная запись JSON с проверкой целостности
    Атомарний запис JSON з перевіркою цілісності
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    hide_dir(directory)

    try:
        content = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')

        from storage.config_file_ops import secure_write
        if not secure_write(path, content, make_hidden=True):
            return False

        from storage.config_file_ops import secure_read
        read_content = secure_read(path)
        if read_content:
            test_data = json.loads(read_content.decode('utf-8'))
            if test_data != data:
                logger.error("JSON integrity check failed - data mismatch / Проверка целостности JSON не пройдена - несоответствие данных / Перевірку цілісності JSON не пройдено - невідповідність даних")
                return False

        return True
    except (OSError, IOError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Atomic write failed / Ошибка атомарной записи / Помилка атомарного запису: {e}")
        return False


def _create_backup(config_path: str) -> Optional[ConfigBackup]:
    """
    Create backup of config file

    Создаёт резервную копию конфига
    Створює резервну копію конфігу
    """
    if not os.path.exists(config_path):
        return None

    backup_dir = os.path.join(get_config_dir(), "config_backups")
    os.makedirs(backup_dir, exist_ok=True)
    hide_dir(backup_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"config_backup_{timestamp}.json")

    try:
        shutil.copy2(config_path, backup_path)
        logger.debug(f"Config backup created: {backup_path} / Создана резервная копия конфига: {backup_path} / Створено резервну копію конфігу: {backup_path}")

        version = 1
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version = data.get("_schema_version", 1)
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.debug(f"Failed to read backup version / Ошибка чтения версии бэкапа / Помилка читання версії бекапу: {e}")

        return ConfigBackup(
            path=backup_path,
            timestamp=time.time(),
            version=version,
            size=os.path.getsize(backup_path)
        )
    except (OSError, IOError, PermissionError, shutil.Error) as e:
        logger.error(f"Failed to create config backup / Ошибка создания резервной копии конфига / Помилка створення резервної копії конфігу: {e}")
        return None


def _cleanup_old_backups(backup_dir: str, max_backups: int = 10) -> None:
    """
    Clean up old backups

    Очищает старые резервные копии
    Очищує старі резервні копії
    """
    try:
        if not os.path.exists(backup_dir):
            return

        backups = []
        for f in os.listdir(backup_dir):
            if f.startswith("config_backup_") and f.endswith(".json"):
                f_path = os.path.join(backup_dir, f)
                backups.append((f_path, os.path.getmtime(f_path)))

        backups.sort(key=lambda x: x[1])

        while len(backups) > max_backups:
            old_file = backups.pop(0)[0]
            try:
                os.remove(old_file)
                logger.debug(f"Removed old backup: {old_file} / Удалён старый бэкап: {old_file} / Видалено старий бекап: {old_file}")
            except (OSError, IOError, PermissionError) as e:
                logger.warning(f"Failed to remove old backup / Ошибка удаления старого бэкапа / Помилка видалення старого бекапу: {e}")
    except (OSError, IOError) as e:
        logger.debug(f"Backup cleanup error / Ошибка очистки бэкапов / Помилка очищення бекапів: {e}")


def _get_available_backups() -> List[ConfigBackup]:
    """
    Get list of available backups

    Получить список доступных резервных копий
    Отримати список доступних резервних копій
    """
    backup_dir = os.path.join(get_config_dir(), "config_backups")
    backups = []

    if not os.path.exists(backup_dir):
        return backups

    try:
        for f in os.listdir(backup_dir):
            if f.startswith("config_backup_") and f.endswith(".json"):
                f_path = os.path.join(backup_dir, f)
                try:
                    with open(f_path, 'r', encoding='utf-8') as bf:
                        data = json.load(bf)
                        version = data.get("_schema_version", 1)

                    backups.append(ConfigBackup(
                        path=f_path,
                        timestamp=os.path.getmtime(f_path),
                        version=version,
                        size=os.path.getsize(f_path)
                    ))
                except (OSError, IOError, json.JSONDecodeError) as e:
                    logger.debug(f"Failed to read backup {f}: {e} / Ошибка чтения бэкапа {f} / Помилка читання бекапу {f}")
    except (OSError, IOError) as e:
        logger.debug(f"Failed to list backups / Ошибка списка бэкапов / Помилка списку бекапів: {e}")

    backups.sort(key=lambda x: x.timestamp, reverse=True)
    return backups


def _validate_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validate configuration by schema

    Валидация конфигурации по схеме
    Валідація конфігурації за схемою
    """
    validated = {}
    errors = []

    for key, schema in CONFIG_SCHEMA.items():
        value = config.get(key, copy.deepcopy(schema["default"]))

        if not isinstance(value, schema["type"]):
            errors.append(f"Config key '{key}' has wrong type {type(value).__name__}, expected {schema['type'].__name__} / Ключ конфигурации '{key}' имеет неверный тип {type(value).__name__}, ожидался {schema['type'].__name__} / Ключ конфігурації '{key}' має невірний тип {type(value).__name__}, очікувався {schema['type'].__name__}")
            logger.warning(f"Config key '{key}' has wrong type, using default: {schema['default']} / Ключ конфигурации '{key}' имеет неверный тип, используется значение по умолчанию: {schema['default']} / Ключ конфігурації '{key}' має невірний тип, використовується значення за замовчуванням: {schema['default']}")
            value = copy.deepcopy(schema["default"])

        if "allowed" in schema and value not in schema["allowed"]:
            errors.append(f"Config key '{key}' value '{value}' not allowed. Allowed: {schema['allowed']} / Значение '{value}' для ключа '{key}' не разрешено. Разрешены: {schema['allowed']} / Значення '{value}' для ключа '{key}' не дозволено. Дозволені: {schema['allowed']}")
            logger.warning(f"Config key '{key}' value '{value}' not allowed, using default: {schema['default']} / Значение '{value}' для ключа '{key}' не разрешено, используется значение по умолчанию: {schema['default']} / Значення '{value}' для ключа '{key}' не дозволено, використовується значення за замовчуванням: {schema['default']}")
            value = copy.deepcopy(schema["default"])

        if "min" in schema and isinstance(value, (int, float)) and value < schema["min"]:
            errors.append(f"Config key '{key}' value {value} below minimum {schema['min']} / Значение {value} для ключа '{key}' ниже минимума {schema['min']} / Значення {value} для ключа '{key}' нижче мінімуму {schema['min']}")
            logger.warning(f"Config key '{key}' value {value} below min {schema['min']}, using default: {schema['default']} / Значение {value} для ключа '{key}' ниже минимума {schema['min']}, используется значение по умолчанию: {schema['default']} / Значення {value} для ключа '{key}' нижче мінімуму {schema['min']}, використовується значення за замовчуванням: {schema['default']}")
            value = copy.deepcopy(schema["default"])

        if "max" in schema and isinstance(value, (int, float)) and value > schema["max"]:
            errors.append(f"Config key '{key}' value {value} above maximum {schema['max']} / Значение {value} для ключа '{key}' выше максимума {schema['max']} / Значення {value} для ключа '{key}' вище максимуму {schema['max']}")
            logger.warning(f"Config key '{key}' value {value} above max {schema['max']}, using default: {schema['default']} / Значение {value} для ключа '{key}' выше максимума {schema['max']}, используется значение по умолчанию: {schema['default']} / Значення {value} для ключа '{key}' вище максимуму {schema['max']}, використовується значення за замовчуванням: {schema['default']}")
            value = copy.deepcopy(schema["default"])

        validated[key] = value

    for key, value in config.items():
        if key not in validated and not key.startswith("_"):
            validated[key] = value

    return validated, errors


def _migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate config from older versions

    Миграция конфигурации из старых версий
    Міграція конфігурації зі старих версій
    """
    version = config.get("_schema_version", 1)

    if version >= SCHEMA_VERSION:
        return config

    logger.info(f"Migrating config from version {version} to {SCHEMA_VERSION} / Миграция конфигурации с версии {version} на {SCHEMA_VERSION} / Міграція конфігурації з версії {version} на {SCHEMA_VERSION}")

    _create_backup(get_config_file())

    try:
        from storage.config_migrations import SCHEMA_MIGRATIONS

        for v in range(version + 1, SCHEMA_VERSION + 1):
            if v in SCHEMA_MIGRATIONS:
                config = SCHEMA_MIGRATIONS[v](config)

        if version == 1:
            for key, schema in CONFIG_SCHEMA.items():
                if key not in config:
                    config[key] = schema["default"]
            if "PDF_THEME" not in config:
                config["PDF_THEME"] = "light"
            config["_schema_version"] = 2

        if version <= 2:
            for key, schema in CONFIG_SCHEMA.items():
                if key in config:
                    value = config[key]
                    if "allowed" in schema and value not in schema["allowed"]:
                        config[key] = schema["default"]
                        logger.warning(f"Migrated invalid value for {key} to default: {schema['default']} / Некорректное значение для {key} мигрировано к значению по умолчанию: {schema['default']} / Некорректне значення для {key} мігровано до значення за замовчуванням: {schema['default']}")
            config["_schema_version"] = 3

        if version <= 3:
            for key in ["2fa_enabled", "2fa_secret", "2fa_backup_hashes",
                        "2fa_account_name", "2fa_setup_completed", "2fa_last_verified"]:
                if key not in config:
                    config[key] = CONFIG_SCHEMA.get(key, {"default": None})["default"]
            config["_schema_version"] = 4
            logger.info("Added 2FA configuration fields during migration / Добавлены поля конфигурации 2FA во время миграции / Додано поля конфігурації 2FA під час міграції")

        if version <= 4:
            secret = config.get("2fa_secret", "")
            if secret and not secret.startswith("[enc]"):
                config["2fa_secret"] = _encrypt_config_value(secret)
                logger.info("Encrypted existing 2FA secret during migration / Существующий секрет 2FA зашифрован во время миграции / Існуючий секрет 2FA зашифровано під час міграції")
            config["_schema_version"] = 5

        logger.info(f"Config migrated to version {SCHEMA_VERSION} / Конфигурация мигрирована на версию {SCHEMA_VERSION} / Конфігурацію мігровано на версію {SCHEMA_VERSION}")
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Migration error / Ошибка миграции / Помилка міграції: {e}")
        from storage.config_exceptions import ConfigMigrationError
        raise ConfigMigrationError(f"Failed to migrate config / Ошибка миграции конфигурации / Помилка міграції конфігурації: {e}")

    return config


def _repair_config(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to repair corrupted config

    Попытка восстановить повреждённый конфиг
    Спроба відновити пошкоджений конфіг
    """
    logger.warning(f"Attempting to repair config: {file_path} / Попытка восстановления конфига: {file_path} / Спроба відновлення конфігу: {file_path}")

    backup_path = file_path + ".corrupted"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup of corrupted config saved to: {backup_path} / Резервная копия повреждённого конфига сохранена в: {backup_path} / Резервну копію пошкодженого конфігу збережено в: {backup_path}")
    except (OSError, IOError, PermissionError, shutil.Error) as e:
        logger.warning(f"Failed to backup corrupted config / Ошибка резервного копирования повреждённого конфига / Помилка резервного копіювання пошкодженого конфігу: {e}")

    try:
        import re
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        clean_content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)

        json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
        if json_match:
            clean_content = json_match.group()

        try:
            repaired = json.loads(clean_content)
            logger.info("Config successfully repaired / Конфиг успешно восстановлен / Конфіг успішно відновлено")
            return repaired
        except json.JSONDecodeError:
            clean_content = clean_content.replace("'", '"')
            clean_content = re.sub(r'//.*?$', '', clean_content, flags=re.MULTILINE)
            clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
            try:
                repaired = json.loads(clean_content)
                logger.info("Config successfully repaired (aggressive mode) / Конфиг успешно восстановлен (агрессивный режим) / Конфіг успішно відновлено (агресивний режим)")
                return repaired
            except json.JSONDecodeError:
                return _restore_from_backup()
    except (OSError, IOError) as e:
        logger.error(f"Config repair failed / Ошибка восстановления конфига / Помилка відновлення конфігу: {e}")

    return _restore_from_backup()


def _restore_from_backup() -> Optional[Dict[str, Any]]:
    """
    Restore config from latest backup

    Восстанавливает конфиг из последнего бэкапа
    Відновлює конфіг з останнього бекапу
    """
    backups = _get_available_backups()

    if not backups:
        logger.warning("No backups found for recovery / Не найдено резервных копий для восстановления / Не знайдено резервних копій для відновлення")
        return None

    latest_backup = backups[0].path

    try:
        with open(latest_backup, 'r', encoding='utf-8') as f:
            restored = json.load(f)
        logger.info(f"Config restored from backup: {latest_backup} / Конфиг восстановлен из резервной копии: {latest_backup} / Конфіг відновлено з резервної копії: {latest_backup}")
        return restored
    except (OSError, IOError, json.JSONDecodeError) as e:
        logger.error(f"Backup restore failed / Ошибка восстановления из бэкапа / Помилка відновлення з бекапу: {e}")
        return None


# Import here to avoid circular import
import datetime
from storage.config_paths import get_config_file


__all__ = [
    '_atomic_write_json',
    '_create_backup',
    '_cleanup_old_backups',
    '_get_available_backups',
    '_validate_config',
    '_migrate_config',
    '_repair_config',
    '_restore_from_backup',

]
