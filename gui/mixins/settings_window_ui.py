"""
Settings window mixin - UI creation (main window)
Миксин окна настроек - Создание UI (главное окно)
Міксин вікна налаштувань - Створення UI (головне вікно)

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from Langs.lang import LANGUAGES
from utils.helpers import set_window_icon, apply_window_rounding

logger = get_logger("settings_window")


class SettingsWindowUIMixin:
    """UI creation for settings window

    Создание интерфейса для окна настроек
    Створення інтерфейсу для вікна налаштувань
    """

    def _show_settings(self) -> None:
        """
        Show settings window / Показать окно настроек / Показати вікно налаштувань
        """
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        L = LANGUAGES[self.current_lang]
        actual_theme = self._get_actual_theme()
        is_dark = actual_theme == "dark"

        # Colors for modern design / Цвета для современного дизайна / Кольори для сучасного дизайну
        if is_dark:
            bg_win = "#202020"
            bg_card = "#2d2d2d"
            bg_card_hover = "#383838"
            text_primary = "#ffffff"
            text_secondary = "#a0a0a0"
            border_color = "#3d3d3d"
            accent_color = "#2d6a4f"
            accent_hover = "#40916c"
            icon_bg = "#383838"
        else:
            bg_win = "#f0f0f0"
            bg_card = "#ffffff"
            bg_card_hover = "#f8f8f8"
            text_primary = "#202020"
            text_secondary = "#606060"
            border_color = "#e0e0e0"
            accent_color = "#2d6a4f"
            accent_hover = "#40916c"
            icon_bg = "#f0f0f0"

        try:
            self.settings_window = ctk.CTkToplevel(self)
            self.settings_window.configure(fg_color=bg_win)
            self.settings_window.title(L["settings_title"])
            self.settings_window.geometry("850x650")
            self.settings_window.minsize(750, 500)
            set_window_icon(self.settings_window)
            self.settings_window.transient(self)
            self.settings_window.grab_set()
            self.settings_window.attributes("-topmost", True)
            self.settings_window.after(100, lambda: self.settings_window.attributes("-topmost", False))
            self._center_window_relative_to_parent(self.settings_window, 850, 650)
            apply_window_rounding(self.settings_window)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to create settings window / Ошибка создания окна настроек / Помилка створення вікна налаштувань: {e}")
            return

        rad = self.current_radius

        # ========== MAIN CONTAINER ==========
        main_container = ctk.CTkFrame(self.settings_window, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # ========== HEADER WITH SEARCH ==========
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(header_frame, text=L["settings_title"],
                    font=("Segoe UI", 24, "bold"), text_color=text_primary)
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(header_frame, text=L.get("settings_subtitle", "Configure the app to your needs / Настройте приложение под свои потребности / Налаштуйте додаток під свої потреби"),
                    font=("Segoe UI", 12), text_color=text_secondary)
        subtitle_label.pack(anchor="w", pady=(5, 0))

        # Search bar for settings / Строка поиска настроек / Рядок пошуку налаштувань
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(fill="x", pady=(15, 0))

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=" " + L.get("settings_search", "Search settings... / Поиск настроек... / Пошук налаштувань..."),
            height=40,
            corner_radius=rad,
            fg_color=bg_card,
            text_color=text_primary
        )
        search_entry.pack(fill="x")

        # ========== SIDEBAR (TABS LIKE IN EDGE) ==========
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Left panel with categories / Левая панель с категориями / Ліва панель з категоріями
        sidebar = ctk.CTkFrame(content_frame, width=200, fg_color="transparent")
        sidebar.pack(side="left", fill="y", padx=(0, 20))
        sidebar.pack_propagate(False)

        # Right panel with content / Правая панель с содержимым / Права панель з вмістом
        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.pack(side="left", fill="both", expand=True)

        # ========== CATEGORIES IN SIDEBAR ==========
        categories = [
            ("design", "tab_design", L.get("tab_design", "Дизайн / Design / Дизайн")),
            ("security", "tab_security", L.get("tab_security", "Безопасность / Security / Безпека")),
            ("general", "tab_general", L.get("tab_general", "Общие / General / Загальні")),
            ("cloud",   "tab_cloud",   L.get("tab_cloud",   "Облако / Cloud / Хмара")),
        ]

        self.category_buttons = {}
        self.category_frames = {}
        self.settings_cards = []
        self._settings_pack_options = {}
        self._settings_search_active = False
        self._active_settings_category = "design"

        for key, lang_key, display_text in categories:
            content_frame_inner = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
            self.category_frames[key] = content_frame_inner

            btn_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
            btn_frame.pack(fill="x", pady=3)
            btn_frame.pack_propagate(False)

            btn = ctk.CTkButton(
                btn_frame,
                text=display_text,
                anchor="w",
                font=("Segoe UI", 14),
                fg_color="transparent",
                text_color=text_primary,
                hover_color=bg_card_hover,
                corner_radius=rad,
                height=45,
                command=lambda k=key: self._switch_category(k)
            )
            btn.pack(fill="both", expand=True, padx=5, pady=2)
            self.category_buttons[key] = btn

        self._switch_category("design")

        # Search functionality
        def on_search(*args) -> None:
            """
            Handle the search event.
            Обработчик события search.
            Обробник події search.
            """
            self._filter_settings(search_entry.get())

        search_entry.bind("<KeyRelease>", on_search)

        # ========== FILL CATEGORIES ==========

        # ----- CATEGORY: DESIGN -----
        design_frame = self.category_frames["design"]

        # Card: Language / Карточка: Язык / Картка: Мова
        self._add_settings_card(design_frame, "settings_lang", L.get("settings_lang_desc", "Choose interface language / Выберите язык интерфейса / Виберіть мову інтерфейсу"))
        lang_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        lang_frame.pack(fill="x", pady=(0, 20))

        self.lang_buttons.clear()
        for lang_code in ["RU", "EN", "UA"]:
            btn = ctk.CTkButton(
                lang_frame,
                text=lang_code,
                width=80,
                height=36,
                command=lambda l=lang_code: self._change_language(l),
                fg_color=accent_color if self.current_lang == lang_code else bg_card,
                text_color=text_primary if self.current_lang == lang_code else text_secondary,
                hover_color=accent_hover,
                font=("Segoe UI", 13, "bold"),
                corner_radius=rad
            )
            btn.pack(side="left", padx=8)
            self.lang_buttons[lang_code] = btn

        # Card: Theme / Карточка: Тема / Картка: Тема
        self._add_settings_card(design_frame, "settings_theme", L.get("settings_theme_desc", "Choose application appearance / Выберите оформление приложения / Виберіть оформлення додатку"))
        theme_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 20))

        theme_btn = ctk.CTkButton(
            theme_frame,
            text=L["theme_light"],
            width=100,
            height=36,
            command=lambda: self._change_theme("Light"),
            fg_color=accent_color if self.current_theme == "Light" else bg_card,
            text_color=text_primary if self.current_theme == "Light" else text_secondary,
            corner_radius=rad
        )
        theme_btn.pack(side="left", padx=8)

        theme_btn2 = ctk.CTkButton(
            theme_frame,
            text=L["theme_dark"],
            width=100,
            height=36,
            command=lambda: self._change_theme("Dark"),
            fg_color=accent_color if self.current_theme == "Dark" else bg_card,
            text_color=text_primary if self.current_theme == "Dark" else text_secondary,
            corner_radius=rad
        )
        theme_btn2.pack(side="left", padx=8)

        theme_btn3 = ctk.CTkButton(
            theme_frame,
            text=L["theme_sys"],
            width=100,
            height=36,
            command=lambda: self._change_theme("System"),
            fg_color=accent_color if self.current_theme == "System" else bg_card,
            text_color=text_primary if self.current_theme == "System" else text_secondary,
            corner_radius=rad
        )
        theme_btn3.pack(side="left", padx=8)

        self.theme_buttons = {"Light": theme_btn, "Dark": theme_btn2, "System": theme_btn3}

        # Card: RGB / Карточка: RGB / Картка: RGB
        self._add_settings_card(design_frame, "rgb_label", L.get("rgb_label_desc", "Colorful border animation / Цветная анимация границ / Кольорова анімація границь"))
        rgb_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        rgb_frame.pack(fill="x", pady=(0, 20))

        self._rgb_on_btn_ref = ctk.CTkButton(
            rgb_frame, text=L["rgb_on"], width=100, height=36,
            command=lambda: self._set_rgb(True),
            fg_color=accent_color if self.rgb_enabled.get() else bg_card,
            text_color=text_primary if self.rgb_enabled.get() else text_secondary,
            corner_radius=rad
        )
        self._rgb_on_btn_ref.pack(side="left", padx=8)

        self._rgb_off_btn_ref = ctk.CTkButton(
            rgb_frame, text=L["rgb_off"], width=100, height=36,
            command=lambda: self._set_rgb(False),
            fg_color=accent_color if not self.rgb_enabled.get() else bg_card,
            text_color=text_primary if not self.rgb_enabled.get() else text_secondary,
            corner_radius=rad
        )
        self._rgb_off_btn_ref.pack(side="left", padx=8)

        # Card: RGB Speed / Карточка: Скорость RGB / Картка: Швидкість RGB
        self._add_settings_card(design_frame, "rgb_speed", L.get("rgb_speed_desc", "RGB animation speed / Скорость RGB анимации / Швидкість RGB анімації"))
        speed_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        speed_frame.pack(fill="x", pady=(0, 20))

        speeds = [("slow", L.get("rgb_speed_slow", "Slow / Медленная / Повільна")),
                  ("normal", L.get("rgb_speed_normal", "Normal / Нормальная / Нормальна")),
                  ("fast", L.get("rgb_speed_fast", "Fast / Быстрая / Швидка"))]
        for speed_val, speed_name in speeds:
            btn = ctk.CTkButton(
                speed_frame, text=speed_name, width=100, height=36,
                command=lambda s=speed_val: self._set_rgb_speed(s),
                fg_color=accent_color if getattr(self, 'rgb_speed_setting', 'normal') == speed_val else bg_card,
                text_color=text_primary if getattr(self, 'rgb_speed_setting', 'normal') == speed_val else text_secondary,
                corner_radius=rad
            )
            btn.pack(side="left", padx=8)
            if speed_val == "slow":
                self._rgb_speed_btn_slow = btn
            elif speed_val == "normal":
                self._rgb_speed_btn_normal = btn
            else:
                self._rgb_speed_btn_fast = btn

        # Card: RGB Width / Карточка: Толщина RGB / Картка: Товщина RGB
        self._add_settings_card(design_frame, "rgb_width", L.get("rgb_width_desc", "RGB border thickness / Толщина RGB подсветки / Товщина RGB підсвітки"))
        width_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        width_frame.pack(fill="x", pady=(0, 20))

        widths = [("thin", L.get("rgb_width_thin", "Thin / Тонкая / Тонка")),
                  ("normal", L.get("rgb_width_normal", "Normal / Средняя / Середня")),
                  ("thick", L.get("rgb_width_thick", "Thick / Толстая / Товста"))]
        for width_val, width_name in widths:
            btn = ctk.CTkButton(
                width_frame, text=width_name, width=100, height=36,
                command=lambda w=width_val: self._set_rgb_width(w),
                fg_color=accent_color if getattr(self, 'rgb_width_setting', 'normal') == width_val else bg_card,
                text_color=text_primary if getattr(self, 'rgb_width_setting', 'normal') == width_val else text_secondary,
                corner_radius=rad
            )
            btn.pack(side="left", padx=8)
            if width_val == "thin":
                self._rgb_width_btn_thin = btn
            elif width_val == "normal":
                self._rgb_width_btn_normal = btn
            else:
                self._rgb_width_btn_thick = btn

        # Card: Font size / Карточка: Размер шрифта / Картка: Розмір шрифту
        self._add_settings_card(design_frame, "font_size", L.get("font_size_desc", "Interface text size / Размер текста в интерфейсе / Розмір тексту в інтерфейсі"))
        font_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        font_frame.pack(fill="x", pady=(0, 20))

        self.font_size_value = ctk.CTkLabel(font_frame, text=f"{self.current_font_size}px",
                                           font=("Segoe UI", 18, "bold"), text_color=accent_color)
        self.font_size_value.pack(pady=(0, 5))

        self._font_update_timer = None

        def on_font_size_change(val) -> None:
            """
            Handle the font size change event.
            Обработчик события font size change.
            Обробник події font size change.
            """
            size = int(float(val))
            self.font_size_value.configure(text=f"{size}px")
            if self._font_update_timer:
                self.after_cancel(self._font_update_timer)
            self._font_update_timer = self.after(150, lambda: self._apply_font_size(size))

        self.font_size_slider = ctk.CTkSlider(font_frame, from_=10, to=20, number_of_steps=10,
                                             command=on_font_size_change, width=300)
        self.font_size_slider.set(self.current_font_size)
        self.font_size_slider.pack()

        # Card: Corner radius / Карточка: Закругление углов / Картка: Закруглення кутів
        self._add_settings_card(design_frame, "settings_radius", L.get("radius_desc", "Corner rounding of elements / Закругление углов элементов / Закруглення кутів елементів"))
        radius_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        radius_frame.pack(fill="x", pady=(0, 20))

        self.settings_radius_label = ctk.CTkLabel(radius_frame, text=f"{self.current_radius} px",
                                                 font=("Segoe UI", 14), text_color=accent_color)
        self.settings_radius_label.pack(pady=(0, 5))

        self._radius_update_timer = None

        def on_radius_change(val) -> None:
            """
            Handle the radius change event.
            Обработчик события radius change.
            Обробник події radius change.
            """
            new_radius = int(float(val))
            self.settings_radius_label.configure(text=f"{new_radius} px")
            if self._radius_update_timer:
                self.after_cancel(self._radius_update_timer)
            self._radius_update_timer = self.after(200, lambda: self._change_radius(new_radius))

        radius_slider = ctk.CTkSlider(radius_frame, from_=0, to=25, command=on_radius_change, width=300)
        radius_slider.set(self.current_radius)
        radius_slider.pack()

        # Card: PDF Theme / Карточка: Тема PDF / Картка: Тема PDF
        self._add_settings_card(design_frame, "pdf_theme", L.get("pdf_theme_desc", "PDF export appearance / Оформление экспорта в PDF / Оформлення експорту в PDF"))
        pdf_theme_frame = ctk.CTkFrame(design_frame, fg_color="transparent")
        pdf_theme_frame.pack(fill="x", pady=(0, 20))

        current_pdf_theme = self.config.get("PDF_THEME", "light")

        self.pdf_theme_light_btn = ctk.CTkButton(
            pdf_theme_frame, text=L.get("pdf_theme_light", "Light / Светлая / Світла"), width=120, height=36,
            command=lambda: self._set_pdf_theme("light"),
            fg_color=accent_color if current_pdf_theme == "light" else bg_card,
            text_color=text_primary if current_pdf_theme == "light" else text_secondary,
            corner_radius=rad
        )
        self.pdf_theme_light_btn.pack(side="left", padx=8)

        self.pdf_theme_dark_btn = ctk.CTkButton(
            pdf_theme_frame, text=L.get("pdf_theme_dark", "Dark / Тёмная / Темна"), width=120, height=36,
            command=lambda: self._set_pdf_theme("dark"),
            fg_color=accent_color if current_pdf_theme == "dark" else bg_card,
            text_color=text_primary if current_pdf_theme == "dark" else text_secondary,
            corner_radius=rad
        )
        self.pdf_theme_dark_btn.pack(side="left", padx=8)

        # ----- CATEGORY: SECURITY -----
        security_frame = self.category_frames["security"]

        # Card: Master password / Карточка: Мастер-пароль / Картка: Майстер-пароль
        self._add_settings_card(security_frame, "master_title", L.get("master_desc", "Program access protection / Защита доступа к программе / Захист доступу до програми"))
        master_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        master_frame.pack(fill="x", pady=(0, 20))

        self._master_status_label = ctk.CTkLabel(master_frame, text="", font=("Segoe UI", 12))
        self._master_status_label.pack(pady=(0, 10))
        self._update_master_status_label()

        self._master_set_btn = ctk.CTkButton(
            master_frame, text="", width=200, height=40,
            font=("Segoe UI", 13, "bold"), corner_radius=rad
        )
        self._master_set_btn.pack()
        self._update_master_buttons()

        # Card: 2FA / Карточка: 2FA / Картка: 2FA
        self._add_settings_card(security_frame, "2fa_title", L.get("2fa_description", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"))
        twofa_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        twofa_frame.pack(fill="x", pady=(0, 20))

        self._2fa_status_label = ctk.CTkLabel(
            twofa_frame,
            text=self._get_2fa_status_text(),
            font=("Segoe UI", 12, "bold"),
            text_color=self._get_2fa_status_color()
        )
        self._2fa_status_label.pack(pady=(0, 10))

        self._2fa_settings_btn = ctk.CTkButton(
            twofa_frame,
            text=L.get("2fa_settings_title", "2FA Settings / Настройки 2FA / Налаштування 2FA"),
            width=200,
            height=40,
            command=self._show_2fa_settings,
            fg_color=accent_color,
            hover_color=accent_hover,
            font=("Segoe UI", 13, "bold"),
            corner_radius=rad
        )
        self._2fa_settings_btn.pack()

        # Card: Auto-lock / Карточка: Автоблокировка / Картка: Автоблокування
        self._add_settings_card(security_frame, "auto_lock", L.get("auto_lock_desc", "Auto lock on inactivity / Автоматическая блокировка при бездействии / Автоматичне блокування при бездіяльності"))
        auto_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        auto_frame.pack(fill="x", pady=(0, 20))

        self._auto_lock_btn = ctk.CTkButton(
            auto_frame, text="", width=160, height=40,
            command=self._toggle_auto_lock,
            fg_color=accent_color if self.auto_lock_enabled.get() else bg_card,
            corner_radius=rad
        )
        self._auto_lock_btn.pack(pady=(0, 10))
        self._update_auto_lock_button()

        self._auto_lock_label_ref = ctk.CTkLabel(auto_frame, text="", font=("Segoe UI", 12))
        self._auto_lock_label_ref.pack()
        self._update_auto_lock_label()

        self._auto_timer = None

        def on_auto_timeout_change(val) -> None:
            """
            Handle the auto timeout change event.
            Обработчик события auto timeout change.
            Обробник події auto timeout change.
            """
            minutes = int(float(val))
            L_local = LANGUAGES[self.current_lang]
            self._auto_lock_label_ref.configure(text=L_local["auto_lock_timeout"].format(minutes))
            if self._auto_timer:
                self.after_cancel(self._auto_timer)
            self._auto_timer = self.after(100, lambda: self._apply_auto_timeout(minutes))

        self._auto_lock_slider = ctk.CTkSlider(auto_frame, from_=1, to=30, number_of_steps=29,
                                              width=300, command=on_auto_timeout_change)
        self._auto_lock_slider.set(self.auto_lock_timeout)
        self._auto_lock_slider.pack(pady=(10, 0))

        # Card: Clipboard / Карточка: Буфер обмена / Картка: Буфер обміну
        self._add_settings_card(security_frame, "clip_timeout", L.get("clip_timeout_desc", "Auto clear clipboard / Автоочистка буфера обмена / Автоочищення буфера обміну"))
        clip_frame = ctk.CTkFrame(security_frame, fg_color="transparent")
        clip_frame.pack(fill="x", pady=(0, 20))

        self._clip_timeout_label_ref = ctk.CTkLabel(clip_frame, text="", font=("Segoe UI", 12))
        self._clip_timeout_label_ref.pack(pady=(0, 10))

        self._clip_timer = None

        def on_clip_timeout_change(val) -> None:
            """
            Handle the clip timeout change event.
            Обработчик события clip timeout change.
            Обробник події clip timeout change.
            """
            seconds = int(float(val))
            L_local = LANGUAGES[self.current_lang]
            self._clip_timeout_label_ref.configure(text=L_local["clip_timeout"].format(seconds))
            if self._clip_timer:
                self.after_cancel(self._clip_timer)
            self._clip_timer = self.after(100, lambda: self._apply_clip_timeout(seconds))

        clip_slider = ctk.CTkSlider(clip_frame, from_=10, to=120, number_of_steps=110,
                                   width=300, command=on_clip_timeout_change)
        clip_slider.set(self.clipboard_timeout)
        clip_slider.pack()

        # ----- CATEGORY: GENERAL -----
        general_frame = self.category_frames["general"]

        # Card: Sound / Карточка: Звук / Картка: Звук
        self._add_settings_card(general_frame, "settings_sound", L.get("sound_desc", "Sound effects for actions / Звуковые эффекты при действиях / Звукові ефекти при діях"))
        sound_frame = ctk.CTkFrame(general_frame, fg_color="transparent")
        sound_frame.pack(fill="x", pady=(0, 20))

        self._sound_btn = ctk.CTkButton(
            sound_frame, text="", width=160, height=40,
            command=self._toggle_sound_settings,
            fg_color=accent_color if self.sound_enabled.get() else bg_card,
            corner_radius=rad
        )
        self._sound_btn.pack()
        self._update_sound_button()

        # Card: Auto save / Карточка: Автосохранение / Картка: Автозбереження
        self._add_settings_card(general_frame, "auto_save_label", L.get("auto_save_desc", "Automatically save passwords / Автоматическое сохранение паролей / Автоматичне збереження паролів"))
        autosave_frame = ctk.CTkFrame(general_frame, fg_color="transparent")
        autosave_frame.pack(fill="x", pady=(0, 20))

        self.auto_save_btn = ctk.CTkButton(
            autosave_frame, text="", width=160, height=40,
            command=self._toggle_auto_save,
            fg_color=accent_color if self.auto_save_var.get() else bg_card,
            corner_radius=rad
        )
        self.auto_save_btn.pack()
        self._update_auto_save_button()

        # Settings Profiles / Профили настроек / Профілі налаштувань
        self._add_settings_card(general_frame, "settings_profiles", L.get("settings_profiles_desc", "Save and load settings profiles / Сохраняйте и загружайте профили настроек / Зберігайте та завантажуйте профілі налаштувань"))
        profiles_frame = ctk.CTkFrame(general_frame, fg_color="transparent")
        profiles_frame.pack(fill="x", pady=(0, 20))

        profile_btn_frame = ctk.CTkFrame(profiles_frame, fg_color="transparent")
        profile_btn_frame.pack()

        self.save_profile_btn = ctk.CTkButton(
            profile_btn_frame, text=L.get("save_profile", "Save Profile / Сохранить профиль / Зберегти профіль"),
            command=self._save_settings_profile, width=140, height=36,
            fg_color="#2d6a4f", corner_radius=rad, font=("Segoe UI", 12)
        )
        self.save_profile_btn.pack(side="left", padx=5)

        self.load_profile_btn = ctk.CTkButton(
            profile_btn_frame, text=L.get("load_profile", "Load Profile / Загрузить профиль / Завантажити профіль"),
            command=self._load_settings_profile, width=140, height=36,
            fg_color="#1f538d", corner_radius=rad, font=("Segoe UI", 12)
        )
        self.load_profile_btn.pack(side="left", padx=5)

        self.reset_profile_btn = ctk.CTkButton(
            profile_btn_frame, text=L.get("reset_profile", "Reset / Сбросить / Скинути"),
            command=self._reset_settings_profile, width=140, height=36,
            fg_color="#8b0000", corner_radius=rad, font=("Segoe UI", 12)
        )
        self.reset_profile_btn.pack(side="left", padx=5)

        # ========== CLOUD SYNC SECTION ==========
        cloud_frame = self.category_frames["cloud"]

        # Load saved sync config once
        try:
            from utils.cloud_sync import load_sync_config
            _sync_cfg = load_sync_config() or {}
        except (ImportError, OSError, ValueError, KeyError):
            _sync_cfg = {}

        def _cfg_get(key, default="") -> Any:
            """
            Handle cfg get.
            Обработать cfg get.
            Обробити cfg get.
            """
            key_map = {
                "SYNC_PROVIDER": "provider",
                "SYNC_URL":      "url",
                "SYNC_USERNAME": "username",
                "SYNC_PASSWORD": "password",
            }
            return _sync_cfg.get(key_map.get(key, key), default)

        self._add_settings_card(cloud_frame, "sync_title",
            L.get("sync_desc", "Sync encrypted database via WebDAV."))

        note_frame = ctk.CTkFrame(cloud_frame, fg_color="#1e2a1e", corner_radius=8)
        note_frame.pack(fill="x", padx=2, pady=(0, 14))
        ctk.CTkLabel(note_frame,
            text=L.get("sync_security_note",
                "Only the encrypted file is synced — your key never leaves the device"),
            font=("Segoe UI", 11), text_color="#6dbf6d",
            wraplength=560, justify="left").pack(anchor="w", padx=12, pady=8)

        # ── Provider ──────────────────────────────────────────────
        PROVIDERS = [
            ("nextcloud", "Nextcloud",
             L.get("sync_nextcloud_desc", "Your own Nextcloud server")),
            ("pcloud",    "🇨🇭 pCloud",
             L.get("sync_pcloud_desc", "Swiss cloud storage")),
            ("box",       "Box",
             L.get("sync_box_desc", "Box cloud storage")),
            ("webdav",    L.get("sync_provider_webdav", "Custom WebDAV"),
             L.get("sync_webdav_desc", "Any WebDAV-compatible server")),
        ]
        PROV_URLS = {
            "nextcloud": "https://your-server.com/remote.php/dav/files/username/",
            "pcloud":    "https://webdav.pcloud.com/",
            "box":       "https://dav.box.com/dav/",
            "webdav":    "https://your-server.com/webdav/",
        }

        prov_card = ctk.CTkFrame(cloud_frame, fg_color="#1c1c2e", corner_radius=10)
        prov_card.pack(fill="x", padx=2, pady=(0, 10))
        ctk.CTkLabel(prov_card,
            text=L.get("sync_provider_header", "Provider"),
            font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(10, 6))

        sync_provider_var = tk.StringVar(value=_cfg_get("SYNC_PROVIDER", "nextcloud"))
        prov_radio_row = ctk.CTkFrame(prov_card, fg_color="transparent")
        prov_radio_row.pack(anchor="w", padx=14, pady=(0, 4))

        prov_desc_lbl = ctk.CTkLabel(prov_card, text="",
            font=("Segoe UI", 11), text_color="gray")
        prov_desc_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        sync_url_var  = tk.StringVar(value=_cfg_get("SYNC_URL", ""))
        url_entry_ref = []

        def _on_provider_change(*_) -> None:
            """
            Handle the provider change event.
            Обработчик события provider change.
            Обробник події provider change.
            """
            prov = sync_provider_var.get()
            desc = next((d for v, _, d in PROVIDERS if v == prov), "")
            prov_desc_lbl.configure(text=desc)
            if url_entry_ref:
                url_entry_ref[0].configure(placeholder_text=PROV_URLS.get(prov, ""))

        for val, label, _ in PROVIDERS:
            ctk.CTkRadioButton(prov_radio_row, text=label,
                variable=sync_provider_var, value=val,
                font=("Segoe UI", 12),
                command=_on_provider_change).pack(side="left", padx=(0, 18))

        _on_provider_change()

        # ── Fields card ───────────────────────────────────────────
        fields_card = ctk.CTkFrame(cloud_frame, fg_color="#1c1c2e", corner_radius=10)
        fields_card.pack(fill="x", padx=2, pady=(0, 10))

        def _field(parent, label_text, var, show="", placeholder="") -> Any:
            """
            Handle field.
            Обработать field.
            Обробити field.
            """
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(10, 0))
            ctk.CTkLabel(row, text=label_text,
                font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w", pady=(0, 4))
            entry = ctk.CTkEntry(row, textvariable=var, height=36,
                font=("Segoe UI", 12), show=show, placeholder_text=placeholder)
            entry.pack(fill="x")
            return entry

        url_entry = _field(fields_card,
            L.get("sync_url", "WebDAV Server URL") + ":",
            sync_url_var,
            placeholder=PROV_URLS.get(_cfg_get("SYNC_PROVIDER", "nextcloud"), ""))
        url_entry_ref.append(url_entry)

        sync_user_var = tk.StringVar(value=_cfg_get("SYNC_USERNAME", ""))
        _field(fields_card,
            L.get("sync_username", "Username") + ":",
            sync_user_var,
            placeholder=L.get("sync_placeholder_user", "your_login"))

        sync_pass_var = tk.StringVar(value=_cfg_get("SYNC_PASSWORD", ""))
        _field(fields_card,
            L.get("sync_password", "Password") + ":",
            sync_pass_var, show="*", placeholder="••••••••")

        ctk.CTkFrame(fields_card, fg_color="transparent", height=12).pack()

        # ── Status ────────────────────────────────────────────────
        sync_status_lbl = ctk.CTkLabel(cloud_frame, text="",
            font=("Segoe UI", 12), text_color="gray")
        sync_status_lbl.pack(anchor="w", pady=(0, 6))

        # ── Buttons ───────────────────────────────────────────────
        sync_btn_row = ctk.CTkFrame(cloud_frame, fg_color="transparent")
        sync_btn_row.pack(fill="x", pady=(0, 10))

        def _save_sync_cfg() -> None:
            """
            Save sync cfg.
            Сохранить sync cfg.
            Зберегти sync cfg.
            """
            try:
                from utils.cloud_sync import save_sync_config
                save_sync_config({
                    "provider": sync_provider_var.get(),
                    "url":      sync_url_var.get().strip(),
                    "username": sync_user_var.get().strip(),
                    "password": sync_pass_var.get(),
                })
            except (ImportError, OSError, ValueError, TypeError) as e:
                logger.error(f"Failed to save sync config: {e}")

        def _do_test() -> None:
            """
            Handle do test.
            Обработать do test.
            Обробити do test.
            """
            _save_sync_cfg()
            sync_status_lbl.configure(
                text=L.get("sync_testing", "Testing..."), text_color="gray")
            sync_status_lbl.update()
            try:
                from utils.cloud_sync import create_sync_from_config, load_sync_config
                cfg = load_sync_config() or {
                    "provider": sync_provider_var.get(),
                    "url": sync_url_var.get().strip(),
                    "username": sync_user_var.get().strip(),
                    "password": sync_pass_var.get()}
                sync = create_sync_from_config(cfg)
                if not sync:
                    sync_status_lbl.configure(
                        text=L.get("sync_not_configured", "Not configured"),
                        text_color="#e04040"); return
                ok, msg = sync.test_connection()
                sync_status_lbl.configure(
                    text=L.get("sync_conn_ok", "OK") if ok else f"[ERR] {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, ConnectionError, AttributeError) as e:
                sync_status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        def _do_upload() -> None:
            """
            Handle do upload.
            Обработать do upload.
            Обробити do upload.
            """
            _save_sync_cfg()
            sync_status_lbl.configure(
                text=L.get("sync_uploading", "Uploading..."), text_color="gray")
            sync_status_lbl.update()
            try:
                from utils.cloud_sync import create_sync_from_config, load_sync_config
                from storage.database_queries import get_db_path
                cfg = load_sync_config() or {
                    "provider": sync_provider_var.get(),
                    "url": sync_url_var.get().strip(),
                    "username": sync_user_var.get().strip(),
                    "password": sync_pass_var.get()}
                sync = create_sync_from_config(cfg)
                if not sync:
                    sync_status_lbl.configure(
                        text=L.get("sync_not_configured", "Not configured"),
                        text_color="#e04040"); return
                ok, msg = sync.upload(get_db_path())
                sync_status_lbl.configure(
                    text=L.get("sync_success_up", "Uploaded") if ok else f"[ERR] {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, ConnectionError, AttributeError) as e:
                sync_status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        def _do_download() -> None:
            """
            Handle do download.
            Обработать do download.
            Обробити do download.
            """
            _save_sync_cfg()
            sync_status_lbl.configure(
                text=L.get("sync_downloading", "Downloading..."), text_color="gray")
            sync_status_lbl.update()
            try:
                from utils.cloud_sync import create_sync_from_config, load_sync_config
                from storage.database_queries import get_db_path
                cfg = load_sync_config() or {
                    "provider": sync_provider_var.get(),
                    "url": sync_url_var.get().strip(),
                    "username": sync_user_var.get().strip(),
                    "password": sync_pass_var.get()}
                sync = create_sync_from_config(cfg)
                if not sync:
                    sync_status_lbl.configure(
                        text=L.get("sync_not_configured", "Not configured"),
                        text_color="#e04040"); return
                ok, msg = sync.download(get_db_path())
                sync_status_lbl.configure(
                    text=L.get("sync_success_down", "Downloaded") if ok else f"[ERR] {msg}",
                    text_color="#40b040" if ok else "#e04040")
            except (OSError, ValueError, RuntimeError, ConnectionError, AttributeError) as e:
                sync_status_lbl.configure(text=f"[ERR] {e}", text_color="#e04040")

        btn_cfg = dict(height=38, font=("Segoe UI", 12, "bold"),
                       text_color="white", corner_radius=8)
        ctk.CTkButton(sync_btn_row,
            text=L.get("sync_test", "Test connection"),
            fg_color="#5c4a8a", hover_color="#7a61b5",
            command=_do_test, **btn_cfg).pack(side="left", padx=(0, 8))
        ctk.CTkButton(sync_btn_row,
            text=L.get("sync_upload", "Upload"),
            fg_color="#107c10", hover_color="#159e15",
            command=_do_upload, **btn_cfg).pack(side="left", padx=(0, 8))
        ctk.CTkButton(sync_btn_row,
            text=L.get("sync_download", "Download"),
            fg_color="#0078d4", hover_color="#1a92ec",
            command=_do_download, **btn_cfg).pack(side="left")

        # ========== CLOSE BUTTON (general) ==========
        close_btn = ctk.CTkButton(
            general_frame, text=L.get("close", "Close / Закрыть / Закрити"), width=160, height=40,
            command=self._close_settings,
            fg_color="#8b0000", hover_color="#aa0000",
            font=("Segoe UI", 13, "bold"), corner_radius=rad
        )
        close_btn.pack(pady=(20, 0))

        # Save references / Сохраняем ссылки / Зберігаємо посилання
        self._radius_slider = radius_slider
        self._clip_slider = clip_slider
        self._font_slider = self.font_size_slider
        self._auto_lock_slider_ref = self._auto_lock_slider
        self._close_btn = close_btn
        self._search_entry = search_entry

        def on_close() -> None:
            """
            Handle the close event.
            Обработчик события close.
            Обробник події close.
            """
            try:
                self.config.save()
            except (OSError, IOError, AttributeError, TypeError) as e:
                logger.debug(f"Config save error on close / Ошибка сохранения конфига при закрытии / Помилка збереження конфігу при закритті: {e}")
            self._close_settings()

        self.settings_window.protocol("WM_DELETE_WINDOW", on_close)

    def _switch_category(self, category_key: str) -> None:
        """
        Switch between settings categories

        Переключает между категориями настроек
        Перемикає між категоріями налаштувань
        """
        actual_theme = self._get_actual_theme()
        is_dark = actual_theme == "dark"
        bg_card_hover = "#383838" if is_dark else "#f8f8f8"

        self._active_settings_category = category_key
        self._settings_search_active = False

        if hasattr(self, '_search_entry') and self._search_entry:
            try:
                if self._search_entry.get():
                    self._search_entry.delete(0, "end")
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

        self._show_all_settings_sections()

        for key, frame in self.category_frames.items():
            try:
                frame.pack_forget()
            except (tk.TclError, RuntimeError) as _:
                pass

        try:
            self.category_frames[category_key].pack(fill="both", expand=True)
        except (tk.TclError, RuntimeError, KeyError) as _:
            pass

        for key, btn in self.category_buttons.items():
            try:
                btn.configure(fg_color=bg_card_hover if key == category_key else "transparent")
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass

    def _add_separator(self, parent) -> None:
        """Add separator line (placeholder) / Добавить линию-разделитель (заглушка) / Додати лінію-розділювач (заглушка)"""
        pass

    def _close_settings(self) -> None:
        """
        Close settings window and cleanup

        Закрывает окно настроек и очищает ресурсы
        Закриває вікно налаштувань та очищує ресурси
        """
        if self.settings_window:
            try:
                self.settings_window.grab_release()
                self.settings_window.destroy()
            except (tk.TclError, AttributeError, RuntimeError) as _:
                pass
            self.settings_window = None
            self.category_buttons = {}
            self.category_frames = {}
            self.settings_cards = []
            self._settings_pack_options = {}
            self._settings_search_active = False
            self._active_settings_category = "design"
            self._master_set_btn = None
            self._master_status_label = None
            self._sound_btn = None
            self._rgb_on_btn_ref = None
            self._rgb_off_btn_ref = None
            self._rgb_speed_btn_slow = None
            self._rgb_speed_btn_normal = None
            self._rgb_speed_btn_fast = None
            self._rgb_width_btn_thin = None
            self._rgb_width_btn_normal = None
            self._rgb_width_btn_thick = None
            self.pdf_theme_light_btn = None
            self.pdf_theme_dark_btn = None
            self.settings_radius_label = None
            self._clip_timeout_label_ref = None
            self._auto_lock_btn = None
            self._auto_lock_slider = None
            self._auto_lock_label_ref = None
            self._radius_slider = None
            self._clip_slider = None
            self._font_slider = None
            self._auto_lock_slider_ref = None
            self._close_btn = None
            self._radius_timer = None
            self._clip_timer = None
            self._auto_timer = None
            self._font_timer = None
            self._2fa_status_label = None
            self._2fa_settings_btn = None
            self._2fa_info_label = None
            self.save_profile_btn = None
            self.load_profile_btn = None
            self.reset_profile_btn = None
            self._search_entry = None
