"""
Secure memory management - Core functions
Безопасная работа с чувствительными данными - Основные функции
Безпечна робота з чутливими даними - Основні функції

FIXED #50: Improved secure_zero_string with multiple strategies and clear warnings
FIXED #41: Centralized logging

Исправлено #50: Улучшена secure_zero_string с несколькими стратегиями и чёткими предупреждениями
Исправлено #41: Централизованное логирование

Виправлено #50: Покращено secure_zero_string з декількома стратегіями та чіткими попередженнями
Виправлено #41: Централізоване логування
"""
from __future__ import annotations

import ctypes
import gc
from typing import Optional, Union, Any
from utils.logger import get_logger

logger = get_logger("secure_memory")


# ==================== LOW-LEVEL CLEARING FUNCTIONS ====================

def secure_zero_memory(buffer: Union[bytearray, memoryview, ctypes.Array]) -> None:
    """
    Safely zero out a memory buffer using ctypes.memset.

    Безопасно обнуляет буфер памяти.
    Безпечно обнуляє буфер пам'яті.
    """
    if buffer is None:
        return

    # Multiple passes for security
    passes = 3

    try:
        for _ in range(passes):
            if isinstance(buffer, memoryview):
                buffer_bytes = buffer.tobytes()
                if isinstance(buffer_bytes, (bytes, bytearray)):
                    length = len(buffer_bytes)
                    addr = ctypes.addressof(ctypes.c_char.from_buffer(buffer_bytes))
                    ctypes.memset(addr, 0, length)
            elif isinstance(buffer, (bytes, bytearray)):
                length = len(buffer)
                addr = ctypes.addressof(ctypes.c_char.from_buffer(buffer))
                ctypes.memset(addr, 0, length)
            elif hasattr(buffer, '__len__') and hasattr(buffer, '__getitem__'):
                for i in range(len(buffer)):
                    try:
                        buffer[i] = 0
                    except (TypeError, ValueError, IndexError):
                        pass
            else:
                try:
                    length = ctypes.sizeof(buffer)
                    addr = ctypes.addressof(buffer)
                    ctypes.memset(addr, 0, length)
                except (TypeError, AttributeError, ValueError):
                    pass
    except (TypeError, AttributeError, ValueError, OSError, BufferError) as e:
        logger.debug(f"Secure zero memory failed / Ошибка безопасного обнуления памяти / Помилка безпечного обнулення пам'яті: {e}")
        try:
            for i in range(len(buffer)):
                try:
                    buffer[i] = 0
                except (TypeError, ValueError, IndexError):
                    pass
        except (TypeError, ValueError, AttributeError) as e2:
            logger.debug(f"Fallback zeroing failed / Ошибка резервного обнуления / Помилка резервного обнулення: {e2}")


def secure_zero_string(s: str) -> None:
    """
    ATTEMPT to clear a string from memory.

    WARNING: Python strings are IMMUTABLE. This function attempts best-effort
    clearing but CANNOT guarantee complete removal from memory.

    ПЫТАЕТСЯ очистить строку из памяти.

    ВНИМАНИЕ: Строки Python НЕИЗМЕНЯЕМЫ. Эта функция пытается сделать всё возможное,
    но НЕ МОЖЕТ гарантировать полное удаление из памяти.

    НАМАГАЄТЬСЯ очистити рядок з пам'яті.

    УВАГА: Рядки Python НЕЗМІННІ. Ця функція намагається зробити все можливе,
    але НЕ МОЖЕ гарантувати повне видалення з пам'яті.
    """
    if not s:
        return

    if s.startswith(('[encrypted', 'enc1:', 'enc2:', 'enc3:', '[FILTERED]')):
        return

    max_string_length = 10000
    if len(s) > max_string_length:
        logger.debug(f"String too long for secure zeroing: {len(s)} chars - skipping / Строка слишком длинная для безопасного обнуления: {len(s)} символов - пропуск / Рядок занадто довгий для безпечного обнулення: {len(s)} символів - пропуск")
        return

    logger.debug(f"Attempting best-effort string clearing (length: {len(s)}) - NOTE: Python strings are immutable / Попытка очистки строки с максимальными усилиями (длина: {len(s)}) - ПРИМЕЧАНИЕ: строки Python неизменяемы / Спроба очищення рядка з максимальними зусиллями (довжина: {len(s)}) - ПРИМІТКА: рядки Python незмінні")

    try:
        ba = bytearray(s.encode('utf-8'))
        secure_zero_memory(ba)

        try:
            addr = id(s) + 32
            length = len(s)
            ctypes.memset(addr, 0, length)
        except (TypeError, AttributeError, OSError) as e:
            logger.debug(f"Direct string memory overwrite failed (expected): {e} / Прямая перезапись памяти строки не удалась (ожидаемо): {e} / Прямий перезапис пам'яті рядка не вдався (очікувано): {e}")

        gc.collect()
        gc.collect()

        logger.debug("Best-effort string clearing attempted (may not be fully secure) / Выполнена попытка очистки строки с максимальными усилиями (может быть не полностью безопасной) / Виконано спробу очищення рядка з максимальними зусиллями (може бути не повністю безпечною)")

    except (UnicodeEncodeError, TypeError, MemoryError, ValueError, OSError) as e:
        logger.debug(f"String clearing failed / Ошибка очистки строки / Помилка очищення рядка: {e}")


def secure_zero_dict(data: dict) -> None:
    """
    Safely clear all values in a dictionary.

    Безопасно очищает все значения в словаре.
    Безпечно очищає всі значення у словнику.
    """
    if not data:
        return

    try:
        for key in list(data.keys()):
            try:
                value = data[key]
                if isinstance(value, str):
                    secure_zero_string(value)
                elif isinstance(value, (bytes, bytearray)):
                    secure_zero_memory(value)
                elif hasattr(value, 'clear'):
                    try:
                        value.clear()
                    except (AttributeError, RuntimeError):
                        pass
                data[key] = None
            except (KeyError, RuntimeError, AttributeError, TypeError) as e:
                logger.debug(f"Dict value clearing error / Ошибка очистки значения словаря / Помилка очищення значення словника: {e}")
        data.clear()
    except (RuntimeError, AttributeError, TypeError) as e:
        logger.debug(f"Dict clearing error / Ошибка очистки словаря / Помилка очищення словника: {e}")


def wipe_variable(var: Any) -> None:
    """Attempt to safely delete a variable and clear its data
    Попытаться безопасно удалить переменную и очистить её данные
    Спробувати безпечно видалити змінну та очистити її дані"""
    if var is None:
        return

    try:
        if isinstance(var, str):
            secure_zero_string(var)
        elif isinstance(var, (bytes, bytearray)):
            secure_zero_memory(var)
        elif isinstance(var, dict):
            secure_zero_dict(var)
        elif isinstance(var, list):
            try:
                for i, item in enumerate(var):
                    if isinstance(item, str):
                        secure_zero_string(item)
                    elif isinstance(item, (bytes, bytearray)):
                        secure_zero_memory(item)
                    var[i] = None
                var.clear()
            except (TypeError, RuntimeError, AttributeError) as e:
                logger.debug(f"List clearing error / Ошибка очистки списка / Помилка очищення списку: {e}")
        elif hasattr(var, 'clear'):
            try:
                var.clear()
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"Object clear error / Ошибка очистки объекта / Помилка очищення об'єкта: {e}")
    except (TypeError, ValueError, AttributeError, RuntimeError, OSError) as e:
        logger.debug(f"Variable wiping failed / Ошибка удаления переменной / Помилка видалення змінної: {e}")
    finally:
        try:
            del var
        except (NameError, ReferenceError):
            pass


def is_memory_secure() -> bool:
    """Check if secure memory mechanisms are available
    Проверить, доступны ли механизмы безопасной памяти
    Перевірити, чи доступні механізми безпечної пам'яті"""
    try:
        test_buffer = bytearray(10)
        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(test_buffer)), 0, 10)
        return True
    except (TypeError, AttributeError, OSError, ValueError, BufferError) as e:
        logger.debug(f"Memory security check failed / Ошибка проверки безопасности памяти / Помилка перевірки безпеки пам'яті: {e}")
        return False


def get_memory_usage() -> Optional[int]:
    """Get current memory usage of the process in bytes
    Получить текущее использование памяти процесса в байтах
    Отримати поточне використання пам'яті процесу в байтах"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss
    except ImportError:
        pass
    except (OSError, AttributeError, ValueError, RuntimeError) as e:
        logger.debug(f"Memory usage check failed / Ошибка проверки использования памяти / Помилка перевірки використання пам'яті: {e}")
    return None


def force_memory_cleanup() -> None:
    """Force memory cleanup including garbage collection
    Принудительная очистка памяти, включая сборщик мусора
    Примусове очищення пам'яті, включаючи збирач сміття"""
    try:
        gc.collect()
        gc.collect()
    except (RuntimeError, ImportError) as e:
        logger.debug(f"GC collect error / Ошибка сборщика мусора / Помилка збирача сміття: {e}")


def init_secure_memory() -> None:
    """Initialize the secure memory system
    Инициализировать систему безопасной памяти
    Ініціалізувати систему безпечної пам'яті"""
    if not is_memory_secure():
        logger.warning("Secure memory fallback mode active - some protections may be limited / Активен резервный режим безопасной памяти - некоторые защиты могут быть ограничены / Активний резервний режим безпечної пам'яті - деякі захисти можуть бути обмежені")
    else:
        logger.info("Secure memory system initialized / Система безопасной памяти инициализирована / Систему безпечної пам'яті ініціалізовано")

    force_memory_cleanup()


def get_secure_string_recommendation() -> str:
    """
    Returns recommendation for secure string handling.

    Возвращает рекомендацию по безопасной работе со строками.
    Повертає рекомендацію щодо безпечної роботи з рядками.
    """
    return (
        "For truly secure string handling, use SecurePassword or SecureBytes instead of regular strings. "
        "Python strings are immutable and cannot be reliably cleared from memory. / "
        "Для действительно безопасной работы со строками используйте SecurePassword или SecureBytes вместо обычных строк. "
        "Строки Python неизменяемы и не могут быть надежно удалены из памяти. / "
        "Для дійсно безпечної роботи з рядками використовуйте SecurePassword або SecureBytes замість звичайних рядків. "
        "Рядки Python незмінні і не можуть бути надійно видалені з пам'яті."
    )


# Initialize on module import
init_secure_memory()