"""
Dialogs mixin - Helper functions and utilities
Миксин диалогов - Вспомогательные функции и утилиты
Міксин діалогів - Допоміжні функції та утиліти

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import tkinter as tk
import customtkinter as ctk
from typing import Optional, Dict, Any, List
from utils.logger import get_logger

logger = get_logger("dialogs")


def _input_dialog(parent, title: str, prompt: str, show: str = "",
                  theme: str = "dark", lang: str = "RU") -> Optional[str]:
    """
    Custom input dialog that works without CTkInputDialog

    Пользовательский диалог ввода, работающий без CTkInputDialog
    Власний діалог введення, що працює без CTkInputDialog
    """
    from Langs.lang import LANGUAGES
    L = LANGUAGES.get(lang, LANGUAGES["RU"])
    result = {"value": None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x250")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.attributes("-topmost", True)

    # Center window / Центрируем окно / Центруємо вікно
    try:
        dialog.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - 420) // 2
        y = parent_y + (parent_height - 250) // 2
        dialog.geometry(f"420x250+{x}+{y}")
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")

    # Colors based on theme / Цвета в зависимости от теми / Кольори залежно від теми
    if theme == "light":
        bg_color = "#F3F3F3"
        fg_color = "#000000"
        entry_bg = "#FFFFFF"
        btn_fg = "#2d6a4f"
        btn_hover = "#40916c"
    else:
        bg_color = "#1d1e1e"
        fg_color = "#FFFFFF"
        entry_bg = "#2b2b2b"
        btn_fg = "#2d6a4f"
        btn_hover = "#40916c"

    dialog.configure(fg_color=bg_color)

    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Icon (empty) / Иконка (пустая) / Іконка (порожня)
    ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 36), text_color="#4EC9B0").pack(pady=(0, 5))

    # Prompt label / Метка с вопросом / Мітка з питанням
    ctk.CTkLabel(main_frame, text=prompt, font=("Segoe UI", 13), text_color=fg_color).pack(pady=(0, 10))

    # Entry field / Поле ввода / Поле введення
    entry = ctk.CTkEntry(main_frame, width=300, height=38, show=show,
                         fg_color=entry_bg, text_color=fg_color)
    entry.pack(pady=(0, 15))
    entry.focus_set()

    # Button frame / Фрейм кнопок / Фрейм кнопок
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack()

    def on_ok() -> None:
        """
        Handle the ok event.
        Обработчик ok.
        Обробник ok.
        """
        result["value"] = entry.get()
        dialog.destroy()

    def on_cancel() -> None:
        """
        Handle the cancel event.
        Обработчик cancel.
        Обробник cancel.
        """
        dialog.destroy()

    ctk.CTkButton(btn_frame, text=L.get("ok", "OK / Хорошо / Гаразд"), width=100, height=34, command=on_ok,
                  fg_color="#2d6a4f", corner_radius=17, font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text=L.get("cancel", "Cancel / Отмена / Скасувати"), width=100, height=34, command=on_cancel,
                  fg_color="#8b0000", corner_radius=17, font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

    entry.bind("<Return>", lambda e: on_ok())
    entry.bind("<Escape>", lambda e: on_cancel())

    dialog.after(100, lambda: dialog.attributes("-topmost", False))

    parent.wait_window(dialog)
    return result["value"]


def _get_colors_for_theme(theme: str) -> dict:
    """
    Return colors for theme

    Возвращает цвета для темы
    Повертає кольори для теми
    """
    if theme == "light":
        return {
            "bg": "#F3F3F3",
            "fg": "#000000",
            "entry_bg": "#FFFFFF",
            "label_text": "#000000",
            "button_fg": "#1f538d",
            "card_bg": "#E2E2E2",
        }
    return {
        "bg": "#1d1e1e",
        "fg": "#FFFFFF",
        "entry_bg": "#2b2b2b",
        "label_text": "#FFFFFF",
        "button_fg": "#1f538d",
        "card_bg": "#252627",
    }


def _get_actual_theme(self) -> str:
    """
    Return actual theme (light/dark)

    Возвращает актуальную тему (light/dark)
    Повертає актуальну тему (light/dark)
    """
    if hasattr(self, 'current_theme'):
        if self.current_theme == "Light":
            return "light"
        elif self.current_theme == "Dark":
            return "dark"
    return "dark"


def _center_window_relative_to_parent(self, window, width: int, height: int) -> None:
    """
    Center window relative to parent

    Центрирует окно относительно родителя
    Центрує вікно відносно батька
    """
    try:
        window.update_idletasks()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        if x < 0:
            x = 10
        if y < 30:
            y = 30
        if x + width > screen_width:
            x = screen_width - width - 10
        if y + height > screen_height:
            y = screen_height - height - 10

        window.geometry(f"{width}x{height}+{x}+{y}")
    except (tk.TclError, AttributeError) as e:
        logger.debug(f"Window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            window.geometry(f"{width}x{height}+{x}+{y}")
        except tk.TclError:
            pass


def _setup_window_style(window) -> None:
    """
    Set up window style for proper taskbar minimization

    Настраивает стиль окна для правильного сворачивания в панель задач
    Налаштовує стиль вікна для правильного згортання в панель завдань
    """
    from utils.helpers import is_windows
    if not is_windows():
        return

    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), 2)

        if hwnd:
            GWL_EXSTYLE = -20
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | 0x40000)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002)
    except (ImportError, AttributeError, OSError, TypeError) as e:
        logger.debug(f"Window style setup error / Ошибка настройки стиля окна / Помилка налаштування стилю вікна: {e}")


def _set_topmost_false(window) -> None:
    """
    Safely remove topmost flag

    Безопасно снимает флаг topmost
    Безпечно знімає прапор topmost
    """
    try:
        window.attributes("-topmost", False)
    except tk.TclError:
        pass
