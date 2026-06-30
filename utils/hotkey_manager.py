"""
Global hotkey manager for SecurePassPro.
Registers Ctrl+Alt+P to open a mini quick-search popup over any window.
Requires the `keyboard` package (pip install keyboard).
Falls back gracefully if not available or if running without the right
permissions (Linux/macOS usually need root or accessibility access).
"""
from __future__ import annotations

import sys
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger("hotkey_manager")

_hotkey_thread: Optional[threading.Thread] = None
_registered: bool = False
_callback: Optional[Callable] = None
_HOTKEY = "ctrl+alt+p"


def _try_import_keyboard() -> Any:
    """
    Handle try import keyboard.
    Обработать try import keyboard.
    Обробити try import keyboard.
    """
    try:
        import keyboard
        return keyboard
    except ImportError:
        return None


def register_quick_search(callback: Callable) -> bool:
    """
    Register Ctrl+Alt+P global hotkey that calls *callback* on the main thread.
    Returns True if registration succeeded.
    """
    global _registered, _callback, _hotkey_thread
    keyboard = _try_import_keyboard()
    if keyboard is None:
        logger.info("keyboard package not installed – global hotkey disabled")
        return False

    _callback = callback

    def _run() -> None:
        """
        Handle run.
        Обработать run.
        Обробити run.
        """
        global _registered
        try:
            keyboard.add_hotkey(_HOTKEY, _fire, suppress=False)
            _registered = True
            logger.info(f"Global hotkey registered: {_HOTKEY}")
            keyboard.wait()        # blocks until unregister() or process exit
        except (ImportError, OSError, ValueError, RuntimeError) as e:
            logger.warning(f"Global hotkey registration failed: {e}")
            _registered = False

    _hotkey_thread = threading.Thread(target=_run, daemon=True, name="hotkey-thread")
    _hotkey_thread.start()
    return True


def _fire() -> None:
    """Called by keyboard lib on hotkey press (background thread)."""
    # keyboard lib calls this from a background thread - callback must be
    # thread-safe (should schedule via root.after(0,...) in the callback)
    if _callback:
        try:
            _callback()
        except Exception as e:  # noqa: BLE001 – callback can raise anything
            logger.error(f"Hotkey callback error: {e}")


def unregister() -> None:
    """
    Handle unregister.
    Обработать unregister.
    Обробити unregister.
    """
    global _registered
    keyboard = _try_import_keyboard()
    if keyboard and _registered:
        try:
            keyboard.remove_hotkey(_HOTKEY)
            _registered = False
            logger.info("Global hotkey unregistered")
        except (OSError, ValueError, KeyError, RuntimeError) as e:
            logger.debug(f"Unregister error: {e}")


def is_registered() -> bool:
    """
    Return True if registered.
    True, если registered.
    True, якщо registered.
    """
    return _registered


# ── Quick-search popup (shown on hotkey press) ──────────────────────────────

def show_quick_search_popup(root_window, lang: str = "RU") -> None:
    """
    Create and show a small always-on-top search popup.
    Must be called from the Tk main thread.
    """
    import tkinter as tk
    try:
        import customtkinter as ctk
    except ImportError:
        logger.error("customtkinter not available for quick-search popup")
        return

    try:
        from storage.database import PasswordDB
        from Langs.lang import LANGUAGES
    except ImportError as e:
        logger.error(f"Import error in quick-search popup: {e}")
        return

    L = LANGUAGES.get(lang, LANGUAGES.get("EN", LANGUAGES.get("RU")))

    # ── Window ──────────────────────────────────────────────────────────────
    popup = ctk.CTkToplevel(root_window)
    popup.title(L.get("qs_title", "Quick Search / Быстрый поиск / Швидкий пошук"))
    popup.geometry("520x380")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)

    # Center on screen
    popup.update_idletasks()
    sw = popup.winfo_screenwidth()
    sh = popup.winfo_screenheight()
    x = (sw - 520) // 2
    y = (sh - 380) // 3
    popup.geometry(f"520x380+{x}+{y}")

    # ── Search field ────────────────────────────────────────────────────────
    search_var = tk.StringVar()
    header = ctk.CTkLabel(popup,
                          text=L.get("qs_title", "Quick Search / Быстрый поиск / Швидкий пошук"),
                          font=("Segoe UI", 15, "bold"))
    header.pack(pady=(14, 6), padx=16)

    entry = ctk.CTkEntry(popup, textvariable=search_var,
                         font=("Segoe UI", 14), height=40,
                         placeholder_text=L.get("qs_placeholder", "Type to search… / Введите запрос… / Введіть запит…"))
    entry.pack(fill="x", padx=16, pady=(0, 8))
    entry.focus_set()

    results_frame = ctk.CTkScrollableFrame(popup, height=250)
    results_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def _refresh(*_args) -> None:
        """
        Handle refresh.
        Обработать refresh.
        Обробити refresh.
        """
        for w in results_frame.winfo_children():
            w.destroy()
        q = search_var.get().strip()
        if not q:
            return
        try:
            records = PasswordDB.search(q)[:12]   # cap at 12 results
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
            records = []
        for rec in records:
            row = ctk.CTkFrame(results_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=rec.get("label", "—")[:40],
                         font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left", padx=(0, 8))

            def _copy(p=rec.get("password", "")) -> None:
                """
                Handle copy.
                Обработать copy.
                Обробити copy.
                """
                try:
                    popup.clipboard_clear()
                    popup.clipboard_append(p)
                    popup.update()
                    popup.destroy()
                except tk.TclError:
                    pass

            ctk.CTkButton(row, text=L.get("db_copy", "Copy"),
                          width=70, height=26, font=("Segoe UI", 11),
                          fg_color="#107c10", hover_color="#159e15",
                          command=_copy).pack(side="right")

    try:
        search_var.trace_add("write", _refresh)
    except AttributeError:
        # Tk < 8.6 fallback
        search_var.trace("w", _refresh)

    popup.bind("<Escape>", lambda _e: popup.destroy())

    popup.grab_set()


__all__ = [
    "register_quick_search",
    "unregister",
    "is_registered",
    "show_quick_search_popup",
]
