"""
Master password authentication - 2FA methods
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import sys
from typing import Tuple, Optional

from security.master_auth_core import MasterPassword
from security.master_auth_verify import verify
from security.master_auth_history import _load_password_history
from security.master_auth_trusted import _load_trusted_devices
from security.master_auth_recovery import _load_recovery_codes
from security.master_auth_session import _load_sessions
from security.master_auth_lockout import _load_lockout_state
from security.master_auth_audit import _load_audit_log

from utils.logger import get_logger
from core.app_settings import AppSettings  # centralised settings

logger = get_logger("master_auth")


def set_config(cls, config) -> None:
    """Set configuration object reference
    Установить ссылку на объект конфигурации
    Встановити посилання на об'єкт конфігурації"""
    cls._cached_config = config
    _load_password_history(cls)
    _load_trusted_devices(cls)
    _load_recovery_codes(cls)
    _load_sessions(cls)


def is_2fa_required(cls) -> bool:
    """Check if 2FA is required
    Проверить, требуется ли 2FA
    Перевірити, чи потрібна 2FA"""
    if cls._cached_config is None:
        return False
    try:
        return cls._cached_config.is_2fa_enabled()
    except AttributeError:
        return False


def set_skip_2fa_once(cls, skip: bool) -> None:
    """Set flag to skip 2FA for next authentication
    Установить флаг пропуска 2FA для следующей аутентификации
    Встановити прапорець пропуску 2FA для наступної аутентифікації"""
    cls._skip_2fa_once = skip


def should_skip_2fa(cls) -> bool:
    """Check if 2FA should be skipped for this authentication
    Проверить, следует ли пропустить 2FA для этой аутентификации
    Перевірити, чи слід пропустити 2FA для цієї аутентифікації"""
    if cls._skip_2fa_once:
        cls._skip_2fa_once = False
        return True
    return False


def verify_with_2fa(cls, password: str, source: str = "startup") -> Tuple[bool, Optional[str]]:
    """Verify master password with 2FA if enabled.
    Проверить мастер-пароль с 2FA, если включена.
    Перевірити майстер-пароль з 2FA, якщо ввімкнено."""
    if not verify(cls, password, source=source):
        return False, "master_password_incorrect"

    if not cls.is_2fa_required() or cls.should_skip_2fa():
        return True, None

    try:
        from security.totp import TOTP, get_totp_manager

        secret = cls._cached_config.get_2fa_secret()
        if not secret:
            logger.error("2FA enabled but no secret found / 2FA включена, но секрет не найден / 2FA увімкнено, але секрет не знайдено")
            cls._log_audit_event("2fa_verification_failed", {"reason": "no_secret", "source": source})
            return False, "2fa_missing_secret"

        totp = TOTP(secret)

        from gui.dialogs import CTkMessageBox
        from localization.lang import LANGUAGES
        import customtkinter as ctk

        lang = cls._cached_config.get("LANG", "RU")
        L = LANGUAGES.get(lang, LANGUAGES["RU"])

        from tkinter import simpledialog
        root = ctk.CTk()
        root.withdraw()
        code = simpledialog.askstring(
            L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
            L.get("2fa_enter_code", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:"),
            parent=root
        )
        root.destroy()

        if code is None:
            cls._log_audit_event("2fa_verification_failed", {"reason": "cancelled", "source": source})
            return False, "2fa_cancelled"

        code_clean = ''.join(filter(str.isdigit, str(code)))

        if totp.verify(code_clean)[0]:
            cls._log_audit_event("2fa_verification_success", {"source": source})
            return True, None

        manager = get_totp_manager()
        if manager.verify_backup_code(code_clean):
            cls._log_audit_event("2fa_backup_used", {"source": source})
            if cls._cached_config:
                cls._cached_config.set_2fa_backup_hashes(manager.get_backup_codes_hashes())
                cls._cached_config.save()
            return True, None

        cls._log_audit_event("2fa_verification_failed", {"reason": "invalid_code", "source": source})
        return False, "2fa_invalid_code"

    except ImportError as e:
        logger.error(f"Failed to import 2FA modules / Ошибка импорта модулей 2FA / Помилка імпорту модулів 2FA: {e}")
        return False, "2fa_module_error"
    except (ValueError, TypeError, AttributeError, RuntimeError) as e:
        logger.error(f"2FA verification error / Ошибка верификации 2FA / Помилка верифікації 2FA: {e}")
        return False, "2fa_error"


def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
    """Show master password prompt on startup.
    Показать запрос мастер-пароля при запуске.
    Показати запит майстер-пароля при запуску."""
    _load_lockout_state(cls)
    _load_audit_log(cls)
    _load_password_history(cls)
    _load_trusted_devices(cls)
    _load_recovery_codes(cls)
    _load_sessions(cls)

    if not cls.is_set():
        return True

    try:
        import customtkinter as ctk
        import tkinter as tk
        from localization.lang import LANGUAGES
        from security.encryption import set_key_from_master
        from utils.helpers import center_screen
    except ImportError as e:
        logger.error(f"Failed to import GUI modules / Ошибка импорта GUI модулей / Помилка імпорту GUI модулів: {e}")
        return True

    L = LANGUAGES.get(lang, LANGUAGES.get("RU", {}))

    if theme == "light":
        bg_color = "#F3F3F3"
        fg_color = "#000000"
        entry_bg = "#FFFFFF"
        btn_fg = "#2d6a4f"
        btn_hover = "#40916c"
    else:
        bg_color = "#1d1e1e"
        fg_color = "#FFFFFF"
        entry_bg = "#2b2b2b"
        btn_fg = "#2d6a4f"
        btn_hover = "#40916c"

    root = ctk.CTk()
    root.title(L.get("master_title", "Master password / Мастер-пароль / Майстер-пароль"))
    root.resizable(False, False)
    root.configure(fg_color=bg_color)
    center_screen(root, 380, 280)

    result = {"ok": False}
    max_attempts = cls.get_max_attempts()
    is_closing = False

    main_frame = ctk.CTkFrame(root, fg_color="transparent")
    main_frame.pack(expand=True, fill="both", padx=25, pady=20)

    ctk.CTkLabel(
        main_frame,
        text="",
        font=("Segoe UI", 32),
        text_color="#4EC9B0"
    ).pack(pady=(0, 8))

    ctk.CTkLabel(
        main_frame,
        text=L.get("master_prompt", "Enter master password to access the program: / Введите мастер-пароль для доступа к программе: / Введіть майстер-пароль для доступу до програми:"),
        font=("Segoe UI", 13),
        text_color=fg_color,
    ).pack(pady=(0, 12))

    entry = ctk.CTkEntry(
        main_frame,
        width=280,
        height=38,
        show="*",
        fg_color=entry_bg,
        text_color=fg_color,
        corner_radius=12,
    )
    entry.pack(pady=(0, 12))
    entry.focus_set()

    status = ctk.CTkLabel(
        main_frame,
        text="",
        font=("Segoe UI", 11),
        text_color="#E24B4A",
        wraplength=300
    )
    status.pack(pady=(0, 8))

    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack(pady=(10, 0))

    def update_status() -> None:
        """
        Update status.
        Обновить status.
        Оновити status.
        """
        if is_closing:
            return
        try:
            info = cls.get_lockout_info()
            if info['is_locked']:
                status.configure(text=f"{L.get('lock_wait', 'Please wait / Подождите / Зачекайте')} {info['lockout_seconds']} {L.get('seconds_short', 'sec / сек / сек')}...")
                entry.configure(state="disabled")
                submit_btn.configure(state="disabled")
                cancel_btn.configure(state="disabled")
                root.after(1000, update_status)
            elif info['is_permanently_locked']:
                status.configure(text=L.get("master_blocked", "Too many attempts. Program closed. / Слишком много попыток. Программа закрыта. / Занадто багато спроб. Програму закрито."))
                entry.configure(state="disabled")
                submit_btn.configure(state="disabled")
                cancel_btn.configure(state="disabled")
                root.after(2000, _safe_exit)
            else:
                entry.configure(state="normal")
                submit_btn.configure(state="normal")
                cancel_btn.configure(state="normal")
                if info['attempts'] > 0:
                    status.configure(text=L["master_wrong"].format(info['attempts'], max_attempts))
                else:
                    status.configure(text="")
        except (KeyError, AttributeError, tk.TclError, TypeError) as e:
            logger.debug(f"Update status error / Ошибка обновления статуса / Помилка оновлення статусу: {e}")

    def _safe_exit() -> None:
        """
        Handle safe exit.
        Обработать safe exit.
        Обробити safe exit.
        """
        nonlocal is_closing
        is_closing = True
        try:
            root.destroy()
        except tk.TclError:
            pass
        sys.exit(0)

    def finish_ok() -> None:
        """
        Handle finish ok.
        Обработать finish ok.
        Обробити finish ok.
        """
        if is_closing:
            return
        result["ok"] = True
        try:
            root.destroy()
        except tk.TclError:
            pass

    def cancel() -> None:
        """
        Handle cancel.
        Обработать cancel.
        Обробити cancel.
        """
        nonlocal is_closing
        is_closing = True
        result["ok"] = False
        try:
            root.destroy()
        except tk.TclError:
            pass

    def submit() -> None:
        """
        Handle submit.
        Обработать submit.
        Обробити submit.
        """
        if is_closing:
            return

        if cls.get_remaining_lockout_time() > 0:
            update_status()
            return

        pwd = entry.get()
        if pwd:
            success, error_code = cls.verify_with_2fa(pwd, source="startup")

            if success:
                try:
                    set_key_from_master(pwd)
                except (ValueError, TypeError, RuntimeError) as e:
                    logger.error(f"Failed to set key from master / Ошибка установки ключа из мастер-пароля / Помилка встановлення ключа з майстер-пароля: {e}")
                    return
                finish_ok()
                return
            elif error_code == "2fa_missing_secret":
                logger.warning("2FA secret missing, disabling 2FA as fallback / Секрет 2FA отсутствует, отключаем 2FA как fallback / Секрет 2FA відсутній, вимикаємо 2FA як fallback")
                if cls._cached_config:
                    try:
                        cls._cached_config.set_2fa_enabled(False)
                        cls._cached_config.save()
                    except (AttributeError, OSError) as e:
                        logger.debug(f"Failed to disable 2FA / Ошибка отключения 2FA / Помилка вимкнення 2FA: {e}")
                if cls.verify(pwd, source="startup"):
                    try:
                        set_key_from_master(pwd)
                    except (ValueError, TypeError, RuntimeError) as e:
                        logger.error(f"Failed to set key from master / Ошибка установки ключа из мастер-пароля / Помилка встановлення ключа з майстер-пароля: {e}")
                        return
                    finish_ok()
                    return
            elif error_code == "2fa_cancelled":
                cancel()
                return
            elif error_code == "2fa_invalid_code":
                status.configure(text=L.get("2fa_invalid_code", "Invalid verification code / Неверный код подтверждения / Невірний код підтвердження"))
                entry.delete(0, "end")
                entry.focus_set()
                return

        info = cls.get_lockout_info()
        if info['is_permanently_locked']:
            status.configure(text=L.get("master_blocked", "Too many attempts. Program closed. / Слишком много попыток. Программа закрыта. / Занадто багато спроб. Програму закрито."))
            entry.configure(state="disabled")
            submit_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            root.after(2000, _safe_exit)
        elif info['is_locked']:
            status.configure(text=f"{L.get('lock_wait', 'Please wait / Подождите / Зачекайте')} {info['lockout_seconds']} {L.get('seconds_short', 'sec / сек / сек')}...")
            entry.delete(0, "end")
            entry.configure(state="disabled")
            submit_btn.configure(state="disabled")
            cancel_btn.configure(state="disabled")
            root.after(1000, update_status)
        else:
            status.configure(text=L["master_wrong"].format(info['attempts'], max_attempts))
            entry.delete(0, "end")
            entry.focus_set()

    submit_btn = ctk.CTkButton(
        btn_frame,
        text=L.get("unlock", "Unlock / Разблокировать / Розблокувати"),
        width=100,
        height=34,
        corner_radius=17,
        fg_color=btn_fg,
        hover_color=btn_hover,
        font=("Segoe UI", 12, "bold"),
        command=submit,
    )
    submit_btn.pack(side="left", padx=6)

    cancel_btn = ctk.CTkButton(
        btn_frame,
        text=L.get("close", "Close / Закрыть / Закрити"),
        width=100,
        height=34,
        corner_radius=17,
        fg_color="#8b0000",
        hover_color="#cc0000",
        font=("Segoe UI", 12, "bold"),
        command=cancel,
    )
    cancel_btn.pack(side="left", padx=6)

    entry.bind("<Return>", lambda _e: submit())
    entry.bind("<Escape>", lambda _e: cancel())
    root.protocol("WM_DELETE_WINDOW", cancel)

    update_status()

    try:
        root.mainloop()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.debug(f"Startup prompt interrupted / Запрос при запуске прерван / Запит при запуску перервано: {e}")
        return False

    return result["ok"]
