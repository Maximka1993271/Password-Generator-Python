"""
Settings window mixin - Event handlers
Миксин окна настроек - Обработчики событий
Міксин вікна налаштувань - Обробники подій

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import time
import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from Langs.lang import LANGUAGES
from gui.dialogs import CTkMessageBox
from utils.helpers import play_sound, set_global_radius
from core.app_settings import AppSettings, Key  # centralised settings

logger = get_logger("settings_window")


class SettingsWindowHandlersMixin:
    """Event handlers for settings window

    Обработчики событий для окна настроек
    Обробники подій для вікна налаштувань
    """

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

    def _update_auto_lock_button(self) -> None:
        """
        Update auto-lock button appearance

        Обновляет внешний вид кнопки автоблокировки
        Оновлює зовнішній вигляд кнопки автоблокування
        """
        L = LANGUAGES[self.current_lang]
        if self.auto_lock_enabled.get():
            self._auto_lock_btn.configure(text=L["auto_lock"], fg_color="#2d6a4f")
        else:
            self._auto_lock_btn.configure(text=L["auto_lock"], fg_color="#8b0000")

    def _update_sound_button(self) -> None:
        """
        Update sound button appearance

        Обновляет внешний вид кнопки звука
        Оновлює зовнішній вигляд кнопки звуку
        """
        L = LANGUAGES[self.current_lang]
        if self.sound_enabled.get():
            self._sound_btn.configure(text=L["sound_on"], fg_color="#2d6a4f")
        else:
            self._sound_btn.configure(text=L["sound_off"], fg_color="#8b0000")

    def _update_auto_save_button(self) -> None:
        """
        Update auto-save button appearance

        Обновляет внешний вид кнопки автосохранения
        Оновлює зовнішній вигляд кнопки автозбереження
        """
        L = LANGUAGES[self.current_lang]
        if self.auto_save_var.get():
            self.auto_save_btn.configure(text=L.get("auto_save_on", "On / Вкл / Увімк"), fg_color="#2d6a4f")
        else:
            self.auto_save_btn.configure(text=L.get("auto_save_off", "Off / Выкл / Вимк"), fg_color="#8b0000")

    def _update_clip_timeout_label(self) -> None:
        """
        Update clipboard timeout label

        Обновляет метку таймаута буфера обмена
        Оновлює мітку таймауту буфера обміну
        """
        L = LANGUAGES[self.current_lang]
        self._clip_timeout_label_ref.configure(text=L["clip_timeout"].format(self.clipboard_timeout))

    def _refresh_settings_tabs_language(self) -> None:
        """
        Refresh settings tabs language

        Обновляет язык вкладок настроек
        Оновлює мову вкладок налаштувань
        """
        if not hasattr(self, 'category_buttons') or not self.category_buttons:
            return

        L = LANGUAGES[self.current_lang]

        categories = [
            ("design", "tab_design", L.get("tab_design", "Дизайн / Design / Дизайн")),
            ("security", "tab_security", L.get("tab_security", "Безопасность / Security / Безпека")),
            ("general", "tab_general", L.get("tab_general", "Общие / General / Загальні")),
        ]

        for key, lang_key, display_text in categories:
            if key in self.category_buttons:
                self.category_buttons[key].configure(text=display_text)

        self._update_auto_lock_button()
        self._update_sound_button()
        self._update_auto_save_button()
        self._update_clip_timeout_label()

        if hasattr(self, '_2fa_status_label') and self._2fa_status_label:
            try:
                self._2fa_status_label.configure(
                    text=self._get_2fa_status_text(),
                    text_color=self._get_2fa_status_color()
                )
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

        if hasattr(self, '_2fa_settings_btn') and self._2fa_settings_btn:
            try:
                self._2fa_settings_btn.configure(text=L.get("2fa_settings_title", "2FA Settings / Настройки 2FA / Налаштування 2FA"))
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

        # Update search placeholder
        if hasattr(self, '_search_entry') and self._search_entry:
            try:
                self._search_entry.configure(placeholder_text=" " + L.get("settings_search", "Search settings... / Поиск настроек... / Пошук налаштувань..."))
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

        for widget in self.settings_window.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel):
                        try:
                            current_text = child.cget("text")
                            if current_text in ["Настройки", "Settings"]:
                                child.configure(text=L["settings_title"])
                            elif current_text in ["Настройте приложение под свои потребности", "Configure the app to your needs"]:
                                child.configure(text=L.get("settings_subtitle", "Configure the app to your needs / Настройте приложение под свои потребности / Налаштуйте додаток під свої потреби"))
                        except (tk.TclError, AttributeError, RuntimeError) as _:
                            pass

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
