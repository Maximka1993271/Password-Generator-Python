"""
Global panic cleanup handler for SecurePassPro

Глобальный обработчик аварийной очистки для SecurePassPro
Глобальний обробник аварійного очищення для SecurePassPro

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations
import sys
import signal
import atexit
import os
import tempfile
import time
import threading
import gc
import hashlib
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from utils.logger import get_logger

logger = get_logger("panic")

# ==================== PANIC AUDIT LOG ====================

PANIC_LOG_FILE = os.path.join(tempfile.gettempdir(), "securepasspro_panic.log")


@dataclass
class PanicEvent:
    """Panic event structure for audit / Структура события паники для аудита / Структура події паніки для аудиту"""
    timestamp: str
    reason: str
    cleanup_duration_ms: float
    success: bool
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


def _log_panic_event(event: PanicEvent) -> None:
    """Log panic event to file / Логирование события паники в файл / Логування події паніки у файл"""
    try:
        import json
        with open(PANIC_LOG_FILE, 'a', encoding='utf-8') as f:
            json.dump(event.to_dict(), f, ensure_ascii=False)
            f.write('\n')
    except (OSError, IOError, PermissionError, TypeError, json.JSONDecodeError) as e:
        # Cannot log - but that's okay during panic
        pass


class PanicCleanup:
    """Global panic handler for emergency cleanup
    Глобальный обработчик паники для аварийной очистки
    Глобальний обробник паніки для аварійного очищення"""

    _clipboard_callbacks: List[Callable] = []
    _temp_files: List[str] = []
    _callbacks: List[Callable] = []
    _memory_cleanup_callbacks: List[Callable] = []
    _db_cleanup_callbacks: List[Callable] = []
    _panic_triggered = False
    _panic_lock = threading.Lock()
    _cleanup_completed = False
    _panic_events: List[PanicEvent] = []

    @classmethod
    def register_clipboard_cleanup(cls, callback: Callable) -> None:
        """Register clipboard cleanup function
        Регистрирует функцию очистки буфера обмена
        Реєструє функцію очищення буфера обміну"""
        if callback not in cls._clipboard_callbacks:
            cls._clipboard_callbacks.append(callback)

    @classmethod
    def register_temp_file(cls, file_path: str) -> None:
        """Register temporary file for cleanup
        Регистрирует временный файл для очистки
        Реєструє тимчасовий файл для очищення"""
        if file_path not in cls._temp_files:
            cls._temp_files.append(file_path)

    @classmethod
    def register_cleanup_callback(cls, callback: Callable) -> None:
        """Register general cleanup callback
        Регистрирует общий callback очистки
        Реєструє загальний callback очищення"""
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)

    @classmethod
    def register_memory_cleanup(cls, callback: Callable) -> None:
        """Register memory cleanup callback
        Регистрирует callback очистки памяти
        Реєструє callback очищення пам'яті"""
        if callback not in cls._memory_cleanup_callbacks:
            cls._memory_cleanup_callbacks.append(callback)

    @classmethod
    def register_db_cleanup(cls, callback: Callable) -> None:
        """Register database cleanup callback
        Регистрирует callback очистки базы данных
        Реєструє callback очищення бази даних"""
        if callback not in cls._db_cleanup_callbacks:
            cls._db_cleanup_callbacks.append(callback)

    @classmethod
    def _get_panic_events(cls) -> List[Dict[str, Any]]:
        """Get panic events for audit / Получить события паники для аудита / Отримати події паніки для аудиту"""
        return [e.to_dict() for e in cls._panic_events[-20:]]  # Last 20 events

    @classmethod
    def emergency_cleanup(cls, reason: str = "unknown") -> None:
        """
        Emergency cleanup on crash/exit.
        Fail-closed: guarantees cleanup even on errors.

        Аварийная очистка при сбое/завершении.
        Fail-closed: гарантирует очистку даже при ошибках.

        Аварійне очищення при збої/завершенні.
        Fail-closed: гарантує очищення навіть при помилках.
        """
        with cls._panic_lock:
            if cls._panic_triggered:
                return
            cls._panic_triggered = True

        start_time = time.time()
        logger.warning(f"Emergency cleanup triggered: {reason} / Аварийная очистка вызвана: {reason} / Аварійне очищення викликано: {reason}")

        # List of errors for logging (does not interrupt cleanup)
        errors = []

        # ========== 1. Clipboard cleanup (critical) ==========
        for callback in cls._clipboard_callbacks:
            try:
                callback()
            except (AttributeError, RuntimeError, OSError, TypeError) as e:
                err_msg = f"Clipboard cleanup callback error / Ошибка callback очистки буфера / Помилка callback очищення буфера: {e}"
                logger.debug(err_msg)
                errors.append(err_msg)

        # Additional Windows API clipboard cleanup (fallback)
        try:
            cls._emergency_clipboard_clear_windows()
        except (AttributeError, OSError, RuntimeError, TypeError) as e:
            err_msg = f"Windows clipboard clear error / Ошибка очистки буфера Windows / Помилка очищення буфера Windows: {e}"
            logger.debug(err_msg)
            errors.append(err_msg)

        # ========== 2. Temporary files cleanup with overwrite ==========
        for file_path in cls._temp_files[:]:
            try:
                if os.path.exists(file_path):
                    # Overwrite before deletion
                    try:
                        size = os.path.getsize(file_path)
                        if 0 < size < 10 * 1024 * 1024:  # Only files up to 10MB
                            for _ in range(3):
                                with open(file_path, 'wb') as f:
                                    f.write(os.urandom(size))
                                    f.flush()
                                    os.fsync(f.fileno())
                    except (OSError, IOError, PermissionError, ValueError) as e:
                        logger.debug(f"File overwrite failed / Ошибка перезаписи файла / Помилка перезапису файлу: {e}")

                    # Delete
                    try:
                        os.remove(file_path)
                    except (OSError, IOError, PermissionError) as e:
                        err_msg = f"Temp file remove error / Ошибка удаления временного файла / Помилка видалення тимчасового файлу: {e}"
                        logger.debug(err_msg)
                        errors.append(err_msg)

                    if file_path in cls._temp_files:
                        cls._temp_files.remove(file_path)
            except (OSError, AttributeError, RuntimeError) as e:
                err_msg = f"Temp file cleanup error / Ошибка очистки временного файла / Помилка очищення тимчасового файлу: {e}"
                logger.debug(err_msg)
                errors.append(err_msg)

        # ========== 3. Memory cleanup with ordering ==========
        for callback in cls._memory_cleanup_callbacks:
            try:
                callback()
            except (AttributeError, RuntimeError, TypeError, MemoryError) as e:
                err_msg = f"Memory cleanup error / Ошибка очистки памяти / Помилка очищення пам'яті: {e}"
                logger.debug(err_msg)
                errors.append(err_msg)

        try:
            gc.collect()
            gc.collect()
        except (RuntimeError, ImportError) as e:
            err_msg = f"GC collect error / Ошибка сборщика мусора / Помилка збирача сміття: {e}"
            logger.debug(err_msg)
            errors.append(err_msg)

        # ========== 4. Database cleanup with flush ==========
        for callback in cls._db_cleanup_callbacks:
            try:
                callback()
            except (AttributeError, RuntimeError, OSError) as e:
                err_msg = f"DB cleanup error / Ошибка очистки БД / Помилка очищення БД: {e}"
                logger.debug(err_msg)
                errors.append(err_msg)

        # Attempt to force DB flush
        try:
            import sqlite3
            from storage.database import get_db_path
            db_path = get_db_path()
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path, timeout=1)
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                    conn.close()
                except (sqlite3.Error, OSError, RuntimeError) as e:
                    logger.debug(f"DB checkpoint error / Ошибка контрольной точки БД / Помилка контрольної точки БД: {e}")
        except (ImportError, AttributeError, OSError, RuntimeError) as e:
            logger.debug(f"DB flush error / Ошибка сброса БД / Помилка скидання БД: {e}")

        # ========== 5. General callbacks ==========
        for callback in cls._callbacks:
            try:
                callback()
            except (AttributeError, RuntimeError, TypeError, OSError) as e:
                err_msg = f"General callback error / Ошибка общего callback / Помилка загального callback: {e}"
                logger.debug(err_msg)
                errors.append(err_msg)

        cls._cleanup_completed = True
        elapsed_ms = (time.time() - start_time) * 1000

        # Log panic event for audit
        try:
            event = PanicEvent(
                timestamp=datetime.now().isoformat(),
                reason=reason,
                cleanup_duration_ms=elapsed_ms,
                success=len(errors) == 0,
                errors=errors[:10]
            )
            cls._panic_events.append(event)
            _log_panic_event(event)
        except (TypeError, ValueError, OSError) as e:
            logger.debug(f"Panic event logging error / Ошибка логирования события паники / Помилка логування події паніки: {e}")

        if errors:
            logger.warning(f"Emergency cleanup completed with {len(errors)} errors in {elapsed_ms:.0f}ms / Аварийная очистка завершена с {len(errors)} ошибками за {elapsed_ms:.0f}мс / Аварійне очищення завершено з {len(errors)} помилками за {elapsed_ms:.0f}мс")
        else:
            logger.info(f"Emergency cleanup completed successfully in {elapsed_ms:.0f}ms / Аварийная очистка успешно завершена за {elapsed_ms:.0f}мс / Аварійне очищення успішно завершено за {elapsed_ms:.0f}мс")

    @classmethod
    def _emergency_clipboard_clear_windows(cls) -> None:
        """Windows-specific clipboard clear / Очистка буфера обмена для Windows / Очищення буфера обміну для Windows"""
        if sys.platform != "win32":
            return

        try:
            import ctypes
            user32 = ctypes.windll.user32
            if user32.OpenClipboard(0):
                try:
                    user32.EmptyClipboard()
                except (AttributeError, OSError) as e:
                    logger.debug(f"EmptyClipboard error / Ошибка EmptyClipboard / Помилка EmptyClipboard: {e}")
                finally:
                    try:
                        user32.CloseClipboard()
                    except (AttributeError, OSError) as e:
                        logger.debug(f"CloseClipboard error / Ошибка CloseClipboard / Помилка CloseClipboard: {e}")
        except (ImportError, AttributeError, OSError, TypeError) as e:
            logger.debug(f"Windows clipboard clear error / Ошибка очистки буфера Windows / Помилка очищення буфера Windows: {e}")

    @classmethod
    def emergency_db_wipe(cls, db_path: str, passes: int = 3) -> bool:
        """
        Emergency database wipe - overwrites and deletes the database file.
        Returns True if successful.

        Аварийное удаление базы данных - перезаписывает и удаляет файл БД.
        Возвращает True при успехе.

        Аварійне видалення бази даних - перезаписує та видаляє файл БД.
        Повертає True при успіху.
        """
        if not os.path.exists(db_path):
            return True

        if passes < 1:
            passes = 1
        if passes > 10:
            passes = 10

        try:
            size = os.path.getsize(db_path)
            if 0 < size < 100 * 1024 * 1024:  # Only for DBs under 100MB
                with open(db_path, 'wb') as f:
                    for i in range(passes):
                        try:
                            f.write(os.urandom(size))
                            f.flush()
                            os.fsync(f.fileno())
                            f.seek(0)
                        except (OSError, IOError, ValueError) as e:
                            logger.debug(f"Overwrite pass {i + 1} error / Ошибка прохода перезаписи {i + 1} / Помилка проходу перезапису {i + 1}: {e}")
                            break

            os.remove(db_path)
            logger.info(f"Emergency DB wipe completed: {db_path} / Аварийное удаление БД завершено: {db_path} / Аварійне видалення БД завершено: {db_path}")
            return True
        except (OSError, IOError, PermissionError, ValueError) as e:
            logger.error(f"Emergency DB wipe failed / Ошибка аварийного удаления БД / Помилка аварійного видалення БД: {e}")
            return False

    @classmethod
    def secure_shutdown(cls, exit_code: int = 0) -> None:
        """
        Perform secure shutdown with emergency cleanup.
        Guarantees cleanup even on errors.

        Выполняет безопасное завершение с аварийной очисткой.
        Гарантирует очистку даже при ошибках.

        Виконує безпечне завершення з аварійним очищенням.
        Гарантує очищення навіть при помилках.
        """
        try:
            cls.emergency_cleanup(reason="secure_shutdown")
        except (RuntimeError, SystemExit, KeyboardInterrupt) as e:
            logger.error(f"Cleanup failed during shutdown / Ошибка очистки при завершении / Помилка очищення при завершенні: {e}")
        finally:
            try:
                gc.collect()
                gc.collect()
            except (ImportError, RuntimeError) as e:
                logger.debug(f"Final GC error / Ошибка финального GC / Помилка фінального GC: {e}")

        sys.exit(exit_code)

    @classmethod
    def is_panic_triggered(cls) -> bool:
        """Check if panic cleanup has been triggered / Проверить, была ли вызвана аварийная очистка / Перевірити, чи було викликано аварійне очищення"""
        return cls._panic_triggered

    @classmethod
    def is_cleanup_completed(cls) -> bool:
        """Check if cleanup has completed successfully / Проверить, завершена ли очистка успешно / Перевірити, чи завершено очищення успішно"""
        return cls._cleanup_completed

    @classmethod
    def get_panic_history(cls) -> List[Dict[str, Any]]:
        """Get panic event history for audit / Получить историю событий паники для аудита / Отримати історію подій паніки для аудиту"""
        return cls._get_panic_events()

    @classmethod
    def reset(cls) -> None:
        """Reset panic state (for testing) / Сбросить состояние паники (для тестирования) / Скинути стан паніки (для тестування)"""
        with cls._panic_lock:
            cls._panic_triggered = False
            cls._cleanup_completed = False
            cls._clipboard_callbacks.clear()
            cls._temp_files.clear()
            cls._callbacks.clear()
            cls._memory_cleanup_callbacks.clear()
            cls._db_cleanup_callbacks.clear()
            cls._panic_events.clear()

    @classmethod
    def _signal_handler(cls, signum: int, frame) -> None:
        """Signal handler for crashes / Обработчик сигналов для сбоев / Обробник сигналів для збоїв"""
        signal_names = {
            signal.SIGINT: "SIGINT",
            signal.SIGTERM: "SIGTERM",
        }
        if sys.platform != "win32":
            try:
                signal_names[signal.SIGQUIT] = "SIGQUIT"
            except AttributeError:
                pass

        name = signal_names.get(signum, f"signal_{signum}")
        try:
            cls.emergency_cleanup(reason=name)
        except (RuntimeError, SystemExit) as e:
            logger.error(f"Signal handler cleanup error / Ошибка очистки в обработчике сигнала / Помилка очищення в обробнику сигналу: {e}")
        sys.exit(1)

    @classmethod
    def _windows_exception_handler(cls, exception_type, exception_value, traceback) -> None:
        """Windows-specific exception handler / Обработчик исключений для Windows / Обробник винятків для Windows"""
        try:
            cls.emergency_cleanup(reason="unhandled_exception")
        except (RuntimeError, SystemExit) as e:
            logger.error(f"Exception handler cleanup error / Ошибка очистки в обработчике исключений / Помилка очищення в обробнику винятків: {e}")
        # Call original exception handler
        try:
            sys.__excepthook__(exception_type, exception_value, traceback)
        except (TypeError, AttributeError, RuntimeError) as e:
            logger.debug(f"Original exception hook error / Ошибка оригинального хука исключений / Помилка оригінального хука винятків: {e}")

    @classmethod
    def init(cls) -> None:
        """Initialize panic handlers / Инициализировать обработчики паники / Ініціалізувати обробники паніки"""
        # Register atexit
        try:
            atexit.register(lambda: cls.emergency_cleanup(reason="atexit"))
        except (TypeError, RuntimeError) as e:
            logger.debug(f"Atexit registration error / Ошибка регистрации atexit / Помилка реєстрації atexit: {e}")

        # Register signal handlers
        try:
            signal.signal(signal.SIGTERM, cls._signal_handler)
            signal.signal(signal.SIGINT, cls._signal_handler)
        except (ValueError, AttributeError, OSError) as e:
            logger.debug(f"Signal handler registration error / Ошибка регистрации обработчика сигналов / Помилка реєстрації обробника сигналів: {e}")

        # Unix-specific signals
        if sys.platform != "win32":
            try:
                signal.signal(signal.SIGQUIT, cls._signal_handler)
            except (ValueError, AttributeError, OSError) as e:
                logger.debug(f"SIGQUIT handler registration error / Ошибка регистрации обработчика SIGQUIT / Помилка реєстрації обробника SIGQUIT: {e}")

        # Windows-specific
        if sys.platform == "win32":
            try:
                import ctypes
                # Set error mode to prevent crash dialogs
                ctypes.windll.kernel32.SetErrorMode(0x8001)
            except (ImportError, AttributeError, OSError) as e:
                logger.debug(f"Windows error mode setting error / Ошибка установки режима ошибок Windows / Помилка встановлення режиму помилок Windows: {e}")

            try:
                sys.excepthook = cls._windows_exception_handler
            except (TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Windows exception handler error / Ошибка обработчика исключений Windows / Помилка обробника винятків Windows: {e}")

        logger.info("Panic cleanup system initialized / Система аварийной очистки инициализирована / Систему аварійного очищення ініціалізовано")


# Global hotkey for panic cleanup (Ctrl+Alt+Shift+P)
_panic_hotkey_thread = None
_panic_hotkey_running = False


def _panic_hotkey_listener() -> None:
    """Background thread for panic hotkey detection
    Фоновый поток для обнаружения горячей клавиши паники
    Фоновий потік для виявлення гарячої клавіші паніки"""
    global _panic_hotkey_running

    try:
        import keyboard
    except ImportError as e:
        logger.debug(f"Keyboard module not available, panic hotkey disabled: {e} / Модуль keyboard недоступен, горячая клавиша паники отключена / Модуль keyboard недоступний, гарячу клавішу паніки вимкнено")
        return

    def on_panic():
        logger.warning("Panic hotkey triggered! Performing emergency cleanup... / Сработала горячая клавиша паники! Выполняется аварийная очистка... / Спрацювала гаряча клавіша паніки! Виконується аварійне очищення...")
        PanicCleanup.emergency_cleanup(reason="hotkey")

    try:
        keyboard.add_hotkey('ctrl+alt+shift+p', on_panic)
        while _panic_hotkey_running:
            time.sleep(0.1)
    except (ImportError, AttributeError, OSError, RuntimeError) as e:
        logger.debug(f"Hotkey listener error / Ошибка прослушивателя горячих клавиш / Помилка прослуховувача гарячих клавіш: {e}")
    finally:
        _panic_hotkey_running = False


def start_panic_hotkey() -> None:
    """Start panic hotkey listener (Ctrl+Alt+Shift+P)
    Запустить прослушиватель горячей клавиши паники (Ctrl+Alt+Shift+P)
    Запустити прослуховувач гарячої клавіші паніки (Ctrl+Alt+Shift+P)"""
    global _panic_hotkey_thread, _panic_hotkey_running

    if _panic_hotkey_thread is not None and _panic_hotkey_thread.is_alive():
        return

    _panic_hotkey_running = True
    _panic_hotkey_thread = threading.Thread(target=_panic_hotkey_listener, daemon=True)
    try:
        _panic_hotkey_thread.start()
        logger.info("Panic hotkey enabled: Ctrl+Alt+Shift+P / Горячая клавиша паники включена: Ctrl+Alt+Shift+P / Гарячу клавішу паніки увімкнено: Ctrl+Alt+Shift+P")
    except (RuntimeError, threading.ThreadError) as e:
        logger.debug(f"Failed to start panic hotkey thread / Ошибка запуска потока горячей клавиши паники / Помилка запуску потоку гарячої клавіші паніки: {e}")
        _panic_hotkey_running = False


def stop_panic_hotkey() -> None:
    """Stop panic hotkey listener / Остановить прослушиватель горячей клавиши паники / Зупинити прослуховувач гарячої клавіші паніки"""
    global _panic_hotkey_running, _panic_hotkey_thread

    _panic_hotkey_running = False
    if _panic_hotkey_thread and _panic_hotkey_thread.is_alive():
        try:
            _panic_hotkey_thread.join(timeout=1.0)
        except (RuntimeError, threading.ThreadError) as e:
            logger.debug(f"Hotkey thread join error / Ошибка присоединения потока горячей клавиши / Помилка приєднання потоку гарячої клавіші: {e}")
    _panic_hotkey_thread = None


def init_panic_cleanup(enable_hotkey: bool = False) -> None:
    """
    Initialize panic cleanup system.

    Инициализировать систему аварийной очистки.
    Ініціалізувати систему аварійного очищення.

    Args:
        enable_hotkey: Enable panic hotkey (Ctrl+Alt+Shift+P) / Включить горячую клавишу паники / Увімкнути гарячу клавішу паніки
    """
    PanicCleanup.init()

    if enable_hotkey:
        try:
            start_panic_hotkey()
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.debug(f"Failed to start panic hotkey / Ошибка запуска горячей клавиши паники / Помилка запуску гарячої клавіші паніки: {e}")


def get_panic_history() -> List[Dict[str, Any]]:
    """Get panic event history for audit / Получить историю событий паники для аудита / Отримати історію подій паніки для аудиту"""
    return PanicCleanup.get_panic_history()


# For backward compatibility
def register_clipboard_cleanup(callback: Callable) -> None:
    """
    Handle register clipboard cleanup.
    Обработать register clipboard cleanup.
    Обробити register clipboard cleanup.
    """
    PanicCleanup.register_clipboard_cleanup(callback)


def register_temp_file(file_path: str) -> None:
    """
    Handle register temp file.
    Обработать register temp file.
    Обробити register temp file.
    """
    PanicCleanup.register_temp_file(file_path)


def register_cleanup_callback(callback: Callable) -> None:
    """
    Handle register cleanup callback.
    Обработать register cleanup callback.
    Обробити register cleanup callback.
    """
    PanicCleanup.register_cleanup_callback(callback)


__all__ = [
    'PanicCleanup',
    'init_panic_cleanup',
    'start_panic_hotkey',
    'stop_panic_hotkey',
    'register_clipboard_cleanup',
    'register_temp_file',
    'register_cleanup_callback',
    'get_panic_history',
]