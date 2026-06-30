from __future__ import annotations
# storage/config_exceptions.py
"""
Config exceptions module for Secure Pass Pro.
Модуль Config exceptions для Secure Pass Pro.
Модуль Config exceptions для Secure Pass Pro.
"""
"""
Config exceptions module for Secure Pass Pro.
Модуль Config exceptions для Secure Pass Pro.
Модуль Config exceptions для Secure Pass Pro.
"""
"""
Configuration exception classes
Классы исключений для конфигурации
Класи винятків для конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""


class ConfigError(Exception):
    """Exception for configuration errors
    Исключение для ошибок конфигурации
    Виняток для помилок конфігурації"""
    pass


class ConfigCorruptionError(ConfigError):
    """Exception for configuration corruption
    Исключение для повреждения конфигурации
    Виняток для пошкодження конфігурації"""
    pass


class ConfigMigrationError(ConfigError):
    """Exception for migration errors
    Исключение для ошибок миграции
    Виняток для помилок міграції"""
    pass


class ConfigValidationError(ConfigError):
    """Exception for validation errors
    Исключение для ошибок проверки
    Виняток для помилок перевірки"""
    pass


__all__ = [
    'ConfigError',
    'ConfigCorruptionError',
    'ConfigMigrationError',
    'ConfigValidationError',

]
