from __future__ import annotations
# storage/config_accessors.py
"""
Config accessors module for Secure Pass Pro.
Модуль Config accessors для Secure Pass Pro.
Модуль Config accessors для Secure Pass Pro.
"""
"""
Config accessors module for Secure Pass Pro.
Модуль Config accessors для Secure Pass Pro.
Модуль Config accessors для Secure Pass Pro.
"""
"""
Configuration accessor methods - get, set, update, reset, validate
Методы доступа к конфигурации - get, set, update, reset, validate
Методи доступу до конфігурації - get, set, update, reset, validate
"""
import os
from typing import Dict, Any, List, Tuple
from storage.config_constants import logger, CONFIG_SCHEMA, SCHEMA_VERSION, _is_sensitive_config_key
from storage.config_crypto import _decrypt_config_value, _encrypt_config_value
from storage.config_helpers import _validate_config


class ConfigAccessorsMixin:
    """Config accessor methods (get, set, update, reset, validate)
    Методы доступа к конфигурации (get, set, update, reset, validate)
    Методи доступу до конфігурації (get, set, update, reset, validate)"""

    def get(self, key: str, default=None):
        """
        Get config value with type validation and decryption for sensitive keys
        
        Получить значение конфигурации с проверкой типа и дешифрованием для чувствительных ключей
        Отримати значення конфігурації з перевіркою типу та дешифруванням для чутливих ключів
        """
        value = self._data.get(key, default)

        if key in CONFIG_SCHEMA and value is not None:
            expected_type = CONFIG_SCHEMA[key]["type"]
            if not isinstance(value, expected_type):
                logger.warning(f"Config key '{key}' has wrong type, returning default / Ключ конфигурации '{key}' имеет неверный тип, возвращаем значение по умолчанию / Ключ конфігурації '{key}' має невірний тип, повертаємо значення за замовчуванням")
                return CONFIG_SCHEMA[key]["default"]

        if key == "2fa_secret" and isinstance(value, str) and value.startswith("[enc"):
            return _decrypt_config_value(value)

        return value

    def set(self, key: str, value) -> bool:
        """
        Set config value with validation and encryption for sensitive keys.
        
        Установить значение конфигурации с проверкой и шифрованием для чувствительных ключей.
        Встановити значення конфігурації з перевіркою та шифруванням для чутливих ключів.
        """
        with self._lock:
            if key in CONFIG_SCHEMA:
                schema = CONFIG_SCHEMA[key]

                if not isinstance(value, schema["type"]):
                    logger.error(f"Config key '{key}' expects type {schema['type'].__name__}, got {type(value).__name__} / Ключ конфигурации '{key}' ожидает тип {schema['type'].__name__}, получен {type(value).__name__} / Ключ конфігурації '{key}' очікує тип {schema['type'].__name__}, отримано {type(value).__name__}")
                    return False

                if "allowed" in schema and value not in schema["allowed"]:
                    logger.error(f"Config key '{key}' value '{value}' not allowed. Allowed: {schema['allowed']} / Значение '{value}' для ключа '{key}' не разрешено. Разрешены: {schema['allowed']} / Значення '{value}' для ключа '{key}' не дозволено. Дозволені: {schema['allowed']}")
                    return False

                if "min" in schema and isinstance(value, (int, float)) and value < schema["min"]:
                    logger.error(f"Config key '{key}' value {value} below minimum {schema['min']} / Значение {value} для ключа '{key}' ниже минимума {schema['min']} / Значення {value} для ключа '{key}' нижче мінімуму {schema['min']}")
                    return False

                if "max" in schema and isinstance(value, (int, float)) and value > schema["max"]:
                    logger.error(f"Config key '{key}' value {value} above maximum {schema['max']} / Значение {value} для ключа '{key}' выше максимума {schema['max']} / Значення {value} для ключа '{key}' вище максимуму {schema['max']}")
                    return False

            if key == "2fa_secret" and isinstance(value, str) and value and not value.startswith("[enc"):
                value = _encrypt_config_value(value)

            old_value = self._data.get(key)
            self._data[key] = value
            result = self.save()

            if result:
                if _is_sensitive_config_key(key):
                    logger.info(f"Config key '{key}' changed / Ключ конфигурации '{key}' изменён / Ключ конфігурації '{key}' змінено")
                else:
                    logger.info(f"Config key '{key}' changed from '{old_value}' to '{value}' / Ключ конфигурации '{key}' изменён с '{old_value}' на '{value}' / Ключ конфігурації '{key}' змінено з '{old_value}' на '{value}'")
            else:
                logger.error(f"Failed to save config key '{key}' / Не удалось сохранить ключ конфигурации '{key}' / Не вдалося зберегти ключ конфігурації '{key}'")
                self._data[key] = old_value

            return result

    def update(self, updates: Dict[str, Any]) -> int:
        """
        Update multiple config values.
        
        Обновить несколько значений конфигурации.
        Оновити кілька значень конфігурації.
        """
        success_count = 0
        for key, value in updates.items():
            if self.set(key, value):
                success_count += 1
            else:
                logger.error(f"Failed to update config key '{key}' / Не удалось обновить ключ конфигурации '{key}' / Не вдалося оновити ключ конфігурації '{key}'")

        if success_count > 0:
            self.save()

        return success_count

    def reset_to_defaults(self) -> bool:
        """
        Reset all settings to defaults
        
        Сбросить все настройки к значениям по умолчанию
        Скинути всі налаштування до значень за замовчуванням
        """
        with self._lock:
            self._data = self._get_default_config()
            self._data["_schema_version"] = SCHEMA_VERSION
            return self.save()

    def validate_all(self) -> Tuple[bool, List[str]]:
        """
        Validate entire config.
        
        Проверить всю конфигурацию.
        Перевірити всю конфігурацію.
        """
        _, errors = _validate_config(self._data)
        return len(errors) == 0, errors

    def get_validation_errors(self) -> List[str]:
        """
        Get last validation errors
        
        Получить последние ошибки проверки
        Отримати останні помилки перевірки
        """
        return self._validation_errors.copy()

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get schema information for UI
        
        Получить информацию о схеме для UI
        Отримати інформацію про схему для UI
        """
        info = {}
        for key, schema in CONFIG_SCHEMA.items():
            info[key] = {
                "type": schema["type"].__name__,
                "default": schema["default"],
                "current": self._data.get(key, schema["default"]),
                "encrypted": schema.get("encrypted", False)
            }
            if "allowed" in schema:
                info[key]["allowed"] = schema["allowed"]
            if "min" in schema:
                info[key]["min"] = schema["min"]
            if "max" in schema:
                info[key]["max"] = schema["max"]
        return info

    def get_version(self) -> int:
        """
        Get current config schema version
        
        Получить текущую версию схемы конфигурации
        Отримати поточну версію схеми конфігурації
        """
        return self._data.get("_schema_version", 1)

    def has_key(self, key: str) -> bool:
        """
        Check if key exists in config
        
        Проверить, существует ли ключ в конфигурации
        Перевірити, чи існує ключ у конфігурації
        """
        return key in self._data

    def get_all(self) -> Dict[str, Any]:
        """
        Get a copy of all config data
        
        Получить копию всех данных конфигурации
        Отримати копію всіх даних конфігурації
        """
