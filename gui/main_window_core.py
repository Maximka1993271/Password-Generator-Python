"""
Main application window - CORE CLASS (skeleton)
Главное окно приложения - ОСНОВНОЙ КЛАСС (скелет)
Головне вікно програми - ОСНОВНИЙ КЛАС (скелет)

This file contains only the class definition and __init__ method.
All other methods are imported from mixin files.

Этот файл содержит только определение класса и метод __init__.
Все остальные методы импортируются из файлов миксинов.

Цей файл містить лише визначення класу та метод __init__.
Всі інші методи імпортуються з файлів міксинів.

FIXED: Added full type hints for all methods and attributes
"""

from __future__ import annotations
from collections import deque
import time
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, TypeVar, cast

import customtkinter as ctk

from core.generator import PasswordGenerator, StrengthCalculator
from security.master import MasterPassword
from security.panic import PanicCleanup
from storage.config import Config
from core.app_settings import AppSettings, settings as _app_settings
from gui.widgets import ToolTip
from utils.helpers import (
    set_global_radius, get_resource_path, is_linux,
    get_system_scaling, apply_linux_theme, set_window_icon, apply_window_rounding
)
from utils.paths import get_base_dir, get_config_dir, get_config_file
from utils.logger import get_logger
from utils.radius_manager import register_window

# Import for 2FA
# Импорт для 2FA
# Імпорт для 2FA
from security.totp import init_totp_from_config
from utils.qr_utils import QRUtils

logger = get_logger("main_window")

# Import mixin groups
# Импорт групп миксинов
# Імпорт груп міксинів
from gui.mixins import UIMixins, SecurityMixins, OpsMixins, VisualMixins

# Import all method modules (they will be mixed in)
# Импорт всех модулей методов (они будут примешаны)
# Імпорт всіх модулів методів (вони будуть домішані)
from gui.main_window_ui import UIMethods
from gui.main_window_events import EventMethods
from gui.main_window_helpers import HelperMethods
from gui.main_window_cleanup import CleanupMethods

# ==================== CONSTANTS ====================

HISTORY_MAX: int = 50
UPD_URL: str = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

BASE_DIR: str = get_base_dir()
CONFIG_DIR: str = get_config_dir()
CONFIG_FILE: str = get_config_file()


# ==================== IMPORTS FOR HELPER FUNCTIONS ====================
# Импорты для вспомогательных функций
# Імпорти для допоміжних функцій
try:
    import sqlite3
except ImportError:
    sqlite3 = None

try:
    from cryptography.exceptions import InvalidTag
except ImportError:
    InvalidTag = Exception


# ==================== HELPER FUNCTIONS ====================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ДОПОМІЖНІ ФУНКЦІЇ

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength for saving.

    Проверяет надёжность пароля для сохранения.
    Перевіряє надійність пароля для збереження.
    """
    if not password:
        return False, "Password is empty / Пароль пуст / Пароль порожній"

    if len(password) < 4:
        return False, "Password too short (minimum 4 characters) / Пароль слишком короткий (минимум 4 символа) / Пароль занадто короткий (мінімум 4 символи)"

    weak_patterns: List[str] = ['123456', 'password', 'qwerty', 'admin', 'letmein', 'welcome']
    for pattern in weak_patterns:
        if pattern.lower() in password.lower():
            return False, f"Password contains weak pattern: {pattern} / Пароль содержит слабый паттерн: {pattern} / Пароль містить слабкий патерн: {pattern}"

    return True, ""


def sanitize_label(label: str, max_length: int = 200) -> str:
    """
    Sanitize label for database storage.

    Очищает метку для хранения в БД.
    Очищує мітку для зберігання в БД.
    """
    import re
    if not label:
        return "Без метки / No label / Без мітки"

    sanitized: str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(label))
    sanitized = sanitized.strip()

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized if sanitized else "Без метки / No label / Без мітки"


# ==================== SECUREPASSPRO MAIN CLASS ====================
# ГЛАВНЫЙ КЛАСС SECUREPASSPRO
# ГОЛОВНИЙ КЛАС SECUREPASSPRO

class SecurePassPro(
    UIMixins,
    SecurityMixins,
    OpsMixins,
    VisualMixins,
    UIMethods,
    EventMethods,
    HelperMethods,
    CleanupMethods,
    ctk.CTk
):
    """
    Main application window

    Главное окно приложения
    Головне вікно програми
    """

    def __init__(self) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__()

        # Settings / Настройки / Налаштування
        self.current_lang: str = "RU"
        self.current_theme: str = "Dark"
        self.current_radius: int = 25
        self.current_font_size: int = 14
        self.clipboard_timeout: int = 60
        self._clipboard_timer: Optional[str] = None
        self._rgb_anim_id: Optional[str] = None
        self._pulse_animation_id: Optional[str] = None
        self._suspend_check_id: Optional[str] = None
        self._minimize_check_id: Optional[str] = None
        self._lock_check_timer: Optional[str] = None

        # RGB Speed and Width settings
        # Настройки скорости и толщины RGB
        # Налаштування швидкості та товщини RGB
        self.rgb_speed_setting: str = "normal"
        self.rgb_width_setting: str = "normal"

        # Auto-lock
        # Автоблокировка
        # Автоблокування
        self.auto_lock_enabled: tk.BooleanVar = tk.BooleanVar(value=False)
        self.auto_lock_timeout: int = 5
        self._last_activity_time: float = time.time()
        self._lock_check_id: Optional[str] = None
        self._was_minimized: bool = False
        self._last_lock_state: bool = False

        self._radius_timer: Optional[str] = None
        self._clip_timer: Optional[str] = None
        self._auto_timer: Optional[str] = None
        self._font_timer: Optional[str] = None

        set_global_radius(self.current_radius)

        # Linux adaptation
        # Адаптация для Linux
        # Адаптація для Linux
        if is_linux():
            try:
                apply_linux_theme(self)
                scaling: float = get_system_scaling()
                if scaling > 1.0:
                    ctk.set_widget_scaling(scaling)
                    ctk.set_window_scaling(scaling)
            except (AttributeError, RuntimeError, ImportError) as e:
                logger.debug(f"Linux theme application error / Ошибка применения темы Linux / Помилка застосування теми Linux: {e}")

        # UI Variables / Переменные интерфейса / Змінні інтерфейсу
        self.upper_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.lower_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.digits_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.symb_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.ambig_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.unambig_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.at_least_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.hide_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.no_repeat_var: tk.BooleanVar = tk.BooleanVar(value=False)
        self.sound_enabled: tk.BooleanVar = tk.BooleanVar(value=True)
        self.rgb_enabled: tk.BooleanVar = tk.BooleanVar(value=True)

        self.history: deque = deque(maxlen=HISTORY_MAX)
        self._rgb_t: float = 0.0

        # Windows / Окна / Вікна
        self.settings_window: Optional[ctk.CTkToplevel] = None
        self.about_window: Optional[ctk.CTkToplevel] = None
        self.history_window: Optional[ctk.CTkToplevel] = None
        self.qr_window: Optional[ctk.CTkToplevel] = None
        self.db_window: Optional[ctk.CTkToplevel] = None

        # Widget references / Ссылки на виджеты / Посилання на віджети
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
        self.auto_save_var: tk.BooleanVar = tk.BooleanVar(value=False)

        # 2FA elements / Элементы 2FA / Елементи 2FA
        self._2fa_status_label: Optional[ctk.CTkLabel] = None
        self._2fa_settings_btn: Optional[ctk.CTkButton] = None

        # RGB canvases / Холсты RGB / Полотна RGB
        self._rgb_c_top: Optional[tk.Canvas] = None
        self._rgb_c_bottom: Optional[tk.Canvas] = None
        self._rgb_c_left: Optional[tk.Canvas] = None
        self._rgb_c_right: Optional[tk.Canvas] = None

        self._icon_image: Optional[tk.PhotoImage] = None
        # FIXED: Updated path to font in Resources folder
        # Исправлено: Обновлён путь к шрифту в папке Resources
        # Виправлено: Оновлено шлях до шрифту в папці Resources
        self._pdf_font_path: str = get_resource_path("Resources/DejaVuSans.ttf")

        # Initialize password generator
        # Инициализация генератора паролей
        # Ініціалізація генератора паролів
        self.generator: PasswordGenerator = PasswordGenerator()
        self.strength_calc: StrengthCalculator = StrengthCalculator()
        self.config = AppSettings.instance()

        # Initialize 2FA
        # Инициализация 2FA
        # Ініціалізація 2FA
        try:
            init_totp_from_config(self.config)
            MasterPassword.set_config(self.config)
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.error(f"2FA initialization error / Ошибка инициализации 2FA / Помилка ініціалізації 2FA: {e}")

        if not QRUtils.is_available():
            logger.warning("QR code module not available. 2FA setup will show text only. / Модуль QR-кода недоступен. Настройка 2FA будет показывать только текст. / Модуль QR-коду недоступний. Налаштування 2FA буде показувати лише текст.")

        # Setup UI
        # Настройка интерфейса
        # Налаштування інтерфейсу
        try:
            ctk.set_widget_scaling(1.0)
            ctk.set_window_scaling(1.0)
        except (ValueError, AttributeError, RuntimeError) as e:
            logger.debug(f"Scaling setup error / Ошибка настройки масштабирования / Помилка налаштування масштабування: {e}")

        self.title("Secure Pass Pro v4.0")

        # Window settings
        # Настройки окна
        # Налаштування вікна
        try:
            self.resizable(True, True)
            self.minsize(800, 650)
            self.geometry("950x800")
            set_window_icon(self)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Window initialization error / Ошибка инициализации окна / Помилка ініціалізації вікна: {e}")

        try:
            self._create_rgb_canvases()
            self._setup_ui()
            self._apply_lang("RU")
            self._center_main_window()
            apply_window_rounding(self)
        except (AttributeError, RuntimeError, tk.TclError) as e:
            logger.error(f"UI setup error / Ошибка настройки интерфейса / Помилка налаштування інтерфейсу: {e}")

        # Bind keys
        # Привязка клавиш
        # Прив'язка клавіш
        try:
            self.bind('<F5>', lambda e: self._generate())
            self.bind('<Control-c>', lambda e: self._copy() if self.focus_get() is not self.entry_res else None)
            self.bind('<Control-s>', lambda e: self._save())
            self.bind('<Control-o>', lambda e: self._open())
            self.bind('<Escape>', lambda e: self._close_settings() if self.settings_window else None)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Key binding error / Ошибка привязки клавиш / Помилка прив'язки клавіш: {e}")

        # Activity tracking for auto-lock
        # Отслеживание активности для автоблокировки
        # Відстеження активності для автоблокування
        try:
            self.bind_all('<Key>', self._reset_activity_timer)
            self.bind_all('<Button>', self._reset_activity_timer)
            self.bind_all('<Motion>', self._reset_activity_timer)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Activity tracking binding error / Ошибка привязки отслеживания активности / Помилка прив'язки відстеження активності: {e}")

        # Load settings AFTER UI is created
        # Загрузка настроек ПОСЛЕ создания интерфейса
        # Завантаження налаштувань ПІСЛЯ створення інтерфейсу
        self.after(50, self._load_all_settings)
        self.after(100, self._start_lock_checker)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Register panic cleanup
        # Регистрация аварийной очистки
        # Реєстрація аварійного очищення
        try:
            PanicCleanup.register_clipboard_cleanup(self._emergency_clipboard_clear)
            PanicCleanup.register_cleanup_callback(self._emergency_cleanup)
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Panic cleanup registration error / Ошибка регистрации аварийной очистки / Помилка реєстрації аварійного очищення: {e}")

        # Register main window for radius updates
        # Регистрация главного окна для обновления радиуса
        # Реєстрація головного вікна для оновлення радіусу
        try:
            register_window(self)
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Window registration error / Ошибка регистрации окна / Помилка реєстрації вікна: {e}")

        # ========== SHIELD ICON LOADER ==========
        # Загружаем иконки щита для разных уровней силы пароля
        # Завантажуємо іконки щита для різних рівнів сили пароля
        self.after(100, self._load_shield_icons)

        # ── Global hotkey Ctrl+Alt+P ─────────────────────────────────────
        self.after(300, self._register_global_hotkey)

        # ── Auto-backup database ─────────────────────────────────────────
        self.after(1500, self._run_auto_backup)


# ==================== EXPORTS ====================
# ЭКСПОРТЫ
# ЕКСПОРТИ

__all__: List[str] = [
    'SecurePassPro',
    'validate_password_strength',
    'sanitize_label',
    'HISTORY_MAX',
    'UPD_URL',
    'BASE_DIR',
    'CONFIG_DIR',
    'CONFIG_FILE',
]