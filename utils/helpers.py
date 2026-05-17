"""
Helper functions and utilities
"""
import os
import sys
import math
import platform
import ctypes
import subprocess
import shutil
import tkinter as tk
from typing import Optional

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"
_global_radius = 10


def get_global_radius() -> int:
    """Get global corner radius"""
    return _global_radius


def set_global_radius(radius: int) -> None:
    """Set global corner radius"""
    global _global_radius
    _global_radius = radius


def is_windows() -> bool:
    return _IS_WINDOWS


def is_macos() -> bool:
    return _IS_MACOS


def is_linux() -> bool:
    return _IS_LINUX


def center_screen(win: tk.Tk, width: int, height: int) -> None:
    """Center window on screen"""
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def get_resource_path(filename: str) -> str:
    """Get path to resource file (works for PyInstaller)"""
    base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, filename)


def apply_window_rounding(window) -> None:
    """Apply rounded corners to window (Windows only)"""
    if not _IS_WINDOWS:
        return
    try:
        window.update()
        HWND = ctypes.windll.user32.GetParent(window.winfo_id())
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            HWND, DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
            ctypes.sizeof(ctypes.c_int(DWMWCP_ROUND))
        )
    except Exception:
        pass


def set_window_icon(window, icon_path: str = None) -> None:
    """Set window icon"""
    if icon_path is None:
        icon_path = get_resource_path("icon.ico")
    
    if not os.path.exists(icon_path):
        return
    
    try:
        if _IS_WINDOWS:
            window.iconbitmap(icon_path)
        else:
            try:
                img = tk.PhotoImage(file=icon_path)
                window.iconphoto(True, img)
                window._icon_image = img
            except Exception:
                pass
    except Exception:
        pass


def play_sound(sound_type: str = "click", sound_enabled: bool = True, 
               base_path: str = None) -> None:
    """Play sound effect"""
    if not sound_enabled:
        return
    
    # Определяем правильный путь к файлу
    if base_path is None:
        # Сначала пробуем найти файл в папке с программой
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(script_dir, "Computer Mouse Click.mp3")
        
        # Если не нашли, пробуем путь PyInstaller
        if not os.path.exists(file_path) and hasattr(sys, '_MEIPASS'):
            file_path = os.path.join(sys._MEIPASS, "Computer Mouse Click.mp3")
    else:
        file_path = base_path if os.path.isfile(base_path) else os.path.join(base_path, "Computer Mouse Click.mp3")
    
    if not os.path.exists(file_path):
        print(f"[Sound] Файл не найден: {file_path}")
        return
    
    try:
        if _IS_WINDOWS:
            winmm = ctypes.windll.winmm
            alias = "app_click"
            winmm.mciSendStringW(f'close {alias}', None, 0, 0)
            winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, 0)
            winmm.mciSendStringW(f'play {alias} from 0', None, 0, 0)
            
            def close_sound():
                try:
                    winmm.mciSendStringW(f'close {alias}', None, 0, 0)
                except Exception:
                    pass
            
            import threading
            threading.Timer(1.0, close_sound).start()
        elif _IS_MACOS:
            if shutil.which("afplay"):
                subprocess.Popen(["afplay", file_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if shutil.which("mpg123"):
                subprocess.Popen(["mpg123", "-q", file_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif shutil.which("ffplay"):
                subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[Sound] Ошибка: {e}")
