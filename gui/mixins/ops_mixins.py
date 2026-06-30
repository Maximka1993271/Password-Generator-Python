"""
Operation-related mixins grouped together

Миксины, связанные с операциями, сгруппированные вместе
Міксини, пов'язані з операціями, згруповані разом

FIXED #C10: Fixed circular import - now properly imports from submodules
FIXED: Fixed export of PasswordOpsMixin and NameGeneratorMixin
FIXED: Added proper 3-language support in comments

Исправлено #C10: Исправлен циклический импорт - теперь правильно импортирует из подмодулей
Исправлено: Исправлен экспорт PasswordOpsMixin и NameGeneratorMixin
Исправлено: Добавлена правильная поддержка 3 языков в комментариях

Виправлено #C10: Виправлено циклічний імпорт - тепер правильно імпортує з підмодулів
Виправлено: Виправлено експорт PasswordOpsMixin та NameGeneratorMixin
Виправлено: Додано правильну підтримку 3 мов у коментарях

EN: This file serves as a central export point for operation-related mixins.
RU: Этот файл служит центральной точкой экспорта для миксинов, связанных с операциями.
UA: Цей файл слугує центральною точкою експорту для міксинів, пов'язаних з операціями.
"""
from __future__ import annotations

# ==================== IMPORTS ====================
# EN: Import from submodules (no circular dependencies)
# RU: Импорт из подмодулей (без циклических зависимостей)
# UA: Імпорт з підмодулів (без циклічних залежностей)

# EN: Direct import of PasswordOpsMixin from its module
# RU: Прямой импорт PasswordOpsMixin из его модуля
# UA: Прямий імпорт PasswordOpsMixin з його модуля
from gui.mixins.password_ops_mixin import PasswordOpsMixin

# EN: Direct import of NameGeneratorMixin from its module
# RU: Прямой импорт NameGeneratorMixin из его модуля
# UA: Прямий імпорт NameGeneratorMixin з його модуля
from gui.mixins.name_generator_mixin import NameGeneratorMixin

# ==================== EXPORTS ====================
# EN: Export all mixins for use in other modules
# RU: Экспорт всех миксинов для использования в других модулях
# UA: Експорт всіх міксинів для використання в інших модулях

__all__ = [
    'PasswordOpsMixin',
    'NameGeneratorMixin'
]

# ==================== CLASS ALIASES (FOR BACKWARD COMPATIBILITY) ====================
# EN: Keep old class names for backward compatibility with existing code
# RU: Сохраняем старые имена классов для обратной совместимости с существующим кодом
# UA: Зберігаємо старі імена класів для зворотної сумісності з існуючим кодом

OpsMixinsContainer = PasswordOpsMixin
NameGenContainer = NameGeneratorMixin

# ==================== COMBINED OPS CLASS (OPTIONAL) ====================
# EN: Optional combined class if someone needs both mixins in one
# RU: Опциональный объединённый класс, если кому-то нужны оба миксина
# UA: Опціональний об'єднаний клас, якщо комусь потрібні обидва міксини


class CombinedOpsMixins(PasswordOpsMixin, NameGeneratorMixin):
    """
    Combined class that inherits from both operation mixins.
    Use this if you need both password operations and name generation.

    Объединённый класс, наследующий от обоих миксинов операций.
    Используйте этот класс, если вам нужны и операции с паролями, и генерация имён.

    Об'єднаний клас, що успадковує від обох міксинів операцій.
    Використовуйте цей клас, якщо вам потрібні і операції з паролями, і генерація імен.
    """
    pass


# ==================== HELPER FUNCTIONS ====================
# EN: Helper functions to check if a class has specific operation methods
# RU: Вспомогательные функции для проверки наличия определённых методов операций
# UA: Допоміжні функції для перевірки наявності певних методів операцій


def has_password_ops(cls) -> bool:
    """
    Check if a class has password operations methods.

    Проверяет, есть ли у класса методы операций с паролями.
    Перевіряє, чи є у класу методи операцій з паролями.

    Args:
        cls: Class to check / Класс для проверки / Клас для перевірки

    Returns:
        True if the class has password operations methods / True если класс имеет методы операций с паролями / True якщо клас має методи операцій з паролями
    """
    return hasattr(cls, '_generate') and hasattr(cls, '_copy') and hasattr(cls, '_save')


def has_name_gen_ops(cls) -> bool:
    """
    Check if a class has name generator methods.

    Проверяет, есть ли у класса методы генератора имён.
    Перевіряє, чи є у класу методи генератора імен.

    Args:
        cls: Class to check / Класс для проверки / Клас для перевірки

    Returns:
        True if the class has name generator methods / True если класс имеет методы генератора имён / True якщо клас має методи генератора імен
    """
    return hasattr(cls, '_open_name_generator') and hasattr(cls, '_generate_name_async')


def has_generation_ops(cls) -> bool:
    """
    Check if a class has generation operations (both password and name).

    Проверяет, есть ли у класса операции генерации (и паролей, и имён).
    Перевіряє, чи є у класу операції генерації (і паролів, і імен).

    Args:
        cls: Class to check / Класс для проверки / Клас для перевірки

    Returns:
        True if the class has both password and name generation / True если класс имеет генерацию паролей и имён / True якщо клас має генерацію паролів та імен
    """
    return has_password_ops(cls) and has_name_gen_ops(cls)


# ==================== DOCUMENTATION ====================
# EN: Module documentation
# RU: Документация модуля
# UA: Документація модуля

"""
OPERATIONS MIXINS - OVERVIEW / ОБЗОР / ОГЛЯД

This module exports the following mixins:
1. PasswordOpsMixin - Password generation, copy, save, open operations
2. NameGeneratorMixin - Name generation for various purposes (SAMP, email, game, etc.)

Usage example / Пример использования / Приклад використання:
    from gui.mixins.ops_mixins import PasswordOpsMixin, NameGeneratorMixin

    class MyWidget(PasswordOpsMixin, NameGeneratorMixin):
        pass

The CombinedOpsMixins class combines both for convenience.
Класс CombinedOpsMixins объединяет оба для удобства.
Клас CombinedOpsMixins об'єднує обидва для зручності.
"""

# ==================== FIX: ENSURE DIRECT CLASS AVAILABILITY ====================
# EN: Make sure PasswordOpsMixin is directly available at module level
# RU: Убеждаемся, что PasswordOpsMixin доступен напрямую на уровне модуля
# UA: Переконуємось, що PasswordOpsMixin доступний безпосередньо на рівні модуля

# This ensures that 'from gui.mixins.ops_mixins import PasswordOpsMixin' works
# Это гарантирует, что 'from gui.mixins.ops_mixins import PasswordOpsMixin' работает
# Це гарантує, що 'from gui.mixins.ops_mixins import PasswordOpsMixin' працює

# Re-export for clarity / Повторный экспорт для ясности / Повторний експорт для ясності
PasswordOpsMixin = PasswordOpsMixin
NameGeneratorMixin = NameGeneratorMixin