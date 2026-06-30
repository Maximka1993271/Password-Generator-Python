"""
Cross-platform sound playback utilities.
Кроссплатформенные утилиты воспроизведения звука.
Кросплатформені утиліти відтворення звуку.
"""
from __future__ import annotations
import os
import platform
import subprocess
import threading
from typing import Optional

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS   = platform.system() == "Darwin"
_IS_LINUX   = platform.system() == "Linux"

_SOUND_CACHE: Optional[str] = None
_SOUND_CACHE_LOCK = threading.Lock()


def _get_sound_path() -> str:
    """
    Handle get sound path.
    Обработать get sound path.
    Обробити get sound path.
    """
    global _SOUND_CACHE
    with _SOUND_CACHE_LOCK:
        if _SOUND_CACHE:
            return _SOUND_CACHE
        from utils.resources import get_resource_path
        for name in ("click.wav", "click.mp3", "alert.wav"):
            p = get_resource_path(name)
            if p and os.path.exists(p):
                _SOUND_CACHE = p
                return p
        return ""


def _validate_sound_path(file_path: str) -> bool:
    """
    Handle validate sound path.
    Обработать validate sound path.
    Обробити validate sound path.
    """
    if not file_path or not os.path.isfile(file_path):
        return False
    if os.path.getsize(file_path) > 10 * 1024 * 1024:
        return False
    return file_path.lower().endswith((".wav", ".mp3", ".ogg"))


def _play_sound_windows(file_path: str) -> None:
    """
    Handle play sound windows.
    Обработать play sound windows.
    Обробити play sound windows.
    """
    try:
        import winsound
        winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except (RuntimeError, OSError, ImportError):
        try:
            import ctypes
            ctypes.windll.winmm.PlaySoundW(file_path, None, 0x0001 | 0x0002)
        except (AttributeError, OSError, TypeError):
            pass


def _play_sound_macos(file_path: str) -> None:
    """
    Handle play sound macos.
    Обработать play sound macos.
    Обробити play sound macos.
    """
    try:
        subprocess.Popen(["afplay", file_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, FileNotFoundError):
        pass


def _play_sound_linux(file_path: str) -> None:
    """
    Handle play sound linux.
    Обработать play sound linux.
    Обробити play sound linux.
    """
    players = ["paplay", "aplay", "mpg123", "ffplay"]
    for player in players:
        try:
            subprocess.Popen([player, file_path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except (OSError, FileNotFoundError):
            continue


def play_sound(sound_type: str = "click", sound_enabled: bool = True,
               sound_path: Optional[str] = None) -> None:
    """Play a UI sound asynchronously.
    Воспроизводит звук интерфейса асинхронно.
    Відтворює звук інтерфейсу асинхронно."""
    if not sound_enabled:
        return
    def _play() -> None:
        try:
            path = sound_path or _get_sound_path()
            if not path or not _validate_sound_path(path):
                return
            if _IS_WINDOWS:
                _play_sound_windows(path)
            elif _IS_MACOS:
                _play_sound_macos(path)
            else:
                _play_sound_linux(path)
        except (OSError, RuntimeError, AttributeError, ImportError):
            pass
    threading.Thread(target=_play, daemon=True).start()
