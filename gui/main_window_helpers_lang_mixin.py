from __future__ import annotations
# gui/main_window_helpers_lang_mixin.py
"""
Main window helpers lang mixin module for Secure Pass Pro.
Модуль Main window helpers lang mixin для Secure Pass Pro.
Модуль Main window helpers lang mixin для Secure Pass Pro.
"""
"""
Main window helpers lang mixin module for Secure Pass Pro.
Модуль Main window helpers lang mixin для Secure Pass Pro.
Модуль Main window helpers lang mixin для Secure Pass Pro.
"""
"""
Main window helper methods - Language operations
Методы-помощники главного окна - Языковые операции
Методи-помічники головного вікна - Мовні операції
"""
import tkinter as tk
import customtkinter as ctk

from Langs.lang import LANGUAGES
from utils.logger import get_logger
from security.master import MasterPassword

logger = get_logger("main_window_helpers")


class MainWindowLangMixin:
    """Language helper methods for SecurePassPro main window

    Методы-помощники для работы с языком для главного окна SecurePassPro
    Методи-помічники для роботи з мовою для головного вікна SecurePassPro
    """

    def _apply_lang(self, lang: str) -> None:
        """Full UI language update

        Полное обновление языка интерфейса
        Повне оновлення мови інтерфейсу
        """
        self.current_lang = lang
        L = LANGUAGES[lang]

        try:
            self.lbl_author.configure(text=L["author"])
            self.lbl_menu.configure(text=L["menu_title"])
            self.lbl_title.configure(text=L["win_title"])
            self._update_len_label(self.slider_len.get())
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.error(f"Language application error / Ошибка применения языка / Помилка застосування мови: {e}")

        try:
            self.cb_upper.configure(text=L["upper"])
            self.cb_lower.configure(text=L["lower"])
            self.cb_digits.configure(text=L["digits"])
            self.cb_symb.configure(text=L["symb"])
            self.cb_ambig.configure(text=L["ambig"])
            self.cb_at_least.configure(text=L["at_least"])
            self.cb_hide.configure(text=L["hide"])
            self.cb_no_repeat.configure(text=L["no_repeat"])
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.error(f"Checkbox language error / Ошибка языка чекбоксов / Помилка мови чекбоксів: {e}")

        menu_btns = [self.btn_gen, self.btn_name_gen, self.btn_copy, self.btn_save, self.btn_open,
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_hibp,
                     self.btn_upd, self.btn_settings, self.btn_about]
        for btn in menu_btns:
            if btn and btn.winfo_exists():
                try:
                    if hasattr(btn, 'icon') and btn.icon:
                        display_text = f" {btn.icon}   {L[btn.lang_key]}"
                    else:
                        display_text = f"   {L[btn.lang_key]}"

                    btn.configure(text=display_text)

                    if btn.lang_key in self._tooltips and self._tooltips[btn.lang_key]:
                        tt_text = L[btn.tt_key]
                        if btn.tt_key == "tt_copy":
                            tt_text = tt_text.format(self.clipboard_timeout)
                        self._tooltips[btn.lang_key].set_text(tt_text)
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Menu button language error / Ошибка языка кнопки меню / Помилка мови кнопки меню: {e}")

        if "btn_eye" in self._tooltips and self._tooltips["btn_eye"]:
            try:
                self._tooltips["btn_eye"].set_text(L.get("tt_eye", "Show / hide password / Показать / скрыть пароль / Показати / приховати пароль"))
            except (AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Eye tooltip error / Ошибка подсказки кнопки глаза / Помилка підказки кнопки ока: {e}")

        if hasattr(self, 'btn_eye') and self.btn_eye and self.btn_eye.winfo_exists():
            try:
                if self.hide_var.get():
                    self.btn_eye.configure(text=L.get("btn_eye_closed", ""))
                else:
                    self.btn_eye.configure(text=L.get("btn_eye", ""))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Eye button language update error / Ошибка обновления языка кнопки глаза / Помилка оновлення мови кнопки ока: {e}")

        try:
            self.title(L["win_title"])
        except (tk.TclError, KeyError, RuntimeError) as e:
            logger.error(f"Window title error / Ошибка заголовка окна / Помилка заголовка вікна: {e}")

        if self.entry_res.get():
            self._update_strength_meter(self.entry_res.get())

        self._update_master_status_label()
        self._update_auto_lock_label()

        if hasattr(self, 'auto_save_btn') and self.auto_save_btn and self.auto_save_btn.winfo_exists():
            if self.auto_save_var.get():
                self.auto_save_btn.configure(text=L.get("auto_save_on", "On / Вкл / Увімк"))
            else:
                self.auto_save_btn.configure(text=L.get("auto_save_off", "Off / Выкл / Вимк"))

        if self._auto_lock_btn and self._auto_lock_btn.winfo_exists():
            if self.auto_lock_enabled.get():
                self._auto_lock_btn.configure(text=L["auto_lock"])
            else:
                self._auto_lock_btn.configure(text=L["auto_lock"])

        if self._sound_btn and self._sound_btn.winfo_exists():
            if self.sound_enabled.get():
                self._sound_btn.configure(text=L["sound_on"])
            else:
                self._sound_btn.configure(text=L["sound_off"])

        if self._clip_timeout_label_ref and self._clip_timeout_label_ref.winfo_exists():
            self._clip_timeout_label_ref.configure(text=L["clip_timeout"].format(self.clipboard_timeout))

        # 2FA LANGUAGE UPDATE
        # 2FA ОБНОВЛЕНИЕ ЯЗЫКА
        # 2FA ОНОВЛЕННЯ МОВИ
        if hasattr(self, '_2fa_indicator_label') and self._2fa_indicator_label and self._2fa_indicator_label.winfo_exists():
            try:
                if self.config.is_2fa_enabled():
                    self._2fa_indicator_label.configure(
                        text=L.get("2fa_status_enabled", "2FA Enabled / 2FA Включена / 2FA Увімкнено"),
                        text_color="#2ECC71"
                    )
                else:
                    self._2fa_indicator_label.configure(
                        text=L.get("2fa_status_disabled", "2FA Disabled / 2FA Отключена / 2FA Вимкнено"),
                        text_color="#888888"
                    )
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"2FA indicator language update error / Ошибка обновления языка индикатора 2FA / Помилка оновлення мови індикатора 2FA: {e}")

        if self.settings_window and self.settings_window.winfo_exists():
            self._update_settings_window_language()

    def _update_settings_window_language(self) -> None:
        """
        Update language in open settings window without reopening

        Обновляет язык в открытом окне настроек без переоткрытия
        Оновлює мову у відкритому вікні налаштувань без перевідкриття
        """
        if not self.settings_window or not self.settings_window.winfo_exists():
            return

        L = LANGUAGES[self.current_lang]

        # Update window title
        # Обновляем заголовок окна
        # Оновлюємо заголовок вікна
        try:
            self.settings_window.title(L["settings_title"])
        except (tk.TclError, AttributeError, RuntimeError):
            pass

        # Update tab buttons
        # Обновляем кнопки вкладок
        # Оновлюємо кнопки вкладок
        tab_labels = {
            "design": L.get("tab_design", "Дизайн / Design / Дизайн"),
            "security": L.get("tab_security", "Безопасность / Security / Безпека"),
            "general": L.get("tab_general", "Общие / General / Загальні"),
        }

        if hasattr(self, 'category_buttons') and self.category_buttons:
            for key, btn in self.category_buttons.items():
                if btn and btn.winfo_exists() and key in tab_labels:
                    try:
                        btn.configure(text=tab_labels[key])
                    except (tk.TclError, AttributeError, RuntimeError):
                        pass

        # Update search placeholder
        # Обновляем плейсхолдер поиска
        # Оновлюємо плейсхолдер пошуку
        if hasattr(self, '_search_entry') and self._search_entry:
            try:
                self._search_entry.configure(placeholder_text=" " + L.get("settings_search", "Search settings... / Поиск настроек... / Пошук налаштувань..."))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Update all settings cards
        # Обновляем все карточки настроек
        # Оновлюємо всі картки налаштувань
        self._update_settings_widgets_text()

    def _update_settings_widgets_text(self) -> None:
        """
        Update text of all widgets in settings window

        Обновляет текст всех виджетов в окне настроек
        Оновлює текст всіх віджетів у вікні налаштувань
        """
        if not self.settings_window or not self.settings_window.winfo_exists():
            return

        L = LANGUAGES[self.current_lang]

        def update_widgets_recursive(widget) -> None:
            try:
                if isinstance(widget, ctk.CTkLabel):
                    current_text = widget.cget("text")
                    if current_text in ["Язык интерфейса", "Interface language", "Мова інтерфейсу"]:
                        widget.configure(text=L["settings_lang"])
                    elif current_text in ["Тема оформления", "Appearance theme", "Тема оформлення"]:
                        widget.configure(text=L["settings_theme"])
                    elif current_text in ["RGB-подсветка", "RGB border", "RGB-підсвітка"]:
                        widget.configure(text=L["rgb_label"])
                    elif current_text in ["Скорость RGB", "RGB Speed", "Швидкість RGB"]:
                        widget.configure(text=L.get("rgb_speed", "RGB Speed / Скорость RGB / Швидкість RGB"))
                    elif current_text in ["Толщина RGB", "RGB Width", "Товщина RGB"]:
                        widget.configure(text=L.get("rgb_width", "RGB Width / Толщина RGB / Товщина RGB"))
                    elif current_text in ["Размер шрифта", "Font size", "Розмір шрифту"]:
                        widget.configure(text=L.get("font_size", "Font size / Размер шрифта / Розмір шрифту"))
                    elif current_text in ["Закругление углов", "Corner radius", "Закруглення кутів"]:
                        widget.configure(text=L["settings_radius"])
                    elif current_text in ["Безопасность", "Security"]:
                        widget.configure(text=L["security"])
                    elif current_text in ["Общие", "General"]:
                        widget.configure(text=L.get("tab_general", "General / Общие / Загальні"))
                    elif "Мастер-пароль" in current_text or "Master password" in current_text or "Майстер-пароль" in current_text:
                        widget.configure(text=L["master_title"])
                    elif current_text in ["Автоблокировка", "Auto lock", "Автоблокування"]:
                        widget.configure(text=L["auto_lock"])
                    elif current_text in ["Звук приложения", "App sound", "Звук програми"]:
                        widget.configure(text=L["settings_sound"])
                    elif current_text in ["Автосохранение", "Auto save", "Автозбереження"]:
                        widget.configure(text=L.get("auto_save_label", "Auto save / Автосохранение / Автозбереження"))
                    elif current_text in ["Закрыть", "Close", "Закрити"]:
                        widget.configure(text=L["close"])
                    elif "Двухфакторная" in current_text or "Two-Factor" in current_text or "Двофакторна" in current_text:
                        widget.configure(text=L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"))

                elif isinstance(widget, ctk.CTkButton):
                    current_text = widget.cget("text")
                    if current_text in ["RU", "EN", "UA"]:
                        pass
                    elif current_text in ["Системная", "System", "Системна"]:
                        widget.configure(text=L["theme_sys"])
                    elif current_text in ["Светлая", "Light", "Світла"]:
                        widget.configure(text=L["theme_light"])
                    elif current_text in ["Тёмная", "Dark", "Темна"]:
                        widget.configure(text=L["theme_dark"])
                    elif current_text in ["Вкл", "On", "Уві"]:
                        widget.configure(text=L["rgb_on"])
                    elif current_text in ["Выкл", "Off", "Вим"]:
                        widget.configure(text=L["rgb_off"])
                    elif current_text in ["Медленная", "Slow", "Повільна"]:
                        widget.configure(text=L.get("rgb_speed_slow", "Slow / Медленная / Повільна"))
                    elif current_text in ["Нормальная", "Normal", "Нормальна"]:
                        widget.configure(text=L.get("rgb_speed_normal", "Normal / Нормальная / Нормальна"))
                    elif current_text in ["Быстрая", "Fast", "Швидка"]:
                        widget.configure(text=L.get("rgb_speed_fast", "Fast / Быстрая / Швидка"))
                    elif current_text in ["Тонкая", "Thin", "Тонка"]:
                        widget.configure(text=L.get("rgb_width_thin", "Thin / Тонкая / Тонка"))
                    elif current_text in ["Средняя", "Normal", "Середня"]:
                        widget.configure(text=L.get("rgb_width_normal", "Normal / Средняя / Середня"))
                    elif current_text in ["Толстая", "Thick", "Товста"]:
                        widget.configure(text=L.get("rgb_width_thick", "Thick / Толстая / Товста"))
                    elif current_text in ["Установить мастер-пароль", "Set master password", "Встановити майстер-пароль"]:
                        if MasterPassword.is_set():
                            widget.configure(text=L["master_btn_remove"])
                        else:
                            widget.configure(text=L["master_btn_set"])
                    elif current_text in ["Удалить мастер-пароль", "Remove master password", "Видалити майстер-пароль"]:
                        if MasterPassword.is_set():
                            widget.configure(text=L["master_btn_remove"])
                        else:
                            widget.configure(text=L["master_btn_set"])
                    elif "Автоблокировка" in current_text or "Auto lock" in current_text or "Автоблокування" in current_text:
                        if self.auto_lock_enabled.get():
                            widget.configure(text=L["auto_lock"])
                        else:
                            widget.configure(text=L["auto_lock"])
                    elif current_text in ["Сохранить текущий пароль", "Save current password", "Зберегти поточний пароль"]:
                        widget.configure(text=L["db_save_current"])
                    elif "Очистка буфера:" in current_text or "Clipboard clear:" in current_text or "Очищення буфера:" in current_text:
                        widget.configure(text=L["clip_timeout"].format(self.clipboard_timeout))
                    elif current_text in ["2FA Settings", "Настройки 2FA", "Налаштування 2FA"]:
                        widget.configure(text=L.get("2fa_settings_title", "2FA Settings / Настройки 2FA / Налаштування 2FA"))

                for child in widget.winfo_children():
                    update_widgets_recursive(child)

            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Widget update error / Ошибка обновления виджета / Помилка оновлення віджета: {e}")

        try:
            update_widgets_recursive(self.settings_window)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Settings widgets update error / Ошибка обновления виджетов настроек / Помилка оновлення віджетів налаштувань: {e}")
