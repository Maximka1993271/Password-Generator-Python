"""
Enhanced tooltip class.
Улучшенный класс всплывающих подсказок.
Покращений клас спливаючих підказок.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

from utils.logger import get_logger
from gui.dialogs_base import safe_winfo_exists

logger = get_logger("dialogs_tooltip")


class ToolTip:
    """
    Enhanced tooltip with accessibility support.
    Улучшенная всплывающая подсказка с поддержкой доступности.
    Покращена спливаюча підказка з підтримкою доступності.
    """

    def __init__(self, widget: tk.Widget, text: str = "", delay: int = 500) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.widget: tk.Widget = widget
        self.text: str = text
        self.delay: int = delay
        self.tip_window: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<FocusIn>", self._on_focus_in)
        widget.bind("<FocusOut>", self._on_focus_out)

    def set_text(self, text: str) -> None:
        """Set tooltip text."""
        self.text = text

    def _on_enter(self, event: Optional[tk.Event] = None) -> None:
        """
        Handle on enter.
        Обработать on enter.
        Обробити on enter.
        """
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except (tk.TclError, ValueError) as e:
                logger.debug(f"After cancel error: {e}")
        self._after_id = self.widget.after(self.delay, self._show_tip)

    def _on_leave(self, event: Optional[tk.Event] = None) -> None:
        """
        Handle on leave.
        Обработать on leave.
        Обробити on leave.
        """
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except (tk.TclError, ValueError) as e:
                logger.debug(f"After cancel error: {e}")
            self._after_id = None
        self._hide_tip()

    def _on_focus_in(self, event: Optional[tk.Event] = None) -> None:
        """
        Handle on focus in.
        Обработать on focus in.
        Обробити on focus in.
        """
        self._show_tip()

    def _on_focus_out(self, event: Optional[tk.Event] = None) -> None:
        """
        Handle on focus out.
        Обработать on focus out.
        Обробити on focus out.
        """
        self._hide_tip()

    def _show_tip(self) -> None:
        """
        Handle show tip.
        Обработать show tip.
        Обробити show tip.
        """
        if self.tip_window or not self.text:
            return
        try:
            if not safe_winfo_exists(self.widget):
                return
        except (tk.TclError, AttributeError):
            return

        try:
            x: int = self.widget.winfo_rootx() + 25
            y: int = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except (tk.TclError, AttributeError):
            return

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        try:
            tk.Label(
                self.tip_window,
                text=self.text,
                justify='left',
                background="#ffffe0",
                relief='solid',
                borderwidth=1,
                font=("Segoe UI", 9, "normal")
            ).pack(ipadx=1)
        except tk.TclError as e:
            logger.debug(f"Tooltip label error: {e}")
            self._hide_tip()

    def _hide_tip(self) -> None:
        """
        Handle hide tip.
        Обработать hide tip.
        Обробити hide tip.
        """
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except tk.TclError as e:
                logger.debug(f"Tooltip destroy error: {e}")
            finally:
                self.tip_window = None


__all__: List[str] = [
    'ToolTip',
]