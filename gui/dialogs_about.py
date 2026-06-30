"""
About dialog window.
Окно "О программе".
Вікно "Про програму".

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import webbrowser
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from gui.dialogs_base import safe_destroy, safe_winfo_exists, set_topmost_false, setup_window_style
from utils.logger import get_logger
from utils.helpers import apply_window_rounding, center_window_relative
from Langs.lang import LANGUAGES

logger = get_logger("dialogs_about")


def create_about_dialog(
    parent: tk.Widget,
    lang: str,
    radius: int,
    theme: str,
    on_close_callback: Optional[Callable] = None
) -> ctk.CTkToplevel:
    """Create and show about dialog."""
    L: Dict[str, str] = LANGUAGES.get(lang, LANGUAGES["RU"])
    wiki_url: str = "https://github.com/Maximka1993271/Password-Generator-Python/wiki"

    about_window: ctk.CTkToplevel = ctk.CTkToplevel(parent)
    about_window.title(L["btn_about"])
    about_window.resizable(False, False)
    about_window.transient(parent)
    about_window.attributes('-topmost', True)

    # Remove topmost safely
    def remove_topmost() -> None:
        """
        Handle remove topmost.
        Обработать remove topmost.
        Обробити remove topmost.
        """
        if safe_winfo_exists(about_window):
            about_window.attributes("-topmost", False)
    about_window.after(100, remove_topmost)

    try:
        setup_window_style(about_window)
    except (AttributeError, OSError) as e:
        logger.debug(f"Setup window style error: {e}")

    try:
        if not safe_winfo_exists(parent):
            center_screen_about(about_window, 400, 320)
        else:
            center_window_relative(parent, about_window, 400, 320)
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"About window centering error: {e}")
        about_window.geometry("400x320")

    try:
        apply_window_rounding(about_window)
    except (AttributeError, OSError) as e:
        logger.debug(f"Window rounding error: {e}")

    # Apply theme colors
    if theme == "light":
        bg_color: str = "#F3F3F3"
        fg_color: str = "#000000"
    else:
        bg_color = "#1d1e1e"
        fg_color = "#FFFFFF"
    about_window.configure(fg_color=bg_color)

    main_frame: ctk.CTkFrame = ctk.CTkFrame(about_window, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=30, pady=25)

    title_label: ctk.CTkLabel = ctk.CTkLabel(
        main_frame,
        text="Secure Pass Pro v4.0",
        font=("Segoe UI", 26, "bold"),
        text_color=fg_color
    )
    title_label.pack(pady=(0, 15))

    about_text: str = L.get("about_text_simple", "Professional password generator\n\nMaxim Melnikov\nMIT License")
    text_label: ctk.CTkLabel = ctk.CTkLabel(
        main_frame,
        text=about_text,
        wraplength=380,
        font=("Segoe UI", 13),
        justify="center",
        text_color=fg_color
    )
    text_label.pack(pady=10)

    btn_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack(pady=(20, 10))

    def close() -> None:
        """
        Handle close.
        Обработать close.
        Обробити close.
        """
        safe_destroy(about_window)
        if on_close_callback:
            on_close_callback()

    close_btn: ctk.CTkButton = ctk.CTkButton(
        btn_frame,
        text=L.get("ok", "OK / Хорошо / Гаразд"),
        width=100,
        height=35,
        command=close,
        corner_radius=radius,
        fg_color="#2d6a4f",
        hover_color="#40916c",
        font=("Segoe UI", 13, "bold"),
        text_color="white"
    )
    close_btn.pack(side="left", padx=10)

    wiki_btn: ctk.CTkButton = ctk.CTkButton(
        btn_frame,
        text=L.get("wiki_link", "Wiki / Вики"),
        width=100,
        height=35,
        command=lambda: webbrowser.open(wiki_url),
        corner_radius=radius,
        fg_color="#1f538d",
        hover_color="#2d6a4f",
        font=("Segoe UI", 13),
        text_color="white"
    )
    wiki_btn.pack(side="left", padx=10)

    safe_focus_about(about_window)
    return about_window


def center_screen_about(window: tk.Toplevel, width: int, height: int) -> None:
    """Center window on screen (standalone function)."""
    try:
        screen_width: int = window.winfo_screenwidth()
        screen_height: int = window.winfo_screenheight()
        x: int = (screen_width - width) // 2
        y: int = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"Center screen error: {e}")
        window.geometry(f"{width}x{height}")


def safe_focus_about(window: tk.Toplevel) -> None:
    """Safely set focus on window."""
    try:
        if safe_winfo_exists(window):
            window.focus_set()
    except (tk.TclError, AttributeError, RuntimeError):
        pass


__all__: List[str] = [
    'create_about_dialog',
]