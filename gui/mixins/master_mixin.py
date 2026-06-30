from __future__ import annotations
# master_mixin.py
"""
Master mixin module for Secure Pass Pro.
Модуль Master mixin для Secure Pass Pro.
Модуль Master mixin для Secure Pass Pro.
"""
"""
Master mixin module for Secure Pass Pro.
Модуль Master mixin для Secure Pass Pro.
Модуль Master mixin для Secure Pass Pro.
"""
"""
Master password mixin for SecurePassPro
FULL 3-LANGUAGE SUPPORT: RU, EN, UA

Миксин мастер-пароля для SecurePassPro
ПОЛНАЯ ПОДДЕРЖКА 3 ЯЗЫКОВ: RU, EN, UA

Міксин майстер-пароля для SecurePassPro
ПОВНА ПІДТРИМКА 3 МОВ: RU, EN, UA

FIXED #C3, #H5: Replaced non-existent CTkInputDialog with local _custom_input_dialog function
Исправлено #C3, #H5: Заменён несуществующий CTkInputDialog на локальную функцию _custom_input_dialog
Виправлено #C3, #H5: Замінено неіснуючий CTkInputDialog на локальну функцію _custom_input_dialog

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""

# ИСПРАВЛЕНИЕ: Относительные импорты из-за расположения внутри подпапки (точки)
# FIX: Relative imports due to location inside subfolder (dots)
# ВИПРАВЛЕННЯ: Відносні імпорти через розташування всередині підпапки (крапки)
from .master_mixin_base import (
    MasterPasswordError,
    _custom_input_dialog,
    CONFIG_DIR,
    MASTER_FILE
)

from .master_mixin_core import MasterMixinCore
from .master_mixin_ui import MasterMixinUI
from .master_mixin_2fa import MasterMixin2FA

from utils.logger import get_logger
logger = get_logger("master_mixin")


class MasterMixin(MasterMixinCore, MasterMixinUI, MasterMixin2FA):
    """
    Mixin class for master password management and lock screen

    Класс-миксин для управления мастер-паролем и экраном блокировки
    Клас-міксин для керування майстер-паролем та екраном блокування
    """
    pass