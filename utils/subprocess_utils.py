"""
Cross-platform subprocess helpers that suppress the console window on Windows.
Кроссплатформенные вспомогательные функции subprocess без консольного окна Windows.
Кросплатформені допоміжні функції subprocess без консольного вікна Windows.
"""
from __future__ import annotations
import platform
import subprocess
from typing import Any

_IS_WINDOWS = platform.system() == "Windows"

def _no_window_kwargs() -> dict[str, object]:
    """Return kwargs that prevent a console window from flashing on Windows."""
    if _IS_WINDOWS:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return {
            "creationflags": subprocess.CREATE_NO_WINDOW,
            "startupinfo": si,
        }
    return {}


def silent_popen(cmd: list[str] | str, **kwargs: object) -> subprocess.Popen[bytes]:
    """subprocess.Popen with console hidden on Windows."""
    kwargs.setdefault("stdout", subprocess.DEVNULL)
    kwargs.setdefault("stderr", subprocess.DEVNULL)
    kwargs.update(_no_window_kwargs())
    return subprocess.Popen(cmd, **kwargs)


def silent_run(cmd: list[str] | str, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
    """subprocess.run with console hidden on Windows."""
    kwargs.update(_no_window_kwargs())
    return subprocess.run(cmd, **kwargs)
