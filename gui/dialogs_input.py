"""
Custom input dialog.
Кастомный диалог ввода.
Кастомний діалог введення.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from gui.dialogs_base import (
    safe_focus,
    safe_destroy,
    safe_winfo_exists,
    center_window_relative,
    get_colors_for_theme
)
from utils.logger import get_logger
from Langs.lang import LANGUAGES

logger = get_logger("dialogs_input")


class CTkInputDialog:
    """Custom input dialog with theme support."""
    
    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        prompt: str,
        show: str = "",
        theme: str = "dark",
        lang: str = "RU"
    ) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.result: Optional[str] = None
        self.parent: tk.Widget = parent
        self.win: ctk.CTkToplevel = ctk.CTkToplevel(parent)
        self.win.title(title)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.attributes("-topmost", True)

        L: Dict[str, str] = LANGUAGES.get(lang, LANGUAGES["RU"])
        radius: int = get_global_radius()

        colors: Dict[str, str] = get_colors_for_theme(theme)
        self.win.configure(fg_color=colors["bg"])

        self._center_relative_to_parent()

        main_frame: ctk.CTkFrame = ctk.CTkFrame(self.win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            main_frame,
            text=prompt,
            font=("Segoe UI", 13),
            wraplength=360,
            text_color=colors["label_text"]
        ).pack(pady=(0, 8))

        self.entry: ctk.CTkEntry = ctk.CTkEntry(
            main_frame,
            width=360,
            height=40,
            font=("Segoe UI", 14),
            show=show,
            fg_color=colors["entry_bg"],
            text_color=colors["fg"],
            corner_radius=radius
        )
        self.entry.pack(pady=(0, 12))
        safe_focus(self.entry)

        self.entry.bind("<Return>", lambda e: self._ok())
        self.entry.bind("<Escape>", lambda e: self._cancel())

        btn_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack()
        
        ctk.CTkButton(
            btn_frame,
            text=L["ok"],
            width=110,
            height=36,
            command=self._ok,
            fg_color=colors["button_fg"],
            corner_radius=radius,
            text_color="white"
        ).pack(side="left", padx=8)
        
        ctk.CTkButton(
            btn_frame,
            text=L["cancel"],
            width=110,
            height=36,
            command=self._cancel,
            fg_color="#ca5010",
            corner_radius=radius,
            text_color="white"
        ).pack(side="left", padx=8)

        self.win.protocol("WM_DELETE_WINDOW", self._cancel)
        parent.wait_window(self.win)

    def _center_relative_to_parent(self) -> None:
        """Center window relative to parent."""
        center_window_relative(self.parent, self.win, 420, 220)

    def _ok(self) -> None:
        """
        Handle ok.
        Обработать ok.
        Обробити ok.
        """
        self.result = self.entry.get() if safe_winfo_exists(self.entry) else None
        safe_destroy(self.win)

    def _cancel(self) -> None:
        """
        Handle cancel.
        Обработать cancel.
        Обробити cancel.
        """
        self.result = None
        safe_destroy(self.win)

    @staticmethod
    def ask(
        parent: tk.Widget,
        title: str,
        prompt: str,
        show: str = "",
        theme: str = "dark",
        lang: str = "RU"
    ) -> Optional[str]:
        """
        Handle ask.
        Обработать ask.
        Обробити ask.
        """
        return CTkInputDialog(parent, title, prompt, show, theme, lang).result


__all__: List[str] = [
    'CTkInputDialog',
]