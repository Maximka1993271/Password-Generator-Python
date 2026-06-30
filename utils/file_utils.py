"""
General-purpose file and string utilities.
Утилиты для файлов и строк общего назначения.
Утиліти для файлів і рядків загального призначення.
"""
from __future__ import annotations
import os
import platform
import time
from typing import Optional

_IS_WINDOWS = platform.system() == "Windows"


def format_time(seconds: int) -> str:
    """Convert *seconds* into a human-readable string."""
    if seconds < 0:   return "0 сек / 0 sec"
    if seconds < 60:  return f"{seconds} сек / sec"
    if seconds < 3600:
        return f"{seconds // 60} мин / min"
    if seconds < 86400:
        return f"{seconds // 3600} ч / h"
    return f"{seconds // 86400} дн / d"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate *text* to *max_length* characters."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - len(suffix)] + suffix


def is_valid_filename(filename: str) -> bool:
    """Return True if *filename* contains no forbidden characters."""
    if not filename:
        return False
    return not any(c in '<>:"/\\|?*' for c in filename)


def ensure_dir(path: str) -> bool:
    """Create *path* (and parents) if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
        if not _IS_WINDOWS:
            os.chmod(path, 0o700)
        return True
    except (PermissionError, OSError, IOError) as e:
        print(f"[file_utils] Failed to create {path}: {e}")
        return False


def get_file_size_mb(file_path: str) -> float:
    """Return *file_path* size in megabytes, or 0.0 on error."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except (OSError, IOError):
        return 0.0


def safe_remove_file(file_path: str, max_attempts: int = 3) -> bool:
    """Remove *file_path* with retries on Windows lock errors."""
    for attempt in range(max_attempts):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except (PermissionError, OSError, IOError) as e:
            if attempt == max_attempts - 1:
                print(f"[file_utils] Failed to remove {file_path}: {e}")
                return False
            time.sleep(0.1 * (attempt + 1))
    return False
