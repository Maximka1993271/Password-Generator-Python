"""
Auto-lock mixin for SecurePassPro
FIXED: Disabled problematic Windows window procedure hooks to prevent access violation errors
FIXED: Improved detection of desktop lock, hibernation/sleep, window minimize
FIXED: Removed _check_suspend_windows that caused ctypes.ArgumentError

English:
This module provides auto-lock functionality for SecurePassPro including:
- Lock on inactivity (idle detection)
- Lock on system suspend/hibernation (macOS/Linux only)
- Lock on window minimize
- Activity tracking

Русский:
Этот модуль обеспечивает автоматическую блокировку для SecurePassPro:
- Блокировка при бездействии
- Блокировка при гибернации/сне системы (только macOS/Linux)
- Блокировка при сворачивании окна
- Отслеживание активности

Українська:
Цей модуль забезпечує автоматичне блокування для SecurePassPro:
- Блокування при бездіяльності
- Блокування при гібернації/сні системи (тільки macOS/Linux)
- Блокування при згортанні вікна
- Відстеження активності
"""
from __future__ import annotations

import time
import tkinter as tk
import platform
import threading

from security.master import MasterPassword
from utils.logger import get_logger
from gui.mixins.dialogs_helpers import _get_colors_for_theme as _get_colors_for_theme_func
from utils.subprocess_utils import silent_run as _silent_run

logger = get_logger("auto_lock")

# Platform detection / Определение платформы / Визначення платформи
_is_windows = platform.system() == "Windows"
_is_macos = platform.system() == "Darwin"
_is_linux = platform.system() == "Linux"


class AutoLockMixin:
    """
    Mixin class for auto-lock functionality on inactivity and minimize

    Класс-миксин для автоматической блокировки при бездействии и сворачивании
    Клас-міксин для автоматичного блокування при бездіяльності та згортанні
    """

    def _reset_activity_timer(self, event=None) -> None:
        """
        Reset activity timer

        Сбрасывает таймер активности
        Скидає таймер активності
        """
        if not self.auto_lock_enabled.get():
            return
        self._last_activity_time = time.time()

    def _start_lock_checker(self) -> None:
        """
        Start all lock detection systems

        Запускает все системы обнаружения блокировки
        Запускає всі системи виявлення блокування
        """
        self._check_lock()
        self._start_suspend_detection()
        self._start_minimize_detection()
        self._start_idle_detection()

    def _bind_focus_events(self) -> None:
        """
        Bind focus events to reset activity timer

        Привязывает события фокуса для сброса таймера активности
        Прив'язує події фокусу для скидання таймера активності
        """
        try:
            self.bind("<FocusIn>", self._reset_activity_timer)
            self.bind_all("<FocusIn>", self._reset_activity_timer)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Focus event binding error: {e}")

    # ==================== LOCK ON INACTIVITY ====================
    # БЛОКИРОВКА ПРИ БЕЗДЕЙСТВИИ
    # БЛОКУВАННЯ ПРИ БЕЗДІЯЛЬНОСТІ

    def _start_idle_detection(self) -> None:
        """
        Start idle detection via API (Windows only)

        Запускает обнаружение неактивности через API (Windows)
        Запускає виявлення неактивності через API (Windows)
        """
        if not _is_windows:
            return

        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            def get_idle_time() -> int:
                """Get idle time in milliseconds (Windows)"""
                try:
                    class LASTINPUTINFO(ctypes.Structure):
                        _fields_ = [
                            ("cbSize", wintypes.UINT),
                            ("dwTime", wintypes.DWORD)
                        ]

                    lii = LASTINPUTINFO()
                    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)

                    if user32.GetLastInputInfo(ctypes.byref(lii)):
                        ticks = user32.GetTickCount()
                        return (ticks - lii.dwTime) & 0xFFFFFFFF
                    return 0
                except (AttributeError, OSError, TypeError, ValueError):
                    return 0

            self._get_idle_time = get_idle_time
            logger.debug("Idle detection started / Обнаружение бездействия запущено / Виявлення бездіяльності запущено")

        except (ImportError, AttributeError, OSError, TypeError, ValueError) as e:
            logger.debug(f"Idle detection not available: {e}")
            self._get_idle_time = lambda: 0

    def _check_lock(self) -> None:
        """
        Check inactivity and lock if needed

        Проверяет неактивность и блокирует если нужно
        Перевіряє неактивність та блокує якщо потрібно
        """
        if not self.auto_lock_enabled.get():
            self._lock_check_id = self.after(1000, self._check_lock)
            return

        if not MasterPassword.is_set():
            self._lock_check_id = self.after(1000, self._check_lock)
            return

        # Use system API to get idle time if available
        if hasattr(self, '_get_idle_time') and callable(self._get_idle_time):
            try:
                idle_ms = self._get_idle_time()
                idle_seconds = idle_ms / 1000
                if idle_seconds >= self.auto_lock_timeout * 60:
                    self._lock_program()
                    self._lock_check_id = self.after(1000, self._check_lock)
                    return
            except (AttributeError, TypeError, RuntimeError, ValueError) as e:
                logger.debug(f"Idle time detection error: {e}")

        # Fallback: use our timer
        idle_time = time.time() - self._last_activity_time
        if idle_time >= self.auto_lock_timeout * 60:
            self._lock_program()

        self._lock_check_id = self.after(1000, self._check_lock)

    # ==================== LOCK ON SUSPEND (HIBERNATION/SLEEP) ====================
    # БЛОКИРОВКА ПРИ ГИБЕРНАЦИИ/СНЕ
    # БЛОКУВАННЯ ПРИ ГІБЕРНАЦІЇ/СНІ

    def _start_suspend_detection(self) -> None:
        """
        Start detection for system suspend/resume
        Windows detection is disabled to prevent access violation errors and ctypes overflow
        
        Запускает обнаружение приостановки/возобновления системы
        Обнаружение Windows отключено для предотвращения ошибок доступа и ctypes переполнения
        
        Запускає виявлення призупинення/відновлення системи
        Виявлення Windows вимкнено для запобігання помилок доступу та ctypes переповнення
        """
        if _is_windows:
            # Windows suspend detection is disabled due to:
            # 1. Access violation issues
            # 2. ctypes.ArgumentError: int too long to convert
            # Обнаружение приостановки Windows отключено из-за:
            # 1. Проблем с доступом
            # 2. ctypes.ArgumentError: int too long to convert
            # Виявлення призупинення Windows вимкнено через:
            # 1. Проблеми з доступом
            # 2. ctypes.ArgumentError: int too long to convert
            logger.debug("Windows suspend detection disabled to prevent errors")
            pass
        elif _is_macos:
            self._check_suspend_macos()
        elif _is_linux:
            self._check_suspend_linux()

    def _check_suspend_macos(self) -> None:
        """
        Detect macOS suspend/resume using system events

        Обнаружение приостановки/возобновления macOS через системные события
        Виявлення призупинення/відновлення macOS через системні події
        """
        try:
            import subprocess

            def monitor() -> None:
                last_time = time.time()
                while True:
                    try:
                        result = _silent_run(
                            ['sysctl', '-n', 'kern.boottime'],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            import re
                            match = re.search(r'sec = (\d+)', result.stdout)
                            if match:
                                uptime = time.time() - float(match.group(1))
                                if uptime < last_time - 5:
                                    logger.debug("macOS suspend detected, locking program")
                                    try:
                                        self.after(0, self._lock_program)
                                    except (tk.TclError, RuntimeError):
                                        pass
                                last_time = uptime
                    except (subprocess.SubprocessError, TimeoutError, ValueError, TypeError, OSError):
                        pass
                    time.sleep(10)

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
        except (ImportError, OSError, RuntimeError) as e:
            logger.debug(f"macOS suspend detection failed: {e}")

    def _check_suspend_linux(self) -> None:
        """
        Detect Linux suspend/resume using log monitoring

        Обнаружение приостановки/возобновления Linux через мониторинг логов
        Виявлення призупинення/відновлення Linux через моніторинг логів
        """
        try:
            import subprocess

            def monitor() -> None:
                last_line = None
                while True:
                    try:
                        result = _silent_run(
                            ['journalctl', '--since=now', '-n', '5', '-o', 'cat'],
                            capture_output=True, text=True, timeout=5
                        )
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if 'Resuming' in line or 'resumed' in line or 'wakeup' in line.lower():
                                    if line != last_line:
                                        logger.debug("Linux resume detected, checking lock")
                                        try:
                                            if MasterPassword.is_set() and self.auto_lock_enabled.get():
                                                self.after(0, self._lock_program)
                                        except (AttributeError, RuntimeError, tk.TclError):
                                            pass
                                        last_line = line
                    except (subprocess.SubprocessError, TimeoutError, ValueError, TypeError, OSError):
                        pass
                    time.sleep(10)

            thread = threading.Thread(target=monitor, daemon=True)
            thread.start()
        except (ImportError, OSError, RuntimeError) as e:
            logger.debug(f"Linux suspend detection failed: {e}")

    # ==================== LOCK ON MINIMIZE (WINDOW MINIMIZE) ====================
    # БЛОКИРОВКА ПРИ СВОРАЧИВАНИИ ОКНА
    # БЛОКУВАННЯ ПРИ ЗГОРТАННІ ВІКНА

    def _start_minimize_detection(self) -> None:
        """
        Start detection for window minimize/restore

        Запускает обнаружение сворачивания/восстановления окна
        Запускає виявлення згортання/відновлення вікна
        """
        self._check_minimize()

    def _check_minimize(self) -> None:
        """
        Check if window was minimized

        Проверяет, было ли окно свернуто
        Перевіряє, чи було вікно згорнуто
        """
        try:
            if not self.winfo_exists():
                return

            is_minimized = False

            if _is_windows:
                try:
                    import ctypes
                    is_minimized = ctypes.windll.user32.IsIconic(self.winfo_id())
                except (ImportError, AttributeError, OSError, TypeError, ValueError):
                    pass

            if self.auto_lock_enabled.get() and MasterPassword.is_set():
                if is_minimized:
                    if not getattr(self, '_was_minimized', False):
                        logger.debug("Window minimized, locking program")
                        try:
                            self.after(0, self._lock_program)
                        except (tk.TclError, RuntimeError):
                            pass
                        self._was_minimized = True
                else:
                    self._was_minimized = False

        except (tk.TclError, RuntimeError, AttributeError) as e:
            logger.debug(f"Minimize check error: {e}")

        if hasattr(self, '_minimize_check_id') and self._minimize_check_id:
            try:
                self.after_cancel(self._minimize_check_id)
            except (tk.TclError, ValueError, RuntimeError):
                pass
        self._minimize_check_id = self.after(1000, self._check_minimize)

    # ==================== HELPER METHODS ====================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ДОПОМІЖНІ МЕТОДИ

    def _close_all_child_windows(self) -> None:
        """
        Close all child windows before locking

        Закрывает все дочерние окна перед блокировкой
        Закриває всі дочірні вікна перед блокуванням
        """
        windows = [
            ('db_window', '_close_db_window'),
            ('settings_window', '_close_settings'),
            ('history_window', '_close_history'),
            ('qr_window', '_close_qr'),
            ('about_window', '_close_about'),
            ('_name_window', '_close_window'),
        ]

        for win_attr, close_method in windows:
            win = getattr(self, win_attr, None)
            if win and win.winfo_exists():
                try:
                    if hasattr(self, close_method):
                        getattr(self, close_method)()
                    else:
                        win.destroy()
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Window close error for {win_attr}: {e}")
                setattr(self, win_attr, None)

    def _lock_program(self) -> None:
        """
        Lock the program

        Блокирует программу
        Блокує програму
        """
        if not MasterPassword.is_set():
            return

        try:
            if not self.winfo_viewable():
                return
        except (tk.TclError, AttributeError, RuntimeError):
            return

        self._close_all_child_windows()

        rgb_was_enabled = False
        try:
            rgb_was_enabled = self.rgb_enabled.get()
            if rgb_was_enabled:
                self._stop_rgb()
        except (AttributeError, tk.TclError, RuntimeError):
            pass

        try:
            self.withdraw()
        except tk.TclError as e:
            logger.error(f"Cannot withdraw window: {e}")
            return

        try:
            unlocked = self._show_lock_screen()
        except (tk.TclError, RuntimeError, AttributeError) as e:
            logger.error(f"Lock screen error: {e}")
            unlocked = False

        if unlocked:
            try:
                self.deiconify()
                self.lift()
                self.focus_force()
            except tk.TclError as e:
                logger.error(f"Window restore error: {e}")
                return

            if rgb_was_enabled:
                try:
                    self._start_rgb()
                except (AttributeError, tk.TclError, RuntimeError):
                    pass

            self._last_activity_time = time.time()
            self._was_minimized = False
        else:
            try:
                self._on_closing()
            except (AttributeError, tk.TclError, RuntimeError) as e:
                logger.error(f"Close on lock error: {e}")
                import sys
                sys.exit(0)

    def _get_actual_theme(self) -> str:
        """
        Return actual theme for lock screen

        Возвращает актуальную тему для lock screen
        Повертає актуальну тему для lock screen
        """
        if hasattr(self, 'current_theme'):
            if self.current_theme == "Light":
                return "light"
            elif self.current_theme == "Dark":
                return "dark"
        return "dark"

    def _get_colors_for_theme(self, theme: str) -> dict:
        """
        Return colors for theme

        Возвращает цвета для темы
        Повертає кольори для теми
        """
        return _get_colors_for_theme_func(theme)
        return {
            "bg": "#1d1e1e",
            "fg": "#FFFFFF",
            "entry_bg": "#2b2b2b",
            "label_text": "#FFFFFF",
            "button_fg": "#1f538d"
        }

    def _center_window_relative_to_parent(self, window, width: int, height: int) -> None:
        """
        Center window relative to parent

        Центрирует окно относительно родителя
        Центрує вікно відносно батька
        """
        try:
            window.update_idletasks()
            parent_x = self.winfo_x()
            parent_y = self.winfo_y()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            if x < 0:
                x = 10
            if y < 30:
                y = 30
            if x + width > screen_width:
                x = screen_width - width - 10
            if y + height > screen_height:
                y = screen_height - height - 10

            window.geometry(f"{width}x{height}+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError, ValueError) as e:
            logger.debug(f"Window centering error: {e}")
