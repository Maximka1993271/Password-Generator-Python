"""
Auto-Type — кросс-платформенная автовставка для Secure Pass Pro
Auto-Type — cross-platform auto-type for Secure Pass Pro

Windows : Win32 SendInput (ctypes)
Linux   : xdotool (if available), xclip/xsel fallback
macOS   : osascript

Usage:
    from utils.autotype import AutoType
    AutoType.clipboard_paste("MyP@ss!", clear_after=15)
    AutoType.type_to_active_window("MyP@ss!")
"""
from __future__ import annotations
import os, sys, time, threading, subprocess, platform, shutil
from typing import Optional, Callable
from utils.logger import get_logger

logger = get_logger("autotype")
_WIN = platform.system() == "Windows"
_LIN = platform.system() == "Linux"
_MAC = platform.system() == "Darwin"


# ── clipboard ──────────────────────────────────────────────────────────────
def _set_clipboard(text: str) -> bool:
    """
    Handle set clipboard.
    Обработать set clipboard.
    Обробити set clipboard.
    """
    try:
        import pyperclip; pyperclip.copy(text); return True
    except (ImportError, AttributeError, RuntimeError, OSError): pass
    if _WIN:
        try:
            import ctypes; CF = 13
            data = text.encode("utf-16-le") + b"\x00\x00"
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            h = ctypes.windll.kernel32.GlobalAlloc(0x0002, len(data))
            p = ctypes.windll.kernel32.GlobalLock(h)
            ctypes.memmove(p, data, len(data))
            ctypes.windll.kernel32.GlobalUnlock(h)
            ctypes.windll.user32.SetClipboardData(CF, h)
            ctypes.windll.user32.CloseClipboard()
            return True
        except (AttributeError, OSError): pass
    if _LIN:
        for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                p.communicate(input=text.encode(), timeout=3)
                if p.returncode == 0: return True
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError): continue
    if _MAC:
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode(), timeout=3); return True
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError): pass
    return False


def _paste_clipboard() -> bool:
    """
    Handle paste clipboard.
    Обработать paste clipboard.
    Обробити paste clipboard.
    """
    time.sleep(0.1)
    if _WIN:
        try:
            import ctypes; VK_CTRL, VK_V, KUP = 0x11, 0x56, 0x0002
            ctypes.windll.user32.keybd_event(VK_CTRL, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(VK_V, 0, KUP, 0)
            ctypes.windll.user32.keybd_event(VK_CTRL, 0, KUP, 0)
            return True
        except (AttributeError, OSError): pass
    if _LIN:
        try:
            subprocess.run(["xdotool", "key", "ctrl+v"], timeout=3, check=True); return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired): pass
    if _MAC:
        try:
            subprocess.run(["osascript", "-e",
                'tell application "System Events" to keystroke "v" using {command down}'],
                timeout=3, check=True); return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired): pass
    return False


# ── direct typing ──────────────────────────────────────────────────────────
def _type_xdotool(text: str, delay_ms: int = 30) -> bool:
    """
    Handle type xdotool.
    Обработать type xdotool.
    Обробити type xdotool.
    """
    try:
        subprocess.run(["xdotool", "type", f"--delay={delay_ms}",
                        "--clearmodifiers", "--", text],
                       timeout=max(10, len(text) * delay_ms / 1000 + 5), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, OSError): return False


def _type_win32(text: str, delay_ms: int = 30) -> bool:
    """
    Handle type win32.
    Обработать type win32.
    Обробити type win32.
    """
    try:
        import ctypes; from ctypes import wintypes
        KEYUP = 0x0002; UNICODE = 0x0004
        class KBD(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
        class INP(ctypes.Structure):
            class _U(ctypes.Union): _fields_ = [("ki", KBD)]
            _anonymous_ = ("_input",)
            _fields_ = [("type", wintypes.DWORD), ("_input", _U)]
        for ch in text:
            for fl in (UNICODE, UNICODE | KEYUP):
                inp = INP(type=1, ki=KBD(wVk=0, wScan=ord(ch), dwFlags=fl))
                ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(delay_ms / 1000)
        return True
    except (AttributeError, OSError, TypeError): return False


def _type_osascript(text: str) -> bool:
    """
    Handle type osascript.
    Обработать type osascript.
    Обробити type osascript.
    """
    esc = text.replace("\\", "\\\\").replace('"', '\\"')
    try:
        subprocess.run(["osascript", "-e",
                        f'tell application "System Events" to keystroke "{esc}"'],
                       timeout=max(10, len(text) + 5), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, OSError): return False


# ── public API ─────────────────────────────────────────────────────────────
class AutoType:
    """
    Cross-platform password auto-type.
    Кросс-платформенная автовставка паролей.
    Кросплатформений автовведення паролів.
    """

    @staticmethod
    def is_available() -> bool:
        """
        Return True if available.
        True, если available.
        True, якщо available.
        """
        if _WIN:
            try: import ctypes; ctypes.windll.user32; return True
            except (AttributeError, OSError): return False
        if _LIN:
            return any(shutil.which(t) for t in ("xdotool", "xclip", "xsel"))
        if _MAC:
            return shutil.which("osascript") is not None
        return False

    @staticmethod
    def type_to_active_window(text: str, delay_ms: int = 30) -> bool:
        """Type text char-by-char into the currently focused window."""
        if not text: return True
        if _LIN and shutil.which("xdotool"):
            return _type_xdotool(text, delay_ms)
        if _WIN:
            return _type_win32(text, delay_ms)
        if _MAC:
            return _type_osascript(text)
        # universal fallback
        return AutoType.clipboard_paste(text, clear_after=15, do_paste=True)

    @staticmethod
    def clipboard_paste(text: str, clear_after: int = 15,
                        do_paste: bool = True,
                        on_clear: Optional[Callable] = None) -> bool:
        """
        Copy to clipboard → optionally Ctrl+V → auto-clear after N seconds.
        Скопировать → Ctrl+V → очистить через N секунд.
        """
        if not _set_clipboard(text):
            logger.error("Failed to set clipboard")
            return False
        if do_paste:
            _paste_clipboard()
        if clear_after > 0:
            def _clear():
                """
                Handle clear.
                Обработать clear.
                Обробити clear.
                """
                time.sleep(clear_after)
                _set_clipboard("")
                logger.debug(f"Clipboard cleared after {clear_after}s")
                if on_clear:
                    try: on_clear()
                    except (RuntimeError, AttributeError, TypeError): pass
            threading.Thread(target=_clear, daemon=True).start()
        return True

    # alias
    type_text = type_to_active_window

    @staticmethod
    def get_platform_info() -> dict:
        """
        Return platform info.
        Возвращает platform info.
        Повертає platform info.
        """
        info = {"platform": platform.system(), "available": AutoType.is_available()}
        if _LIN:
            info["xdotool"] = shutil.which("xdotool") is not None
            info["xclip"]   = shutil.which("xclip")   is not None
            info["xsel"]    = shutil.which("xsel")     is not None
        return info


__all__ = ["AutoType"]
