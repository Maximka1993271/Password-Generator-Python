"""
Secure memory-wiping utilities.
Утилиты безопасной очистки памяти.
Утиліти безпечного очищення пам'яті.
"""
from __future__ import annotations
import ctypes
import sys
from typing import Optional

from utils.logger import get_logger

logger = get_logger("encryption.memory")


# ── Memory-wiping rationale ───────────────────────────────────
# Python's garbage collector does NOT guarantee that unreferenced objects
# are immediately zeroed or freed.  A key held in a bytearray that goes out
# of scope might remain readable in the process heap for seconds or minutes.
# ctypes.memset() writes directly to the buffer's memory address, bypassing
# Python's object model.  The double-pass (wipe → re-wipe) frustrates
# optimising compilers that might elide a single "dead write".
def zero(buf: Optional[bytearray]) -> None:
    """Zero-out a bytearray in place (double-pass).
    Безопасно обнуляет bytearray (двойной проход).
    Безпечно обнуляє bytearray (подвійний прохід)."""
    if buf is None:
        return
    try:
        # Pass 1: zero the entire buffer
        ctypes.memset((ctypes.c_char * len(buf)).from_buffer(buf), 0, len(buf))
        # Pass 2: repeat to prevent dead-store elimination by aggressive optimisers
        ctypes.memset((ctypes.c_char * len(buf)).from_buffer(buf), 0, len(buf))
    except (TypeError, AttributeError, OSError, ValueError) as e:
        logger.debug("Zero buffer fallback: %s", e)
        try:
            for i in range(len(buf)):
                buf[i] = 0
        except (TypeError, IndexError, RuntimeError) as e2:
            logger.debug("Fallback zeroing failed: %s", e2)

# Keep old name for internal compatibility
_zero = zero


def secure_zero(data: bytearray) -> None:
    """Zero-out a bytearray via ctypes.memset.
    Обнуляет bytearray через ctypes.memset.
    Обнуляє bytearray через ctypes.memset."""
    if data is None:
        return
    try:
        length = len(data)
        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(data)), 0, length)
    except (TypeError, AttributeError, OSError) as e:
        logger.debug("Memory zeroing failed: %s", e)
        for i in range(len(data)):
            data[i] = 0

_secure_zero = secure_zero


def clear_bytes(data: Optional[bytes]) -> None:
    """Clear a bytes object by converting to bytearray and zeroing.
    Очищает байты (преобразует в bytearray и обнуляет).
    Очищує байти (перетворює на bytearray та обнуляє)."""
    if data is None:
        return
    try:
        ba = bytearray(data)
        secure_zero(ba)
    except (TypeError, MemoryError, OSError, ValueError) as e:
        logger.debug("Bytes clearing failed: %s", e)

_clear_bytes = clear_bytes


def clear_string(s: str) -> None:
    """Best-effort wipe of a Python string.
    Попытка очистить строку Python.
    Спроба очистити рядок Python."""
    if not s:
        return
    if s.startswith(("[encrypted", "enc1:", "enc2:", "enc3:")):
        return
    try:
        ba = bytearray(s.encode("utf-8"))
        secure_zero(ba)
    except (UnicodeEncodeError, TypeError, MemoryError, ValueError) as e:
        logger.debug("String clearing failed: %s", e)

_clear_string = clear_string


def clear_bytearray(data: Optional[bytearray]) -> None:
    """Clear a bytearray.
    Очищает bytearray.
    Очищує bytearray."""
    if data is None:
        return
    secure_zero(data)

_clear_bytearray = clear_bytearray


def hide_dir(path: str) -> None:
    """Set the hidden attribute on a directory (Windows only).
    Устанавливает атрибут скрытия для директории (только Windows).
    Встановлює атрибут прихованості для директорії (тільки Windows)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except (AttributeError, OSError, TypeError) as e:
            logger.debug("Hide dir failed: %s", e)

_hide_dir = hide_dir
