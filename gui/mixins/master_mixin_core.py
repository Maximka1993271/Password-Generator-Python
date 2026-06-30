from __future__ import annotations
# master_mixin_core.py
"""
Master mixin core module for Secure Pass Pro.
Модуль Master mixin core для Secure Pass Pro.
Модуль Master mixin core для Secure Pass Pro.
"""
"""
Master mixin core module for Secure Pass Pro.
Модуль Master mixin core для Secure Pass Pro.
Модуль Master mixin core для Secure Pass Pro.
"""
"""
Master password mixin - Core methods (set, remove, update status)
Миксин мастер-пароля - Основные методы (установка, удаление, обновление статуса)
Міксин майстер-пароля - Основні методи (встановлення, видалення, оновлення статусу)
"""
import os
import tkinter as tk
from gui.dialogs import CTkMessageBox
from security.master import MasterPassword
from security.master_auth_types import MasterPasswordError
from security.encryption import set_key_from_master, clear_master_key, reencrypt_all
from Langs.lang import LANGUAGES
from cryptography.exceptions import InvalidTag
from utils.logger import get_logger

# ИСПРАВЛЕНИЕ: Добавлена точка для относительного импорта
# FIX: Added dot for relative import
# ВИПРАВЛЕННЯ: Додано крапку для відносного імпорту
from .master_mixin_base import _custom_input_dialog, MASTER_FILE

logger = get_logger("master_mixin")

class MasterMixinCore:
    """Core methods for master password management

    Основные методы для управления мастер-паролем
    Основні методи для керування майстер-паролем
    """

    def _update_master_status_label(self) -> None:
        """
        Update master password status

        Обновить статус мастер-пароля
        Оновити статус майстер-пароля
        """
        if not hasattr(self, '_master_status_label') or self._master_status_label is None:
            return
        try:
            if self._master_status_label.winfo_exists():
                L = LANGUAGES[self.current_lang]
                if MasterPassword.is_set():
                    self._master_status_label.configure(
                        text=f"{L.get('master_current', 'Status: / Статус: / Статус:')} {L.get('master_status_set', 'Set / Установлен / Встановлено')}",
                        text_color="#2ECC71"
                    )
                else:
                    self._master_status_label.configure(
                        text=f"{L.get('master_current', 'Status: / Статус: / Статус:')} {L.get('master_status_not_set', 'Not set / Не установлен / Не встановлено')}",
                        text_color="#FF4444"
                    )
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Update master status label error / Ошибка обновления статуса мастер-пароля / Помилка оновлення статусу майстер-пароля: {e}")

    def _update_master_buttons(self) -> None:
        """
        Update master password button state

        Обновить состояние кнопки мастер-пароля
        Оновити стан кнопки майстер-пароля
        """
        if not hasattr(self, '_master_set_btn') or self._master_set_btn is None:
            return
        try:
            if not self._master_set_btn.winfo_exists():
                return
            L = LANGUAGES[self.current_lang]
            if MasterPassword.is_set():
                self._master_set_btn.configure(
                    text=L.get("master_btn_remove", "Remove master password / Удалить мастер-пароль / Видалити майстер-пароль"),
                    fg_color="#8b0000",
                    hover_color="#aa2222",
                    command=self._remove_master_password
                )
            else:
                self._master_set_btn.configure(
                    text=L.get("master_btn_set", "Set master password / Установить мастер-пароль / Встановити майстер-пароль"),
                    fg_color="#2d6a4f",
                    hover_color="#40916c",
                    command=self._set_master_password
                )
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Update master buttons error / Ошибка обновления кнопок мастер-пароля / Помилка оновлення кнопок майстер-пароля: {e}")

    def _refresh_settings_window(self) -> None:
        """
        Refresh settings window if open

        Обновить окно настроек если открыто
        Оновити вікно налаштувань якщо відкрите
        """
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            try:
                if hasattr(self, '_master_set_btn') and self._master_set_btn:
                    L = LANGUAGES[self.current_lang]
                    if MasterPassword.is_set():
                        self._master_set_btn.configure(
                            text=L.get("master_btn_remove", "Remove master password / Удалить мастер-пароль / Видалити майстер-пароль"),
                            fg_color="#8b0000",
                            hover_color="#aa2222",
                            command=self._remove_master_password
                        )
                    else:
                        self._master_set_btn.configure(
                            text=L.get("master_btn_set", "Set master password / Установить мастер-пароль / Встановити майстер-пароль"),
                            fg_color="#2d6a4f",
                            hover_color="#40916c",
                            command=self._set_master_password
                        )

                if hasattr(self, '_master_status_label') and self._master_status_label:
                    L = LANGUAGES[self.current_lang]
                    if MasterPassword.is_set():
                        self._master_status_label.configure(
                            text=f"{L.get('master_current', 'Status: / Статус: / Статус:')} {L.get('master_status_set', 'Set / Установлен / Встановлено')}",
                            text_color="#2ECC71"
                        )
                    else:
                        self._master_status_label.configure(
                            text=f"{L.get('master_current', 'Status: / Статус: / Статус:')} {L.get('master_status_not_set', 'Not set / Не установлен / Не встановлено')}",
                            text_color="#FF4444"
                        )

                if hasattr(self, '_refresh_settings_window_language'):
                    self._refresh_settings_window_language()

                self.settings_window.update_idletasks()
                logger.debug("Settings window refreshed after master password change / Окно настроек обновлено после изменения мастер-пароля / Вікно налаштувань оновлено після зміни майстер-пароля")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Refresh settings window error / Ошибка обновления окна настроек / Помилка оновлення вікна налаштувань: {e}")

    def _set_master_password(self) -> None:
        """
        Set a new master password

        Установить новый мастер-пароль
        Встановити новий майстер-пароль
        """
        L = LANGUAGES[self.current_lang]
        actual_theme = self._get_actual_theme()

        if MasterPassword.is_set():
            CTkMessageBox.warning(self, L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                                 L.get("master_already_set", "Master password already set! / Мастер-пароль уже установлен! / Майстер-пароль вже встановлено!"))
            return

        new_pwd = _custom_input_dialog(
            self,
            L.get("master_set_title", "Set Master Password / Установить мастер-пароль / Встановити майстер-пароль"),
            L.get("master_set_prompt", "Create master password: / Придумайте мастер-пароль: / Придумайте майстер-пароль:"),
            show="*",
            theme=actual_theme,
            lang=self.current_lang
        )
        if not new_pwd or new_pwd == "":
            return

        if len(new_pwd) < 8:
            CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"),
                               L.get("master_too_short", "Password too short. Minimum 8 characters. / Пароль слишком короткий. Минимум 8 символов. / Пароль занадто короткий. Мінімум 8 символів."))
            return

        import re
        if not re.search(r"[0-9!@#$%^&*()_+=\[\]{};:,.<>/?@%-]", new_pwd):
            CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"),
                               L.get("master_weak", "Password too weak. Add a digit or special character. / Пароль слишком простой. Добавьте цифру или спецсимвол. / Пароль занадто простий. Додайте цифру або спецсимвол."))
            return

        confirm = _custom_input_dialog(
            self,
            L.get("master_set_title", "Set Master Password / Установить мастер-пароль / Встановити майстер-пароль"),
            L.get("master_confirm", "Confirm master password: / Подтвердите мастер-пароль: / Підтвердіть майстер-пароль:"),
            show="*",
            theme=actual_theme,
            lang=self.current_lang
        )
        if not confirm:
            return

        if new_pwd != confirm:
            CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"), L.get("master_mismatch", "Passwords do not match / Пароли не совпадают / Паролі не співпадають"))
            return

        try:
            MasterPassword.set_password(new_pwd)
            reencrypt_all(old_master=None, new_master=new_pwd)
            set_key_from_master(new_pwd)
            CTkMessageBox.info(self, L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                              L.get("master_set_ok", "Master password set / Мастер-пароль установлен / Майстер-пароль встановлено"))
        except (MasterPasswordError, ValueError, IOError, OSError, InvalidTag, RuntimeError) as exc:
            logger.error(f"Failed to set master password / Ошибка установки мастер-пароля / Помилка встановлення майстер-пароля: {exc}")
            try:
                MasterPassword.remove()
            except (OSError, IOError, PermissionError) as e:
                logger.debug(f"Master remove error during rollback / Ошибка удаления мастер-пароля при откате / Помилка видалення майстер-пароля при відкаті: {e}")
            try:
                clear_master_key()
            except (OSError, IOError, AttributeError) as e:
                logger.debug(f"Clear master key error during rollback / Ошибка очистки ключа при откате / Помилка очищення ключа при відкаті: {e}")
            CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"),
                               f"{L.get('master_set_error', 'Failed to set master password. / Ошибка установки мастер-пароля. / Помилка встановлення майстер-пароля.')}\n{exc}")
            return

        self._update_master_buttons()
        self._update_master_status_label()
        self._refresh_settings_window()

    def _remove_master_password(self) -> None:
        """
        Remove master password - FULLY FIXED VERSION with UI updates

        Удалить мастер-пароль - ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ ВЕРСИЯ
        Видалити майстер-пароль - ПОВНІСТЮ ВИПРАВЛЕНА ВЕРСІЯ
        """
        L = LANGUAGES[self.current_lang]

        try:
            if not MasterPassword.is_set():
                CTkMessageBox.info(self, L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                                  L.get("master_not_set", "Master password not set. / Мастер-пароль не установлен. / Майстер-пароль не встановлено."))
                return

            self.update_idletasks()

            confirm_question = CTkMessageBox.question(
                self,
                L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                L.get("master_remove_confirm", "Are you sure you want to remove the master password?\n\nAll passwords will remain accessible without additional protection! / Вы уверены, что хотите удалить мастер-пароль?\n\nВсе пароли останутся доступными без дополнительной защиты! / Ви впевнені, що хочете видалити майстер-пароль?\n\nВсі паролі залишаться доступними без додаткового захисту!")
            )
            if confirm_question not in [True, "Yes", "yes"]:
                return

            self.update_idletasks()

            current = _custom_input_dialog(
                self,
                L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                L.get("master_remove_prompt", "Enter current master password to confirm: / Введите текущий мастер-пароль для подтверждения: / Введіть поточний майстер-пароль для підтвердження:"),
                show="*",
                theme=self._get_actual_theme(),
                lang=self.current_lang
            )
            if not current or current == "":
                return

            if not MasterPassword.verify(current):
                CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"),
                                   L.get("master_wrong", "Wrong password! / Неверный пароль! / Невірний пароль!"))
                return

            # ========== MAIN REMOVAL ==========
            # ОСНОВНОЕ УДАЛЕНИЕ
            # ОСНОВНЕ ВИДАЛЕННЯ
            logger.info("Removing master password... / Удаление мастер-пароля... / Видалення майстер-пароля...")

            try:
                reencrypt_all(old_master=current, new_master=None)
                logger.info("Reencryption completed / Перешифрование завершено / Перешифрування завершено")
            except (ValueError, TypeError, RuntimeError, OSError, InvalidTag) as e:
                logger.warning(f"Reencryption error (continuing anyway): {e} / Ошибка перешифрования (продолжаем): {e} / Помилка перешифрування (продовжуємо): {e}")

            try:
                MasterPassword.remove()
                logger.info("MasterPassword.remove() completed / MasterPassword.remove() выполнен / MasterPassword.remove() виконано")
            except (OSError, IOError, PermissionError, RuntimeError) as e:
                logger.warning(f"MasterPassword.remove() error / Ошибка MasterPassword.remove() / Помилка MasterPassword.remove(): {e}")

            try:
                if os.path.exists(MASTER_FILE):
                    os.remove(MASTER_FILE)
                    logger.info(f"Master file deleted / Файл мастер-пароля удалён / Файл майстер-пароля видалено: {MASTER_FILE}")
            except (OSError, IOError, PermissionError, RuntimeError) as e:
                logger.warning(f"Direct master file deletion error / Ошибка прямого удаления файла мастер-пароля / Помилка прямого видалення файлу майстер-пароля: {e}")

            try:
                clear_master_key()
                logger.info("Master key cleared from memory / Ключ мастер-пароля очищен из памяти / Ключ майстер-пароля очищено з пам'яті")
            except (AttributeError, RuntimeError, OSError) as e:
                logger.warning(f"Clear master key error / Ошибка очистки ключа / Помилка очищення ключа: {e}")

            try:
                if hasattr(self, 'config') and self.config:
                    self.config.set_2fa_enabled(False)
                    self.config.set_2fa_secret("")
                    self.config.set_2fa_backup_hashes([])
                    self.config.set_2fa_setup_completed(False)
                    self.config.save()
                    logger.info("2FA disabled in config / 2FA отключена в конфиге / 2FA вимкнено в конфігу")
            except (AttributeError, OSError, TypeError, ValueError) as e:
                logger.debug(f"2FA config disable error / Ошибка отключения 2FA в конфиге / Помилка вимкнення 2FA в конфігу: {e}")

            try:
                from security.totp import get_totp_manager
                manager = get_totp_manager()
                manager.disable_2fa()
                logger.info("2FA disabled via TOTP / 2FA отключена через TOTP / 2FA вимкнено через TOTP")
            except (ImportError, AttributeError, RuntimeError) as e:
                logger.debug(f"TOTP disable error / Ошибка отключения TOTP / Помилка вимкнення TOTP: {e}")

            try:
                self.update_idletasks()
                self._update_master_buttons()
                self._update_master_status_label()

                if hasattr(self, '_update_2fa_indicator'):
                    self._update_2fa_indicator()
                if hasattr(self, '_update_2fa_buttons'):
                    self._update_2fa_buttons()

                self.update()
                self._refresh_settings_window()

            except (tk.TclError, RuntimeError, AttributeError) as e:
                logger.debug(f"UI update trace error during master removal / Ошибка обновления UI при удалении мастер-пароля / Помилка оновлення UI при видаленні майстер-пароля: {e}")

            CTkMessageBox.info(self, L.get("master_title", "Master Password / Мастер-пароль / Майстер-пароль"),
                              L.get("master_removed", "Master password removed successfully!\n\nPasswords are now stored without additional protection. / Мастер-пароль успешно удалён!\n\nПароли теперь хранятся без дополнительной защиты. / Майстер-пароль успішно видалено!\n\nПаролі тепер зберігаються без додаткового захисту."))

            logger.info("Master password removal completed successfully / Удаление мастер-пароля успешно завершено / Видалення майстер-пароля успішно завершено")

        except (ValueError, RuntimeError, tk.TclError, OSError, IOError, PermissionError, AttributeError, TypeError) as exc:
            logger.error(f"Failed to remove master password / Ошибка удаления мастер-пароля / Помилка видалення майстер-пароля: {exc}")
            CTkMessageBox.error(self, L.get("err_title", "Error / Ошибка / Помилка"),
                               f"{L.get('master_remove_error', 'Failed to remove master password. / Ошибка удаления мастер-пароля. / Помилка видалення майстер-пароля.')}\n{exc}")
            return