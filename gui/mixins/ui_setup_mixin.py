from __future__ import annotations
"""
Ui setup mixin module for Secure Pass Pro.
Модуль Ui setup mixin для Secure Pass Pro.
Модуль Ui setup mixin для Secure Pass Pro.
"""
"""
Ui setup mixin module for Secure Pass Pro.
Модуль Ui setup mixin для Secure Pass Pro.
Модуль Ui setup mixin для Secure Pass Pro.
"""
import os
import json
"""
UI Setup mixin for SecurePassPro

Миксин настройки интерфейса для SecurePassPro
Міксин налаштування інтерфейсу для SecurePassPro

FIXED: Removed recursive _reopen_settings_window calls
FIXED: Simplified theme and language switching
FIXED #EX: Replaced broad Exception with specific exceptions

Исправлено: Удалены рекурсивные вызовы _reopen_settings_window
Исправлено: Упрощено переключение темы и языка
Исправлено #EX: Заменены общие Exception на конкретные исключения

Виправлено: Видалено рекурсивні виклики _reopen_settings_window
Виправлено: Спрощено перемикання теми та мови
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
import tkinter as tk
import customtkinter as ctk
import webbrowser
from gui.widgets import ToolTip
from utils.helpers import (
    set_global_radius,
    play_sound,
    is_windows,
    is_linux,
    get_system_scaling,
    is_wayland,
    get_linux_desktop_environment,
    center_window_relative
)
from utils.paths import get_config_dir, get_config_file
from Langs.lang import LANGUAGES
from security.master import MasterPassword
from utils.logger import get_logger
from gui.mixins.dialogs_helpers import _get_colors_for_theme as _get_colors_for_theme_func

logger = get_logger("ui_setup")

CONFIG_DIR = get_config_dir()
CONFIG_FILE = get_config_file()

class UISetupMixin:
    """Mixin class for UI setup, theming, and window management
    Класс-миксин для настройки интерфейса, темизации и управления окнами
    Клас-міксин для налаштування інтерфейсу, тематизації та керування вікнами"""

    def _get_actual_theme(self) -> str:
        """Get actual theme (light/dark) / Получить актуальную тему (light/dark) / Отримати актуальну тему (light/dark)"""
        if self.current_theme == "Light":
            return "light"
        if self.current_theme == "Dark":
            return "dark"
        if is_windows():
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "light" if value == 1 else "dark"
            except (ImportError, OSError, WindowsError, TypeError, ValueError) as e:
                logger.debug(f"Theme detection error / Ошибка определения темы / Помилка визначення теми: {e}")
        return "dark"

    def _get_colors_for_theme(self, theme: str) -> dict:
        """Return colors for theme / Возвращает цвета для темы / Повертає кольори для теми"""
        return _get_colors_for_theme_func(theme)
        return {"bg": "#1d1e1e", "fg": "#FFFFFF", "entry_bg": "#2b2b2b", "label_text": "#FFFFFF", "button_fg": "#1f538d"}

    def _apply_theme_colors(self, actual_theme: str) -> None:
        """Apply theme colors to all widgets
        Применяет цвета темы ко всем виджетам
        Застосовує кольори теми до всіх віджетів"""
        if actual_theme == "light":
            bg_main, fg_main, entry_bg = "#F3F3F3", "#000000", "#FFFFFF"
            panel_bg, _, checkmark_color = "#F3F3F3", "#d0d0d0", "#1f538d"
        else:
            bg_main, fg_main, entry_bg = "#1d1e1e", "#FFFFFF", "#2b2b2b"
            panel_bg, _, checkmark_color = "#1d1e1e", "#3a3a3a", "#4EC9B0"

        try:
            self.configure(fg_color=bg_main)
            self.left_panel.configure(fg_color=panel_bg)
            self.right_panel.configure(fg_color=panel_bg)
            self.entry_res.configure(fg_color=entry_bg, text_color=fg_main)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Theme color application error / Ошибка применения цветов темы / Помилка застосування кольорів теми: {e}")

        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb, self.cb_ambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            if cb and cb.winfo_exists():
                try:
                    cb.configure(fg_color=panel_bg, text_color=fg_main, checkmark_color=checkmark_color)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Checkbox color error / Ошибка цвета чекбокса / Помилка кольору чекбокса: {e}")

        try:
            self.lbl_title.configure(text_color=fg_main)
            self.lbl_author.configure(text_color=fg_main)
            self.lbl_len.configure(text_color=fg_main)
            self.lbl_strength.configure(text_color=fg_main)
            self.lbl_strength_text.configure(text_color=fg_main)
            self.lbl_crack.configure(text_color=fg_main)
            self.lbl_menu.configure(text_color=fg_main)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Label color error / Ошибка цвета метки / Помилка кольору мітки: {e}")

        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            if c:
                try:
                    c.configure(bg=bg_main)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Canvas color error / Ошибка цвета canvas / Помилка кольору canvas: {e}")

        self._update_rgb_speed_buttons()
        self._update_rgb_width_buttons()

    def _apply_lang(self, lang: str) -> None:
        """Full UI language update / Полное обновление языка интерфейса / Повне оновлення мови інтерфейсу"""
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

        # Update eye button text / Обновляем текст кнопки глаза / Оновлюємо текст кнопки ока
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

        # 2FA LANGUAGE UPDATE / 2FA ОБНОВЛЕНИЕ ЯЗЫКА / 2FA ОНОВЛЕННЯ МОВИ
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

        # FIXED: Update settings window in place if open, without recursion
        if self.settings_window and self.settings_window.winfo_exists():
            self._update_settings_window_language()

    def _update_settings_window_language(self) -> None:
        """Update language in open settings window without reopening
        Обновляет язык в открытом окне настроек без переоткрытия
        Оновлює мову у відкритому вікні налаштувань без перевідкриття"""
        if not self.settings_window or not self.settings_window.winfo_exists():
            return

        L = LANGUAGES[self.current_lang]

        # Update window title
        try:
            self.settings_window.title(L["settings_title"])
        except (tk.TclError, AttributeError, RuntimeError):
            pass

        # Update tab buttons
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
        if hasattr(self, '_search_entry') and self._search_entry:
            try:
                self._search_entry.configure(placeholder_text=" " + L.get("settings_search", "Search settings... / Поиск настроек... / Пошук налаштувань..."))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Update all settings cards
        self._update_settings_widgets_text()

    def _update_settings_widgets_text(self) -> None:
        """Update text of all widgets in settings window
        Обновляет текст всех виджетов в окне настроек
        Оновлює текст всіх віджетів у вікні налаштувань"""
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

    def _center_main_window(self) -> None:
        """Center main window on screen
        Центрирует главное окно на экране
        Центрує головне вікно на екрані"""
        try:
            self.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (950 // 2)
            y = (self.winfo_screenheight() // 2) - (800 // 2)
            self.geometry(f"950x800+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Main window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            self.geometry("950x800")

    def _center_window_relative_to_parent(self, window, width: int, height: int) -> None:
        """Center window relative to parent - uses shared helper
        Центрирует окно относительно родителя - использует общий вспомогательный метод
        Центрує вікно відносно батька - використовує загальний допоміжний метод"""
        center_window_relative(self, window, width, height)

    def _setup_ui(self) -> None:
        """Create UI / Создание интерфейса / Створення інтерфейсу"""
        try:
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self.grid_rowconfigure(0, weight=1)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Grid configuration error / Ошибка сетки / Помилка сітки: {e}")

        try:
            self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

            self.lbl_title = ctk.CTkLabel(self.left_panel, text="Secure Pass Pro v4.0", font=("Segoe UI", 20, "bold"))
            self.lbl_title.pack(pady=(5, 0))
            self.lbl_author = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "italic"), text_color="gray")
            self.lbl_author.pack(pady=(0, 10))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Left panel setup error / Ошибка левой панели / Помилка лівої панелі: {e}")

        # 2FA INDICATOR / 2FA ИНДИКАТОР / 2FA ІНДИКАТОР
        try:
            self._2fa_indicator_label = ctk.CTkLabel(
                self.left_panel,
                text="",
                font=("Segoe UI", 11),
                text_color="#888888"
            )
            self._2fa_indicator_label.pack(pady=(0, 5))
            self.after(100, self._update_2fa_indicator)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"2FA indicator setup error / Ошибка индикатора 2FA / Помилка індикатора 2FA: {e}")

        # ========== CHECKBOXES - ORIGINAL LAYOUT, ONLY TEXT ALIGNMENT FIXED ==========
        try:
            self.cb_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
            self.cb_frame.pack(pady=10)

            # ORIGINAL POSITIONS - DO NOT CHANGE
            self.cb_upper = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.upper_var,
                                            border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_upper.grid(row=0, column=1, padx=(70, 20), pady=6, sticky="w")

            self.cb_lower = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.lower_var,
                                            border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_lower.grid(row=0, column=0, padx=(20, 70), pady=6, sticky="w")

            self.cb_digits = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.digits_var,
                                             border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_digits.grid(row=1, column=1, padx=(70, 20), pady=6, sticky="w")

            self.cb_symb = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.symb_var,
                                           border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_symb.grid(row=1, column=0, padx=(20, 70), pady=6, sticky="w")

            self.cb_ambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.ambig_var,
                                            border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            self.cb_at_least = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.at_least_var,
                                               border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            self.cb_hide = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.hide_var,
                                           command=self._toggle_hide, border_color="#4EC9B0",
                                           hover_color="#4EC9B0")
            self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            self.cb_no_repeat = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.no_repeat_var,
                                                             border_color="#4EC9B0", hover_color="#4EC9B0")
            self.cb_no_repeat.grid(row=6, column=0, columnspan=2, padx=20, pady=8, sticky="w")

        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Checkbox setup error / Ошибка чекбоксов / Помилка чекбоксів: {e}")

        # ========== LENGTH SLIDER — под чекбоксами, над полем пароля ==========
        try:
            self.lbl_len = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 16, "bold"))
            self.lbl_len.pack(pady=(10, 0))
            self.slider_len = ctk.CTkSlider(self.left_panel, from_=4, to=64, number_of_steps=60, width=400, command=self._update_len_label)
            self.slider_len.set(20)
            self.slider_len.pack(pady=(4, 0))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Slider setup error / Ошибка слайдера / Помилка слайдера: {e}")

        try:
            self.entry_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
            self.entry_frame.pack(pady=15, padx=40, fill="x")
            self.entry_res = ctk.CTkEntry(self.entry_frame, height=50, font=("Consolas", 22), justify="center", corner_radius=self.current_radius)
            self.entry_res.pack(side="left", fill="x", expand=True)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Entry setup error / Ошибка поля ввода / Помилка поля введення: {e}")

        # Eye button with emoji from lang.py / Кнопка глаза с эмодзи из lang.py / Кнопка ока з емодзі з lang.py
        try:
            L = LANGUAGES[self.current_lang]
            self.btn_eye = ctk.CTkButton(self.entry_frame, text=L.get("btn_eye", ""), width=50, height=50,
                                         font=("Segoe UI", 20), fg_color="#3a3a3a", hover_color="#555555",
                                         corner_radius=self.current_radius, command=self._toggle_eye)
            self.btn_eye.pack(side="left", padx=(6, 0))
            self._tooltips["btn_eye"] = ToolTip(self.btn_eye)
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Eye button setup error / Ошибка кнопки глаза / Помилка кнопки ока: {e}")

        try:
            self.lbl_stars_top = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 24))
            self.lbl_stars_top.pack(pady=(5, 0))
            self.lbl_strength_text = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "bold"))
            self.lbl_strength_text.pack()
            self.lbl_strength = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13))
            self.lbl_strength.pack()
            self.lbl_crack = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13, "bold"), wraplength=500)
            self.lbl_crack.pack(pady=(0, 5))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Strength indicators setup error / Ошибка индикаторов силы / Помилка індикаторів сили: {e}")

        # Right panel with scroll / Правая панель со скроллом / Права панель зі скролом
        try:
            self.right_panel = ctk.CTkScrollableFrame(self, width=280)
            self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

            self.lbl_menu = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 18, "bold"))
            self.lbl_menu.pack(pady=15)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Right panel setup error / Ошибка правой панели / Помилка правої панелі: {e}")

        # Pass empty strings "" instead of emoji icons to icon argument
        try:
            self.btn_gen = self._create_menu_btn(self.right_panel, "btn_gen", "tt_gen", self._generate, "#00C853", "")
            self.btn_name_gen = self._create_menu_btn(self.right_panel, "btn_name_gen", "tt_name_gen", self._open_name_generator, "#E91E63", "")
            self.btn_copy = self._create_menu_btn(self.right_panel, "btn_copy", "tt_copy", self._copy, "#00B0F0", "")
            self.btn_save = self._create_menu_btn(self.right_panel, "btn_save", "tt_save", self._save, "#9C27B0", "")
            self.btn_open = self._create_menu_btn(self.right_panel, "btn_open", "tt_open", self._open, "#FF9800", "")
            self.btn_qr = self._create_menu_btn(self.right_panel, "btn_qr", "tt_qr", self._show_qr, "#E91E63", "")
            self.btn_hist = self._create_menu_btn(self.right_panel, "btn_hist", "tt_hist", self._show_history, "#FFC107", "")
            self.btn_db = self._create_menu_btn(self.right_panel, "btn_db", "tt_db", self._show_db_window, "#2196F3", "")
            self.btn_hibp = self._create_menu_btn(self.right_panel, "btn_hibp", "tt_hibp", self._check_hibp, "#FF5722", "")
            self.btn_upd = self._create_menu_btn(self.right_panel, "btn_upd", "tt_upd", self._open_update_url, "#009688", "")
            self.btn_settings = self._create_menu_btn(self.right_panel, "btn_settings", "tt_settings", self._show_settings, "#607D8B", "")
            self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#455A64", "")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Menu buttons setup error / Ошибка кнопок меню / Помилка кнопок меню: {e}")

        try:
            self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
            self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="", font=("Segoe UI", 20), text_color="#FFD700")
            self.lbl_app_rating.pack(pady=(5, 5))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Bottom frame setup error / Ошибка нижней панели / Помилка нижньої панелі: {e}")

        # ========== LINUX ADAPTATION - additional settings / ЛИНУКС АДАПТАЦИЯ - дополнительная настройка / АДАПТАЦІЯ ДЛЯ LINUX - додаткове налаштування ==========
        if is_linux():
            try:
                scaling = get_system_scaling()
                desktop_env = get_linux_desktop_environment()

                if scaling > 1.0:
                    try:
                        self.lbl_title.configure(font=("Segoe UI", int(20 * min(scaling, 2.0))))
                        self.lbl_menu.configure(font=("Segoe UI", int(18 * min(scaling, 2.0))))
                        self.entry_res.configure(font=("Consolas", int(22 * min(scaling, 2.0))))
                        self.btn_eye.configure(font=("Segoe UI", int(20 * min(scaling, 2.0))))
                    except (tk.TclError, AttributeError, RuntimeError) as e:
                        logger.debug(f"Linux font scaling error / Ошибка масштабирования шрифтов / Помилка масштабування шрифтів: {e}")

                if 'gnome' in desktop_env or 'unity' in desktop_env:
                    try:
                        self.right_panel.configure(scrollbar_button_color="#2d6a4f")
                    except (tk.TclError, AttributeError, RuntimeError):
                        pass
                elif 'kde' in desktop_env or 'plasma' in desktop_env:
                    try:
                        ctk.set_widget_scaling(1.0)
                    except (tk.TclError, AttributeError, RuntimeError):
                        pass

                if is_wayland():
                    try:
                        self.attributes('-type', 'normal')
                    except (tk.TclError, AttributeError, RuntimeError):
                        pass
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Linux adaptation error / Ошибка адаптации Linux / Помилка адаптації Linux: {e}")

    def _update_2fa_indicator(self) -> None:
        """Update 2FA indicator in main window
        Обновляет индикатор 2FA в главном окне
        Оновлює індикатор 2FA в головному вікні"""
        if not hasattr(self, '_2fa_indicator_label') or not self._2fa_indicator_label:
            return

        try:
            L = LANGUAGES[self.current_lang]
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
            logger.debug(f"Update 2FA indicator error / Ошибка обновления 2FA / Помилка оновлення 2FA: {e}")

    def _open_update_url(self) -> None:
        """Open GitHub releases page
        Открыть страницу релизов GitHub
        Відкрити сторінку релізів GitHub"""
        UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"
        try:
            webbrowser.open(UPD_URL)
        except webbrowser.Error as e:
            logger.error(f"Failed to open URL / Не удалось открыть URL / Не вдалося відкрити URL: {e}")

    def _create_menu_btn(self, parent, lang_key: str, tt_key: str, cmd, color: str, icon: str = "") -> ctk.CTkButton:
        """
        Handle create menu btn.
        Обработать create menu btn.
        Обробити create menu btn.
        """
        neon_colors = {
            "#00C853": "#00E676", "#00B0F0": "#4FC3F7", "#9C27B0": "#CE93D8",
            "#FF9800": "#FFB74D", "#E91E63": "#F06292", "#FFC107": "#FFD54F",
            "#2196F3": "#64B5F6", "#009688": "#4DB6AC", "#607D8B": "#90A4AE",
            "#455A64": "#78909C",
        }

        hover = neon_colors.get(color, color)

        btn = ctk.CTkButton(parent, text="", fg_color=color, height=45, border_width=0,
                            font=("Segoe UI", 13, "bold"), hover_color=hover,
                            corner_radius=self.current_radius, anchor="w")

        def animated_cmd() -> None:
            self._animate_button(btn)
            cmd()

        btn.configure(command=animated_cmd)
        btn.pack(pady=6, padx=20, fill="x")
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        btn.icon = icon
        self._tooltips[lang_key] = ToolTip(btn)
        return btn

    def _animate_button(self, btn: ctk.CTkButton) -> None:
        """
        Handle animate button.
        Обработать animate button.
        Обробити animate button.
        """
        play_sound("click", self.sound_enabled.get())

    def _toggle_hide(self) -> None:
        """
        Handle toggle hide.
        Обработать toggle hide.
        Обробити toggle hide.
        """
        self._sync_eye_to_hide_var()

    def _toggle_eye(self) -> None:
        """
        Handle toggle eye.
        Обработать toggle eye.
        Обробити toggle eye.
        """
        self.hide_var.set(not self.hide_var.get())
        self._sync_eye_to_hide_var()

    def _sync_eye_to_hide_var(self) -> None:
        """
        Handle sync eye to hide var.
        Обработать sync eye to hide var.
        Обробити sync eye to hide var.
        """
        hidden = self.hide_var.get()
        L = LANGUAGES[self.current_lang]
        try:
            self.entry_res.configure(show="*" if hidden else "")
            if hidden:
                self.btn_eye.configure(text=L.get("btn_eye_closed", ""))
            else:
                self.btn_eye.configure(text=L.get("btn_eye", ""))
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Eye button sync error / Ошибка синхронизации кнопки глаза / Помилка синхронізації кнопки ока: {e}")

    def _update_button_radius(self, radius: int) -> None:
        """Update radius for all buttons including name generator
        Обновить радиус для всех кнопок включая генератор имён
        Оновити радіус для всіх кнопок включаючи генератор імен"""
        if hasattr(self, 'btn_name_gen') and self.btn_name_gen:
            try:
                self.btn_name_gen.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        try:
            for widget in self.right_panel.winfo_children():
                if isinstance(widget, ctk.CTkButton):
                    widget.configure(corner_radius=radius)
        except (tk.TclError, AttributeError, RuntimeError):
            pass

        try:
            self.entry_res.configure(corner_radius=radius)
            self.btn_eye.configure(corner_radius=radius)
        except (tk.TclError, AttributeError, RuntimeError):
            pass

        if hasattr(self, '_update_name_window_radius'):
            self._update_name_window_radius(radius)

        if hasattr(self, '_update_hibp_window_radius'):
            self._update_hibp_window_radius(radius)

    def _change_radius(self, radius: int) -> None:
        """
        Handle change radius.
        Обработать change radius.
        Обробити change radius.
        """
        self.current_radius = radius
        set_global_radius(radius)
        self._update_button_radius(radius)

    def _on_closing(self) -> None:
        """
        Handle on closing.
        Обработать on closing.
        Обробити on closing.
        """
        self._stop_rgb()
        if self._pulse_animation_id:
            try:
                self.after_cancel(self._pulse_animation_id)
            except (tk.TclError, ValueError, RuntimeError):
                pass
        if self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except (tk.TclError, ValueError, RuntimeError):
                pass
        if self._lock_check_id:
            try:
                self.after_cancel(self._lock_check_id)
            except (tk.TclError, ValueError, RuntimeError):
                pass

        try:
            from storage.database import PasswordDB
            PasswordDB.close_connection()
        except (ImportError, AttributeError, OSError, RuntimeError) as e:
            logger.debug(f"DB close error / Ошибка закрытия БД / Помилка закриття БД: {e}")

        for win_attr in ("settings_window", "about_window", "history_window", "qr_window", "db_window"):
            win = getattr(self, win_attr, None)
            if win is not None:
                try:
                    win.destroy()
                except tk.TclError as e:
                    logger.debug(f"Window destroy error / Ошибка уничтожения окна / Помилка знищення вікна: {e}")
        try:
            self.destroy()
        except (tk.TclError, RuntimeError) as e:
            logger.debug(f"Destroy error / Ошибка уничтожения / Помилка знищення: {e}")

    def _load_all_settings(self) -> None:
        """Load all settings from config file / Загрузить все настройки из файла конфигурации / Завантажити всі налаштування з файлу конфігурації"""
        default_config = {
            "THEME": "Dark",
            "LANG": "RU",
            "SOUND": True,
            "RGB": True,
            "RGB_SPEED": "normal",
            "RGB_WIDTH": "normal",
            "RADIUS": 25,
            "font_size": 14,
            "CLIP_TIMEOUT": 60,
            "AUTO_LOCK": False,
            "AUTO_LOCK_TIMEOUT": 5,
            "auto_save": False
        }

        need_save = False

        if not os.path.exists(CONFIG_FILE):
            need_save = True
            config = default_config.copy()
        else:
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                        need_save = True
            except json.JSONDecodeError as e:
                print(f"[Config] JSON decode error / Ошибка декодирования JSON / Помилка декодування JSON: {e}, using defaults / использование стандартных / використання стандартних")
                config = default_config.copy()
                need_save = True
            except (PermissionError, OSError, IOError) as e:
                print(f"[Config] Error reading config / Ошибка чтения конфига / Помилка читання конфігу: {e}, using defaults / использование стандартных / використання стандартних")
                config = default_config.copy()
                need_save = True

        if need_save:
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except (PermissionError, OSError, IOError) as e:
                print(f"[Config] Cannot save config / Не удаётся сохранить конфиг / Не вдається зберегти конфіг: {e}")

        self.config.update(config)

        self.current_theme = config.get("THEME", "Dark")
        self.current_lang = config.get("LANG", "RU")
        self.sound_enabled.set(config.get("SOUND", True))
        self.rgb_enabled.set(config.get("RGB", True))

        self.rgb_speed_setting = config.get("RGB_SPEED", "normal")
        if self.rgb_speed_setting not in ["slow", "normal", "fast"]:
            self.rgb_speed_setting = "normal"

        self.rgb_width_setting = config.get("RGB_WIDTH", "normal")
        if self.rgb_width_setting not in ["thin", "normal", "thick"]:
            self.rgb_width_setting = "normal"

        self.current_radius = config.get("RADIUS", 25)
        self.current_font_size = config.get("font_size", 14)
        self.clipboard_timeout = config.get("CLIP_TIMEOUT", 60)
        self.auto_lock_enabled.set(config.get("AUTO_LOCK", False))
        self.auto_lock_timeout = config.get("AUTO_LOCK_TIMEOUT", 5)
        self.auto_save_var.set(config.get("auto_save", False))

        set_global_radius(self.current_radius)
        self._change_radius(self.current_radius)
        self._apply_font_size(self.current_font_size)

        actual_theme = self._get_actual_theme()
        try:
            ctk.set_appearance_mode(self.current_theme)
        except (ValueError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to set appearance mode / Ошибка установки режима оформления / Помилка встановлення режиму оформлення: {e}")
        self.after(50, lambda: self._apply_theme_colors(actual_theme))
        self.after(60, lambda: self.configure(fg_color="#F3F3F3" if actual_theme == "light" else "#1d1e1e"))

        if self.rgb_enabled.get():
            self.after(200, self._start_rgb)

        self._update_master_status_label()
        self._update_auto_lock_label()
        self._update_rgb_speed_buttons()
        self._update_rgb_width_buttons()

        # 2FA UPDATE / 2FA ОБНОВЛЕНИЕ / 2FA ОНОВЛЕННЯ
        self._update_2fa_indicator()

        self._apply_lang(self.current_lang)
