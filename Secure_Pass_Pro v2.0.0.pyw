import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import secrets
import string
import webbrowser
import os
import sys
import platform
import math
import configparser

# =============================================================================
# DEPENDENCIES / ЗАВИСИМОСТИ / ЗАЛЕЖНОСТІ
# =============================================================================
try:
    import qrcode
    from PIL import Image
except ImportError:
    # Print error and exit if libraries are missing
    # Вывод ошибки и выход если библиотеки не установлены
    # Виведення помилки та вихід якщо бібліотеки не встановлено
    print("Missing dependencies! Run: pip install qrcode[pil] pillow customtkinter")
    sys.exit(1)

# =============================================================================
# CONSTANTS / КОНСТАНТЫ / КОНСТАНТИ
# =============================================================================

# Config file stores theme and language between sessions
# Файл конфига хранит тему и язык между запусками
# Файл конфігу зберігає тему та мову між запусками
CONFIG_FILE = "config.ini"

# History max entries — prevents memory growth on heavy use
# Максимум записей в истории — предотвращает рост памяти при интенсивном использовании
# Максимум записів в історії — запобігає зростанню пам'яті при інтенсивному використанні
HISTORY_MAX = 50

# MD5 GPU brute-force speed used for crack time estimate
# Скорость перебора GPU MD5 для оценки времени взлома
# Швидкість перебору GPU MD5 для оцінки часу зламу
CRACK_SPEED = 100_000_000_000

# Internal theme identifiers — never localized, used as config keys
# Внутренние идентификаторы тем — никогда не локализуются, используются как ключи конфига
# Внутрішні ідентифікатори тем — ніколи не локалізуються, використовуються як ключі конфігу
THEME_INTERNAL = ("System", "Dark", "Light")

GITHUB_URL     = "https://github.com/Maximka1993271/Password-Generator-Python"
UPDATE_EXE_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe"

# =============================================================================
# LOCALIZATION / ЛОКАЛИЗАЦИЯ / ЛОКАЛІЗАЦІЯ
# =============================================================================
LANGUAGES: dict[str, dict[str, str]] = {
    "RU": {
        # Main UI / Основной интерфейс / Основний інтерфейс
        "title":    "Настройки генерации",
        "len":      "Длина пароля",
        "author":   "Автор: Максим Мельников",

        # Checkboxes / Флажки / Прапорці
        "upper":    "Заглавные буквы",
        "lower":    "Строчные буквы",
        "digits":   "Цифры",
        "symb":     "Спецсимволы",
        "ambig":    "Исключить похожие (i, l, 1, L, o, 0, O)",
        "at_least": "Минимум 1 из каждой категории",
        "hide":     "Скрывать символы",

        # Buttons / Кнопки / Кнопки
        "btn_gen":  "СГЕНЕРИРОВАТЬ",
        "btn_copy": "КОПИРОВАТЬ ПАРОЛЬ",
        "btn_save": "СОХРАНИТЬ В ФАЙЛ",
        "btn_open": "ОТКРЫТЬ ФАЙЛ",
        "btn_qr":   "QR-КОД ПАРОЛЯ",
        "btn_hist": "ИСТОРИЯ",
        "btn_upd":  "ОБНОВИТЬ ПРОГРАММУ",

        # Strength labels / Метки сложности / Мітки складності
        "strength": "Сложность",
        "time":     "Время взлома",

        # Dialog titles and messages / Заголовки диалогов / Заголовки діалогів
        "dlg_success":  "Успешно",
        "dlg_error":    "Ошибка",
        "dlg_update":   "Обновление",
        "dlg_history":  "История паролей",
        "dlg_qr":       "QR-код пароля",
        "dlg_no_pwd":   "Нет пароля для сохранения",
        "dlg_empty":    "Файл пуст",

        # Notification messages / Сообщения / Повідомлення
        "copied":   "Пароль скопирован!\nОчистка буфера через 60 сек.",
        "saved":    "Файл сохранён.",
        "upd_msg":  "Загрузка обновления v3.9...",

        # Settings / Настройки / Налаштування
        "radius":   "Закругление углов",
        "theme":    "Тема",

        # Crack time units / Единицы времени взлома / Одиниці часу зламу
        "t_instant":  "мгновенно",
        "t_sec":      "~{} сек.",
        "t_min":      "~{} мин.",
        "t_hour":     "~{} ч.",
        "t_days":     "~{} дн.",
        "t_years":    "~{} лет",
        "t_cent":     "~{} веков",
        "t_never":    "практически невозможно",

        # File dialog / Диалог файла / Діалог файлу
        "file_type":  "Текстовый файл",
        "save_title": "Сохранить пароль",
        "open_title": "Открыть файл с паролем",

        # Theme names (localized for display only)
        # Названия тем (локализованы только для отображения)
        # Назви тем (локалізовані лише для відображення)
        "sys":   "Системная",
        "dark":  "Тёмная",
        "light": "Светлая",
    },

    "EN": {
        # Main UI / Основной интерфейс / Основний інтерфейс
        "title":    "Generation Settings",
        "len":      "Password Length",
        "author":   "Author: Maxim Melnikov",

        # Checkboxes / Флажки / Прапорці
        "upper":    "Uppercase Letters",
        "lower":    "Lowercase Letters",
        "digits":   "Digits",
        "symb":     "Special Symbols",
        "ambig":    "Exclude ambiguous (i, l, 1, L, o, 0, O)",
        "at_least": "At least one from each category",
        "hide":     "Hide symbols",

        # Buttons / Кнопки / Кнопки
        "btn_gen":  "GENERATE",
        "btn_copy": "COPY PASSWORD",
        "btn_save": "SAVE TO FILE",
        "btn_open": "OPEN FILE",
        "btn_qr":   "PASSWORD QR-CODE",
        "btn_hist": "HISTORY",
        "btn_upd":  "UPDATE PROGRAM",

        # Strength labels / Метки сложности / Мітки складності
        "strength": "Strength",
        "time":     "Crack time",

        # Dialog titles and messages / Заголовки диалогов / Заголовки діалогів
        "dlg_success":  "Success",
        "dlg_error":    "Error",
        "dlg_update":   "Update",
        "dlg_history":  "Password History",
        "dlg_qr":       "Password QR-Code",
        "dlg_no_pwd":   "No password to save",
        "dlg_empty":    "File is empty",

        # Notification messages / Сообщения / Повідомлення
        "copied":   "Password copied!\nClipboard clears in 60 sec.",
        "saved":    "File saved.",
        "upd_msg":  "Downloading v3.9 update...",

        # Settings / Настройки / Налаштування
        "radius":   "Corner Radius",
        "theme":    "Theme",

        # Crack time units / Единицы времени взлома / Одиниці часу зламу
        "t_instant":  "instantly",
        "t_sec":      "~{} sec.",
        "t_min":      "~{} min.",
        "t_hour":     "~{} hrs.",
        "t_days":     "~{} days",
        "t_years":    "~{} years",
        "t_cent":     "~{} centuries",
        "t_never":    "practically uncrackable",

        # File dialog / Диалог файла / Діалог файлу
        "file_type":  "Text File",
        "save_title": "Save Password",
        "open_title": "Open Password File",

        # Theme names (localized for display only)
        "sys":   "System",
        "dark":  "Dark",
        "light": "Light",
    },

    "UA": {
        # Main UI / Основной интерфейс / Основний інтерфейс
        "title":    "Налаштування генерації",
        "len":      "Довжина пароля",
        "author":   "Автор: Максим Мельников",

        # Checkboxes / Флажки / Прапорці
        "upper":    "Великі літери",
        "lower":    "Малі літери",
        "digits":   "Цифри",
        "symb":     "Спецсимволи",
        "ambig":    "Виключити схожі (i, l, 1, L, o, 0, O)",
        "at_least": "Мінімум 1 з кожної категорії",
        "hide":     "Приховати символи",

        # Buttons / Кнопки / Кнопки
        "btn_gen":  "ЗГЕНЕРУВАТИ",
        "btn_copy": "КОПІЮВАТИ ПАРОЛЬ",
        "btn_save": "ЗБЕРЕГТИ У ФАЙЛ",
        "btn_open": "ВІДКРИТИ ФАЙЛ",
        "btn_qr":   "QR-КОД ПАРОЛЯ",
        "btn_hist": "ІСТОРІЯ",
        "btn_upd":  "ОНОВИТИ ПРОГРАМУ",

        # Strength labels / Метки сложности / Мітки складності
        "strength": "Складність",
        "time":     "Час зламу",

        # Dialog titles and messages / Заголовки диалогов / Заголовки діалогів
        "dlg_success":  "Успішно",
        "dlg_error":    "Помилка",
        "dlg_update":   "Оновлення",
        "dlg_history":  "Історія паролів",
        "dlg_qr":       "QR-код пароля",
        "dlg_no_pwd":   "Немає пароля для збереження",
        "dlg_empty":    "Файл порожній",

        # Notification messages / Сообщения / Повідомлення
        "copied":   "Пароль скопійовано!\nОчищення буфера через 60 сек.",
        "saved":    "Файл збережено.",
        "upd_msg":  "Завантаження оновлення v3.9...",

        # Settings / Настройки / Налаштування
        "radius":   "Закруглення кутів",
        "theme":    "Тема",

        # Crack time units / Единицы времени взлома / Одиниці часу зламу
        "t_instant":  "миттєво",
        "t_sec":      "~{} сек.",
        "t_min":      "~{} хв.",
        "t_hour":     "~{} год.",
        "t_days":     "~{} дн.",
        "t_years":    "~{} років",
        "t_cent":     "~{} віків",
        "t_never":    "практично неможливо",

        # File dialog / Диалог файла / Діалог файлу
        "file_type":  "Текстовий файл",
        "save_title": "Зберегти пароль",
        "open_title": "Відкрити файл з паролем",

        # Theme names (localized for display only)
        # FIX #12: was "Темная" (Russian) — corrected to Ukrainian "Темна"
        # ИСПРАВЛЕНИЕ #12: было "Темная" (по-русски) — исправлено на украинское "Темна"
        # ВИПРАВЛЕННЯ #12: було "Темная" (по-російськи) — виправлено на українське "Темна"
        "sys":   "Системна",
        "dark":  "Темна",      # ← FIX #12: was "Темная" (wrong language)
        "light": "Світла",
    },
}


# =============================================================================
# SOUND ENGINE / ЗВУКОВОЙ ДВИЖОК / ЗВУКОВИЙ РУШІЙ
# =============================================================================

def _beep(freq: int, ms: int) -> None:
    """
    Low-level Windows beep — silent on other platforms.
    Низкоуровневый Windows-бип — тихо на других платформах.
    Низькорівневий Windows-біп — тихо на інших платформах.
    """
    if platform.system() != "Windows":
        return
    try:
        import winsound  # lazy import — safe on all platforms / ленивый импорт / лінивий імпорт
        winsound.Beep(freq, ms)
    except Exception:
        pass  # hardware may not support beep / железо может не поддерживать / залізо може не підтримувати


def sound_generate() -> None:
    """Short rising tone on password generation / Короткий нарастающий тон при генерации / Короткий наростаючий тон при генерації"""
    _beep(900, 40); _beep(1200, 40)


def sound_copy() -> None:
    """Double high tone on clipboard copy / Двойной высокий тон при копировании / Подвійний тон при копіюванні"""
    _beep(1500, 70); _beep(2000, 70)


def sound_save() -> None:
    """Ascending triple tone on file save / Восходящий тройной тон при сохранении / Висхідний потрійний тон при збереженні"""
    _beep(800, 40); _beep(1000, 40); _beep(1300, 60)


def sound_error() -> None:
    """Low double tone on error / Низкий двойной тон при ошибке / Низький подвійний тон при помилці"""
    _beep(300, 120); _beep(250, 120)


# =============================================================================
# MAIN APPLICATION / ГЛАВНЫЙ КЛАСС / ГОЛОВНИЙ КЛАС
# =============================================================================

class SecurePassPro(ctk.CTk):
    """
    Main application window built with CustomTkinter.
    Главное окно приложения на CustomTkinter.
    Головне вікно програми на CustomTkinter.
    """

    VERSION = "v3.9"

    def __init__(self) -> None:
        super().__init__()

        # Application state / Состояние приложения / Стан програми
        self.current_lang: str  = "RU"
        self.current_theme: str = "System"   # internal key, never localized / внутренний ключ, не локализуется / внутрішній ключ
        self.history: list[str] = []
        self._clipboard_job     = None        # pending after() job id for clipboard wipe / ID задачи очистки буфера / ID завдання очищення буфера

        # Widget lists for bulk corner-radius update
        # Списки виджетов для массового обновления радиуса
        # Списки віджетів для масового оновлення радіусу
        self._radius_widgets: list = []

        self.title(f"Secure Pass Pro {self.VERSION}")
        self.geometry("420x880")
        self.resizable(False, False)

        self._setup_vars()
        self._setup_ui()
        self._bind_shortcuts()

        # Load saved config AFTER UI is built
        # Загружаем конфиг ПОСЛЕ построения UI
        # Завантажуємо конфіг ПІСЛЯ побудови UI
        self._load_config()

    # =========================================================================
    # CONFIG / КОНФИГУРАЦИЯ / КОНФІГУРАЦІЯ
    # =========================================================================

    def _load_config(self) -> None:
        """
        Read saved language and theme from config.ini and apply them.
        Читает сохранённые язык и тему из config.ini и применяет их.
        Читає збережені мову та тему з config.ini та застосовує їх.

        FIX #10: was missing entirely — settings reset every launch.
        ИСПРАВЛЕНИЕ #10: отсутствовал полностью — настройки сбрасывались при каждом запуске.
        ВИПРАВЛЕННЯ #10: був відсутній повністю — налаштування скидались при кожному запуску.
        """
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE, encoding="utf-8")
        lang  = config.get("Settings", "lang",  fallback="RU")
        theme = config.get("Settings", "theme", fallback="System")

        # Validate values to prevent corruption / Проверяем значения на корректность / Перевіряємо значення на коректність
        if lang  not in LANGUAGES:     lang  = "RU"
        if theme not in THEME_INTERNAL: theme = "System"

        self._apply_lang(lang)
        self._apply_theme(theme)

        # Sync UI controls / Синхронизируем элементы управления / Синхронізуємо елементи керування
        self.lang_menu.set(lang)
        # Theme menu shows localized label matching the saved internal key
        # Меню темы показывает локализованное название, соответствующее сохранённому ключу
        # Меню теми показує локалізовану назву, що відповідає збереженому ключу
        L = LANGUAGES[self.current_lang]
        locale_map = {"System": L["sys"], "Dark": L["dark"], "Light": L["light"]}
        self.theme_menu.set(locale_map.get(theme, L["sys"]))

    def _save_config(self) -> None:
        """
        Persist current language and theme to config.ini.
        Сохраняет текущий язык и тему в config.ini.
        Зберігає поточну мову та тему в config.ini.
        """
        config = configparser.ConfigParser()
        config["Settings"] = {"lang": self.current_lang, "theme": self.current_theme}
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                config.write(f)
        except OSError:
            pass  # non-critical / некритично / некритично

    # =========================================================================
    # VARIABLES / ПЕРЕМЕННЫЕ / ЗМІННІ
    # =========================================================================

    def _setup_vars(self) -> None:
        """
        Initialise all BooleanVar controls used by checkboxes.
        Инициализирует все BooleanVar, используемые чекбоксами.
        Ініціалізує всі BooleanVar, що використовуються прапорцями.
        """
        self.upper_var        = tk.BooleanVar(value=True)
        self.lower_var        = tk.BooleanVar(value=True)
        self.digits_var       = tk.BooleanVar(value=True)
        self.symb_var         = tk.BooleanVar(value=True)
        self.exclude_ambig_var= tk.BooleanVar(value=False)
        self.at_least_one_var = tk.BooleanVar(value=True)
        self.hide_var         = tk.BooleanVar(value=False)

    # =========================================================================
    # UI SETUP / ПОСТРОЕНИЕ ИНТЕРФЕЙСА / ПОБУДОВА ІНТЕРФЕЙСУ
    # =========================================================================

    def _setup_ui(self) -> None:
        """
        Build the complete widget tree.
        Строит полное дерево виджетов.
        Будує повне дерево віджетів.
        """
        # ---- Header / Заголовок / Заголовок ----
        self.lbl_title = ctk.CTkLabel(self, text="", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(10, 0))

        self.lbl_author = ctk.CTkLabel(self, text="", font=("Segoe UI", 11, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 5))

        # ---- Options frame / Фрейм параметров / Фрейм параметрів ----
        self.opt_frame = ctk.CTkFrame(self, corner_radius=10)
        self.opt_frame.pack(pady=5, padx=20, fill="x")
        self._radius_widgets.append(self.opt_frame)

        # Length slider / Слайдер длины / Слайдер довжини
        self.lbl_len = ctk.CTkLabel(self.opt_frame, text="", font=("Segoe UI", 13, "bold"))
        self.lbl_len.pack(pady=(5, 0))
        self.slider = ctk.CTkSlider(self.opt_frame, from_=4, to=64, number_of_steps=60,
                                    height=16, command=self._on_slider_change)
        self.slider.set(20)
        self.slider.pack(pady=5, padx=15)

        # Checkboxes / Флажки / Прапорці
        self.cb_upper    = self._make_cb(self.upper_var)
        self.cb_lower    = self._make_cb(self.lower_var)
        self.cb_digits   = self._make_cb(self.digits_var)
        self.cb_symb     = self._make_cb(self.symb_var)
        self.cb_ambig    = self._make_cb(self.exclude_ambig_var)
        self.cb_at_least = self._make_cb(self.at_least_one_var)
        self.cb_hide     = self._make_cb(self.hide_var, command=self._toggle_visibility)

        # ---- Password result entry / Поле результата / Поле результату ----
        self.entry_res = ctk.CTkEntry(self, height=38, font=("Consolas", 16),
                                      justify="center", corner_radius=8)
        self.entry_res.pack(pady=5, padx=20, fill="x")
        self._radius_widgets.append(self.entry_res)
        # Update strength whenever user edits the entry manually
        # Обновляем сложность при ручном редактировании поля
        # Оновлюємо складність при ручному редагуванні поля
        self.entry_res.bind("<KeyRelease>", lambda e: self._refresh_strength())

        # ---- Strength meters / Индикаторы / Індикатори ----
        self.strength_bar = ctk.CTkProgressBar(self, width=340, height=8)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=2)

        self.lbl_strength = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_strength.pack()
        self.lbl_time = ctk.CTkLabel(self, text="", font=("Segoe UI", 11))
        self.lbl_time.pack(pady=(0, 5))

        # ---- Action buttons / Кнопки / Кнопки ----
        self.btn_gen  = self._make_btn(self._generate,           "",  height=36, bold=True)
        self.btn_copy = self._make_btn(self._copy_password,      "",  fg="#28a745", hover="#218838")
        self.btn_save = self._make_btn(self._save_to_file,       "",  fg="#17a2b8", hover="#138496")
        self.btn_file = self._make_btn(self._open_file,          "",  fg="#17a2b8", hover="#138496")
        self.btn_qr   = self._make_btn(self._show_qr_window,     "",  fg="#6f42c1", hover="#5a32a3")
        self.btn_hist = self._make_btn(self._show_history_window,"",  fg="transparent", border=1,
                                       text_col=["#3b3b3b", "#ffffff"])
        self.btn_upd  = self._make_btn(self._check_updates,      "",  fg="#f39c12", hover="#e67e22")

        # ---- Corner radius slider / Слайдер радиуса / Слайдер радіусу ----
        self.lbl_radius = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_radius.pack(pady=(5, 0))
        self.slider_radius = ctk.CTkSlider(self, from_=0, to=20, number_of_steps=20,
                                           height=14, command=self._change_corner_radius)
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=(0, 5), padx=60, fill="x")

        # ---- Bottom controls / Нижние элементы / Нижні елементи ----
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=5, padx=20, fill="x")

        self.lang_menu = ctk.CTkOptionMenu(self.bottom_frame, values=["RU", "EN", "UA"],
                                           width=70, height=22, command=self._on_lang_change)
        self.lang_menu.set("RU")
        self.lang_menu.pack(side="left")

        # FIX #2: theme menu stores localized labels but change maps them back via internal key
        # ИСПРАВЛЕНИЕ #2: меню темы хранит локализованные метки, но смена маппит через внутренний ключ
        # ВИПРАВЛЕННЯ #2: меню теми зберігає локалізовані мітки, але зміна маппить через внутрішній ключ
        L0 = LANGUAGES["RU"]
        self.theme_menu = ctk.CTkOptionMenu(
            self.bottom_frame,
            values=[L0["sys"], L0["dark"], L0["light"]],
            width=100, height=22,
            command=self._on_theme_change
        )
        self.theme_menu.pack(side="right")

        # ---- Footer / Подвал / Підвал ----
        self.btn_github = ctk.CTkButton(self, text="GitHub ©", height=20, width=90,
                                        fg_color="#24292e", font=("Segoe UI", 10),
                                        command=lambda: webbrowser.open(GITHUB_URL))
        self.btn_github.pack(pady=(5, 0))
        self._radius_widgets.append(self.btn_github)

        self.lbl_stars = ctk.CTkLabel(self, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_stars.pack(pady=(0, 10))

        # Initial localization pass / Первичная локализация / Первинна локалізація
        self._apply_lang("RU")

    def _make_cb(self, var: tk.BooleanVar, command=None) -> ctk.CTkCheckBox:
        """
        Create and pack a themed checkbox into the options frame.
        Создаёт и упаковывает тематический чекбокс в фрейм параметров.
        Створює та пакує тематичний прапорець у фрейм параметрів.
        """
        cb = ctk.CTkCheckBox(
            self.opt_frame, text="", variable=var,
            font=("Segoe UI", 11), checkbox_width=18, checkbox_height=18,
            command=lambda: (command() if command else None, self._refresh_strength())
        )
        cb.pack(anchor="w", padx=30, pady=2)
        return cb

    def _make_btn(self, cmd, txt: str, fg=None, hover=None,
                  height: int = 30, bold: bool = False,
                  border: int = 0, text_col=None) -> ctk.CTkButton:
        """
        Create and pack a styled action button.
        Создаёт и упаковывает стилизованную кнопку действия.
        Створює та пакує стилізовану кнопку дії.
        """
        btn = ctk.CTkButton(
            self, text=txt, height=height, command=cmd, border_width=border,
            font=("Segoe UI", 12 if bold else 11, "bold")
        )
        if fg:       btn.configure(fg_color=fg)
        if hover:    btn.configure(hover_color=hover)
        if text_col: btn.configure(text_color=text_col)
        btn.pack(pady=2, padx=40, fill="x")
        self._radius_widgets.append(btn)
        return btn

    # =========================================================================
    # KEYBOARD SHORTCUTS / ГОРЯЧИЕ КЛАВИШИ / ГАРЯЧІ КЛАВІШІ
    # =========================================================================

    def _bind_shortcuts(self) -> None:
        """
        Bind global keyboard shortcuts.
        FIX #13: shortcuts were completely missing in the original.

        Привязывает глобальные горячие клавиши.
        ИСПРАВЛЕНИЕ #13: шорткатов не было вообще в оригинале.

        Прив'язує глобальні гарячі клавіші.
        ВИПРАВЛЕННЯ #13: шорткатів не було взагалі в оригіналі.
        """
        self.bind("<Control-g>", lambda e: self._generate())
        self.bind("<Control-G>", lambda e: self._generate())
        self.bind("<Control-s>", lambda e: self._save_to_file())
        self.bind("<Control-S>", lambda e: self._save_to_file())
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-O>", lambda e: self._open_file())

    # =========================================================================
    # LOCALIZATION / ЛОКАЛИЗАЦИЯ / ЛОКАЛІЗАЦІЯ
    # =========================================================================

    def _apply_lang(self, lang: str) -> None:
        """
        Switch all widget text to the chosen language.
        Переключает текст всех виджетов на выбранный язык.
        Перемикає текст усіх віджетів на обрану мову.
        """
        self.current_lang = lang
        L = LANGUAGES[lang]

        self.lbl_title.configure(text=L["title"])
        self.lbl_author.configure(text=L["author"])
        self.lbl_len.configure(text=f"{L['len']}: {int(self.slider.get())}")
        self.lbl_radius.configure(text=f"{L['radius']}: {int(self.slider_radius.get())}")

        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])

        self.btn_gen.configure(text=L["btn_gen"])
        self.btn_copy.configure(text=L["btn_copy"])
        self.btn_save.configure(text=L["btn_save"])
        self.btn_file.configure(text=L["btn_open"])
        self.btn_qr.configure(text=L["btn_qr"])
        self.btn_hist.configure(text=L["btn_hist"])
        self.btn_upd.configure(text=L["btn_upd"])

        # Update theme menu labels to new language while keeping current selection
        # Обновляем метки меню тем на новый язык, сохраняя текущий выбор
        # Оновлюємо мітки меню тем на нову мову, зберігаючи поточний вибір
        self.theme_menu.configure(values=[L["sys"], L["dark"], L["light"]])
        locale_map = {"System": L["sys"], "Dark": L["dark"], "Light": L["light"]}
        self.theme_menu.set(locale_map.get(self.current_theme, L["sys"]))

        self._refresh_strength()

    def _on_lang_change(self, choice: str) -> None:
        """
        Called when user picks a language from the dropdown.
        Вызывается когда пользователь выбирает язык из выпадающего списка.
        Викликається коли користувач вибирає мову з випадного списку.
        """
        self._apply_lang(choice)
        self._save_config()

    # =========================================================================
    # THEME ENGINE / ДВИЖОК ТЕМ / РУШІЙ ТЕМ
    # =========================================================================

    def _apply_theme(self, internal: str) -> None:
        """
        Apply a theme by its internal English key ('System', 'Dark', 'Light').

        FIX #2: original mapped localized label back to English key using the
        CURRENT language at click time — but after a language switch, the menu
        selection was still a label from the OLD language, causing a KeyError or
        silent fallback to System every time.
        Solution: store the internal key separately and never mix it with display labels.

        Применяет тему по внутреннему английскому ключу ('System', 'Dark', 'Light').

        ИСПРАВЛЕНИЕ #2: оригинал маппил локализованную метку обратно в английский ключ
        через текущий язык — но после смены языка выбор в меню оставался меткой из
        СТАРОГО языка, вызывая KeyError или тихий fallback на System.
        Решение: хранить внутренний ключ отдельно и никогда не смешивать с метками.

        Застосовує тему за внутрішнім англійським ключем ('System', 'Dark', 'Light').

        ВИПРАВЛЕННЯ #2: оригінал маппив локалізовану мітку назад в англійський ключ
        через поточну мову — але після зміни мови вибір у меню залишався міткою зі
        СТАРОЇ мови, спричиняючи KeyError або тихий fallback на System.
        Рішення: зберігати внутрішній ключ окремо і ніколи не змішувати з мітками.
        """
        if internal not in THEME_INTERNAL:
            internal = "System"
        self.current_theme = internal
        ctk.set_appearance_mode(internal)

    def _on_theme_change(self, localized_choice: str) -> None:
        """
        Called when user picks a theme from the localized dropdown.
        Reverse-maps the localized label to the internal key.

        Вызывается при выборе темы из локализованного выпадающего меню.
        Маппит локализованную метку обратно в внутренний ключ.

        Викликається при виборі теми з локалізованого випадного меню.
        Маппить локалізовану мітку назад у внутрішній ключ.
        """
        L = LANGUAGES[self.current_lang]
        # Build reverse map from current language's labels to internal keys
        # Строим обратный маппинг из меток текущего языка во внутренние ключи
        # Будуємо зворотний маппінг з міток поточної мови у внутрішні ключі
        reverse = {L["sys"]: "System", L["dark"]: "Dark", L["light"]: "Light"}
        internal = reverse.get(localized_choice, "System")
        self._apply_theme(internal)
        self._save_config()

    # =========================================================================
    # PASSWORD GENERATION / ГЕНЕРАЦИЯ ПАРОЛЯ / ГЕНЕРАЦІЯ ПАРОЛЯ
    # =========================================================================

    def _generate(self) -> None:
        """
        Core password generation using secrets (CSPRNG).

        FIX #11: when length < number of categories and at_least_one is checked,
        the original silently fell through to pure random — guarantee was broken.
        Fix: reduce pools to fit length when at_least_one is active.

        Основная генерация пароля через secrets (CSPRNG).

        ИСПРАВЛЕНИЕ #11: когда длина < количества категорий и включён at_least_one,
        оригинал тихо переходил к чисто случайному — гарантия нарушалась.
        Исправление: сокращаем пулы чтобы влезть в длину.

        Основна генерація пароля через secrets (CSPRNG).

        ВИПРАВЛЕННЯ #11: коли довжина < кількості категорій і увімкнено at_least_one,
        оригінал тихо переходив до чисто випадкового — гарантія порушувалась.
        Виправлення: скорочуємо пули щоб вміститись у довжину.
        """
        sound_generate()

        # Build character pools for each enabled category
        # Формируем пулы символов для каждой включённой категории
        # Формуємо пули символів для кожної увімкненої категорії
        ambig = "il1Lo0O"

        def _filter(s: str) -> str:
            return "".join(c for c in s if c not in ambig) if self.exclude_ambig_var.get() else s

        pools: list[str] = []
        if self.upper_var.get():  pools.append(_filter(string.ascii_uppercase))
        if self.lower_var.get():  pools.append(_filter(string.ascii_lowercase))
        if self.digits_var.get(): pools.append(_filter(string.digits))
        if self.symb_var.get():   pools.append(string.punctuation)

        # Remove pools that became empty after filtering
        # Убираем пулы, ставшие пустыми после фильтрации
        # Прибираємо пули, що стали порожніми після фільтрації
        pools = [p for p in pools if p]
        if not pools:
            sound_error()
            return

        length  = int(self.slider.get())
        full    = "".join(pools)
        result: list[str] = []

        if self.at_least_one_var.get():
            # FIX #11: cap pools to length so at_least guarantee never breaks
            # ИСПРАВЛЕНИЕ #11: ограничиваем пулы длиной чтобы гарантия не нарушалась
            # ВИПРАВЛЕННЯ #11: обмежуємо пули довжиною щоб гарантія не порушувалась
            effective_pools = pools[:length]
            for p in effective_pools:
                result.append(secrets.choice(p))
            for _ in range(length - len(effective_pools)):
                result.append(secrets.choice(full))
        else:
            result = [secrets.choice(full) for _ in range(length)]

        secrets.SystemRandom().shuffle(result)
        pwd = "".join(result)

        # Update entry / Обновляем поле / Оновлюємо поле
        self.entry_res.delete(0, tk.END)
        self.entry_res.insert(0, pwd)

        # FIX #6: cap history at HISTORY_MAX to prevent unbounded memory growth
        # ИСПРАВЛЕНИЕ #6: ограничиваем историю HISTORY_MAX для предотвращения утечки памяти
        # ВИПРАВЛЕННЯ #6: обмежуємо історію HISTORY_MAX для запобігання витоку пам'яті
        self.history.insert(0, f"[{length}] {pwd}")
        if len(self.history) > HISTORY_MAX:
            self.history = self.history[:HISTORY_MAX]

        self._refresh_strength()

    # =========================================================================
    # STRENGTH METER / ИНДИКАТОР СЛОЖНОСТИ / ІНДИКАТОР СКЛАДНОСТІ
    # =========================================================================

    def _calculate_entropy(self, password: str) -> float:
        """
        Calculate Shannon entropy based on charset detected in the password.

        FIX #9: original calculated entropy from checkbox state, not from the
        actual password content. After open_file() or manual edit the display
        was wrong. Now we inspect the actual characters.

        Вычисляет энтропию Шеннона по набору символов в реальном пароле.

        ИСПРАВЛЕНИЕ #9: оригинал вычислял энтропию из состояния чекбоксов, не из
        реального содержимого пароля. После open_file() или ручного редактирования
        индикатор врал. Теперь анализируем реальные символы.

        Обчислює ентропію Шеннона за набором символів у реальному паролі.

        ВИПРАВЛЕННЯ #9: оригінал обчислював ентропію зі стану прапорців, не з
        реального вмісту пароля. Після open_file() або ручного редагування
        індикатор брехав. Тепер аналізуємо реальні символи.
        """
        if not password:
            return 0.0
        sz = 0
        if any(c.islower()             for c in password): sz += 26
        if any(c.isupper()             for c in password): sz += 26
        if any(c.isdigit()             for c in password): sz += 10
        if any(c in string.punctuation for c in password): sz += 32
        return len(password) * math.log2(sz) if sz > 0 else 0.0

    def _get_time_estimate(self, entropy: float) -> str:
        """
        Format crack-time estimate string for the given entropy.

        FIX #1: original skipped days and years entirely — anything over 1 day
        immediately showed '>100 centuries'. The t_days and t_years keys existed
        in LANGUAGES but were never referenced. Now covers all ranges.

        Форматирует строку оценки времени взлома для данной энтропии.

        ИСПРАВЛЕНИЕ #1: оригинал пропускал дни и годы полностью — всё что больше
        1 дня сразу показывало '>100 веков'. Ключи t_days и t_years существовали
        в LANGUAGES но никогда не использовались. Теперь охватываем все диапазоны.

        Форматує рядок оцінки часу зламу для даної ентропії.

        ВИПРАВЛЕННЯ #1: оригінал пропускав дні та роки повністю — все що більше
        1 дня одразу показувало '>100 віків'. Ключі t_days та t_years існували
        в LANGUAGES але ніколи не використовувались. Тепер охоплюємо всі діапазони.
        """
        if entropy <= 0:
            return ""
        sec = (2 ** entropy) / CRACK_SPEED
        L   = LANGUAGES[self.current_lang]

        if   sec < 1:                    return L["t_instant"]
        elif sec < 60:                   return L["t_sec"].format(int(sec))
        elif sec < 3_600:                return L["t_min"].format(int(sec // 60))
        elif sec < 86_400:               return L["t_hour"].format(int(sec // 3_600))
        elif sec < 86_400 * 365:         return L["t_days"].format(int(sec // 86_400))        # ← FIX #1
        elif sec < 86_400 * 365 * 100:   return L["t_years"].format(int(sec // (86_400*365)))  # ← FIX #1
        elif sec < 86_400 * 365 * 10000: return L["t_cent"].format(int(sec // (86_400*365*100)))
        else:                            return L["t_never"]

    def _refresh_strength(self) -> None:
        """
        Recalculate and display strength bar and crack-time from ACTUAL entry content.
        Пересчитывает и отображает индикатор по РЕАЛЬНОМУ содержимому поля.
        Перераховує та відображає індикатор за РЕАЛЬНИМ вмістом поля.
        """
        L   = LANGUAGES[self.current_lang]
        pwd = self.entry_res.get()
        ent = self._calculate_entropy(pwd)

        bar_val = min(ent / 128, 1.0)   # 128 bit = full bar / 128 бит = полная шкала / 128 біт = повна шкала
        color   = "#ff4b4b" if ent < 40 else "#ffcc00" if ent < 80 else "#2ecc71"

        self.strength_bar.set(bar_val)
        self.strength_bar.configure(progress_color=color)
        self.lbl_strength.configure(
            text=f"{L['strength']}: {int(ent)} bit" if pwd else L["strength"],
            text_color=color
        )
        self.lbl_time.configure(
            text=f"{L['time']}: {self._get_time_estimate(ent)}" if pwd else L["time"],
            text_color=color
        )

    # =========================================================================
    # CLIPBOARD / БУФЕР ОБМЕНА / БУФЕР ОБМІНУ
    # =========================================================================

    def _copy_password(self) -> None:
        """
        Copy password to clipboard and schedule auto-clear after 60 s.

        FIX #7: original never cleared the clipboard — password stayed forever.

        Копирует пароль в буфер и планирует автоочистку через 60 с.

        ИСПРАВЛЕНИЕ #7: оригинал никогда не очищал буфер — пароль оставался навсегда.

        Копіює пароль у буфер та планує автоочищення через 60 с.

        ВИПРАВЛЕННЯ #7: оригінал ніколи не очищав буфер — пароль залишався назавжди.
        """
        pwd = self.entry_res.get()
        if not pwd:
            return
        sound_copy()
        self.clipboard_clear()
        self.clipboard_append(pwd)

        # Cancel any previous pending clear job / Отменяем предыдущую отложенную очистку / Скасовуємо попереднє відкладене очищення
        if self._clipboard_job:
            self.after_cancel(self._clipboard_job)

        # FIX #7: schedule clipboard wipe after 60 seconds
        # ИСПРАВЛЕНИЕ #7: планируем очистку буфера через 60 секунд
        # ВИПРАВЛЕННЯ #7: плануємо очищення буфера через 60 секунд
        self._clipboard_job = self.after(
            60_000,
            lambda: self.clipboard_clear() if self.winfo_exists() else None
        )

        L = LANGUAGES[self.current_lang]
        self._show_message(L["dlg_success"], L["copied"])

    # =========================================================================
    # FILE OPERATIONS / ФАЙЛОВЫЕ ОПЕРАЦИИ / ФАЙЛОВІ ОПЕРАЦІЇ
    # =========================================================================

    def _save_to_file(self) -> None:
        """
        Save current password to a .txt file chosen by the user.

        FIX #4: original had no OSError handling — a permission error or full
        disk would crash silently.

        Сохраняет текущий пароль в .txt файл по выбору пользователя.

        ИСПРАВЛЕНИЕ #4: оригинал не обрабатывал OSError — ошибка прав или
        заполненный диск приводили к тихому сбою.

        Зберігає поточний пароль у .txt файл за вибором користувача.

        ВИПРАВЛЕННЯ #4: оригінал не обробляв OSError — помилка прав або
        заповнений диск призводили до тихого збою.
        """
        pwd = self.entry_res.get()
        L   = LANGUAGES[self.current_lang]
        if not pwd:
            sound_error()
            self._show_message(L["dlg_error"], L["dlg_no_pwd"])
            return

        path = filedialog.asksaveasfilename(
            title=L["save_title"],
            defaultextension=".txt",
            filetypes=[(L["file_type"], "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"SecurePassPro {self.VERSION}\n{L['dlg_success']}: {pwd}")
            sound_save()
            self._show_message(L["dlg_success"], L["saved"])
        except OSError as e:     # ← FIX #4: was unhandled
            sound_error()
            self._show_message(L["dlg_error"], str(e))

    def _open_file(self) -> None:
        """
        Load a password from a .txt file into the entry field.

        FIX #3: original used os.startfile() which opens the file in the system
        viewer (Notepad, etc.) — completely wrong behavior. Should read the file
        content and display it in the password entry, matching every other version.

        Загружает пароль из .txt файла в поле ввода.

        ИСПРАВЛЕНИЕ #3: оригинал использовал os.startfile() — открывал файл в
        системном приложении (Блокнот и т.п.) — полностью неправильное поведение.
        Должен читать содержимое и показывать в поле пароля.

        Завантажує пароль з .txt файлу в поле введення.

        ВИПРАВЛЕННЯ #3: оригінал використовував os.startfile() — відкривав файл у
        системному застосунку (Блокнот тощо) — повністю неправильна поведінка.
        Має читати вміст і показувати в полі пароля.
        """
        L    = LANGUAGES[self.current_lang]
        path = filedialog.askopenfilename(
            title=L["open_title"],
            filetypes=[(L["file_type"], "*.txt"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                self._show_message(L["dlg_error"], L["dlg_empty"])
                return
            # If the file was saved by this app, extract just the password line
            # Если файл сохранён этим приложением — берём только строку пароля
            # Якщо файл збережено цією програмою — беремо лише рядок пароля
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            pwd   = lines[-1].split(": ", 1)[-1] if ": " in lines[-1] else lines[-1]

            self.entry_res.delete(0, tk.END)
            self.entry_res.insert(0, pwd)
            self._refresh_strength()
        except OSError as e:
            sound_error()
            self._show_message(L["dlg_error"], str(e))

    # =========================================================================
    # QR CODE / QR-КОД / QR-КОД
    # =========================================================================

    def _show_qr_window(self) -> None:
        """
        Render password as QR code in a Toplevel window.

        FIX #8: original had no exception handling — qrcode or CTkImage failures
        would crash silently with an unhandled exception traceback.

        Рендерит пароль как QR-код в дочернем окне.

        ИСПРАВЛЕНИЕ #8: оригинал не обрабатывал исключения — сбои qrcode или
        CTkImage приводили к тихому падению с трассировкой.

        Рендерить пароль як QR-код у дочірньому вікні.

        ВИПРАВЛЕННЯ #8: оригінал не обробляв виключення — збої qrcode або
        CTkImage призводили до тихого падіння з трасуванням.
        """
        pwd = self.entry_res.get()
        L   = LANGUAGES[self.current_lang]
        if not pwd:
            sound_error()
            return

        win = ctk.CTkToplevel(self)
        win.title(L["dlg_qr"])
        win.attributes("-topmost", True)
        win.resizable(False, False)
        self._center_child(win, 260, 280)

        try:
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(pwd)
            qr.make(fit=True)
            img    = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))
            ctk.CTkLabel(win, image=ctk_img, text="").pack(pady=20)
            ctk.CTkButton(win, text="OK", width=80, height=26, command=win.destroy).pack(pady=5)
        except Exception as e:         # ← FIX #8: was unhandled
            win.destroy()
            sound_error()
            self._show_message(L["dlg_error"], str(e))

    # =========================================================================
    # HISTORY / ИСТОРИЯ / ІСТОРІЯ
    # =========================================================================

    def _show_history_window(self) -> None:
        """
        Display the last HISTORY_MAX generated passwords.
        Отображает последние HISTORY_MAX сгенерированных паролей.
        Відображає останні HISTORY_MAX згенеровані паролі.
        """
        L   = LANGUAGES[self.current_lang]
        win = ctk.CTkToplevel(self)
        win.title(L["dlg_history"])
        win.attributes("-topmost", True)
        self._center_child(win, 380, 400)

        txt = ctk.CTkTextbox(win, font=("Consolas", 12), border_width=2)
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        txt.configure(state="normal")
        txt.insert("0.0", "\n".join(self.history) if self.history else "...")
        txt.configure(state="disabled")

    # =========================================================================
    # UPDATES / ОБНОВЛЕНИЯ / ОНОВЛЕННЯ
    # =========================================================================

    def _check_updates(self) -> None:
        """
        Open the direct EXE download link in the browser.
        Открывает прямую ссылку на скачивание EXE в браузере.
        Відкриває пряме посилання на завантаження EXE у браузері.
        """
        L = LANGUAGES[self.current_lang]
        self._show_message(L["dlg_update"], L["upd_msg"])
        webbrowser.open(UPDATE_EXE_URL)

    # =========================================================================
    # INFO DIALOGS / ДИАЛОГОВЫЕ ОКНА / ДІАЛОГОВІ ВІКНА
    # =========================================================================

    def _show_message(self, title: str, message: str) -> None:
        """
        Generic modal info window — accepts pre-resolved strings, no key lookups.

        FIX #5: original did l[title_key] which raised KeyError for unknown keys.
        Now callers pass already-localised strings — no lookup, no crash risk.

        Универсальное модальное окно — принимает готовые строки, без поиска ключей.

        ИСПРАВЛЕНИЕ #5: оригинал делал l[title_key] что вызывало KeyError для
        неизвестных ключей. Теперь вызывающий код передаёт готовые строки.

        Універсальне модальне вікно — приймає готові рядки, без пошуку ключів.

        ВИПРАВЛЕННЯ #5: оригінал робив l[title_key] що спричиняло KeyError для
        невідомих ключів. Тепер код, що викликає, передає готові рядки.
        """
        win = ctk.CTkToplevel(self)
        win.title(title)      # plain string — never a dict key / готовая строка — никогда не ключ / готовий рядок
        win.attributes("-topmost", True)
        win.resizable(False, False)
        self._center_child(win, 300, 150)
        ctk.CTkLabel(win, text=message, font=("Segoe UI", 12), wraplength=260).pack(pady=20)
        ctk.CTkButton(win, text="OK", width=80, height=26, command=win.destroy).pack()

    # =========================================================================
    # CORNER RADIUS / РАДИУС УГЛОВ / РАДІУС КУТІВ
    # =========================================================================

    def _change_corner_radius(self, val) -> None:
        """
        Apply corner radius to all registered widgets.
        Применяет радиус углов ко всем зарегистрированным виджетам.
        Застосовує радіус кутів до всіх зареєстрованих віджетів.
        """
        r = int(val)
        L = LANGUAGES[self.current_lang]
        self.lbl_radius.configure(text=f"{L['radius']}: {r}")
        for w in self._radius_widgets:
            try:
                w.configure(corner_radius=r)
            except Exception:
                pass  # widget may not support corner_radius / виджет может не поддерживать / віджет може не підтримувати

    # =========================================================================
    # UTILITIES / УТИЛИТЫ / УТИЛІТИ
    # =========================================================================

    def _toggle_visibility(self) -> None:
        """
        Toggle password masking in the result entry.
        Переключает маскировку пароля в поле результата.
        Перемикає маскування пароля в полі результату.
        """
        self.entry_res.configure(show="*" if self.hide_var.get() else "")

    def _on_slider_change(self, val) -> None:
        """
        Update length label when slider moves.
        Обновляет метку длины при движении слайдера.
        Оновлює мітку довжини при русі слайдера.
        """
        L = LANGUAGES[self.current_lang]
        self.lbl_len.configure(text=f"{L['len']}: {int(val)}")
        self._refresh_strength()

    def _center_child(self, win: ctk.CTkToplevel, w: int, h: int) -> None:
        """
        Center a child window over this application window.
        Центрирует дочернее окно над главным окном приложения.
        Центрує дочірнє вікно над головним вікном програми.
        """
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")


# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА / ТОЧКА ВХОДУ
# =============================================================================

if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()
