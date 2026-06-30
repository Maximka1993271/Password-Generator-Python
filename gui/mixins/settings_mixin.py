"""
Settings mixin for SecurePassPro

Миксин настроек для SecurePassPro
Міксин налаштувань для SecurePassPro

FIXED: Fixed theme switching to prevent recursion and freezing - SIMPLIFIED APPROACH
FIXED #C7: Moved set_global_radius import to module level
FIXED #EX: Replaced broad Exception with specific exceptions
FIXED: CTkMessageBox theme now updates dynamically when changing theme/language

Исправлено: Исправлено переключение темы для предотвращения рекурсии и зависания - УПРОЩЁННЫЙ ПОДХОД
Исправлено #C7: Импорт set_global_radius перемещён на уровень модуля
Исправлено #EX: Заменены общие Exception на конкретные исключения
Исправлено: Тема CTkMessageBox теперь динамически обновляется при смене темы/языка

Виправлено: Виправлено перемикання теми для запобігання рекурсії та зависання - СПРОЩЕНИЙ ПІДХІД
Виправлено #C7: Імпорт set_global_radius переміщено на рівень модуля
Виправлено #EX: Замінено загальні Exception на конкретні винятки
Виправлено: Тема CTkMessageBox тепер динамічно оновлюється при зміні теми/мови
"""
from __future__ import annotations
import tkinter as tk
import time
import customtkinter as ctk
from Langs.lang import LANGUAGES
from utils.helpers import set_global_radius, play_sound
from gui.dialogs import CTkMessageBox
from utils.logger import get_logger
from core.app_settings import AppSettings, Key  # centralised settings

logger = get_logger("settings")


class SettingsMixin:
    """
    Mixin class for application settings (theme, language, fonts, etc.)

    Класс-миксин для настроек приложения (тема, язык, шрифты и т.д.)
    Клас-міксин для налаштувань додатку (тема, мова, шрифти тощо)
    """

    def _update_messagebox_theme(self) -> None:
        """
        Update CTkMessageBox theme when main theme changes

        Обновляет тему CTkMessageBox при смене основной темы
        Оновлює тему CTkMessageBox при зміні основної теми
        """
        try:
            from gui.dialogs import CTkMessageBox
            actual_theme = "light" if self.current_theme == "Light" else "dark"
            CTkMessageBox.set_theme(actual_theme)
            CTkMessageBox.set_lang(self.current_lang)
            logger.debug(f"MessageBox theme updated to: {actual_theme}")
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug(f"Failed to update MessageBox theme: {e}")

    def _change_radius(self, val: int) -> None:
        """
        Change corner radius for all UI elements

        Изменяет скругление углов для всех элементов UI
        Змінює заокруглення кутів для всіх елементів UI
        """
        rad = int(val)
        self.current_radius = rad
        set_global_radius(rad)

        # Update buttons in main window / Обновляем кнопки в главном окне / Оновлюємо кнопки в головному вікні
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open,
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_hibp,
                     self.btn_upd, self.btn_settings, self.btn_about, self.btn_name_gen]
        for btn in menu_btns:
            if btn and btn.winfo_exists():
                try:
                    btn.configure(corner_radius=rad)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Button radius error / Ошибка радиуса кнопки / Помилка радіусу кнопки: {e}")

        if self.btn_eye and self.btn_eye.winfo_exists():
            try:
                self.btn_eye.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Eye button radius error / Ошибка радиуса кнопки глаза / Помилка радіусу кнопки ока: {e}")

        # Update checkboxes (they have fixed radius of 6) / Обновляем чекбоксы (у них фиксированный радиус 6) / Оновлюємо чекбокси (у них фіксований радіус 6)
        CHECKBOX_RADIUS = 6
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
                   self.cb_ambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            if cb and cb.winfo_exists():
                try:
                    cb.configure(corner_radius=CHECKBOX_RADIUS)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Checkbox radius error / Ошибка радиуса чекбокса / Помилка радіусу чекбокса: {e}")

        # Update frames / Обновляем фреймы / Оновлюємо фрейми
        if self.bottom_frame and self.bottom_frame.winfo_exists():
            try:
                self.bottom_frame.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Bottom frame radius error / Ошибка радиуса нижней рамки / Помилка радіусу нижньої рамки: {e}")

        if self.right_panel and self.right_panel.winfo_exists():
            try:
                self.right_panel.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Right panel radius error / Ошибка радиуса правой панели / Помилка радіусу правої панелі: {e}")

        if self.entry_res and self.entry_res.winfo_exists():
            try:
                self.entry_res.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Entry radius error / Ошибка радиуса поля ввода / Помилка радіусу поля введення: {e}")

        if self.entry_frame and self.entry_frame.winfo_exists():
            try:
                self.entry_frame.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Entry frame radius error / Ошибка радиуса рамки поля ввода / Помилка радіусу рамки поля введення: {e}")

        # Update radius label in settings / Обновляем метку радиуса в настройках / Оновлюємо мітку радіусу в налаштуваннях
        if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
            try:
                self.settings_radius_label.configure(text=f"{rad} px")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Radius label error / Ошибка метки радиуса / Помилка мітки радіусу: {e}")

        self._update_settings_radius()

        # Save to config / Сохраняем в конфиг / Зберігаємо в конфіг
        try:
            self.config.set("RADIUS", rad)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save radius / Ошибка сохранения радиуса / Помилка збереження радіусу: {e}")

    def _update_settings_radius(self) -> None:
        """
        Update radius for settings window buttons

        Обновляет радиус для кнопок окна настроек
        Оновлює радіус для кнопок вікна налаштувань
        """
        rad = self.current_radius
        # Update language buttons / Обновляем кнопки языков / Оновлюємо кнопки мов
        for btn in self.lang_buttons.values():
            if btn and btn.winfo_exists():
                try:
                    btn.configure(corner_radius=rad)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Lang button radius error / Ошибка радиуса кнопки языка / Помилка радіусу кнопки мови: {e}")

        # Update theme buttons / Обновляем кнопки темы / Оновлюємо кнопки теми
        for btn in self.theme_buttons.values():
            if btn and btn.winfo_exists():
                try:
                    btn.configure(corner_radius=rad)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Theme button radius error / Ошибка радиуса кнопки темы / Помилка радіусу кнопки теми: {e}")

        # Update other buttons / Обновляем остальные кнопки / Оновлюємо інші кнопки
        for btn in [self._sound_btn, self._close_btn, self._master_set_btn,
                    self._rgb_on_btn_ref, self._rgb_off_btn_ref, self._auto_lock_btn,
                    self.auto_save_btn]:
            if btn and btn.winfo_exists():
                try:
                    btn.configure(corner_radius=rad)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Settings button radius error / Ошибка радиуса кнопки настроек / Помилка радіусу кнопки налаштувань: {e}")

        # Update PDF theme buttons / Обновляем кнопки темы PDF / Оновлюємо кнопки теми PDF
        if hasattr(self, 'pdf_theme_light_btn') and self.pdf_theme_light_btn and self.pdf_theme_light_btn.winfo_exists():
            try:
                self.pdf_theme_light_btn.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"PDF theme light button radius error / Ошибка радиуса кнопки светлой темы PDF / Помилка радіусу кнопки світлої теми PDF: {e}")

        if hasattr(self, 'pdf_theme_dark_btn') and self.pdf_theme_dark_btn and self.pdf_theme_dark_btn.winfo_exists():
            try:
                self.pdf_theme_dark_btn.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"PDF theme dark button radius error / Ошибка радиуса кнопки тёмной темы PDF / Помилка радіусу кнопки темної теми PDF: {e}")

        # 2FA button / 2FA КНОПКА / 2FA КНОПКА
        if hasattr(self, '_2fa_settings_btn') and self._2fa_settings_btn and self._2fa_settings_btn.winfo_exists():
            try:
                self._2fa_settings_btn.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"2FA button radius error / Ошибка радиуса кнопки 2FA / Помилка радіусу кнопки 2FA: {e}")

    def _apply_font_size(self, size: int) -> None:
        """
        Apply font size to all UI elements

        Применяет размер шрифта ко всем элементам UI
        Застосовує розмір шрифту до всіх елементів UI
        """
        self.current_font_size = size
        try:
            self.config.set("font_size", size)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save font size / Ошибка сохранения размера шрифта / Помилка збереження розміру шрифту: {e}")

        # Update menu buttons / Обновляем кнопки меню / Оновлюємо кнопки меню
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open,
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_hibp,
                     self.btn_upd, self.btn_settings, self.btn_about, self.btn_name_gen]
        for btn in menu_btns:
            if btn and btn.winfo_exists():
                try:
                    btn.configure(font=("Segoe UI", size - 1, "bold"))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Button font error / Ошибка шрифта кнопки / Помилка шрифту кнопки: {e}")

        # Update headers / Обновляем заголовки / Оновлюємо заголовки
        if self.lbl_title and self.lbl_title.winfo_exists():
            try:
                self.lbl_title.configure(font=("Segoe UI", size + 6, "bold"))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Title font error / Ошибка шрифта заголовка / Помилка шрифту заголовка: {e}")

        if self.lbl_menu and self.lbl_menu.winfo_exists():
            try:
                self.lbl_menu.configure(font=("Segoe UI", size + 4, "bold"))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Menu font error / Ошибка шрифта меню / Помилка шрифту меню: {e}")

        if self.lbl_strength_text and self.lbl_strength_text.winfo_exists():
            try:
                self.lbl_strength_text.configure(font=("Segoe UI", size, "bold"))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Strength font error / Ошибка шрифта индикатора стойкости / Помилка шрифту індикатора стійкості: {e}")

        # Update password entry field / Обновляем поле ввода пароля / Оновлюємо поле введення пароля
        if self.entry_res and self.entry_res.winfo_exists():
            try:
                self.entry_res.configure(font=("Consolas", size + 8))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Entry font error / Ошибка шрифта поля ввода / Помилка шрифту поля введення: {e}")

        # Update eye button / Обновляем кнопку глаза / Оновлюємо кнопку ока
        if self.btn_eye and self.btn_eye.winfo_exists():
            try:
                self.btn_eye.configure(font=("Segoe UI", size + 6))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Eye button font error / Ошибка шрифта кнопки глаза / Помилка шрифту кнопки ока: {e}")

        # Update font size label in settings / Обновляем метку размера шрифта в настройках / Оновлюємо мітку розміру шрифту в налаштуваннях
        if hasattr(self, 'font_size_value') and self.font_size_value and self.font_size_value.winfo_exists():
            try:
                self.font_size_value.configure(font=("Segoe UI", size + 4, "bold"))
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Font size value label error / Ошибка метки значения размера шрифта / Помилка мітки значення розміру шрифту: {e}")

    def _on_font_size_change(self, val: float) -> None:
        """
        Handle font size slider change

        Обрабатывает изменение слайдера размера шрифта
        Обробляє зміну повзунка розміру шрифту
        """
        size = int(val)
        if hasattr(self, 'font_size_value') and self.font_size_value and self.font_size_value.winfo_exists():
            try:
                self.font_size_value.configure(text=f"{size}px")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Font size label error / Ошибка метки размера шрифта / Помилка мітки розміру шрифту: {e}")

        # Apply instantly / Применяем мгновенно / Застосовуємо миттєво
        self._apply_font_size(size)

    def _on_radius_change(self, val: float) -> None:
        """
        Handle radius slider change

        Обрабатывает изменение слайдера радиуса
        Обробляє зміну повзунка радіусу
        """
        rad = int(val)
        if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
            try:
                self.settings_radius_label.configure(text=f"{rad} px")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Radius label error / Ошибка метки радиуса / Помилка мітки радіусу: {e}")

        # Apply instantly / Применяем мгновенно / Застосовуємо миттєво
        self._change_radius(rad)

    def _on_clip_timeout_change(self, val: float) -> None:
        """
        Handle clipboard timeout slider change

        Обрабатывает изменение слайдера таймаута буфера обмена
        Обробляє зміну повзунка таймауту буфера обміну
        """
        seconds = int(val)
        if self._clip_timeout_label_ref and self._clip_timeout_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            try:
                self._clip_timeout_label_ref.configure(text=L["clip_timeout"].format(seconds))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Clip timeout label error / Ошибка метки таймаута буфера / Помилка мітки таймауту буфера: {e}")

        # Apply instantly / Применяем мгновенно / Застосовуємо миттєво
        self._apply_clip_timeout(seconds)

    def _apply_clip_timeout(self, seconds: int) -> None:
        """
        Apply clipboard timeout setting

        Применяет настройку таймаута буфера обмена
        Застосовує налаштування таймауту буфера обміну
        """
        self.clipboard_timeout = seconds
        if "btn_copy" in self._tooltips and self._tooltips["btn_copy"]:
            L = LANGUAGES[self.current_lang]
            try:
                self._tooltips["btn_copy"].set_text(L["tt_copy"].format(seconds))
            except (AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Tooltip error / Ошибка подсказки / Помилка підказки: {e}")
        try:
            self.config.set("CLIP_TIMEOUT", seconds)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save clip timeout / Ошибка сохранения таймаута буфера / Помилка збереження таймауту буфера: {e}")

    def _on_auto_lock_timeout_change(self, val: float) -> None:
        """
        Handle auto-lock timeout slider change

        Обрабатывает изменение слайдера таймаута автоблокировки
        Обробляє зміну повзунка таймауту автоблокування
        """
        minutes = int(val)
        if self._auto_lock_label_ref and self._auto_lock_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            try:
                self._auto_lock_label_ref.configure(text=L["auto_lock_timeout"].format(minutes))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Auto lock label error / Ошибка метки автоблокировки / Помилка мітки автоблокування: {e}")

        # Apply instantly / Применяем мгновенно / Застосовуємо миттєво
        self._apply_auto_timeout(minutes)

    def _apply_auto_timeout(self, minutes: int) -> None:
        """
        Apply auto-lock timeout setting

        Применяет настройку таймаута автоблокировки
        Застосовує налаштування таймауту автоблокування
        """
        self.auto_lock_timeout = minutes
        try:
            self.config.set("AUTO_LOCK_TIMEOUT", minutes)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save auto lock timeout / Ошибка сохранения таймаута автоблокировки / Помилка збереження таймауту автоблокування: {e}")

    def _toggle_sound_settings(self) -> None:
        """
        Toggle sound effects on/off

        Включает/выключает звуковые эффекты
        Увімкнює/вимикає звукові ефекти
        """
        self.sound_enabled.set(not self.sound_enabled.get())
        if self._sound_btn and self._sound_btn.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if self.sound_enabled.get():
                try:
                    self._sound_btn.configure(
                        text=L["sound_on"],
                        fg_color="#2d6a4f",
                        hover_color="#2d6a4f"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Sound button error / Ошибка кнопки звука / Помилка кнопки звуку: {e}")
            else:
                try:
                    self._sound_btn.configure(
                        text=L["sound_off"],
                        fg_color="#8b0000",
                        hover_color="#8b0000"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Sound button error / Ошибка кнопки звука / Помилка кнопки звуку: {e}")
        play_sound("click", self.sound_enabled.get())
        try:
            self.config.set("SOUND", self.sound_enabled.get())
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save sound setting / Ошибка сохранения настройки звука / Помилка збереження налаштування звуку: {e}")

    def _toggle_auto_save(self) -> None:
        """
        Toggle auto-save on/off

        Включает/выключает автосохранение
        Увімкнює/вимикає автозбереження
        """
        new_value = not self.auto_save_var.get()
        self.auto_save_var.set(new_value)
        try:
            self.config.set("auto_save", new_value)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save auto save setting / Ошибка сохранения настройки автосохранения / Помилка збереження налаштування автозбереження: {e}")

        L = LANGUAGES[self.current_lang]
        if new_value:
            if self.auto_save_btn and self.auto_save_btn.winfo_exists():
                try:
                    self.auto_save_btn.configure(
                        text=L["auto_save_on"],
                        fg_color="#2d6a4f",
                        hover_color="#2d6a4f"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Auto save button error / Ошибка кнопки автосохранения / Помилка кнопки автозбереження: {e}")
            CTkMessageBox.info(self, L["auto_save"], L["auto_save_enabled"])
        else:
            if self.auto_save_btn and self.auto_save_btn.winfo_exists():
                try:
                    self.auto_save_btn.configure(
                        text=L["auto_save_off"],
                        fg_color="#8b0000",
                        hover_color="#8b0000"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Auto save button error / Ошибка кнопки автосохранения / Помилка кнопки автозбереження: {e}")
            CTkMessageBox.info(self, L["auto_save"], L["auto_save_disabled"])

    def _change_theme(self, mode: str) -> None:
        """
        Change application theme without freezing.

        Сменить тему приложения без зависания.
        Змінити тему додатку без зависання.
        """
        # Prevent recursive calls / Предотвращаем рекурсивные вызовы / Запобігаємо рекурсивним викликам
        if hasattr(self, '_changing_theme') and self._changing_theme:
            return

        self._changing_theme = True

        try:
            self.current_theme = mode
            
            # Update MessageBox theme
            self._update_messagebox_theme()

            # Save to config / Сохраняем в конфиг / Зберігаємо в конфіг
            try:
                self.config.set("THEME", mode)
            except (KeyError, ValueError, OSError, AttributeError) as e:
                logger.error(f"Failed to save theme / Ошибка сохранения темы / Помилка збереження теми: {e}")

            # Update theme buttons colors only / Обновляем только цвета кнопок темы / Оновлюємо тільки кольори кнопок теми
            for name, btn in self.theme_buttons.items():
                if btn and btn.winfo_exists():
                    try:
                        btn.configure(fg_color="#2d6a4f" if name == mode else "#4b4b4b")
                    except (tk.TclError, AttributeError, RuntimeError) as e:
                        logger.debug(f"Theme button error / Ошибка кнопки темы / Помилка кнопки теми: {e}")

            # Apply theme to customtkinter - this is the main action
            try:
                ctk.set_appearance_mode(mode)
            except (ValueError, AttributeError, RuntimeError) as e:
                logger.error(f"Failed to set appearance mode / Ошибка установки режима оформления / Помилка встановлення режиму оформлення: {e}")
                return

            # Update main window colors with a single after() call (not recursive)
            self.after(10, self._update_main_window_colors)

            # Close settings window if open - it will be recreated with new theme on next open
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                try:
                    self.settings_window.destroy()
                    self.settings_window = None
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Settings window destroy error / Ошибка уничтожения окна настроек / Помилка знищення вікна налаштувань: {e}")
                    self.settings_window = None

        finally:
            # Reset flag after a short delay to allow UI to settle
            self.after(100, lambda: setattr(self, '_changing_theme', False))

    def _update_main_window_colors(self) -> None:
        """
        Update main window colors after theme change

        Обновляет цвета главного окна после смены темы
        Оновлює кольори головного вікна після зміни теми
        """
        try:
            actual_theme = self._get_actual_theme()
            self._apply_theme_colors(actual_theme)
            bg = "#F3F3F3" if actual_theme == "light" else "#1d1e1e"
            self.configure(fg_color=bg)
            self.update_idletasks()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Main window colors update error / Ошибка обновления цветов главного окна / Помилка оновлення кольорів головного вікна: {e}")

    def _change_language(self, lang: str) -> None:
        """
        Change language and update UI without freezing

        Сменить язык и обновить интерфейс без зависания
        Змінити мову та оновити інтерфейс без зависання
        """
        # Prevent recursive calls / Предотвращаем рекурсивные вызовы / Запобігаємо рекурсивним викликам
        if hasattr(self, '_changing_language') and self._changing_language:
            return

        self._changing_language = True

        try:
            self.current_lang = lang
            
            # Update MessageBox theme
            self._update_messagebox_theme()
            
            self._apply_lang(lang)
            try:
                self.config.set("LANG", lang)
            except (KeyError, ValueError, OSError, AttributeError) as e:
                logger.error(f"Failed to save language / Ошибка сохранения языка / Помилка збереження мови: {e}")

            for l, btn in self.lang_buttons.items():
                if btn and btn.winfo_exists():
                    try:
                        btn.configure(fg_color="#2d6a4f" if l == lang else "#4b4b4b")
                    except (tk.TclError, AttributeError, RuntimeError) as e:
                        logger.debug(f"Language button error / Ошибка кнопки языка / Помилка кнопки мови: {e}")

            # Close and recreate settings window if open
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                try:
                    self.settings_window.destroy()
                    self.settings_window = None
                    # Reopen settings window with new language
                    self._show_settings()
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Settings window reopen error / Ошибка переоткрытия окна настроек / Помилка перевідкриття вікна налаштувань: {e}")
                    self.settings_window = None

            # Update main window UI elements
            if self.entry_res.get():
                self._update_strength_meter(self.entry_res.get())
            self._update_master_status_label()
            self._update_auto_lock_label()

            if hasattr(self, 'font_size_value') and self.font_size_value and self.font_size_value.winfo_exists():
                try:
                    self.font_size_value.configure(text=f"{self.current_font_size}px")
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Font size label error / Ошибка метки размера шрифта / Помилка мітки розміру шрифту: {e}")

            # 2FA UPDATE WHEN CHANGING LANGUAGE
            self._update_2fa_status_in_settings()

        finally:
            self._changing_language = False

    def _toggle_auto_lock(self) -> None:
        """
        Toggle auto-lock on/off

        Включает/выключает автоблокировку
        Увімкнює/вимикає автоблокування
        """
        self.auto_lock_enabled.set(not self.auto_lock_enabled.get())
        if self._auto_lock_btn and self._auto_lock_btn.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if self.auto_lock_enabled.get():
                try:
                    self._auto_lock_btn.configure(
                        text=L["auto_lock"],
                        fg_color="#2d6a4f",
                        hover_color="#2d6a4f"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Auto lock button error / Ошибка кнопки автоблокировки / Помилка кнопки автоблокування: {e}")
            else:
                try:
                    self._auto_lock_btn.configure(
                        text=L["auto_lock"],
                        fg_color="#8b0000",
                        hover_color="#8b0000"
                    )
                except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                    logger.debug(f"Auto lock button error / Ошибка кнопки автоблокировки / Помилка кнопки автоблокування: {e}")
        try:
            self.config.set("AUTO_LOCK", self.auto_lock_enabled.get())
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save auto lock / Ошибка сохранения автоблокировки / Помилка збереження автоблокування: {e}")
        if self.auto_lock_enabled.get():
            self._last_activity_time = time.time()

    def _update_auto_lock_label(self) -> None:
        """
        Update auto-lock label text

        Обновляет текст метки автоблокировки
        Оновлює текст мітки автоблокування
        """
        if self._auto_lock_label_ref and self._auto_lock_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            try:
                self._auto_lock_label_ref.configure(text=L["auto_lock_timeout"].format(self.auto_lock_timeout))
            except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
                logger.debug(f"Auto lock label error / Ошибка метки автоблокировки / Помилка мітки автоблокування: {e}")

    def _set_pdf_theme(self, theme: str) -> None:
        """
        Set PDF theme (light/dark)

        Установить тему PDF (светлая/тёмная)
        Встановити тему PDF (світла/темна)
        """
        if theme not in ["light", "dark"]:
            return

        try:
            self.config.set("PDF_THEME", theme)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.error(f"Failed to save PDF theme / Ошибка сохранения темы PDF / Помилка збереження теми PDF: {e}")

        # Update button colors / Обновляем цвета кнопок / Оновлюємо кольори кнопок
        if hasattr(self, 'pdf_theme_light_btn') and self.pdf_theme_light_btn and self.pdf_theme_light_btn.winfo_exists():
            try:
                self.pdf_theme_light_btn.configure(fg_color="#2d6a4f" if theme == "light" else "#4b4b4b")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"PDF theme light button update error / Ошибка обновления кнопки светлой темы PDF / Помилка оновлення кнопки світлої теми PDF: {e}")

        if hasattr(self, 'pdf_theme_dark_btn') and self.pdf_theme_dark_btn and self.pdf_theme_dark_btn.winfo_exists():
            try:
                self.pdf_theme_dark_btn.configure(fg_color="#2d6a4f" if theme == "dark" else "#4b4b4b")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"PDF theme dark button update error / Ошибка обновления кнопки тёмной темы PDF / Помилка оновлення кнопки темної теми PDF: {e}")

        logger.info(f"PDF theme set to: {theme} / Тема PDF установлена: {theme} / Тему PDF встановлено: {theme}")

    def _change_radius_instant(self, val: int) -> None:
        """
        Instant radius change (for slider)

        Мгновенное изменение радиуса (для слайдера)
        Миттєва зміна радіусу (для повзунка)
        """
        rad = int(val)
        self.current_radius = rad
        set_global_radius(rad)

        # Update all buttons in main window / Обновляем все кнопки в главном окне / Оновлюємо всі кнопки в головному вікні
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open,
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_hibp,
                     self.btn_upd, self.btn_settings, self.btn_about, self.btn_name_gen]
        for btn in menu_btns:
            if btn and btn.winfo_exists():
                try:
                    btn.configure(corner_radius=rad)
                except (tk.TclError, AttributeError, RuntimeError):
                    pass

        if self.btn_eye and self.btn_eye.winfo_exists():
            try:
                self.btn_eye.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        if self.entry_res and self.entry_res.winfo_exists():
            try:
                self.entry_res.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        if self.bottom_frame and self.bottom_frame.winfo_exists():
            try:
                self.bottom_frame.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        if self.right_panel and self.right_panel.winfo_exists():
            try:
                self.right_panel.configure(corner_radius=rad)
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Save to config / Сохраняем в конфиг / Зберігаємо в конфіг
        try:
            self.config.set("RADIUS", rad)
        except (KeyError, ValueError, OSError, AttributeError):
            pass

    def _apply_font_size_instant(self, size: int) -> None:
        """
        Instant font size change (for slider)

        Мгновенное изменение размера шрифта (для слайдера)
        Миттєва зміна розміру шрифту (для повзунка)
        """
        self.current_font_size = size

        # Update menu buttons / Обновляем кнопки меню / Оновлюємо кнопки меню
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open,
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_hibp,
                     self.btn_upd, self.btn_settings, self.btn_about, self.btn_name_gen]
        for btn in menu_btns:
            if btn and btn.winfo_exists():
                try:
                    btn.configure(font=("Segoe UI", size - 1, "bold"))
                except (tk.TclError, AttributeError, RuntimeError):
                    pass

        # Update headers / Обновляем заголовки / Оновлюємо заголовки
        if self.lbl_title and self.lbl_title.winfo_exists():
            try:
                self.lbl_title.configure(font=("Segoe UI", size + 6, "bold"))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        if self.lbl_menu and self.lbl_menu.winfo_exists():
            try:
                self.lbl_menu.configure(font=("Segoe UI", size + 4, "bold"))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        if self.lbl_strength_text and self.lbl_strength_text.winfo_exists():
            try:
                self.lbl_strength_text.configure(font=("Segoe UI", size, "bold"))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Update password entry field / Обновляем поле ввода пароля / Оновлюємо поле введення пароля
        if self.entry_res and self.entry_res.winfo_exists():
            try:
                self.entry_res.configure(font=("Consolas", size + 8))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Update eye button / Обновляем кнопку глаза / Оновлюємо кнопку ока
        if self.btn_eye and self.btn_eye.winfo_exists():
            try:
                self.btn_eye.configure(font=("Segoe UI", size + 6))
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        # Save to config / Сохраняем в конфиг / Зберігаємо в конфіг
        try:
            self.config.set("font_size", size)
        except (KeyError, ValueError, OSError, AttributeError):
            pass