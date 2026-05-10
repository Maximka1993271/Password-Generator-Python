"""
Do not modify user .key, .log, .txt, or PDF files during audit.
Не изменять пользовательские .key, .log, .txt и PDF-файлы во время аудита.
Не змінювати користувацькі .key, .log, .txt та PDF-файли під час аудиту.

Keep comments in 3 languages.
Оставлять комментарии на 3 языках.
Залишати коментарі 3 мовами.

SecurePassPro v3.9 — Cryptographically secure password generator
Author / Автор: Maxim Melnikov
"""

from __future__ import annotations
from collections import deque
import hashlib
import logging
import math
import platform
import random
import secrets
import string
import sys
import os
import webbrowser
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Dict
import ctypes


def _show_startup_error(title, text):
    root = tk.Tk()
    root.withdraw()
    try:
        messagebox.showerror(title, text)
    finally:
        root.destroy()


_IS_WINDOWS = platform.system() == "Windows"
if _IS_WINDOWS:
    import winsound

if sys.version_info < (3, 9):
    _show_startup_error("Error", "Python 3.9+ required!")
    sys.exit(1)

try:
    import customtkinter as ctk
    import qrcode
    from PIL import Image
    from fpdf import FPDF
except ImportError as exc:
    _show_startup_error("Error", f"Required: pip install qrcode[pil] pillow customtkinter fpdf\n\n{exc}")
    sys.exit(1)

HISTORY_MAX = 50
AMBIGUOUS_CHARS = "il1Lo0O"
UNAMBIG_CHARS = "{}[]()/\\'\"`~,;:.<>"
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"
SUPPORTED_EXTENSIONS = [".txt", ".log", ".key", ".pdf"]


class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.text = ""
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def set_text(self, text):
        self.text = text

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro v3.9",
        "menu_title": "Меню",
        "len": "Длина",
        "author": "Автор: Максим Мельников",
        "upper": "Заглавные буквы",
        "lower": "Строчные буквы",
        "digits": "Цифры",
        "symb": "Спецсимволы",
        "ambig": "Исключить похожие (i, l, 1...)",
        "unambig": "Исключить не однозначные",
        "at_least": "Минимум 1 из каждой категории",
        "hide": "Скрывать символы",
        "btn_gen": "Сгенерировать",
        "btn_copy": "Копировать пароль",
        "btn_save": "Сохранить в файл",
        "btn_open": "Открыть файл",
        "btn_qr": "QR-код пароль",
        "btn_hist": "История",
        "btn_upd": "Обновить программу",
        "btn_about": "О программе",
        "btn_settings": "Настройки",
        "radius": "Закругление углов",
        "sound_on": "Звук: ВКЛ", "sound_off": "Звук: ВЫКЛ",
        "theme_sys": "Системная", "theme_dark": "Тёмная", "theme_light": "Светлая",
        "about_text": "Secure Pass Pro v3.9\n\nПрофессиональный инструмент для генерации паролей.\nИспользует криптографически стойкие алгоритмы.",
        "copied": "Скопировано! (60с)",
        "strength": "Стойкость: ~{0} вариантов",
        "crack_time": "{0}",
        "time_sec": "Несколько секунд на взлом",
        "time_day": "Дни на взлом",
        "time_year": "Года на взлом",
        "time_cent": "Столетия на взлом",
        "st_low": "Слабый пароль", "st_mid": "Средний пароль", "st_high": "Надежный пароль",
        "tt_gen": "Создать новый случайный пароль",
        "tt_copy": "Копировать в буфер (очистка через 60 сек)",
        "tt_save": "Сохранить текущий пароль в файл",
        "tt_open": "Открыть пароль из файла .key, .log или .txt",
        "tt_qr": "Создать QR-код для быстрого сканирования",
        "tt_hist": "Показать последние 50 паролей",
        "tt_upd": "Проверить наличие новой версии на GitHub",
        "tt_about": "Информация о разработчике и программе",
        "tt_settings": "Язык, звук и тема оформления",
        "settings_title": "Настройки",
        "settings_lang": "Язык интерфейса",
        "settings_sound": "Звук приложения",
        "settings_theme": "Тема оформления",
        "settings_radius": "Закругление углов",
        "close": "Закрыть",
        "err_cat": "Выберите хотя бы одну категорию!",
        "err_pool_small": "Слишком мало доступных символов после исключений!",
        "err_save": "Ошибка сохранения: {0}",
        "err_open": "Не удалось прочитать файл: {0}",
        "err_unsupported": "Неподдерживаемый тип файла: {0}",
        "err_integrity": "Критическая ошибка: Файл поврежден после записи!",
        "hist_empty": "История пуста...",
        "btn_clear_hist": "Очистить историю",
        "pdf_date": "Дата",
        "pdf_pass": "Пароль",
        "wiki_link": "Читать Security Logic Wiki",
        "err_title": "Ошибка",
    },
    "EN": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro v3.9",
        "menu_title": "Menu",
        "len": "Length",
        "author": "Author: Maxim Melnikov",
        "upper": "Uppercase",
        "lower": "Lowercase",
        "digits": "Digits",
        "symb": "Special symbols",
        "ambig": "Exclude ambiguous (i, l, 1...)",
        "unambig": "Exclude non-obvious",
        "at_least": "Min 1 from each category",
        "hide": "Hide symbols",
        "btn_gen": "Generate",
        "btn_copy": "Copy password",
        "btn_save": "Save to file",
        "btn_open": "Open file",
        "btn_qr": "Password QR-code",
        "btn_hist": "History",
        "btn_upd": "Update program",
        "btn_about": "About",
        "btn_settings": "Settings",
        "radius": "Corner radius",
        "sound_on": "Sound: ON", "sound_off": "Sound: OFF",
        "theme_sys": "System", "theme_dark": "Dark", "theme_light": "Light",
        "about_text": "Secure Pass Pro v3.9\n\nProfessional password generation tool.\nUses cryptographically secure algorithms.",
        "copied": "Copied! (60s)",
        "strength": "Strength: ~{0} combos",
        "crack_time": "{0}",
        "time_sec": "A few seconds to crack",
        "time_day": "Days to crack",
        "time_year": "Years to crack",
        "time_cent": "Centuries to crack",
        "st_low": "Weak password", "st_mid": "Medium password", "st_high": "Strong password",
        "tt_gen": "Create a new random password",
        "tt_copy": "Copy to clipboard (clears in 60 sec)",
        "tt_save": "Save current password to file",
        "tt_open": "Open password from .key, .log or .txt",
        "tt_qr": "Create a QR code for quick scanning",
        "tt_hist": "Show last 50 generated passwords",
        "tt_upd": "Check for new version on GitHub",
        "tt_about": "Developer and program info",
        "tt_settings": "Language, sound and theme",
        "settings_title": "Settings",
        "settings_lang": "Interface language",
        "settings_sound": "App Sound",
        "settings_theme": "Appearance theme",
        "settings_radius": "Corner radius",
        "close": "Close",
        "err_cat": "Select at least one category!",
        "err_pool_small": "Too few available characters after exclusions!",
        "err_save": "Save failed: {0}",
        "err_open": "Could not read file: {0}",
        "err_unsupported": "Unsupported file type: {0}",
        "err_integrity": "Critical error: File corrupted after write!",
        "hist_empty": "History is empty...",
        "btn_clear_hist": "Clear History",
        "pdf_date": "Date",
        "pdf_pass": "Password",
        "wiki_link": "Read Security Logic Wiki",
        "err_title": "Error",
    },
    "UA": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro v3.9",
        "menu_title": "Меню",
        "len": "Довжина",
        "author": "Автор: Максим Мельніков",
        "upper": "Великі літери",
        "lower": "Малі літери",
        "digits": "Цифри",
        "symb": "Спецсимволи",
        "ambig": "Виключити схожі (i, l, 1...)",
        "unambig": "Виключити не однозначні",
        "at_least": "Мінімум 1 з категорії",
        "hide": "Приховати символи",
        "btn_gen": "Згенерувати",
        "btn_copy": "Копіювати пароль",
        "btn_save": "Зберегти у файл",
        "btn_open": "Відкрити файл",
        "btn_qr": "QR-код пароль",
        "btn_hist": "Історія",
        "btn_upd": "Оновити програму",
        "btn_about": "Про програму",
        "btn_settings": "Налаштування",
        "radius": "Закруглення кутів",
        "sound_on": "Звук: ВКЛ", "sound_off": "Звук: ВИКЛ",
        "theme_sys": "Системна", "theme_dark": "Темна", "theme_light": "Світла",
        "about_text": "Secure Pass Pro v3.9\n\nПрофесійний інструмент для генерації паролів.\nВикористовує криптографічно стійкі алгоритми.",
        "copied": "Скопійовано! (60с)",
        "strength": "Стійкість: ~{0} варіантів",
        "crack_time": "{0}",
        "time_sec": "Кілька секунд на злам",
        "time_day": "Дні на злам",
        "time_year": "Роки на злам",
        "time_cent": "Століття на злам",
        "st_low": "Слабкий пароль", "st_mid": "Середній пароль", "st_high": "Надійний пароль",
        "tt_gen": "Створити новий випадковий пароль",
        "tt_copy": "Копіювати в буфер (очищення через 60 сек)",
        "tt_save": "Зберегти поточний пароль у файл",
        "tt_open": "Відкрити пароль з файлу .key, .log або .txt",
        "tt_qr": "Створити QR-код для швидкого сканування",
        "tt_hist": "Показати останні 50 паролів",
        "tt_upd": "Перевірити наявність нової версії на GitHub",
        "tt_about": "Інформація про розробника та програму",
        "tt_settings": "Мова, звук та тема оформлення",
        "settings_title": "Налаштування",
        "settings_lang": "Мова інтерфейсу",
        "settings_sound": "Звук програми",
        "settings_theme": "Тема оформлення",
        "settings_radius": "Закруглення кутів",
        "close": "Закрити",
        "err_cat": "Виберіть хоча б одну категорію!",
        "err_pool_small": "Занадто мало доступних символів після виключень!",
        "err_save": "Помилка збереження: {0}",
        "err_open": "Не вдалося прочитати файл: {0}",
        "err_unsupported": "Непідтримуваний тип файлу: {0}",
        "err_integrity": "Критична помилка: Файл пошкоджений після запису!",
        "hist_empty": "Історія порожня...",
        "btn_clear_hist": "Очистити історію",
        "pdf_date": "Дата",
        "pdf_pass": "Пароль",
        "wiki_link": "Читати Security Logic Wiki",
        "err_title": "Помилка",
    }
}


class UTF8PDF(FPDF):
    """Custom PDF class with UTF-8 support using DejaVu font"""
    
    def __init__(self):
        super().__init__()
        self.dejavu_loaded = False
    
    def load_dejavu_font(self, font_path):
        """Load DejaVu Sans font for UTF-8 support"""
        try:
            if os.path.exists(font_path):
                self.add_font('DejaVu', '', font_path, uni=True)
                self.dejavu_loaded = True
                return True
        except Exception:
            pass
        return False
    
    def draw_text(self, text):
        """Draw text with UTF-8 support"""
        if self.dejavu_loaded:
            self.set_font('DejaVu', size=12)
        else:
            self.set_font('Arial', size=12)
        self.cell(200, 10, txt=text, ln=True, align='C')


class SecurePassPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "RU"
        self.current_theme = "System"
        self.current_radius = 10
        self.history = deque(maxlen=HISTORY_MAX)
        self._radius_widgets = []
        self._clipboard_timer = None
        self._tooltips = {}
        self._icon_image = None
        self._pdf_font_path = self._get_resource_path("DejaVuSans.ttf")
        self._secure_random = random.SystemRandom()
        self.sound_enabled = tk.BooleanVar(value=True)
        self.settings_window = None
        self.about_window = None
        self.history_window = None
        self.qr_window = None
        self.lang_buttons = {}
        self.theme_buttons = {}
        
        # Оптимизация
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        
        self.title("Secure Pass Pro v3.9")
        self.resizable(False, False)

        self._setup_main_icon()
        
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symb_var = tk.BooleanVar(value=True)
        self.ambig_var = tk.BooleanVar(value=False)
        self.unambig_var = tk.BooleanVar(value=False)
        self.at_least_var = tk.BooleanVar(value=True)
        self.hide_var = tk.BooleanVar(value=False)

        self._setup_ui()
        self._apply_lang("RU")
        self._center_main_window()
        self._apply_window_rounding(self)
        
        # Загружаем настройки после создания UI
        self.after(50, self._load_all_settings)
        self.after(50, self._load_radius_settings)

    def _load_radius_settings(self):
        """Load saved corner radius from config file"""
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".securepasspro", "config.txt")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("RADIUS="):
                            radius = int(line.strip().split("=")[1])
                            if 0 <= radius <= 25:
                                self.current_radius = radius
                                self._change_radius(radius)
        except:
            pass

    def _save_radius_settings(self, radius):
        """Save corner radius to config file"""
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".securepasspro")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.txt")
            existing = {}
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            existing[key] = val
            existing["RADIUS"] = str(radius)
            with open(config_file, "w", encoding="utf-8") as f:
                for key, val in existing.items():
                    f.write(f"{key}={val}\n")
        except:
            pass

    def _load_all_settings(self):
        """Load all settings from config file"""
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".securepasspro", "config.txt")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("THEME="):
                            theme = line.strip().split("=")[1]
                            if theme in ["System", "Light", "Dark"]:
                                self.current_theme = theme
                                ctk.set_appearance_mode(theme)
                        elif line.startswith("LANG="):
                            lang = line.strip().split("=")[1]
                            if lang in ["RU", "EN", "UA"]:
                                self._apply_lang(lang)
                        elif line.startswith("SOUND="):
                            sound_val = line.strip().split("=")[1].lower() == "true"
                            self.sound_enabled.set(sound_val)
        except:
            pass

    def _save_theme_settings(self):
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".securepasspro")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.txt")
            existing = {}
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            existing[key] = val
            existing["THEME"] = self.current_theme
            with open(config_file, "w", encoding="utf-8") as f:
                for key, val in existing.items():
                    f.write(f"{key}={val}\n")
        except:
            pass

    def _save_language_settings(self):
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".securepasspro")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.txt")
            existing = {}
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            existing[key] = val
            existing["LANG"] = self.current_lang
            with open(config_file, "w", encoding="utf-8") as f:
                for key, val in existing.items():
                    f.write(f"{key}={val}\n")
        except:
            pass

    def _save_sound_settings(self):
        try:
            config_dir = os.path.join(os.path.expanduser("~"), ".securepasspro")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.txt")
            existing = {}
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, val = line.strip().split("=", 1)
                            existing[key] = val
            existing["SOUND"] = str(self.sound_enabled.get())
            with open(config_file, "w", encoding="utf-8") as f:
                for key, val in existing.items():
                    f.write(f"{key}={val}\n")
        except:
            pass

    def _apply_window_rounding(self, window):
        if not _IS_WINDOWS: return
        try:
            window.update()
            HWND = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, 
                DWMWA_WINDOW_CORNER_PREFERENCE, 
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 
                ctypes.sizeof(ctypes.c_int(DWMWCP_ROUND))
            )
        except:
            pass

    def _get_icon_path(self):
        return self._get_resource_path("icon.ico")

    def _get_resource_path(self, filename):
        if hasattr(sys, '_MEIPASS'):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, filename)

    def _set_window_icon(self, window):
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            try:
                if _IS_WINDOWS:
                    window.iconbitmap(icon_path)
                else:
                    if self._icon_image is None:
                        self._icon_image = tk.PhotoImage(file=icon_path)
                    window.iconphoto(True, self._icon_image)
            except:
                pass

    def _setup_main_icon(self):
        self._set_window_icon(self)

    def _play_sound(self, sound_type: str = "click"):
        if not self.sound_enabled.get() or not _IS_WINDOWS: 
            return
        try:
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            file_name = "Computer Mouse Click.mp3"
            file_path = os.path.join(base_path, file_name)
            if os.path.exists(file_path):
                winmm = ctypes.windll.winmm
                alias = "app_click"
                winmm.mciSendStringW(f'close {alias}', None, 0, 0)
                winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, 0)
                winmm.mciSendStringW(f'play {alias} from 0', None, 0, 0)
                self.after(1000, lambda: winmm.mciSendStringW(f'close {alias}', None, 0, 0))
        except:
            pass

    def _center_main_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.winfo_screenheight() // 2) - (780 // 2)
        self.geometry(f"850x780+{x}+{y}")

    def _center_window_relative_to_parent(self, window, width, height):
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

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

        self.lbl_title = ctk.CTkLabel(self.left_panel, text="Secure Pass Pro v3.9", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(5, 0))
        
        self.lbl_author = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 10))

        self.lbl_len = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_len.pack()
        self.slider_len = ctk.CTkSlider(self.left_panel, from_=4, to=64, number_of_steps=60, width=400, command=self._update_len_label)
        self.slider_len.set(20)
        self.slider_len.pack(pady=5)

        self.cb_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.cb_frame.pack(pady=5)
        
        self.cb_upper = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.upper_var)
        self.cb_upper.grid(row=0, column=1, padx=(70, 20), pady=2, sticky="w")

        self.cb_lower = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.lower_var)
        self.cb_lower.grid(row=0, column=0, padx=(20, 70), pady=2, sticky="w")

        self.cb_digits = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.digits_var)
        self.cb_digits.grid(row=1, column=1, padx=(70, 20), pady=2, sticky="w")

        self.cb_symb = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.symb_var)
        self.cb_symb.grid(row=1, column=0, padx=(20, 70), pady=2, sticky="w")

        self.cb_ambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.ambig_var)
        self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=(8, 2), sticky="w")

        self.cb_unambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.unambig_var)
        self.cb_unambig.grid(row=3, column=0, columnspan=2, padx=20, pady=2, sticky="w")

        self.cb_at_least = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.at_least_var)
        self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=(8, 2), sticky="w")

        self.cb_hide = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.hide_var, command=self._toggle_hide)
        self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=2, sticky="w")

        self.entry_res = ctk.CTkEntry(self.left_panel, height=50, font=("Consolas", 22), justify="center")
        self.entry_res.pack(pady=10, padx=40, fill="x")
        self._radius_widgets.append(self.entry_res)

        # Звезды надежности пароля
        self.lbl_stars_top = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 24))
        self.lbl_stars_top.pack(pady=(5, 0))

        self.lbl_strength_text = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_strength_text.pack()

        self.lbl_strength = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13))
        self.lbl_strength.pack()
        self.lbl_crack = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13, "bold"), wraplength=500)
        self.lbl_crack.pack(pady=(0, 5))

        self.right_panel = ctk.CTkFrame(self, width=250)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.right_panel.grid_propagate(False)
        self._radius_widgets.append(self.right_panel)

        self.lbl_menu = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 18, "bold"))
        self.lbl_menu.pack(pady=15)

        self.btn_gen = self._create_menu_btn(self.right_panel, "btn_gen", "tt_gen", self._generate, "#0067c0")
        self.btn_copy = self._create_menu_btn(self.right_panel, "btn_copy", "tt_copy", self._copy, "#107c10")
        self.btn_save = self._create_menu_btn(self.right_panel, "btn_save", "tt_save", self._save, "#0078d4")
        self.btn_open = self._create_menu_btn(self.right_panel, "btn_open", "tt_open", self._open, "#0078d4")
        self.btn_qr = self._create_menu_btn(self.right_panel, "btn_qr", "tt_qr", self._show_qr, "#8764b8")
        self.btn_hist = self._create_menu_btn(self.right_panel, "btn_hist", "tt_hist", self._show_history, "#4b4b4b")
        self.btn_upd = self._create_menu_btn(self.right_panel, "btn_upd", "tt_upd", lambda: webbrowser.open(UPD_URL), "#ca5010")
        self.btn_settings = self._create_menu_btn(self.right_panel, "btn_settings", "tt_settings", self._show_settings, "#2d6a4f")
        self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#4b4b4b")

        # Нижняя панель с золотыми звездами (оценка программы)
        self.bottom_frame = ctk.CTkFrame(self, fg_color=("#e0e0e0", "#1e1e1e"), corner_radius=15)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        
        self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_app_rating.pack(pady=(5, 5))

    def _create_menu_btn(self, parent, lang_key, tt_key, cmd, color):
        colors_map = {
            "#0067c0": "#00A2FF", "#107c10": "#20CF20", "#0078d4": "#309FFF",
            "#8764b8": "#B080FF", "#4b4b4b": "#808080", "#ca5010": "#FF8C00", "#2d6a4f": "#40916c"
        }
        neon_color = colors_map.get(color, color)

        btn = ctk.CTkButton(
            parent, 
            text="", 
            command=lambda command=cmd: self._run_menu_command(command),
            fg_color=color, 
            height=45, 
            border_width=2, 
            border_color=neon_color,
            font=("Segoe UI Variable", 13, "bold"),
            hover_color=neon_color,
            corner_radius=self.current_radius
        )
        btn.pack(pady=6, padx=15, fill="x")
        
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        
        self._radius_widgets.append(btn)
        self._tooltips[lang_key] = ToolTip(btn)
        return btn

    def _run_menu_command(self, command):
        self._play_sound("click")
        command()

    def _change_radius(self, val):
        rad = int(val)
        self.current_radius = rad
        
        menu_btns = [
            self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, 
            self.btn_qr, self.btn_hist, self.btn_upd, self.btn_settings, self.btn_about
        ]

        for btn in menu_btns:
            btn.configure(corner_radius=rad)

        for w in self._radius_widgets:
            if w not in menu_btns: 
                try:
                    w.configure(corner_radius=rad)
                except:
                    pass

        cb_rad = max(rad // 2, 0)
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
                   self.cb_ambig, self.cb_unambig, self.cb_at_least, self.cb_hide]:
            cb.configure(corner_radius=cb_rad)
        
        self.bottom_frame.configure(corner_radius=rad)
        self.right_panel.configure(corner_radius=rad)
        
        # Update radius label in settings window if open
        if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self.settings_radius_label.configure(text=f"{L['settings_radius']}: {rad}")
        
        # Save radius setting
        self._save_radius_settings(rad)

    def _show_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title(L["settings_title"])
        self.settings_window.resizable(False, False)
        self._set_window_icon(self.settings_window)
        
        self.settings_window.transient(self)
        self.settings_window.attributes('-topmost', True)
        self.settings_window.after(100, lambda: self.settings_window.attributes('-topmost', False))
        self.settings_window.focus_force()
        self.settings_window.grab_set()
        
        self._center_window_relative_to_parent(self.settings_window, 420, 480)
        self._apply_window_rounding(self.settings_window)
        
        self.settings_window.protocol("WM_DELETE_WINDOW", self._close_settings)
        
        main_frame = ctk.CTkFrame(self.settings_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Language selection
        lang_label = ctk.CTkLabel(main_frame, text=L["settings_lang"], font=("Segoe UI", 16, "bold"))
        lang_label.pack(pady=(0, 8))
        
        lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lang_frame.pack(pady=(0, 12))
        
        for lang in ["RU", "EN", "UA"]:
            btn = ctk.CTkButton(
                lang_frame, 
                text=lang, 
                width=80, 
                height=35,
                command=lambda l=lang: self._change_language(l),
                fg_color="#2d6a4f" if self.current_lang == lang else "#4b4b4b",
                font=("Segoe UI", 14, "bold"),
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.lang_buttons[lang] = btn
        
        # Separator
        sep1 = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        sep1.pack(fill="x", pady=8)
        
        # Theme selection
        theme_label = ctk.CTkLabel(main_frame, text=L["settings_theme"], font=("Segoe UI", 16, "bold"))
        theme_label.pack(pady=(8, 8))
        
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(pady=(0, 12))
        
        sys_btn = ctk.CTkButton(
            theme_frame, text=L["theme_sys"], width=100, height=35,
            command=lambda: self._change_theme("System"),
            fg_color="#2d6a4f" if self.current_theme == "System" else "#4b4b4b",
            font=("Segoe UI", 12), corner_radius=8
        )
        sys_btn.pack(side="left", padx=5)
        
        light_btn = ctk.CTkButton(
            theme_frame, text=L["theme_light"], width=100, height=35,
            command=lambda: self._change_theme("Light"),
            fg_color="#2d6a4f" if self.current_theme == "Light" else "#4b4b4b",
            font=("Segoe UI", 12), corner_radius=8
        )
        light_btn.pack(side="left", padx=5)
        
        dark_btn = ctk.CTkButton(
            theme_frame, text=L["theme_dark"], width=100, height=35,
            command=lambda: self._change_theme("Dark"),
            fg_color="#2d6a4f" if self.current_theme == "Dark" else "#4b4b4b",
            font=("Segoe UI", 12), corner_radius=8
        )
        dark_btn.pack(side="left", padx=5)
        
        self.theme_buttons = {"System": sys_btn, "Light": light_btn, "Dark": dark_btn}
        
        # Separator
        sep2 = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        sep2.pack(fill="x", pady=8)
        
        # Corner radius selection
        radius_label = ctk.CTkLabel(main_frame, text=f"{L['settings_radius']}: {self.current_radius}", font=("Segoe UI", 16, "bold"))
        radius_label.pack(pady=(8, 5))
        self.settings_radius_label = radius_label
        
        radius_slider = ctk.CTkSlider(main_frame, from_=0, to=25, command=self._on_radius_change, width=300)
        radius_slider.set(self.current_radius)
        radius_slider.pack(pady=(5, 12))
        
        # Separator
        sep3 = ctk.CTkFrame(main_frame, height=2, fg_color="gray")
        sep3.pack(fill="x", pady=8)
        
        # Sound toggle
        sound_label = ctk.CTkLabel(main_frame, text=L["settings_sound"], font=("Segoe UI", 16, "bold"))
        sound_label.pack(pady=(8, 8))
        
        sound_text = L["sound_on"] if self.sound_enabled.get() else L["sound_off"]
        sound_btn = ctk.CTkButton(
            main_frame,
            text=sound_text,
            width=150,
            height=40,
            command=self._toggle_sound_settings,
            fg_color="#0078d4",
            font=("Segoe UI", 14),
            corner_radius=10
        )
        sound_btn.pack(pady=(0, 15))
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text=L["close"],
            command=self._close_settings,
            fg_color="#ca5010",
            width=150,
            height=40,
            font=("Segoe UI", 14),
            corner_radius=10
        )
        close_btn.pack(pady=(5, 10))
        
        self.settings_labels = {
            'lang': lang_label,
            'theme': theme_label,
            'sound': sound_label,
            'close_btn': close_btn,
            'sound_btn': sound_btn,
            'radius_slider': radius_slider
        }

    def _on_radius_change(self, val):
        """Handle radius slider change"""
        rad = int(val)
        if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self.settings_radius_label.configure(text=f"{L['settings_radius']}: {rad}")
        self._change_radius(rad)

    def _close_settings(self):
        if self.settings_window:
            self.settings_window.grab_release()
            self.settings_window.destroy()
            self.settings_window = None
            self.settings_labels = {}
            self.lang_buttons = {}
            self.theme_buttons = {}

    def _change_language(self, lang):
        self.current_lang = lang
        self._apply_lang(lang)
        self._save_language_settings()
        
        # Update language button colors
        if self.lang_buttons:
            for l, btn in self.lang_buttons.items():
                if btn.winfo_exists():
                    btn.configure(fg_color="#2d6a4f" if l == lang else "#4b4b4b")
        
        if self.settings_window and self.settings_window.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self.settings_window.title(L["settings_title"])
            
            if self.settings_labels:
                if 'lang' in self.settings_labels and self.settings_labels['lang']:
                    self.settings_labels['lang'].configure(text=L["settings_lang"])
                if 'theme' in self.settings_labels and self.settings_labels['theme']:
                    self.settings_labels['theme'].configure(text=L["settings_theme"])
                if 'sound' in self.settings_labels and self.settings_labels['sound']:
                    self.settings_labels['sound'].configure(text=L["settings_sound"])
                if 'close_btn' in self.settings_labels and self.settings_labels['close_btn']:
                    self.settings_labels['close_btn'].configure(text=L["close"])
                if 'sound_btn' in self.settings_labels and self.settings_labels['sound_btn']:
                    self.settings_labels['sound_btn'].configure(text=L["sound_on"] if self.sound_enabled.get() else L["sound_off"])
            
            # Update radius label
            if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
                self.settings_radius_label.configure(text=f"{L['settings_radius']}: {self.current_radius}")
            
            # Update theme buttons text
            if hasattr(self, "theme_buttons"):
                if "System" in self.theme_buttons and self.theme_buttons["System"].winfo_exists():
                    self.theme_buttons["System"].configure(text=L["theme_sys"])
                if "Light" in self.theme_buttons and self.theme_buttons["Light"].winfo_exists():
                    self.theme_buttons["Light"].configure(text=L["theme_light"])
                if "Dark" in self.theme_buttons and self.theme_buttons["Dark"].winfo_exists():
                    self.theme_buttons["Dark"].configure(text=L["theme_dark"])

    def _change_theme(self, mode):
        """Safe theme change - close settings window first to avoid freezing"""
        self.current_theme = mode
        self._save_theme_settings()
        
        # Update button colors immediately
        if self.theme_buttons:
            for name, btn in self.theme_buttons.items():
                if btn.winfo_exists():
                    if name == mode:
                        btn.configure(fg_color="#2d6a4f")
                    else:
                        btn.configure(fg_color="#4b4b4b")
        
        # Close settings window to prevent freezing
        if self.settings_window and self.settings_window.winfo_exists():
            self._close_settings()
        
        # Apply theme with minimal delay
        def apply_theme():
            try:
                ctk.set_appearance_mode(mode)
                self.update_idletasks()
            except:
                pass
        
        self.after(50, apply_theme)

    def _toggle_sound_settings(self):
        self.sound_enabled.set(not self.sound_enabled.get())
        if hasattr(self, 'settings_labels') and self.settings_labels and 'sound_btn' in self.settings_labels and self.settings_labels['sound_btn']:
            L = LANGUAGES[self.current_lang]
            self.settings_labels['sound_btn'].configure(text=L["sound_on"] if self.sound_enabled.get() else L["sound_off"])
        self._play_sound("click")
        self._save_sound_settings()

    def _apply_lang(self, lang):
        self.current_lang = lang
        L = LANGUAGES[lang]
        self.lbl_author.configure(text=L["author"])
        self.lbl_menu.configure(text=L["menu_title"])
        self.lbl_title.configure(text=L["proton_title"])
        self._update_len_label(self.slider_len.get())
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_unambig.configure(text=L["unambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, 
                     self.btn_qr, self.btn_hist, self.btn_upd, self.btn_settings, self.btn_about]
        for btn in menu_btns:
            btn.configure(text=L[btn.lang_key])
            if btn.lang_key in self._tooltips:
                self._tooltips[btn.lang_key].set_text(L[btn.tt_key])
        
        self.title(L["win_title"])

    def _update_len_label(self, val):
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")

    def _toggle_hide(self):
        if self.hide_var.get():
            self.entry_res.configure(show="*")
        else:
            self.entry_res.configure(show="")

    def _generate(self):
        L = LANGUAGES[self.current_lang]
        exclude = set(AMBIGUOUS_CHARS if self.ambig_var.get() else "")
        if self.unambig_var.get(): exclude.update(set(UNAMBIG_CHARS))
        
        def get_chars(src, var):
            if not var.get(): return ""
            return "".join(c for c in src if c not in exclude)
            
        p_upper = get_chars(string.ascii_uppercase, self.upper_var)
        p_lower = get_chars(string.ascii_lowercase, self.lower_var)
        p_digits = get_chars(string.digits, self.digits_var)
        p_symb = get_chars(string.punctuation, self.symb_var)
        
        full_pool = p_upper + p_lower + p_digits + p_symb
        if not full_pool:
            self._play_sound("error")
            messagebox.showwarning(L.get("err_title", "Error"), L["err_cat"])
            return
        if len(set(full_pool)) < 2:
            self._play_sound("error")
            messagebox.showwarning(L.get("err_title", "Error"), L["err_pool_small"])
            return
            
        self._play_sound("success")
        length = int(self.slider_len.get())
        result = []
        
        if self.at_least_var.get():
            for p in [p_upper, p_lower, p_digits, p_symb]:
                if p: result.append(secrets.choice(p))
                
        if len(result) > length:
            random.shuffle(result)
            result = result[:length]
        else:
            while len(result) < length:
                result.append(secrets.choice(full_pool))
        random.shuffle(result)
        pwd = "".join(result)
        
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, pwd)
        
        pool_size = len(full_pool)
        entropy_bits = math.log2(pool_size) * length if pool_size else 0
        combinations = f"{pool_size**length:.1e}"
        self.lbl_strength.configure(text=L["strength"].format(combinations))
        
        # Звезды надежности пароля с правильными цветами
        if entropy_bits < 40:
            stars_display = "★☆☆☆☆"
            stars_color = "#FF4C4C"
            st_text = L["st_low"]
            crack_phrase = L["time_sec"]
        elif entropy_bits < 60:
            stars_display = "★★★☆☆"
            stars_color = "#FFA500"
            st_text = L["st_mid"]
            crack_phrase = L["time_day"]
        elif entropy_bits < 80:
            stars_display = "★★★★☆"
            stars_color = "#FFD700"
            st_text = L["st_mid"]
            crack_phrase = L["time_year"]
        else:
            stars_display = "★★★★★"
            stars_color = "#2ECC71"
            st_text = L["st_high"]
            crack_phrase = L["time_cent"]
        
        self.lbl_stars_top.configure(text=stars_display, text_color=stars_color)
        self.lbl_strength_text.configure(text=st_text, text_color=stars_color)
        self.lbl_crack.configure(text=L["crack_time"].format(crack_phrase), text_color=stars_color)
        
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        self.history.append(f"{timestamp} {pwd}")

    def _copy(self):
        pwd = str(self.entry_res.get())
        if not pwd: return
        L = LANGUAGES[self.current_lang]
        self._play_sound("copy")
        self.clipboard_clear()
        self.clipboard_append(pwd)
        
        if self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except:
                pass
        self._clipboard_timer = self.after(60000, lambda value=pwd: self._clear_clipboard_if_current(value))
        
        old_text = L["btn_copy"]
        self.btn_copy.configure(text=L["copied"])
        self.after(2000, lambda: self.btn_copy.configure(text=old_text))

    def _clear_clipboard_if_current(self, expected):
        try:
            if self.clipboard_get() == expected:
                self.clipboard_clear()
        except:
            pass
        finally:
            self._clipboard_timer = None

    def _verify_pdf(self, path):
        try:
            with open(path, "rb") as f:
                header = f.read(5)
                return header == b"%PDF-"
        except:
            return False

    def _verify_text_file(self, path, expected_bytes):
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest() == expected_hash
        except:
            return False

    def _get_supported_extension(self, path, extensions):
        ext = os.path.splitext(path)[1].lower()
        valid_exts = list(extensions)
        if ".pdf" not in valid_exts:
            valid_exts.append(".pdf")
        if ext not in valid_exts:
            raise ValueError(ext)
        return ext

    def _save(self):
        L = LANGUAGES[self.current_lang]
        pwd = self.entry_res.get()
        if not pwd: return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Supported Files", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
                ("Text File", "*.txt"),
                ("Password File", "*.key"), 
                ("Log File", "*.log"), 
                ("PDF File", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        if path:
            try:
                ext = self._get_supported_extension(path, SUPPORTED_EXTENSIONS)
                if ext == ".pdf":
                    # Create PDF with UTF-8 support
                    pdf = UTF8PDF()
                    pdf.set_author("Maxim Melnikov")
                    pdf.set_creator("Secure Pass Pro v3.9")
                    pdf.set_title("Secure Pass Pro Password")
                    pdf.add_page()
                    
                    # Load DejaVu font if available
                    dejavu_loaded = False
                    if os.path.exists(self._pdf_font_path):
                        try:
                            pdf.add_font('DejaVu', '', self._pdf_font_path, uni=True)
                            dejavu_loaded = True
                        except Exception:
                            pass
                    
                    # Set font
                    if dejavu_loaded:
                        pdf.set_font('DejaVu', '', 16)
                    else:
                        pdf.set_font('Arial', 'B', 16)
                    
                    pdf.cell(200, 10, txt="Secure Pass Pro v3.9", ln=True, align='C')
                    
                    # Set font for content
                    if dejavu_loaded:
                        pdf.set_font('DejaVu', '', 12)
                    else:
                        pdf.set_font('Arial', '', 12)
                    
                    pdf.ln(10)
                    
                    date_val = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    pdf.cell(200, 10, txt=f"{L['pdf_date']}: {date_val}", ln=True)
                    pdf.cell(200, 10, txt=f"{L['pdf_pass']}: {pwd}", ln=True)
                    
                    pdf.output(path)
                    if not self._verify_pdf(path): 
                        raise IOError(L["err_integrity"])
                else:
                    pwd_bytes = pwd.encode("utf-8")
                    with open(path, "wb") as f:
                        f.write(pwd_bytes)
                    if not self._verify_text_file(path, pwd_bytes): 
                        raise IOError(L["err_integrity"])
                self._play_sound("success")
            except Exception as e:
                messagebox.showerror(L.get("err_title", "Error"), L["err_save"].format(e))

    def _open(self):
        L = LANGUAGES[self.current_lang]
        supported_str = ";".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", supported_str),
                ("Password File", "*.key"), 
                ("Log File", "*.log"), 
                ("Text File", "*.txt"), 
                ("PDF File", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        
        if not path:
            return

        try:
            ext = os.path.splitext(path)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise ValueError(L["err_unsupported"].format(ext))

            if path.lower().endswith(".pdf"):
                if _IS_WINDOWS:
                    os.startfile(path)
                else:
                    webbrowser.open(f"file://{path}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    file_content = f.read().strip()
                    self.entry_res.delete(0, "end")
                    self.entry_res.insert(0, file_content)

            self._play_sound("success")

        except ValueError as ve:
            messagebox.showwarning(L.get("err_title", "Error"), str(ve))
        except Exception as e:
            messagebox.showerror(L.get("err_title", "Error"), L["err_open"].format(e))

    def _show_qr(self):
        pwd = self.entry_res.get()
        if not pwd: return
        
        if self.qr_window and self.qr_window.winfo_exists():
            self.qr_window.lift()
            self.qr_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        rad = self.current_radius
        
        self.qr_window = ctk.CTkToplevel(self)
        self.qr_window.title(L["btn_qr"])
        self._set_window_icon(self.qr_window)
        
        self.qr_window.transient(self)
        self.qr_window.attributes('-topmost', True)
        self.qr_window.after(100, lambda: self.qr_window.attributes('-topmost', False))
        
        self._center_window_relative_to_parent(self.qr_window, 380, 480)
        self._apply_window_rounding(self.qr_window)
        
        self.qr_window.protocol("WM_DELETE_WINDOW", self._close_qr)
        
        resampling_source = getattr(Image, "Resampling", Image)
        resampling_filter = getattr(resampling_source, "LANCZOS", getattr(Image, "NEAREST", 0))
        img = qrcode.make(pwd).resize((280, 280), resampling_filter)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
        
        f = ctk.CTkFrame(self.qr_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_qr"], font=("Segoe UI", 18, "bold")).pack()
        
        disp = ctk.CTkFrame(f, fg_color="white", corner_radius=rad, border_width=2, border_color="gray")
        disp.pack(pady=10)
        qr_label = ctk.CTkLabel(disp, image=ctk_img, text="")
        qr_label.image = ctk_img
        qr_label.pack(padx=10, pady=10)
        ctk.CTkButton(f, text="OK", command=self._close_qr, corner_radius=rad).pack(pady=10)
        
        self.qr_window.focus_force()

    def _close_qr(self):
        if self.qr_window:
            self.qr_window.destroy()
            self.qr_window = None

    def _show_history(self):
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        rad = self.current_radius
        
        self.history_window = ctk.CTkToplevel(self)
        self.history_window.title(L["btn_hist"])
        self._set_window_icon(self.history_window)
        
        self.history_window.transient(self)
        self.history_window.attributes('-topmost', True)
        self.history_window.after(100, lambda: self.history_window.attributes('-topmost', False))
        
        self._center_window_relative_to_parent(self.history_window, 500, 580)
        self._apply_window_rounding(self.history_window)
        
        self.history_window.protocol("WM_DELETE_WINDOW", self._close_history)
        
        f = ctk.CTkFrame(self.history_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_hist"], font=("Segoe UI", 20, "bold")).pack(pady=10)
        
        txt = ctk.CTkTextbox(f, font=("Consolas", 14), corner_radius=rad)
        txt.pack(fill="both", expand=True, pady=10)
        
        if not self.history:
            txt.insert("1.0", L["hist_empty"])
        else:
            history_snapshot = list(reversed(self.history))
            txt.insert("1.0", "\n".join(history_snapshot))
        
        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.pack(fill="x")
        ctk.CTkButton(
            btn_f,
            text=L["btn_clear_hist"],
            corner_radius=rad,
            fg_color="#d13438",
            command=lambda textbox=txt: self._clear_history_textbox(textbox)
        ).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="OK", corner_radius=rad, command=self._close_history).pack(side="right", padx=5)
        
        self.history_window.focus_force()
        self.history_textbox = txt

    def _close_history(self):
        if self.history_window:
            self.history_window.destroy()
            self.history_window = None
            self.history_textbox = None

    def _clear_history_textbox(self, textbox):
        L = LANGUAGES[self.current_lang]
        self.history.clear()
        textbox.delete("1.0", "end")
        textbox.insert("1.0", L["hist_empty"])

    def _show_about(self):
        if self.about_window and self.about_window.winfo_exists():
            self.about_window.lift()
            self.about_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        wiki_url = "https://github.com/Maximka1993271/Password-Generator-Python/wiki/Security-Logic"
        
        self.about_window = ctk.CTkToplevel(self)
        self.about_window.title(L["btn_about"])
        self.about_window.resizable(False, False)
        
        self.about_window.transient(self)
        self.about_window.attributes('-topmost', True)
        self.about_window.after(100, lambda: self.about_window.attributes('-topmost', False))
        
        self._center_window_relative_to_parent(self.about_window, 400, 350)
        self._apply_window_rounding(self.about_window)
        
        self.about_window.protocol("WM_DELETE_WINDOW", self._close_about)

        ctk.CTkLabel(self.about_window, text="Secure Pass Pro", font=("Segoe UI", 22, "bold")).pack(pady=(25, 5))
        ctk.CTkLabel(self.about_window, text="Version 3.9", font=("Segoe UI", 14)).pack(pady=(0, 15))

        ctk.CTkLabel(
            self.about_window, 
            text=L["about_text"], 
            wraplength=350, 
            font=("Segoe UI", 13)
        ).pack(pady=10)

        ctk.CTkButton(
            self.about_window, 
            text="OK", 
            width=120, 
            command=self._close_about
        ).pack(pady=(20, 10))

        lbl_wiki = ctk.CTkLabel(
            self.about_window, 
            text=L.get("wiki_link", "Security Logic Wiki"), 
            font=("Segoe UI", 12, "underline"),
            text_color="#1f538d",
            cursor="hand2"
        )
        lbl_wiki.pack(pady=(0, 20))
        lbl_wiki.bind("<Button-1>", lambda e: webbrowser.open(wiki_url))
        
        self.about_window.focus_force()

    def _close_about(self):
        if self.about_window:
            self.about_window.destroy()
            self.about_window = None


if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    app = SecurePassPro()
    app.mainloop()