"""
SecurePassPro v3.9 — Cryptographically secure password generator
Криптографически стойкий генератор паролей /
Криптографічно стійкий генератор паролів

Requires / Требует / Вимагає:
    pip install qrcode[pil] pillow customtkinter
    Python >= 3.9
"""

from __future__ import annotations

import math
import platform
import secrets
import string
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, List, Dict

import customtkinter as ctk

# =============================================================================
# PLATFORM CACHE
# =============================================================================
_IS_WINDOWS: bool = platform.system() == "Windows"

# =============================================================================
# SOUND ENGINE
# =============================================================================
def _beep(freq: int, ms: int) -> None:
    if _IS_WINDOWS:
        try:
            import winsound
            winsound.Beep(freq, ms)
        except Exception:
            pass

def _beep_async(*pairs: tuple) -> None:
    def _run() -> None:
        for freq, ms in pairs:
            _beep(int(freq), int(ms))
    threading.Thread(target=_run, daemon=True).start()

def sound_generate() -> None: _beep_async((800, 50), (1200, 50))
def sound_copy()     -> None: _beep_async((1500, 100),)
def sound_action()   -> None: _beep_async((1000, 60),)
def sound_error()    -> None: _beep_async((400, 150), (300, 150))

# =============================================================================
# DEPENDENCIES CHECK
# =============================================================================
try:
    import qrcode
    from PIL import Image
except ImportError:
    _err_root = tk.Tk()
    _err_root.withdraw()
    messagebox.showerror(
        "Критическая ошибка",
        "Отсутствуют необходимые библиотеки!\n\n"
        "pip install qrcode[pil] pillow customtkinter",
    )
    sys.exit(1)

def _get_resample() -> int:
    try:
        return Image.Resampling.LANCZOS   # Pillow >= 9.1
    except AttributeError:
        return Image.LANCZOS              # Pillow 8.x fallback

RESAMPLE: int = _get_resample()

# =============================================================================
# TOOLTIP CLASS
# =============================================================================
class ToolTip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text   = text
        self.tip_window: Optional[tk.Toplevel] = None

    def show_tip(self) -> None:
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 35
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid",
            borderwidth=1, font=("Tahoma", 9),
        ).pack(ipadx=1)

    def hide_tip(self) -> None:
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# =============================================================================
# CONSTANTS
# =============================================================================
HISTORY_MAX     = 50
FILE_READ_LIMIT = 1024
UPD_URL         = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe"
AMBIGUOUS_CHARS = "il1Lo0O"

_SYSRNG = secrets.SystemRandom()

# =============================================================================
# LANGUAGE DEFINITIONS
# =============================================================================
LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Настройки генерации",
        "len":        "Длина пароля",
        "author":      "Автор: Максим Мельников",
        "upper":      "Заглавные буквы",
        "lower":      "Строчные буквы",
        "digits":     "Цифры",
        "symb":       "Спецсимволы",
        "ambig":      "Исключить похожие (i, l, 1, L, o, 0, O)",
        "unambig":    "Исключить неоднозначные ({} [] () / \ ' \" ` ~ , ; : . < >)",
        "at_least":   "Минимум 1 из каждой категории",
        "hide":       "Скрывать символы",
        "btn_gen":    "СГЕНЕРИРОВАТЬ",
        "btn_copy":   "КОПИРОВАТЬ ПАРОЛЬ",
        "btn_save":   "СОХРАНИТЬ В ФАЙЛ",
        "btn_open":   "ОТКРЫТЬ ФАЙЛ",
        "btn_qr":     "QR-КОД ПАРОЛЯ",
        "btn_hist":   "ИСТОРИЯ",
        "btn_upd":    "ОБНОВИТЬ ПРОГРАММУ",
        "strength":   "Сложность",
        "radius":     "Закругление углов",
        "sys":        "Системная",
        "dark":        "Тёмная",
        "light":      "Светлая",
        "copied":     "Скопировано!",
        "bits":       "бит",
        "qr_title":   "QR-код пароля",
        "hist_title": "История",
        "t0":  "Мгновенно", "t1": "Секунды", "t2": "Минуты", "t3": "Часы", "t4": "Дни",
        "t5":  "Недели", "t6": "Месяцы", "t7": "Годы", "t8": "Десятилетия", "t9": "Столетия", "t10": "Тысячелетия",
        "tt_gen":     "Создать новый случайный пароль",
        "tt_copy":    "Копировать и очистить через 60с",
        "tt_save":    "Сохранить пароль в текстовый файл",
        "tt_open":    "Загрузить пароль из файла",
        "tt_qr":      "Создать QR-код для сканирования",
        "tt_hist":    "Посмотреть последние пароли",
        "tt_upd":     "Открыть страницу релизов",
        "err_no_pool": "Выберите хотя бы один тип символов!",
        "clipboard_note": "Внимание: на Linux/macOS автоочистка буфера ограничена возможностями Tk.",
    },
    "EN": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Generation Settings",
        "len":        "Password Length",
        "author":      "Author: Maxim Melnikov",
        "upper":      "Uppercase Letters",
        "lower":      "Lowercase Letters",
        "digits":     "Digits",
        "symb":       "Special Symbols",
        "ambig":      "Exclude ambiguous (i, l, 1, L, o, 0, O)",
        "unambig":    "Exclude symbols ({} [] () / \ ' \" ` ~ , ; : . < >)",
        "at_least":   "At least one from each category",
        "hide":       "Hide symbols",
        "btn_gen":    "GENERATE",
        "btn_copy":   "COPY PASSWORD",
        "btn_save":   "SAVE TO FILE",
        "btn_open":   "OPEN FILE",
        "btn_qr":     "QR-CODE",
        "btn_hist":   "HISTORY",
        "btn_upd":    "UPDATE PROGRAM",
        "strength":   "Strength",
        "radius":     "Corner Radius",
        "sys":        "System",
        "dark":        "Dark",
        "light":      "Light",
        "copied":     "Copied!",
        "bits":       "bits",
        "qr_title":   "Password QR-Code",
        "hist_title": "History",
        "t0":  "Instantly", "t1": "Seconds", "t2": "Minutes", "t3": "Hours", "t4": "Days",
        "t5":  "Weeks", "t6": "Months", "t7": "Years", "t8": "Decades", "t9": "Centuries", "t10": "Millennia",
        "tt_gen":     "Create a new random password",
        "tt_copy":    "Copy and clear clipboard in 60s",
        "tt_save":    "Save password to a text file",
        "tt_open":    "Load password from file",
        "tt_qr":      "Generate QR-code for scanning",
        "tt_hist":    "View recent passwords",
        "tt_upd":     "Open releases page",
        "err_no_pool": "Select at least one character type!",
        "clipboard_note": "Note: on Linux/macOS clipboard auto-clear is limited by Tk.",
    },
    "UA": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Налаштування генерації",
        "len":        "Довжина пароля",
        "author":      "Автор: Максим Мельников",
        "upper":      "Великі літери",
        "lower":      "Малі літери",
        "digits":     "Цифри",
        "symb":       "Спецсимволи",
        "ambig":      "Виключити схожі (i, l, 1, L, o, 0, O)",
        "unambig":    "Виключити неоднозначні ({} [] () / \ ' \" ` ~ , ; : . < >)",
        "at_least":   "Мінімум 1 з кожної категорії",
        "hide":       "Приховати символи",
        "btn_gen":    "ЗГЕНЕРУВАТИ",
        "btn_copy":   "КОПІЮВАТИ ПАРОЛЬ",
        "btn_save":   "ЗБЕРЕГТИ У ФАЙЛ",
        "btn_open":   "ВІДКРИТИ ФАЙЛ",
        "btn_qr":     "QR-КОД ПАРОЛЯ",
        "btn_hist":   "ІСТОРІЯ",
        "btn_upd":    "ОНОВИТИ ПРОГРАМУ",
        "strength":   "Складність",
        "radius":     "Закруглення кутів",
        "sys":        "Системна",
        "dark":        "Темна",
        "light":      "Світла",
        "copied":     "Скопійовано!",
        "bits":       "біт",
        "qr_title":   "QR-код пароля",
        "hist_title": "Історія",
        "t0":  "Миттєво", "t1": "Секунди", "t2": "Хвилини", "t3": "Години", "t4": "Дні",
        "t5":  "Тижні", "t6": "Місяці", "t7": "Роки", "t8": "Десятиліття", "t9": "Століття", "t10": "Тисячоліття",
        "tt_gen":     "Створити новий випадковий пароль",
        "tt_copy":    "Копіювати та очистити за 60с",
        "tt_save":    "Зберегти пароль у текстовий файл",
        "tt_open":    "Завантажити пароль з файлу",
        "tt_qr":      "Створити QR-код для сканування",
        "tt_hist":    "Переглянути останні паролі",
        "tt_upd":     "Відкрити сторінку релізів",
        "err_no_pool": "Оберіть хоча б один тип символів!",
        "clipboard_note": "Увага: на Linux/macOS автоочищення буфера обмежено можливостями Tk.",
    },
}

# =============================================================================
# ENTROPY HELPERS
# =============================================================================
_ENTROPY_THRESHOLDS: List[tuple] = [
    (20, "t0"), (30, "t1"), (40, "t2"), (50, "t3"), (60, "t4"),
    (70, "t5"), (80, "t6"), (90, "t7"), (100, "t8"), (120, "t9")
]
_ENTROPY_MAX_KEY = "t10"

def _entropy_to_time_key(entropy: float) -> str:
    for threshold, key in _ENTROPY_THRESHOLDS:
        if entropy < threshold: return key
    return _ENTROPY_MAX_KEY

def _entropy_to_color(entropy: float) -> str:
    if entropy < 50: return "#FF4B4B"
    if entropy < 80: return "#FFD700"
    return "#28A745"

# =============================================================================
# MAIN APPLICATION
# =============================================================================
class SecurePassPro(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.current_lang:  str = "RU"
        self.current_theme: str = "System"
        self.history:        List[str] = []
        self._radius_widgets: List[tk.Widget] = []
        self.tooltips:        Dict[str, ToolTip] = {}

        self.history_window: Optional[ctk.CTkToplevel] = None
        self.hist_txt:       Optional[ctk.CTkTextbox]  = None
        self.qr_window:      Optional[ctk.CTkToplevel] = None
        self.qr_label:       Optional[ctk.CTkLabel]    = None
        self._qr_ctk_image:  Optional[ctk.CTkImage]    = None

        self._last_copied_pwd: str = ""
        self._clipboard_job:   Optional[str] = None

        self.geometry("420x980")
        self.resizable(False, False)
        self._setup_vars()
        self._setup_ui()
        self._apply_lang("RU")
        ctk.set_appearance_mode("System")

    def _center_window(self, win: ctk.CTkToplevel) -> None:
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        mx, my = self.winfo_x(), self.winfo_y()
        mw, mh = self.winfo_width(), self.winfo_height()
        x = mx + (mw // 2) - (w // 2)
        y = my + (mh // 2) - (h // 2)
        win.geometry(f"+{x}+{y}")

    def _setup_vars(self) -> None:
        self.upper_var           = tk.BooleanVar(value=True)
        self.lower_var           = tk.BooleanVar(value=True)
        self.digits_var          = tk.BooleanVar(value=True)
        self.symb_var            = tk.BooleanVar(value=True)
        self.exclude_ambig_var   = tk.BooleanVar(value=False)
        self.exclude_unambig_var = tk.BooleanVar(value=False)
        self.at_least_one_var    = tk.BooleanVar(value=True)
        self.hide_var            = tk.BooleanVar(value=False)

    def _setup_ui(self) -> None:
        self._build_header()
        self._build_options()
        self._build_strength()
        self._build_buttons()
        self._build_footer()

    def _build_header(self) -> None:
        self.lbl_title = ctk.CTkLabel(self, text="", font=("Segoe UI", 22, "bold"))
        self.lbl_title.pack(pady=(15, 0))
        self.lbl_author = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.lbl_author.pack()

    def _build_options(self) -> None:
        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.pack(pady=10, padx=20, fill="x")
        self._radius_widgets.append(self.opt_frame)

        self.lbl_len = ctk.CTkLabel(self.opt_frame, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_len.pack(pady=(10, 0))
        self.slider = ctk.CTkSlider(self.opt_frame, from_=4, to=64, command=self._on_slider_move)
        self.slider.set(20)
        self.slider.pack(pady=10, padx=20)

        self.cb_upper    = self._create_cb(self.upper_var)
        self.cb_lower    = self._create_cb(self.lower_var)
        self.cb_digits   = self._create_cb(self.digits_var)
        self.cb_symb     = self._create_cb(self.symb_var)
        self.cb_ambig    = self._create_cb(self.exclude_ambig_var)
        self.cb_unambig  = self._create_cb(self.exclude_unambig_var)
        self.cb_at_least = self._create_cb(self.at_least_one_var)
        self.cb_hide     = self._create_cb(self.hide_var, command=self._toggle_visibility)

    def _build_strength(self) -> None:
        self.entry_res = ctk.CTkEntry(self, height=45, font=("Consolas", 18), justify="center")
        self.entry_res.pack(pady=10, padx=20, fill="x")
        self.entry_res.bind("<KeyRelease>", lambda _e: self._refresh_strength())
        self._radius_widgets.append(self.entry_res)

        self.strength_bar = ctk.CTkProgressBar(self, height=10)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=5, padx=40, fill="x")

        self.lbl_time_to_crack = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_time_to_crack.pack()
        self.lbl_strength = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_strength.pack()

    def _build_buttons(self) -> None:
        self.btn_gen  = self._create_btn(self._generate,      "btn_gen",  "#1f538d", "tt_gen",  bold=True)
        self.btn_copy = self._create_btn(self._copy,          "btn_copy", "#28a745", "tt_copy")
        self.btn_save = self._create_btn(self._save,          "btn_save", "#17a2b8", "tt_save")
        self.btn_open = self._create_btn(self._open,          "btn_open", "#17a2b8", "tt_open")
        self.btn_qr   = self._create_btn(self._show_qr,       "btn_qr",   "#6f42c1", "tt_qr")
        self.btn_hist = self._create_btn(self._show_history,  "btn_hist", "#6c757d", "tt_hist")
        self.btn_upd  = self._create_btn(self._update_app,    "btn_upd",  "#f39c12", "tt_upd")

    def _build_footer(self) -> None:
        self.lbl_radius = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_radius.pack(pady=(5, 0))
        self.slider_radius = ctk.CTkSlider(self, from_=0, to=25, height=14, command=self._change_radius)
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=5, padx=60, fill="x")

        self.lbl_stars = ctk.CTkLabel(self, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_stars.pack(side="bottom", pady=(0, 10))

        self.sw_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sw_frame.pack(side="bottom", fill="x", padx=20, pady=5)
        self.lang_sw = ctk.CTkSegmentedButton(self.sw_frame, values=["RU", "EN", "UA"], command=self._on_lang_change)
        self.lang_sw.pack(side="left")
        self.theme_sw = ctk.CTkSegmentedButton(self.sw_frame, values=["System", "Dark", "Light"], command=self._on_theme_change)
        self.theme_sw.pack(side="right")

    def _create_cb(self, var: tk.BooleanVar, command=None) -> ctk.CTkCheckBox:
        cb = ctk.CTkCheckBox(
            self.opt_frame, text="", variable=var, font=("Segoe UI", 12),
            command=lambda: (command() if command else None, self._refresh_strength()),
        )
        cb.pack(anchor="w", padx=35, pady=2)
        return cb

    def _create_btn(self, cmd, key: str, color: str, tt_key: str, bold: bool = False) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            self, text="", command=cmd, fg_color=color, height=35,
            font=("Segoe UI", 13 if bold else 12, "bold" if bold else "normal"),
        )
        btn.pack(pady=3, padx=40, fill="x")
        btn._key = key
        btn._tt_key = tt_key
        self._radius_widgets.append(btn)
        tip = ToolTip(btn, "")
        self.tooltips[key] = tip
        btn.bind("<Enter>", lambda _e: tip.show_tip())
        btn.bind("<Leave>", lambda _e: tip.hide_tip())
        return btn

    def _build_pools(self) -> tuple:
        exclude = set(AMBIGUOUS_CHARS) if self.exclude_ambig_var.get() else set()
        if self.exclude_unambig_var.get():
            unambig_chars = "{}[]()/\\'\"`~,;:.<>"
            exclude.update(unambig_chars)

        def _pool(var: tk.BooleanVar, src: str) -> str:
            if not var.get(): return ""
            return "".join(c for c in src if c not in exclude)

        pools = [
            _pool(self.upper_var,  string.ascii_uppercase),
            _pool(self.lower_var,  string.ascii_lowercase),
            _pool(self.digits_var, string.digits),
            _pool(self.symb_var,   string.punctuation),
        ]
        return pools, "".join(pools)

    def _generate(self) -> None:
        L = LANGUAGES[self.current_lang]
        pools, full_pool = self._build_pools()

        if not full_pool:
            sound_error()
            messagebox.showwarning(self.title(), L["err_no_pool"])
            return

        length = int(self.slider.get())
        mandatory = []
        if self.at_least_one_var.get():
            mandatory = [secrets.choice(p) for p in pools if p]

        if len(mandatory) > length:
            mandatory = _SYSRNG.sample(mandatory, length)

        remainder = [secrets.choice(full_pool) for _ in range(length - len(mandatory))]
        pwd_list = mandatory + remainder
        _SYSRNG.shuffle(pwd_list)
        
        pwd = "".join(pwd_list)
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, pwd)
        self.history.insert(0, pwd)
        if len(self.history) > HISTORY_MAX: self.history.pop()
        
        self._refresh_strength()
        sound_generate()

    def _save(self) -> None:
        """
        Save current password to a text file chosen by the user
        """
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Log Files",  "*.log"),
                ("Key Files",  "*.key"),
                ("All Files",  "*.*"),
            ],
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(pwd)
                sound_action()
            except OSError:
                sound_error()

    def _open(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(FILE_READ_LIMIT).strip()
                    self.entry_res.delete(0, "end")
                    self.entry_res.insert(0, content)
                    self._refresh_strength()
                    sound_action()
            except OSError:
                sound_error()

    def _copy(self) -> None:
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return
        
        self.clipboard_clear()
        self.clipboard_append(pwd)
        self._last_copied_pwd = pwd
        
        L = LANGUAGES[self.current_lang]
        self.btn_copy.configure(text=L["copied"])
        sound_copy()
        
        if self._clipboard_job: self.after_cancel(self._clipboard_job)
        self._clipboard_job = self.after(2000, self._reset_copy_btn)
        self.after(60000, self._clear_clipboard_secure)

    def _reset_copy_btn(self) -> None:
        self.btn_copy.configure(text=LANGUAGES[self.current_lang]["btn_copy"])

    def _clear_clipboard_secure(self) -> None:
        try:
            if self.clipboard_get() == self._last_copied_pwd:
                self.clipboard_clear()
                self.clipboard_append(" ") # Avoid empty clipboard issues
                self.clipboard_clear()
        except Exception:
            pass

    def _refresh_strength(self) -> None:
        pwd = self.entry_res.get()
        L = LANGUAGES[self.current_lang]
        if not pwd:
            self.strength_bar.set(0)
            self.lbl_time_to_crack.configure(text="")
            self.lbl_strength.configure(text="")
            return

        charset_size = 0
        if any(c in string.ascii_uppercase for c in pwd): charset_size += 26
        if any(c in string.ascii_lowercase for c in pwd): charset_size += 26
        if any(c in string.digits for c in pwd): charset_size += 10
        if any(c in string.punctuation for c in pwd): charset_size += 32

        entropy = len(pwd) * math.log2(max(charset_size, 1))
        
        self.strength_bar.set(min(entropy / 128, 1.0))
        self.strength_bar.configure(progress_color=_entropy_to_color(entropy))
        
        time_key = _entropy_to_time_key(entropy)
        self.lbl_time_to_crack.configure(text=f"{L['strength']}: {L[time_key]}")
        self.lbl_strength.configure(text=f"{int(entropy)} {L['bits']}")

    def _show_qr(self) -> None:
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return
        
        L = LANGUAGES[self.current_lang]
        if self.qr_window is None or not self.qr_window.winfo_exists():
            self.qr_window = ctk.CTkToplevel(self)
            self.qr_window.title(L["qr_title"])
            self.qr_window.geometry("300x350")
            self.qr_window.resizable(False, False)
            self.qr_window.attributes("-topmost", True)
            self.qr_window.transient(self)
            self.qr_label = ctk.CTkLabel(self.qr_window, text="")
            self.qr_label.pack(expand=True)
            self._center_window(self.qr_window)
        
        self.qr_window.lift()
        self.qr_window.focus()

        qr_img = qrcode.make(pwd).resize((250, 250), RESAMPLE)
        self._qr_ctk_image = ctk.CTkImage(light_image=qr_img, dark_image=qr_img, size=(250, 250))
        self.qr_label.configure(image=self._qr_ctk_image)
        sound_action()

    def _show_history(self) -> None:
        L = LANGUAGES[self.current_lang]
        if self.history_window is None or not self.history_window.winfo_exists():
            self.history_window = ctk.CTkToplevel(self)
            self.history_window.title(L["hist_title"])
            self.history_window.geometry("350x450")
            self.history_window.attributes("-topmost", True)
            self.history_window.transient(self)
            self.hist_txt = ctk.CTkTextbox(self.history_window, font=("Consolas", 12))
            self.hist_txt.pack(fill="both", expand=True, padx=10, pady=10)
            self._center_window(self.history_window)
        
        self.history_window.lift()
        self.history_window.focus()
        
        self.hist_txt.delete("1.0", "end")
        self.hist_txt.insert("1.0", "\n".join(self.history))
        sound_action()

    def _update_app(self) -> None:
        webbrowser.open(UPD_URL)

    def _on_slider_move(self, value: float) -> None:
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(value)}")

    def _change_radius(self, val: float) -> None:
        for w in self._radius_widgets:
            try:
                w.configure(corner_radius=int(val))
            except Exception:
                pass

    def _toggle_visibility(self) -> None:
        self.entry_res.configure(show="*" if self.hide_var.get() else "")

    def _on_lang_change(self, lang: str) -> None:
        self._apply_lang(lang)

    def _apply_lang(self, lang: str) -> None:
        self.current_lang = lang
        L = LANGUAGES[lang]
        self.title(L["win_title"])
        self.lbl_title.configure(text=L["win_title"])
        self.lbl_author.configure(text=L["author"])
        self.lbl_len.configure(text=f"{L['len']}: {int(self.slider.get())}")
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_unambig.configure(text=L["unambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])
        self.btn_gen.configure(text=L["btn_gen"])
        self.btn_copy.configure(text=L["btn_copy"])
        self.btn_save.configure(text=L["btn_save"])
        self.btn_open.configure(text=L["btn_open"])
        self.btn_qr.configure(text=L["btn_qr"])
        self.btn_hist.configure(text=L["btn_hist"])
        self.btn_upd.configure(text=L["btn_upd"])
        self.lbl_radius.configure(text=L["radius"])
        self.theme_sw.configure(values=[L["sys"], L["dark"], L["light"]])
        
        for key, tip in self.tooltips.items():
            tip.text = L[getattr(self, key)._tt_key]

        self._refresh_strength()

    def _on_theme_change(self, theme_localized: str) -> None:
        L = LANGUAGES[self.current_lang]
        mapping = {L["sys"]: "System", L["dark"]: "Dark", L["light"]: "Light"}
        mode = mapping.get(theme_localized, "System")
        ctk.set_appearance_mode(mode)

if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()