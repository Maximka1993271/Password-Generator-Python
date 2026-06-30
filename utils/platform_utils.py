"""
Cross-platform detection helpers.
Кроссплатформенные утилиты обнаружения.
Кросплатформені утиліти виявлення.
"""
from __future__ import annotations
import os
import platform
import subprocess
import sys
from typing import Dict, Any

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS   = platform.system() == "Darwin"
_IS_LINUX   = platform.system() == "Linux"


def is_windows() -> bool:
    """Return True on Windows."""
    return _IS_WINDOWS

def is_macos() -> bool:
    """Return True on macOS."""
    return _IS_MACOS

def is_linux() -> bool:
    """Return True on Linux."""
    return _IS_LINUX

def get_platform() -> str:
    """Return 'windows', 'macos', or 'linux'."""
    if _IS_WINDOWS: return "windows"
    if _IS_MACOS:   return "macos"
    return "linux"

def is_admin() -> bool:
    """Return True if the process has admin/root privileges."""
    try:
        if _IS_WINDOWS:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        return os.getuid() == 0
    except (AttributeError, OSError):
        return False

def get_screen_size() -> tuple[int, int]:
    """Return (width, height) of the primary screen."""
    try:
        import tkinter as tk
        root = tk.Tk(); root.withdraw()
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return w, h
    except (ImportError, RuntimeError, OSError):
        return 1920, 1080

def get_system_scaling() -> float:
    """Return the DPI-based scale factor (best effort)."""
    try:
        if _IS_WINDOWS:
            import ctypes
            return ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0
        if _IS_MACOS:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True, text=True, timeout=3)
            if "Retina" in result.stdout:
                return 2.0
        return 1.0
    except (OSError, ValueError, subprocess.SubprocessError, AttributeError):
        return 1.0

def get_linux_desktop_environment() -> str:
    """Return the current DE name (e.g. 'gnome', 'kde')."""
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if de:
        return de
    session = os.environ.get("DESKTOP_SESSION", "").lower()
    return session or "unknown"

def is_wayland() -> bool:
    """Return True if running under Wayland."""
    return (os.environ.get("WAYLAND_DISPLAY") is not None
            or os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland")

def get_platform_info() -> Dict[str, Any]:
    """Return a dict of platform metadata."""
    return {
        "system":    platform.system(),
        "release":   platform.release(),
        "version":   platform.version(),
        "machine":   platform.machine(),
        "processor": platform.processor(),
        "python":    sys.version,
        "is_admin":  is_admin(),
        "is_wayland": is_wayland(),
        "de":        get_linux_desktop_environment() if _IS_LINUX else "",
    }
