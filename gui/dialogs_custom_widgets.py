"""
Custom GUI widgets with accessibility support.
Пользовательские GUI виджеты с поддержкой доступности.
Користувацькі GUI віджети з підтримкою доступності.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from gui.dialogs_tooltip import ToolTip
from utils.logger import get_logger

logger = get_logger("dialogs_widgets")


class CustomButton(ctk.CTkButton):
    """Custom button with tooltip support."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the button."""
        self._tooltip = ToolTip(self, text, delay)


class CustomCheckBox(ctk.CTkCheckBox):
    """Custom checkbox with tooltip support."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the checkbox."""
        self._tooltip = ToolTip(self, text, delay)


class CustomEntry(ctk.CTkEntry):
    """Custom entry with tooltip and password toggle."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None
        self._show_password: bool = False
        self._original_show: str = kwargs.get("show", "")

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the entry."""
        self._tooltip = ToolTip(self, text, delay)

    def toggle_password_visibility(self) -> None:
        """Toggle password visibility."""
        self._show_password = not self._show_password
        self.configure(show="" if self._show_password else "*")


class CustomLabel(ctk.CTkLabel):
    """Custom label with tooltip support."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the label."""
        self._tooltip = ToolTip(self, text, delay)


class CustomSlider(ctk.CTkSlider):
    """Custom slider with tooltip and value label."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None
        self._value_label: Optional[CustomLabel] = None
        self._format_str: str = "{}"

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the slider."""
        self._tooltip = ToolTip(self, text, delay)

    def attach_value_label(self, label: CustomLabel, format_str: str = "{}") -> None:
        """Attach a label to display current value."""
        self._value_label = label
        self._format_str = format_str
        self.configure(command=self._on_value_change)
        self._on_value_change(self.get())

    def _on_value_change(self, value: float) -> None:
        """Update value label when slider changes."""
        if self._value_label:
            self._value_label.configure(text=self._format_str.format(int(value)))


__all__: List[str] = [
    'CustomButton',
    'CustomCheckBox',
    'CustomEntry',
    'CustomLabel',
    'CustomSlider',
]