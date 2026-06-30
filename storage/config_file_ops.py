from __future__ import annotations
# storage/config_file_ops.py
"""
Config file ops module for Secure Pass Pro.
Модуль Config file ops для Secure Pass Pro.
Модуль Config file ops для Secure Pass Pro.
"""
"""
Config file ops module for Secure Pass Pro.
Модуль Config file ops для Secure Pass Pro.
Модуль Config file ops для Secure Pass Pro.
"""
"""
Secure file operations for configuration
Безопасные файловые операции для конфигурации
Безпечні файлові операції для конфігурації

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

import os
import sys
import tempfile
import ctypes
from typing import Optional


# ==================== SECURE FILE OPERATIONS (BUILT-IN) ====================

def secure_write(path: str, content: bytes, make_hidden: bool = True) -> bool:
    """
    Secure file write with atomic replacement.
    FIXED #38: Uses os.replace for atomic operation instead of remove+rename.

    Безопасная запись файла с атомарной заменой.
    Исправлено #38: Использует os.replace для атомарной операции вместо remove+rename.

    Безпечний запис файлу з атомарною заміною.
    Виправлено #38: Використовує os.replace для атомарної операції замість remove+rename.
    """
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=directory,
            prefix='.config_tmp_',
            suffix='.json'
        )
        os.close(fd)

        try:
            with open(temp_path, 'wb') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            os.replace(temp_path, path)

            if make_hidden and sys.platform == 'win32':
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(path, 2)
                except (ImportError, AttributeError, OSError) as _:
                    pass

            return True

        except (OSError, IOError, PermissionError) as e:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except (OSError, IOError, PermissionError):
                pass
            raise e

    except (OSError, IOError, PermissionError, TypeError) as e:
        print(f"Secure write failed / Безопасная запись не удалась / Безпечний запис не вдався: {e}")
        return False


def secure_read(path: str) -> Optional[bytes]:
    """
    Secure file read

    Безопасное чтение файла
    Безпечне читання файлу
    """
    try:
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return f.read()
    except (OSError, IOError, PermissionError, TypeError) as e:
        print(f"Secure read failed / Безопасное чтение не удалось / Безпечне читання не вдалося: {e}")
        return None


__all__ = [
    'secure_write',
    'secure_read',

]
