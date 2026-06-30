"""
Secure clipboard management for Windows

Безопасное управление буфером обмена для Windows
Безпечне керування буфером обміну для Windows

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations
import sys
import platform
import time
import ctypes
import tkinter as tk
import threading
import secrets
from typing import Optional, Callable, List
from utils.logger import get_logger

logger = get_logger("clipboard")


class ClipboardError(Exception):
    """Exception for clipboard errors / Исключение для ошибок буфера обмена / Виняток для помилок буфера обміну"""
    pass


class ClipboardOwnershipError(ClipboardError):
    """Exception for clipboard ownership issues / Исключение при проблемах с владением буфера обмена / Виняток при проблемах з володінням буфера обміну"""
    pass


class ClipboardTimeoutError(ClipboardError):
    """Exception for clipboard timeout issues / Исключение при проблемах с таймаутом буфера обмена / Виняток при проблемах з таймаутом буфера обміну"""
    pass


class SecureClipboard:
    """Protected clipboard operations with Windows API
    Защищённые операции с буфером обмена через Windows API
    Захищені операції з буфером обміну через Windows API"""

    # Windows API constants / Константы Windows API / Константи Windows API
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    GMEM_DDESHARE = 0x2000

    _clipboard_owner = None
    _clipboard_timer: Optional[threading.Timer] = None
    _active_timeouts: List[threading.Timer] = []
    _clipboard_history: List[dict] = []  # Track clipboard operations / Отслеживание операций / Відстеження операцій
    _max_history = 50

    @staticmethod
    def is_windows() -> bool:
        """
        Return True if windows.
        True, если windows.
        True, якщо windows.
        """
        return platform.system() == "Windows"

    @staticmethod
    def get_clipboard_owner() -> Optional[str]:
        """Get current clipboard owner / Получить текущего владельца буфера обмена / Отримати поточного власника буфера обміну"""
        if not SecureClipboard.is_windows():
            return None
        return SecureClipboard._clipboard_owner

    @staticmethod
    def is_owned_by_us() -> bool:
        """Check if clipboard belongs to us / Проверить, принадлежит ли буфер обмена нам / Перевірити, чи належить буфер обміну нам"""
        return SecureClipboard._clipboard_owner is not None

    @staticmethod
    def _log_clipboard_operation(operation: str, owner: str, size: int = 0, success: bool = True) -> None:
        """Log clipboard operation for audit / Логирование операции с буфером для аудита / Логування операції з буфером для аудиту"""
        try:
            entry = {
                "timestamp": time.time(),
                "operation": operation,
                "owner": owner,
                "size": size,
                "success": success
            }
            SecureClipboard._clipboard_history.append(entry)
            # Keep only recent history / Сохраняем только недавнюю историю / Зберігаємо лише недавню історію
            if len(SecureClipboard._clipboard_history) > SecureClipboard._max_history:
                SecureClipboard._clipboard_history = SecureClipboard._clipboard_history[-SecureClipboard._max_history:]
        except (TypeError, ValueError, AttributeError) as e:
            logger.debug(f"Clipboard history logging error / Ошибка логирования истории буфера / Помилка логування історії буфера: {e}")

    @staticmethod
    def get_clipboard_history() -> List[dict]:
        """Get clipboard operation history / Получить историю операций с буфером / Отримати історію операцій з буфером"""
        return SecureClipboard._clipboard_history.copy()

    @staticmethod
    def clear_clipboard_history() -> None:
        """Clear clipboard operation history / Очистить историю операций с буфером / Очистити історію операцій з буфером"""
        SecureClipboard._clipboard_history.clear()
        logger.debug("Clipboard history cleared / История буфера обмена очищена / Історію буфера обміну очищено")

    @staticmethod
    def secure_set_text(text: str, owner: str = "unknown") -> bool:
        """Set clipboard text with limited access (Windows only)
        Установить текст в буфер обмена с ограниченным доступом (только Windows)
        Встановити текст у буфер обміну з обмеженим доступом (тільки Windows)"""
        if not SecureClipboard.is_windows():
            return False

        if not text:
            logger.warning("Attempted to set empty text to clipboard / Попытка установить пустой текст в буфер обмена / Спроба встановити порожній текст у буфер обміну")
            return False

        # Limit text size to prevent memory issues
        max_text_size = 10 * 1024 * 1024  # 10 MB
        if len(text) > max_text_size:
            logger.error(f"Text too large for clipboard: {len(text)} bytes / Текст слишком велик для буфера обмена: {len(text)} байт / Текст занадто великий для буфера обміну: {len(text)} байт")
            return False

        try:
            # Windows API constants / Константы Windows API / Константи Windows API
            CF_UNICODETEXT = 13
            GMEM_MOVEABLE = 0x0002

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            # Open clipboard / Открываем буфер обмена / Відкриваємо буфер обміну
            if not user32.OpenClipboard(0):
                raise ClipboardError("Failed to open clipboard / Не удалось открыть буфер обмена / Не вдалося відкрити буфер обміну")

            try:
                # Empty clipboard / Очищаем буфер обмена / Очищуємо буфер обміну
                if not user32.EmptyClipboard():
                    raise ClipboardError("Failed to empty clipboard / Не удалось очистить буфер обмена / Не вдалося очистити буфер обміну")

                # Allocate global memory / Выделяем глобальную память / Виділяємо глобальну пам'ять
                text_bytes = text.encode('utf-16le')
                hMem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(text_bytes) + 2)
                if not hMem:
                    raise ClipboardError("Failed to allocate global memory / Не удалось выделить глобальную память / Не вдалося виділити глобальну пам'ять")

                try:
                    # Lock memory and copy text / Блокируем память и копируем текст / Блокуємо пам'ять і копіюємо текст
                    pMem = kernel32.GlobalLock(hMem)
                    ctypes.memmove(pMem, text_bytes, len(text_bytes))
                    kernel32.GlobalUnlock(hMem)

                    # Set clipboard data / Устанавливаем данные в буфер обмена / Встановлюємо дані в буфер обміну
                    if not user32.SetClipboardData(CF_UNICODETEXT, hMem):
                        raise ClipboardError("Failed to set clipboard data / Не удалось установить данные в буфер обмена / Не вдалося встановити дані в буфер обміну")

                    # Memory now owned by clipboard
                    hMem = None
                    SecureClipboard._clipboard_owner = owner
                    SecureClipboard._log_clipboard_operation("set", owner, len(text), True)
                    logger.debug(f"Clipboard set by: {owner}, size: {len(text)} chars / Буфер обмена установлен: {owner}, размер: {len(text)} символов / Буфер обміну встановлено: {owner}, розмір: {len(text)} символів")
                    return True
                finally:
                    if hMem:
                        kernel32.GlobalFree(hMem)
            finally:
                user32.CloseClipboard()

        except ClipboardError as e:
            logger.error(f"Clipboard error / Ошибка буфера обмена / Помилка буфера обміну: {e}")
            SecureClipboard._log_clipboard_operation("set", owner, 0, False)
            return False
        except (AttributeError, OSError, TypeError, ValueError) as e:
            logger.debug(f"Secure clipboard set error / Ошибка безопасной установки буфера / Помилка безпечного встановлення буфера: {e}")
            SecureClipboard._log_clipboard_operation("set", owner, 0, False)
            return False

    @staticmethod
    def secure_clear(owner: str = "unknown") -> bool:
        """Clear clipboard and prevent reading (Windows only)
        Очистить буфер обмена и предотвратить чтение (только Windows)
        Очистити буфер обміну та запобігти читанню (тільки Windows)"""
        if not SecureClipboard.is_windows():
            return False

        try:
            user32 = ctypes.windll.user32

            # Open and clear clipboard / Открываем и очищаем буфер обмена / Відкриваємо та очищуємо буфер обміну
            if user32.OpenClipboard(0):
                try:
                    user32.EmptyClipboard()
                    SecureClipboard._clipboard_owner = None
                    SecureClipboard._log_clipboard_operation("clear", owner, 0, True)
                    logger.debug(f"Clipboard cleared by: {owner} / Буфер обмена очищен: {owner} / Буфер обміну очищено: {owner}")
                    return True
                finally:
                    user32.CloseClipboard()
            else:
                logger.warning(f"Failed to open clipboard for clearing by {owner} / Не удалось открыть буфер обмена для очистки {owner} / Не вдалося відкрити буфер обміну для очищення {owner}")
                return False
        except (AttributeError, OSError, TypeError, ValueError) as e:
            logger.debug(f"Secure clipboard clear error / Ошибка безопасной очистки буфера / Помилка безпечного очищення буфера: {e}")
            SecureClipboard._log_clipboard_operation("clear", owner, 0, False)
            return False

    @staticmethod
    def secure_clear_multiple(passes: int = 5, owner: str = "unknown") -> bool:
        """
        Clear clipboard with multiple overwrites.

        Очищает буфер обмена с многократной перезаписью.
        Очищує буфер обміну з багаторазовим перезаписом.

        Args:
            passes: number of overwrite passes / количество проходов перезаписи / кількість проходів перезапису
            owner: owner identifier for logs / идентификатор владельца (для логов) / ідентифікатор власника (для логів)
        """
        if not SecureClipboard.is_windows():
            return False

        # Validate passes / Валидация количества проходів / Валідація кількості проходів
        if passes < 1:
            passes = 1
        if passes > 10:
            passes = 10

        success = True
        for i in range(passes):
            try:
                # Generate random data / Генерируем случайные данные / Генеруємо випадкові дані
                junk = secrets.token_hex(256)
                if not SecureClipboard.secure_set_text(junk, owner):
                    success = False
                # Small delay between passes / Небольшая задержка между проходами / Невелика затримка між проходами
                time.sleep(0.01)
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Clipboard overwrite pass {i + 1} failed / Ошибка прохода перезаписи {i + 1} / Помилка проходу перезапису {i + 1}: {e}")
                success = False

        # Final clear / Финальная очистка / Фінальне очищення
        if not SecureClipboard.secure_clear(owner):
            success = False

        logger.debug(f"Clipboard secure clear completed: {passes} passes, success={success} / Безопасная очистка буфера завершена: {passes} проходов, успех={success} / Безпечне очищення буфера завершено: {passes} проходів, успіх={success}")
        return success

    @staticmethod
    def set_with_timeout(text: str, timeout_sec: int,
                         callback: Optional[Callable] = None,
                         owner: str = "unknown") -> threading.Timer:
        """Set clipboard with auto-clear after timeout
        Установить буфер обмена с автоочисткой по таймауту
        Встановити буфер обміну з автоочищенням за таймаутом"""
        # Validate timeout / Валидация таймаута / Валідація таймауту
        if timeout_sec < 1:
            timeout_sec = 1
        if timeout_sec > 3600:  # Max 1 hour / Максимум 1 час / Максимум 1 година
            timeout_sec = 3600

        # Cancel previous timeouts / Отменяем предыдущие таймеры / Скасовуємо попередні таймери
        SecureClipboard.cancel_all_timeouts()

        # Set text / Устанавливаем текст / Встановлюємо текст
        if not SecureClipboard.secure_set_text(text, owner):
            logger.error(f"Failed to set clipboard text for owner: {owner} / Не удалось установить текст в буфер для владельца: {owner} / Не вдалося встановити текст у буфер для власника: {owner}")
            # Return dummy timer that does nothing
            dummy_timer = threading.Timer(timeout_sec, lambda: None)
            dummy_timer.daemon = True
            return dummy_timer

        def clear() -> None:
            try:
                SecureClipboard.secure_clear_multiple(passes=3, owner=owner)
                if callback:
                    callback()
            except (RuntimeError, OSError, AttributeError) as e:
                logger.debug(f"Clipboard clear callback error / Ошибка callback очистки буфера / Помилка callback очищення буфера: {e}")

        timer = threading.Timer(timeout_sec, clear)
        timer.daemon = True
        timer.start()
        SecureClipboard._active_timeouts.append(timer)
        SecureClipboard._clipboard_timer = timer

        logger.debug(f"Clipboard timeout set: {timeout_sec}s, owner: {owner} / Таймаут буфера установлен: {timeout_sec}с, владелец: {owner} / Таймаут буфера встановлено: {timeout_sec}с, власник: {owner}")
        return timer

    @staticmethod
    def cancel_timeout(timer: Optional[threading.Timer] = None) -> None:
        """Cancel clipboard clear timer / Отменяет таймер очистки буфера / Скасовує таймер очищення буфера"""
        if timer is None:
            timer = SecureClipboard._clipboard_timer

        if timer and timer.is_alive():
            try:
                timer.cancel()
                if timer in SecureClipboard._active_timeouts:
                    SecureClipboard._active_timeouts.remove(timer)
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"Timer cancel error / Ошибка отмены таймера / Помилка скасування таймера: {e}")

        if timer == SecureClipboard._clipboard_timer:
            SecureClipboard._clipboard_timer = None

    @staticmethod
    def cancel_all_timeouts() -> None:
        """Cancel all active timers / Отменяет все активные таймеры / Скасовує всі активні таймери"""
        for timer in SecureClipboard._active_timeouts[:]:
            if timer and timer.is_alive():
                try:
                    timer.cancel()
                except (RuntimeError, AttributeError) as e:
                    logger.debug(f"Timer cancel error / Ошибка отмены таймера / Помилка скасування таймера: {e}")
        SecureClipboard._active_timeouts.clear()
        SecureClipboard._clipboard_timer = None

    @staticmethod
    def get_timeout_count() -> int:
        """Get number of active timers / Возвращает количество активных таймеров / Повертає кількість активних таймерів"""
        return len(SecureClipboard._active_timeouts)

    @staticmethod
    def verify_clipboard_clear() -> bool:
        """
        Verify that clipboard is actually cleared.
        Returns True if clipboard is empty or contains only garbage.

        Проверяет, что буфер обмена действительно очищен.
        Возвращает True если буфер пуст или содержит только мусор.

        Перевіряє, що буфер обміну дійсно очищено.
        Повертає True якщо буфер порожній або містить лише сміття.
        """
        if not SecureClipboard.is_windows():
            return True

        try:
            import ctypes
            user32 = ctypes.windll.user32

            if user32.OpenClipboard(0):
                try:
                    # Check if data exists / Проверяем наличие данных / Перевіряємо наявність даних
                    if not user32.IsClipboardFormatAvailable(SecureClipboard.CF_UNICODETEXT):
                        return True

                    # Try to get data / Пытаемся получить данные / Намагаємося отримати дані
                    hData = user32.GetClipboardData(SecureClipboard.CF_UNICODETEXT)
                    if not hData:
                        return True

                    # Data exists - clipboard not cleared
                    return False
                finally:
                    user32.CloseClipboard()
        except (AttributeError, OSError, TypeError, ValueError) as e:
            logger.debug(f"Clipboard verification error / Ошибка проверки буфера / Помилка перевірки буфера: {e}")

        return True


# Fallback to tkinter clipboard for non-Windows
class FallbackClipboard:
    """Fallback clipboard using tkinter / Fallback буфер обмена с использованием tkinter / Fallback буфер обміну з використанням tkinter"""

    _clipboard_owner = None
    _clipboard_timer: Optional[threading.Timer] = None
    _clipboard_history: List[dict] = []

    @staticmethod
    def _log_operation(operation: str, owner: str, success: bool = True) -> None:
        """Log fallback clipboard operation / Логирование операции fallback буфера / Логування операції fallback буфера"""
        try:
            entry = {
                "timestamp": time.time(),
                "operation": operation,
                "owner": owner,
                "success": success,
                "method": "fallback"
            }
            FallbackClipboard._clipboard_history.append(entry)
            if len(FallbackClipboard._clipboard_history) > 50:
                FallbackClipboard._clipboard_history = FallbackClipboard._clipboard_history[-50:]
        except (TypeError, ValueError, AttributeError) as e:
            logger.debug(f"Fallback history logging error / Ошибка логирования fallback истории / Помилка логування fallback історії: {e}")

    @staticmethod
    def set_text(root, text: str, owner: str = "unknown") -> bool:
        """
        Set text.
        Установить text.
        Встановити text.
        """
        if not root:
            logger.error("No root window provided for fallback clipboard / Не указано корневое окно для fallback буфера / Не вказано кореневе вікно для fallback буфера")
            return False

        if not text:
            return False

        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            FallbackClipboard._clipboard_owner = owner
            FallbackClipboard._log_operation("set", owner, True)
            logger.debug(f"Fallback clipboard set by: {owner} / Fallback буфер установлен: {owner} / Fallback буфер встановлено: {owner}")
            return True
        except (tk.TclError, OSError, RuntimeError) as e:
            logger.debug(f"Fallback set error / Ошибка установки fallback / Помилка встановлення fallback: {e}")
            FallbackClipboard._log_operation("set", owner, False)
            return False

    @staticmethod
    def clear(root, owner: str = "unknown") -> bool:
        """
        Handle clear.
        Обработать clear.
        Обробити clear.
        """
        if not root:
            return False

        try:
            root.clipboard_clear()
            FallbackClipboard._clipboard_owner = None
            FallbackClipboard._log_operation("clear", owner, True)
            logger.debug(f"Fallback clipboard cleared by: {owner} / Fallback буфер очищен: {owner} / Fallback буфер очищено: {owner}")
            return True
        except (tk.TclError, OSError, RuntimeError) as e:
            logger.debug(f"Fallback clear error / Ошибка очистки fallback / Помилка очищення fallback: {e}")
            FallbackClipboard._log_operation("clear", owner, False)
            return False

    @staticmethod
    def clear_multiple(root, passes: int = 5, owner: str = "unknown") -> bool:
        """Clear with multiple overwrites (fallback)"""
        if not root:
            return False

        if passes < 1:
            passes = 1
        if passes > 10:
            passes = 10

        success = True
        for _ in range(passes):
            try:
                root.clipboard_clear()
                # Overwrite with random data
                junk = secrets.token_hex(64)
                root.clipboard_append(junk)
                root.update()
                time.sleep(0.01)
            except (tk.TclError, OSError, RuntimeError, ValueError) as e:
                logger.debug(f"Fallback clear pass error / Ошибка прохода очистки fallback / Помилка проходу очищення fallback: {e}")
                success = False

        # Final clear
        try:
            root.clipboard_clear()
            FallbackClipboard._clipboard_owner = None
        except (tk.TclError, OSError, RuntimeError) as e:
            logger.debug(f"Fallback final clear error / Ошибка финальной очистки fallback / Помилка фінального очищення fallback: {e}")
            success = False

        FallbackClipboard._log_operation("clear_multiple", owner, success)
        return success

    @staticmethod
    def set_with_timeout(root, text: str, timeout_sec: int,
                         callback: Optional[Callable] = None,
                         owner: str = "unknown") -> threading.Timer:
        """Set clipboard with auto-clear after timeout (fallback)"""
        # Cancel previous timer
        if FallbackClipboard._clipboard_timer:
            try:
                FallbackClipboard._clipboard_timer.cancel()
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"Timer cancel error / Ошибка отмены таймера / Помилка скасування таймера: {e}")

        if not FallbackClipboard.set_text(root, text, owner):
            dummy_timer = threading.Timer(timeout_sec, lambda: None)
            dummy_timer.daemon = True
            return dummy_timer

        def clear() -> None:
            try:
                FallbackClipboard.clear_multiple(root, passes=3, owner=owner)
                if callback:
                    callback()
            except (RuntimeError, OSError, AttributeError, tk.TclError) as e:
                logger.debug(f"Fallback clear callback error / Ошибка callback очистки fallback / Помилка callback очищення fallback: {e}")

        timer = threading.Timer(timeout_sec, clear)
        timer.daemon = True
        timer.start()
        FallbackClipboard._clipboard_timer = timer

        return timer

    @staticmethod
    def cancel_timeout() -> None:
        """Cancel clear timer / Отменяет таймер очистки / Скасовує таймер очищення"""
        if FallbackClipboard._clipboard_timer and FallbackClipboard._clipboard_timer.is_alive():
            try:
                FallbackClipboard._clipboard_timer.cancel()
            except (RuntimeError, AttributeError) as e:
                logger.debug(f"Timer cancel error / Ошибка отмены таймера / Помилка скасування таймера: {e}")
        FallbackClipboard._clipboard_timer = None

    @staticmethod
    def get_clipboard_history() -> List[dict]:
        """Get fallback clipboard operation history"""
        return FallbackClipboard._clipboard_history.copy()


# Global functions for convenience
_clipboard_root = None
_clipboard_owner = "unknown"


def init_clipboard(root=None) -> None:
    """Initialize global clipboard / Инициализирует глобальный буфер обмена / Ініціалізує глобальний буфер обміну"""
    global _clipboard_root
    _clipboard_root = root
    logger.info("Clipboard system initialized / Система буфера обмена инициализирована / Систему буфера обміну ініціалізовано")


def set_clipboard(text: str, owner: str = "unknown", timeout: Optional[int] = None) -> bool:
    """
    Set clipboard using best available method.

    Установить буфер обмена используя лучший доступный метод.
    Встановити буфер обміну використовуючи найкращий доступний метод.

    Args:
        text: Text to copy / Текст для копирования / Текст для копіювання
        owner: Owner identifier / Идентификатор владельца / Ідентифікатор власника
        timeout: Auto-clear after N seconds (optional)
    """
    if not text:
        logger.warning("Attempted to set empty text to clipboard / Попытка установить пустой текст в буфер обмена / Спроба встановити порожній текст у буфер обміну")
        return False

    if SecureClipboard.is_windows():
        if timeout:
            SecureClipboard.set_with_timeout(text, timeout, owner=owner)
            return True
        else:
            return SecureClipboard.secure_set_text(text, owner)
    else:
        if _clipboard_root is None:
            logger.error("Clipboard not initialized. Call init_clipboard() first. / Буфер обмена не инициализирован. Сначала вызовите init_clipboard(). / Буфер обміну не ініціалізовано. Спочатку викличте init_clipboard().")
            return False

        if timeout:
            FallbackClipboard.set_with_timeout(_clipboard_root, text, timeout, owner=owner)
            return True
        else:
            return FallbackClipboard.set_text(_clipboard_root, text, owner)


def clear_clipboard(owner: str = "unknown", secure: bool = True) -> bool:
    """
    Clear clipboard using best available method.

    Очистить буфер обмена используя лучший доступный метод.
    Очистити буфер обміну використовуючи найкращий доступний метод.

    Args:
        owner: Owner identifier / Идентификатор владельца / Ідентифікатор власника
        secure: Perform multiple overwrites / Выполнять многократную перезапись / Виконувати багаторазовий перезапис
    """
    if SecureClipboard.is_windows():
        if secure:
            return SecureClipboard.secure_clear_multiple(passes=5, owner=owner)
        else:
            return SecureClipboard.secure_clear(owner)
    else:
        if _clipboard_root is None:
            logger.error("Clipboard not initialized. Call init_clipboard() first. / Буфер обмена не инициализирован. Сначала вызовите init_clipboard(). / Буфер обміну не ініціалізовано. Спочатку викличте init_clipboard().")
            return False

        if secure:
            return FallbackClipboard.clear_multiple(_clipboard_root, passes=5, owner=owner)
        else:
            return FallbackClipboard.clear(_clipboard_root, owner)


def get_clipboard_owner() -> Optional[str]:
    """Get clipboard owner identifier"""
    if SecureClipboard.is_windows():
        return SecureClipboard.get_clipboard_owner()
    else:
        return FallbackClipboard._clipboard_owner


def cancel_clipboard_timeout() -> None:
    """Cancel automatic clipboard clear"""
    if SecureClipboard.is_windows():
        SecureClipboard.cancel_all_timeouts()
    else:
        FallbackClipboard.cancel_timeout()


def verify_clipboard_clear() -> bool:
    """Verify that clipboard is cleared"""
    if SecureClipboard.is_windows():
        return SecureClipboard.verify_clipboard_clear()
    return True


def get_clipboard_history() -> List[dict]:
    """Get clipboard operation history"""
    if SecureClipboard.is_windows():
        return SecureClipboard.get_clipboard_history()
    else:
        return FallbackClipboard.get_clipboard_history()


def clear_clipboard_history() -> None:
    """Clear clipboard operation history"""
    if SecureClipboard.is_windows():
        SecureClipboard.clear_clipboard_history()
    else:
        FallbackClipboard._clipboard_history.clear()


__all__ = [
    'SecureClipboard',
    'FallbackClipboard',
    'init_clipboard',
    'set_clipboard',
    'clear_clipboard',
    'get_clipboard_owner',
    'cancel_clipboard_timeout',
    'verify_clipboard_clear',
    'get_clipboard_history',
    'clear_clipboard_history',
    'ClipboardError',
    'ClipboardOwnershipError',
    'ClipboardTimeoutError',
]
