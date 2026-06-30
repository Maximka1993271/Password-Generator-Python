"""
Custom message box dialogs.
Кастомные диалоговые окна сообщений.
Кастомні діалогові вікна повідомлень.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from gui.dialogs_base import (
    safe_destroy,
    safe_winfo_exists,
    center_window_relative,
    get_colors_for_theme,
    set_topmost_false
)
from utils.helpers import get_global_radius
from utils.logger import get_logger
from Langs.lang import LANGUAGES

logger = get_logger("dialogs_messagebox")


class CTkMessageBox:
    """Custom message box with theme support."""
    
    _current_theme: str = "dark"
    _current_lang: str = "RU"

    @classmethod
    def set_theme(cls, theme: str) -> None:
        """Set current theme for message boxes."""
        cls._current_theme = theme

    @classmethod
    def set_lang(cls, lang: str) -> None:
        """Set current language for message boxes."""
        cls._current_lang = lang

    @staticmethod
    def _get_icon_text(icon_type: str) -> str:
        """Get icon text for message box."""
        icons: Dict[str, str] = {
            "info": "ℹ",
            "warning": "(!)",
            "error": "(x)",
            "question": "?",
            "success": "(v)",
        }
        return icons.get(icon_type, "•")

    @staticmethod
    def _show(
        parent: tk.Widget,
        title: str,
        message: str,
        button_text: str = "OK",
        icon_type: str = "",
        icon_color: str = "#4EC9B0",
        button_color: str = "#1f538d",
        is_question: bool = False
    ) -> Optional[Union[str, bool]]:
        """Show message box dialog."""
        win: ctk.CTkToplevel = ctk.CTkToplevel(parent)
        win.title(title)
        win.resizable(False, False)
        win.grab_set()
        win.attributes("-topmost", True)

        # Get live theme
        try:
            _live: str = ctk.get_appearance_mode().lower()
            _theme_now: str = "light" if _live == "light" else "dark"
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
            _theme_now = CTkMessageBox._current_theme

        colors: Dict[str, str] = get_colors_for_theme(_theme_now)
        L: Dict[str, str] = LANGUAGES.get(CTkMessageBox._current_lang, LANGUAGES["RU"])
        radius: int = get_global_radius()

        win.configure(fg_color=colors["bg"])

        w: int = 420
        h: int = 220 if is_question else 200

        # Set initial geometry, then re-center after widgets are laid out
        win.geometry(f"{w}x{h}")
        win.after(10, lambda: center_window_relative(parent, win, w, h))

        main_frame: ctk.CTkFrame = ctk.CTkFrame(win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        if icon_type:
            icon_text: str = CTkMessageBox._get_icon_text(icon_type)
            icon_label: ctk.CTkLabel = ctk.CTkLabel(
                main_frame,
                text=icon_text,
                font=("Segoe UI", 40),
                text_color=icon_color
            )
            icon_label.pack(pady=(0, 5))

        msg_label: ctk.CTkLabel = ctk.CTkLabel(
            main_frame,
            text=message,
            font=("Segoe UI", 13),
            wraplength=360,
            justify="center",
            text_color=colors["label_text"]
        )
        msg_label.pack(pady=(0, 15))

        btn_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack()

        result: List[Optional[Union[str, bool]]] = [None]

        if is_question:
            def on_yes() -> None:
                """
                Handle the yes event.
                Обработчик yes.
                Обробник yes.
                """
                result[0] = "yes"
                safe_destroy(win)

            def on_no() -> None:
                """
                Handle the no event.
                Обработчик no.
                Обробник no.
                """
                result[0] = "no"
                safe_destroy(win)

            yes_btn: ctk.CTkButton = ctk.CTkButton(
                btn_frame,
                text=L.get("yes", "Yes / Да / Так"),
                width=100,
                height=35,
                command=on_yes,
                fg_color="#2d6a4f",
                corner_radius=radius,
                text_color="white"
            )
            yes_btn.pack(side="left", padx=8)

            no_btn: ctk.CTkButton = ctk.CTkButton(
                btn_frame,
                text=L.get("no", "No / Нет / Ні"),
                width=100,
                height=35,
                command=on_no,
                fg_color="#8b0000",
                corner_radius=radius,
                text_color="white"
            )
            no_btn.pack(side="left", padx=8)
        else:
            def on_ok() -> None:
                """
                Handle the ok event.
                Обработчик ok.
                Обробник ok.
                """
                result[0] = "ok"
                safe_destroy(win)

            btn_text_display: str = button_text if button_text != "OK" else L.get("ok", "OK / Хорошо / Гаразд")
            ok_btn: ctk.CTkButton = ctk.CTkButton(
                btn_frame,
                text=btn_text_display,
                width=120,
                height=35,
                command=on_ok,
                fg_color=colors["button_fg"],
                corner_radius=radius,
                text_color=colors["button_text"]
            )
            ok_btn.pack()

        # Schedule topmost removal
        def remove_topmost() -> None:
            """
            Handle remove topmost.
            Обработать remove topmost.
            Обробити remove topmost.
            """
            if safe_winfo_exists(win):
                win.attributes("-topmost", False)
        win.after(100, remove_topmost)

        parent.wait_window(win)
        return result[0]

    @classmethod
    def info(cls, parent: tk.Widget, title: str, message: str) -> None:
        """Show info message."""
        _t: str = "light" if ctk.get_appearance_mode().lower() == "light" else "dark"
        colors: Dict[str, str] = get_colors_for_theme(_t)
        cls._show(parent, title, message, icon_type="info", icon_color=colors["icon_info"])

    @classmethod
    def warning(cls, parent: tk.Widget, title: str, message: str) -> None:
        """Show warning message."""
        _t: str = "light" if ctk.get_appearance_mode().lower() == "light" else "dark"
        colors: Dict[str, str] = get_colors_for_theme(_t)
        cls._show(parent, title, message, icon_type="warning", icon_color=colors["icon_warning"])

    @classmethod
    def error(cls, parent: tk.Widget, title: str, message: str) -> None:
        """Show error message."""
        _t: str = "light" if ctk.get_appearance_mode().lower() == "light" else "dark"
        colors = get_colors_for_theme(_t)
        cls._show(parent, title, message, icon_type="error", icon_color=colors["icon_error"])

    @classmethod
    def success(cls, parent: tk.Widget, title: str, message: str) -> None:
        """Show success message."""
        _t: str = "light" if ctk.get_appearance_mode().lower() == "light" else "dark"
        colors = get_colors_for_theme(_t)
        cls._show(parent, title, message, icon_type="success", icon_color=colors["icon_success"])

    @classmethod
    def question(cls, parent: tk.Widget, title: str, message: str) -> bool:
        """Show question dialog."""
        _t: str = "light" if ctk.get_appearance_mode().lower() == "light" else "dark"
        colors = get_colors_for_theme(_t)
        result = cls._show(parent, title, message, icon_type="question",
                          icon_color=colors["icon_question"], is_question=True)
        return result == "yes"


__all__: List[str] = [
    'CTkMessageBox',
]