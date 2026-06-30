"""
Cross-platform window management utilities (centering, rounding, icons, themes).
Кроссплатформенные утилиты управления окнами.
Кросплатформені утиліти керування вікнами.
"""
from __future__ import annotations
import os
import platform
import subprocess
import sys
import tkinter as tk
from typing import Optional

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS   = platform.system() == "Darwin"
_IS_LINUX   = platform.system() == "Linux"

_global_radius: int = 10


def get_global_radius() -> int:
    """Return the global corner-radius setting."""
    return _global_radius

def set_global_radius(radius: int) -> None:
    """Set the global corner-radius (clamped 0–50)."""
    global _global_radius
    _global_radius = max(0, min(50, radius))


def center_screen(win: tk.Tk, width: int, height: int) -> None:
    """Center *win* on the primary screen."""
    try:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{width}x{height}+{max(0,(sw-width)//2)}+{max(0,(sh-height)//2)}")
    except (tk.TclError, AttributeError, RuntimeError):
        try:
            win.geometry(f"{width}x{height}")
        except tk.TclError:
            pass


def center_window_relative(parent: tk.Tk, child: tk.Tk, width: int, height: int) -> None:
    """Center *child* window relative to *parent*."""
    try:
        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = max(0, px + (pw - width)  // 2)
        y = max(0, py + (ph - height) // 2)
        child.geometry(f"{width}x{height}+{x}+{y}")
    except (tk.TclError, AttributeError, RuntimeError):
        try:
            child.geometry(f"{width}x{height}")
        except tk.TclError:
            pass


def apply_window_rounding(window: tk.Tk) -> None:
    """Apply rounded corners (Windows 11 DWM / macOS native)."""
    if _IS_WINDOWS:
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if hwnd == 0:
                hwnd = window.winfo_id()
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), ctypes.sizeof(ctypes.c_int))
        except (AttributeError, OSError, TypeError):
            pass
    elif _IS_MACOS:
        try:
            window.tk.call("wm", "attributes", window, "-transparentcolor", "")
        except tk.TclError:
            pass


def set_window_icon(window: tk.Tk, icon_path: Optional[str] = None) -> None:
    """Set the window titlebar icon (.ico or .png)."""
    try:
        from utils.resources import get_resource_path
        path = icon_path or get_resource_path("icon.ico") or get_resource_path("icon.png")
        if not path or not os.path.exists(path):
            return
        if path.endswith(".ico"):
            window.iconbitmap(path)
        else:
            from PIL import Image, ImageTk
            img  = Image.open(path).resize((32, 32))
            icon = ImageTk.PhotoImage(img)
            window.iconphoto(True, icon)
    except (tk.TclError, AttributeError, OSError, ImportError):
        pass


def apply_linux_theme(window: tk.Tk) -> None:
    """Apply basic GTK theming hints on Linux."""
    if not _IS_LINUX:
        return
    try:
        de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in de or "unity" in de:
            window.tk.call("tk", "scaling", 1.0)
        if os.environ.get("WAYLAND_DISPLAY"):
            window.tk.call("wm", "attributes", window, "-type", "normal")
    except tk.TclError:
        pass


def apply_macos_theme(window: tk.Tk) -> None:
    """Apply macOS-specific theming hints."""
    if not _IS_MACOS:
        return
    try:
        window.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", window, "document", "closeBox")
    except tk.TclError:
        pass
