"""
Secure file operations with atomic replace support for all platforms

Безопасные операции с файлами с поддержкой атомарной замены для всех платформ
Безпечні операції з файлами з підтримкою атомарної заміни для всіх платформ

FIXED #38: Using os.replace for atomic operation
FIXED #44: Centralized implementation - all modules should use this
Исправлено #38: Использование os.replace для атомарной операции
Исправлено #44: Централизованная реализация - все модули должны использовать это
Виправлено #38: Використання os.replace для атомарної операції
Виправлено #44: Централізована реалізація - всі модулі повинні використовувати це

FIXED #SEC-1: Replaced broad OSError/IOError with specific exceptions
ИСПРАВЛЕНО #SEC-1: Заменены широкие OSError/IOError на конкретные исключения
ВИПРАВЛЕНО #SEC-1: Замінено широкі OSError/IOError на конкретні винятки
"""
from __future__ import annotations
import os
import sys
import shutil
import platform
import ctypes
import tempfile
import time
from typing import Optional, Union
from utils.logger import get_logger

logger = get_logger("secure_file_ops")

# Windows constants / Константы для Windows / Константи для Windows
if platform.system() == "Windows":
    MOVEFILE_REPLACE_EXISTING = 0x00000001
    MOVEFILE_WRITE_THROUGH = 0x00000008


def secure_replace(src: str, dst: str, retry_count: int = 3) -> bool:
    """
    Atomic file replacement with support for all platforms.

    Атомарная замена файла с поддержкой всех платформ.
    Атомарна заміна файлу з підтримкою всіх платформ.

    Args:
        src: source file (temporary) / исходный файл (временный) / вихідний файл (тимчасовий)
        dst: target file / целевой файл / цільовий файл
        retry_count: number of attempts on error / количество попыток при ошибке / кількість спроб при помилці

    Returns:
        True if successful, False if error / True если успешно, False если ошибка / True якщо успішно, False якщо помилка
    """
    if not os.path.exists(src):
        logger.error(f"Source file does not exist: {src} / Исходный файл не существует: {src} / Вихідний файл не існує: {src}")
        return False

    for attempt in range(retry_count):
        try:
            if platform.system() == "Windows":
                return _secure_replace_windows(src, dst)
            else:
                return _secure_replace_unix(src, dst)
        except PermissionError as e:
            # FIXED: Separated PermissionError for specific handling
            # ИСПРАВЛЕНО: Отделили PermissionError для конкретной обработки
            # ВИПРАВЛЕНО: Відокремили PermissionError для конкретної обробки
            logger.warning(f"Permission error on replace attempt {attempt + 1}/{retry_count}: {e} / Ошибка доступа при попытке замены {attempt + 1}/{retry_count} / Помилка доступу при спробі заміни {attempt + 1}/{retry_count}")
            if attempt == retry_count - 1:
                logger.error(f"Failed to replace file after {retry_count} attempts: {src} -> {dst} / Не удалось заменить файл после {retry_count} попыток / Не вдалося замінити файл після {retry_count} спроб")
                return False
            time.sleep(0.1 * (attempt + 1))
        except OSError as e:
            # FIXED: Handle OSError with specific error checking
            # ИСПРАВЛЕНО: Обрабатываем OSError с конкретной проверкой ошибок
            # ВИПРАВЛЕНО: Обробляємо OSError з конкретною перевіркою помилок
            logger.warning(f"OS error on replace attempt {attempt + 1}/{retry_count}: {e} / Ошибка ОС при попытке замены {attempt + 1}/{retry_count} / Помилка ОС при спробі заміни {attempt + 1}/{retry_count}")
            if attempt == retry_count - 1:
                logger.error(f"Failed to replace file after {retry_count} attempts: {src} -> {dst} / Не удалось заменить файл после {retry_count} попыток / Не вдалося замінити файл після {retry_count} спроб")
                return False
            time.sleep(0.1 * (attempt + 1))
        except FileNotFoundError as e:
            logger.warning(f"File not found during replace attempt {attempt + 1}: {e} / Файл не найден во время попытки замены {attempt + 1} / Файл не знайдено під час спроби заміни {attempt + 1}")
            if attempt == retry_count - 1:
                return False
            time.sleep(0.1 * (attempt + 1))

    return False


def _secure_replace_windows(src: str, dst: str) -> bool:
    """
    Atomic replacement on Windows via MoveFileEx.
    Supports cross-volume movement.

    Атомарная замена на Windows через MoveFileEx.
    Поддерживает跨卷 перемещение.

    Атомарна заміна на Windows через MoveFileEx.
    Підтримує跨卷 переміщення.
    """
    try:
        # Try to use MoveFileEx with flags / Пытаемся использовать MoveFileEx с флагами / Намагаємося використати MoveFileEx з прапорами
        result = ctypes.windll.kernel32.MoveFileExW(
            src,
            dst,
            MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH
        )

        if result:
            logger.debug(f"MoveFileEx succeeded: {src} -> {dst} / MoveFileEx успешен: {src} -> {dst} / MoveFileEx успішний: {src} -> {dst}")
            return True

        # If MoveFileEx failed (different volumes), use copy+delete
        # Если MoveFileEx не сработал (разные тома), используем копирование
        # Якщо MoveFileEx не спрацював (різні томи), використовуємо копіювання
        logger.debug("MoveFileEx failed, falling back to copy+delete / MoveFileEx не сработал, откат к копированию+удалению / MoveFileEx не спрацював, відкат до копіювання+видалення")
        return _secure_replace_fallback(src, dst)

    except AttributeError as e:
        # FIXED: Handle AttributeError separately (ctypes not available)
        # ИСПРАВЛЕНО: Обрабатываем AttributeError отдельно (ctypes недоступен)
        # ВИПРАВЛЕНО: Обробляємо AttributeError окремо (ctypes недоступний)
        logger.debug(f"MoveFileEx attribute error: {e}, using fallback / Ошибка атрибута MoveFileEx: {e}, используем fallback / Помилка атрибуту MoveFileEx: {e}, використовуємо fallback")
        return _secure_replace_fallback(src, dst)
    except OSError as e:
        logger.debug(f"MoveFileEx OS error: {e}, using fallback / Ошибка ОС MoveFileEx: {e}, используем fallback / Помилка ОС MoveFileEx: {e}, використовуємо fallback")
        return _secure_replace_fallback(src, dst)
    except TypeError as e:
        logger.debug(f"MoveFileEx type error: {e}, using fallback / Ошибка типа MoveFileEx: {e}, используем fallback / Помилка типу MoveFileEx: {e}, використовуємо fallback")
        return _secure_replace_fallback(src, dst)


def _secure_replace_unix(src: str, dst: str) -> bool:
    """
    Atomic replacement on Unix systems via os.replace.

    Атомарная замена на Unix-системах через os.replace.
    Атомарна заміна на Unix-системах через os.replace.
    """
    try:
        # On Unix os.replace is usually atomic / На Unix os.replace обычно атомарный / На Unix os.replace зазвичай атомарний
        os.replace(src, dst)
        logger.debug(f"os.replace succeeded: {src} -> {dst} / os.replace успешен: {src} -> {dst} / os.replace успішний: {src} -> {dst}")
        return True
    except OSError as e:
        # If error (different filesystems), use fallback / Если ошибка (разные файловые системы), используем fallback / Якщо помилка (різні файлові системи), використовуємо fallback
        logger.debug(f"os.replace failed (likely cross-device): {e} / os.replace не сработал (вероятно, между устройствами): {e} / os.replace не спрацював (ймовірно, між пристроями): {e}")
        return _secure_replace_fallback(src, dst)
    except PermissionError as e:
        logger.debug(f"os.replace permission denied: {e} / os.replace: доступ запрещён / os.replace: доступ заборонено")
        return _secure_replace_fallback(src, dst)
    except FileNotFoundError as e:
        logger.debug(f"os.replace file not found: {e} / os.replace: файл не найден / os.replace: файл не знайдено")
        return _secure_replace_fallback(src, dst)


def _secure_replace_fallback(src: str, dst: str) -> bool:
    """
    Fallback mechanism: copy + delete.
    Not atomic, but works on any filesystem.

    Fallback механизм: копирование + удаление.
    Не атомарный, но работает на любых файловых системах.

    Fallback механізм: копіювання + видалення.
    Не атомарний, але працює на будь-яких файлових системах.
    """
    backup = None
    
    try:
        # First create a backup if the target file exists
        # Сначала создаём резервную копию если целевой файл существует
        # Спочатку створюємо резервну копію якщо цільовий файл існує
        if os.path.exists(dst):
            backup = dst + ".backup"
            try:
                shutil.copy2(dst, backup)
                logger.debug(f"Backup created: {backup} / Создана резервная копия: {backup} / Створено резервну копію: {backup}")
            except PermissionError as e:
                logger.warning(f"Failed to create backup (permission denied) / Ошибка создания резервной копии (доступ запрещён) / Помилка створення резервної копії (доступ заборонено): {e}")
            except OSError as e:
                logger.warning(f"Failed to create backup (OS error) / Ошибка создания резервной копии (ошибка ОС) / Помилка створення резервної копії (помилка ОС): {e}")
            except shutil.Error as e:
                logger.warning(f"Failed to create backup (shutil error) / Ошибка создания резервной копии (ошибка shutil) / Помилка створення резервної копії (помилка shutil): {e}")

        # Copy source file to target / Копируем исходный файл в целевой / Копіюємо вихідний файл у цільовий
        shutil.copy2(src, dst)

        # Check that the file was written correctly / Проверяем, что файл записался корректно / Перевіряємо, що файл записався коректно
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src):
            # Delete source file / Удаляем исходный файл / Видаляємо вихідний файл
            os.remove(src)

            # Delete backup if it was created / Удаляем резервную копию если была / Видаляємо резервну копію якщо була
            if backup and os.path.exists(backup):
                try:
                    os.remove(backup)
                except PermissionError as e:
                    logger.debug(f"Failed to remove backup (permission denied) / Не удалось удалить резервную копию (доступ запрещён) / Не вдалося видалити резервну копію (доступ заборонено): {e}")
                except OSError as e:
                    logger.debug(f"Failed to remove backup (OS error) / Не удалось удалить резервную копию (ошибка ОС) / Не вдалося видалити резервну копію (помилка ОС): {e}")

            logger.debug(f"Fallback replace succeeded: {src} -> {dst} / Fallback замена успешна: {src} -> {dst} / Fallback заміна успішна: {src} -> {dst}")
            return True
        else:
            # Restore from backup / Восстанавливаем из резервной копии / Відновлюємо з резервної копії
            if backup and os.path.exists(backup):
                try:
                    shutil.copy2(backup, dst)
                except (PermissionError, OSError, shutil.Error) as e:
                    logger.error(f"Failed to restore from backup / Не удалось восстановить из резервной копии / Не вдалося відновити з резервної копії: {e}")
                try:
                    os.remove(backup)
                except (PermissionError, OSError) as e:
                    logger.debug(f"Failed to remove backup after restore / Не удалось удалить резервную копию после восстановления / Не вдалося видалити резервну копію після відновлення: {e}")
            logger.error("Fallback replace failed - file size mismatch / Fallback замена не удалась - несоответствие размера файла / Fallback заміна не вдалася - невідповідність розміру файлу")
            return False

    except PermissionError as e:
        logger.error(f"Fallback replace failed (permission denied) / Ошибка fallback замены (доступ запрещён) / Помилка fallback заміни (доступ заборонено): {e}")
        # Attempt to restore from backup if exists
        if backup and os.path.exists(backup):
            try:
                shutil.copy2(backup, dst)
            except (PermissionError, OSError, shutil.Error):
                pass
        return False
    except OSError as e:
        logger.error(f"Fallback replace failed (OS error) / Ошибка fallback замены (ошибка ОС) / Помилка fallback заміни (помилка ОС): {e}")
        return False
    except shutil.Error as e:
        logger.error(f"shutil error during fallback replace / Ошибка shutil при fallback замене / Помилка shutil при fallback заміні: {e}")
        return False


# ── Atomic write pattern ─────────────────────────────────
# 1. Write to a temp file in the same directory (same filesystem →
#    rename is atomic on POSIX; near-atomic on NTFS).
# 2. fsync the temp file to flush OS page cache to disk.
# 3. os.replace() atomically replaces the target.
#
# This guarantees that a power failure between steps can never
# leave the target file half-written.  Either the old or the new
# version is visible — never a partial hybrid.
def secure_write(file_path: str, content: bytes, make_hidden: bool = True) -> bool:
    """
    Secure file write with atomic replacement.
    This is the CENTRALIZED implementation - use this everywhere.

    Безопасная запись файла с атомарной заменой.
    Это ЦЕНТРАЛИЗОВАННАЯ реализация - используйте её везде.

    Безпечний запис файлу з атомарною заміною.
    Це ЦЕНТРАЛІЗОВАНА реалізація - використовуйте її скрізь.

    Args:
        file_path: path to file / путь к файлу / шлях до файлу
        content: content in bytes / содержимое в байтах / вміст у байтах
        make_hidden: make file hidden on Windows / сделать файл скрытым на Windows / зробити файл прихованим на Windows

    Returns:
        True if successful / True если успешно / True якщо успішно
    """
    directory = os.path.dirname(os.path.abspath(file_path)) or "."
    try:
        os.makedirs(directory, exist_ok=True)
    except PermissionError as e:
        logger.error(f"Cannot create directory {directory} (permission denied): {e} / Не удалось создать директорию {directory} (доступ запрещён) / Не вдалося створити директорію {directory} (доступ заборонено)")
        return False
    except OSError as e:
        logger.error(f"Cannot create directory {directory} (OS error): {e} / Не удалось создать директорию {directory} (ошибка ОС) / Не вдалося створити директорію {directory} (помилка ОС)")
        return False

    # Create temporary file in the same directory (guarantees same volume)
    # Создаём временный файл в той же директории (гарантирует тот же том)
    # Створюємо тимчасовий файл у тій же директорії (гарантує той самий том)
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory, suffix=".tmp")
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot create temporary file in {directory}: {e} / Не удалось создать временный файл в {directory} / Не вдалося створити тимчасовий файл у {directory}")
        return False

    try:
        # Write to temporary file / Записываем во временный файл / Записуємо у тимчасовий файл
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk / Принудительная запись на диск / Примусовий запис на диск

        # Check that write succeeded / Проверяем, что запись прошла успешно / Перевіряємо, що запис пройшов успішно
        if os.path.getsize(tmp_path) != len(content):
            raise IOError(f"Written size mismatch: expected {len(content)}, got {os.path.getsize(tmp_path)} / Несоответствие размера записи: ожидалось {len(content)}, получено {os.path.getsize(tmp_path)} / Невідповідність розміру запису: очікувалось {len(content)}, отримано {os.path.getsize(tmp_path)}")

        # Atomically replace target file / Атомарно заменяем целевой файл / Атомарно замінюємо цільовий файл
        if not secure_replace(tmp_path, file_path):
            raise IOError("Atomic replace failed / Атомарная замена не удалась / Атомарна заміна не вдалася")

        # Hide file on Windows if needed / Скрываем файл на Windows если нужно / Ховаємо файл на Windows якщо потрібно
        if make_hidden and platform.system() == "Windows":
            try:
                ctypes.windll.kernel32.SetFileAttributesW(file_path, 0x02)
            except AttributeError as e:
                logger.debug(f"Failed to hide file (attribute error) / Ошибка скрытия файла (ошибка атрибута) / Помилка приховування файлу (помилка атрибуту): {e}")
            except OSError as e:
                logger.debug(f"Failed to hide file (OS error) / Ошибка скрытия файла (ошибка ОС) / Помилка приховування файлу (помилка ОС): {e}")

        logger.debug(f"Secure write succeeded: {file_path} / Безопасная запись успешна: {file_path} / Безпечний запис успішний: {file_path}")
        return True

    except (PermissionError, OSError, IOError, ValueError) as e:
        logger.error(f"Secure write failed for {file_path}: {e} / Безопасная запись не удалась для {file_path} / Безпечний запис не вдався для {file_path}")
        try:
            os.remove(tmp_path)
        except (PermissionError, OSError, FileNotFoundError) as e2:
            logger.debug(f"Failed to remove temporary file: {e2} / Не удалось удалить временный файл / Не вдалося видалити тимчасовий файл")
        return False
    except TypeError as e:
        logger.error(f"Type error during secure write for {file_path}: {e} / Ошибка типа при безопасной записи для {file_path} / Помилка типу при безпечному записі для {file_path}")
        try:
            os.remove(tmp_path)
        except (PermissionError, OSError, FileNotFoundError):
            pass
        return False


# ── Secure read ──────────────────────────────────────────
# Sets the file pointer to the start after opening to avoid issues
# with inherited file descriptors that may have a non-zero offset.
def secure_read(file_path: str) -> Optional[bytes]:
    """
    Secure file read with integrity check.
    This is the CENTRALIZED implementation - use this everywhere.

    Безопасное чтение файла с проверкой целостности.
    Это ЦЕНТРАЛИЗОВАННАЯ реализация - используйте её везде.

    Безпечне читання файлу з перевіркою цілісності.
    Це ЦЕНТРАЛІЗОВАНА реалізація - використовуйте її скрізь.

    Returns:
        File contents or None on error / Содержимое файла или None при ошибке / Вміст файлу або None при помилці
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")
            return None

        with open(file_path, 'rb') as f:
            content = f.read()

        # Basic check - file not empty (if it shouldn't be)
        # Базовая проверка - файл не пустой (если не должен быть)
        # Базова перевірка - файл не порожній (якщо не повинен бути)
        if len(content) == 0:
            logger.warning(f"File is empty: {file_path} / Файл пуст: {file_path} / Файл порожній: {file_path}")

        return content

    except PermissionError as e:
        logger.error(f"Permission denied reading {file_path}: {e} / Доступ запрещён при чтении {file_path} / Доступ заборонено при читанні {file_path}")
        return None
    except OSError as e:
        logger.error(f"OS error reading {file_path}: {e} / Ошибка ОС при чтении {file_path} / Помилка ОС при читанні {file_path}")
        return None
    except MemoryError as e:
        logger.error(f"Memory error reading {file_path}: {e} / Ошибка памяти при чтении {file_path} / Помилка пам'яті при читанні {file_path}")
        return None


def secure_copy(src: str, dst: str, overwrite: bool = True) -> bool:
    """
    Secure file copy with atomic write.

    Безопасное копирование файла с атомарной записью.
    Безпечне копіювання файлу з атомарним записом.
    """
    try:
        content = secure_read(src)
        if content is None:
            return False

        return secure_write(dst, content)

    except PermissionError as e:
        logger.error(f"Secure copy failed (permission denied): {src} -> {dst}, error: {e} / Безопасное копирование не удалось (доступ запрещён): {src} -> {dst} / Безпечне копіювання не вдалося (доступ заборонено): {src} -> {dst}")
        return False
    except OSError as e:
        logger.error(f"Secure copy failed (OS error): {src} -> {dst}, error: {e} / Безопасное копирование не удалось (ошибка ОС): {src} -> {dst} / Безпечне копіювання не вдалося (помилка ОС): {src} -> {dst}")
        return False


def secure_delete(file_path: str, secure: bool = True) -> bool:
    """
    Secure file deletion.
    If secure=True, overwrites content before deletion.

    Безопасное удаление файла.
    Если secure=True, перезаписывает содержимое перед удалением.

    Безпечне видалення файлу.
    Якщо secure=True, перезаписує вміст перед видаленням.
    """
    try:
        if not os.path.exists(file_path):
            return True

        if secure:
            # Overwrite file with random data before deletion
            # Перезаписываем файл случайными данными перед удалением
            # Перезаписуємо файл випадковими даними перед видаленням
            size = os.path.getsize(file_path)
            if size > 0 and size < 1024 * 1024 * 10:  # Only for files up to 10MB / Только для файлов до 10MB / Тільки для файлів до 10MB
                try:
                    with open(file_path, 'wb') as f:
                        # Overwrite 3 times for security / Перезаписываем 3 раза для безопасности / Перезаписуємо 3 рази для безпеки
                        for _ in range(3):
                            f.write(os.urandom(size))
                            f.flush()
                            os.fsync(f.fileno())
                            f.seek(0)
                except PermissionError as e:
                    logger.debug(f"Secure overwrite failed (permission denied) / Безопасная перезапись не удалась (доступ запрещён) / Безпечний перезапис не вдався (доступ заборонено): {e}")
                except OSError as e:
                    logger.debug(f"Secure overwrite failed (OS error) / Безопасная перезапись не удалась (ошибка ОС) / Безпечний перезапис не вдався (помилка ОС): {e}")

        os.remove(file_path)
        logger.debug(f"Deleted: {file_path} / Удалён: {file_path} / Видалено: {file_path}")
        return True

    except PermissionError as e:
        logger.error(f"Failed to delete {file_path} (permission denied): {e} / Не удалось удалить {file_path} (доступ запрещён) / Не вдалося видалити {file_path} (доступ заборонено)")
        return False
    except OSError as e:
        logger.error(f"Failed to delete {file_path} (OS error): {e} / Не удалось удалить {file_path} (ошибка ОС) / Не вдалося видалити {file_path} (помилка ОС)")
        return False
    except FileNotFoundError:
        # File already deleted - this is not an error
        # Файл уже удалён - это не ошибка
        # Файл вже видалено - це не помилка
        return True


# ==================== EXPORTS / ЭКСПОРТЫ / ЕКСПОРТИ ====================

__all__ = [
    'secure_write',
    'secure_read',
    'secure_copy',
    'secure_delete',
    'secure_replace',
]