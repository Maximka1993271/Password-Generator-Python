"""
Custom GUI widgets with accessibility support
Пользовательские GUI виджеты с поддержкой доступности
Користувацькі GUI віджети з підтримкою доступності

FIXED #EX: Replaced broad Exception with specific exceptions
FIXED: Added full type hints for all methods
FIXED: Syntax error in docstring

Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from utils.logger import get_logger

logger = get_logger("widgets")


# ==================== ENHANCED TOOLTIP / УЛУЧШЕННЫЙ TOOLTIP / ПОКРАЩЕНИЙ TOOLTIP ====================

class ToolTip:
    """Enhanced tooltip with accessibility support
    Улучшенная всплывающая подсказка с поддержкой доступности
    Покращена спливаюча підказка з підтримкою доступності"""

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
        """Set tooltip text / Установить текст подсказки / Встановити текст підказки"""
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
                logger.debug(f"After cancel error / Ошибка отмены / Помилка скасування: {e}")
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
                logger.debug(f"After cancel error / Ошибка отмены / Помилка скасування: {e}")
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
            if not self.widget.winfo_exists():
                return
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Tooltip show error / Ошибка показа подсказки / Помилка показу підказки: {e}")
            return

        try:
            x: int = self.widget.winfo_rootx() + 25
            y: int = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Tooltip position error / Ошибка позиции подсказки / Помилка позиції підказки: {e}")
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
            logger.debug(f"Tooltip label error / Ошибка метки подсказки / Помилка мітки підказки: {e}")
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
                logger.debug(f"Tooltip destroy error / Ошибка уничтожения подсказки / Помилка знищення підказки: {e}")
            except AttributeError as e:
                logger.debug(f"Tooltip attribute error / Ошибка атрибута подсказки / Помилка атрибута підказки: {e}")
            finally:
                self.tip_window = None


# ==================== CUSTOM BUTTON / КАСТОМНАЯ КНОПКА / КАСТОМНА КНОПКА ====================

class CustomButton(ctk.CTkButton):
    """Custom button with tooltip support
    Кастомная кнопка с поддержкой подсказок
    Кастомна кнопка з підтримкою підказок"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the button / Установить подсказку для кнопки / Встановити підказку для кнопки"""
        self._tooltip = ToolTip(self, text, delay)


# ==================== CUSTOM CHECKBOX / КАСТОМНЫЙ ЧЕКБОКС / КАСТОМНИЙ ЧЕКБОКС ====================

class CustomCheckBox(ctk.CTkCheckBox):
    """Custom checkbox with tooltip support
    Кастомный чекбокс с поддержкой подсказок
    Кастомний чекбокс з підтримкою підказок"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the checkbox / Установить подсказку для чекбокса / Встановити підказку для чекбоксу"""
        self._tooltip = ToolTip(self, text, delay)


# ==================== CUSTOM ENTRY / КАСТОМНОЕ ПОЛЕ ВВОДА / КАСТОМНЕ ПОЛЕ ВВЕДЕННЯ ====================

class CustomEntry(ctk.CTkEntry):
    """Custom entry with tooltip and password toggle
    Кастомное поле ввода с подсказкой и переключением пароля
    Кастомне поле введення з підказкою та перемиканням пароля"""

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
        """Set tooltip for the entry / Установить подсказку для поля ввода / Встановити підказку для поля введення"""
        self._tooltip = ToolTip(self, text, delay)

    def toggle_password_visibility(self) -> None:
        """Toggle password visibility / Переключить видимость пароля / Перемкнути видимість пароля"""
        self._show_password = not self._show_password
        self.configure(show="" if self._show_password else "*")


# ==================== CUSTOM LABEL / КАСТОМНАЯ МЕТКА / КАСТОМНА МІТКА ====================

class CustomLabel(ctk.CTkLabel):
    """Custom label with tooltip support
    Кастомная метка с поддержкой подсказок
    Кастомна мітка з підтримкою підказок"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(*args, **kwargs)
        self._tooltip: Optional[ToolTip] = None

    def set_tooltip(self, text: str, delay: int = 500) -> None:
        """Set tooltip for the label / Установить подсказку для метки / Встановити підказку для мітки"""
        self._tooltip = ToolTip(self, text, delay)


# ==================== CUSTOM SLIDER / КАСТОМНЫЙ СЛАЙДЕР / КАСТОМНИЙ СЛАЙДЕР ====================

class CustomSlider(ctk.CTkSlider):
    """Custom slider with tooltip and value label
    Кастомный слайдер с подсказкой и отображением значения
    Кастомний слайдер з підказкою та відображенням значення"""

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
        """Set tooltip for the slider / Установить подсказку для слайдера / Встановити підказку для слайдера"""
        self._tooltip = ToolTip(self, text, delay)

    def attach_value_label(self, label: CustomLabel, format_str: str = "{}") -> None:
        """Attach a label to display current value
        Прикрепить метку для отображения текущего значения
        Прикріпити мітку для відображення поточного значення"""
        self._value_label = label
        self._format_str = format_str
        self.configure(command=self._on_value_change)
        self._on_value_change(self.get())

    def _on_value_change(self, value: float) -> None:
        """Update value label when slider changes
        Обновить метку значения при изменении слайдера
        Оновити мітку значення при зміні слайдера"""
        if self._value_label:
            self._value_label.configure(text=self._format_str.format(int(value)))


# ==================== BACKWARD COMPATIBILITY / ОБРАТНАЯ СОВМЕСТИМОСТЬ / ЗВОРОТНЯ СУМІСНІСТЬ ====================

# FIXED #34: Create proper alias instead of self-assignment
# Исправлено #34: Создаём правильный алиас вместо самоприсваивания
# Виправлено #34: Створюємо правильний аліас замість самоприсвоєння

# OriginalToolTip is kept as an alias for ToolTip for backward compatibility
# OriginalToolTip оставлен как алиас для ToolTip для обратной совместимости
# OriginalToolTip залишений як аліас для ToolTip для зворотної сумісності
OriginalToolTip = ToolTip


__all__: List[str] = [
    'ToolTip',
    'OriginalToolTip',
    'CustomButton',
    'CustomCheckBox',
    'CustomEntry',
    'CustomLabel',
    'CustomSlider',
]
