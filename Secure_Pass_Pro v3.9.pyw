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
import ctypes  # Added for Windows API (corner rounding) / Добавлено для API Windows (скругление углов) / Додано для API Windows (заокруглення кутів)


def _show_startup_error(title, text):
    """
    Startup error dialog with root cleanup
    Диалог ошибки запуска с очисткой корневого окна
    Діалог помилки запуску з очищенням кореневого вікна
    """
    root = tk.Tk()
    root.withdraw()
    try:
        messagebox.showerror(title, text)
    finally:
        root.destroy()

# Check OS for sound support / Проверка ОС для поддержки звука / Перевірка ОС для підтримки звуку
_IS_WINDOWS = platform.system() == "Windows"
if _IS_WINDOWS:
    import winsound

# Requirements check / Проверка системных требований / Перевірка системних вимог
if sys.version_info < (3, 9):
    _show_startup_error("Error", "Python 3.9+ required!")
    sys.exit(1)

# Dependencies check / Проверка библиотек / Перевірка бібліотек
try:
    import customtkinter as ctk
    import qrcode
    from PIL import Image  # Pillow availability check / Проверка наличия Pillow / Перевірка наявності Pillow
    from fpdf import FPDF
except ImportError as exc:
    _show_startup_error("Error", f"Required: pip install qrcode[pil] pillow customtkinter fpdf\n\n{exc}")
    sys.exit(1)

HISTORY_MAX = 50
AMBIGUOUS_CHARS = "il1Lo0O"
UNAMBIG_CHARS = "{}[]()/\\'\"`~,;:.<>"
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

SUPPORTED_EXTENSIONS = (".key", ".log", ".txt", ".pdf")
TEXT_EXTENSIONS = (".key", ".log", ".txt")

class ToolTip:
    """
    Simple ToolTip implementation for widgets
    Реализация всплывающих подсказок
    Реалізація підказок, що спливають
    """
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

# Localization Dictionary / Словарь локализации / Словник локалізації
LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro",
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
        "btn_theme": "Цвет программы",
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
        "err_cat": "Выберите хотя бы одну категорию!",
        "err_pool_small": "Слишком мало доступных символов после исключений!",
        "err_save": "Ошибка сохранения: {0}",
        "err_open": "Не удалось прочитать файл: {0}",
        "err_unsupported": "Неподдерживаемый тип файла: {0}",
        "err_integrity": "Критическая ошибка: Файл поврежден после записи!",
        "hist_empty": "История пуста...",
        "btn_clear_hist": "Очистить историю",
        "pdf_date": "Дата",
        "pdf_pass": "Пароль"
    },
    "EN": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro",
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
        "btn_theme": "App color",
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
        "err_cat": "Select at least one category!",
        "err_pool_small": "Too few available characters after exclusions!",
        "err_save": "Save failed: {0}",
        "err_open": "Could not read file: {0}",
        "err_unsupported": "Unsupported file type: {0}",
        "err_integrity": "Critical error: File corrupted after write!",
        "hist_empty": "History is empty...",
        "btn_clear_hist": "Clear History",
        "pdf_date": "Date",
        "pdf_pass": "Password"
    },
    "UA": {
        "win_title": "Secure Pass Pro v3.9",
        "proton_title": "Secure Pass Pro",
        "menu_title": "Меню",
        "len": "Довжина",
        "author": "Автор: Максим Мельников",
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
        "btn_theme": "Колір програми",
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
        "err_cat": "Виберіть хоча б одну категорію!",
        "err_pool_small": "Занадто мало доступних символів після виключень!",
        "err_save": "Помилка збереження: {0}",
        "err_open": "Не вдалося прочитати файл: {0}",
        "err_unsupported": "Непідтримуваний тип файлу: {0}",
        "err_integrity": "Критична помилка: Файл пошкоджений після запису!",
        "hist_empty": "Історія порожня...",
        "btn_clear_hist": "Очистити історію",
        "pdf_date": "Дата",
        "pdf_pass": "Пароль"
    }
}

class SecurePassPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "RU"
        self.current_theme_key = "theme_sys"
        self.history = deque(maxlen=HISTORY_MAX)
        self._radius_widgets = []
        self._clipboard_timer = None
        self._tooltips = {}
        self._icon_image = None
        self._pdf_font_path = self._get_resource_path("DejaVuSans.ttf")
        self._secure_random = random.SystemRandom()
        self.sound_enabled = tk.BooleanVar(value=True)
        
        self.title("Secure Pass Pro v3.9")
        self.resizable(False, False)

        self._setup_main_icon()
        
        # Generator Logic Flags / Флаги логики генератора / Прапорці логіки генератора
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
        
        # Apply system rounding to main window / Применить внешнее закругление окна / Застосувати зовнішнє закруглення вікна
        self._apply_window_rounding(self)

    def _apply_window_rounding(self, window):
        """
        Rounding the external window corners (Windows 11 effect)
        Закругление внешних углов окна программы (эффект Windows 11)
        Закруглення зовнішніх кутів вікна програми (ефект Windows 11)
        """
        if not _IS_WINDOWS: return
        try:
            window.update()
            HWND = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2  # Standard rounding / Стандартное скругление / Стандартне заокруглення
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, 
                DWMWA_WINDOW_CORNER_PREFERENCE, 
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)), 
                ctypes.sizeof(ctypes.c_int(DWMWCP_ROUND))
            )
        except (AttributeError, OSError, tk.TclError) as exc:
            logging.debug("Window rounding failed: %s", exc)

    def _get_icon_path(self):
        return self._get_resource_path("icon.ico")

    def _get_resource_path(self, filename):
        """
        Resource path for source and PyInstaller builds
        Путь к ресурсу для исходника и сборки PyInstaller
        Шлях до ресурсу для джерельного файлу та збірки PyInstaller
        """
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
            except (OSError, tk.TclError):
                pass

    def _setup_main_icon(self):
        self._set_window_icon(self)

    def _play_sound(self, sound_type: str = "click"):
        if not _IS_WINDOWS or not self.sound_enabled.get(): return
        try:
            sounds = {
                "click": winsound.MB_ICONASTERISK,
                "success": winsound.MB_OK,
                "copy": winsound.MB_ICONEXCLAMATION,
                "error": winsound.MB_ICONHAND
            }
            winsound.MessageBeep(sounds.get(sound_type, winsound.MB_OK))
        except RuntimeError:
            pass

    def _center_main_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.winfo_screenheight() // 2) - (780 // 2)
        self.geometry(f"850x780+{x}+{y}")

    def _center_window(self, window, width, height):
        window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.transient(self)
        window.grab_set()

    def _setup_ui(self):
        """
        Building the GUI structure
        Создание структуры графического интерфейса
        Створення структури графічного інтерфейсу
        """
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # Left Panel (Settings & Result) / Левая панель (настройки и результат) / Ліва панель (налаштування та результат)
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
        self.cb_upper.grid(row=0, column=0, padx=20, pady=2, sticky="w")
        self.cb_lower = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.lower_var)
        self.cb_lower.grid(row=0, column=1, padx=20, pady=2, sticky="w")
        self.cb_digits = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.digits_var)
        self.cb_digits.grid(row=1, column=0, padx=20, pady=2, sticky="w")
        self.cb_symb = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.symb_var)
        self.cb_symb.grid(row=1, column=1, padx=20, pady=2, sticky="w")
        
        self.cb_ambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.ambig_var)
        self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=2, sticky="w")
        self.cb_unambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.unambig_var)
        self.cb_unambig.grid(row=3, column=0, columnspan=2, padx=20, pady=2, sticky="w")
        
        self.cb_at_least = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.at_least_var)
        self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=2, sticky="w")
        self.cb_hide = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.hide_var, command=self._toggle_hide)
        self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=2, sticky="w")

        self.entry_res = ctk.CTkEntry(self.left_panel, height=50, font=("Consolas", 22), justify="center")
        self.entry_res.pack(pady=10, padx=40, fill="x")
        self._radius_widgets.append(self.entry_res)

        # Strength indicators / Индикаторы стойкости / Індикатори стійкості
        self.strength_bar = ctk.CTkProgressBar(self.left_panel, width=400, height=8)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=(5, 5))
        
        self.lbl_stars_top = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 24), text_color="#FFD700")
        self.lbl_stars_top.pack()

        self.lbl_strength_text = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_strength_text.pack()

        self.lbl_strength = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13))
        self.lbl_strength.pack()
        self.lbl_crack = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13, "bold"), wraplength=500)
        self.lbl_crack.pack(pady=(0, 5))

        # Right Panel (Menu) / Правая панель (меню) / Права панель (меню)
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
        self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#4b4b4b")

        # Bottom Panel (Control & Personalization) / Нижняя панель (управление и персонализация) / Нижня панель (керування та персоналізація)
        self.bottom_frame = ctk.CTkFrame(self, fg_color=("#e0e0e0", "#1e1e1e"), corner_radius=15)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        
        self.lbl_radius = ctk.CTkLabel(self.bottom_frame, text="", text_color=("black", "white"), height=20)
        self.lbl_radius.pack(pady=(5, 0))
        self.slider_radius = ctk.CTkSlider(self.bottom_frame, from_=0, to=25, width=400, command=self._change_radius)
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=2)

        self.ctrl_line = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.ctrl_line.pack(fill="x", padx=20, pady=5)

        self.lang_sw = ctk.CTkSegmentedButton(self.ctrl_line, values=["RU", "EN", "UA"], command=self._apply_lang)
        self.lang_sw.set("RU")
        self.lang_sw.pack(side="left")

        self.btn_sound = ctk.CTkButton(self.ctrl_line, text="", width=120, command=self._toggle_sound, fg_color="#4b4b4b")
        self.btn_sound.pack(side="left", padx=10)

        self.btn_theme = ctk.CTkOptionMenu(self.ctrl_line, values=[], command=self._change_theme, width=200)
        self.btn_theme.pack(side="right")

        self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="★★★★★", font=("Segoe UI", 24), text_color="#FFD700", height=25)
        self.lbl_app_rating.pack(pady=(0, 5))

    def _create_menu_btn(self, parent, lang_key, tt_key, cmd, color):
        btn = ctk.CTkButton(
            parent, text="", 
            command=lambda command=cmd: self._run_menu_command(command),
            fg_color=color, height=45, font=("Segoe UI Variable", 13, "bold")
        )
        btn.pack(pady=5, padx=15, fill="x")
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        self._radius_widgets.append(btn)
        self._tooltips[lang_key] = ToolTip(btn)
        return btn

    def _run_menu_command(self, command):
        """
        Run menu action with click feedback
        Запуск действия меню со звуком клика
        Запуск дії меню зі звуком кліка
        """
        self._play_sound("click")
        command()

    def _change_radius(self, val):
        """
        Dynamic rounding of widgets
        Динамическое закругление виджетов
        Динамічне заокруглення віджетів
        """
        rad = int(val)
        L = LANGUAGES[self.current_lang]
        self.lbl_radius.configure(text=f"{L['radius']}: {rad}")
        for w in self._radius_widgets:
            w.configure(corner_radius=rad)
        self.bottom_frame.configure(corner_radius=rad)
        self.cb_upper.configure(corner_radius=rad//2)
        self.cb_lower.configure(corner_radius=rad//2)
        self.cb_digits.configure(corner_radius=rad//2)
        self.cb_symb.configure(corner_radius=rad//2)
        self.cb_ambig.configure(corner_radius=rad//2)
        self.cb_unambig.configure(corner_radius=rad//2)
        self.cb_at_least.configure(corner_radius=rad//2)
        self.cb_hide.configure(corner_radius=rad//2)

    def _change_theme(self, choice):
        L = LANGUAGES[self.current_lang]
        theme_map = {
            L["theme_sys"]: ("theme_sys", "System"),
            L["theme_dark"]: ("theme_dark", "Dark"),
            L["theme_light"]: ("theme_light", "Light"),
        }
        self.current_theme_key, mode = theme_map.get(choice, ("theme_light", "Light"))
        self.after(0, lambda: ctk.set_appearance_mode(mode))

    def _apply_lang(self, lang):
        """
        Switching UI Language
        Смена языка интерфейса
        Зміна мови інтерфейсу
        """
        self.current_lang = lang
        L = LANGUAGES[lang]
        self.lbl_author.configure(text=L["author"])
        self.lbl_menu.configure(text=L["menu_title"])
        self.lbl_title.configure(text=L["proton_title"])
        self._update_len_label(self.slider_len.get())
        self._update_sound_btn_text()
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_unambig.configure(text=L["unambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr, self.btn_hist, self.btn_upd, self.btn_about]
        for btn in menu_btns:
            btn.configure(text=L[btn.lang_key])
            if btn.lang_key in self._tooltips:
                self._tooltips[btn.lang_key].set_text(L[btn.tt_key])
        self.btn_theme.configure(values=[L["theme_sys"], L["theme_dark"], L["theme_light"]])
        self.btn_theme.set(L[self.current_theme_key])
        self._change_radius(self.slider_radius.get())
        self.title(L["win_title"])

    def _update_len_label(self, val):
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")

    def _toggle_hide(self):
        if self.hide_var.get():
            self.entry_res.configure(show="*")
        else:
            self.entry_res.configure(show="")

    def _toggle_sound(self):
        self.sound_enabled.set(not self.sound_enabled.get())
        self._update_sound_btn_text()
        self._play_sound("click")

    def _update_sound_btn_text(self):
        L = LANGUAGES[self.current_lang]
        txt = L["sound_on"] if self.sound_enabled.get() else L["sound_off"]
        self.btn_sound.configure(text=txt)

    def _generate(self):
        """
        Main Generation Logic (Secrets Module)
        Основная логика генерации (Модуль Secrets)
        Основна логіка генерації (Модуль Secrets)
        """
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
            messagebox.showwarning("Error", L["err_cat"])
            return
        if len(set(full_pool)) < 2:
            self._play_sound("error")
            messagebox.showwarning("Error", L["err_pool_small"])
            return
            
        self._play_sound("success")
        length = int(self.slider_len.get())
        result = []
        
        if self.at_least_var.get():
            for p in [p_upper, p_lower, p_digits, p_symb]:
                if p: result.append(secrets.choice(p))
                
        if len(result) > length:
            self._secure_random.shuffle(result)
            result = result[:length]
        else:
            while len(result) < length:
                result.append(secrets.choice(full_pool))
        self._secure_random.shuffle(result)
        pwd = "".join(result)
        
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, pwd)
        
        pool_size = len(full_pool)
        entropy_bits = math.log2(pool_size) * length if pool_size else 0
        combinations = f"{pool_size**length:.1e}"
        self.lbl_strength.configure(text=L["strength"].format(combinations))
        
        if entropy_bits < 40: crack_phrase, color, progress, stars = L["time_sec"], "#FF4C4C", 0.25, "★☆☆☆☆"
        elif entropy_bits < 60: crack_phrase, color, progress, stars = L["time_day"], "#FFA500", 0.5, "★★★☆☆"
        elif entropy_bits < 80: crack_phrase, color, progress, stars = L["time_year"], "#FFFF00", 0.75, "★★★★☆"
        else: crack_phrase, color, progress, stars = L["time_cent"], "#2ECC71", 1.0, "★★★★★"
        
        self.strength_bar.configure(progress_color=color)
        self.strength_bar.set(progress)
        self.lbl_stars_top.configure(text=stars, text_color=color)
        st_text = L["st_low"] if progress <= 0.25 else (L["st_mid"] if progress <= 0.75 else L["st_high"])
        self.lbl_strength_text.configure(text=st_text, text_color=color)
        self.lbl_crack.configure(text=L["crack_time"].format(crack_phrase), text_color=color)
        
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.history.append(f"[{now}] {pwd}")

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
            except (tk.TclError, ValueError):
                pass
        self._clipboard_timer = self.after(60000, lambda value=pwd: self._clear_clipboard_if_current(value))
        
        old_text = L["btn_copy"]
        self.btn_copy.configure(text=L["copied"])
        self.after(2000, lambda: self.btn_copy.configure(text=old_text))

    def _clear_clipboard_if_current(self, expected):
        """
        Clipboard auto-cleanup after copying
        Автоочистка буфера после копирования
        Автоочищення буфера після копіювання
        """
        try:
            if self.clipboard_get() == expected:
                self.clipboard_clear()
        except (tk.TclError, RuntimeError, AttributeError):
            pass
        finally:
            self._clipboard_timer = None

    def _verify_pdf(self, path):
        try:
            with open(path, "rb") as f:
                header = f.read(5)
                return header == b"%PDF-"
        except OSError:
            return False

    def _verify_text_file(self, path, expected_bytes):
        """
        Text save integrity check
        Проверка целостности сохранения текста
        Перевірка цілісності збереження тексту
        """
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()
        try:
            with open(path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            return False
        return actual_hash == expected_hash

    def _get_supported_extension(self, path, allowed_extensions):
        """
        Validate selected file extension
        Проверка выбранного расширения файла
        Перевірка вибраного розширення файлу
        """
        ext = os.path.splitext(path)[1].lower()
        if ext not in allowed_extensions:
            L = LANGUAGES[self.current_lang]
            raise ValueError(L["err_unsupported"].format(ext or "no extension"))
        return ext

    def _save(self):
        """
        Save to TXT/KEY/LOG/PDF / Сохранение / Збереження
        """
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
                    pdf = FPDF()
                    pdf.set_author("Maxim Melnikov")
                    pdf.set_creator("Secure Pass Pro v3.9")
                    pdf.set_title("Secure Pass Pro Password")
                    pdf.add_page()
                    
                    font_name = "Arial"
                    if os.path.exists(self._pdf_font_path):
                        pdf.add_font("DejaVu", "", self._pdf_font_path, uni=True)
                        font_name = "DejaVu"

                    pdf.set_font(font_name, 'B', 16)
                    pdf.cell(200, 10, txt="Secure Pass Pro v3.9", ln=True, align='C')
                    
                    pdf.set_font(font_name, size=12)
                    pdf.ln(10)
                    
                    date_val = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    if font_name == "Arial":
                        pdf.cell(200, 10, txt=f"Date: {date_val}", ln=True)
                        pdf.cell(200, 10, txt=f"Password: {pwd}", ln=True)
                    else:
                        pdf.cell(200, 10, txt=f"{L['pdf_date']}: {date_val}", ln=True)
                        pdf.cell(200, 10, txt=f"{L['pdf_pass']}: {pwd}", ln=True)
                    
                    pdf.output(path)
                    if not self._verify_pdf(path): raise IOError(L["err_integrity"])
                else:
                    pwd_bytes = pwd.encode("utf-8")
                    with open(path, "wb") as f:
                        f.write(pwd_bytes)
                    if not self._verify_text_file(path, pwd_bytes): raise IOError(L["err_integrity"])
                self._play_sound("success")
            except (OSError, ValueError, RuntimeError, UnicodeEncodeError, tk.TclError) as e:
                messagebox.showerror("Error", L["err_save"].format(e))

    def _open(self):
        L = LANGUAGES[self.current_lang]
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", " ".join(f"*{ext}" for ext in TEXT_EXTENSIONS)),
                ("Password File", "*.key"), 
                ("Log File", "*.log"), 
                ("Text File", "*.txt"), 
                ("All Files", "*.*")
            ]
        )
        if path:
            try:
                self._get_supported_extension(path, TEXT_EXTENSIONS)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    self.entry_res.delete(0, "end")
                    self.entry_res.insert(0, content)
                self._play_sound("success")
            except (OSError, ValueError, UnicodeDecodeError, tk.TclError) as e:
                messagebox.showerror("Error", L["err_open"].format(e))

    def _show_qr(self):
        pwd = self.entry_res.get()
        if not pwd: return
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        qr_win = ctk.CTkToplevel(self)
        qr_win.title(L["btn_qr"])
        self._set_window_icon(qr_win)
        self._center_window(qr_win, 380, 480)
        self._apply_window_rounding(qr_win)
        
        resampling_source = getattr(Image, "Resampling", Image)
        resampling_filter = getattr(resampling_source, "LANCZOS", getattr(Image, "NEAREST", 0))
        img = qrcode.make(pwd).resize((280, 280), resampling_filter)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
        
        f = ctk.CTkFrame(qr_win, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_qr"], font=("Segoe UI", 18, "bold")).pack()
        
        disp = ctk.CTkFrame(f, fg_color="white", corner_radius=rad, border_width=2, border_color="gray")
        disp.pack(pady=10)
        qr_label = ctk.CTkLabel(disp, image=ctk_img, text="")
        qr_label.image = ctk_img
        qr_label.pack(padx=10, pady=10)
        ctk.CTkButton(f, text="OK", command=qr_win.destroy, corner_radius=rad).pack(pady=10)

    def _show_history(self):
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        h_win = ctk.CTkToplevel(self)
        h_win.title(L["btn_hist"])
        self._set_window_icon(h_win)
        self._center_window(h_win, 500, 580)
        self._apply_window_rounding(h_win)
        
        f = ctk.CTkFrame(h_win, fg_color="transparent")
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
        ctk.CTkButton(btn_f, text="OK", corner_radius=rad, command=h_win.destroy).pack(side="right", padx=5)

    def _clear_history_textbox(self, textbox):
        """
        Clear password history window
        Очистка окна истории паролей
        Очищення вікна історії паролів
        """
        L = LANGUAGES[self.current_lang]
        self.history.clear()
        textbox.delete("1.0", "end")
        textbox.insert("1.0", L["hist_empty"])

    def _show_about(self):
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        a_win = ctk.CTkToplevel(self)
        a_win.title(L["btn_about"])
        self._set_window_icon(a_win)
        self._center_window(a_win, 450, 320)
        self._apply_window_rounding(a_win)
        
        f = ctk.CTkFrame(a_win, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=30, pady=30)
        
        ctk.CTkLabel(f, text="Secure Pass Pro", font=("Segoe UI", 24, "bold")).pack()
        ctk.CTkLabel(f, text="Version 3.9", font=("Segoe UI", 12)).pack()
        ctk.CTkLabel(f, text=L["about_text"], font=("Segoe UI", 14), wraplength=380, pady=20).pack()
        ctk.CTkButton(f, text="OK", command=a_win.destroy, corner_radius=rad).pack(pady=10)

if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()
