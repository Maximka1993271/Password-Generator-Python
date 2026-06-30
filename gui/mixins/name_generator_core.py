from __future__ import annotations
# gui/mixins/name_generator_core.py
"""
Name generator core module for Secure Pass Pro.
Модуль Name generator core для Secure Pass Pro.
Модуль Name generator core для Secure Pass Pro.
"""
"""
Name generator core module for Secure Pass Pro.
Модуль Name generator core для Secure Pass Pro.
Модуль Name generator core для Secure Pass Pro.
"""
"""
Name Generator Mixin for SecurePassPro - Core Class
Генератор имён для SecurePassPro - Основной класс
Генератор імен для SecurePassPro - Основний клас

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""

import random
import time
import tkinter as tk
import threading
import hashlib
from typing import Optional, List, Set, Any
import customtkinter as ctk
from utils.helpers import play_sound
from utils.logger import get_logger
from Langs.lang import LANGUAGES

from gui.mixins.name_generator_data import (
    RUSSIAN_NAMES_MALE, RUSSIAN_NAMES_FEMALE, RUSSIAN_LASTNAMES,
    ENGLISH_NAMES_MALE, ENGLISH_NAMES_FEMALE, ENGLISH_LASTNAMES,
    GAME_WORDS, COOL_PREFIXES, BEAUTY_WORDS, SHORT_NAMES, LONG_NAMES,
    NUMBERS, EMAIL_DOMAINS
)

logger = get_logger("name_generator")


class NameGeneratorMixin:
    """Mixin for name generation functionality with duplicate filtering and async generation
    Миксин для функциональности генерации имён с фильтрацией дубликатов и асинхронной генерацией
    Міксин для функціональності генерації імен з фільтрацією дублікатів та асинхронною генерацією"""

    def _open_name_generator(self) -> None:
        """Open name generator window / Открыть окно генератора имён / Відкрити вікно генератора імен"""
        if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
            try:
                self._name_window.lift()
                self._name_window.focus()
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Window focus error / Ошибка фокуса окна / Помилка фокусу вікна: {e}")
            return

        L = LANGUAGES[self.current_lang]

        try:
            self._name_window = ctk.CTkToplevel(self)
            self._name_window.title(L.get("name_gen_title", "Генератор имён / Name Generator / Генератор імен"))
            self._name_window.geometry("1050x920")
            self._name_window.minsize(1000, 880)
            self._name_window.resizable(True, True)
            self._center_window_relative_to_parent(self._name_window, 1050, 920)
            self._name_window.transient(self)
            self._name_window.grab_set()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to create name generator window / Ошибка создания окна генератора имён / Помилка створення вікна генератора імен: {e}")
            return

        radius = getattr(self, 'current_radius', 25)

        self._generated_names: Set[str] = set()
        self._generation_in_progress = False
        self._cancel_requested = False
        self._generation_thread: Optional[threading.Thread] = None
        self._neon_frames = []
        self._neon_active = True

        # Main frame
        main_frame = ctk.CTkFrame(self._name_window, fg_color="transparent")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)

        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        title_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title = ctk.CTkLabel(title_frame, text=L.get("name_gen_title", "Генератор имён / Name Generator / Генератор імен"),
                            font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(anchor=tk.CENTER)

        # Decorative line
        line_frame = ctk.CTkFrame(scroll_frame, height=3, fg_color="#4EC9B0", corner_radius=5)
        line_frame.pack(fill=tk.X, pady=(0, 20))

        # Generation type section with neon border
        type_neon_frame = ctk.CTkFrame(scroll_frame, corner_radius=radius, border_width=3, border_color="#4EC9B0")
        type_neon_frame.pack(fill=tk.X, pady=8)
        type_frame = ctk.CTkFrame(type_neon_frame, corner_radius=radius-2, fg_color=("#F8F9FA", "#2d2d3d"))
        type_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        ctk.CTkLabel(type_frame, text=L.get("name_gen_type_label", "Тип генерации / Generation type / Тип генерації"),
                    font=ctk.CTkFont(size=17, weight="bold")).pack(anchor=tk.CENTER, pady=(15, 5))

        types_grid = ctk.CTkFrame(type_frame, fg_color="transparent")
        types_grid.pack(pady=(5, 15), padx=25, fill=tk.X)
        for i in range(4):
            types_grid.columnconfigure(i, weight=1)

        self.gen_type = tk.StringVar(value="samp")

        all_types = [
            ("samp", L.get("name_gen_samp", "SAMP RP"), 0, 0),
            ("email", L.get("name_gen_email", "Email адрес / Email address / Email адреса"), 0, 1),
            ("game", L.get("name_gen_game", "Игровой ник / Game nickname / Ігровий нік"), 0, 2),
            ("cool", L.get("name_gen_cool", "Крутой ник / Cool nickname / Крутий нік"), 0, 3),
            ("beauty", L.get("name_gen_beauty", "Красивый ник / Beautiful nickname / Красивий нік"), 1, 0),
            ("short", L.get("name_gen_short", "Короткий (3-5) / Short (3-5) / Короткий (3-5)"), 1, 1),
            ("long", L.get("name_gen_long", "Длинный (8+) / Long (8+) / Довгий (8+)"), 1, 2),
            ("random", L.get("name_gen_random", "Случайный / Random / Випадковий"), 1, 3),
        ]

        for val, text, row, col in all_types:
            try:
                rb = ctk.CTkRadioButton(types_grid, text=text, variable=self.gen_type, value=val, font=ctk.CTkFont(size=13))
                rb.grid(row=row, column=col, padx=15, pady=10, sticky="w")
            except (tk.TclError, AttributeError, KeyError) as e:
                logger.debug(f"Radio button error / Ошибка радиокнопки / Помилка радіокнопки: {e}")

        # Settings section with neon border
        settings_neon_frame = ctk.CTkFrame(scroll_frame, corner_radius=radius, border_width=3, border_color="#4EC9B0")
        settings_neon_frame.pack(fill=tk.X, pady=15)
        settings_frame = ctk.CTkFrame(settings_neon_frame, corner_radius=radius-2, fg_color=("#F8F9FA", "#2d2d3d"))
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        ctk.CTkLabel(settings_frame, text=L.get("name_gen_settings_label", "Настройки / Settings / Налаштування"),
                    font=ctk.CTkFont(size=17, weight="bold")).pack(anchor=tk.CENTER, pady=(15, 5))

        settings_grid = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_grid.pack(pady=(5, 15), padx=25, fill=tk.X)
        settings_grid.columnconfigure((0, 1), weight=1)

        # Column 1 - Gender and Language
        col1 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        col1.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        # Gender
        gender_container = ctk.CTkFrame(col1, fg_color="transparent")
        gender_container.pack(fill=tk.X, pady=8)
        ctk.CTkLabel(gender_container, text=L.get("name_gen_gender", "Пол: / Gender: / Стать:"),
                    font=ctk.CTkFont(size=14, weight="bold"), width=90, anchor="w").pack(side=tk.LEFT)

        self.gen_gender = tk.StringVar(value="random")
        gender_buttons = ctk.CTkFrame(gender_container, fg_color="transparent")
        gender_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ctk.CTkRadioButton(gender_buttons, text=L.get("name_gen_male", "Мужской / Male / Чоловіча"),
                          variable=self.gen_gender, value="male", font=ctk.CTkFont(size=13)).pack(side=tk.LEFT, padx=(0, 15))
        ctk.CTkRadioButton(gender_buttons, text=L.get("name_gen_female", "Женский / Female / Жіноча"),
                          variable=self.gen_gender, value="female", font=ctk.CTkFont(size=13)).pack(side=tk.LEFT, padx=15)
        ctk.CTkRadioButton(gender_buttons, text=L.get("name_gen_random_gender", "Случайный / Random / Випадкова"),
                          variable=self.gen_gender, value="random", font=ctk.CTkFont(size=13)).pack(side=tk.LEFT, padx=15)

        # Language
        lang_container = ctk.CTkFrame(col1, fg_color="transparent")
        lang_container.pack(fill=tk.X, pady=8)
        ctk.CTkLabel(lang_container, text=L.get("name_gen_lang", "Язык: / Language: / Мова:"),
                    font=ctk.CTkFont(size=14, weight="bold"), width=90, anchor="w").pack(side=tk.LEFT)

        self.gen_lang = tk.StringVar(value="russian")
        lang_buttons = ctk.CTkFrame(lang_container, fg_color="transparent")
        lang_buttons.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ctk.CTkRadioButton(lang_buttons, text=L.get("name_gen_russian", "Русский / Russian / Російська"),
                          variable=self.gen_lang, value="russian", font=ctk.CTkFont(size=13)).pack(side=tk.LEFT, padx=(0, 15))
        ctk.CTkRadioButton(lang_buttons, text=L.get("name_gen_english", "English"),
                          variable=self.gen_lang, value="english", font=ctk.CTkFont(size=13)).pack(side=tk.LEFT, padx=15)

        # Column 2 - Separator and Count
        col2 = ctk.CTkFrame(settings_grid, fg_color="transparent")
        col2.grid(row=0, column=1, sticky="nsew", padx=(20, 0))

        # Separator
        sep_container = ctk.CTkFrame(col2, fg_color="transparent")
        sep_container.pack(fill=tk.X, pady=8)
        ctk.CTkLabel(sep_container, text=L.get("name_gen_separator", "Разделитель: / Separator: / Розділювач:"),
                    font=ctk.CTkFont(size=14, weight="bold"), width=110, anchor="w").pack(side=tk.LEFT)

        self.gen_separator_value = tk.StringVar(value="_")
        sep_values = [L.get("name_gen_separator_yes", "ДА (_) / YES (_) / ТАК (_)"), L.get("name_gen_separator_no", "НЕТ / NO / НІ")]

        self.sep_menu = ctk.CTkOptionMenu(sep_container, values=sep_values, width=140,
                                          font=ctk.CTkFont(size=13), corner_radius=radius,
                                          command=self._on_separator_change)
        self.sep_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.sep_menu.set(sep_values[0])

        # Count
        count_container = ctk.CTkFrame(col2, fg_color="transparent")
        count_container.pack(fill=tk.X, pady=8)
        ctk.CTkLabel(count_container, text=L.get("name_gen_count", "Количество: / Count: / Кількість:"),
                    font=ctk.CTkFont(size=14, weight="bold"), width=110, anchor="w").pack(side=tk.LEFT)

        self.gen_count = tk.StringVar(value="1")
        count_menu = ctk.CTkOptionMenu(count_container, values=["1", "2", "3", "4", "5", "10"],
                                       variable=self.gen_count, width=140, font=ctk.CTkFont(size=13),
                                       corner_radius=radius)
        count_menu.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Result section with neon border
        result_neon_frame = ctk.CTkFrame(scroll_frame, corner_radius=radius, border_width=3, border_color="#4EC9B0")
        result_neon_frame.pack(fill=tk.BOTH, expand=True, pady=15)
        result_frame = ctk.CTkFrame(result_neon_frame, corner_radius=radius-2, fg_color=("#F8F9FA", "#2d2d3d"))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        ctk.CTkLabel(result_frame, text=L.get("name_gen_result_label", "Результат / Result / Результат"),
                    font=ctk.CTkFont(size=17, weight="bold")).pack(anchor=tk.CENTER, pady=(15, 8))

        self.result_text = ctk.CTkTextbox(result_frame, height=280, font=ctk.CTkFont(family="Consolas", size=15),
                                          corner_radius=radius-4, border_spacing=12,
                                          fg_color=("#FFFFFF", "#1a1a2e"))
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Control buttons - компактное расположение
        controls = ctk.CTkFrame(main_frame, fg_color="transparent")
        controls.pack(fill=tk.X, pady=(10, 0))

        button_container = ctk.CTkFrame(controls, fg_color="transparent")
        button_container.pack(anchor=tk.CENTER)

        # Generate button
        self.gen_btn = ctk.CTkButton(button_container, text=L.get("name_gen_generate_btn", "Сгенерировать / Generate / Згенерувати"),
                                     fg_color="#00C853", hover_color="#00E676", height=42, width=130,
                                     font=ctk.CTkFont(size=14, weight="bold"), corner_radius=radius,
                                     command=self._generate_name_async)
        self.gen_btn.pack(side=tk.LEFT, padx=1)

        # Clear button
        self.clear_btn = ctk.CTkButton(button_container, text=L.get("name_gen_clear_btn", "Очистить / Clear / Очистити"),
                                       fg_color="#FF9800", hover_color="#FFB74D", height=42, width=110,
                                       font=ctk.CTkFont(size=14), corner_radius=radius,
                                       command=self._clear_result)
        self.clear_btn.pack(side=tk.LEFT, padx=1)

        # Copy all button
        self.copy_btn = ctk.CTkButton(button_container, text=L.get("name_gen_copy_btn", "Копировать всё / Copy all / Копіювати всі"),
                                      fg_color="#2196F3", hover_color="#64B5F6", height=42, width=120,
                                      font=ctk.CTkFont(size=14), corner_radius=radius,
                                      command=self._copy_all)
        self.copy_btn.pack(side=tk.LEFT, padx=1)

        # Cancel button - cancels ongoing generation, stays clickable after
        self.cancel_btn = ctk.CTkButton(button_container, text=L.get("cancel", "Отмена / Cancel / Скасувати"),
                                        fg_color="#8b0000", hover_color="#cc0000", height=42, width=90,
                                        font=ctk.CTkFont(size=14), corner_radius=radius,
                                        command=self._cancel_generation)
        self.cancel_btn.pack(side=tk.LEFT, padx=1)

        # Close button
        self.close_btn = ctk.CTkButton(button_container, text=L.get("close", "Закрыть / Close / Закрити"),
                                       fg_color="#607D8B", hover_color="#90A4AE", height=42, width=90,
                                       font=ctk.CTkFont(size=14), corner_radius=radius,
                                       command=self._close_window)
        self.close_btn.pack(side=tk.LEFT, padx=1)

        # Neon animation
        self._neon_frames = [type_neon_frame, settings_neon_frame, result_neon_frame]
        self._neon_active = True
        self._animate_neon_border()

        self._name_window_buttons = [self.gen_btn, self.clear_btn, self.copy_btn, self.close_btn, self.cancel_btn]
        self._name_window_textbox = self.result_text

        from utils.radius_manager import register_window
        register_window(self._name_window)

        self._name_window.protocol("WM_DELETE_WINDOW", self._close_window)

    def _cancel_generation(self) -> None:
        """Cancel ongoing generation and clear result / Отмена генерации и очистка результата / Скасування генерації та очищення результату"""
        # Останавливаем поток генерации / Stop generation thread / Зупиняємо потік генерації
        self._generation_in_progress = False
        self._cancel_requested = True

        if hasattr(self, '_generation_thread') and self._generation_thread and self._generation_thread.is_alive():
            logger.debug("Generation cancelled by user / Генерация отменена пользователем / Генерацію скасовано користувачем")

        # Очищаем результат — пользователь видит, что кнопка сработала
        # Clear result — user sees the button worked
        # Очищаємо результат — користувач бачить, що кнопка спрацювала
        try:
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
            if hasattr(self, '_generated_names'):
                self._generated_names.clear()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Clear on cancel error / Ошибка очистки при отмене / Помилка очищення при скасуванні: {e}")

        # Возвращаем кнопку "Сгенерировать" в активное состояние
        # Re-enable generate button / Повертаємо кнопку "Згенерувати" в активний стан
        try:
            if hasattr(self, 'gen_btn') and self.gen_btn and self.gen_btn.winfo_exists():
                self.gen_btn.configure(state="normal")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Button config error / Ошибка настройки кнопки / Помилка налаштування кнопки: {e}")

    def _animate_neon_border(self, step=0) -> None:
        """Animate neon border / Анимация неоновой рамки / Анімація неонової рамки"""
        if not hasattr(self, '_name_window') or not self._name_window or not self._name_window.winfo_exists():
            return

        colors = ["#4EC9B0", "#00C853", "#00E676", "#4EC9B0", "#00BFA5", "#4EC9B0"]
        next_color = colors[step % len(colors)]

        try:
            for frame in self._neon_frames:
                if frame and frame.winfo_exists():
                    frame.configure(border_color=next_color)
        except (tk.TclError, AttributeError, RuntimeError) as _:
            pass

        if hasattr(self, '_neon_active') and self._neon_active:
            self._name_window.after(600, lambda: self._animate_neon_border(step + 1))

    def _on_separator_change(self, choice) -> None:
        """Handle separator change / Обработка изменения разделителя / Обробка зміни розділювача"""
        L = LANGUAGES[self.current_lang]
        yes_text = L.get("name_gen_separator_yes", "ДА (_) / YES (_) / ТАК (_)")
        if choice == yes_text:
            self.gen_separator_value.set("_")
        else:
            self.gen_separator_value.set("")

    def _update_name_window_radius(self, radius: int) -> None:
        """Update radius for name generator window / Обновить радиус для окна генератора имён / Оновити радіус для вікна генератора імен"""
        if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
            try:
                for btn in self._name_window_buttons:
                    if btn and btn.winfo_exists():
                        btn.configure(corner_radius=radius)
                if self._name_window_textbox and self._name_window_textbox.winfo_exists():
                    self._name_window_textbox.configure(corner_radius=radius)
                for frame in self._neon_frames:
                    if frame and frame.winfo_exists():
                        frame.configure(corner_radius=radius)
                if hasattr(self, 'sep_menu') and self.sep_menu:
                    self.sep_menu.configure(corner_radius=radius)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Radius update error / Ошибка обновления радиуса / Помилка оновлення радіусу: {e}")

    def _close_window(self) -> None:
        """Close name generator window / Закрыть окно генератора имён / Закрити вікно генератора імен"""
        if hasattr(self, '_neon_active'):
            self._neon_active = False
        if hasattr(self, '_generation_in_progress'):
            self._generation_in_progress = False

        if hasattr(self, '_name_window') and self._name_window:
            from utils.radius_manager import unregister_window
            try:
                unregister_window(self._name_window)
                self._name_window.grab_release()
                self._name_window.destroy()
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Window destruction error / Ошибка уничтожения окна / Помилка знищення вікна: {e}")
            finally:
                self._name_window = None
                self._name_window_buttons = []
                self._name_window_textbox = None
                self._neon_frames = []
                if hasattr(self, 'gen_type'):
                    self.gen_type = None
                if hasattr(self, 'gen_gender'):
                    self.gen_gender = None
                if hasattr(self, 'gen_lang'):
                    self.gen_lang = None
                if hasattr(self, 'gen_separator_value'):
                    self.gen_separator_value = None
                if hasattr(self, 'gen_count'):
                    self.gen_count = None
                if hasattr(self, 'sep_menu'):
                    self.sep_menu = None

    def _clear_result(self) -> None:
        """Clear result field / Очистить поле результата / Очистити поле результату"""
        try:
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                if hasattr(self, '_generated_names'):
                    self._generated_names.clear()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Clear result error / Ошибка очистки результата / Помилка очищення результату: {e}")

    def _copy_all(self) -> None:
        """Copy all results to clipboard / Копировать все результаты в буфер обмена / Копіювати всі результати в буфер обміну"""
        try:
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                text = self.result_text.get("1.0", tk.END).strip()
                if text:
                    self.clipboard_clear()
                    self.clipboard_append(text)
                    play_sound("copy", self.sound_enabled.get())
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Copy all error / Ошибка копирования всех / Помилка копіювання всіх: {e}")

    def _generate_name_async(self) -> None:
        """Generate name(s) asynchronously / Асинхронная генерация / Асинхронна генерація"""
        if hasattr(self, '_generation_in_progress') and self._generation_in_progress:
            return

        # Сбрасываем флаг отмены перед новой генерацией
        # Reset cancel flag before new generation / Скидаємо прапор скасування перед новою генерацією
        self._cancel_requested = False
        self._generation_in_progress = True
        try:
            if hasattr(self, 'gen_btn') and self.gen_btn:
                self.gen_btn.configure(state="disabled")
            if hasattr(self, 'cancel_btn') and self.cancel_btn:
                self.cancel_btn.configure(state="normal")
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", LANGUAGES[self.current_lang].get("name_gen_generating", "Генерация... / Generating... / Генерація..."))
        except (tk.TclError, AttributeError, KeyError) as e:
            logger.debug(f"UI update error / Ошибка обновления UI / Помилка оновлення UI: {e}")

        self._generation_thread = threading.Thread(target=self._generate_name_worker, daemon=True)
        self._generation_thread.start()

        def check_completion() -> bool:
            if not self._generation_in_progress or not self._generation_thread.is_alive():
                try:
                    if hasattr(self, 'gen_btn') and self.gen_btn:
                        self.gen_btn.configure(state="normal")
                    # cancel_btn НЕ отключаем — она должна оставаться кликабельной
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Button restore error / Ошибка восстановления кнопки / Помилка відновлення кнопки: {e}")
                self._generation_in_progress = False
                self._cancel_requested = False
                # Если в поле всё ещё "Генерация..." — просто очищаем (результат придёт позже через after)
                if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                    try:
                        generating_text = LANGUAGES[self.current_lang].get("name_gen_generating", "Генерация... / Generating... / Генерація...")
                        current_text = self.result_text.get("1.0", "end").strip()
                        if current_text == generating_text:
                            self.result_text.delete("1.0", tk.END)
                    except (tk.TclError, AttributeError, KeyError) as e:
                        logger.debug(f"Text clear error / Ошибка очистки текста / Помилка очищення тексту: {e}")
            else:
                if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
                    self._name_window.after(500, check_completion)

        if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
            self._name_window.after(500, check_completion)

    def _generate_name_worker(self) -> None:
        """Worker for asynchronous name generation / Воркер для асинхронной генерации / Воркер для асинхронної генерації"""
        try:
            gen_type = self.gen_type.get() if hasattr(self, 'gen_type') and self.gen_type else "samp"
            count = int(self.gen_count.get()) if hasattr(self, 'gen_count') and self.gen_count else 1

            if count > 100:
                count = 100

            results = []
            if hasattr(self, '_generated_names'):
                self._generated_names.clear()

            for i in range(count):
                if hasattr(self, '_generation_in_progress') and not self._generation_in_progress:
                    break
                if hasattr(self, '_cancel_requested') and self._cancel_requested:
                    break

                name = self._generate_single_name(gen_type)

                if name:
                    name_hash = hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]  # SHA-256 replaces MD5
                    if name_hash not in self._generated_names:
                        self._generated_names.add(name_hash)
                        results.append(name)
                    else:
                        alt_name = self._generate_single_name(gen_type, attempt=2)
                        if alt_name:
                            results.append(alt_name)
                            self._generated_names.add(hashlib.sha256(alt_name.encode('utf-8')).hexdigest()[:16])
                        elif name:
                            results.append(name)

                time.sleep(0.01)

            if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
                self._name_window.after(0, lambda: self._display_results(results))

        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"Generation worker error / Ошибка воркера генерации / Помилка воркера генерації: {e}")
            if hasattr(self, '_name_window') and self._name_window and self._name_window.winfo_exists():
                self._name_window.after(0, lambda e=e: self._display_error(str(e)))

    def _display_error(self, error_msg: str) -> None:
        """Display error message / Отображение ошибки / Відображення помилки"""
        try:
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert("1.0", f"Error / Ошибка / Помилка: {error_msg}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Display error error / Ошибка отображения ошибки / Помилка відображення помилки: {e}")

    def _generate_single_name(self, gen_type: str, attempt: int = 1) -> str:
        """Generate single name / Генерация одного имени / Генерація одного імені"""
        try:
            if gen_type == "samp":
                return self._generate_samp()
            elif gen_type == "email":
                return self._generate_email()
            elif gen_type == "game":
                return self._generate_game()
            elif gen_type == "cool":
                return self._generate_cool()
            elif gen_type == "beauty":
                return self._generate_beauty()
            elif gen_type == "short":
                return self._generate_short()
            elif gen_type == "long":
                return self._generate_long()
            elif gen_type == "random":
                return self._generate_random()
            else:
                return self._generate_samp()
        except (IndexError, ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Name generation error (attempt {attempt}) / Ошибка генерации имени (попытка {attempt}) / Помилка генерації імені (спроба {attempt}): {e}")
            return f"Error_{attempt}"

    def _display_results(self, results: List[str]) -> None:
        """Display generated results / Отображение результатов / Відображення результатів"""
        # Если отмена была запрошена — не перезаписываем результат
        # If cancel was requested — do not overwrite the cleared result
        # Якщо скасування було запитано — не перезаписуємо результат
        if hasattr(self, '_cancel_requested') and self._cancel_requested:
            return
        try:
            if hasattr(self, 'result_text') and self.result_text and self.result_text.winfo_exists():
                self.result_text.delete("1.0", tk.END)
                if results:
                    if len(results) == 1:
                        self.result_text.insert(tk.END, results[0])
                    else:
                        self.result_text.insert(tk.END, "\n".join(results))
                    play_sound("generate", self.sound_enabled.get())
                else:
                    self.result_text.insert(tk.END, LANGUAGES[self.current_lang].get("name_gen_error", "Ошибка генерации / Generation error / Помилка генерації"))
        except (tk.TclError, AttributeError, RuntimeError, KeyError) as e:
            logger.debug(f"Display results error / Ошибка отображения результатов / Помилка відображення результатів: {e}")

    def _get_name_data(self) -> Any:
        """Get random name data / Получить случайные данные имени / Отримати випадкові дані імені"""
        lang = self.gen_lang.get() if hasattr(self, 'gen_lang') and self.gen_lang else "russian"
        gender = self.gen_gender.get() if hasattr(self, 'gen_gender') and self.gen_gender else "random"
        if gender == "random":
            gender = random.choice(["male", "female"])
        if lang == "russian":
            first = RUSSIAN_NAMES_MALE if gender == "male" else RUSSIAN_NAMES_FEMALE
            last = RUSSIAN_LASTNAMES
        else:
            first = ENGLISH_NAMES_MALE if gender == "male" else ENGLISH_NAMES_FEMALE
            last = ENGLISH_LASTNAMES
        return random.choice(first), random.choice(last)

    def _generate_samp(self) -> Any:
        """Generate SAMP RP name / Генерация имени для SAMP RP / Генерація імені для SAMP RP"""
        first, last = self._get_name_data()
        sep = self.gen_separator_value.get() if hasattr(self, 'gen_separator_value') and self.gen_separator_value else "_"
        if sep == "":
            return f"{first} {last}"
        return f"{first}_{last}"

    def _generate_email(self) -> Any:
        """Generate email address / Генерация email адреса / Генерація email адреси"""
        first, last = self._get_name_data()
        sep = self.gen_separator_value.get() if hasattr(self, 'gen_separator_value') and self.gen_separator_value else "_"
        lang = self.gen_lang.get() if hasattr(self, 'gen_lang') and self.gen_lang else "russian"

        email_sep = sep if sep != "" else "."

        if lang == "russian":
            translit = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
                       'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
                       'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch',
                       'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'}
            first = ''.join(translit.get(c, c) for c in first.lower())
            last = ''.join(translit.get(c, c) for c in last.lower())
        else:
            first = first.lower()
            last = last.lower()
        num = random.choice(NUMBERS)
        username = f"{first}{email_sep}{last}{num}"
        domain = random.choice(EMAIL_DOMAINS)
        return f"{username}{domain}"

    def _generate_game(self) -> Any:
        """Generate game nickname / Генерация игрового ника / Генерація ігрового ніка"""
        word1 = random.choice(GAME_WORDS)
        word2 = random.choice(GAME_WORDS) if random.choice([True, False]) else ""
        sep = self.gen_separator_value.get() if hasattr(self, 'gen_separator_value') and self.gen_separator_value else "_"
        game_sep = sep if sep != "" else "_"
        name = f"{word1}{game_sep}{word2}" if word2 else word1
        if random.choice([True, False]):
            name += random.choice(NUMBERS)
        prefix = random.choice(["", "xX_", "Xx_"])
        suffix = random.choice(["", "_xX", "_Xx"])
        return f"{prefix}{name}{suffix}"

    def _generate_cool(self) -> Any:
        """Generate cool nickname / Генерация крутого ника / Генерація крутого ніка"""
        prefix = random.choice(COOL_PREFIXES)
        word = random.choice(GAME_WORDS)
        sep = self.gen_separator_value.get() if hasattr(self, 'gen_separator_value') and self.gen_separator_value else "_"
        cool_sep = sep if sep != "" else "_"
        name = f"{prefix}{cool_sep}{word}"
        if random.choice([True, False]):
            name += random.choice(NUMBERS)
        return name

    def _generate_beauty(self) -> Any:
        """Generate beautiful nickname / Генерация красивого ника / Генерація красивого ніка"""
        word = random.choice(BEAUTY_WORDS)
        if random.choice([True, False]):
            word += random.choice(NUMBERS[:50])
        return word

    def _generate_short(self) -> Any:
        """Generate short name (3-5 chars) / Генерация короткого имени (3-5 символов) / Генерація короткого імені (3-5 символів)"""
        name = random.choice(SHORT_NAMES)
        if random.choice([True, False]):
            name += random.choice(NUMBERS[:9])
        return name

    def _generate_long(self) -> Any:
        """Generate long name (8+ chars) / Генерация длинного имени (8+ символов) / Генерація довгого імені (8+ символів)"""
        name = random.choice(LONG_NAMES)
        if random.choice([True, False]):
            name += random.choice(NUMBERS)
        return name

    def _generate_random(self) -> Any:
        """Generate random type name / Генерация случайного типа имени / Генерація випадкового типу імені"""
        types = ["samp", "email", "game", "cool", "beauty", "short", "long"]
        funcs = {
            "samp": self._generate_samp,
            "email": self._generate_email,
            "game": self._generate_game,
            "cool": self._generate_cool,
            "beauty": self._generate_beauty,
            "short": self._generate_short,
            "long": self._generate_long
        }
        t = random.choice(types)
        return funcs[t]()
