from __future__ import annotations
# utils/radius_manager.py
"""
Radius manager module for Secure Pass Pro.
Модуль Radius manager для Secure Pass Pro.
Модуль Radius manager для Secure Pass Pro.
"""
"""
Radius manager module for Secure Pass Pro.
Модуль Radius manager для Secure Pass Pro.
Модуль Radius manager для Secure Pass Pro.
"""
"""
Global radius manager for all buttons

Глобальный менеджер радиуса для всех кнопок
Глобальний менеджер радіусу для всіх кнопок

Manages corner radius for all UI elements across the application.
Управляет скруглением углов для всех элементов интерфейса приложения.
Керує заокругленням кутів для всіх елементів інтерфейсу програми.
"""

import customtkinter as ctk
import tkinter as tk
from typing import List, Optional, Any, Tuple
import atexit
import weakref

# Default radius value / Значение радиуса по умолчанию / Значення радіусу за замовчуванням
DEFAULT_RADIUS = 25

# Minimum and maximum allowed radius / Минимальный и максимальный допустимый радиус / Мінімальний та максимальний допустимий радіус
MIN_RADIUS = 0
MAX_RADIUS = 50

_current_radius = DEFAULT_RADIUS
# Используем weakref для автоматической очистки уничтоженных окон
# Using weakref for automatic cleanup of destroyed windows
# Використовуємо weakref для автоматичного очищення знищених вікон
_all_windows: List[weakref.ref] = []

# Флаг для отслеживания регистрации очистки
# Flag to track cleanup registration
# Прапорець для відстеження реєстрації очищення
_cleanup_registered = False


def _cleanup_dead_windows() -> None:
    """
    Remove references to destroyed windows.

    Удалить ссылки на уничтоженные окна.
    Видалити посилання на знищені вікна.
    """
    global _all_windows
    _all_windows = [ref for ref in _all_windows if ref() is not None]


def _register_cleanup() -> None:
    """
    Register cleanup function at exit.

    Зарегистрировать функцию очистки при завершении.
    Зареєструвати функцію очищення при завершенні.
    """
    global _cleanup_registered
    if not _cleanup_registered:
        atexit.register(clear_registered_windows)
        _cleanup_registered = True


def set_global_radius(radius: int) -> None:
    """
    Set global radius and update all buttons.

    Установить глобальный радиус и обновить все кнопки.
    Встановити глобальний радіус та оновити всі кнопки.

    Args:
        radius: New radius value in pixels / Новое значение радиуса в пикселях / Нове значення радіусу в пікселях
    """
    global _current_radius

    # Validate radius range / Проверяем диапазон радиуса / Перевіряємо діапазон радіусу
    if radius < MIN_RADIUS:
        radius = MIN_RADIUS
    if radius > MAX_RADIUS:
        radius = MAX_RADIUS

    _current_radius = radius

    # Clean up dead windows before update / Очищаем мёртвые окна перед обновлением / Очищуємо мертві вікна перед оновленням
    _cleanup_dead_windows()

    # Update all registered windows / Обновляем все зарегистрированные окна / Оновлюємо всі зареєстровані вікна
    for ref in _all_windows[:]:  # Copy list to avoid modification during iteration / Копируем список для избежания изменений / Копіюємо список для уникнення змін
        window = ref()
        if window and window.winfo_exists():
            try:
                _update_window_radius(window, radius)
            except (tk.TclError, AttributeError, RuntimeError, KeyError, TypeError):
                # Silently ignore errors for windows that are being destroyed
                # Игнорируем ошибки для окон, которые уничтожаются
                # Ігноруємо помилки для вікон, які знищуються
                pass


def get_global_radius() -> int:
    """
    Get current global radius value.

    Получить текущее глобальное значение радиуса.
    Отримати поточне глобальне значення радіусу.

    Returns:
        Current radius in pixels / Текущий радиус в пикселях / Поточний радіус у пікселях
    """
    return _current_radius


def register_window(window: Any) -> None:
    """
    Register a window for radius updates.

    Зарегистрировать окно для обновления радиуса.
    Зареєструвати вікно для оновлення радіусу.

    Args:
        window: Window to register / Окно для регистрации / Вікно для реєстрації
    """
    if window is None:
        return

    _register_cleanup()
    _cleanup_dead_windows()

    # Check if already registered / Проверяем, не зарегистрировано ли уже / Перевіряємо, чи не зареєстровано вже
    for ref in _all_windows:
        if ref() is window:
            return

    _all_windows.append(weakref.ref(window))


def unregister_window(window: Any) -> None:
    """
    Unregister a window.

    Отменить регистрацию окна.
    Скасувати реєстрацію вікна.

    Args:
        window: Window to unregister / Окно для отмены регистрации / Вікно для скасування реєстрації
    """
    if window is None:
        return

    _cleanup_dead_windows()

    for i, ref in enumerate(_all_windows):
        if ref() is window:
            try:
                _all_windows.pop(i)
                break
            except (ValueError, IndexError, AttributeError):
                # Window wasn't in list or index error, ignore
                # Окна не было в списке или ошибка индекса, игнорируем
                # Вікна не було в списку або помилка індексу, ігноруємо
                pass


def _update_window_radius(widget: Any, radius: int) -> None:
    """
    Recursively update radius of all buttons in widget.

    Рекурсивно обновить радиус всех кнопок в виджете.
    Рекурсивно оновити радіус всіх кнопок у віджеті.

    Args:
        widget: Widget to process / Виджет для обработки / Віджет для обробки
        radius: New radius value / Новое значение радиуса / Нове значення радіусу
    """
    try:
        # Check if widget exists / Проверяем существование виджета / Перевіряємо існування віджета
        if not widget or not widget.winfo_exists():
            return

        # Update buttons / Обновляем кнопки / Оновлюємо кнопки
        if isinstance(widget, ctk.CTkButton):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Update entry fields / Обновляем поля ввода / Оновлюємо поля введення
        elif isinstance(widget, ctk.CTkEntry):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Update text fields / Обновляем текстовые поля / Оновлюємо текстові поля
        elif isinstance(widget, ctk.CTkTextbox):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Update scrollable frames / Обновляем фреймы со скроллом / Оновлюємо фрейми зі скролом
        elif isinstance(widget, ctk.CTkScrollableFrame):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Update option menus / Обновляем выпадающие меню / Оновлюємо випадаючі меню
        elif isinstance(widget, ctk.CTkOptionMenu):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Update frames / Обновляем фреймы / Оновлюємо фрейми
        elif isinstance(widget, ctk.CTkFrame):
            try:
                widget.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, TypeError, KeyError):
                pass

        # Recursively traverse children / Рекурсивно обходим всех детей / Рекурсивно обходимо всіх дітей
        try:
            for child in widget.winfo_children():
                _update_window_radius(child, radius)
        except (tk.TclError, AttributeError, RuntimeError, KeyError, TypeError):
            # Error getting children, skip this branch
            # Ошибка получения дочерних элементов, пропускаем эту ветку
            # Помилка отримання дочірніх елементів, пропускаємо цю гілку
            pass

    except (tk.TclError, AttributeError, RuntimeError, TypeError, KeyError, IndexError):
        # Silent fail for any widget that doesn't support radius
        # Игнорируем ошибки для виджетов, которые не поддерживают радиус
        # Ігноруємо помилки для віджетів, які не підтримують радіус
        pass


def update_all_buttons_radius(radius: int) -> None:
    """
    Update radius of all buttons in all windows.

    Обновить радиус всех кнопок во всех окнах.
    Оновити радіус всіх кнопок у всіх вікнах.

    Args:
        radius: New radius value / Новое значение радиуса / Нове значення радіусу
    """
    set_global_radius(radius)


def get_registered_windows_count() -> int:
    """
    Get number of registered windows.

    Получить количество зарегистрированных окон.
    Отримати кількість зареєстрованих вікон.

    Returns:
        Number of registered windows / Количество зарегистрированных окон / Кількість зареєстрованих вікон
    """
    _cleanup_dead_windows()
    return len(_all_windows)


def clear_registered_windows() -> None:
    """
    Clear all registered windows (for testing and cleanup).

    Очистить все зарегистрированные окна (для тестирования и очистки).
    Очистити всі зареєстровані вікна (для тестування та очищення).
    """
    # Clear references properly / Правильно очищаем ссылки / Правильно очищуємо посилання
    for ref in _all_windows:
        try:
            window = ref()
            if window:
                # Try to unregister any children recursively / Пытаемся отменить регистрацию всех детей / Намагаємося скасувати реєстрацію всіх дітей
                pass
        except (tk.TclError, AttributeError, RuntimeError):
            pass
    _all_windows.clear()


def get_radius_limits() -> Tuple[int, int]:
    """
    Get minimum and maximum allowed radius values.

    Получить минимальное и максимальное допустимое значение радиуса.
    Отримати мінімальне та максимальне допустиме значення радіусу.

    Returns:
        (min_radius, max_radius) / (мин_радиус, макс_радиус) / (мін_радіус, макс_радіус)
    """
    return (MIN_RADIUS, MAX_RADIUS)


def is_radius_valid(radius: int) -> bool:
    """
    Check if radius value is within allowed limits.

    Проверить, находится ли значение радиуса в допустимых пределах.
    Перевірити, чи знаходиться значення радіусу в допустимих межах.

    Args:
        radius: Radius value to check / Значение радиуса для проверки / Значення радіусу для перевірки

    Returns:
        True if radius is valid, False otherwise / True, если радиус допустим, иначе False / True, якщо радіус допустимий, інакше False
    """
    return MIN_RADIUS <= radius <= MAX_RADIUS


def clamp_radius(radius: int) -> int:
    """
    Clamp radius value to allowed limits.

    Ограничить значение радиуса допустимыми пределами.
    Обмежити значення радіусу допустимими межами.

    Args:
        radius: Radius value to clamp / Значение радиуса для ограничения / Значення радіусу для обмеження

    Returns:
        Clamped radius value / Ограниченное значение радиуса / Обмежене значення радіусу
    """
    if radius < MIN_RADIUS:
        return MIN_RADIUS
    if radius > MAX_RADIUS:
        return MAX_RADIUS
    return radius


# Export public functions / Экспорт публичных функций / Експорт публічних функцій
__all__ = [
    'set_global_radius',
    'get_global_radius',
    'register_window',
    'unregister_window',
    'update_all_buttons_radius',
    'get_registered_windows_count',
    'clear_registered_windows',
    'get_radius_limits',
    'is_radius_valid',
    'clamp_radius',
    'DEFAULT_RADIUS',
    'MIN_RADIUS',
    'MAX_RADIUS',
]