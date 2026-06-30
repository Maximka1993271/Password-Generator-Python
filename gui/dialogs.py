"""
Dialog module - main entry point.
Модуль диалогов - главная точка входа.
Модуль діалогів - головна точка входу.

FIXED: Added full type hints for all methods and exports
FIXED: Removed BOM (U+FEFF) character
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from gui.dialogs_base import (
    safe_winfo_exists,
    safe_focus,
    safe_destroy,
    safe_after_cancel,
    get_colors_for_theme,
    center_window_relative,
    setup_window_style,
    set_topmost_false
)
from gui.dialogs_tooltip import ToolTip
from gui.dialogs_custom_widgets import (
    CustomButton,
    CustomCheckBox,
    CustomEntry,
    CustomLabel,
    CustomSlider
)
from gui.dialogs_messagebox import CTkMessageBox
from gui.dialogs_input import CTkInputDialog
from gui.dialogs_about import create_about_dialog

# ==================== BACKWARD COMPATIBILITY ====================

# OriginalToolTip is kept as an alias for ToolTip for backward compatibility
# OriginalToolTip оставлен как алиас для ToolTip для обратной совместимости
# OriginalToolTip залишений як аліас для ToolTip для зворотної сумісності
OriginalToolTip = ToolTip

# ==================== EXPORTS ====================

__all__: List[str] = [
    # Base utilities
    'safe_winfo_exists',
    'safe_focus',
    'safe_destroy',
    'safe_after_cancel',
    'get_colors_for_theme',
    'center_window_relative',
    'setup_window_style',
    'set_topmost_false',
    # Tooltip
    'ToolTip',
    'OriginalToolTip',
    # Custom widgets
    'CustomButton',
    'CustomCheckBox',
    'CustomEntry',
    'CustomLabel',
    'CustomSlider',
    # Dialogs
    'CTkMessageBox',
    'CTkInputDialog',
    'create_about_dialog',
]
