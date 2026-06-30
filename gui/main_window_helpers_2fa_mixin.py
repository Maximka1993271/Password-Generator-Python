from __future__ import annotations
# gui/main_window_helpers_2fa_mixin.py
"""
Main window helpers 2fa mixin module for Secure Pass Pro.
Модуль Main window helpers 2fa mixin для Secure Pass Pro.
Модуль Main window helpers 2fa mixin для Secure Pass Pro.
"""
"""
Main window helpers 2fa mixin module for Secure Pass Pro.
Модуль Main window helpers 2fa mixin для Secure Pass Pro.
Модуль Main window helpers 2fa mixin для Secure Pass Pro.
"""
"""
2FA helper methods for main window
Методы 2FA для главного окна
Методи 2FA для головного вікна
"""
import tkinter as tk
import customtkinter as ctk

from gui.dialogs import CTkMessageBox
from utils.helpers import get_global_radius
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from security.master import MasterPassword
from typing import Optional

logger = get_logger("main_window_helpers")


class MainWindow2FAMixin:
    """2FA helper methods for SecurePassPro main window

    Методы 2FA для главного окна SecurePassPro
    Методи 2FA для головного вікна SecurePassPro
    """

    def _update_2fa_status_in_settings(self) -> None:
        """
        Update 2FA status in settings window if open

        Обновляет статус 2FA в окне настроек если открыто
        Оновлює статус 2FA у вікні налаштувань якщо відкрито
        """
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            if hasattr(self, '_2fa_status_label') and self._2fa_status_label:
                try:
                    self._2fa_status_label.configure(
                        text=self._get_2fa_status_text(),
                        text_color=self._get_2fa_status_color()
                    )
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Update 2FA status error / Ошибка обновления статуса 2FA / Помилка оновлення статусу 2FA: {e}")

    def _get_2fa_status_text(self) -> str:
        """
        Get 2FA status text for display

        Получить текст статуса 2FA для отображения
        Отримати текст статусу 2FA для відображення
        """
        L = LANGUAGES[self.current_lang]
        if self.config.is_2fa_enabled():
            return L.get("2fa_status_enabled", "Enabled / Включена / Увімкнено")
        else:
            return L.get("2fa_status_disabled", "Disabled / Отключена / Вимкнено")

    def _get_2fa_status_color(self) -> str:
        """
        Get 2FA status color

        Получить цвет статуса 2FA
        Отримати колір статусу 2FA
        """
        if self.config.is_2fa_enabled():
            return "#2ECC71"
        else:
            return "#888888"

    def _update_2fa_buttons(self) -> None:
        """
        Update 2FA button states

        Обновляет состояние кнопок 2FA
        Оновлює стан кнопок 2FA
        """
        self._update_2fa_status_in_settings()

    def _setup_2fa(self) -> None:
        """
        Setup two-factor authentication

        Настройка двухфакторной аутентификации
        Налаштування двофакторної аутентифікації
        """
        from security.totp import TOTP, get_totp_manager
        from utils.qr_utils import QRUtils

        L = LANGUAGES[self.current_lang]

        if not MasterPassword.is_set():
            CTkMessageBox.warning(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_master_required", "Please set a master password before enabling 2FA. / Пожалуйста, установите мастер-пароль перед включением 2FA. / Будь ласка, встановіть майстер-пароль перед увімкненням 2FA.")
            )
            return

        if self.config.is_2fa_enabled():
            result = CTkMessageBox.question(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_disable_confirm", "2FA is already enabled.\n\nDo you want to disable it? / 2FA уже включена.\n\nВы хотите отключить её? / 2FA вже увімкнена.\n\nВи хочете вимкнути її?")
            )
            if result in [True, "Yes", "yes"]:
                self._disable_2fa()
            return

        account_name = self.config.get_2fa_account_name()
        if not account_name:
            account_name = "SecurePassPro_User"

        totp = TOTP()
        secret = totp.secret
        provisioning_uri = TOTP.get_provisioning_uri(secret, account_name, "SecurePassPro")

        QRUtils.show_qr_window(
            self,
            provisioning_uri,
            secret,
            self.current_lang,
            L.get("2fa_setup_title", "2FA Setup / Настройка 2FA / Налаштування 2FA")
        )

        code = self._verify_2fa_dialog(
            L.get("2fa_verify_title", "Verify 2FA / Подтверждение 2FA / Підтвердження 2FA"),
            L.get("2fa_enter_verification", "Enter the 6-digit code from your authenticator app: / Введите 6-значный код из приложения-аутентификатора: / Введіть 6-значний код з додатку-аутентифікатора:")
        )

        if not code:
            CTkMessageBox.info(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_setup_cancelled", "2FA setup cancelled. / Настройка 2FA отменена. / Налаштування 2FA скасовано.")
            )
            return

        code_clean = ''.join(filter(str.isdigit, code))

        if totp.verify(code_clean)[0]:
            backup_codes = totp.get_backup_codes(count=10, length=8)

            manager = get_totp_manager()
            manager.enable_2fa(secret)
            manager.set_backup_codes(backup_codes)
            manager.set_account_name(account_name)

            self.config.set_2fa_enabled(True)
            self.config.set_2fa_secret(secret)
            self.config.set_2fa_backup_hashes(manager.get_backup_codes_hashes())
            self.config.set_2fa_account_name(account_name)
            self.config.set_2fa_setup_completed(True)
            self.config.set_2fa_last_verified()
            self.config.save()

            self._show_backup_codes(backup_codes)

            CTkMessageBox.info(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_enabled_success", "Two-Factor Authentication has been enabled successfully!\n\nPlease save your backup codes in a safe place. / Двухфакторная аутентификация успешно включена!\n\nПожалуйста, сохраните резервные коды в надёжном месте. / Двофакторну аутентифікацію успішно увімкнено!\n\nБудь ласка, збережіть резервні коди в надійному місці.")
            )

            self._update_2fa_buttons()
            self._update_2fa_indicator()
        else:
            CTkMessageBox.error(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_invalid_code", "Invalid verification code. Please try again. / Неверный код подтверждения. Пожалуйста, попробуйте снова. / Невірний код підтвердження. Будь ласка, спробуйте ще раз.")
            )

    def _disable_2fa(self) -> None:
        """
        Disable two-factor authentication

        Отключает двухфакторную аутентификацию
        Вимкає двофакторну аутентифікацію
        """
        from security.totp import get_totp_manager

        L = LANGUAGES[self.current_lang]

        if CTkMessageBox.question(
            self,
            L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
            L.get("2fa_disable_warning", "WARNING: Disabling 2FA will make your account less secure!\n\nAre you sure you want to disable 2FA? / ВНИМАНИЕ: Отключение 2FA сделает ваш аккаунт менее защищённым!\n\nВы уверены, что хотите отключить 2FA? / УВАГА: Вимкнення 2FA зробить ваш акаунт менш захищеним!\n\nВи впевнені, що хочете вимкнути 2FA?")
        ) not in [True, "Yes", "yes"]:
            return

        code = self._verify_2fa_dialog(
            L.get("2fa_verify_disable", "Enter 2FA code to disable / Введите код 2FA для отключения / Введіть код 2FA для вимкнення"),
            L.get("2fa_enter_code", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:")
        )

        if not code:
            return

        code_clean = ''.join(filter(str.isdigit, code))

        from security.totp import TOTP
        secret = self.config.get_2fa_secret()
        if secret:
            secret_clean = secret.upper().replace(" ", "").replace("-", "")
            totp = TOTP(secret_clean)
            if totp.verify(code_clean)[0]:
                manager = get_totp_manager()
                manager.disable_2fa()

                self.config.clear_2fa()
                self.config.save()

                CTkMessageBox.info(
                    self,
                    L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                    L.get("2fa_disabled_success", "Two-Factor Authentication has been disabled. / Двухфакторная аутентификация отключена. / Двофакторну аутентифікацію вимкнено.")
                )

                self._update_2fa_buttons()
                self._update_2fa_indicator()
            else:
                CTkMessageBox.error(
                    self,
                    L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                    L.get("2fa_invalid_code", "Invalid verification code. / Неверный код подтверждения. / Невірний код підтвердження.")
                )
        else:
            manager = get_totp_manager()
            manager.disable_2fa()
            self.config.clear_2fa()
            self.config.save()

            CTkMessageBox.info(
                self,
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_disabled_success", "Two-Factor Authentication has been disabled. / Двухфакторная аутентификация отключена. / Двофакторну аутентифікацію вимкнено.")
            )
            self._update_2fa_buttons()
            self._update_2fa_indicator()

    def _verify_2fa_dialog(self, title: str, prompt: str) -> Optional[str]:
        """
        Show dialog for entering 2FA code

        Показывает диалог для ввода 2FA кода
        Показує діалог для введення 2FA коду
        """
        L = LANGUAGES[self.current_lang]
        theme = self._get_actual_theme()

        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("450x350")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.lift()
        dialog.focus_force()
        dialog.after(100, lambda: dialog.attributes("-topmost", False) if dialog and dialog.winfo_exists() else None)
        dialog.attributes("-topmost", True)

        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 450) // 2
        y = self.winfo_y() + (self.winfo_height() - 350) // 2
        dialog.geometry(f"450x350+{x}+{y}")

        if theme == "light":
            bg_color = "#F3F3F3"
            fg_color = "#000000"
            entry_bg = "#FFFFFF"
        else:
            bg_color = "#1d1e1e"
            fg_color = "#FFFFFF"
            entry_bg = "#2b2b2b"

        dialog.configure(fg_color=bg_color)

        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 40), text_color="#4EC9B0").pack(pady=(0, 15))
        ctk.CTkLabel(main_frame, text=prompt, font=("Segoe UI", 14), text_color=fg_color, wraplength=350).pack(pady=(0, 20))

        entry = ctk.CTkEntry(main_frame, width=250, height=50, font=("Consolas", 24, "bold"),
                            justify="center", fg_color=entry_bg, text_color=fg_color, corner_radius=15)
        entry.pack(pady=(0, 20))
        entry.focus_set()

        result: Optional[str] = None

        def on_ok() -> None:
            """
            Handle the ok event.
            Обработчик ok.
            Обробник ok.
            """
            nonlocal result
            try:
                code = entry.get().strip()
                code_clean = ''.join(filter(str.isdigit, code))
                if len(code_clean) == 6:
                    result = code_clean
                    dialog.destroy()
                else:
                    entry.configure(border_color="#E24B4A", border_width=2)
                    dialog.after(200, lambda: entry.configure(border_color=""))
                    entry.delete(0, "end")
                    entry.focus_set()
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"2FA dialog OK error / Ошибка OK в диалоге 2FA / Помилка OK в діалозі 2FA: {e}")

        def on_cancel() -> None:
            """
            Handle the cancel event.
            Обработчик cancel.
            Обробник cancel.
            """
            dialog.destroy()

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack()

        ctk.CTkButton(btn_frame, text=L.get("ok", "Verify / Подтвердить / Підтвердити"),
                     command=on_ok, width=130, height=40, fg_color="#2d6a4f",
                     corner_radius=20, font=("Segoe UI", 13, "bold")).pack(side="left", padx=15)

        ctk.CTkButton(btn_frame, text=L.get("cancel", "Cancel / Отмена / Скасувати"),
                     command=on_cancel, width=130, height=40, fg_color="#8b0000",
                     corner_radius=20, font=("Segoe UI", 13, "bold")).pack(side="left", padx=15)

        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())

        dialog.after(100, lambda: dialog.attributes("-topmost", False))

        self.wait_window(dialog)

        return result

    def _show_backup_codes(self, backup_codes: list) -> None:
        """
        Show backup codes in a separate window

        Показывает резервные коды в отдельном окне
        Показує резервні коди в окремому вікні
        """
        L = LANGUAGES[self.current_lang]
        theme = self._get_actual_theme()
        radius = get_global_radius()

        win = ctk.CTkToplevel(self)
        win.title(L.get("2fa_backup_codes", "Backup Codes / Резервные коды / Резервні коди"))
        win.geometry("550x600")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.attributes("-topmost", True)

        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 550) // 2
        y = self.winfo_y() + (self.winfo_height() - 600) // 2
        win.geometry(f"550x600+{x}+{y}")

        main_frame = ctk.CTkFrame(win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(main_frame, text=L.get("2fa_backup_codes", "Backup Codes / Резервные коды / Резервні коди"),
                    font=("Segoe UI", 20, "bold")).pack(pady=(0, 15))

        warning_frame = ctk.CTkFrame(main_frame, fg_color="#3a2a0a", corner_radius=12)
        warning_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(warning_frame,
                    text=L.get("2fa_backup_warning_detailed",
                               "Store these codes in a safe place!\nEach code can be used only once to recover access. / Сохраните эти коды в надёжном месте!\nКаждый код можно использовать только один раз для восстановления доступа. / Збережіть ці коди в надійному місці!\nКожен код можна використати лише один раз для відновлення доступу."),
                    font=("Segoe UI", 12), text_color="#FFA500", justify="center").pack(pady=12, padx=15)

        codes_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        codes_frame.pack(pady=10)

        left_frame = ctk.CTkFrame(codes_frame, fg_color="transparent")
        left_frame.pack(side="left", padx=15)

        right_frame = ctk.CTkFrame(codes_frame, fg_color="transparent")
        right_frame.pack(side="left", padx=15)

        half = len(backup_codes) // 2 + len(backup_codes) % 2
        for i, code in enumerate(backup_codes):
            target = left_frame if i < half else right_frame
            code_text = code if '-' in code else f"{code[:4]}-{code[4:]}"

            ctk.CTkLabel(target, text=code_text, font=("Consolas", 16, "bold"),
                        fg_color=("#2b2b2b" if theme == "dark" else "#e0e0e0"),
                        corner_radius=10, padx=20, pady=8).pack(pady=6)

        def copy_all_codes() -> None:
            """
            Handle copy all codes.
            Обработать copy all codes.
            Обробити copy all codes.
            """
            try:
                all_codes = "\n".join(backup_codes)
                win.clipboard_clear()
                win.clipboard_append(all_codes)
                copy_btn.configure(text=L.get("copied", "Copied! / Скопировано! / Скопійовано!"))
                win.after(2000, lambda: copy_btn.configure(text=L.get("copy_all", "Copy All / Копировать все / Копіювати всі")))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Copy all codes error / Ошибка копирования всех кодов / Помилка копіювання всіх кодів: {e}")

        copy_btn = ctk.CTkButton(main_frame, text=L.get("copy_all", "Copy All / Копировать все / Копіювати всі"),
                                command=copy_all_codes, width=180, height=40, fg_color="#2d6a4f",
                                corner_radius=radius, font=("Segoe UI", 13, "bold"))
        copy_btn.pack(pady=15)

        ctk.CTkButton(main_frame, text=L.get("ok", "OK / Хорошо / Гаразд"), command=win.destroy,
                     width=140, height=40, fg_color="#8b0000", corner_radius=radius,
                     font=("Segoe UI", 13, "bold")).pack(pady=10)

        win.after(100, lambda: win.attributes("-topmost", False))
        win.focus_force()

    def _show_2fa_settings(self) -> None:
        """
        Show 2FA settings window

        Показывает окно настроек 2FA
        Показує вікно налаштувань 2FA
        """
        from security.totp import get_totp_manager

        L = LANGUAGES[self.current_lang]
        radius = get_global_radius()

        is_enabled = self.config.is_2fa_enabled()

        win = ctk.CTkToplevel(self)
        win.title(L.get("2fa_settings_title", "2FA Settings / Настройки 2FA / Налаштування 2FA"))
        win.geometry("500x550")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.attributes("-topmost", True)

        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 500) // 2
        y = self.winfo_y() + (self.winfo_height() - 550) // 2
        win.geometry(f"500x550+{x}+{y}")

        main_frame = ctk.CTkFrame(win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(main_frame, text=L.get("2fa_settings_title", "2FA Settings / Настройки 2FA / Налаштування 2FA"),
                    font=("Segoe UI", 22, "bold")).pack(pady=(0, 15))

        if is_enabled:
            status_text = L.get("2fa_status_enabled", "Enabled / Включена / Увімкнено")
            status_color = "#2ECC71"
        else:
            status_text = L.get("2fa_status_disabled", "Disabled / Отключена / Вимкнено")
            status_color = "#FF4444"

        ctk.CTkLabel(main_frame, text=status_text, font=("Segoe UI", 15, "bold"),
                    text_color=status_color).pack(pady=(0, 20))

        ctk.CTkFrame(main_frame, height=2, fg_color="#2d6a4f").pack(fill="x", pady=10)

        if is_enabled:
            manager = get_totp_manager()
            backup_count = manager.get_backup_codes_count()

            ctk.CTkLabel(main_frame, text=L.get("2fa_backup_codes_info", "Backup Codes / Резервные коды / Резервні коди"),
                        font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(15, 8))

            ctk.CTkLabel(main_frame, text=L.get("2fa_backup_count", "Remaining backup codes: {0} / Осталось резервных кодов: {0} / Залишилось резервних кодів: {0}").format(backup_count),
                        font=("Segoe UI", 13)).pack(anchor="w", pady=(0, 15))

            def generate_new_backup() -> None:
                """
                Handle generate new backup.
                Обработать generate new backup.
                Обробити generate new backup.
                """
                from security.totp import TOTP, get_totp_manager

                if CTkMessageBox.question(win, L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                    L.get("2fa_regenerate_backup_confirm", "Generating new backup codes will invalidate old ones.\n\nContinue? / Генерация новых резервных кодов сделает старые недействительными.\n\nПродолжить? / Генерація нових резервних кодів зробить старі недійсними.\n\nПродовжити?")) in [True, "Yes", "yes"]:

                    code = self._verify_2fa_dialog(
                        L.get("2fa_verify_regenerate", "Enter 2FA code to generate new backup codes / Введите код 2FA для генерации новых резервных кодов / Введіть код 2FA для генерації нових резервних кодів"),
                        L.get("2fa_enter_code", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:")
                    )

                    if code:
                        secret = self.config.get_2fa_secret()
                        if secret:
                            secret_clean = secret.upper().replace(" ", "").replace("-", "")
                            totp = TOTP(secret_clean)
                            if totp.verify(code)[0]:
                                new_codes = totp.get_backup_codes(count=10, length=8)
                                manager = get_totp_manager()
                                manager.set_backup_codes(new_codes)
                                self.config.set_2fa_backup_hashes(manager.get_backup_codes_hashes())
                                self.config.save()
                                self._show_backup_codes(new_codes)
                                CTkMessageBox.info(win, L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                                                 L.get("2fa_backup_regenerated", "New backup codes generated successfully! / Новые резервные коды успешно сгенерированы! / Нові резервні коди успішно згенеровано!"))
                                win.destroy()
                            else:
                                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                                  L.get("2fa_invalid_code", "Invalid verification code. / Неверный код подтверждения. / Невірний код підтвердження."))

            ctk.CTkButton(main_frame, text=L.get("2fa_regenerate_backup", "Generate New Backup Codes / Сгенерировать новые резервные коды / Згенерувати нові резервні коди"),
                         command=generate_new_backup, width=320, height=45, fg_color="#FF9800",
                         corner_radius=radius, font=("Segoe UI", 13, "bold")).pack(pady=15)

            ctk.CTkButton(main_frame, text=L.get("2fa_disable", "Disable 2FA / Отключить 2FA / Вимкнути 2FA"),
                         command=lambda: [win.destroy(), self._disable_2fa()],
                         width=320, height=45, fg_color="#8b0000", corner_radius=radius,
                         font=("Segoe UI", 13, "bold")).pack(pady=15)
        else:
            ctk.CTkLabel(main_frame, text=L.get("2fa_description",
                      "Two-Factor Authentication adds an extra layer of security.\n\n"
                      "You will need to enter a 6-digit code from an authenticator app\n"
                      "every time you unlock the program. / Двухфакторная аутентификация добавляет дополнительный уровень безопасности.\n\n"
                      "При каждом входе в программу потребуется вводить 6-значный код из приложения-аутентификатора. / Двофакторна аутентифікація додає додатковий рівень безпеки.\n\n"
                      "При кожному вході в програму потрібно буде вводити 6-значний код із застосунку-аутентифікатора."),
                      wraplength=420, justify="center", font=("Segoe UI", 12)).pack(pady=15)

            ctk.CTkButton(main_frame, text=L.get("2fa_enable", "Enable 2FA / Включить 2FA / Увімкнути 2FA"),
                         command=lambda: [win.destroy(), self._setup_2fa()],
                         width=320, height=50, fg_color="#2d6a4f", corner_radius=radius,
                         font=("Segoe UI", 15, "bold")).pack(pady=25)

        ctk.CTkButton(main_frame, text=L.get("close", "Close / Закрыть / Закрити"), command=win.destroy,
                     width=140, height=40, fg_color="#607D8B", corner_radius=radius,
                     font=("Segoe UI", 13, "bold")).pack(pady=20)

        win.after(100, lambda: win.attributes("-topmost", False))