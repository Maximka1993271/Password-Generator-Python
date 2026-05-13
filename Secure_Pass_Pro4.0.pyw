"""
Secure Pass Pro v4.0 — Cryptographically secure password generator
Author: Maxim Melnikov

Do not modify user .key, .log, .txt, or PDF files during audit.
Не изменять пользовательские .key, .log, .txt и PDF-файлы во время аудита.
Не змінювати користувацькі .key, .log, .txt та PDF-файли під час аудиту.

Keep comments in 3 languages.
Оставлять комментарии на 3 языках.
Залишати коментарі 3 мовами.
"""

from __future__ import annotations
from collections import deque
import hashlib
import hmac
import math
import platform
import random
import secrets
import string
import sys
import os
import webbrowser
import datetime
import shutil
import subprocess
import tempfile
import tkinter as tk
from tkinter import filedialog
import ctypes
import json
from typing import Optional, Dict, Any, List


def _show_startup_error(title: str, text: str) -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        import tkinter.messagebox as msgbox
        msgbox.showerror(title, text)
    finally:
        root.destroy()


_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"

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

# ==================== CONSTANTS ====================
HISTORY_MAX = 50
AMBIGUOUS_CHARS = "il1Lo0O"
UNAMBIG_CHARS = "{}[]()/\\'\"`~,;:.<>"
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"
HASH_EXTENSION = ".sha256"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".securepasspro")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")

# Global radius for all dialogs
_global_radius = 10


def set_global_radius(radius: int) -> None:
    global _global_radius
    _global_radius = radius


def get_global_radius() -> int:
    return _global_radius


def _get_resource_path(filename: str) -> str:
    base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def _center_screen(win: tk.Tk | ctk.CTkToplevel, width: int, height: int) -> None:
    screen_w = win.winfo_screenwidth()
    screen_h = win.winfo_screenheight()
    x = max(0, (screen_w - width) // 2)
    y = max(0, (screen_h - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# ==================== MASTER PASSWORD ====================
class MasterPassword:
    MAX_ATTEMPTS = 5
    SALT_SIZE = 32
    ITERATIONS = 100000
    
    @classmethod
    def _derive_key(cls, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, cls.ITERATIONS, dklen=32)
    
    @classmethod
    def is_set(cls) -> bool:
        return os.path.exists(MASTER_FILE)
    
    @classmethod
    def verify(cls, password: str) -> bool:
        if not cls.is_set():
            return True
        try:
            with open(MASTER_FILE, 'rb') as f:
                salt = f.read(cls.SALT_SIZE)
                stored_hash = f.read()
            derived = cls._derive_key(password, salt)
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(derived, stored_hash)
        except Exception:
            return False
    
    @classmethod
    def set_password(cls, password: str) -> None:
        if not password:
            raise ValueError("Master password must not be empty")
        os.makedirs(CONFIG_DIR, exist_ok=True)
        salt = secrets.token_bytes(cls.SALT_SIZE)
        derived = cls._derive_key(password, salt)
        with open(MASTER_FILE, 'wb') as f:
            f.write(salt + derived)
    
    @classmethod
    def remove(cls) -> None:
        try:
            os.remove(MASTER_FILE)
        except Exception:
            pass
    
    @classmethod
    def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
        if not cls.is_set():
            return True
        
        L = LANGUAGES.get(lang, LANGUAGES["RU"])
        attempts = 0
        root = ctk.CTk()
        root.withdraw()
        
        try:
            while attempts < cls.MAX_ATTEMPTS:
                pwd = CTkInputDialog.ask(
                    root, L["master_title"], L["master_prompt"], 
                    show="*", theme=theme, lang=lang
                )
                if pwd is None:
                    return False
                if cls.verify(pwd):
                    return True
                attempts += 1
                remaining = cls.MAX_ATTEMPTS - attempts
                if remaining > 0:
                    CTkMessageBox.warning(
                        root, L["master_title"], 
                        L["master_wrong"].format(attempts, cls.MAX_ATTEMPTS)
                    )
            CTkMessageBox.error(root, L["master_title"], L["master_blocked"])
            return False
        finally:
            root.destroy()


# ==================== CUSTOM DIALOGS ====================
class CTkMessageBox:
    _current_theme = "dark"
    _current_lang = "RU"
    
    @classmethod
    def set_theme(cls, theme: str) -> None:
        cls._current_theme = theme
    
    @classmethod
    def set_lang(cls, lang: str) -> None:
        cls._current_lang = lang
    
    @staticmethod
    def _get_colors(theme: str) -> Dict[str, str]:
        if theme == "light":
            return {"bg": "#F3F3F3", "fg": "#000000", "button_fg": "#1f538d", "button_text": "#FFFFFF", "label_text": "#000000", "entry_bg": "#FFFFFF"}
        return {"bg": "#1d1e1e", "fg": "#FFFFFF", "button_fg": "#1f538d", "button_text": "#FFFFFF", "label_text": "#FFFFFF", "entry_bg": "#2b2b2b"}
    
    @staticmethod
    def _show(parent, title: str, message: str, button_text: str = "OK", icon: str = "ℹ️", icon_color: str = "#4EC9B0", button_color: str = "#1f538d", is_question: bool = False) -> Optional[str]:
        win = ctk.CTkToplevel(parent)
        win.title(title)
        win.resizable(False, False)
        win.grab_set()
        win.attributes("-topmost", True)
        
        colors = CTkMessageBox._get_colors(CTkMessageBox._current_theme)
        L = LANGUAGES.get(CTkMessageBox._current_lang, LANGUAGES["RU"])
        
        w, h = (420, 220) if is_question else (420, 200)
        
        _center_screen(win, w, h)
        win.configure(fg_color=colors["bg"])
        
        ctk.CTkLabel(win, text=icon, font=("Segoe UI", 40), text_color=icon_color).pack(pady=(20, 5))
        ctk.CTkLabel(win, text=message, font=("Segoe UI", 13), wraplength=360, justify="center", text_color=colors["label_text"]).pack(pady=(0, 15))
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack()
        
        radius = get_global_radius()
        result = [None]
        
        if is_question:
            def on_yes(): result[0] = "yes"; win.destroy()
            def on_no(): result[0] = "no"; win.destroy()
            ctk.CTkButton(btn_frame, text=L.get("yes", "Да"), width=100, height=35, command=on_yes, fg_color="#2d6a4f", corner_radius=radius).pack(side="left", padx=8)
            ctk.CTkButton(btn_frame, text=L.get("no", "Нет"), width=100, height=35, command=on_no, fg_color="#8b0000", corner_radius=radius).pack(side="left", padx=8)
        else:
            def on_ok(): result[0] = "ok"; win.destroy()
            btn_text = button_text if button_text != "OK" else L.get("ok", "OK")
            ctk.CTkButton(btn_frame, text=btn_text, width=120, height=35, command=on_ok, fg_color=colors["button_fg"], corner_radius=radius).pack()
        
        win.after(100, lambda: win.attributes("-topmost", False))
        win.after(50, lambda: _center_screen(win, w, h))
        
        parent.wait_window(win)
        return result[0]
    
    @staticmethod
    def info(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="✅", icon_color="#2ECC71")
    
    @staticmethod
    def warning(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="⚠️", icon_color="#FFA500")
    
    @staticmethod
    def error(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="❌", icon_color="#FF4444")
    
    @staticmethod
    def question(parent, title: str, message: str) -> bool:
        result = CTkMessageBox._show(parent, title, message, is_question=True)
        return result == "yes"


class CTkInputDialog:
    def __init__(self, parent, title: str, prompt: str, show: str = "", theme: str = "dark", lang: str = "RU"):
        self.result: Optional[str] = None
        self.win = ctk.CTkToplevel(parent)
        self.win.title(title)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.attributes("-topmost", True)
        
        L = LANGUAGES.get(lang, LANGUAGES["RU"])
        radius = get_global_radius()
        
        if theme == "light":
            bg_color, fg_color, entry_bg, btn_fg = "#F3F3F3", "#000000", "#FFFFFF", "#1f538d"
        else:
            bg_color, fg_color, entry_bg, btn_fg = "#1d1e1e", "#FFFFFF", "#2b2b2b", "#1f538d"
        
        _center_screen(self.win, 420, 220)
        self.win.configure(fg_color=bg_color)
        
        ctk.CTkLabel(self.win, text=prompt, font=("Segoe UI", 13), wraplength=360, text_color=fg_color).pack(padx=20, pady=(20, 8))
        self.entry = ctk.CTkEntry(self.win, width=360, height=40, font=("Segoe UI", 14), show=show, fg_color=entry_bg, text_color=fg_color, corner_radius=radius)
        self.entry.pack(padx=20, pady=(0, 12))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._ok())
        self.entry.bind("<Escape>", lambda e: self._cancel())
        
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text=L["ok"], width=110, height=36, command=self._ok, fg_color=btn_fg, corner_radius=radius).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=L["cancel"], width=110, height=36, command=self._cancel, fg_color="#ca5010", corner_radius=radius).pack(side="left", padx=8)
        
        self.win.protocol("WM_DELETE_WINDOW", self._cancel)
        self.win.after(100, lambda: self.win.attributes("-topmost", False))
        self.win.after(50, lambda: _center_screen(self.win, 420, 220))
        
        parent.wait_window(self.win)
    
    def _ok(self) -> None:
        self.result = self.entry.get()
        self.win.destroy()
    
    def _cancel(self) -> None:
        self.result = None
        self.win.destroy()
    
    @staticmethod
    def ask(parent, title: str, prompt: str, show: str = "", theme: str = "dark", lang: str = "RU") -> Optional[str]:
        return CTkInputDialog(parent, title, prompt, show, theme, lang).result


class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.text = ""
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    
    def set_text(self, text: str) -> None:
        self.text = text
    
    def show_tip(self, event=None) -> None:
        if self.tip_window or not self.text:
            return
        try:
            if not self.widget.winfo_exists():
                return
        except Exception:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("Segoe UI", 9, "normal")).pack(ipadx=1)
    
    def hide_tip(self, event=None) -> None:
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class UTF8PDF(FPDF):
    """FPDF subclass used for PDF password export."""
    pass


# ==================== LANGUAGES ====================
LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": {
        "win_title": "Secure Pass Pro v4.0", "menu_title": "Меню", "len": "Длина",
        "author": "Автор: Максим Мельников", "upper": "Заглавные буквы", "lower": "Строчные буквы",
        "digits": "Цифры", "symb": "Спецсимволы", "ambig": "Исключить похожие (i, l, 1...)",
        "unambig": "Исключить не однозначные", "at_least": "Минимум 1 из каждой категории",
        "hide": "Скрывать символы", "btn_gen": "Сгенерировать", "btn_copy": "Копировать пароль",
        "btn_save": "Сохранить в файл", "btn_open": "Открыть файл", "btn_qr": "QR-код пароль",
        "btn_hist": "История", "btn_upd": "Обновить программу", "btn_about": "О программе",
        "btn_settings": "Настройки", "radius": "Закругление углов", "sound_on": "Звук: ВКЛ",
        "sound_off": "Звук: ВЫКЛ", "theme_sys": "Системная", "theme_dark": "Тёмная",
        "theme_light": "Светлая", "about_text": "Secure Pass Pro v4.0\n\nПрофессиональный инструмент для генерации паролей.\nИспользует криптографически стойкие алгоритмы.",
        "copied": "Скопировано! ({0}с)", "strength": "Стойкость: ~{0} вариантов",
        "crack_time": "{0}", "time_sec": "Несколько секунд на взлом", "time_day": "Дни на взлом",
        "time_year": "Года на взлом", "time_cent": "Столетия на взлом", "st_low": "Слабый пароль",
        "st_mid": "Средний пароль", "st_high": "Надежный пароль", "tt_gen": "Создать новый случайный пароль",
        "tt_copy": "Копировать в буфер (очистка через {0} сек)", "tt_save": "Сохранить текущий пароль в файл",
        "tt_open": "Открыть пароль из файла .key, .log или .txt", "tt_qr": "Создать QR-код для быстрого сканирования",
        "tt_hist": "Показать последние 50 паролей", "tt_upd": "Проверить наличие новой версии на GitHub",
        "tt_about": "Информация о разработчике и программе", "tt_settings": "Язык, звук и тема оформления",
        "settings_title": "Настройки", "settings_lang": "Язык интерфейса", "settings_sound": "Звук приложения",
        "settings_theme": "Тема оформления", "settings_radius": "Закругление углов", "close": "Закрыть",
        "ok": "OK", "cancel": "Отмена", "yes": "Да", "no": "Нет", "master_status_set": "Установлен",
        "master_status_not_set": "Не установлен", "err_cat": "Выберите хотя бы одну категорию!",
        "err_pool_small": "Слишком мало доступных символов после исключений!",
        "err_save": "Ошибка сохранения: {0}", "err_open": "Не удалось прочитать файл: {0}",
        "err_unsupported": "Неподдерживаемый тип файла: {0}", "err_integrity": "Критическая ошибка: Файл поврежден после записи!",
        "hist_empty": "История пуста...", "btn_clear_hist": "Очистить историю", "pdf_date": "Дата",
        "pdf_pass": "Пароль", "wiki_link": "Читать Security Logic Wiki", "err_title": "Ошибка",
        "no_repeat": "Избегать повторов символов подряд", "tt_no_repeat": "Не допускать одинаковых символов подряд (aaa, 111)",
        "err_no_repeat": "Не удалось создать пароль без повторов. Уменьшите длину или добавьте категории.",
        "err_no_repeat_fallback": "\nИспользован пароль с повторами.", "master_title": "Мастер-пароль",
        "master_prompt": "Введите мастер-пароль для доступа к программе:",
        "master_set_title": "Установить мастер-пароль", "master_set_prompt": "Придумайте мастер-пароль (оставьте пустым — без защиты):",
        "master_confirm": "Подтвердите мастер-пароль:", "master_mismatch": "Пароли не совпадают!",
        "master_wrong": "Неверный мастер-пароль! Попытка {0} из {1}.", "master_blocked": "Превышено число попыток. Программа закрыта.",
        "master_set_ok": "Мастер-пароль установлен.", "master_removed": "Мастер-пароль удалён.",
        "master_btn_set": "Установить мастер-пароль", "master_btn_remove": "Удалить мастер-пароль",
        "master_current": "Статус:", "master_remove_confirm": "Вы уверены, что хотите удалить мастер-пароль?\n\nПосле удаления доступ к программе не будет защищён.",
        "integrity_warn": "⚠ Внимание: контрольная сумма не найдена для файла.\nФайл мог быть изменён сторонним ПО.\nПродолжить открытие?",
        "integrity_fail": "🚨 КРИТИЧЕСКАЯ ОШИБКА: Файл повреждён или подменён!\nКонтрольная сумма не совпадает. Открытие отменено.",
        "integrity_ok": "✅ Целостность файла подтверждена.", "tt_eye": "Показать / скрыть пароль",
        "clip_timeout": "Очистка буфера: {0} сек", "tt_clip_timeout": "Через сколько секунд буфер обмена будет очищен после копирования",
        "rgb_label": "🌈 RGB-подсветка", "rgb_on": "ВКЛ", "rgb_off": "ВЫКЛ",
    },
    "EN": {
        "win_title": "Secure Pass Pro v4.0", "menu_title": "Menu", "len": "Length",
        "author": "Author: Maxim Melnikov", "upper": "Uppercase", "lower": "Lowercase",
        "digits": "Digits", "symb": "Special symbols", "ambig": "Exclude ambiguous (i, l, 1...)",
        "unambig": "Exclude non-obvious", "at_least": "Min 1 from each category",
        "hide": "Hide symbols", "btn_gen": "Generate", "btn_copy": "Copy password",
        "btn_save": "Save to file", "btn_open": "Open file", "btn_qr": "Password QR-code",
        "btn_hist": "History", "btn_upd": "Update program", "btn_about": "About",
        "btn_settings": "Settings", "radius": "Corner radius", "sound_on": "Sound: ON",
        "sound_off": "Sound: OFF", "theme_sys": "System", "theme_dark": "Dark",
        "theme_light": "Light", "about_text": "Secure Pass Pro v4.0\n\nProfessional password generation tool.\nUses cryptographically secure algorithms.",
        "copied": "Copied! ({0}s)", "strength": "Strength: ~{0} combos", "crack_time": "{0}",
        "time_sec": "A few seconds to crack", "time_day": "Days to crack", "time_year": "Years to crack",
        "time_cent": "Centuries to crack", "st_low": "Weak password", "st_mid": "Medium password",
        "st_high": "Strong password", "tt_gen": "Create a new random password",
        "tt_copy": "Copy to clipboard (clears in {0} sec)", "tt_save": "Save current password to file",
        "tt_open": "Open password from .key, .log or .txt", "tt_qr": "Create a QR code for quick scanning",
        "tt_hist": "Show last 50 generated passwords", "tt_upd": "Check for new version on GitHub",
        "tt_about": "Developer and program info", "tt_settings": "Language, sound and theme",
        "settings_title": "Settings", "settings_lang": "Interface language", "settings_sound": "App Sound",
        "settings_theme": "Appearance theme", "settings_radius": "Corner radius", "close": "Close",
        "ok": "OK", "cancel": "Cancel", "yes": "Yes", "no": "No", "master_status_set": "Set",
        "master_status_not_set": "Not set", "err_cat": "Select at least one category!",
        "err_pool_small": "Too few available characters after exclusions!",
        "err_save": "Save failed: {0}", "err_open": "Could not read file: {0}",
        "err_unsupported": "Unsupported file type: {0}", "err_integrity": "Critical error: File corrupted after write!",
        "hist_empty": "History is empty...", "btn_clear_hist": "Clear History", "pdf_date": "Date",
        "pdf_pass": "Password", "wiki_link": "Read Security Logic Wiki", "err_title": "Error",
        "no_repeat": "Avoid consecutive repeated characters", "tt_no_repeat": "Prevent the same character appearing consecutively (aaa, 111)",
        "err_no_repeat": "Could not generate password without repeats. Reduce length or add categories.",
        "err_no_repeat_fallback": "\nPassword with repeats used.", "master_title": "Master Password",
        "master_prompt": "Enter master password to access the program:",
        "master_set_title": "Set Master Password", "master_set_prompt": "Create a master password (leave blank for no protection):",
        "master_confirm": "Confirm master password:", "master_mismatch": "Passwords do not match!",
        "master_wrong": "Wrong master password! Attempt {0} of {1}.", "master_blocked": "Too many failed attempts. Program closed.",
        "master_set_ok": "Master password has been set.", "master_removed": "Master password removed.",
        "master_btn_set": "Set Master Password", "master_btn_remove": "Remove Master Password",
        "master_current": "Status:", "master_remove_confirm": "Are you sure you want to remove the master password?\n\nAfter removal, access to the program will not be protected.",
        "integrity_warn": "⚠ Warning: no checksum found for this file.\nThe file may have been modified externally.\nContinue opening?",
        "integrity_fail": "🚨 CRITICAL ERROR: File is corrupted or tampered!\nChecksum mismatch. Opening cancelled.",
        "integrity_ok": "✅ File integrity verified.", "tt_eye": "Show / hide password",
        "clip_timeout": "Clipboard clear: {0} sec", "tt_clip_timeout": "Seconds before clipboard is cleared after copying",
        "rgb_label": "🌈 RGB border", "rgb_on": "ON", "rgb_off": "OFF",
    },
    "UA": {
        "win_title": "Secure Pass Pro v4.0", "menu_title": "Меню", "len": "Довжина",
        "author": "Автор: Максим Мельніков", "upper": "Великі літери", "lower": "Малі літери",
        "digits": "Цифри", "symb": "Спецсимволи", "ambig": "Виключити схожі (i, l, 1...)",
        "unambig": "Виключити не однозначні", "at_least": "Мінімум 1 з категорії",
        "hide": "Приховати символи", "btn_gen": "Згенерувати", "btn_copy": "Копіювати пароль",
        "btn_save": "Зберегти у файл", "btn_open": "Відкрити файл", "btn_qr": "QR-код пароль",
        "btn_hist": "Історія", "btn_upd": "Оновити програму", "btn_about": "Про програму",
        "btn_settings": "Налаштування", "radius": "Закруглення кутів", "sound_on": "Звук: ВКЛ",
        "sound_off": "Звук: ВИКЛ", "theme_sys": "Системна", "theme_dark": "Темна",
        "theme_light": "Світла", "about_text": "Secure Pass Pro v4.0\n\nПрофесійний інструмент для генерації паролів.\nВикористовує криптографічно стійкі алгоритми.",
        "copied": "Скопійовано! ({0}с)", "strength": "Стійкість: ~{0} варіантів",
        "crack_time": "{0}", "time_sec": "Кілька секунд на злам", "time_day": "Дні на злам",
        "time_year": "Роки на злам", "time_cent": "Століття на злам", "st_low": "Слабкий пароль",
        "st_mid": "Середній пароль", "st_high": "Надійний пароль", "tt_gen": "Створити новий випадковий пароль",
        "tt_copy": "Копіювати в буфер (очищення через {0} сек)", "tt_save": "Зберегти поточний пароль у файл",
        "tt_open": "Відкрити пароль з файлу .key, .log або .txt", "tt_qr": "Створити QR-код для швидкого сканування",
        "tt_hist": "Показати останні 50 паролів", "tt_upd": "Перевірити наявність нової версії на GitHub",
        "tt_about": "Інформація про розробника та програму", "tt_settings": "Мова, звук та тема оформлення",
        "settings_title": "Налаштування", "settings_lang": "Мова інтерфейсу", "settings_sound": "Звук програми",
        "settings_theme": "Тема оформлення", "settings_radius": "Закруглення кутів", "close": "Закрити",
        "ok": "OK", "cancel": "Відміна", "yes": "Так", "no": "Ні", "master_status_set": "Встановлено",
        "master_status_not_set": "Не встановлено", "err_cat": "Виберіть хоча б одну категорію!",
        "err_pool_small": "Занадто мало доступних символів після виключень!",
        "err_save": "Помилка збереження: {0}", "err_open": "Не вдалося прочитати файл: {0}",
        "err_unsupported": "Непідтримуваний тип файлу: {0}", "err_integrity": "Критична помилка: Файл пошкоджений після запису!",
        "hist_empty": "Історія порожня...", "btn_clear_hist": "Очистити історію", "pdf_date": "Дата",
        "pdf_pass": "Пароль", "wiki_link": "Читати Security Logic Wiki", "err_title": "Помилка",
        "no_repeat": "Уникати повторів символів поспіль", "tt_no_repeat": "Не допускати однакових символів підряд (aaa, 111)",
        "err_no_repeat": "Не вдалося створити пароль без повторів. Зменшіть довжину або додайте категорії.",
        "err_no_repeat_fallback": "\nВикористано пароль з повторами.", "master_title": "Майстер-пароль",
        "master_prompt": "Введіть майстер-пароль для доступу до програми:",
        "master_set_title": "Встановити майстер-пароль", "master_set_prompt": "Придумайте майстер-пароль (залиште порожнім — без захисту):",
        "master_confirm": "Підтвердіть майстер-пароль:", "master_mismatch": "Паролі не збігаються!",
        "master_wrong": "Невірний майстер-пароль! Спроба {0} з {1}.", "master_blocked": "Перевищено кількість спроб. Програму закрито.",
        "master_set_ok": "Майстер-пароль встановлено.", "master_removed": "Майстер-пароль видалено.",
        "master_btn_set": "Встановити майстер-пароль", "master_btn_remove": "Видалити майстер-пароль",
        "master_current": "Статус:", "master_remove_confirm": "Ви впевнені, що хочете видалити майстер-пароль?\n\nПісля видалення доступ до програми не буде захищено.",
        "integrity_warn": "⚠ Увага: контрольна сума не знайдена для файлу.\nФайл міг бути змінений стороннім ПЗ.\nПродовжити відкриття?",
        "integrity_fail": "🚨 КРИТИЧНА ПОМИЛКА: Файл пошкоджений або підмінений!\nКонтрольна сума не збігається. Відкриття скасовано.",
        "integrity_ok": "✅ Цілісність файлу підтверджена.", "tt_eye": "Показати / приховати пароль",
        "clip_timeout": "Очищення буфера: {0} сек", "tt_clip_timeout": "Через скільки секунд буфер обміну буде очищено після копіювання",
        "rgb_label": "🌈 RGB-підсвітка", "rgb_on": "УВІ", "rgb_off": "ВИМК",
    }
}


# ==================== MAIN APPLICATION ====================
class SecurePassPro(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        
        # Application state
        self.current_lang = "RU"
        self.current_theme = "System"
        self.current_radius = 10
        self.clipboard_timeout = 60
        self._clipboard_timer: Optional[str] = None
        self._rgb_anim_id: Optional[str] = None
        self._pulse_animation_id: Optional[str] = None
        
        # Set global radius for dialogs
        set_global_radius(self.current_radius)
        
        # UI state - ВСЕ ГАЛОЧКИ СБРОШЕНЫ
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
        self.rgb_enabled = tk.BooleanVar(value=False)
        
        # History storage
        self.history: deque = deque(maxlen=HISTORY_MAX)
        self._rgb_t = 0.0
        
        # Window references
        self.settings_window: Optional[ctk.CTkToplevel] = None
        self.about_window: Optional[ctk.CTkToplevel] = None
        self.history_window: Optional[ctk.CTkToplevel] = None
        self.qr_window: Optional[ctk.CTkToplevel] = None
        
        # Widget references
        self._tooltips: Dict[str, ToolTip] = {}
        self.lang_buttons: Dict[str, ctk.CTkButton] = {}
        self.theme_buttons: Dict[str, ctk.CTkButton] = {}
        self.settings_labels: Dict[str, Any] = {}
        self.history_textbox: Optional[ctk.CTkTextbox] = None
        self.settings_radius_label: Optional[ctk.CTkLabel] = None
        self._master_set_btn: Optional[ctk.CTkButton] = None
        self._master_status_label: Optional[ctk.CTkLabel] = None
        self._sound_btn: Optional[ctk.CTkButton] = None
        self._close_btn: Optional[ctk.CTkButton] = None
        self._clip_timeout_label_ref: Optional[ctk.CTkLabel] = None
        self._rgb_on_btn_ref: Optional[ctk.CTkButton] = None
        self._rgb_off_btn_ref: Optional[ctk.CTkButton] = None
        
        # RGB canvases
        self._rgb_c_top: Optional[tk.Canvas] = None
        self._rgb_c_bottom: Optional[tk.Canvas] = None
        self._rgb_c_left: Optional[tk.Canvas] = None
        self._rgb_c_right: Optional[tk.Canvas] = None
        
        # Icons and resources
        self._icon_image: Optional[tk.PhotoImage] = None
        self._pdf_font_path = _get_resource_path("DejaVuSans.ttf")
        
        # Setup
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        
        self.title("Secure Pass Pro v4.0")
        self.resizable(False, False)
        self._set_window_icon(self)
        
        self._create_rgb_canvases()
        self._setup_ui()
        self._apply_lang("RU")
        self._center_main_window()
        self._apply_window_rounding(self)
        
        self.bind('<F5>', lambda e: self._generate())
        self.bind('<Control-c>', lambda e: self._copy() if self.focus_get() is not self.entry_res else None)
        self.bind('<Control-s>', lambda e: self._save())
        self.bind('<Control-o>', lambda e: self._open())
        self.bind('<Escape>', lambda e: self._close_settings() if self.settings_window else None)
        
        self.after(50, self._load_all_settings)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_rgb_canvases(self) -> None:
        bw = 3
        self._rgb_c_top = tk.Canvas(self, height=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_bottom = tk.Canvas(self, height=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_left = tk.Canvas(self, width=bw, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_right = tk.Canvas(self, width=bw, bg="#1d1e1e", highlightthickness=0)
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            c.place_forget()
    
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
        # Close all child windows gracefully before exit
        for win_attr in ("settings_window", "about_window", "history_window", "qr_window"):
            win = getattr(self, win_attr, None)
            if win is not None:
                try:
                    win.grab_release()
                except Exception:
                    pass
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
        if _IS_WINDOWS:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "light" if value == 1 else "dark"
            except Exception:
                pass
        return "dark"
    
    def _save_config(self, updates: Dict[str, Any]) -> None:
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            existing: Dict[str, Any] = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    existing = {}  # reset corrupted config
            existing.update(updates)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
        except Exception:
            pass
    
    def _load_all_settings(self) -> None:
        try:
            if not os.path.exists(CONFIG_FILE):
                return
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                try:
                    config = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    return  # corrupted config – skip silently
            
            if "THEME" in config and config["THEME"] in ("System", "Light", "Dark"):
                self.current_theme = config["THEME"]
                actual_theme = self._get_actual_theme()
                ctk.set_appearance_mode(self.current_theme)
                CTkMessageBox.set_theme(actual_theme)
                self._apply_theme_colors(actual_theme)
            
            if "LANG" in config and config["LANG"] in ("RU", "EN", "UA"):
                self._apply_lang(config["LANG"])
                CTkMessageBox.set_lang(config["LANG"])
            
            if "SOUND" in config:
                self.sound_enabled.set(config["SOUND"])
            
            if "CLIP_TIMEOUT" in config:
                t = config["CLIP_TIMEOUT"]
                if 10 <= t <= 120:
                    self.clipboard_timeout = t
            
            if "RGB" in config and config["RGB"]:
                self.rgb_enabled.set(True)
                self.after(200, self._start_rgb)
            
            if "RADIUS" in config:
                r = config["RADIUS"]
                if 0 <= r <= 25:
                    self.current_radius = r
                    set_global_radius(r)
                    self._change_radius(r)
        except Exception:
            pass
    
    def _setup_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        
        # Left panel
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))
        
        self.lbl_title = ctk.CTkLabel(self.left_panel, text="Secure Pass Pro v4.0", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(5, 0))
        self.lbl_author = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 10))
        
        # Length slider
        self.lbl_len = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 16, "bold"))
        self.lbl_len.pack()
        self.slider_len = ctk.CTkSlider(self.left_panel, from_=4, to=64, number_of_steps=60, width=400, command=self._update_len_label)
        self.slider_len.set(20)
        self.slider_len.pack(pady=5)
        
        # Checkboxes
        self.cb_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.cb_frame.pack(pady=10)
        
        self.cb_upper = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.upper_var)
        self.cb_upper.grid(row=0, column=1, padx=(70, 20), pady=6, sticky="w")
        self.cb_lower = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.lower_var)
        self.cb_lower.grid(row=0, column=0, padx=(20, 70), pady=6, sticky="w")
        self.cb_digits = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.digits_var)
        self.cb_digits.grid(row=1, column=1, padx=(70, 20), pady=6, sticky="w")
        self.cb_symb = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.symb_var)
        self.cb_symb.grid(row=1, column=0, padx=(20, 70), pady=6, sticky="w")
        self.cb_ambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.ambig_var)
        self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        self.cb_unambig = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.unambig_var)
        self.cb_unambig.grid(row=3, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        self.cb_at_least = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.at_least_var)
        self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        self.cb_hide = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.hide_var, command=self._toggle_hide)
        self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        self.cb_no_repeat = ctk.CTkCheckBox(self.cb_frame, text="", variable=self.no_repeat_var)
        self.cb_no_repeat.grid(row=6, column=0, columnspan=2, padx=20, pady=8, sticky="w")
        
        # Password entry
        self.entry_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.entry_frame.pack(pady=15, padx=40, fill="x")
        self.entry_res = ctk.CTkEntry(self.entry_frame, height=50, font=("Consolas", 22), justify="center", corner_radius=self.current_radius)
        self.entry_res.pack(side="left", fill="x", expand=True)
        
        self.btn_eye = ctk.CTkButton(self.entry_frame, text="👁", width=50, height=50, 
                                      font=("Segoe UI", 20), fg_color="#3a3a3a", hover_color="#555555",
                                      corner_radius=self.current_radius, command=self._toggle_eye)
        self.btn_eye.pack(side="left", padx=(6, 0))
        self._tooltips["btn_eye"] = ToolTip(self.btn_eye)
        
        # Strength meter
        self.lbl_stars_top = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 24))
        self.lbl_stars_top.pack(pady=(5, 0))
        self.lbl_strength_text = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_strength_text.pack()
        self.lbl_strength = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13))
        self.lbl_strength.pack()
        self.lbl_crack = ctk.CTkLabel(self.left_panel, text="", font=("Segoe UI", 13, "bold"), wraplength=500)
        self.lbl_crack.pack(pady=(0, 5))
        
        # Right panel (menu)
        self.right_panel = ctk.CTkFrame(self, width=250)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        self.right_panel.grid_propagate(False)
        
        self.lbl_menu = ctk.CTkLabel(self.right_panel, text="", font=("Segoe UI", 18, "bold"))
        self.lbl_menu.pack(pady=15)
        
        # Menu buttons
        self.btn_gen = self._create_menu_btn(self.right_panel, "btn_gen", "tt_gen", self._generate, "#0067c0")
        self.btn_copy = self._create_menu_btn(self.right_panel, "btn_copy", "tt_copy", self._copy, "#107c10")
        self.btn_save = self._create_menu_btn(self.right_panel, "btn_save", "tt_save", self._save, "#0078d4")
        self.btn_open = self._create_menu_btn(self.right_panel, "btn_open", "tt_open", self._open, "#0078d4")
        self.btn_qr = self._create_menu_btn(self.right_panel, "btn_qr", "tt_qr", self._show_qr, "#8764b8")
        self.btn_hist = self._create_menu_btn(self.right_panel, "btn_hist", "tt_hist", self._show_history, "#4b4b4b")
        self.btn_upd = self._create_menu_btn(self.right_panel, "btn_upd", "tt_upd", lambda: webbrowser.open(UPD_URL), "#ca5010")
        self.btn_settings = self._create_menu_btn(self.right_panel, "btn_settings", "tt_settings", self._show_settings, "#2d6a4f")
        self.btn_about = self._create_menu_btn(self.right_panel, "btn_about", "tt_about", self._show_about, "#4b4b4b")
        
        # Bottom frame
        self.bottom_frame = ctk.CTkFrame(self, fg_color=("#e0e0e0", "#1d1e1e"), corner_radius=15)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))
        self.lbl_app_rating = ctk.CTkLabel(self.bottom_frame, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_app_rating.pack(pady=(5, 5))
    
    def _create_menu_btn(self, parent, lang_key: str, tt_key: str, cmd, color: str) -> ctk.CTkButton:
        colors_map = {
            "#0067c0": "#00A2FF", "#107c10": "#20CF20", "#0078d4": "#309FFF",
            "#8764b8": "#B080FF", "#4b4b4b": "#808080", "#ca5010": "#FF8C00", "#2d6a4f": "#40916c"
        }
        neon_color = colors_map.get(color, color)
        btn = ctk.CTkButton(parent, text="", command=lambda: self._run_menu_command(cmd),
                            fg_color=color, height=45, border_width=2, border_color=neon_color,
                            font=("Segoe UI", 13, "bold"), hover_color=neon_color,
                            corner_radius=self.current_radius)
        btn.pack(pady=6, padx=15, fill="x")
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        self._tooltips[lang_key] = ToolTip(btn)
        return btn
    
    def _run_menu_command(self, command) -> None:
        self._play_sound("click")
        command()
    
    def _apply_theme_colors(self, actual_theme: str) -> None:
        if actual_theme == "light":
            bg_main, fg_main, entry_bg = "#F3F3F3", "#000000", "#FFFFFF"
            panel_bg, border_color, checkmark_color = "#F3F3F3", "#d0d0d0", "#1f538d"
        else:
            bg_main, fg_main, entry_bg = "#1d1e1e", "#FFFFFF", "#2b2b2b"
            panel_bg, border_color, checkmark_color = "#1d1e1e", "#3a3a3a", "#4EC9B0"
        
        self.left_panel.configure(fg_color=panel_bg)
        self.right_panel.configure(fg_color=panel_bg, border_color=border_color)
        self.entry_res.configure(fg_color=entry_bg, text_color=fg_main)
        
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
                   self.cb_ambig, self.cb_unambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            cb.configure(fg_color=panel_bg, text_color=fg_main, checkmark_color=checkmark_color)
        
        self.lbl_title.configure(text_color=fg_main)
        self.lbl_author.configure(text_color=fg_main)
        self.lbl_len.configure(text_color=fg_main)
        self.lbl_strength.configure(text_color=fg_main)
        self.lbl_strength_text.configure(text_color=fg_main)
        self.lbl_crack.configure(text_color=fg_main)
        self.lbl_menu.configure(text_color=fg_main)
        
        new_bg = "#F3F3F3" if actual_theme == "light" else "#1d1e1e"
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            if c:
                c.configure(bg=new_bg)
    
    def _change_radius(self, val: int) -> None:
        rad = int(val)
        self.current_radius = rad
        set_global_radius(rad)
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr,
                     self.btn_hist, self.btn_upd, self.btn_settings, self.btn_about]
        for btn in menu_btns:
            btn.configure(corner_radius=rad)
        
        self.btn_eye.configure(corner_radius=rad)
        
        cb_rad = max(rad // 2, 0)
        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
                   self.cb_ambig, self.cb_unambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            cb.configure(corner_radius=cb_rad)
        
        self.bottom_frame.configure(corner_radius=rad)
        self.right_panel.configure(corner_radius=rad)
        self.entry_res.configure(corner_radius=rad)
        self.entry_frame.configure(corner_radius=rad)
        
        if self.settings_radius_label and self.settings_radius_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self.settings_radius_label.configure(text=f"{L['settings_radius']}: {rad}")
        
        self._update_settings_radius()
        self._save_config({"RADIUS": rad})
    
    def _update_settings_radius(self) -> None:
        rad = self.current_radius
        for btn in self.lang_buttons.values():
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
        for btn in self.theme_buttons.values():
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
        for btn in [self._sound_btn, self._close_btn, self._master_set_btn,
                    self._rgb_on_btn_ref, self._rgb_off_btn_ref]:
            if btn and btn.winfo_exists():
                btn.configure(corner_radius=rad)
    
    def _apply_window_rounding(self, window) -> None:
        if not _IS_WINDOWS:
            return
        try:
            window.update()
            HWND = ctypes.windll.user32.GetParent(window.winfo_id())
            DWMWA_WINDOW_CORNER_PREFERENCE = 33
            DWMWCP_ROUND = 2
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                HWND, DWMWA_WINDOW_CORNER_PREFERENCE,
                ctypes.byref(ctypes.c_int(DWMWCP_ROUND)),
                ctypes.sizeof(ctypes.c_int(DWMWCP_ROUND))
            )
        except Exception:
            pass
    
    def _set_window_icon(self, window) -> None:
        icon_path = _get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            try:
                if _IS_WINDOWS:
                    window.iconbitmap(icon_path)
                else:
                    if self._icon_image is None:
                        self._icon_image = tk.PhotoImage(file=icon_path)
                    window.iconphoto(True, self._icon_image)
            except Exception:
                pass
    
    def _center_main_window(self) -> None:
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (850 // 2)
        y = (self.winfo_screenheight() // 2) - (780 // 2)
        self.geometry(f"850x780+{x}+{y}")
    
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
        
        menu_btns = [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr,
                     self.btn_hist, self.btn_upd, self.btn_settings, self.btn_about]
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
    
    def _change_language(self, lang: str) -> None:
        self.current_lang = lang
        self._apply_lang(lang)
        self._save_config({"LANG": lang})
        CTkMessageBox.set_lang(lang)
        
        for l, btn in self.lang_buttons.items():
            if btn and btn.winfo_exists():
                btn.configure(fg_color="#2d6a4f" if l == lang else "#4b4b4b", corner_radius=self.current_radius)
        
        if self.settings_window and self.settings_window.winfo_exists():
            self._close_settings()   # releases grab before destroy
        
        if self.entry_res.get():
            self._update_strength_meter(self.entry_res.get())
        self._update_master_status_label()
    
    def _change_theme(self, mode: str) -> None:
        self.current_theme = mode
        self._save_config({"THEME": mode})
        
        actual_theme = self._get_actual_theme()
        CTkMessageBox.set_theme(actual_theme)
        self._apply_theme_colors(actual_theme)
        
        for name, btn in self.theme_buttons.items():
            if btn and btn.winfo_exists():
                btn.configure(fg_color="#2d6a4f" if name == mode else "#4b4b4b", corner_radius=self.current_radius)
        
        if self.settings_window and self.settings_window.winfo_exists():
            self._close_settings()
        
        def apply_theme():
            try:
                ctk.set_appearance_mode(mode)
                self.update_idletasks()
            except Exception:
                pass
        self.after(50, apply_theme)
    
    # ==================== RGB ANIMATION ====================
    
    def _rgb_color(self, phase_offset: float) -> str:
        f = self._rgb_t + phase_offset
        r = int((math.sin(f) + 1) / 2 * 255)
        g = int((math.sin(f + 2.1) + 1) / 2 * 255)
        b = int((math.sin(f + 4.2) + 1) / 2 * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _set_titlebar_color(self, hex_color: str) -> None:
        if not _IS_WINDOWS:
            return
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            colorref = r | (g << 8) | (b << 16)
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_CAPTION_COLOR = 35
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(colorref)),
                ctypes.sizeof(ctypes.c_int(colorref))
            )
        except Exception:
            pass
    
    def _reset_titlebar_color(self) -> None:
        if not _IS_WINDOWS:
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            DWMWA_CAPTION_COLOR = 35
            DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_CAPTION_COLOR,
                ctypes.byref(ctypes.c_int(DWMWA_COLOR_DEFAULT)),
                ctypes.sizeof(ctypes.c_int(DWMWA_COLOR_DEFAULT))
            )
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
        self._save_config({"RGB": state})
    
    def _update_rgb_buttons(self) -> None:
        is_on = self.rgb_enabled.get()
        for ref, active in (('_rgb_on_btn_ref', is_on), ('_rgb_off_btn_ref', not is_on)):
            btn = getattr(self, ref, None)
            if btn and btn.winfo_exists():
                btn.configure(fg_color="#7b2d8b" if active else "#4b4b4b", corner_radius=self.current_radius)
    
    # ==================== PASSWORD GENERATION ====================
    
    def _update_len_label(self, val: float) -> None:
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")
    
    def _get_min_length(self) -> int:
        count = sum([self.upper_var.get(), self.lower_var.get(), self.digits_var.get(), self.symb_var.get()])
        return max(4, count)
    
    def _fix_no_repeats(self, chars: List[str], pool: str) -> Optional[str]:
        result = list(chars)
        unique_pool = list(set(pool))
        max_attempts = 500
        
        def _secure_shuffle(lst: list) -> None:
            for i in range(len(lst) - 1, 0, -1):
                j = secrets.randbelow(i + 1)
                lst[i], lst[j] = lst[j], lst[i]

        for _ in range(max_attempts):
            _secure_shuffle(result)
            has_repeat = any(result[i] == result[i + 1] for i in range(len(result) - 1))
            if not has_repeat:
                return "".join(result)
        
        result = list(chars)
        _secure_shuffle(result)
        for attempt in range(max_attempts):
            fixed = False
            for i in range(len(result) - 1):
                if result[i] == result[i + 1]:
                    candidates = [c for c in unique_pool if c != result[i] and (i == 0 or c != result[i - 1])]
                    if candidates:
                        result[i + 1] = secrets.choice(candidates)
                        fixed = True
            if not fixed:
                break
            if not any(result[i] == result[i + 1] for i in range(len(result) - 1)):
                return "".join(result)
        return None
    
    def _generate(self) -> None:
        L = LANGUAGES[self.current_lang]
        
        exclude = set(AMBIGUOUS_CHARS if self.ambig_var.get() else "")
        if self.unambig_var.get():
            exclude.update(set(UNAMBIG_CHARS))
        
        def get_chars(src: str, var: tk.BooleanVar) -> str:
            if not var.get():
                return ""
            return "".join(c for c in src if c not in exclude)
        
        p_upper = get_chars(string.ascii_uppercase, self.upper_var)
        p_lower = get_chars(string.ascii_lowercase, self.lower_var)
        p_digits = get_chars(string.digits, self.digits_var)
        p_symb = get_chars(string.punctuation, self.symb_var)
        
        full_pool = p_upper + p_lower + p_digits + p_symb
        
        if not full_pool:
            self._play_sound("error")
            CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_cat"])
            return
        
        if len(set(full_pool)) < 2:
            self._play_sound("error")
            CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_pool_small"])
            return
        
        self._play_sound("success")
        
        min_len = self._get_min_length()
        length = max(int(self.slider_len.get()), min_len)
        if length != int(self.slider_len.get()):
            self.slider_len.set(length)
            self._update_len_label(length)
        
        result: List[str] = []
        
        if self.at_least_var.get():
            for p in [p_upper, p_lower, p_digits, p_symb]:
                if p:
                    result.append(secrets.choice(p))
        
        if len(result) > length:
            random.shuffle(result)
            result = result[:length]
        else:
            while len(result) < length:
                result.append(secrets.choice(full_pool))
        
        # Cryptographically secure shuffle (Fisher-Yates with secrets)
        for i in range(len(result) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            result[i], result[j] = result[j], result[i]
        pwd = "".join(result)
        
        if self.no_repeat_var.get():
            fixed_pwd = self._fix_no_repeats(result, full_pool)
            if fixed_pwd is None:
                CTkMessageBox.warning(self, L.get("err_title", "Error"), L["err_no_repeat"] + L.get("err_no_repeat_fallback", ""))
            else:
                pwd = fixed_pwd
        
        self.entry_res.delete(0, "end")
        self.entry_res.insert(0, pwd)
        
        self._update_strength_meter(pwd)
        
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S]")
        if len(pwd) > 4:
            masked = pwd[:2] + "••••" + pwd[-2:]
        else:
            masked = "••••"
        self.history.append(f"{timestamp} {masked}")
    
    def _update_strength_meter(self, password: str) -> None:
        if not password:
            self.lbl_strength_text.configure(text="")
            self.lbl_strength.configure(text="")
            self.lbl_crack.configure(text="")
            self.lbl_stars_top.configure(text="")
            return
        
        L = LANGUAGES[self.current_lang]
        
        pool_size = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in string.punctuation for c in password):
            pool_size += 32
        
        entropy_bits = len(password) * math.log2(pool_size) if pool_size > 0 else 0
        combinations = f"{pool_size ** len(password):.1e}" if pool_size > 0 else "0"
        
        self.lbl_strength.configure(text=L["strength"].format(combinations))
        
        if entropy_bits < 40:
            stars_display, stars_color, st_text, crack_phrase, strength_type = "★☆☆☆☆", "#FF4C4C", L["st_low"], L["time_sec"], "weak"
        elif entropy_bits < 60:
            stars_display, stars_color, st_text, crack_phrase, strength_type = "★★★☆☆", "#FFA500", L["st_mid"], L["time_day"], "medium"
        elif entropy_bits < 80:
            stars_display, stars_color, st_text, crack_phrase, strength_type = "★★★★☆", "#FFD700", L["st_mid"], L["time_year"], "medium"
        else:
            stars_display, stars_color, st_text, crack_phrase, strength_type = "★★★★★", "#2ECC71", L["st_high"], L["time_cent"], "strong"
        
        self.lbl_stars_top.configure(text=stars_display, text_color=stars_color)
        self.lbl_strength_text.configure(text=st_text, text_color=stars_color)
        self.lbl_crack.configure(text=L["crack_time"].format(crack_phrase), text_color=stars_color)
        
        self._animate_password_field(strength_type)
    
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
    
    # ==================== CLIPBOARD OPERATIONS ====================
    
    def _copy(self) -> None:
        pwd = self.entry_res.get().strip()
        if not pwd:
            return
        L = LANGUAGES[self.current_lang]
        self._play_sound("copy")

        self.clipboard_clear()
        self.clipboard_append(pwd)

        if self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except Exception:
                pass

        self._clipboard_timer = self.after(
            self.clipboard_timeout * 1000,
            lambda value=pwd: self._clear_clipboard_if_unchanged(value)
        )

        old_text = self.btn_copy.cget("text")
        self.btn_copy.configure(text=L["copied"].format(self.clipboard_timeout))
        self.after(2000, lambda: self.btn_copy.configure(text=old_text))

    def _clear_clipboard_if_unchanged(self, expected: str) -> None:
        try:
            if self.clipboard_get() == expected:
                self.clipboard_clear()
        except Exception:
            pass
        finally:
            self._clipboard_timer = None
    
    def _on_clip_timeout_change(self, val: float) -> None:
        seconds = int(val)
        self.clipboard_timeout = seconds
        if self._clip_timeout_label_ref and self._clip_timeout_label_ref.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self._clip_timeout_label_ref.configure(text=L["clip_timeout"].format(seconds))
        
        if "btn_copy" in self._tooltips:
            L = LANGUAGES[self.current_lang]
            self._tooltips["btn_copy"].set_text(L["tt_copy"].format(seconds))
        
        self._save_config({"CLIP_TIMEOUT": seconds})
    
    # ==================== FILE OPERATIONS ====================
    
    def _verify_pdf(self, path: str) -> bool:
        try:
            with open(path, "rb") as f:
                header = f.read(5)
                return header == b"%PDF-"
        except Exception:
            return False
    
    def _verify_text_file(self, path: str, expected_bytes: bytes) -> bool:
        expected_hash = hashlib.sha256(expected_bytes).hexdigest()
        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest() == expected_hash
        except Exception:
            return False
    
    def _save(self) -> None:
        """Save password to file – one file, no extra sidecar files."""
        L = LANGUAGES[self.current_lang]
        pwd = self.entry_res.get().strip()
        if not pwd:
            return
        
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Password Files", "*.key"),
                ("Log Files", "*.log"),
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*")
            ]
        )
        
        if not path:
            return
        
        try:
            ext = os.path.splitext(path)[1].lower()
            
            # PDF files
            if ext == ".pdf":
                pdf = UTF8PDF()
                pdf.set_author("Maxim Melnikov")
                pdf.set_creator("Secure Pass Pro v4.0")
                pdf.set_title("Secure Pass Pro Password")
                pdf.add_page()
                
                dejavu_loaded = False
                _tmpdir = None
                if os.path.exists(self._pdf_font_path):
                    try:
                        # Copy font to a temp dir so fpdf caches (.pkl) are
                        # created there and NOT in the application folder
                        _tmpdir = tempfile.mkdtemp()
                        _tmp_font = os.path.join(_tmpdir, 'DejaVuSans.ttf')
                        shutil.copy2(self._pdf_font_path, _tmp_font)
                        pdf.add_font('DejaVu', '', _tmp_font, uni=True)
                        dejavu_loaded = True
                    except Exception:
                        pass
                
                def _latin1(text: str) -> str:
                    """Encode text to latin-1 safely, replacing unsupported chars."""
                    return text.encode('latin-1', errors='replace').decode('latin-1')

                if dejavu_loaded:
                    pdf.set_font('DejaVu', '', 16)
                    lbl_title  = "Secure Pass Pro v4.0"
                    lbl_date   = f"{L['pdf_date']}: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    lbl_pass   = f"{L['pdf_pass']}: {pwd}"
                else:
                    # DejaVu unavailable — fall back to Arial (latin-1 only)
                    # Use English labels and sanitize all text including password
                    pdf.set_font('Arial', 'B', 16)
                    lbl_title  = "Secure Pass Pro v4.0"
                    lbl_date   = _latin1(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    lbl_pass   = _latin1(f"Password: {pwd}")

                pdf.cell(200, 10, txt=lbl_title, ln=True, align='C')

                if dejavu_loaded:
                    pdf.set_font('DejaVu', '', 12)
                else:
                    pdf.set_font('Arial', '', 12)

                pdf.ln(10)
                pdf.cell(200, 10, txt=lbl_date, ln=True)
                pdf.cell(200, 10, txt=lbl_pass, ln=True)
                
                try:
                    pdf.output(path)
                finally:
                    # Always clean up temp font dir (removes .pkl cache files)
                    if _tmpdir and os.path.exists(_tmpdir):
                        shutil.rmtree(_tmpdir, ignore_errors=True)
                if not self._verify_pdf(path):
                    raise IOError(L["err_integrity"])
            else:
                # Save password to text file
                pwd_bytes = pwd.encode("utf-8")
                with open(path, "wb") as f:
                    f.write(pwd_bytes)
                
                # Verify integrity (in-memory only, no separate .sha256 file)
                if not self._verify_text_file(path, pwd_bytes):
                    raise IOError(L["err_integrity"])
            
            self._play_sound("success")
            fname = os.path.basename(path)
            self.title(f"✅ {fname}")
            self.after(3000, lambda: self.title(L["win_title"]))
        except Exception as e:
            CTkMessageBox.error(self, L.get("err_title", "Error"), L["err_save"].format(e))
    
    def _open(self) -> None:
        """Open password from file - opens ALL file types"""
        L = LANGUAGES[self.current_lang]
        
        path = filedialog.askopenfilename(
            title="Select password file",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Files", "*.txt"),
                ("Password Files", "*.key"),
                ("Log Files", "*.log"),
                ("PDF Files", "*.pdf")
            ]
        )
        
        if not path:
            return
        
        try:
            ext = os.path.splitext(path)[1].lower()

            # Guard: refuse to open a .sha256 sidecar as a password
            if path.lower().endswith(HASH_EXTENSION):
                CTkMessageBox.error(self, L.get("err_title", "Error"),
                                    L["err_unsupported"].format(HASH_EXTENSION))
                return

            # PDF files - open with external viewer (no shell=True to avoid injection)
            if ext == ".pdf":
                if _IS_WINDOWS:
                    os.startfile(path)
                elif _IS_MACOS:
                    subprocess.run(["open", path], check=False)
                else:
                    subprocess.run(["xdg-open", path], check=False)
                self._play_sound("success")
                return
            
            # Text files - read content
            content = None

            # Refuse oversized files (10 KB limit – passwords don't need more)
            try:
                file_size = os.path.getsize(path)
                if file_size > 10_240:
                    CTkMessageBox.error(self, L.get("err_title", "Error"),
                                        L["err_open"].format("File too large (max 10 KB)"))
                    return
            except OSError:
                pass

            # Try different encodings
            encodings = ['utf-8', 'cp1251', 'latin-1', 'cp866', 'koi8-r', 'utf-16', 'utf-32']
            
            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read().strip()
                    break
                except (UnicodeDecodeError, UnicodeError, UnicodeEncodeError):
                    continue
            
            # Fallback: read as binary
            if content is None:
                try:
                    with open(path, 'rb') as f:
                        raw_bytes = f.read()
                        content = raw_bytes.decode('utf-8', errors='replace').strip()
                except Exception:
                    content = None
            
            if not content:
                raise ValueError("File is empty or contains no readable text")
            
            # SHA-256 integrity check (if .sha256 file exists)
            hash_path = path + HASH_EXTENSION
            if os.path.exists(hash_path):
                try:
                    with open(hash_path, 'r', encoding='utf-8') as hf:
                        stored_hash = hf.read().strip()
                    with open(path, 'rb') as f:
                        raw_bytes = f.read()
                    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
                    if actual_hash != stored_hash:
                        self._play_sound("error")
                        CTkMessageBox.error(self, L.get("err_title", "Error"), L["integrity_fail"])
                        return
                    self.title(L["integrity_ok"])
                    self.after(3000, lambda: self.title(L["win_title"]))
                except Exception:
                    pass
            # No .sha256 file — open silently without warning

            # Insert content into password field
            self.entry_res.delete(0, "end")
            self.entry_res.insert(0, content)
            self._update_strength_meter(content)
            self._play_sound("success")
            
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
    
    def _show_history(self) -> None:
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()
            self.history_window.focus_force()
            return
        
        L = LANGUAGES[self.current_lang]
        
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
        
        txt = ctk.CTkTextbox(f, font=("Consolas", 14), corner_radius=self.current_radius)
        txt.pack(fill="both", expand=True, pady=10)
        
        if not self.history:
            txt.insert("1.0", L["hist_empty"])
        else:
            history_snapshot = list(reversed(self.history))
            txt.insert("1.0", "\n".join(history_snapshot))
        txt.configure(state="disabled")  # read-only
        
        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.pack(fill="x")
        ctk.CTkButton(btn_f, text=L["btn_clear_hist"], corner_radius=self.current_radius, fg_color="#d13438",
                     command=lambda: self._clear_history_textbox(txt)).pack(side="left", padx=5)
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
        self._apply_window_rounding(self.about_window)
        self.about_window.protocol("WM_DELETE_WINDOW", self._close_about)
        
        ctk.CTkLabel(self.about_window, text="Secure Pass Pro", font=("Segoe UI", 22, "bold")).pack(pady=(25, 5))
        ctk.CTkLabel(self.about_window, text="Version 4.0", font=("Segoe UI", 14)).pack(pady=(0, 15))
        ctk.CTkLabel(self.about_window, text=L["about_text"], wraplength=350, font=("Segoe UI", 13)).pack(pady=10)
        ctk.CTkButton(self.about_window, text="OK", width=120, command=self._close_about, corner_radius=self.current_radius).pack(pady=(20, 10))
        
        lbl_wiki = ctk.CTkLabel(self.about_window, text=L.get("wiki_link", "Security Logic Wiki"),
                               font=("Segoe UI", 12, "underline"), text_color="#1f538d", cursor="hand2")
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
        self._set_window_icon(self.settings_window)
        self.settings_window.transient(self)
        self.settings_window.grab_set()
        self._center_window_relative_to_parent(self.settings_window, 420, 640)
        self._apply_window_rounding(self.settings_window)
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
            btn = ctk.CTkButton(lang_frame, text=lang, width=80, height=35,
                               command=lambda l=lang: self._change_language(l),
                               fg_color="#2d6a4f" if self.current_lang == lang else "#4b4b4b",
                               font=("Segoe UI", 14, "bold"), corner_radius=self.current_radius)
            btn.pack(side="left", padx=5)
            self.lang_buttons[lang] = btn
        
        self._add_separator(main_frame)
        
        # Theme
        theme_label = ctk.CTkLabel(main_frame, text=L["settings_theme"], font=("Segoe UI", 16, "bold"))
        theme_label.pack(pady=(8, 8))
        theme_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        theme_frame.pack(pady=(0, 12))
        
        sys_btn = ctk.CTkButton(theme_frame, text=L["theme_sys"], width=100, height=35,
                               command=lambda: self._change_theme("System"),
                               fg_color="#2d6a4f" if self.current_theme == "System" else "#4b4b4b",
                               font=("Segoe UI", 12), corner_radius=self.current_radius)
        sys_btn.pack(side="left", padx=5)
        light_btn = ctk.CTkButton(theme_frame, text=L["theme_light"], width=100, height=35,
                                 command=lambda: self._change_theme("Light"),
                                 fg_color="#2d6a4f" if self.current_theme == "Light" else "#4b4b4b",
                                 font=("Segoe UI", 12), corner_radius=self.current_radius)
        light_btn.pack(side="left", padx=5)
        dark_btn = ctk.CTkButton(theme_frame, text=L["theme_dark"], width=100, height=35,
                                command=lambda: self._change_theme("Dark"),
                                fg_color="#2d6a4f" if self.current_theme == "Dark" else "#4b4b4b",
                                font=("Segoe UI", 12), corner_radius=self.current_radius)
        dark_btn.pack(side="left", padx=5)
        
        self.theme_buttons = {"System": sys_btn, "Light": light_btn, "Dark": dark_btn}
        
        self._add_separator(main_frame)
        
        # Radius
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
        self._sound_btn = ctk.CTkButton(main_frame, text=sound_text, width=150, height=40,
                                       command=self._toggle_sound_settings, fg_color="#0078d4",
                                       font=("Segoe UI", 14), corner_radius=self.current_radius)
        self._sound_btn.pack(pady=(0, 15))
        
        self._add_separator(main_frame)
        
        # Clipboard timeout
        clip_timeout_label = ctk.CTkLabel(main_frame, text=L["clip_timeout"].format(self.clipboard_timeout), font=("Segoe UI", 16, "bold"))
        clip_timeout_label.pack(pady=(8, 5))
        self._clip_timeout_label_ref = clip_timeout_label
        
        clip_slider = ctk.CTkSlider(main_frame, from_=10, to=120, number_of_steps=110, width=300, command=self._on_clip_timeout_change)
        clip_slider.set(self.clipboard_timeout)
        clip_slider.pack(pady=(0, 10))
        
        self._add_separator(main_frame)
        
        # Master Password
        master_label = ctk.CTkLabel(main_frame, text="🔐 " + L["master_title"], font=("Segoe UI", 16, "bold"))
        master_label.pack(pady=(8, 5))
        
        self._master_status_label = ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 13))
        self._master_status_label.pack(pady=(0, 5))
        self._update_master_status_label()
        
        master_btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        master_btn_frame.pack(pady=(0, 10))
        
        self._master_set_btn = ctk.CTkButton(master_btn_frame, text="", width=180, height=40,
                                            font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._master_set_btn.pack(side="left", padx=5)
        self._update_master_buttons()
        
        self._add_separator(main_frame)
        
        # RGB
        rgb_label = ctk.CTkLabel(main_frame, text=L["rgb_label"], font=("Segoe UI", 16, "bold"))
        rgb_label.pack(pady=(8, 6))
        
        rgb_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        rgb_frame.pack(pady=(0, 12))
        
        is_rgb_on = self.rgb_enabled.get()
        
        self._rgb_on_btn_ref = ctk.CTkButton(rgb_frame, text=L["rgb_on"], width=110, height=35,
                                            command=lambda: self._set_rgb(True),
                                            fg_color="#7b2d8b" if is_rgb_on else "#4b4b4b",
                                            font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._rgb_on_btn_ref.pack(side="left", padx=5)
        
        self._rgb_off_btn_ref = ctk.CTkButton(rgb_frame, text=L["rgb_off"], width=110, height=35,
                                             command=lambda: self._set_rgb(False),
                                             fg_color="#4b4b4b" if is_rgb_on else "#7b2d8b",
                                             font=("Segoe UI", 13), corner_radius=self.current_radius)
        self._rgb_off_btn_ref.pack(side="left", padx=5)
        
        self._add_separator(main_frame)
        
        # Close button
        self._close_btn = ctk.CTkButton(main_frame, text=L["close"], command=self._close_settings,
                                       fg_color="#ca5010", width=150, height=40,
                                       font=("Segoe UI", 14), corner_radius=self.current_radius)
        self._close_btn.pack(pady=(10, 10))
        
        self.settings_labels = {'lang': lang_label, 'theme': theme_label, 'sound': sound_label,
                                'close_btn': self._close_btn, 'sound_btn': self._sound_btn, 'radius_slider': radius_slider}
    
    def _add_separator(self, parent) -> None:
        sep = ctk.CTkFrame(parent, height=2, fg_color="gray")
        sep.pack(fill="x", pady=8)
    
    def _on_radius_change(self, val: float) -> None:
        rad = int(val)
        if self.settings_radius_label and self.settings_radius_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self.settings_radius_label.configure(text=f"{L['settings_radius']}: {rad}")
        self._change_radius(rad)
    
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
    
    def _toggle_sound_settings(self) -> None:
        self.sound_enabled.set(not self.sound_enabled.get())
        if self._sound_btn and self._sound_btn.winfo_exists():
            L = LANGUAGES[self.current_lang]
            self._sound_btn.configure(text=L["sound_on"] if self.sound_enabled.get() else L["sound_off"])
            self._sound_btn.configure(corner_radius=self.current_radius)
        self._play_sound("click")
        self._save_config({"SOUND": self.sound_enabled.get()})
    
    def _play_sound(self, sound_type: str = "click") -> None:
        if not self.sound_enabled.get():
            return
        try:
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_path, "Computer Mouse Click.mp3")
            if not os.path.exists(file_path):
                return
            if _IS_WINDOWS:
                winmm = ctypes.windll.winmm
                alias = "app_click"
                winmm.mciSendStringW(f'close {alias}', None, 0, 0)
                winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, 0)
                winmm.mciSendStringW(f'play {alias} from 0', None, 0, 0)
                self.after(1000, lambda: winmm.mciSendStringW(f'close {alias}', None, 0, 0))
            elif _IS_MACOS:
                if shutil.which("afplay"):
                    subprocess.Popen(["afplay", file_path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                if shutil.which("mpg123"):
                    subprocess.Popen(["mpg123", "-q", file_path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif shutil.which("ffplay"):
                    subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                # aplay removed: it supports WAV only, not MP3
        except Exception:
            pass
    
    def _toggle_hide(self) -> None:
        self._sync_eye_to_hide_var()
    
    def _toggle_eye(self) -> None:
        self.hide_var.set(not self.hide_var.get())
        self._sync_eye_to_hide_var()
    
    def _sync_eye_to_hide_var(self) -> None:
        hidden = self.hide_var.get()
        self.entry_res.configure(show="*" if hidden else "")
        self.btn_eye.configure(text="🙈" if hidden else "👁")
    
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
    
    # ==================== MASTER PASSWORD ====================
    
    def _update_master_status_label(self) -> None:
        if self._master_status_label and self._master_status_label.winfo_exists():
            L = LANGUAGES[self.current_lang]
            if MasterPassword.is_set():
                self._master_status_label.configure(text=f"{L['master_current']} 🔒 {L['master_status_set']}", text_color="#2ECC71")
            else:
                self._master_status_label.configure(text=f"{L['master_current']} 🔓 {L['master_status_not_set']}", text_color="#FFA500")
    
    def _update_master_buttons(self) -> None:
        if not self._master_set_btn or not self._master_set_btn.winfo_exists():
            return
        L = LANGUAGES[self.current_lang]
        if MasterPassword.is_set():
            self._master_set_btn.configure(text="🔒 " + L["master_btn_remove"], fg_color="#8b0000",
                                          command=self._remove_master_password, corner_radius=self.current_radius)
        else:
            self._master_set_btn.configure(text="🔓 " + L["master_btn_set"], fg_color="#2d6a4f",
                                          command=self._toggle_master_password, corner_radius=self.current_radius)
    
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


# ==================== APPLICATION ENTRY POINT ====================
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