"""
Main application window
"""
from __future__ import annotations
from collections import deque
import os
import sys
import math
import time
import json
import webbrowser
import datetime
import shutil
import tempfile
import tkinter as tk
import subprocess
import ctypes
from tkinter import filedialog
from typing import Optional, Dict, Any, List

import customtkinter as ctk
import qrcode
from PIL import Image
from fpdf import FPDF

from core.generator import PasswordGenerator, StrengthCalculator
from security.master import MasterPassword
from security.integrity import verify_file_integrity, save_file_with_hash
from storage.database import PasswordDB
from storage.config import Config
from localization.lang import LANGUAGES
from gui.dialogs import CTkMessageBox, CTkInputDialog
from gui.widgets import ToolTip
from utils.helpers import (
    get_global_radius, set_global_radius, center_screen,
    get_resource_path, play_sound, is_windows, is_macos, is_linux,
    apply_window_rounding, set_window_icon
)

# ==================== CONSTANTS & PORTABLE LOGIC ====================
HISTORY_MAX = 50
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

# Определение базовой директории (путь к EXE или скрипту)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Путь к скрытой папке данных прямо в директории приложения
CONFIG_DIR = os.path.join(BASE_DIR, "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Создание папки data (без fallback!)
try:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if sys.platform == "win32":
        ctypes.windll.kernel32.SetFileAttributesW(CONFIG_DIR, 0x02)
    print(f"[Config] Using config dir: {CONFIG_DIR}")
except Exception as e:
    print(f"[Config] Error creating config dir: {e}")
    # НЕ откатываемся к старой папке!
    # Если не удалось, программа будет использовать временную папку
    import tempfile
    CONFIG_DIR = os.path.join(tempfile.gettempdir(), "securepasspro")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
    os.makedirs(CONFIG_DIR, exist_ok=True)
    print(f"[Config] Using fallback temp dir: {CONFIG_DIR}")

# Удаляем старую папку, если она существует
OLD_CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".securepasspro")
if os.path.exists(OLD_CONFIG_DIR):
    try:
        import shutil
        shutil.rmtree(OLD_CONFIG_DIR)
        print("[Cleanup] Removed old config folder")
    except Exception as e:
        print(f"[Cleanup] Error removing old folder: {e}")
# =====================================================================


class SecurePassPro(ctk.CTk):
    """Main application window"""
    
    def __init__(self) -> None:
        super().__init__()
        
        # Settings
        self.current_lang = "RU"
        self.current_theme = "Dark"
        self.current_radius = 25
        self.current_font_size = 14
        self.clipboard_timeout = 60
        self._clipboard_timer: Optional[str] = None
        self._rgb_anim_id: Optional[str] = None
        self._pulse_animation_id: Optional[str] = None
        
        # Auto-lock
        self.auto_lock_enabled = tk.BooleanVar(value=False)
        self.auto_lock_timeout = 5
        self._last_activity_time = time.time()
        self._lock_check_id: Optional[str] = None
        
        # Таймеры для плавных слайдеров
        self._radius_timer = None
        self._clip_timer = None
        self._auto_timer = None
        self._font_timer = None
        
        set_global_radius(self.current_radius)
        
        # UI Variables
        self.upper_var = tk.BooleanVar(value=False)
        self.lower_var = tk.BooleanVar(value=False)
        self.digits_var = tk.BooleanVar(value=False)
        self.symb_var = tk.BooleanVar(value=False)
        self.ambig_var = tk.BooleanVar(value=False)
        self.unambig_var = tk.BooleanVar(value=False)
        self.at_least_var = tk.BooleanVar(value=False)
        self.hide_var = tk.BooleanVar(value=False)
        self.no_repeat_var = tk.BooleanVar(value=False)
        self.sound_enabled = tk.BooleanVar(value=True)
        self.rgb_enabled = tk.BooleanVar(value=True)
        
        self.history: deque = deque(maxlen=HISTORY_MAX)
        self._rgb_t = 0.0
        
        # Windows
        self.settings_window: Optional[ctk.CTkToplevel] = None
        self.about_window: Optional[ctk.CTkToplevel] = None
        self.history_window: Optional[ctk.CTkToplevel] = None
        self.qr_window: Optional[ctk.CTkToplevel] = None
        self.db_window: Optional[ctk.CTkToplevel] = None
        
        # Widget references
        self._tooltips: Dict[str, ToolTip] = {}
        self.lang_buttons: Dict[str, ctk.CTkButton] = {}
        self.theme_buttons: Dict[str, ctk.CTkButton] = {}
        self.settings_labels: Dict[str, Any] = {}
        self._master_set_btn: Optional[ctk.CTkButton] = None
        self._master_status_label: Optional[ctk.CTkLabel] = None
        self._sound_btn: Optional[ctk.CTkButton] = None
        self._close_btn: Optional[ctk.CTkButton] = None
        self._clip_timeout_label_ref: Optional[ctk.CTkLabel] = None
        self._rgb_on_btn_ref: Optional[ctk.CTkButton] = None
        self._rgb_off_btn_ref: Optional[ctk.CTkButton] = None
        self._auto_lock_btn: Optional[ctk.CTkButton] = None
        self._auto_lock_slider: Optional[ctk.CTkSlider] = None
        self._auto_lock_label_ref: Optional[ctk.CTkLabel] = None
        self.auto_save_btn: Optional[ctk.CTkButton] = None
        self.auto_save_var = tk.BooleanVar(value=False)
        
        # RGB canvases
        self._rgb_c_top: Optional[tk.Canvas] = None
        self._rgb_c_bottom: Optional[tk.Canvas] = None
        self._rgb_c_left: Optional[tk.Canvas] = None
        self._rgb_c_right: Optional[tk.Canvas] = None
        
        self._icon_image: Optional[tk.PhotoImage] = None
        self._pdf_font_path = get_resource_path("DejaVuSans.ttf")
        
        # Initialize password generator
        self.generator = PasswordGenerator()
        self.strength_calc = StrengthCalculator()
        self.config = Config()
        
        # Setup UI
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        
        self.title("Secure Pass Pro v4.0")
        self.resizable(False, False)
        set_window_icon(self)
        
        self._create_rgb_canvases()
        self._setup_ui()
        self._apply_lang("RU")
        self._center_main_window()
        apply_window_rounding(self)
        
        # Bind keys
        self.bind('<F5>', lambda e: self._generate())
        self.bind('<Control-c>', lambda e: self._copy() if self.focus_get() is not self.entry_res else None)
        self.bind('<Control-s>', lambda e: self._save())
        self.bind('<Control-o>', lambda e: self._open())
        self.bind('<Escape>', lambda e: self._close_settings() if self.settings_window else None)
        
        # Activity tracking for auto-lock
        self.bind_all('<Key>', self._reset_activity_timer)
        self.bind_all('<Button>', self._reset_activity_timer)
        self.bind_all('<Motion>', self._reset_activity_timer)
        
        # Load settings
        self.after(50, self._load_all_settings)
        self.after(100, self._start_lock_checker)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    # ==================== AUTO-LOCK METHODS ====================
    
    def _reset_activity_timer(self, event=None) -> None:
        if not self.auto_lock_enabled.get():
            return
        self._last_activity_time = time.time()
    
    def _start_lock_checker(self) -> None:
        self._check_lock()
    
    def _check_lock(self) -> None:
        if not self.auto_lock_enabled.get():
            self._lock_check_id = self.after(1000, self._check_lock)
            return
        
        if not MasterPassword.is_set():
            self._lock_check_id = self.after(1000, self._check_lock)
            return
        
        if self.settings_window and self.settings_window.winfo_exists():
            self._last_activity_time = time.time()
            self._lock_check_id = self.after(1000, self._check_lock)
            return
        
        idle_time = time.time() - self._last_activity_time
        if idle_time >= self.auto_lock_timeout * 60:
            self._lock_program()
        
        self._lock_check_id = self.after(1000, self._check_lock)
    
    def _lock_program(self) -> None:
        if not MasterPassword.is_set():
            return
        
        if self.db_window and self.db_window.winfo_exists():
            try:
                self.db_window.destroy()
            except Exception:
                pass
        
        rgb_was_enabled = self.rgb_enabled.get()
        if rgb_was_enabled:
            self._stop_rgb()
        
        self.withdraw()
        unlocked = self._show_lock_screen()
        
        if unlocked:
            self.deiconify()
            self.lift()
            self.focus_force()
            if rgb_was_enabled:
                self._start_rgb()
            self._last_activity_time = time.time()
        else:
            self._on_closing()
    
    def _show_lock_screen(self) -> bool:
        L = LANGUAGES[self.current_lang]
        theme = self._get_actual_theme()
        colors = self._get_colors_for_theme(theme)
        radius = get_global_radius()
        
        win = ctk.CTkToplevel(self)
        win.title(L["win_title"])
        win.resizable(False, False)
        win.grab_set()
        win.attributes("-topmost", True)
        
        w, h = 450, 320
        center_screen(win, w, h)
        win.configure(fg_color=colors["bg"])
        
        ctk.CTkLabel(win, text="🔒", font=("Segoe UI", 64), text_color="#4EC9B0").pack(pady=(30, 10))
        ctk.CTkLabel(win, text=L.get("auto_lock_title", "Program Locked"), 
                    font=("Segoe UI", 18, "bold"), text_color=colors["label_text"]).pack(pady=(0, 10))
        
        entry = ctk.CTkEntry(win, width=340, height=45, font=("Segoe UI", 16), show="*",
                            fg_color=colors["entry_bg"], text_color=colors["fg"], corner_radius=radius)
        entry.pack(pady=(0, 20))
        entry.focus_set()
        
        result = [False]
        
        def on_unlock():
            pwd = entry.get()
            if MasterPassword.verify(pwd):
                result[0] = True
                win.destroy()
            else:
                CTkMessageBox.error(win, L["master_title"], L["master_wrong"].format(1, 1))
                entry.delete(0, "end")
                entry.focus_set()
        
        entry.bind("<Return>", lambda e: on_unlock())
        
        unlock_btn = ctk.CTkButton(win, text=L.get("unlock", "Unlock"), width=200, height=45, command=on_unlock,
                                   fg_color="#2d6a4f", hover_color="#40916c", corner_radius=radius, font=("Segoe UI", 15, "bold"))
        unlock_btn.pack(pady=(10, 30))
        
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        win.after(100, lambda: win.attributes("-topmost", False))
        self.wait_window(win)
        
        return result[0]
    
    def _get_colors_for_theme(self, theme: str) -> dict:
        if theme == "light":
            return {"bg": "#F3F3F3", "fg": "#000000", "entry_bg": "#FFFFFF", "label_text": "#000000", "button_fg": "#1f538d"}
        return {"bg": "#1d1e1e", "fg": "#FFFFFF", "entry_bg": "#2b2b2b", "label_text": "#FFFFFF", "button_fg": "#1f538d"}
    
    # ==================== RGB METHODS ====================
    
    def _create_rgb_canvases(self) -> None:
        bw = 3
        self._rgb_c_top = tk.Canvas(self, height=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_bottom = tk.Canvas(self, height=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_left = tk.Canvas(self, width=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_right = tk.Canvas(self, width=bw, bg="#1d1e1e", highlightthickness=0)
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            c.place_forget()
    
    def _rgb_color(self, phase_offset: float) -> str:
        f = self._rgb_t + phase_offset
        r = int((math.sin(f) + 1) / 2 * 255)
        g = int((math.sin(f + 2.1) + 1) / 2 * 255)
        b = int((math.sin(f + 4.2) + 1) / 2 * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _set_titlebar_color(self, hex_color: str) -> None:
        if not is_windows():
            return
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            colorref = r | (g << 8) | (b << 16)
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_CAPTION_COLOR = 35
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(colorref)), ctypes.sizeof(ctypes.c_int(colorref)))
        except Exception:
            pass
    
    def _reset_titlebar_color(self) -> None:
        if not is_windows():
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_CAPTION_COLOR = 35
            DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(DWMWA_COLOR_DEFAULT)), ctypes.sizeof(ctypes.c_int(DWMWA_COLOR_DEFAULT)))
        except Exception:
            pass
    
    def _animate_rgb(self) -> None:
        if not self.rgb_enabled.get():
            return
        if self._rgb_c_top:
            self._rgb_c_top.configure(bg=self._rgb_color(0.0))
        if self._rgb_c_right:
            self._rgb_c_right.configure(bg=self._rgb_color(0.8))
        if self._rgb_c_bottom:
            self._rgb_c_bottom.configure(bg=self._rgb_color(1.6))
        if self._rgb_c_left:
            self._rgb_c_left.configure(bg=self._rgb_color(2.4))
        self._set_titlebar_color(self._rgb_color(3.2))
        self._rgb_t = (self._rgb_t + 0.08) % (2 * math.pi)
        if self._rgb_anim_id:
            self.after_cancel(self._rgb_anim_id)
        self._rgb_anim_id = self.after(30, self._animate_rgb)
    
    def _start_rgb(self) -> None:
        if self._rgb_c_top:
            self._rgb_c_top.place(relx=0, rely=0, relwidth=1)
            self._rgb_c_bottom.place(relx=0, rely=1, anchor="sw", relwidth=1)
            self._rgb_c_left.place(relx=0, rely=0, relheight=1)
            self._rgb_c_right.place(relx=1, rely=0, anchor="ne", relheight=1)
        if not self._rgb_anim_id:
            self._animate_rgb()
    
    def _stop_rgb(self) -> None:
        if self._rgb_anim_id:
            self.after_cancel(self._rgb_anim_id)
            self._rgb_anim_id = None
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            if c:
                c.place_forget()
        self._reset_titlebar_color()
    
    def _set_rgb(self, state: bool) -> None:
        if self.rgb_enabled.get() == state:
            return
        self.rgb_enabled.set(state)
        if state:
            self._start_rgb()
        else:
            self._stop_rgb()
        self._update_rgb_buttons()
        self.config.set("RGB", state)
    
    def _update_rgb_buttons(self) -> None:
        is_on = self.rgb_enabled.get()
        if self._rgb_on_btn_ref and self._rgb_on_btn_ref.winfo_exists():
            self._rgb_on_btn_ref.configure(fg_color="#2d6a4f" if is_on else "#4b4b4b", hover_color="#2d6a4f")
        if self._rgb_off_btn_ref and self._rgb_off_btn_ref.winfo_exists():
            self._rgb_off_btn_ref.configure(fg_color="#8b0000", hover_color="#8b0000")
    
    # ==================== UI SETUP ====================
    
    def _on_closing(self) -> None:
        self._stop_rgb()
        if self._pulse_animation_id:
            try:
                self.after_cancel(self._pulse_animation_id)
            except Exception:
                pass
        if self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except Exception:
                pass
        if self._lock_check_id:
            try:
                self.after_cancel(self._lock_check_id)
            except Exception:
                pass
        for win_attr in ("settings_window", "about_window", "history_window", "qr_window", "db_window"):
            win = getattr(self, win_attr, None)
            if win is not None:
                try:
                    win.destroy()
                except Exception:
                    pass
        self.destroy()
    
    def _get_actual_theme(self) -> str:
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
            except Exception:
                pass
        return "dark"
    
    def _load_all_settings(self) -> None:
        # Полный список настроек по умолчанию
        default_config = {
            "THEME": "Dark",
            "LANG": "RU",
            "SOUND": True,
            "RGB": True,
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
                # Проверяем, есть ли все ключи
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                        need_save = True
            except Exception:
                config = default_config.copy()
                need_save = True
        
        # Сохраняем, если нужно
        if need_save:
            try:
                os.makedirs(CONFIG_DIR, exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
        
        # Синхронизируем синглтон Config с полным словарём настроек.
        # Это гарантирует, что при первом запуске (или неполном файле)
        # все ключи будут записаны в config.json через Config.save().
        self.config.update(config)
        
        # Применяем настройки
        self.current_theme = config.get("THEME", "Dark")
        self.current_lang = config.get("LANG", "RU")
        self.sound_enabled.set(config.get("SOUND", True))
        self.rgb_enabled.set(config.get("RGB", True))
        self.current_radius = config.get("RADIUS", 25)
        self.current_font_size = config.get("font_size", 14)
        self.clipboard_timeout = config.get("CLIP_TIMEOUT", 60)
        self.auto_lock_enabled.set(config.get("AUTO_LOCK", False))
        self.auto_lock_timeout = config.get("AUTO_LOCK_TIMEOUT", 5)
        self.auto_save_var.set(config.get("auto_save", False))
        
        # Применяем визуальные настройки
        set_global_radius(self.current_radius)
        self._change_radius(self.current_radius)
        self._apply_font_size(self.current_font_size)
        
        actual_theme = self._get_actual_theme()
        ctk.set_appearance_mode(self.current_theme)
        self.after(50, lambda: self._apply_theme_colors(actual_theme))
        self.after(60, lambda: self.configure(fg_color="#F3F3F3" if actual_theme == "light" else "#1d1e1e"))
        
        if self.rgb_enabled.get():
            self.after(200, self._start_rgb)
        
        self._update_master_status_label()
        self._update_auto_lock_label()
        
        # Обновляем язык
        self._apply_lang(self.current_lang)
    
    def _update_auto_lock_label(self) -> None:
        if self._auto_lock_label_ref and self._auto_lock_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self._auto_lock_label_ref.configure(text=L["auto_lock_timeout"].format(self.auto_lock_timeout))
    
    def _toggle_auto_lock(self) -> None:
        self.auto_lock_enabled.set(not self.auto_lock_enabled.get())
        if self._auto_lock_btn and self._auto_lock_btn.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if self.auto_lock_enabled.get():
                self._auto_lock_btn.configure(
                    text=L["auto_lock"] + " ✅",
                    fg_color="#2d6a4f",
                    hover_color="#2d6a4f"
                )
            else:
                self._auto_lock_btn.configure(
                    text=L["auto_lock"] + " ❌",
                    fg_color="#8b0000",
                    hover_color="#8b0000"
                )
        self.config.set("AUTO_LOCK", self.auto_lock_enabled.get())
        if self.auto_lock_enabled.get():
            self._last_activity_time = time.time()
    
    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        
        self.lbl_title = ctk.CTkLabel(self.left_panel, text="Secure Pass Pro v4.0", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(5, 0))
        self.lbl_author = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 10))
        
        self.lbl_len = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_len.pack()
        self.slider_len = ctk.CTkSlider(self.left_panel, from_=4, to=64, number_of_steps=60, width=400, command=self._update_len_label)
        self.slider_len.set(20)
        self.slider_len.pack(pady=5)
        
        self.cb_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.cb_frame.pack(pady=10)
        
        self.cb_upper = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.upper_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_upper.grid(row=0, column=1, padx=(70, 20), pady=6, sticky="w")
        
        self.cb_lower = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.lower_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_lower.grid(row=0, column=0, padx=(20, 70), pady=6, sticky="w")
        
        self.cb_digits = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.digits_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_digits.grid(row=1, column=1, padx=(70, 20), pady=6, sticky="w")
        
        self.cb_symb = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.symb_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_symb.grid(row=1, column=0, padx=(20, 70), pady=6, sticky="w")
        
        self.cb_ambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.ambig_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        self.cb_unambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.unambig_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_unambig.grid(row=3, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        self.cb_at_least = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.at_least_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        self.cb_hide = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.hide_var, command=self._toggle_hide, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        self.cb_no_repeat = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.no_repeat_var, border_color="#4EC9B0", hover_color="#4EC9B0")
        self.cb_no_repeat.grid(row=6, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        self.entry_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.entry_frame.pack(pady=15, padx=40, fill="x")
        self.entry_res = ctk.CTkEntry(self.entry_frame, height=50, font=("Consolas", 22), justify="center", corner_radius=self.current_radius)
        self.entry_res.pack(side="left", fill="x", expand=True)
        
        self.btn_eye = ctk.CTkButton(self.entry_frame, text="👁", width=50, height=50,
                                     font=("Segoe UI", 20), fg_color="#3a3a3a", hover_color="#555555",
                                     corner_radius=self.current_radius, command=self._toggle_eye)
        self.btn_eye.pack(side="left", padx=(6, 0))
        self._tooltips["btn_eye"] = ToolTip(self.btn_eye)
        
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
        
        self.lbl_menu = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 18, "bold"))
        self.lbl_menu.pack(pady=15)
        
        self.btn_gen = self._create_menu_btn(self.right_panel, "btn_gen", "tt_gen", self._generate, "#00C853")
        self.btn_copy = self._create_menu_btn(self.right_panel, "btn_copy", "tt_copy", self._copy, "#00B0F0")
        self.btn_save = self._create_menu_btn(self.right_panel, "btn_save", "tt_save", self._save, "#9C27B0")
        self.btn_open = self._create_menu_btn(self.right_panel, "btn_open", "tt_open", self._open, "#FF9800")
        self.btn_qr = self._create_menu_btn(self.right_panel, "btn_qr", "tt_qr", self._show_qr, "#E91E63")
        self.btn_hist = self._create_menu_btn(self.right_panel, "btn_hist", "tt_hist", self._show_history, "#FFC107")
        self.btn_db = self._create_menu_btn(self.right_panel, "btn_db", "tt_db", self._show_db_window, "#2196F3")
        self.btn_upd = self._create_menu_btn(self.right_panel, "btn_upd", "tt_upd", lambda: webbrowser.open(UPD_URL), "#009688")
        self.btn_settings = self._create_menu_btn(self.right_panel, "btn_settings", "tt_settings", self._show_settings, "#607D8B")
        self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#455A64")
        
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_app_rating.pack(pady=(5, 5))
    
    def _create_menu_btn(self, parent, lang_key: str, tt_key: str, cmd, color: str) -> ctk.CTkButton:
        # Словарь цветов для неона при наведении
        neon_colors = {
            "#00C853": "#00E676",  # Зелёный -> ярко-зелёный
            "#00B0F0": "#4FC3F7",  # Голубой -> светло-голубой
            "#9C27B0": "#CE93D8",  # Фиолетовый -> светло-фиолетовый
            "#FF9800": "#FFB74D",  # Оранжевый -> светло-оранжевый
            "#E91E63": "#F06292",  # Малиновый -> светло-малиновый
            "#FFC107": "#FFD54F",  # Золотой -> светло-золотой
            "#2196F3": "#64B5F6",  # Синий -> светло-синий
            "#009688": "#4DB6AC",  # Бирюзовый -> светло-бирюзовый
            "#607D8B": "#90A4AE",  # Серый -> светло-серый
            "#455A64": "#78909C",  # Тёмно-серый -> серый
        }
        
        hover = neon_colors.get(color, color)
        
        btn = ctk.CTkButton(parent, text="", fg_color=color, height=45, border_width=0, font=("Segoe UI", 13, "bold"), hover_color=hover, corner_radius=self.current_radius)
        
        original_cmd = cmd
        
        def animated_cmd():
            self._animate_button(btn)
            original_cmd()
        
        btn.configure(command=animated_cmd)
        btn.pack(pady=6, padx=15, fill="x")
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        self._tooltips[lang_key] = ToolTip(btn)
        return btn
    
    def _animate_button(self, btn: ctk.CTkButton) -> None:
        """Анимация нажатия кнопки (только звук)"""
        play_sound("click", self.sound_enabled.get())
    
    def _apply_theme_colors(self, actual_theme: str) -> None:
        if actual_theme == "light":
            bg_main, fg_main, entry_bg = "#F3F3F3", "#000000", "#FFFFFF"
            panel_bg, border_color, checkmark_color = "#F3F3F3", "#d0d0d0", "#1f538d"
        else:
            bg_main, fg_main, entry_bg = "#1d1e1e", "#FFFFFF", "#2b2b2b"
            panel_bg, border_color, checkmark_color = "#1d1e1e", "#3a3a3a", "#4EC9B0"
        
        self.configure(fg_color=bg_main)
        self.left_panel.configure(fg_color=panel_bg)
        self.right_panel.configure(fg_color=panel_bg, border_color=border_color)
        self.entry_res.configure(fg_color=entry_bg, text_color=fg_main)
        
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb, self.cb_ambig, self.cb_unambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            cb.configure(fg_color=panel_bg, text_color=fg_main, checkmark_color=checkmark_color)
        
        self.lbl_title.configure(text_color=fg_main)
        self.lbl_author.configure(text_color=fg_main)
        self.lbl_len.configure(text_color=fg_main)
        self.lbl_strength.configure(text_color=fg_main)
        self.lbl_strength_text.configure(text_color=fg_main)
        self.lbl_crack.configure(text_color=fg_main)
        self.lbl_menu.configure(text_color=fg_main)
        
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            if c:
                c.configure(bg=bg_main)
    
    def _change_radius(self, val: int) -> None:
        rad = int(val)
        self.current_radius = rad
        set_global_radius(rad)
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr, self.btn_hist, self.btn_db, self.btn_upd, self.btn_settings, self.btn_about]
        for btn in menu_btns:
            btn.configure(corner_radius=rad)
        
        self.btn_eye.configure(corner_radius=rad)
        
        cb_rad = max(rad // 2, 0)
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb, self.cb_ambig, self.cb_unambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            cb.configure(corner_radius=cb_rad)
        
        self.bottom_frame.configure(corner_radius=rad)
        self.right_panel.configure(corner_radius=rad)
        self.entry_res.configure(corner_radius=rad)
        self.entry_frame.configure(corner_radius=rad)
        
        if hasattr(self, 'settings_radius_label') and self.settings_radius_label and self.settings_radius_label.winfo_exists():
            self.settings_radius_label.configure(text=f"{rad} px")
        
        self._update_settings_radius()
        self.config.set("RADIUS", rad)
    
    def _update_settings_radius(self) -> None:
        rad = self.current_radius
        for btn in self.lang_buttons.values():
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
        for btn in self.theme_buttons.values():
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
        for btn in [self._sound_btn, self._close_btn, self._master_set_btn, self._rgb_on_btn_ref, self._rgb_off_btn_ref, self._auto_lock_btn, self.auto_save_btn]:
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
    
    def _center_main_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (950 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"950x800+{x}+{y}")
    
    def _center_window_relative_to_parent(self, window, width: int, height: int) -> None:
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
    
    # ==================== LANGUAGE METHODS ====================
    
    def _apply_lang(self, lang: str) -> None:
        self.current_lang = lang
        L = LANGUAGES[lang]
        
        self.lbl_author.configure(text=L["author"])
        self.lbl_menu.configure(text=L["menu_title"])
        self.lbl_title.configure(text=L["win_title"])
        self._update_len_label(self.slider_len.get())
        
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_unambig.configure(text=L["unambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])
        self.cb_no_repeat.configure(text=L["no_repeat"])
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr, self.btn_hist, self.btn_db, self.btn_upd, self.btn_settings, self.btn_about]
        for btn in menu_btns:
            btn.configure(text=L[btn.lang_key])
            if btn.lang_key in self._tooltips:
                tt_text = L[btn.tt_key]
                if btn.tt_key == "tt_copy":
                    tt_text = tt_text.format(self.clipboard_timeout)
                self._tooltips[btn.lang_key].set_text(tt_text)
        
        if "btn_eye" in self._tooltips:
            self._tooltips["btn_eye"].set_text(L.get("tt_eye", "Show / hide password"))
        
        self.title(L["win_title"])
        
        if self.entry_res.get():
            self._update_strength_meter(self.entry_res.get())
        
        self._update_master_status_label()
        self._update_auto_lock_label()
        
        if hasattr(self, 'auto_save_btn') and self.auto_save_btn:
            if self.auto_save_var.get():
                self.auto_save_btn.configure(text=L.get("auto_save_on", "✅ ВКЛ"))
            else:
                self.auto_save_btn.configure(text=L.get("auto_save_off", "❌ ВЫКЛ"))
    
    def _change_language(self, lang: str) -> None:
        self.current_lang = lang
        self._apply_lang(lang)
        self.config.set("LANG", lang)
        
        for l, btn in self.lang_buttons.items():
            if btn and btn.winfo_exists():
                btn.configure(fg_color="#2d6a4f" if l == lang else "#4b4b4b")
        
        if self.settings_window and self.settings_window.winfo_exists():
            self._close_settings()
        
        if self.entry_res.get():
            self._update_strength_meter(self.entry_res.get())
        self._update_master_status_label()
        self._update_auto_lock_label()
        
        if hasattr(self, 'font_size_value') and self.font_size_value:
            self.font_size_value.configure(text=f"{self.current_font_size}px")
    
    def _change_theme(self, mode: str) -> None:
        self.current_theme = mode
        self.config.set("THEME", mode)

        for name, btn in self.theme_buttons.items():
            if btn and btn.winfo_exists():
                btn.configure(fg_color="#2d6a4f" if name == mode else "#4b4b4b")

        if self.settings_window and self.settings_window.winfo_exists():
            self._close_settings()

        try:
            ctk.set_appearance_mode(mode)
        except Exception:
            pass

        self.after(50, self._sync_theme_colors)
    
    def _sync_theme_colors(self) -> None:
        actual_theme = self._get_actual_theme()
        self._apply_theme_colors(actual_theme)
        bg = "#F3F3F3" if actual_theme == "light" else "#1d1e1e"
        self.configure(fg_color=bg)
        self.update_idletasks()

    # ==================== PASSWORD GENERATION ====================
    
    def _update_len_label(self, val: float) -> None:
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")
    
    def _get_min_length(self) -> int:
        count = sum([self.upper_var.get(), self.lower_var.get(), self.digits_var.get(), self.symb_var.get()])
        return max(4, count)
    
    def _update_strength_meter(self, password: str) -> None:
        if not password:
            self.lbl_strength_text.configure(text="")
            self.lbl_strength.configure(text="")
            self.lbl_crack.configure(text="")
            self.lbl_stars_top.configure(text="")
            return
        
        L = LANGUAGES[self.current_lang]
        stats = self.strength_calc.calculate(password)
        
        self.lbl_strength.configure(text=L["strength"].format(stats['combinations']))
        
        if stats['strength_level'] == 'weak':
            stars_display, stars_color, st_text = "★☆☆☆☆", "#FF4C4C", L["st_low"]
        elif stats['strength_level'] == 'medium':
            if stats['entropy_bits'] < 60:
                stars_display, stars_color, st_text = "★★★☆☆", "#FFA500", L["st_mid"]
            else:
                stars_display, stars_color, st_text = "★★★★☆", "#FFD700", L["st_mid"]
        else:
            stars_display, stars_color, st_text = "★★★★★", "#2ECC71", L["st_high"]
        
        self.lbl_stars_top.configure(text=stars_display, text_color=stars_color)
        self.lbl_strength_text.configure(text=st_text, text_color=stars_color)
        self.lbl_crack.configure(text=L["crack_time"].format(L[stats['crack_time_label']]), text_color=stars_color)
        
        self._animate_password_field(stats['strength_level'])
    
    def _animate_password_field(self, strength_type: str = "medium") -> None:
        original_border = self.entry_res.cget("border_color")
        
        if strength_type == "weak":
            neon_colors = ["#FF4444", "#FF6666", "#FF8888", "#FF6666", "#FF4444"]
        elif strength_type == "strong":
            neon_colors = ["#2ECC71", "#55DD88", "#88EEAA", "#55DD88", "#2ECC71"]
        else:
            neon_colors = ["#FFA500", "#FFBB33", "#FFCC66", "#FFBB33", "#FFA500"]
        
        def pulse_step(step: int = 0) -> None:
            if step < len(neon_colors):
                try:
                    self.entry_res.configure(border_color=neon_colors[step], border_width=3)
                    self._pulse_animation_id = self.after(60, lambda: pulse_step(step + 1))
                except Exception:
                    pass
            else:
                try:
                    self.entry_res.configure(border_color=original_border if original_border else "#2b2b2b", border_width=2)
                except Exception:
                    pass
                self._pulse_animation_id = None
        
        if self._pulse_animation_id:
            try:
                self.after_cancel(self._pulse_animation_id)
            except Exception:
                pass
        pulse_step()
        
    def _generate(self) -> None:
        if hasattr(self, 'btn_gen') and self.btn_gen:
            self._animate_button(self.btn_gen)
        
        L = LANGUAGES[self.current_lang]
        
        self.generator.use_upper = self.upper_var.get()
        self.generator.use_lower = self.lower_var.get()
        self.generator.use_digits = self.digits_var.get()
        self.generator.use_special = self.symb_var.get()
        self.generator.exclude_ambiguous = self.ambig_var.get()
        self.generator.exclude_unambiguous = self.unambig_var.get()
        self.generator.min_each = self.at_least_var.get()
        self.generator.no_repeat = self.no_repeat_var.get()
        self.generator.length = int(self.slider_len.get())
        
        if not (self.generator.use_upper or self.generator.use_lower or self.generator.use_digits or self.generator.use_special):
            CTkMessageBox.warning(self, L.get("err_title", "Error"), L["err_cat"])
            return
        
        password = self.generator.generate()
        
        if password is None:
            CTkMessageBox.warning(self, L.get("err_title", "Error"), L["err_pool_small"])
            return
        
        if self.generator.no_repeat and password is None:
            CTkMessageBox.warning(self, L.get("err_title", "Error"), L["err_no_repeat"] + L["err_no_repeat_fallback"])
            self.generator.no_repeat = False
            password = self.generator.generate()
            self.generator.no_repeat = True
        
        if password:
            self.entry_res.delete(0, "end")
            self.entry_res.insert(0, password)
            self.history.append(password)
            self._update_strength_meter(password)
            play_sound("generate", self.sound_enabled.get())
            
            if self.auto_save_var.get():
                label = f"Auto {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                PasswordDB.save(label, password)
                print(f"[AutoSave] Saved: {label}")
    
    def _copy(self) -> None:
        if hasattr(self, 'btn_copy') and self.btn_copy:
            self._animate_button(self.btn_copy)
        
        pwd = self.entry_res.get().strip()
        if not pwd:
            return
        
        L = LANGUAGES[self.current_lang]
        play_sound("copy", self.sound_enabled.get())
        
        self.clipboard_clear()
        self.clipboard_append(pwd)
        
        if self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except Exception:
                pass
        
        self._clipboard_timer = self.after(self.clipboard_timeout * 1000, lambda value=pwd: self._clear_clipboard_if_unchanged(value))
        
        old_text = self.btn_copy.cget("text")
        self.btn_copy.configure(text=L["copied"].format(self.clipboard_timeout))
        self.after(2000, lambda: self.btn_copy.configure(text=old_text))
    
    def _clear_clipboard_if_unchanged(self, expected: str) -> None:
        try:
            if self.clipboard_get() == expected:
                self.clipboard_clear()
                L = LANGUAGES[self.current_lang]
                CTkMessageBox.info(self, L["master_title"], L.get("clipboard_cleared", "✅ Clipboard cleared!"))
        except Exception:
            pass
        finally:
            self._clipboard_timer = None
    
    # ==================== FILE OPERATIONS ====================
    
    def _verify_pdf(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                header = f.read(5)
                return header == b"%PDF-"
        except Exception:
            return False
    
    def _save(self) -> None:
        L = LANGUAGES[self.current_lang]
        pwd = self.entry_res.get().strip()
        if not pwd:
            return
        
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("Password Files", "*.key"), ("Log Files", "*.log"), ("PDF Files", "*.pdf"), ("All Files", "*.*")])
        
        if not path:
            return
        
        try:
            ext = os.path.splitext(path)[1].lower()
            
            if ext == ".pdf":
                pdf = FPDF()
                pdf.set_author("Maxim Melnikov")
                pdf.set_creator("Secure Pass Pro v4.0")
                pdf.set_title("Secure Pass Pro Password")
                pdf.add_page()
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(200, 10, txt="Secure Pass Pro v4.0", ln=True, align='C')
                pdf.set_font('Arial', '', 12)
                pdf.ln(10)
                pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
                pdf.cell(200, 10, txt=f"Password: {pwd}", ln=True)
                pdf.output(path)
                
                if not self._verify_pdf(path):
                    raise IOError(L["err_integrity"])
            else:
                pwd_bytes = pwd.encode("utf-8")
                success = save_file_with_hash(path, pwd_bytes)
                if not success:
                    raise IOError(L["err_integrity"])
            
            play_sound("success", self.sound_enabled.get())
            fname = os.path.basename(path)
            self.title(f"✅ {fname}")
            self.after(3000, lambda: self.title(L["win_title"]))
        except Exception as e:
            CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_save"].format(e))
    
    def _open(self) -> None:
        L = LANGUAGES[self.current_lang]
        
        path = filedialog.askopenfilename(title="Select password file", filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Password Files", "*.key"), ("Log Files", "*.log"), ("PDF Files", "*.pdf")])
        
        if not path:
            return
        
        try:
            ext = os.path.splitext(path)[1].lower()
            
            if path.lower().endswith(".sha256"):
                CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_unsupported"].format(".sha256"))
                return
            
            if ext == ".pdf":
                if is_windows():
                    os.startfile(path)
                elif is_macos():
                    subprocess.run(["open", path], check=False)
                else:
                    subprocess.run(["xdg-open", path], check=False)
                play_sound("success", self.sound_enabled.get())
                return
            
            if not verify_file_integrity(path):
                if CTkMessageBox.question(self, L.get("err_title", "Error"), L["integrity_warn"]):
                    pass
                else:
                    return
            
            content = None
            encodings = ['utf-8', 'cp1251', 'latin-1', 'cp866', 'koi8-r']
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read().strip()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                with open(path, 'rb') as f:
                    raw_bytes = f.read()
                    content = raw_bytes.decode('utf-8', errors='replace').strip()
            
            if not content:
                raise ValueError("File is empty")
            
            self.entry_res.delete(0, "end")
            self.entry_res.insert(0, content)
            self._update_strength_meter(content)
            play_sound("success", self.sound_enabled.get())
            
        except Exception as e:
            CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_open"].format(str(e)))
    
    # ==================== DIALOGS ====================
    
    def _show_qr(self) -> None:
        pwd = self.entry_res.get()
        if not pwd:
            return
        
        if self.qr_window and self.qr_window.winfo_exists():
            self.qr_window.lift()
            self.qr_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        
        self.qr_window = ctk.CTkToplevel(self)
        self.qr_window.title(L["btn_qr"])
        set_window_icon(self.qr_window)
        self.qr_window.transient(self)
        self.qr_window.attributes('-topmost', True)
        self.qr_window.after(100, lambda: self.qr_window.attributes('-topmost', False))
        self._center_window_relative_to_parent(self.qr_window, 380, 480)
        apply_window_rounding(self.qr_window)
        self.qr_window.protocol("WM_DELETE_WINDOW", self._close_qr)
        
        img = qrcode.make(pwd).resize((280, 280))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
        
        f = ctk.CTkFrame(self.qr_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_qr"], font=("Segoe UI", 18, "bold")).pack()
        
        disp = ctk.CTkFrame(f, fg_color="white", corner_radius=self.current_radius, border_width=2, border_color="gray")
        disp.pack(pady=10)
        qr_label = ctk.CTkLabel(disp, image=ctk_img, text="")
        qr_label.image = ctk_img
        qr_label.pack(padx=10, pady=10)
        ctk.CTkButton(f, text="OK", command=self._close_qr, corner_radius=self.current_radius).pack(pady=10)
        
        self.qr_window.focus_force()
    
    def _close_qr(self) -> None:
        if self.qr_window:
            try:
                self.qr_window.destroy()
            except Exception:
                pass
            self.qr_window = None
    
    def _show_db_window(self) -> None:
        L = LANGUAGES[self.current_lang]
        colors = self._get_colors_for_theme(self._get_actual_theme())
        radius = self.current_radius
        
        if self.db_window and self.db_window.winfo_exists():
            self.db_window.lift()
            self.db_window.focus_force()
            return
        
        self.db_window = ctk.CTkToplevel(self)
        self.db_window.title(L["db_title"])
        self.db_window.resizable(True, True)
        apply_window_rounding(self.db_window)
        self._center_window_relative_to_parent(self.db_window, 700, 560)
        self.db_window.configure(fg_color=colors["bg"])
        self.db_window.protocol("WM_DELETE_WINDOW", self._close_db_window)
        
        top = ctk.CTkFrame(self.db_window, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 6))
        
        ctk.CTkLabel(top, text=L["db_label_prompt"], font=("Segoe UI", 13), text_color=colors["label_text"]).pack(side="left", padx=(0, 6))
        
        label_var = tk.StringVar()
        label_entry = ctk.CTkEntry(top, textvariable=label_var, width=220, height=36, font=("Segoe UI", 13), fg_color=colors["entry_bg"], text_color=colors["fg"], corner_radius=radius)
        label_entry.pack(side="left", padx=(0, 10))
        
        def do_save():
            pwd = self.entry_res.get()
            if not pwd:
                CTkMessageBox.warning(self.db_window, L["db_title"], L["db_no_pass"])
                return
            PasswordDB.save(label_var.get().strip(), pwd)
            CTkMessageBox.info(self.db_window, L["db_title"], L["db_saved"])
            label_var.set("")
            refresh()
        
        label_entry.bind("<Return>", lambda e: do_save())
        
        save_btn = ctk.CTkButton(top, text=L["db_save_current"], width=190, height=36, fg_color="#1a6b5a", hover_color="#2da882", font=("Segoe UI", 13, "bold"), corner_radius=radius, command=do_save)
        save_btn.pack(side="left")
        
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(self.db_window, textvariable=search_var, height=34, font=("Segoe UI", 13), fg_color=colors["entry_bg"], text_color=colors["fg"], corner_radius=radius, placeholder_text=L["db_search"])
        search_entry.pack(fill="x", padx=16, pady=(4, 2))
        search_var.trace_add("write", lambda *_: refresh())
        
        count_lbl = ctk.CTkLabel(self.db_window, text="", font=("Segoe UI", 12), text_color="gray")
        count_lbl.pack(anchor="w", padx=16)
        
        scroll_frame = ctk.CTkScrollableFrame(self.db_window, fg_color=colors["bg"], corner_radius=radius)
        scroll_frame.pack(fill="both", expand=True, padx=14, pady=(6, 10))
        
        close_btn = ctk.CTkButton(self.db_window, text=L["close"], width=140, height=38, fg_color="#ca5010", hover_color="#e05a1a", font=("Segoe UI", 13), corner_radius=radius, command=self._close_db_window)
        close_btn.pack(pady=(0, 12))
        
        def open_edit_dialog(rec):
            dlg = ctk.CTkToplevel(self.db_window)
            dlg.title(L["db_edit_title"])
            dlg.resizable(False, False)
            dlg.grab_set()
            dlg.attributes("-topmost", True)
            dlg_colors = self._get_colors_for_theme(self._get_actual_theme())
            dlg.configure(fg_color=dlg_colors["bg"])
            self._center_window_relative_to_parent(dlg, 420, 260)
            
            ctk.CTkLabel(dlg, text=L["db_edit_label"], font=("Segoe UI", 13), text_color=dlg_colors["label_text"]).pack(padx=20, pady=(18, 2), anchor="w")
            lbl_var = tk.StringVar(value=rec["label"])
            ctk.CTkEntry(dlg, textvariable=lbl_var, width=380, height=36, font=("Segoe UI", 13), fg_color=dlg_colors["entry_bg"], text_color=dlg_colors["fg"], corner_radius=radius).pack(padx=20, pady=(0, 8))
            
            ctk.CTkLabel(dlg, text=L["db_edit_pass"], font=("Segoe UI", 13), text_color=dlg_colors["label_text"]).pack(padx=20, pady=(0, 2), anchor="w")
            pwd_var = tk.StringVar()
            ctk.CTkEntry(dlg, textvariable=pwd_var, width=380, height=36, font=("Consolas", 13), fg_color=dlg_colors["entry_bg"], text_color=dlg_colors["fg"], corner_radius=radius).pack(padx=20, pady=(0, 16))
            
            def do_save_edit():
                new_label = lbl_var.get().strip()
                new_pwd = pwd_var.get().strip() or None
                PasswordDB.update(rec["id"], new_label, new_pwd)
                dlg.destroy()
                refresh()
            
            btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
            btn_row.pack()
            ctk.CTkButton(btn_row, text=L["ok"], width=110, height=34, fg_color="#1a6b5a", corner_radius=radius, command=do_save_edit).pack(side="left", padx=8)
            ctk.CTkButton(btn_row, text=L["cancel"], width=110, height=34, fg_color="#ca5010", corner_radius=radius, command=dlg.destroy).pack(side="left", padx=8)
        
        def refresh():
            for w in scroll_frame.winfo_children():
                w.destroy()
            
            query = search_var.get().strip()
            if query:
                records = PasswordDB.search(query)
            else:
                records = PasswordDB.get_all()
            
            count_lbl.configure(text=L["db_count"].format(len(records)))
            
            if not records:
                ctk.CTkLabel(scroll_frame, text=L["db_empty"], font=("Segoe UI", 14), text_color="gray").pack(pady=30)
                return
            
            for rec in records:
                row = ctk.CTkFrame(scroll_frame, fg_color=colors["entry_bg"], corner_radius=radius)
                row.pack(fill="x", pady=4, padx=2)
                
                info_frame = ctk.CTkFrame(row, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=10, pady=6)
                
                lbl_text = rec["label"] if rec["label"] else f"#{rec['id']}"
                ctk.CTkLabel(info_frame, text=lbl_text, font=("Segoe UI", 13, "bold"), text_color=colors["label_text"]).pack(anchor="w")
                ctk.CTkLabel(info_frame, text=rec["password"], font=("Consolas", 13), text_color="#4EC9B0").pack(anchor="w")
                ctk.CTkLabel(info_frame, text=rec["created"], font=("Segoe UI", 10), text_color="gray").pack(anchor="w")
                
                btn_frame = ctk.CTkFrame(row, fg_color="transparent")
                btn_frame.pack(side="right", padx=8, pady=6)
                
                def make_copy(p=rec["password"]):
                    self.clipboard_clear()
                    self.clipboard_append(p)
                    CTkMessageBox.info(self.db_window, L["db_title"], L["copied"].format(5))
                
                def make_delete(rid=rec["id"]):
                    if CTkMessageBox.question(self.db_window, L["db_title"], L["db_del_confirm"]):
                        PasswordDB.delete(rid)
                        refresh()
                
                def make_edit(r=rec):
                    open_edit_dialog(r)
                
                ctk.CTkButton(btn_frame, text=L["db_copy"], width=80, height=28, fg_color="#107c10", hover_color="#20cf20", font=("Segoe UI", 12), corner_radius=radius, command=make_copy).pack(pady=2)
                ctk.CTkButton(btn_frame, text=L["db_edit"], width=80, height=28, fg_color="#0078d4", hover_color="#309FFF", font=("Segoe UI", 12), corner_radius=radius, command=make_edit).pack(pady=2)
                ctk.CTkButton(btn_frame, text=L["db_delete"], width=80, height=28, fg_color="#8b0000", hover_color="#cc0000", font=("Segoe UI", 12), corner_radius=radius, command=make_delete).pack(pady=2)
        
        refresh()
    
    def _close_db_window(self) -> None:
        if self.db_window and self.db_window.winfo_exists():
            try:
                self.db_window.destroy()
            except Exception:
                pass
            self.db_window = None
    
    def _show_history(self) -> None:
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        
        self.history_window = ctk.CTkToplevel(self)
        self.history_window.title(L["btn_hist"])
        set_window_icon(self.history_window)
        self.history_window.transient(self)
        self.history_window.attributes('-topmost', True)
        self.history_window.after(100, lambda: self.history_window.attributes('-topmost', False))
        self._center_window_relative_to_parent(self.history_window, 500, 580)
        apply_window_rounding(self.history_window)
        self.history_window.protocol("WM_DELETE_WINDOW", self._close_history)
        
        f = ctk.CTkFrame(self.history_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(f, text=L["btn_hist"], font=("Segoe UI", 20, "bold")).pack(pady=10)
        self.current_radius = 25
        txt = ctk.CTkTextbox(f, font=("Consolas", 14), corner_radius=self.current_radius)
        txt.pack(fill="both", expand=True, pady=10)
        
        if not self.history:
            txt.insert("1.0", L["hist_empty"])
        else:
            history_snapshot = list(reversed(self.history))
            txt.insert("1.0", "\n".join(history_snapshot))
        txt.configure(state="disabled")
        
        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.pack(fill="x")
        ctk.CTkButton(btn_f, text=L["btn_clear_hist"], corner_radius=self.current_radius, fg_color="#d13438", command=lambda: self._clear_history_textbox(txt)).pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="OK", corner_radius=self.current_radius, command=self._close_history).pack(side="right", padx=5)
        
        self.history_window.focus_force()
        self.history_textbox = txt
    
    def _close_history(self) -> None:
        if self.history_window:
            try:
                self.history_window.destroy()
            except Exception:
                pass
            self.history_window = None
            self.history_textbox = None
    
    def _clear_history_textbox(self, textbox: ctk.CTkTextbox) -> None:
        L = LANGUAGES[self.current_lang]
        self.history.clear()
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", L["hist_empty"])
        textbox.configure(state="disabled")
    
    def _show_about(self) -> None:
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
        apply_window_rounding(self.about_window)
        self.about_window.protocol("WM_DELETE_WINDOW", self._close_about)
        
        ctk.CTkLabel(self.about_window, text="Secure Pass Pro", font=("Segoe UI", 22, "bold")).pack(pady=(25, 5))
        ctk.CTkLabel(self.about_window, text="Version 4.0", font=("Segoe UI", 14)).pack(pady=(0, 15))
        ctk.CTkLabel(self.about_window, text=L["about_text"], wraplength=350, font=("Segoe UI", 13)).pack(pady=10)
        ctk.CTkButton(self.about_window, text="OK", width=120, command=self._close_about, corner_radius=self.current_radius).pack(pady=(20, 10))
        
        lbl_wiki = ctk.CTkLabel(self.about_window, text=L.get("wiki_link", "Security Logic Wiki"), font=("Segoe UI", 12, "underline"), text_color="#1f538d", cursor="hand2")
        lbl_wiki.pack(pady=(0, 20))
        lbl_wiki.bind("<Button-1>", lambda e: webbrowser.open(wiki_url))
        
        self.about_window.focus_force()
    
    def _close_about(self) -> None:
        if self.about_window:
            try:
                self.about_window.destroy()
            except Exception:
                pass
            self.about_window = None
    
    # ==================== SETTINGS WINDOW ====================
    
    def _show_settings(self) -> None:
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        actual_theme = self._get_actual_theme()
        
        self.settings_window = ctk.CTkToplevel(self)
        if actual_theme == "light":
            self.settings_window.configure(fg_color="#F3F3F3")
        else:
            self.settings_window.configure(fg_color="#1d1e1e")
        self.settings_window.title(L["settings_title"])
        self.settings_window.resizable(False, False)
        set_window_icon(self.settings_window)
        self.settings_window.transient(self)
        self.settings_window.grab_set()
        self._center_window_relative_to_parent(self.settings_window, 550, 800)
        apply_window_rounding(self.settings_window)
        self.settings_window.attributes('-topmost', True)
        self.settings_window.after(100, lambda: self.settings_window.attributes('-topmost', False))
        self.settings_window.focus_force()
        self.settings_window.protocol("WM_DELETE_WINDOW", self._close_settings)
        
        main_frame = ctk.CTkScrollableFrame(self.settings_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Language
        lang_label = ctk.CTkLabel(main_frame, text=L["settings_lang"], font=("Segoe UI", 16, "bold"))
        lang_label.pack(pady=(0, 8))
        lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lang_frame.pack(pady=(0, 12))
        
        self.lang_buttons.clear()
        for lang in ["RU", "EN", "UA"]:
            btn = ctk.CTkButton(lang_frame, text=lang, width=80, height=35, command=lambda l=lang: self._change_language(l), fg_color="#2d6a4f" if self.current_lang == lang else "#4b4b4b", font=("Segoe UI", 14, "bold"), corner_radius=self.current_radius)
            btn.pack(side="left", padx=5)
            self.lang_buttons[lang] = btn
        
        self._add_separator(main_frame)
        
        # Theme
        theme_label = ctk.CTkLabel(main_frame, text=L["settings_theme"], font=("Segoe UI", 16, "bold"))
        theme_label.pack(pady=(8, 8))
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(pady=(0, 12))
        
        sys_btn = ctk.CTkButton(theme_frame, text=L["theme_sys"], width=100, height=35, command=lambda: self._change_theme("System"), fg_color="#2d6a4f" if self.current_theme == "System" else "#4b4b4b", font=("Segoe UI", 12), corner_radius=self.current_radius)
        sys_btn.pack(side="left", padx=5)
        light_btn = ctk.CTkButton(theme_frame, text=L["theme_light"], width=100, height=35, command=lambda: self._change_theme("Light"), fg_color="#2d6a4f" if self.current_theme == "Light" else "#4b4b4b", font=("Segoe UI", 12), corner_radius=self.current_radius)
        light_btn.pack(side="left", padx=5)
        dark_btn = ctk.CTkButton(theme_frame, text=L["theme_dark"], width=100, height=35, command=lambda: self._change_theme("Dark"), fg_color="#2d6a4f" if self.current_theme == "Dark" else "#4b4b4b", font=("Segoe UI", 12), corner_radius=self.current_radius)
        dark_btn.pack(side="left", padx=5)
        
        self.theme_buttons = {"System": sys_btn, "Light": light_btn, "Dark": dark_btn}
        
        self._add_separator(main_frame)
        
        # Security info
        security_label = ctk.CTkLabel(main_frame, text="🛡️ " + L.get("security", "Security"), font=("Segoe UI", 16, "bold"))
        security_label.pack(pady=(8, 5))
        
        if MasterPassword.is_set():
            security_status = ctk.CTkLabel(main_frame, text=L.get("master_status_text", "🔐 Master password: SET (Argon2id)"), font=("Segoe UI", 13), text_color="#2ECC71")
        else:
            security_status = ctk.CTkLabel(main_frame, text=L.get("master_status_not_set_text", "⚠️ Master password: NOT SET"), font=("Segoe UI", 13), text_color="#FF4444")
        security_status.pack(pady=(0, 10))
        
        self._add_separator(main_frame)
        
        # Radius (плавный слайдер)
        radius_label = ctk.CTkLabel(main_frame, text=f"{L['settings_radius']}: {self.current_radius}", font=("Segoe UI", 16, "bold"))
        radius_label.pack(pady=(8, 5))
        self.settings_radius_label = radius_label
        
        radius_slider = ctk.CTkSlider(main_frame, from_=0, to=25, command=self._on_radius_change, width=300)
        radius_slider.set(self.current_radius)
        radius_slider.pack(pady=(5, 12))
        
        self._add_separator(main_frame)
        
        # Sound
        sound_label = ctk.CTkLabel(main_frame, text=L["settings_sound"], font=("Segoe UI", 16, "bold"))
        sound_label.pack(pady=(8, 8))
        
        sound_text = L["sound_on"] if self.sound_enabled.get() else L["sound_off"]
        self._sound_btn = ctk.CTkButton(main_frame, text=sound_text, width=150, height=40, command=self._toggle_sound_settings, fg_color="#2d6a4f" if self.sound_enabled.get() else "#8b0000", hover_color="#2d6a4f" if self.sound_enabled.get() else "#8b0000", font=("Segoe UI", 14), corner_radius=self.current_radius)
        self._sound_btn.pack(pady=(0, 15))
        
        self._add_separator(main_frame)
        
        # Clipboard timeout (плавный слайдер)
        clip_timeout_label = ctk.CTkLabel(main_frame, text=L["clip_timeout"].format(self.clipboard_timeout), font=("Segoe UI", 16, "bold"))
        clip_timeout_label.pack(pady=(8, 5))
        self._clip_timeout_label_ref = clip_timeout_label
        
        clip_slider = ctk.CTkSlider(main_frame, from_=10, to=120, number_of_steps=110, width=300, command=self._on_clip_timeout_change)
        clip_slider.set(self.clipboard_timeout)
        clip_slider.pack(pady=(0, 10))
        
        self._add_separator(main_frame)
        
         # Auto Lock
        auto_lock_label = ctk.CTkLabel(main_frame, text=L["auto_lock"], font=("Segoe UI", 16, "bold"))
        auto_lock_label.pack(pady=(8, 5))
        
        auto_lock_text = L["auto_lock"] + (" ✅" if self.auto_lock_enabled.get() else " ❌")
        self._auto_lock_btn = ctk.CTkButton(main_frame, text=auto_lock_text, width=150, height=40, command=self._toggle_auto_lock, fg_color="#2d6a4f" if self.auto_lock_enabled.get() else "#8b0000", hover_color="#2d6a4f" if self.auto_lock_enabled.get() else "#8b0000", font=("Segoe UI", 14), corner_radius=self.current_radius)
        self._auto_lock_btn.pack(pady=(5, 5))
        self._tooltips["auto_lock"] = ToolTip(self._auto_lock_btn)
        self._tooltips["auto_lock"].set_text(L.get("tt_auto_lock", "Auto lock on inactivity"))
        
        self._auto_lock_label_ref = ctk.CTkLabel(main_frame, text=L["auto_lock_timeout"].format(self.auto_lock_timeout), font=("Segoe UI", 13))
        self._auto_lock_label_ref.pack(pady=(5, 0))
        
        # Auto lock timeout (плавный слайдер)
        self._auto_lock_slider = ctk.CTkSlider(main_frame, from_=1, to=30, number_of_steps=29, width=300, command=self._on_auto_lock_timeout_change)
        self._auto_lock_slider.set(self.auto_lock_timeout)
        self._auto_lock_slider.pack(pady=(5, 15))
        
        self._add_separator(main_frame)
        
        # Master Password
        master_label = ctk.CTkLabel(main_frame, text="🔐 " + L["master_title"], font=("Segoe UI", 16, "bold"))
        master_label.pack(pady=(8, 5))
        
        self._master_status_label = ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 13))
        self._master_status_label.pack(pady=(0, 5))
        self._update_master_status_label()
        
        master_btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        master_btn_frame.pack(pady=(0, 10))
        
        self._master_set_btn = ctk.CTkButton(master_btn_frame, text="", width=180, height=40, font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._master_set_btn.pack(side="left", padx=5)
        self._update_master_buttons()
        
        self._add_separator(main_frame)
        
        # RGB
        rgb_label = ctk.CTkLabel(main_frame, text=L["rgb_label"], font=("Segoe UI", 16, "bold"))
        rgb_label.pack(pady=(8, 6))
        
        rgb_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        rgb_frame.pack(pady=(0, 12))
        
        is_rgb_on = self.rgb_enabled.get()
        
        self._rgb_on_btn_ref = ctk.CTkButton(rgb_frame, text=L["rgb_on"], width=110, height=35, command=lambda: self._set_rgb(True), fg_color="#2d6a4f" if is_rgb_on else "#4b4b4b", hover_color="#2d6a4f", font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._rgb_on_btn_ref.pack(side="left", padx=5)
        
        self._rgb_off_btn_ref = ctk.CTkButton(rgb_frame, text=L["rgb_off"], width=110, height=35, command=lambda: self._set_rgb(False), fg_color="#8b0000", hover_color="#8b0000", font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._rgb_off_btn_ref.pack(side="left", padx=5)
        
        self._add_separator(main_frame)
        
        # Font size (плавный слайдер)
        font_size_label = ctk.CTkLabel(main_frame, text=L.get("font_size", "Размер шрифта"), 
                                        font=("Segoe UI", 16, "bold"))
        font_size_label.pack(pady=(8, 5))
        
        self.font_size_value = ctk.CTkLabel(main_frame, text=f"{self.current_font_size}px",
                                             font=("Segoe UI", 18, "bold"))
        self.font_size_value.pack(pady=(0, 5))
        
        self.font_size_slider = ctk.CTkSlider(main_frame, from_=10, to=20, number_of_steps=10,
                                               command=self._on_font_size_change, width=300)
        self.font_size_slider.set(self.current_font_size)
        self.font_size_slider.pack(pady=(0, 10))
        
        self._add_separator(main_frame)
        
        # ========== AUTO SAVE SETTING ==========
        auto_save_label_settings = ctk.CTkLabel(main_frame, text=L.get("auto_save_label", "📁 Автосохранение"), font=("Segoe UI", 16, "bold"))
        auto_save_label_settings.pack(pady=(8, 6))
        
        self.auto_save_btn = ctk.CTkButton(
            main_frame,
            text=L["auto_save_on"] if self.auto_save_var.get() else L["auto_save_off"],
            width=150,
            height=40,
            command=self._toggle_auto_save,
            fg_color="#2d6a4f" if self.auto_save_var.get() else "#8b0000",
            hover_color="#2d6a4f" if self.auto_save_var.get() else "#8b0000",
            corner_radius=self.current_radius
        )
        self.auto_save_btn.pack(pady=(0, 15))
        
        self.auto_save_btn.pack(pady=(0, 15))
        
        self._add_separator(main_frame)
        
        # Close button
        self._close_btn = ctk.CTkButton(main_frame, text=L["close"], command=self._close_settings, fg_color="#8b0000", hover_color="#8b0000", width=150, height=40, font=("Segoe UI", 14), corner_radius=self.current_radius)
        self._close_btn.pack(pady=(10, 10))
        
        self.settings_labels = {'lang': lang_label, 'theme': theme_label, 'sound': sound_label, 'close_btn': self._close_btn, 'sound_btn': self._sound_btn, 'radius_slider': radius_slider}
    
    def _add_separator(self, parent) -> None:
        sep = ctk.CTkFrame(parent, height=2, fg_color="gray")
        sep.pack(fill="x", pady=8)
    
    def _on_radius_change(self, val: float) -> None:
        rad = int(val)
        if self.settings_radius_label and self.settings_radius_label.winfo_exists():
            self.settings_radius_label.configure(text=f"{rad} px")
        
        if self._radius_timer:
            self.after_cancel(self._radius_timer)
        self._radius_timer = self.after(50, lambda: self._change_radius(rad))
    
    def _on_clip_timeout_change(self, val: float) -> None:
        seconds = int(val)
        if self._clip_timeout_label_ref and self._clip_timeout_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self._clip_timeout_label_ref.configure(text=L["clip_timeout"].format(seconds))
        
        if self._clip_timer:
            self.after_cancel(self._clip_timer)
        self._clip_timer = self.after(50, lambda: self._apply_clip_timeout(seconds))
    
    def _apply_clip_timeout(self, seconds: int) -> None:
        self.clipboard_timeout = seconds
        if "btn_copy" in self._tooltips:
            L = LANGUAGES[self.current_lang]
            self._tooltips["btn_copy"].set_text(L["tt_copy"].format(seconds))
        self.config.set("CLIP_TIMEOUT", seconds)
    
    def _on_auto_lock_timeout_change(self, val: float) -> None:
        minutes = int(val)
        if self._auto_lock_label_ref and self._auto_lock_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self._auto_lock_label_ref.configure(text=L["auto_lock_timeout"].format(minutes))
        
        if self._auto_timer:
            self.after_cancel(self._auto_timer)
        self._auto_timer = self.after(50, lambda: self._apply_auto_timeout(minutes))
    
    def _apply_auto_timeout(self, minutes: int) -> None:
        self.auto_lock_timeout = minutes
        self.config.set("AUTO_LOCK_TIMEOUT", minutes)
    
    def _on_font_size_change(self, val: float) -> None:
        size = int(val)
        if hasattr(self, 'font_size_value') and self.font_size_value:
            self.font_size_value.configure(text=f"{size}px")
        
        if self._font_timer:
            self.after_cancel(self._font_timer)
        self._font_timer = self.after(50, lambda: self._apply_font_size(size))
    
    def _apply_font_size(self, size: int) -> None:
        self.current_font_size = size
        self.config.set("font_size", size)
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, 
                     self.btn_qr, self.btn_hist, self.btn_db, self.btn_upd, 
                     self.btn_settings, self.btn_about]
        for btn in menu_btns:
            btn.configure(font=("Segoe UI", size - 1, "bold"))
        
        self.lbl_title.configure(font=("Segoe UI", size + 6, "bold"))
        self.lbl_menu.configure(font=("Segoe UI", size + 4, "bold"))
        self.lbl_strength_text.configure(font=("Segoe UI", size, "bold"))
        self.entry_res.configure(font=("Consolas", size + 8))
        self.btn_eye.configure(font=("Segoe UI", size + 6))
    
    def _close_settings(self) -> None:
        if self.settings_window:
            self.settings_window.grab_release()
            self.settings_window.destroy()
            self.settings_window = None
            self.settings_labels = {}
            self.lang_buttons = {}
            self.theme_buttons = {}
            self._master_set_btn = None
            self._master_status_label = None
            self._sound_btn = None
            self._close_btn = None
            self._rgb_on_btn_ref = None
            self._rgb_off_btn_ref = None
            self.settings_radius_label = None
            self._clip_timeout_label_ref = None
            self._auto_lock_btn = None
            self._auto_lock_slider = None
            self._auto_lock_label_ref = None
            self._radius_timer = None
            self._clip_timer = None
            self._auto_timer = None
            self._font_timer = None
    
    def _toggle_sound_settings(self) -> None:
        self.sound_enabled.set(not self.sound_enabled.get())
        if self._sound_btn and self._sound_btn.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if self.sound_enabled.get():
                self._sound_btn.configure(
                    text=L["sound_on"],
                    fg_color="#2d6a4f",
                    hover_color="#2d6a4f"
                )
            else:
                self._sound_btn.configure(
                    text=L["sound_off"],
                    fg_color="#8b0000",
                    hover_color="#8b0000"
                )
        play_sound("click", self.sound_enabled.get())
        self.config.set("SOUND", self.sound_enabled.get())
    
    def _toggle_auto_save(self) -> None:
        new_value = not self.auto_save_var.get()
        self.auto_save_var.set(new_value)
        self.config.set("auto_save", new_value)
        
        L = LANGUAGES[self.current_lang]
        if new_value:
            self.auto_save_btn.configure(
                text=L["auto_save_on"],
                fg_color="#2d6a4f",
                hover_color="#2d6a4f"
            )
            CTkMessageBox.info(self, L["auto_save"], L["auto_save_enabled"])
        else:
            self.auto_save_btn.configure(
                text=L["auto_save_off"],
                fg_color="#8b0000",
                hover_color="#8b0000"
            )
            CTkMessageBox.info(self, L["auto_save"], L["auto_save_disabled"])
    
    def _toggle_hide(self) -> None:
        self._sync_eye_to_hide_var()
    
    def _toggle_eye(self) -> None:
        self.hide_var.set(not self.hide_var.get())
        self._sync_eye_to_hide_var()
    
    def _sync_eye_to_hide_var(self) -> None:
        hidden = self.hide_var.get()
        self.entry_res.configure(show="*" if hidden else "")
        self.btn_eye.configure(text="🙈" if hidden else "👁")
    
    # ==================== MASTER PASSWORD ====================
    
    def _update_master_status_label(self) -> None:
        if self._master_status_label and self._master_status_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if MasterPassword.is_set():
                self._master_status_label.configure(text=f"{L['master_current']} 🔒 {L['master_status_set']}", text_color="#2ECC71")
            else:
                self._master_status_label.configure(text=f"{L['master_current']} 🔓 {L['master_status_not_set']}", text_color="#FF4444")
    
    def _update_master_buttons(self) -> None:
        if not self._master_set_btn or not self._master_set_btn.winfo_exists():
            return
        L = LANGUAGES[self.current_lang]
        if MasterPassword.is_set():
            self._master_set_btn.configure(
                text="🔒 " + L["master_btn_remove"],
                fg_color="#8b0000",
                hover_color="#8b0000",
                command=self._remove_master_password
            )
        else:
            self._master_set_btn.configure(
                text="🔓 " + L["master_btn_set"],
                fg_color="#2d6a4f",
                hover_color="#2d6a4f",
                command=self._toggle_master_password
            )
    
    def _toggle_master_password(self) -> None:
        L = LANGUAGES[self.current_lang]
        actual_theme = self._get_actual_theme()
        
        if MasterPassword.is_set():
            current = CTkInputDialog.ask(self, L["master_title"], L["master_prompt"], show="*", theme=actual_theme, lang=self.current_lang)
            if current is None:
                return
            if not MasterPassword.verify(current):
                CTkMessageBox.error(self, L.get("err_title", "Error"), L["master_wrong"].format(1, 1))
                return
            MasterPassword.remove()
            CTkMessageBox.info(self, L["master_title"], L["master_removed"])
        else:
            new_pwd = CTkInputDialog.ask(self, L["master_set_title"], L["master_set_prompt"], show="*", theme=actual_theme, lang=self.current_lang)
            if new_pwd is None or new_pwd == "":
                return
            confirm = CTkInputDialog.ask(self, L["master_set_title"], L["master_confirm"], show="*", theme=actual_theme, lang=self.current_lang)
            if confirm is None:
                return
            if new_pwd != confirm:
                CTkMessageBox.error(self, L.get("err_title", "Error"), L["master_mismatch"])
                return
            MasterPassword.set_password(new_pwd)
            CTkMessageBox.info(self, L["master_title"], L["master_set_ok"])
        
        self._update_master_buttons()
        self._update_master_status_label()
    
    def _remove_master_password(self) -> None:
        L = LANGUAGES[self.current_lang]
        if not MasterPassword.is_set():
            return
        if CTkMessageBox.question(self, L["master_title"], L["master_remove_confirm"]):
            MasterPassword.remove()
            CTkMessageBox.info(self, L["master_title"], L["master_removed"])
            self._update_master_buttons()
            self._update_master_status_label()


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    
    _startup_lang = "RU"
    _startup_theme = "dark"
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as _f:
                try:
                    _cfg = json.load(_f)
                except (json.JSONDecodeError, ValueError):
                    _cfg = {}
                if "LANG" in _cfg and _cfg["LANG"] in ("RU", "EN", "UA"):
                    _startup_lang = _cfg["LANG"]
                if "THEME" in _cfg:
                    if _cfg["THEME"] == "Light":
                        _startup_theme = "light"
                    elif _cfg["THEME"] == "Dark":
                        _startup_theme = "dark"
    except Exception:
        pass
    
    if not MasterPassword.prompt_on_startup(_startup_lang, _startup_theme):
        sys.exit(0)
    
    app = SecurePassPro()
    app.mainloop()