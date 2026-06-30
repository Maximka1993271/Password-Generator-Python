from __future__ import annotations
# storage/config_base.py
"""
Config base module for Secure Pass Pro.
Модуль Config base для Secure Pass Pro.
Модуль Config base для Secure Pass Pro.
"""
"""
Config base module for Secure Pass Pro.
Модуль Config base для Secure Pass Pro.
Модуль Config base для Secure Pass Pro.
"""
"""
Configuration base class - loading, saving, backup management
Базовый класс конфигурации - загрузка, сохранение, управление резервными копиями
Базовий клас конфігурації - завантаження, збереження, керування резервними копіями
"""
import os
import json
import time
import threading
import copy
from typing import Dict, Any, List, Optional, Tuple

from storage.config_paths import get_config_file, get_config_dir
from storage.config_file_ops import secure_read
from storage.config_constants import logger, SCHEMA_VERSION, CONFIG_SCHEMA
from storage.config_helpers import (
    _atomic_write_json,
    _create_backup,
    _cleanup_old_backups,
    _validate_config,
    _migrate_config,
    _repair_config,
    _restore_from_backup,
)
from storage.config_exceptions import ConfigCorruptionError
from storage.config_2fa import Config2FAMixin


class ConfigBase(Config2FAMixin):
    """Base configuration class with loading, saving, and backup functionality
    Базовый класс конфигурации с функциональностью загрузки, сохранения и резервного копирования
    Базовий клас конфігурації з функціональністю завантаження, збереження та резервного копіювання"""

    _instance = None
    _lock = threading.RLock()
    _data: Dict[str, Any] = {}
    _backup_path: Optional[str] = None
    _config_file: Optional[str] = None
    _last_save_time: float = 0
    _save_cooldown: float = 0.5
    _validation_errors: List[str] = []

    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._config_file = get_config_file()
                    cls._instance._backup_path = cls._instance._config_file + ".backup"
                    cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """
        Load config from file with validation, recovery, and migration
        
        Загрузить конфигурацию из файла с проверкой, восстановлением и миграцией
        Завантажити конфігурацію з файлу з перевіркою, відновленням та міграцією
        """
        config_file = self._config_file

        if not os.path.exists(config_file):
            logger.info("Config file not found, creating default / Файл конфигурации не найден, создаём стандартный / Файл конфігурації не знайдено, створюємо стандартний")
            self._data = self._get_default_config()
            self._data["_schema_version"] = SCHEMA_VERSION
            self.save()
            return

        try:
            content = secure_read(config_file)
            if content:
                raw_data = json.loads(content.decode('utf-8'))
            else:
                raise ConfigCorruptionError("Empty config file / Пустой файл конфигурации / Порожній файл конфігурації")

            if raw_data.get("_schema_version", 1) < SCHEMA_VERSION:
                raw_data = _migrate_config(raw_data)

            validated_data, errors = _validate_config(raw_data)
            self._validation_errors = errors

            if errors:
                logger.warning(f"Config validation had {len(errors)} errors: {errors[:3]}... / Проверка конфигурации обнаружила {len(errors)} ошибок: {errors[:3]}... / Перевірка конфігурації виявила {len(errors)} помилок: {errors[:3]}...")

            self._data = validated_data
            self._data["_schema_version"] = SCHEMA_VERSION

            if validated_data != raw_data:
                logger.info("Config normalized, saving changes / Конфигурация нормализована, сохраняем изменения / Конфігурацію нормалізовано, зберігаємо зміни")
                self.save()

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error / Ошибка декодирования JSON / Помилка декодування JSON: {e}")
            repaired = _repair_config(config_file)
            if repaired:
                validated_data, errors = _validate_config(repaired)
                self._data = validated_data
                self._data["_schema_version"] = SCHEMA_VERSION
                self.save()
                logger.info("Config restored after corruption / Конфигурация восстановлена после повреждения / Конфігурацію відновлено після пошкодження")
            else:
                logger.warning("Using default config / Используется стандартная конфигурация / Використовується стандартна конфігурація")
                self._data = self._get_default_config()
                self._data["_schema_version"] = SCHEMA_VERSION
        except ConfigCorruptionError as e:
            logger.error(f"Config corruption / Повреждение конфигурации / Пошкодження конфігурації: {e}")
            self._data = self._get_default_config()
            self._data["_schema_version"] = SCHEMA_VERSION
        except (PermissionError, OSError, ValueError) as e:
            logger.error(f"Error reading config / Ошибка чтения конфигурации / Помилка читання конфігурації: {e}")
            self._data = self._get_default_config()
            self._data["_schema_version"] = SCHEMA_VERSION

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration
        
        Получить стандартную конфигурацию
        Отримати стандартну конфігурацію
        """
        return {key: copy.deepcopy(schema["default"]) for key, schema in CONFIG_SCHEMA.items()}

    def save(self) -> bool:
        """
        Save config to file with atomic write, backup, and cooldown
        
        Сохранить конфигурацию в файл с атомарной записью, резервным копированием и задержкой
        Зберегти конфігурацію у файл з атомарним записом, резервним копіюванням та затримкою
        """
        config_file = self._config_file
        current_time = time.time()

        if os.path.exists(config_file):
            _create_backup(config_file)

        save_data = self._data.copy()
        save_data["_schema_version"] = SCHEMA_VERSION

        success = _atomic_write_json(config_file, save_data)
        if success:
            self._last_save_time = current_time
            backup_dir = os.path.join(get_config_dir(), "config_backups")
            _cleanup_old_backups(backup_dir, max_backups=10)
            logger.debug(f"Config saved successfully to {config_file} / Конфигурация успешно сохранена в {config_file} / Конфігурацію успішно збережено в {config_file}")
        else:
            logger.error("Failed to save config / Ошибка сохранения конфигурации / Помилка збереження конфігурації")
            restored = _restore_from_backup()
            if restored:
                self._data = restored
                return self.save()

        return success

    def force_save(self) -> bool:
        """
        Force save settings (without cooldown check)
        
        Принудительно сохранить настройки (без проверки задержки)
        Примусово зберегти налаштування (без перевірки затримки)
        """
        config_file = self._config_file
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            save_data = self._data.copy()
            save_data["_schema_version"] = SCHEMA_VERSION
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            self._last_save_time = time.time()
            logger.info(f"Config force saved to: {config_file} / Конфигурация принудительно сохранена в: {config_file} / Конфігурацію примусово збережено в: {config_file}")
            return True
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.error(f"Failed to force save config / Ошибка принудительного сохранения конфигурации / Помилка примусового збереження конфігурації: {e}")
