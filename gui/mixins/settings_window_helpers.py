"""
Settings window mixin - Helper functions
Миксин окна настроек - Вспомогательные функции
Міксин вікна налаштувань - Допоміжні функції

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from typing import Dict, Any, List, Optional
from utils.logger import get_logger

logger = get_logger("settings_window")


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
            "button_fg": "#1f538d"
        }
    return {
        "bg": "#1d1e1e",
        "fg": "#FFFFFF",
        "entry_bg": "#2b2b2b",
        "label_text": "#FFFFFF",
        "button_fg": "#1f538d"
    }


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
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"Window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
        try:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            window.geometry(f"{width}x{height}+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e2:
            pass