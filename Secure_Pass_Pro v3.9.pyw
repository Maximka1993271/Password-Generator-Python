"""
SecurePassPro v3.9 — Cryptographically secure password generator
EN: Cryptographically secure password generator
RU: Криптографически стойкий генератор паролей
UA: Криптографічно стійкий генератор паролів

Author / Автор: Maxim Melnikov
"""

from __future__ import annotations
import math
import platform
import secrets
import string
import sys
import os
import threading
import webbrowser
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict, Callable
import customtkinter as ctk

# EN: Check Windows for winsound | RU: Проверка Windows для winsound | UA: Перевірка Windows для winsound
_IS_WINDOWS = platform.system() == "Windows"
if _IS_WINDOWS:
    import winsound

# =============================================================================
# DEPENDENCIES & VERSION CHECK
# =============================================================================
if sys.version_info < (3, 9):
    _ver_root = tk.Tk()
    _ver_root.withdraw()
    messagebox.showerror("Error", "Python 3.9+ required!")
    sys.exit(1)

try:
    import qrcode
    from PIL import Image, ImageTk
except ImportError:
    _err_root = tk.Tk()
    _err_root.withdraw()
    messagebox.showerror("Error", "Required: pip install qrcode[pil] pillow customtkinter")
    sys.exit(1)

# =============================================================================
# CONSTANTS & ASSETS
# =============================================================================
HISTORY_MAX = 50
AMBIGUOUS_CHARS = "il1Lo0O"
UNAMBIG_CHARS = "{}[]()/\\'\"`~,;:.<>"
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

# =============================================================================
# TOOLTIP CLASS
# =============================================================================
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

# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================
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
        "err_save": "Ошибка сохранения: {0}",
        "err_open": "Не удалось прочитать файл: {0}",
        "hist_empty": "История пуста..."
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
        "tt_open": "Open password from .key, .log or .txt file",
        "tt_qr": "Create a QR code for quick scanning",
        "tt_hist": "Show last 50 generated passwords",
        "tt_upd": "Check for new version on GitHub",
        "tt_about": "Developer and program info",
        "err_cat": "Select at least one category!",
        "err_save": "Save failed: {0}",
        "err_open": "Could not read file: {0}",
        "hist_empty": "History is empty..."
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
        "btn_upd": "Оновити программу",
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
        "tt_about": "Інформація про розробника та программу",
        "err_cat": "Виберіть хоча б одну категорію!",
        "err_save": "Помилка збереження: {0}",
        "err_open": "Не вдалося прочитати файл: {0}",
        "hist_empty": "Історія порожня..."
    }
}

# =============================================================================
# MAIN APP CLASS
# =============================================================================
class SecurePassPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "RU"
        self.history = []
        self._radius_widgets = []
        self._clipboard_timer = None
        self._tooltips = {}
        self.sound_enabled = tk.BooleanVar(value=True)
        
        # Window settings
        self.title("Secure Pass Pro v3.9")
        self.geometry("850x780")
        
        # RU: Запрет масштабирования окна | EN: Disable window resizing
        self.resizable(False, False)

        # RU: Инициализация иконки | EN: Icon init
        self._setup_icon()
        
        # Variables
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

    def _setup_icon(self):
        """ RU: Установка иконки приложения | EN: Setup app icon """
        # RU: Поддержка .ico для скомпилированного .exe | EN: .ico support for compiled .exe
        if hasattr(sys, '_MEIPASS'):
            # Сначала ищем по имени из твоей команды (app_icon.ico)
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
            if not os.path.exists(icon_path):
                # Если не нашли, пробуем стандартное icon.ico
                icon_path = os.path.join(sys._MEIPASS, "icon.ico")
        else:
            # Для запуска из Python пробуем оба варианта
            icon_path = "icon.ico" if os.path.exists("icon.ico") else "app_icon.ico"

        if os.path.exists(icon_path):
            try:
                if _IS_WINDOWS:
                    self.iconbitmap(icon_path)
                else:
                    self.icon_img = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, self.icon_img)
            except Exception:
                pass
        elif os.path.exists("icon.png"):
            try:
                self.icon_img = tk.PhotoImage(file="icon.png")
                self.iconphoto(True, self.icon_img)
            except Exception:
                pass

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
        except: pass

    def _center_main_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.winfo_screenheight() // 2) - (780 // 2)
        self.geometry(f"+{x}+{y}")

    def _center_window(self, window, width, height):
        window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.transient(self)
        window.grab_set()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL ---
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

        self.lbl_title = ctk.CTkLabel(self.left_panel, text="Secure Pass Pro v3.9", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(5, 0))
        
        self.lbl_author = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 10))

        self.lbl_len = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_len.pack()
        self.slider_len = ctk.CTkSlider(self.left_panel, from_=4, to=64, width=400, command=self._update_len_label)
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

        # --- RIGHT PANEL ---
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
        self.btn_upd = self._create_menu_btn(self.right_panel, "btn_upd", "tt_upd", lambda: [self._play_sound("click"), webbrowser.open(UPD_URL)], "#ca5010")
        self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#4b4b4b")

        # --- BOTTOM PANEL ---
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

        # RU: Кнопка переключения звука | EN: Sound toggle button
        self.btn_sound = ctk.CTkButton(self.ctrl_line, text="", width=120, command=self._toggle_sound, fg_color="#4b4b4b")
        self.btn_sound.pack(side="left", padx=10)

        self.btn_theme = ctk.CTkOptionMenu(self.ctrl_line, values=[], command=self._change_theme, width=200)
        self.btn_theme.pack(side="right")

        self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="★★★★★", font=("Segoe UI", 24), text_color="#FFD700", height=25)
        self.lbl_app_rating.pack(pady=(0, 5))

    def _create_menu_btn(self, parent, lang_key, tt_key, cmd, color):
        btn = ctk.CTkButton(
            parent, text="", 
            command=lambda: [self._play_sound("click"), cmd()], 
            fg_color=color, height=45, font=("Segoe UI Variable", 13, "bold")
        )
        btn.pack(pady=5, padx=15, fill="x")
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        self._radius_widgets.append(btn)
        self._tooltips[lang_key] = ToolTip(btn)
        return btn

    def _apply_lang(self, lang):
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
        self.btn_theme.set(L["btn_theme"])
        self._change_radius(self.slider_radius.get())
        self.title(L["win_title"])

    def _toggle_sound(self):
        self.sound_enabled.set(not self.sound_enabled.get())
        self._update_sound_btn_text()
        self._play_sound("click")

    def _update_sound_btn_text(self):
        L = LANGUAGES[self.current_lang]
        txt = L["sound_on"] if self.sound_enabled.get() else L["sound_off"]
        self.btn_sound.configure(text=txt)

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
            messagebox.showwarning("Error", L["err_cat"])
            return
        self._play_sound("success")
        length = int(self.slider_len.get())
        result = []
        if self.at_least_var.get():
            for p in [p_upper, p_lower, p_digits, p_symb]:
                if p: result.append(secrets.choice(p))
        while len(result) < length: result.append(secrets.choice(full_pool))
        secrets.SystemRandom().shuffle(result)
        pwd = "".join(result[:length])
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, pwd)
        pool_size = len(full_pool)
        combinations = f"{pool_size**length:.1e}"
        self.lbl_strength.configure(text=L["strength"].format(combinations))
        if length <= 6: crack_phrase, color, progress, stars = L["time_sec"], "#FF4C4C", 0.25, "★☆☆☆☆"
        elif length <= 10: crack_phrase, color, progress, stars = L["time_day"], "#FFA500", 0.5, "★★★☆☆"
        elif length <= 14: crack_phrase, color, progress, stars = L["time_year"], "#FFFF00", 0.75, "★★★★☆"
        else: crack_phrase, color, progress, stars = L["time_cent"], "#2ECC71", 1.0, "★★★★★"
        self.strength_bar.configure(progress_color=color)
        self.strength_bar.set(progress)
        self.lbl_stars_top.configure(text=stars, text_color=color)
        st_text = L["st_low"] if progress <= 0.25 else (L["st_mid"] if progress <= 0.75 else L["st_high"])
        self.lbl_strength_text.configure(text=st_text, text_color=color)
        self.lbl_crack.configure(text=L["crack_time"].format(crack_phrase), text_color=color)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.history.append(f"[{now}] {pwd}")
        if len(self.history) > HISTORY_MAX: self.history.pop(0)

    def _copy(self):
        pwd = self.entry_res.get()
        if not pwd: return
        L = LANGUAGES[self.current_lang]
        self._play_sound("copy")
        self.clipboard_clear()
        self.clipboard_append(pwd)
        if self._clipboard_timer: self.after_cancel(self._clipboard_timer)
        self._clipboard_timer = self.after(60000, lambda: [self.clipboard_clear(), self.clipboard_append(" ")])
        old_text = L["btn_copy"]
        self.btn_copy.configure(text=L["copied"])
        self.after(2000, lambda: self.btn_copy.configure(text=old_text))

    def _save(self):
        L = LANGUAGES[self.current_lang]
        pwd = self.entry_res.get()
        if not pwd: return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Password File", "*.key"), 
                ("Log File", "*.log"), 
                ("Text File", "*.txt"), 
                ("All Files", "*.*")
            ]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f: f.write(pwd)
                self._play_sound("success")
            except Exception as e: messagebox.showerror("Error", L["err_save"].format(e))

    def _open(self):
        L = LANGUAGES[self.current_lang]
        path = filedialog.askopenfilename(
            filetypes=[
                ("Supported Files", "*.key *.log *.txt"),
                ("Password File", "*.key"), 
                ("Log File", "*.log"), 
                ("Text File", "*.txt"), 
                ("All Files", "*.*")
            ]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    self.entry_res.delete(0, "end")
                    self.entry_res.insert(0, content)
                self._play_sound("success")
            except Exception as e: messagebox.showerror("Error", L["err_open"].format(e))

    def _show_qr(self):
        pwd = self.entry_res.get()
        if not pwd: return
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        qr_win = ctk.CTkToplevel(self)
        qr_win.title(L["btn_qr"])
        self._center_window(qr_win, 380, 480)
        img = qrcode.make(pwd).resize((280, 280))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
        f = ctk.CTkFrame(qr_win, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_qr"], font=("Segoe UI", 18, "bold")).pack()
        disp = ctk.CTkFrame(f, fg_color="white", corner_radius=rad, border_width=2, border_color="gray")
        disp.pack(pady=10)
        ctk.CTkLabel(disp, image=ctk_img, text="").pack(padx=10, pady=10)
        ctk.CTkButton(f, text="OK", command=qr_win.destroy, corner_radius=rad).pack(pady=10)

    def _show_history(self):
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        h_win = ctk.CTkToplevel(self)
        h_win.title(L["btn_hist"])
        self._center_window(h_win, 500, 550)
        f = ctk.CTkFrame(h_win, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_hist"], font=("Segoe UI", 20, "bold")).pack(pady=10)
        txt = ctk.CTkTextbox(f, font=("Consolas", 14), corner_radius=rad)
        txt.pack(fill="both", expand=True)
        txt.insert("0.0", "\n".join(self.history) if self.history else L["hist_empty"])
        txt.configure(state="disabled")
        ctk.CTkButton(f, text="OK", command=h_win.destroy, corner_radius=rad).pack(pady=15)

    def _show_about(self):
        L = LANGUAGES[self.current_lang]
        rad = int(self.slider_radius.get())
        about_win = ctk.CTkToplevel(self)
        about_win.title(L["btn_about"])
        self._center_window(about_win, 450, 320)
        a_frame = ctk.CTkFrame(about_win, corner_radius=rad)
        a_frame.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(a_frame, text="Secure Pass Pro v3.9", font=("Segoe UI", 22, "bold")).pack(pady=10)
        ctk.CTkLabel(a_frame, text=L["about_text"], justify="center").pack(pady=10)
        ctk.CTkLabel(a_frame, text="2026 © Maxim Melnikov", font=("Segoe UI", 11), text_color="gray").pack(side="bottom", pady=10)
        ctk.CTkButton(a_frame, text="OK", command=about_win.destroy, corner_radius=rad).pack()

    def _change_theme(self, choice):
        L = LANGUAGES[self.current_lang]
        if choice == L["theme_sys"]: ctk.set_appearance_mode("System")
        elif choice == L["theme_dark"]: ctk.set_appearance_mode("Dark")
        elif choice == L["theme_light"]: ctk.set_appearance_mode("Light")

    def _change_radius(self, val):
        L = LANGUAGES[self.current_lang]
        for w in self._radius_widgets:
            try: w.configure(corner_radius=int(val))
            except: pass
        self.lbl_radius.configure(text=f"{L['radius']}: {int(val)}")

    def _update_len_label(self, val):
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")

    def _toggle_hide(self):
        self.entry_res.configure(show="*" if self.hide_var.get() else "")

if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()