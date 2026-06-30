from __future__ import annotations
# master_mixin_ui.py
"""
Master mixin ui module for Secure Pass Pro.
Модуль Master mixin ui для Secure Pass Pro.
Модуль Master mixin ui для Secure Pass Pro.
"""
"""
Master mixin ui module for Secure Pass Pro.
Модуль Master mixin ui для Secure Pass Pro.
Модуль Master mixin ui для Secure Pass Pro.
"""
"""
Master password mixin - UI methods (lock screen, minimize, colors)
Миксин мастер-пароля - UI методы (экран блокировки, сворачивание, цвета)
Міксин майстер-пароля - UI методи (екран блокування, згортання, кольори)
"""
import tkinter as tk
import ctypes
from typing import Any
import customtkinter as ctk
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from utils.helpers import get_global_radius
from security.master import MasterPassword
from security.encryption import set_key_from_master
from gui.dialogs import CTkMessageBox
from gui.mixins.dialogs_helpers import _get_colors_for_theme as _get_colors_for_theme_func

logger = get_logger("master_mixin")

class MasterMixinUI:
    """UI methods for master password (lock screen, minimize)

    UI методы для мастер-пароля (экран блокировки, сворачивание)
    UI методи для майстер-пароля (екран блокування, згортання)
    """

    def _minimize_window(self, window: Any) -> None:
        """
        Minimize window to taskbar

        Сворачивает окно в панель задач
        Згортає вікно в панель завдань
        """
        try:
            hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
            if not hwnd:
                hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), 2)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)
            else:
                window.iconify()
        except (AttributeError, OSError, TypeError, tk.TclError, RuntimeError) as e:
            logger.debug(f"Minimize error / Ошибка сворачивания / Помилка згортання: {e}")
            window.iconify()

    def _show_lock_screen(self) -> bool:
        """
        Show lock screen with working minimize button and correct 2FA

        Показать экран блокировки с работающей кнопкой сворачивания и корректным 2FA
        Показати екран блокування з працюючою кнопкою згортання та коректним 2FA
        """
        from security.totp import TOTP, get_totp_manager

        L = LANGUAGES[self.current_lang]
        theme = self._get_actual_theme()
        colors = self._get_colors_for_theme(theme)
        radius = get_global_radius()

        win = ctk.CTkToplevel(self)
        win.title(L.get("win_title", "Secure Pass Pro v4.0"))

        self.withdraw()

        win.protocol("WM_DELETE_WINDOW", self.destroy)

        win.minsize(450, 480)
        win.maxsize(450, 480)

        win.attributes("-topmost", True)
        win.after(100, lambda: win.attributes("-topmost", False))

        win.geometry("450x480")
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 480) // 2
        win.geometry(f"450x480+{x}+{y}")
        win.configure(fg_color=colors["bg"])

        main_frame = ctk.CTkFrame(win, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 48), text_color="#4EC9B0").pack(pady=(0, 5))
        ctk.CTkLabel(main_frame, text=L.get("auto_lock_title", "Program Locked / Программа заблокирована / Програму заблоковано"),
                    font=("Segoe UI", 18, "bold"), text_color=colors["label_text"]).pack(pady=(0, 10))

        ctk.CTkLabel(main_frame, text=L.get("master_prompt", "Enter master password: / Введите мастер-пароль: / Введіть майстер-пароль:"),
                    font=("Segoe UI", 13), text_color=colors["label_text"]).pack()

        pwd_entry = ctk.CTkEntry(main_frame, width=320, height=45, font=("Segoe UI", 14), show="*",
                                fg_color=colors["entry_bg"], text_color=colors["fg"], corner_radius=radius)
        pwd_entry.pack(pady=(5, 10))
        pwd_entry.focus_set()

        _2fa_frame = ctk.CTkFrame(main_frame, fg_color="transparent")

        code_label = ctk.CTkLabel(_2fa_frame, text=L.get("2fa_enter_verification", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:"),
                                  font=("Segoe UI", 13), text_color=colors["label_text"])
        code_label.pack()

        code_entry = ctk.CTkEntry(_2fa_frame, width=220, height=45, font=("Consolas", 20, "bold"),
                                 justify="center", fg_color=colors["entry_bg"], text_color=colors["fg"],
                                 corner_radius=radius)
        code_entry.pack(pady=(5, 0))
        code_entry.configure(state="disabled")

        status_label = ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 12), text_color="#E24B4A")
        status_label.pack(pady=(5, 5))

        unlock_btn = ctk.CTkButton(main_frame, text=L.get("unlock", "Unlock / Разблокировать / Розблокувати"),
                                   width=160, height=45, fg_color="#2d6a4f",
                                   hover_color="#40916c", corner_radius=radius,
                                   font=("Segoe UI", 14, "bold"))
        unlock_btn.pack(pady=(10, 15))

        result = [False]
        master_verified = [False]

        def unlock_success() -> None:
            """
            Handle unlock success.
            Обработать unlock success.
            Обробити unlock success.
            """
            result[0] = True
            self.deiconify()
            win.destroy()

        def update_status() -> None:
            """
            Update status.
            Обновить status.
            Оновити status.
            """
            try:
                info = MasterPassword.get_lockout_info()
                if info['is_locked']:
                    status_label.configure(text=f"{L.get('lock_wait', 'Please wait / Подождите / Зачекайте')} {info['lockout_seconds']} {L.get('seconds_short', 'sec / сек / сек')}...")
                    pwd_entry.configure(state="disabled")
                    code_entry.configure(state="disabled")
                    unlock_btn.configure(state="disabled")
                    win.after(1000, update_status)
                else:
                    pwd_entry.configure(state="normal")
                    unlock_btn.configure(state="normal")
                    pwd_entry.focus_set()
                    if info['attempts'] > 0 and not master_verified[0]:
                        status_label.configure(text=L.get("master_wrong", "Wrong password! Attempt {0} of {1} / Неверный пароль! Попытка {0} из {1} / Невірний пароль! Спроба {0} з {1}").format(info['attempts'], 5))
                    else:
                        status_label.configure(text="")
            except (KeyError, TypeError, AttributeError, RuntimeError) as e:
                logger.debug(f"Update status error / Ошибка обновления статуса / Помилка оновлення статусу: {e}")

        def check_master_password() -> None:
            """
            Check master password.
            Проверить master password.
            Перевірити master password.
            """
            pwd = pwd_entry.get()
            if MasterPassword.verify(pwd):
                set_key_from_master(pwd)
                master_verified[0] = True
                status_label.configure(text=L.get("master_verified", "Master password verified / Мастер-пароль подтверждён / Майстер-пароль підтверджено"), text_color="#2ECC71")

                if self.config.is_2fa_enabled():
                    code_entry.configure(state="normal")
                    code_entry.focus_set()
                    unlock_btn.configure(text=L.get("2fa_verify_title", "Verify 2FA / Подтвердить 2FA / Підтвердити 2FA"))
                    pwd_entry.configure(state="disabled")
                    _2fa_frame.pack(pady=(10, 5))
                else:
                    unlock_success()
            else:
                info = MasterPassword.get_lockout_info()
                status_label.configure(text=L.get("master_wrong", "Wrong password! Attempt {0} of {1} / Неверный пароль! Попытка {0} из {1} / Невірний пароль! Спроба {0} з {1}").format(info['attempts'], 5))
                pwd_entry.delete(0, "end")
                pwd_entry.focus_set()

        def check_2fa() -> None:
            """
            Check 2fa.
            Проверить 2fa.
            Перевірити 2fa.
            """
            try:
                code_raw = code_entry.get().strip()
                code_clean = ''.join(filter(str.isdigit, code_raw))

                if len(code_clean) != 6:
                    status_label.configure(text=L.get("2fa_invalid_code", "Invalid code - enter 6 digits / Неверный код - введите 6 цифр / Невірний код - введіть 6 цифр"))
                    code_entry.delete(0, "end")
                    code_entry.focus_set()
                    return

                secret = self.config.get_2fa_secret()
                if secret:
                    secret_clean = secret.upper().replace(" ", "").replace("-", "")
                    totp = TOTP(secret_clean)
                    is_valid, _ = totp.verify(code_clean)
                    if is_valid:
                        self.config.set_2fa_last_verified()
                        unlock_success()
                        return

                manager = get_totp_manager()
                if manager.verify_backup_code(code_clean):
                    self.config.set_2fa_backup_hashes(manager.get_backup_codes_hashes())
                    self.config.save()
                    CTkMessageBox.warning(win, L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                                         L.get("2fa_backup_used", "Backup code used! Please generate new backup codes in settings. / Использован резервный код! Пожалуйста, сгенерируйте новые резервные коды в настройках. / Використано резервний код! Будь ласка, згенеруйте нові резервні коди в налаштуваннях."))
                    unlock_success()
                    return

                status_label.configure(text=L.get("2fa_invalid_code", "Invalid verification code / Неверный код подтверждения / Невірний код підтвердження"))
                code_entry.delete(0, "end")
                code_entry.focus_set()
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                logger.error(f"2FA verification error / Ошибка верификации 2FA / Помилка верифікації 2FA: {e}")
                status_label.configure(text=L.get("2fa_error", "Verification error / Ошибка верификации / Помилка верифікації"))

        def on_unlock() -> None:
            """
            Handle the unlock event.
            Обработчик unlock.
            Обробник unlock.
            """
            if MasterPassword.get_remaining_lockout_time() > 0:
                update_status()
                return

            if master_verified[0] and self.config.is_2fa_enabled():
                check_2fa()
            else:
                check_master_password()

        unlock_btn.configure(command=on_unlock)

        pwd_entry.bind("<Return>", lambda e: on_unlock())
        code_entry.bind("<Return>", lambda e: on_unlock())

        update_status()

        try:
            self.wait_window(win)
        except (tk.TclError, RuntimeError, AttributeError) as e:
            logger.debug(f"Lock screen wait error / Ошибка ожидания экрана блокировки / Помилка очікування екрану блокування: {e}")

        return result[0]

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

    def _center_window_relative_to_parent(self, window: Any, width: int, height: int) -> None:
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
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")