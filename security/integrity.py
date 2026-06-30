"""
File integrity checking - DISABLED for SHA-256 files.
SHA-256 file creation has been removed per user request.
Only simple file save without hash file.

Проверка целостности файлов - ОТКЛЮЧЕНА для SHA-256 файлов.
Создание SHA-256 файлов удалено по запросу пользователя.
Только простое сохранение файлов без хеш-файла.

Перевірка цілісності файлів - ВИМКНЕНА для SHA-256 файлів.
Створення SHA-256 файлів видалено за запитом користувача.
Тільки просте збереження файлів без хеш-файлу.

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import os
import tempfile
import hashlib
import hmac
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger("integrity")

HASH_EXTENSION = ".sha256"


class IntegrityError(Exception):
    """Exception for file integrity violation / Исключение при нарушении целостности файла / Виняток при порушенні цілісності файлу"""
    pass


class IntegrityCheckError(IntegrityError):
    """Exception for integrity check failure / Исключение при провале проверки целостности / Виняток при провалі перевірки цілісності"""
    pass


def _atomic_write(path: str, content: bytes) -> None:
    """
    Atomic file write (without creating .sha256)

    Атомарная запись файла (без создания .sha256)
    Атомарний запис файлу (без створення .sha256)
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except (PermissionError, OSError, IOError) as e:
        try:
            os.remove(tmp_path)
        except (OSError, PermissionError):
            pass
        raise IntegrityError(f"Failed to write file atomically: {e} / Не удалось атомарно записать файл: {e} / Не вдалося атомарно записати файл: {e}")


def _calculate_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """Calculate file hash / Вычисляет хеш файла / Обчислює хеш файлу"""
    if not os.path.exists(file_path):
        return None

    try:
        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha3-256":
            hasher = hashlib.sha3_256()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm} / Неподдерживаемый алгоритм: {algorithm} / Непідтримуваний алгоритм: {algorithm}")

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e} / Не удалось вычислить хеш для {file_path} / Не вдалося обчислити хеш для {file_path}")
        return None


def verify_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> bool:
    """
    Verify file integrity.

    FIXED #21: Now returns False when no hash file exists and expected_hash is None.
    Use expected_hash parameter if you trust the file and want to skip hash verification.

    Проверка целостности файла.
    Исправлено #21: Теперь возвращает False, когда нет хеш-файла и expected_hash не указан.
    Используйте параметр expected_hash, если вы доверяете файлу и хотите пропустить проверку хеша.

    Перевірка цілісності файлу.
    Виправлено #21: Тепер повертає False, коли немає хеш-файла та expected_hash не вказано.
    Використовуйте параметр expected_hash, якщо ви довіряєте файлу та хочете пропустити перевірку хеша.

    Args:
        file_path: path to file / путь к файлу / шлях до файлу
        expected_hash: expected hash (optional) / ожидаемый хеш (опционально) / очікуваний хеш (опціонально)

    Returns:
        True if file is intact, False if integrity is violated or cannot be verified
        True если файл цел, False в случае нарушения или невозможности проверки
        True якщо файл цілий, False у разі порушення або неможливості перевірки
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")
        return False

    try:
        # If hash is provided, use it directly
        if expected_hash:
            actual_hash = _calculate_file_hash(file_path)
            if actual_hash is None:
                logger.error(f"Could not calculate hash for {file_path} / Не удалось вычислить хеш для {file_path} / Не вдалося обчислити хеш для {file_path}")
                return False

            if hmac.compare_digest(actual_hash.lower(), expected_hash.lower()):
                logger.debug(f"Integrity check passed for {file_path} / Проверка целостности пройдена для {file_path} / Перевірку цілісності пройдено для {file_path}")
                return True
            else:
                logger.error(f"Integrity check FAILED for {file_path} / Проверка целостности НЕ ПРОЙДЕНА для {file_path} / Перевірку цілісності НЕ ПРОЙДЕНО для {file_path}")
                logger.error(f"  Expected: {expected_hash[:16]}... / Ожидалось: {expected_hash[:16]}... / Очікувалось: {expected_hash[:16]}...")
                logger.error(f"  Actual:   {actual_hash[:16]}... / Фактически: {actual_hash[:16]}... / Фактично: {actual_hash[:16]}...")
                return False

        # No expected_hash provided - look for hash file next to it
        hash_file = file_path + HASH_EXTENSION
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r', encoding='utf-8') as f:
                    expected_hash = f.read().strip()

                if expected_hash:
                    return verify_file_integrity(file_path, expected_hash)
                else:
                    logger.warning(f"Hash file is empty: {hash_file} / Файл хеша пуст: {hash_file} / Файл хеша порожній: {hash_file}")
                    return False
            except (OSError, IOError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read hash file: {e} / Не удалось прочитать файл хеша: {e} / Не вдалося прочитати файл хеша: {e}")
                return False

        # FIXED #21: No hash file and no expected_hash - treat as failure
        logger.warning(f"No hash file found for {file_path} and no expected_hash provided - integrity cannot be verified / Не найден файл хеша для {file_path} и не указан expected_hash - целостность не может быть проверена / Не знайдено файл хеша для {file_path} та не вказано expected_hash - цілісність не може бути перевірена")
        return False

    except (OSError, IOError, ValueError) as e:
        logger.error(f"Integrity verification error / Ошибка проверки целостности / Помилка перевірки цілісності: {e}")
        return False


def save_file_with_hash(file_path: str, content: bytes, create_hash: bool = False) -> bool:
    """
    Save file and optionally create .sha256 file.

    Сохраняет файл и опционально создаёт .sha256 файл.
    Зберігає файл та опціонально створює .sha256 файл.

    Args:
        file_path: path to save file / путь для сохранения файла / шлях для збереження файлу
        content: file content in bytes / содержимое файла в байтах / вміст файлу в байтах
        create_hash: whether to create hash file (default False) / создавать ли файл с хешем (по умолчанию False) / створювати чи файл з хешем (за замовчуванням False)

    Returns:
        True if file saved successfully, False on error
        True если файл успешно сохранён, False в случае ошибки
        True якщо файл успішно збережено, False у разі помилки
    """
    try:
        _atomic_write(file_path, content)

        # Check that file was actually written
        if not os.path.exists(file_path) or os.path.getsize(file_path) != len(content):
            raise IntegrityError("File size mismatch after write / Несоответствие размера файла после записи / Невідповідність розміру файлу після запису")

        # Create hash file if needed
        if create_hash:
            file_hash = _calculate_file_hash(file_path)
            if file_hash:
                hash_path = file_path + HASH_EXTENSION
                _atomic_write(hash_path, file_hash.encode('utf-8'))
                logger.debug(f"Hash file created: {hash_path} / Файл хеша создан: {hash_path} / Файл хеша створено: {hash_path}")

        logger.debug(f"File saved successfully: {file_path} / Файл успешно сохранён: {file_path} / Файл успішно збережено: {file_path}")
        return True

    except IntegrityError as e:
        logger.error(f"Integrity error saving file / Ошибка целостности при сохранении файла / Помилка цілісності при збереженні файлу: {e}")
        return False
    except (PermissionError, OSError, IOError) as e:
        logger.error(f"Failed to save file {file_path}: {e} / Не удалось сохранить файл {file_path}: {e} / Не вдалося зберегти файл {file_path}: {e}")
        return False


def verify_and_open(file_path: str, expected_hash: Optional[str] = None) -> Optional[bytes]:
    """
    Verify file integrity and return its contents.
    Fail-closed: returns None if integrity is violated or cannot be verified.

    Проверяет целостность файла и возвращает его содержимое.
    Fail-closed: при нарушении целостности или невозможности проверки возвращает None.

    Перевіряє цілісність файлу та повертає його вміст.
    Fail-closed: при порушенні цілісності або неможливості перевірки повертає None.

    Returns:
        File contents or None on error / Содержимое файла или None при ошибке / Вміст файлу або None при помилці
    """
    if not verify_file_integrity(file_path, expected_hash):
        logger.error(f"File integrity check failed, refusing to open: {file_path} / Проверка целостности файла не пройдена, отказ открытия: {file_path} / Перевірку цілісності файлу не пройдено, відмова відкриття: {file_path}")
        return None

    try:
        with open(file_path, 'rb') as f:
            return f.read()
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to open file after integrity check: {e} / Не удалось открыть файл после проверки целостности: {e} / Не вдалося відкрити файл після перевірки цілісності: {e}")
        return None


# ==================== BACKWARD COMPATIBILITY WRAPPERS ====================

def check_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Legacy wrapper for verify_file_integrity.
    Returns (is_valid, actual_hash).

    Устаревшая обёртка для verify_file_integrity.
    Возвращает (is_valid, actual_hash).

    Застаріла обгортка для verify_file_integrity.
    Повертає (is_valid, actual_hash).
    """
    is_valid = verify_file_integrity(file_path, expected_hash)
    actual_hash = _calculate_file_hash(file_path) if is_valid else None
    return is_valid, actual_hash


def get_file_hash(file_path: str) -> Optional[str]:
    """
    Legacy wrapper for _calculate_file_hash.

    Устаревшая обёртка для _calculate_file_hash.

    Застаріла обгортка для _calculate_file_hash.
    """
    return _calculate_file_hash(file_path)


__all__ = [
    'IntegrityError',
    'IntegrityCheckError',
    'verify_file_integrity',
    'save_file_with_hash',
    'verify_and_open',
    'check_file_integrity',
    'get_file_hash',
]