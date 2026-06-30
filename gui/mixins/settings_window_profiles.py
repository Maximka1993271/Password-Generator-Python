"""
Settings window mixin - Profiles (save/load/reset)
Миксин окна настроек - Профили (сохранение/загрузка/сброс)
Міксин вікна налаштувань - Профілі (збереження/завантаження/скидання)

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
import datetime
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from utils.logger import get_logger
from Langs.lang import LANGUAGES
from gui.dialogs import CTkMessageBox

logger = get_logger("settings_window")


class SettingsWindowProfilesMixin:
    """Settings profiles functionality

    Функциональность профилей настроек
    Функціональність профілів налаштувань
    """

    def _save_settings_profile(self) -> None:
        """
        Save current settings as a profile

        Сохранить текущие настройки как профиль
        Зберегти поточні налаштування як профіль
        """
        from storage.config import Config

        L = LANGUAGES[self.current_lang]

        try:
            self.settings_window.attributes("-topmost", False)
            self.settings_window.update_idletasks()
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError): pass
        file_path = filedialog.asksaveasfilename(
            parent=getattr(self, "settings_window", self),
            defaultextension=".json",
            filetypes=[("Profile files", "*.json"), ("All files", "*.*")],
            title=L.get("save_profile", "Save Settings Profile / Сохранить профиль настроек / Зберегти профіль налаштувань")
        )

        if not file_path:
            return

        try:
            config = AppSettings.instance()
            all_config = config.get_all()

            # Remove sensitive data / Удаляем чувствительные данные / Видаляємо чутливі дані
            sensitive_keys = ['2fa_secret', '2fa_backup_hashes', '_schema_version']
            for key in sensitive_keys:
                if key in all_config:
                    del all_config[key]

            # Add metadata / Добавляем метаданные / Додаємо метадані
            profile_data = {
                "profile_version": 1,
                "created": datetime.datetime.now().isoformat(),
                "settings": all_config
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            CTkMessageBox.info(self.settings_window, L.get("save_profile", "Save Profile / Сохранить профиль / Зберегти профіль"),
                              L.get("profile_saved", "Settings profile saved successfully! / Профиль настроек успешно сохранён! / Профіль налаштувань успішно збережено!"))
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.error(f"Failed to save profile / Ошибка сохранения профиля / Помилка збереження профілю: {e}")
            CTkMessageBox.error(self.settings_window, L.get("err_title", "Error / Ошибка / Помилка"),
                               f"Failed to save profile / Ошибка сохранения профиля / Помилка збереження профілю: {e}")

    def _load_settings_profile(self) -> None:
        """
        Load settings from a profile

        Загрузить настройки из профиля
        Завантажити налаштування з профілю
        """
        from storage.config import Config

        L = LANGUAGES[self.current_lang]

        try:
            self.settings_window.attributes("-topmost", False)
            self.settings_window.update_idletasks()
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError, tk.TclError): pass
        file_path = filedialog.askopenfilename(
            parent=getattr(self, "settings_window", self),
            filetypes=[("Profile files", "*.json"), ("All files", "*.*")],
            title=L.get("load_profile", "Load Settings Profile / Загрузить профиль настроек / Завантажити профіль налаштувань")
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            settings = profile_data.get("settings", {})

            # Apply settings / Применяем настройки / Застосовуємо налаштування
            for key, value in settings.items():
                self.config.set(key, value)

            # Reload UI / Перезагружаем UI / Перезавантажуємо UI
            self._load_all_settings()

            CTkMessageBox.info(self.settings_window, L.get("load_profile", "Load Profile / Загрузить профиль / Завантажити профіль"),
                              L.get("profile_loaded", "Settings profile loaded successfully! / Профиль настроек успешно загружен! / Профіль налаштувань успішно завантажено!"))
        except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to load profile / Ошибка загрузки профиля / Помилка завантаження профілю: {e}")
            CTkMessageBox.error(self.settings_window, L.get("err_title", "Error / Ошибка / Помилка"),
                               f"Failed to load profile / Ошибка загрузки профиля / Помилка завантаження профілю: {e}")

    def _reset_settings_profile(self) -> None:
        """
        Reset settings to defaults

        Сбросить настройки к значениям по умолчанию
        Скинути налаштування до значень за замовчуванням
        """
        L = LANGUAGES[self.current_lang]

        if CTkMessageBox.question(self.settings_window, L.get("reset_profile", "Reset / Сбросить / Скинути"),
                                  L.get("reset_profile_confirm", "Reset all settings to defaults? / Сбросить все настройки к значениям по умолчанию? / Скинути всі налаштування до значень за замовчуванням?")):
            self.config.reset_to_defaults()
            self._load_all_settings()
            CTkMessageBox.info(self.settings_window, L.get("reset_profile", "Reset / Сбросить / Скинути"),
                              L.get("profile_reset", "Settings reset to defaults! / Настройки сброшены к значениям по умолчанию! / Налаштування скинуто до значень за замовчуванням!"))