"""
Main application window - Cleanup methods
Главное окно приложения - Методы очистки
Головне вікно програми - Методи очищення

This file contains cleanup and shutdown methods: _on_closing, _emergency_*, _clear_*

Этот файл содержит методы очистки и завершения: _on_closing, _emergency_*, _clear_*
Цей файл містить методи очищення та завершення: _on_closing, _emergency_*, _clear_*

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import os
import sys
import time
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

from storage.database import PasswordDB
from utils.logger import get_logger
from utils.helpers import is_windows

logger = get_logger("main_window_cleanup")


class CleanupMethods:
    """Cleanup and shutdown methods for SecurePassPro

    Методы очистки и завершения для SecurePassPro
    Методи очищення та завершення для SecurePassPro
    """

    # Attributes provided by the main SecurePassPro class (via MRO)
    # Declared here to satisfy pylint E1101 in mixin analysis
    if False:  # pragma: no cover  # pylint: disable=using-constant-test
        clipboard_clear: Callable = lambda self: None
        clipboard_append: Callable = lambda self, t: None
        after_cancel: Callable = lambda self, *a: None
        quit: Callable = lambda self: None
        destroy: Callable = lambda self: None
        update: Callable = lambda self: None
        winfo_exists: Callable = lambda self: True
        _stop_rgb: Callable = lambda self: None
        _clipboard_timer: Optional[str] = None
        _pulse_animation_id: Optional[str] = None
        _lock_check_id: Optional[str] = None
        _minimize_check_id: Optional[str] = None
        _suspend_check_id: Optional[str] = None
        settings_window: Optional[tk.Toplevel] = None
        about_window: Optional[tk.Toplevel] = None
        history_window: Optional[tk.Toplevel] = None
        qr_window: Optional[tk.Toplevel] = None
        db_window: Optional[tk.Toplevel] = None

    def _clear_clipboard(self) -> None:
        """
        Clear clipboard with multiple overwrites for security.

        Очистить буфер обмена с многократной перезаписью для безопасности.
        Очистити буфер обміну з багаторазовим перезаписом для безпеки.
        """
        try:
            if not self.winfo_exists():
                return

            import secrets
            overwrite_passes: int = 5

            for i in range(overwrite_passes):
                try:
                    junk: str = secrets.token_hex(512)

                    self.clipboard_clear()
                    self.clipboard_append(junk)
                    self.update()

                    time.sleep(0.01)

                    from core.generator import _clear_string
                    _clear_string(junk)

                except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Clipboard overwrite pass {i + 1} failed / Ошибка прохода перезаписи {i + 1} / Помилка проходу перезапису {i + 1}: {e}")
                    continue

            self.clipboard_clear()
            self.update()

            if is_windows():
                self._clear_clipboard_windows_api()

            logger.debug(f"Clipboard securely cleared with {overwrite_passes} overwrites / Буфер обмена безопасно очищен с {overwrite_passes} перезаписями / Буфер обміну безпечно очищено з {overwrite_passes} перезаписами")

        except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
            logger.debug(f"Clipboard secure clear error / Ошибка безопасной очистки буфера / Помилка безпечного очищення буфера: {e}")
            try:
                self.clipboard_clear()
            except (tk.TclError, OSError, RuntimeError):
                pass
        finally:
            self._clipboard_timer = None

    def _clear_clipboard_windows_api(self) -> None:
        """
        Additional clipboard clearing via Windows API.

        Дополнительная очистка буфера обмена через Windows API.
        Додаткове очищення буфера обміну через Windows API.
        """
        if not is_windows():
            return

        try:
            import ctypes

            user32 = ctypes.windll.user32

            if user32.OpenClipboard(0):
                try:
                    user32.EmptyClipboard()
                    logger.debug("Clipboard cleared via Windows API / Буфер обмена очищен через Windows API / Буфер обміну очищено через Windows API")
                except (AttributeError, OSError) as e:
                    logger.debug(f"Windows API clipboard clear error / Ошибка очистки буфера через Windows API / Помилка очищення буфера через Windows API: {e}")
                finally:
                    try:
                        user32.CloseClipboard()
                    except (AttributeError, OSError):
                        pass
        except (ImportError, AttributeError, OSError, TypeError) as e:
            logger.debug(f"Windows API error / Ошибка Windows API / Помилка Windows API: {e}")

    def _emergency_clipboard_clear(self) -> None:
        """
        Emergency clipboard clear on crash

        Экстренная очистка буфера обмена при сбое
        Екстрене очищення буфера обміну при збої
        """
        try:
            self.clipboard_clear()
            for _ in range(3):
                self.clipboard_append(" " * 64)
                self.update()
                self.clipboard_clear()
                self.update()
        except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
            logger.debug(f"Emergency clipboard clear error / Ошибка экстренной очистки буфера / Помилка екстреного очищення буфера: {e}")

    def _emergency_cleanup(self) -> None:
        """
        Emergency cleanup on crash

        Экстренная очистка при сбое
        Екстрене очищення при збої
        """
        self._stop_rgb()
        try:
            PasswordDB.close_all_connections()
        except (ImportError, AttributeError, OSError, RuntimeError) as e:
            logger.debug(f"Emergency cleanup error / Ошибка экстренной очистки / Помилка екстреного очищення: {e}")

    def _on_closing(self) -> None:
        """
        Close application with resource cleanup

        Закрывает приложение с очисткой ресурсов
        Закриває додаток з очищенням ресурсів
        """
        self._stop_rgb()
        self._emergency_clipboard_clear()

        timers: List[Optional[str]] = [
            self._pulse_animation_id,
            self._clipboard_timer,
            self._lock_check_id,
            self._suspend_check_id,
            self._minimize_check_id
        ]
        for timer in timers:
            if timer:
                try:
                    self.after_cancel(timer)
                except (tk.TclError, ValueError, RuntimeError) as e:
                    logger.debug(f"Cancel timer error / Ошибка отмены таймера / Помилка скасування таймера: {e}")

        try:
            PasswordDB.close_all_connections()
        except (ImportError, AttributeError, OSError, RuntimeError) as e:
            logger.debug(f"DB close error / Ошибка закрытия БД / Помилка закриття БД: {e}")

        windows: List[Tuple[str, Optional[tk.Toplevel]]] = [
            ("settings_window", self.settings_window),
            ("about_window", self.about_window),
            ("history_window", self.history_window),
            ("qr_window", self.qr_window),
            ("db_window", self.db_window),
        ]
        for win_attr, win in windows:
            if win is not None:
                try:
                    win.destroy()
                except tk.TclError as e:
                    logger.debug(f"Window destroy error for {win_attr} / Ошибка уничтожения окна для {win_attr} / Помилка знищення вікна для {win_attr}: {e}")

        try:
            self.quit()
            self.destroy()
        except (tk.TclError, RuntimeError) as e:
            logger.debug(f"Quit/destroy error / Ошибка выхода/уничтожения / Помилка виходу/знищення: {e}")
        sys.exit(0)

    # ── Auto-backup ───────────────────────────────────────────────────────────

    def _run_auto_backup(self) -> None:
        """Silently backup the database file on startup; keep last 7 copies."""
        try:
            from storage.database import PasswordDB
            from utils.auto_backup import run_backup
            db_path: Optional[str] = getattr(PasswordDB, "_db_path", None)
            if not db_path:
                # Discover db path via the project's own database_health helper
                try:
                    from storage.database_health import get_db_path as _get_db_path
                    db_path = _get_db_path()
                except (ImportError, OSError, AttributeError):
                    pass
            if db_path and os.path.exists(str(db_path)):
                keep: int = 7
                try:
                    from core.app_settings import AppSettings
                    keep = int(AppSettings.instance().get("backup_keep", 7))
                except (ImportError, OSError, ValueError, TypeError, AttributeError):
                    keep = 7
                result: Optional[str] = run_backup(str(db_path), keep=keep)
                if result:
                    logger.info(f"Auto-backup: {result}")
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError) as e:
            logger.debug(f"Auto-backup skipped: {e}")


    # ── Global hotkey ─────────────────────────────────────────────────────────

    def _register_global_hotkey(self) -> None:
        """Register Ctrl+Alt+P global hotkey for quick-search popup."""
        try:
            from utils.hotkey_manager import register_quick_search, show_quick_search_popup
            lang: str = getattr(self, "current_lang", "RU")

            def _on_hotkey() -> None:
                # Must run on Tk main thread
                try:
                    if self.winfo_exists():
                        self.after(0, lambda: show_quick_search_popup(self, lang))
                except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError):
                    pass

            register_quick_search(_on_hotkey)
        except (ImportError, Exception) as e:
            logger.debug(f"Global hotkey registration skipped: {e}")


__all__: List[str] = [
    'CleanupMethods',
]
