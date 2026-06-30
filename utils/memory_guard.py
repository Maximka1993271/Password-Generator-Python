"""
Secure memory management - MemoryGuard class and monitoring
Безопасная работа с чувствительными данными - Класс MemoryGuard и мониторинг
Безпечна робота з чутливими даними - Клас MemoryGuard та моніторинг
"""
from __future__ import annotations

import time
import gc
import threading
from typing import Optional
from utils.logger import get_logger
from utils.secure_bytes import SecureBytes

logger = get_logger("secure_memory")


class MemoryGuard:
    """Context manager for memory protection with memory pressure handling

    Контекстный менеджер для защиты памяти с обработкой давления памяти
    Контекстний менеджер для захисту пам'яті з обробкою тиску пам'яті
    """

    __slots__ = ('sensitive_data', '_pressure_callback')

    def __init__(self, pressure_callback=None) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.sensitive_data = []
        self._pressure_callback = pressure_callback

        if pressure_callback is None:
            self._pressure_callback = self._handle_memory_pressure

    def register(self, data: SecureBytes) -> None:
        """Register data for automatic clearing
        Регистрирует данные для автоматической очистки
        Реєструє дані для автоматичного очищення"""
        if data not in self.sensitive_data:
            self.sensitive_data.append(data)

    def _handle_memory_pressure(self) -> None:
        """Handle memory pressure by clearing old data
        Обрабатывает давление памяти, очищая старые данные
        Обробляє тиск пам'яті, очищаючи старі дані"""
        try:
            for data in self.sensitive_data[:]:
                try:
                    if hasattr(data, 'get_age') and data.get_age() > 300:
                        data.clear()
                        if data in self.sensitive_data:
                            self.sensitive_data.remove(data)
                except (AttributeError, RuntimeError, TypeError) as e:
                    logger.debug(f"Memory pressure cleanup error / Ошибка очистки при давлении памяти / Помилка очищення при тиску пам'яті: {e}")
        except (RuntimeError, AttributeError, TypeError) as e:
            logger.debug(f"Memory pressure handler error / Ошибка обработчика давления памяти / Помилка обробника тиску пам'яті: {e}")

    def clear(self) -> None:
        """Clear all registered data / Очистить все зарегистрированные данные / Очистити всі зареєстровані дані"""
        for data in self.sensitive_data:
            try:
                data.clear()
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.debug(f"Data clear error / Ошибка очистки данных / Помилка очищення даних: {e}")
        self.sensitive_data.clear()
        try:
            gc.collect()
        except (RuntimeError, ImportError) as e:
            logger.debug(f"GC collect error / Ошибка сборщика мусора / Помилка збирача сміття: {e}")

    def clear_by_age(self, max_age_seconds: int = 300) -> int:
        """Clear data older than specified age
        Очищает данные старше указанного возраста
        Очищує дані старші за вказаний вік"""
        cleared_count = 0

        for data in self.sensitive_data[:]:
            try:
                if hasattr(data, 'get_age') and data.get_age() > max_age_seconds:
                    data.clear()
                    if data in self.sensitive_data:
                        self.sensitive_data.remove(data)
                    cleared_count += 1
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.debug(f"Age-based clear error / Ошибка возрастной очистки / Помилка вікової очистки: {e}")

        if cleared_count > 0:
            try:
                gc.collect()
            except (RuntimeError, ImportError):
                pass

        return cleared_count

    def get_registered_count(self) -> int:
        """Get number of registered sensitive objects
        Получить количество зарегистрированных чувствительных объектов
        Отримати кількість зареєстрованих чутливих об'єктів"""
        return len(self.sensitive_data)

    def __enter__(self) -> Any:
        """
        Enter the context manager.
        Войти в контекстный менеджер.
        Увійти в контекстний менеджер.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager and clean up.
        Выйти из контекстного менеджера и освободить ресурсы.
        Вийти з контекстного менеджера та звільнити ресурси.
        """
        self.clear()


# ==================== MEMORY PRESSURE MONITORING ====================

_memory_pressure_monitor: Optional[threading.Thread] = None
_memory_pressure_stop = False


def _monitor_memory_pressure(guard: MemoryGuard, interval: int = 60) -> None:
    """Background thread for memory pressure monitoring
    Фоновый поток для мониторинга давления памяти
    Фоновий потік для моніторингу тиску пам'яті"""

    while not _memory_pressure_stop:
        try:
            time.sleep(interval)
            if hasattr(guard, 'clear_by_age'):
                guard.clear_by_age(300)
        except (RuntimeError, OSError, AttributeError, TypeError) as e:
            logger.debug(f"Memory pressure monitor error / Ошибка монитора давления памяти / Помилка монітора тиску пам'яті: {e}")


def start_memory_pressure_monitoring(guard: MemoryGuard, interval: int = 60) -> None:
    """Start background memory pressure monitoring
    Запустить фоновый мониторинг давления памяти
    Запустити фоновий моніторинг тиску пам'яті"""
    global _memory_pressure_monitor, _memory_pressure_stop

    if _memory_pressure_monitor is not None and _memory_pressure_monitor.is_alive():
        return

    _memory_pressure_stop = False
    _memory_pressure_monitor = threading.Thread(
        target=_monitor_memory_pressure,
        args=(guard, interval),
        daemon=True
    )
    try:
        _memory_pressure_monitor.start()
        logger.info(f"Memory pressure monitoring started (interval: {interval}s) / Мониторинг давления памяти запущен (интервал: {interval}с) / Моніторинг тиску пам'яті запущено (інтервал: {interval}с)")
    except (RuntimeError, threading.ThreadError) as e:
        logger.debug(f"Failed to start memory pressure monitor / Ошибка запуска монитора давления памяти / Помилка запуску монітора тиску пам'яті: {e}")


def stop_memory_pressure_monitoring() -> None:
    """Stop background memory pressure monitoring
    Остановить фоновый мониторинг давления памяти
    Зупинити фоновий моніторинг тиску пам'яті"""
    global _memory_pressure_monitor, _memory_pressure_stop

    _memory_pressure_stop = True
    if _memory_pressure_monitor and _memory_pressure_monitor.is_alive():
        try:
            _memory_pressure_monitor.join(timeout=2.0)
        except (RuntimeError, threading.ThreadError) as e:
            logger.debug(f"Memory pressure monitor join error / Ошибка присоединения монитора давления памяти / Помилка приєднання монітора тиску пам'яті: {e}")
    _memory_pressure_monitor = None
    logger.info("Memory pressure monitoring stopped / Мониторинг давления памяти остановлен / Моніторинг тиску пам'яті зупинено")
