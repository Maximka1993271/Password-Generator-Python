"""
GUI Mixins - grouped by functionality for better organization

Группировка миксинов по функциональности для лучшей организации
Групування міксинів за функціональністю для кращої організації

FIXED #36: Removed duplicate imports - only import from grouped files
FIXED #37: Simplified inheritance hierarchy - using composition over deep inheritance
FIXED: Fixed imports to properly load all mixins

Исправлено #36: Убраны дублирующиеся импорты - только из grouped файлов
Исправлено #37: Упрощена иерархия наследования - использование композиции вместо глубокого наследования
Исправлено: Исправлены импорты для правильной загрузки всех миксинов

Виправлено #36: Прибрано дублюючі імпорти - тільки з grouped файлів
Виправлено #37: Спрощено ієрархію наслідування - використання композиції замість глибокого наслідування
Виправлено: Виправлено імпорти для правильного завантаження всіх міксинів
"""
from __future__ import annotations

# ==================== IMPORTS FROM GROUPED FILES ====================
# FIXED #36: Import only from grouped files, not from individual files
# Исправлено #36: Импортируем только из grouped файлов, не из отдельных файлов
# Виправлено #36: Імпортуємо тільки з grouped файлів, не з окремих файлів

from gui.mixins.ui_mixins import (
    UISetupMixin,
    SettingsMixin,
    SettingsWindowMixin,
    DialogsMixin
)

from gui.mixins.security_mixins import (
    MasterMixin,
    AutoLockMixin,
    HIBPMixin
)

# FIXED: Import directly from the files, not from ops_mixins wrapper
# Исправлено: Импортируем напрямую из файлов, а не из обёртки ops_mixins
# Виправлено: Імпортуємо напряму з файлів, а не з обгортки ops_mixins
from gui.mixins.password_ops_mixin import PasswordOpsMixin
from gui.mixins.name_generator_mixin import NameGeneratorMixin

from gui.mixins.visual_mixins import (
    RGBMixin,
    UpdaterMixin
)

# ==================== EXPORT ALL MIXINS ====================
# Экспорт всех миксинов / Експорт всіх міксинів

__all__ = [
    # UI Mixins
    'UISetupMixin',
    'SettingsMixin',
    'SettingsWindowMixin',
    'DialogsMixin',
    # Security Mixins
    'MasterMixin',
    'AutoLockMixin',
    'HIBPMixin',
    # Operations Mixins
    'PasswordOpsMixin',
    'NameGeneratorMixin',
    # Visual Mixins
    'RGBMixin',
    'UpdaterMixin',
    # Container classes
    'UIMixins',
    'SecurityMixins',
    'OpsMixins',
    'VisualMixins',
    'AllMixins'
]

# ==================== CONTAINER CLASSES ====================

class UIMixins(
    UISetupMixin,
    SettingsMixin,
    SettingsWindowMixin,
    DialogsMixin
):
    """Container for all UI mixins.

    Контейнер для всех UI миксинов.
    Контейнер для всіх UI міксинів.
    """
    pass


class SecurityMixins(
    MasterMixin,
    AutoLockMixin,
    HIBPMixin
):
    """Container for all security mixins.

    Контейнер для всех миксинов безопасности.
    Контейнер для всіх міксинів безпеки.
    """
    pass


class OpsMixins(
    PasswordOpsMixin,
    NameGeneratorMixin
):
    """Container for all operations mixins.

    Контейнер для всех миксинов операций.
    Контейнер для всіх міксинів операцій.
    """
    pass


class VisualMixins(
    RGBMixin,
    UpdaterMixin
):
    """Container for all visual mixins.

    Контейнер для всех визуальных миксинов.
    Контейнер для всіх візуальних міксинів.
    """
    pass


class AllMixins(
    UIMixins,
    SecurityMixins,
    OpsMixins,
    VisualMixins
):
    """
    Container for all mixins.
    Use this class instead of inheriting 11 separate mixins.

    Контейнер для всех миксинов.
    Используйте этот класс вместо наследования 11 отдельных миксинов.

    Контейнер для всіх міксинів.
    Використовуйте цей клас замість успадкування 11 окремих міксинів.
    """
    pass


# ==================== BACKWARD COMPATIBILITY ALIASES ====================

UIMixinsAlias = UIMixins
SecurityMixinsAlias = SecurityMixins
OpsMixinsAlias = OpsMixins
VisualMixinsAlias = VisualMixins
AllMixinsAlias = AllMixins