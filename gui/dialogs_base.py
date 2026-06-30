"""
Base dialog classes and utilities.
Базовые классы диалогов и утилиты.
Базові класи діалогів та утиліти.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from utils.helpers import center_screen, get_global_radius
from utils.logger import get_logger
from Langs.lang import LANGUAGES

logger = get_logger("dialogs_base")


def safe_winfo_exists(widget: Optional[tk.Widget]) -> bool:
    """Safely check if a widget exists."""
    if widget is None:
        return False
    try:
        return widget.winfo_exists()
    except (tk.TclError, AttributeError, RuntimeError):
        return False


def safe_focus(widget: Optional[tk.Widget]) -> None:
    """Safely set focus on a widget if it exists."""
    try:
        if safe_winfo_exists(widget):
            widget.focus_set()
    except (tk.TclError, AttributeError, RuntimeError):
        pass


def safe_destroy(window: Optional[tk.Toplevel]) -> None:
    """Safely destroy a window if it exists."""
    if safe_winfo_exists(window):
        try:
            window.grab_release()
        except (tk.TclError, AttributeError, RuntimeError):
            pass
        try:
            window.destroy()
        except (tk.TclError, AttributeError, RuntimeError):
            pass


def safe_after_cancel(window: Optional[tk.Toplevel], after_id: Optional[str]) -> None:
    """Safely cancel an after callback."""
    if after_id is not None and safe_winfo_exists(window):
        try:
            window.after_cancel(after_id)
        except (tk.TclError, ValueError, RuntimeError):
            pass


def get_colors_for_theme(theme: str) -> Dict[str, str]:
    """
    Get colors based on theme.
    Получить цвета в зависимости от темы.
    Отримати кольори залежно від теми.
    """
    if theme == "light":
        return {
            "bg": "#F3F3F3",
            "fg": "#000000",
            "button_fg": "#1f538d",
            "button_text": "#FFFFFF",
            "label_text": "#000000",
            "entry_bg": "#FFFFFF",
            "icon_info": "#2ECC71",
            "icon_warning": "#FFA500",
            "icon_error": "#FF4444",
            "icon_question": "#4EC9B0",
            "icon_success": "#2ECC71"
        }
    else:
        return {
            "bg": "#1d1e1e",
            "fg": "#FFFFFF",
            "button_fg": "#1f538d",
            "button_text": "#FFFFFF",
            "label_text": "#FFFFFF",
            "entry_bg": "#2b2b2b",
            "icon_info": "#2ECC71",
            "icon_warning": "#FFA500",
            "icon_error": "#FF4444",
            "icon_question": "#4EC9B0",
            "icon_success": "#2ECC71"
        }


def center_window_relative(
    parent: Optional[tk.Widget],
    window: tk.Toplevel,
    width: int,
    height: int
) -> None:
    """Center window relative to parent."""
    try:
        if not safe_winfo_exists(parent):
            center_screen(window, width, height)
            return

        window.update_idletasks()
        parent.update_idletasks()
        parent_x: int = parent.winfo_x()
        parent_y: int = parent.winfo_y()
        parent_width: int = parent.winfo_width()
        parent_height: int = parent.winfo_height()

        x: int = parent_x + (parent_width // 2) - (width // 2)
        y: int = parent_y + (parent_height // 2) - (height // 2)

        screen_width: int = window.winfo_screenwidth()
        screen_height: int = window.winfo_screenheight()

        if x < 0:
            x = 10
        if y < 30:
            y = 30
        if x + width > screen_width:
            x = screen_width - width - 10
        if y + height > screen_height:
            y = screen_height - height - 10

        window.geometry(f"{width}x{height}+{x}+{y}")
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"Center window error: {e}")
        center_screen(window, width, height)


def setup_window_style(window: tk.Toplevel) -> None:
    """Set up window style for proper taskbar minimization."""
    from utils.helpers import is_windows
    if not is_windows():
        return

    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), 2)

        if hwnd:
            GWL_EXSTYLE: int = -20
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | 0x40000)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002)
    except (ImportError, AttributeError, OSError, TypeError) as e:
        logger.debug(f"Window style setup error: {e}")


def set_topmost_false(window: tk.Toplevel) -> None:
    """Safely remove topmost flag."""
    try:
        window.attributes("-topmost", False)
    except tk.TclError:
        pass


__all__: List[str] = [
    'safe_winfo_exists',
    'safe_focus',
    'safe_destroy',
    'safe_after_cancel',
    'get_colors_for_theme',
    'center_window_relative',
    'setup_window_style',
    'set_topmost_false',
]