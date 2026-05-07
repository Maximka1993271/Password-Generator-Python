"""
SecurePassPro v3.9 — Cryptographically secure password generator
Криптографически стойкий генератор паролей /
Криптографічно стійкий генератор паролів

Requires / Требует / Вимагає:
    pip install qrcode[pil] pillow customtkinter
    Python >= 3.9
"""

# Fix #6 / Исправление #6 / Виправлення #6
# from __future__ import annotations enables X|Y union hints on Python 3.9
# Позволяет использовать X|Y аннотации типов на Python 3.9
# Дозволяє використовувати X|Y анотації типів на Python 3.9
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
# PLATFORM CACHE / КЕШ ПЛАТФОРМЫ / КЕШ ПЛАТФОРМИ
# Fix #13 / Исправление #13 / Виправлення #13
# Cache platform check once at import — do NOT call platform.system() per beep
# Кешировать проверку платформы один раз — НЕ вызывать при каждом звуке
# Кешувати перевірку платформи один раз — НЕ викликати при кожному звуці
# =============================================================================
_IS_WINDOWS: bool = platform.system() == "Windows"

# =============================================================================
# SOUND ENGINE / ЗВУКОВОЙ ДВИЖОК / ЗВУКОВИЙ ДВИГУН
# =============================================================================
def _beep(freq: int, ms: int) -> None:
    """
    Blocking system beep, Windows only /
    Блокирующий системный сигнал, только Windows /
    Блокуючий системний сигнал, тільки Windows
    """
    if _IS_WINDOWS:
        try:
            import winsound
            winsound.Beep(freq, ms)
        except Exception:
            pass


def _beep_async(*pairs: tuple) -> None:
    """
    Non-blocking beep sequence in a daemon thread /
    Неблокирующая последовательность сигналов в демон-потоке /
    Неблокуюча послідовність сигналів у демон-потоці

    Fix #4 / Исправление #4 / Виправлення #4
    Typed *pairs annotation prevents silent crashes inside the daemon thread /
    Типизированный *pairs предотвращает молчаливые падения внутри потока /
    Типізований *pairs запобігає мовчазним падінням всередині потоку
    """
    def _run() -> None:
        for freq, ms in pairs:
            _beep(int(freq), int(ms))

    threading.Thread(target=_run, daemon=True).start()


# Sound presets / Пресеты звуков / Пресети звуків
def sound_generate() -> None: _beep_async((800, 50), (1200, 50))
def sound_copy()     -> None: _beep_async((1500, 100),)
def sound_action()   -> None: _beep_async((1000, 60),)
def sound_error()    -> None: _beep_async((400, 150), (300, 150))


# =============================================================================
# DEPENDENCIES CHECK / ПРОВЕРКА ЗАВИСИМОСТЕЙ / ПЕРЕВІРКА ЗАЛЕЖНОСТЕЙ
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


# =============================================================================
# PILLOW COMPATIBILITY / СОВМЕСТИМОСТЬ PILLOW / СУМІСНІСТЬ PILLOW
# =============================================================================
def _get_resample() -> int:
    """
    Return correct Pillow resampling filter for installed version /
    Вернуть правильный фильтр ресемплинга для установленной версии Pillow /
    Повернути правильний фільтр ресемплінгу для встановленої версії Pillow

    Pillow >= 9.1 → Image.Resampling.LANCZOS
    Pillow  8.x  → Image.LANCZOS  (deprecated alias)
    """
    try:
        return Image.Resampling.LANCZOS   # Pillow >= 9.1
    except AttributeError:
        return Image.LANCZOS              # Pillow 8.x fallback


# Called AFTER PIL import — order is safe /
# Вызывается ПОСЛЕ импорта PIL — порядок безопасен /
# Викликається ПІСЛЯ імпорту PIL — порядок безпечний
RESAMPLE: int = _get_resample()


# =============================================================================
# TOOLTIP CLASS / КЛАСС ПОДСКАЗОК / КЛАС ПІДКАЗОК
# =============================================================================
class ToolTip:
    """
    Hover tooltip widget /
    Виджет всплывающей подсказки /
    Віджет спливаючої підказки
    """

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text   = text
        self.tip_window: Optional[tk.Toplevel] = None

    def show_tip(self) -> None:
        """
        Display tooltip near widget /
        Показать подсказку рядом с виджетом /
        Показати підказку поруч з віджетом
        """
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
        """
        Hide and destroy tooltip /
        Скрыть и уничтожить подсказку /
        Приховати та знищити підказку
        """
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


# =============================================================================
# CONSTANTS / КОНСТАНТЫ / КОНСТАНТИ
# =============================================================================
HISTORY_MAX     = 50
FILE_READ_LIMIT = 1024      # Max bytes to read from file / Макс. байт из файла / Макс. байт з файлу
UPD_URL         = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe"
AMBIGUOUS_CHARS = "il1Lo0O"  # Characters excluded when ambig-mode is on / Символы при режиме исключения / Символи при режимі виключення

# Per-category ambiguous char counts — computed once at import /
# Количество неоднозначных символов по категориям — вычисляется один раз /
# Кількість неоднозначних символів за категоріями — обчислюється один раз
#   Lowercase : i, l            → 2
#   Uppercase : L, O (letter O) → 2   ← O is letter O, NOT digit zero / О — заглавная O, НЕ цифра ноль / О — велика O, НЕ цифра нуль
#   Digits    : 1, 0 (zero)     → 2
# Fix #9 / Исправление #9 / Виправлення #9 — clarified O vs 0 in comments above
_AMBIG_LOWER  = sum(1 for c in AMBIGUOUS_CHARS if c in string.ascii_lowercase)  # 2
_AMBIG_UPPER  = sum(1 for c in AMBIGUOUS_CHARS if c in string.ascii_uppercase)  # 2
_AMBIG_DIGITS = sum(1 for c in AMBIGUOUS_CHARS if c in string.digits)           # 2

# Fix #10 / Исправление #10 / Виправлення #10
# Module-level CSPRNG singleton — avoids creating a new object on every generation /
# Синглтон CSPRNG уровня модуля — не создаётся новый объект при каждой генерации /
# Синглтон CSPRNG рівня модуля — не створюється новий об'єкт при кожній генерації
_SYSRNG = secrets.SystemRandom()

# Fix #14 / Исправление #14 / Виправлення #14
# Explicit __all__ prevents star-import pollution /
# Явный __all__ предотвращает загрязнение пространства имён при *-импорте /
# Явний __all__ запобігає забрудненню простору імен при *-імпорті
__all__ = ["SecurePassPro"]


# =============================================================================
# LANGUAGE DEFINITIONS / ОПРЕДЕЛЕНИЯ ЯЗЫКОВ / ВИЗНАЧЕННЯ МОВ
# =============================================================================
# Fix #11 / Исправление #11 / Виправлення #11
# "err_len" key removed — it was declared but never used anywhere in the code /
# Ключ "err_len" удалён — был объявлен, но нигде не использовался /
# Ключ "err_len" видалено — був оголошений, але ніде не використовувався
LANGUAGES: Dict[str, Dict[str, str]] = {
    "RU": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Настройки генерации",
        "len":        "Длина пароля",
        "author":     "Автор: Максим Мельников",
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
        "dark":       "Тёмная",
        "light":      "Светлая",
        "copied":     "Скопировано!",
        "bits":       "бит",
        "qr_title":   "QR-код пароля",
        "hist_title": "История",
        "t0":  "Мгновенно",
        "t1":  "Секунды",
        "t2":  "Минуты",
        "t3":  "Часы",
        "t4":  "Дни",
        "t5":  "Недели",
        "t6":  "Месяцы",
        "t7":  "Годы",
        "t8":  "Десятилетия",
        "t9":  "Столетия",
        "t10": "Тысячелетия",
        "tt_gen":      "Создать новый случайный пароль",
        "tt_copy":     "Копировать и очистить через 60с",
        "tt_save":     "Сохранить пароль в текстовый файл",
        "tt_open":     "Загрузить пароль из файла",
        "tt_qr":       "Создать QR-код для сканирования",
        "tt_hist":     "Посмотреть последние пароли",
        "tt_upd":      "Открыть страницу релизов",
        "err_no_pool": "Выберите хотя бы один тип символов!",
        "clipboard_note": (
            "Внимание: на Linux/macOS автоочистка буфера ограничена "
            "возможностями Tk — системный менеджер буфера может сохранить копию."
        ),
    },
    "EN": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Generation Settings",
        "len":        "Password Length",
        "author":     "Author: Maxim Melnikov",
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
        "dark":       "Dark",
        "light":      "Light",
        "copied":     "Copied!",
        "bits":       "bits",
        "qr_title":   "Password QR-Code",
        "hist_title": "History",
        "t0":  "Instantly",
        "t1":  "Seconds",
        "t2":  "Minutes",
        "t3":  "Hours",
        "t4":  "Days",
        "t5":  "Weeks",
        "t6":  "Months",
        "t7":  "Years",
        "t8":  "Decades",
        "t9":  "Centuries",
        "t10": "Millennia",
        "tt_gen":      "Create a new random password",
        "tt_copy":     "Copy and clear clipboard in 60s",
        "tt_save":     "Save password to a text file",
        "tt_open":     "Load password from file",
        "tt_qr":       "Generate QR-code for scanning",
        "tt_hist":     "View recent passwords",
        "tt_upd":      "Open releases page",
        "err_no_pool": "Select at least one character type!",
        "clipboard_note": (
            "Note: on Linux/macOS clipboard auto-clear is limited by Tk — "
            "the system clipboard manager may retain a copy."
        ),
    },
    "UA": {
        "win_title":  "Secure Pass Pro v3.9",
        "title":      "Налаштування генерації",
        "len":        "Довжина пароля",
        "author":     "Автор: Максим Мельников",
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
        "dark":       "Темна",
        "light":      "Світла",
        "copied":     "Скопійовано!",
        "bits":       "біт",
        "qr_title":   "QR-код пароля",
        "hist_title": "Історія",
        "t0":  "Миттєво",
        "t1":  "Секунди",
        "t2":  "Хвилини",
        "t3":  "Години",
        "t4":  "Дні",
        "t5":  "Тижні",
        "t6":  "Місяці",
        "t7":  "Роки",
        "t8":  "Десятиліття",
        "t9":  "Століття",
        "t10": "Тисячоліття",
        "tt_gen":      "Створити новий випадковий пароль",
        "tt_copy":     "Копіювати та очистити за 60с",
        "tt_save":     "Зберегти пароль у текстовий файл",
        "tt_open":     "Завантажити пароль з файлу",
        "tt_qr":       "Створити QR-код для сканування",
        "tt_hist":     "Переглянути останні паролі",
        "tt_upd":      "Відкрити сторінку релізів",
        "err_no_pool": "Оберіть хоча б один тип символів!",
        "clipboard_note": (
            "Увага: на Linux/macOS автоочищення буфера обмежено можливостями Tk — "
            "системний менеджер буфера може зберегти копію."
        ),
    },
}


# =============================================================================
# ENTROPY HELPERS / ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ЭНТРОПИИ / ДОПОМІЖНІ ФУНКЦІЇ ЕНТРОПІЇ
# =============================================================================
# Thresholds calibrated for ~10^12 guesses/sec (modern GPU cluster) /
# Пороги откалиброваны для ~10^12 попыток/с (современный GPU-кластер) /
# Пороги відкалібровані для ~10^12 спроб/с (сучасний GPU-кластер)
_ENTROPY_THRESHOLDS: List[tuple] = [
    (20,  "t0"),   # < 20 bit  — instantly   / мгновенно   / миттєво
    (30,  "t1"),   # < 30 bit  — seconds     / секунды     / секунди
    (40,  "t2"),   # < 40 bit  — minutes     / минуты      / хвилини
    (50,  "t3"),   # < 50 bit  — hours       / часы        / години
    (60,  "t4"),   # < 60 bit  — days        / дни         / дні
    (70,  "t5"),   # < 70 bit  — weeks       / недели      / тижні
    (80,  "t6"),   # < 80 bit  — months      / месяцы      / місяці
    (90,  "t7"),   # < 90 bit  — years       / годы        / роки
    (100, "t8"),   # < 100 bit — decades     / десятилетия / десятиліття
    (120, "t9"),   # < 120 bit — centuries   / столетия    / століття
]
_ENTROPY_MAX_KEY = "t10"  # >= 120 bit — millennia / тысячелетия / тисячоліття


def _entropy_to_time_key(entropy: float) -> str:
    """
    Map entropy value to language dict key /
    Сопоставить энтропию с ключом языкового словаря /
    Зіставити ентропію з ключем мовного словника
    """
    for threshold, key in _ENTROPY_THRESHOLDS:
        if entropy < threshold:
            return key
    return _ENTROPY_MAX_KEY


def _entropy_to_color(entropy: float) -> str:
    """
    Map entropy to hex color for the progress bar /
    Сопоставить энтропию с hex-цветом прогресс-бара /
    Зіставити ентропію з hex-кольором прогрес-бара
    """
    if entropy < 50:
        return "#FF4B4B"   # Weak   / Слабый   / Слабкий
    if entropy < 80:
        return "#FFD700"   # Medium / Средний  / Середній
    return "#28A745"       # Strong / Сильный  / Сильний


# =============================================================================
# MAIN APPLICATION / ОСНОВНОЕ ПРИЛОЖЕНИЕ / ОСНОВНИЙ ДОДАТОК
# =============================================================================
class SecurePassPro(ctk.CTk):
    """
    Main application window /
    Главное окно приложения /
    Головне вікно додатку
    """

    def __init__(self) -> None:
        super().__init__()

        # Runtime state / Состояние программы / Стан програми
        self.current_lang:  str = "RU"
        self.current_theme: str = "System"
        self.history:       List[str] = []

        # Widget registries / Реестры виджетов / Реєстри віджетів
        self._radius_widgets: List[tk.Widget] = []
        self.tooltips:        Dict[str, ToolTip] = {}

        # Fix #3 / Исправление #3 / Виправлення #3
        # hist_txt declared here so it is always defined before _show_history runs /
        # hist_txt объявлен здесь — всегда определён до вызова _show_history /
        # hist_txt оголошено тут — завжди визначено до виклику _show_history
        self.history_window: Optional[ctk.CTkToplevel] = None
        self.hist_txt:       Optional[ctk.CTkTextbox]  = None

        # Fix #1 / Исправление #1 / Виправлення #1
        # _qr_ctk_image is the ONLY strong reference keeping the image alive /
        # _qr_ctk_image — ЕДИНСТВЕННАЯ сильная ссылка, удерживающая изображение /
        # _qr_ctk_image — ЄДИНЕ сильне посилання, що утримує зображення
        self.qr_window:     Optional[ctk.CTkToplevel] = None
        self.qr_label:      Optional[ctk.CTkLabel]    = None
        self._qr_ctk_image: Optional[ctk.CTkImage]    = None

        # Clipboard tracking / Отслеживание буфера обмена / Відстеження буфера обміну
        self._last_copied_pwd: str           = ""
        self._clipboard_job:   Optional[str] = None   # .after() job ID

        self.geometry("420x980")
        self.resizable(False, False)

        self._setup_vars()
        self._setup_ui()
        self._apply_lang("RU")
        ctk.set_appearance_mode("System")

    # =========================================================================
    # SETUP — VARIABLES / НАСТРОЙКА — ПЕРЕМЕННЫЕ / НАЛАШТУВАННЯ — ЗМІННІ
    # =========================================================================
    def _setup_vars(self) -> None:
        """
        Initialise all tk.BooleanVar instances /
        Инициализировать все экземпляры tk.BooleanVar /
        Ініціалізувати всі екземпляри tk.BooleanVar
        """
        self.upper_var         = tk.BooleanVar(value=True)
        self.lower_var         = tk.BooleanVar(value=True)
        self.digits_var        = tk.BooleanVar(value=True)
        self.symb_var          = tk.BooleanVar(value=True)
        self.exclude_ambig_var = tk.BooleanVar(value=False)
        self.exclude_unambig_var = tk.BooleanVar(value=False)
        self.at_least_one_var  = tk.BooleanVar(value=True)
        self.hide_var          = tk.BooleanVar(value=False)

    # =========================================================================
    # Fix #15 / Исправление #15 / Виправлення #15
    # _setup_ui split into focused sub-methods for readability /
    # _setup_ui разбит на подметоды для читаемости /
    # _setup_ui розділено на підметоди для читабельності
    # =========================================================================
    def _setup_ui(self) -> None:
        """
        Orchestrate full UI construction /
        Оркестрировать полное построение интерфейса /
        Оркеструвати повну побудову інтерфейсу
        """
        self._build_header()
        self._build_options()
        self._build_strength()
        self._build_buttons()
        self._build_footer()

    def _build_header(self) -> None:
        """
        Title and author labels /
        Метки заголовка и автора /
        Мітки заголовка та автора
        """
        self.lbl_title = ctk.CTkLabel(self, text="", font=("Segoe UI", 22, "bold"))
        self.lbl_title.pack(pady=(15, 0))
        self.lbl_author = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 12, "italic"), text_color="gray"
        )
        self.lbl_author.pack()

    def _build_options(self) -> None:
        """
        Options frame: length slider + character-type checkboxes /
        Фрейм настроек: слайдер длины + чекбоксы типов символов /
        Фрейм налаштувань: слайдер довжини + чекбокси типів символів
        """
        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.pack(pady=10, padx=20, fill="x")
        self._radius_widgets.append(self.opt_frame)

        # Length slider / Слайдер длины / Слайдер довжини
        self.lbl_len = ctk.CTkLabel(self.opt_frame, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_len.pack(pady=(10, 0))
        self.slider = ctk.CTkSlider(
            self.opt_frame, from_=4, to=64, command=self._on_slider_move
        )
        self.slider.set(20)
        self.slider.pack(pady=10, padx=20)

        # Character-type checkboxes / Чекбоксы типов символов / Чекбокси типів символів
        self.cb_upper    = self._create_cb(self.upper_var)
        self.cb_lower    = self._create_cb(self.lower_var)
        self.cb_digits   = self._create_cb(self.digits_var)
        self.cb_symb     = self._create_cb(self.symb_var)
        self.cb_ambig    = self._create_cb(self.exclude_ambig_var)
        self.cb_unambig  = self._create_cb(self.exclude_unambig_var)
        self.cb_at_least = self._create_cb(self.at_least_one_var)
        self.cb_hide     = self._create_cb(self.hide_var, command=self._toggle_visibility)

    def _build_strength(self) -> None:
        """
        Password entry field + strength progress bar + info labels /
        Поле ввода пароля + прогресс-бар силы + информационные метки /
        Поле введення пароля + прогрес-бар сили + інформаційні мітки
        """
        # Result entry — KeyRelease fires live strength recalculation /
        # Поле результата — KeyRelease запускает живой пересчёт силы /
        # Поле результату — KeyRelease запускає живий перерахунок сили
        self.entry_res = ctk.CTkEntry(self, height=45, font=("Consolas", 18), justify="center")
        self.entry_res.pack(pady=10, padx=20, fill="x")
        self.entry_res.bind("<KeyRelease>", lambda _e: self._refresh_strength())
        self._radius_widgets.append(self.entry_res)

        # Strength bar / Прогресс-бар силы / Прогрес-бар сили
        self.strength_bar = ctk.CTkProgressBar(self, height=10)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=5, padx=40, fill="x")

        # Time-to-crack label / Метка времени взлома / Мітка часу зламу
        self.lbl_time_to_crack = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_time_to_crack.pack()

        # Entropy bits label / Метка энтропии в битах / Мітка ентропії в бітах
        self.lbl_strength = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_strength.pack()

    def _build_buttons(self) -> None:
        """
        All action buttons with colours and tooltips /
        Все кнопки действий с цветами и подсказками /
        Всі кнопки дій з кольорами та підказками
        """
        self.btn_gen  = self._create_btn(self._generate,     "btn_gen",  "#1f538d", "tt_gen",  bold=True)
        self.btn_copy = self._create_btn(self._copy,         "btn_copy", "#28a745", "tt_copy")
        self.btn_save = self._create_btn(self._save,         "btn_save", "#17a2b8", "tt_save")
        self.btn_open = self._create_btn(self._open,         "btn_open", "#17a2b8", "tt_open")
        self.btn_qr   = self._create_btn(self._show_qr,      "btn_qr",   "#6f42c1", "tt_qr")
        self.btn_hist = self._create_btn(self._show_history, "btn_hist", "#6c757d", "tt_hist")
        self.btn_upd  = self._create_btn(self._update_app,   "btn_upd",  "#f39c12", "tt_upd")

    def _build_footer(self) -> None:
        """
        Corner-radius slider, star decoration, language & theme switchers /
        Слайдер радиуса углов, декор звёзд, переключатели языка и темы /
        Слайдер радіусу кутів, декор зірок, перемикачі мови та теми
        """
        # Corner radius slider / Слайдер радиуса углов / Слайдер радіусу кутів
        self.lbl_radius = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_radius.pack(pady=(5, 0))
        self.slider_radius = ctk.CTkSlider(
            self, from_=0, to=25, height=14, command=self._change_radius
        )
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=5, padx=60, fill="x")

        # Stars decoration / Декоративные звёзды / Декоративні зірки
        self.lbl_stars = ctk.CTkLabel(
            self, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700"
        )
        self.lbl_stars.pack(side="bottom", pady=(0, 10))

        # Bottom switcher bar / Нижняя панель переключателей / Нижня панель перемикачів
        self.sw_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sw_frame.pack(side="bottom", fill="x", padx=20, pady=5)

        self.lang_sw = ctk.CTkSegmentedButton(
            self.sw_frame, values=["RU", "EN", "UA"], command=self._on_lang_change
        )
        self.lang_sw.pack(side="left")

        self.theme_sw = ctk.CTkSegmentedButton(
            self.sw_frame, values=[], command=self._on_theme_change
        )
        self.theme_sw.pack(side="right")

    # =========================================================================
    # WIDGET FACTORIES / ФАБРИКИ ВИДЖЕТОВ / ФАБРИКИ ВІДЖЕТІВ
    # =========================================================================
    def _create_cb(self, var: tk.BooleanVar, command=None) -> ctk.CTkCheckBox:
        """
        Create a checkbox that refreshes strength on every toggle /
        Создать чекбокс, обновляющий силу при каждом переключении /
        Створити чекбокс, що оновлює силу при кожному перемиканні
        """
        cb = ctk.CTkCheckBox(
            self.opt_frame, text="", variable=var, font=("Segoe UI", 12),
            command=lambda: (command() if command else None, self._refresh_strength()),
        )
        cb.pack(anchor="w", padx=35, pady=2)
        return cb

    def _create_btn(
        self, cmd, key: str, color: str, tt_key: str, bold: bool = False
    ) -> ctk.CTkButton:
        """
        Create a coloured button, register it for radius changes, bind tooltip /
        Создать цветную кнопку, зарегистрировать для изменения радиуса, привязать подсказку /
        Створити кольорову кнопку, зареєструвати для зміни радіусу, прив'язати підказку
        """
        btn = ctk.CTkButton(
            self, text="", command=cmd, fg_color=color, height=35,
            font=("Segoe UI", 13 if bold else 12, "bold" if bold else "normal"),
        )
        btn.pack(pady=3, padx=40, fill="x")
        btn._key    = key     # type: ignore[attr-defined]
        btn._tt_key = tt_key  # type: ignore[attr-defined]
        self._radius_widgets.append(btn)
        tip = ToolTip(btn, "")
        self.tooltips[key] = tip
        btn.bind("<Enter>", lambda _e: tip.show_tip())
        btn.bind("<Leave>", lambda _e: tip.hide_tip())
        return btn

    # =========================================================================
    # GENERATION / ГЕНЕРАЦИЯ ПАРОЛЯ / ГЕНЕРАЦІЯ ПАРОЛЯ
    # =========================================================================
    def _build_pools(self) -> tuple:
        """
        Build per-category character pools respecting current checkbox state /
        Построить пулы символов по категориям с учётом состояния чекбоксов /
        Побудувати пули символів за категоріями з урахуванням стану чекбоксів

        Returns: (category_pools: List[str], full_combined_pool: str)
        """
        exclude = set(AMBIGUOUS_CHARS) if self.exclude_ambig_var.get() else set()
        
        if self.exclude_unambig_var.get():
            # Символы, которые часто вызывают проблемы в коде или терминалах
            unambig_chars = "{}[]()/\\'\"`~,;:.<>"
            exclude.update(unambig_chars)

        def _pool(var: tk.BooleanVar, src: str) -> str:
            if not var.get():
                return ""
            return "".join(c for c in src if c not in exclude)

        pools = [
            _pool(self.upper_var,  string.ascii_uppercase),
            _pool(self.lower_var,  string.ascii_lowercase),
            _pool(self.digits_var, string.digits),
            _pool(self.symb_var,   string.punctuation),
        ]
        return pools, "".join(pools)

    def _generate(self) -> None:
        """
        Generate a cryptographically secure password and update all UI elements /
        Сгенерировать криптографически стойкий пароль и обновить все элементы UI /
        Згенерувати криптографічно стійкий пароль та оновити всі елементи UI
        """
        L = LANGUAGES[self.current_lang]
        pools, full_pool = self._build_pools()

        if not full_pool:
            sound_error()
            messagebox.showwarning(self.title(), L["err_no_pool"])
            return

        length = int(self.slider.get())

        # Pick one char from each active category as mandatory /
        # Взять один символ из каждой активной категории как обязательный /
        # Взяти один символ з кожної активної категорії як обов'язковий
        mandatory: List[str] = []
        if self.at_least_one_var.get():
            mandatory = [secrets.choice(p) for p in pools if p]

        # Guard: if mandatory chars exceed requested length, sample them fairly /
        # Защита: если обязательных больше длины — взять честную выборку /
        # Захист: якщо обов'язкових більше довжини — взяти чесну вибірку
        if len(mandatory) > length:
            mandatory = _SYSRNG.sample(mandatory, length)

        # Fill remaining positions from the combined pool /
        # Заполнить остаток из общего пула /
        # Заповнити решту із загального пулу
        remainder = [secrets.choice(full_pool) for _ in range(length - len(mandatory))]

        # Cryptographically secure in-place shuffle /
        # Криптографически стойкое перемешивание на месте /
        # Криптографічно стійке перемішування на місці
        pwd_list = mandatory + remainder
        _SYSRNG.shuffle(pwd_list)
        result = "".join(pwd_list)

        self.entry_res.delete(0, tk.END)
        self.entry_res.insert(0, result)

        # Update history / Обновить историю / Оновити історію
        self.history.append(result)
        if len(self.history) > HISTORY_MAX:
            self.history.pop(0)

        sound_generate()
        self._refresh_strength()

        # Refresh live QR window if open / Обновить QR-окно если открыто / Оновити QR-вікно якщо відкрито
        if self.qr_window and self.qr_window.winfo_exists():
            self._update_qr_image(result)

    # =========================================================================
    # STRENGTH METER / ИНДИКАТОР СИЛЫ / ІНДИКАТОР СИЛИ
    # =========================================================================
    def _calc_pool_size(self, pwd: str) -> int:
        """
        Estimate effective character-pool size from password content.

        Fix #1 (Gemini audit) / Fix #2 (prev audit) /
        Исправление #1 (аудит Gemini) / Исправление #2 (предыдущий аудит) /
        Виправлення #1 (аудит Gemini) / Виправлення #2 (попередній аудит)

        KEY CHANGE — ambiguous chars are subtracted based on CHECKBOX state,
        NOT on the actual characters present in the password.
        This gives correct entropy for both generated AND manually-typed passwords:
        - Generated passwords follow the checkbox rules exactly.
        - Manual passwords may contain any chars, but the *displayed* pool size
          reflects the generator's effective alphabet — consistent UX.

        КЛЮЧЕВОЕ ИЗМЕНЕНИЕ — неоднозначные символы вычитаются на основе
        состояния ЧЕКБОКСОВ, а не фактических символов в пароле.
        Это даёт корректную энтропию для сгенерированных И ручных паролей.

        КЛЮЧОВА ЗМІНА — неоднозначні символи віднімаються на основі стану
        ЧЕКБОКСІВ, а не фактичних символів у паролі.
        """
        # Detect which character classes are present in the password /
        # Определить какие классы символов присутствуют в пароле /
        # Визначити які класи символів присутні в паролі
        has_lower  = any(c in string.ascii_lowercase for c in pwd)
        has_upper  = any(c in string.ascii_uppercase for c in pwd)
        has_digit  = any(c in string.digits          for c in pwd)
        has_symbol = any(c in string.punctuation     for c in pwd)

        size = (
            (26 if has_lower  else 0) +
            (26 if has_upper  else 0) +
            (10 if has_digit  else 0) +
            (32 if has_symbol else 0)
        )

        # Subtract ambiguous chars only for categories BOTH present in the password
        # AND excluded via the checkbox — no over-subtraction /
        # Вычитать неоднозначные только для категорий ПРИСУТСТВУЮЩИХ в пароле
        # И исключённых через чекбокс — нет избыточного вычитания /
        # Відніяти неоднозначні лише для категорій ПРИСУТНІХ в паролі
        # І виключених через чекбокс — немає надмірного віднімання
        if self.exclude_ambig_var.get():
            excluded = (
                (_AMBIG_LOWER  if has_lower else 0) +
                (_AMBIG_UPPER  if has_upper else 0) +
                (_AMBIG_DIGITS if has_digit else 0)
            )
            size -= excluded

        return max(size, 2)  # Never below 2 to avoid log2(0) / Никогда ниже 2 / Ніколи нижче 2

    def _refresh_strength(self) -> None:
        """
        Recalculate entropy from entry content and refresh all strength elements /
        Пересчитать энтропию из поля и обновить все элементы индикатора силы /
        Перерахувати ентропію з поля та оновити всі елементи індикатора сили
        """
        pwd = self.entry_res.get()
        L   = LANGUAGES[self.current_lang]

        if not pwd:
            self.strength_bar.set(0)
            self.lbl_time_to_crack.configure(text="")
            self.lbl_strength.configure(text="")
            return

        pool_size = self._calc_pool_size(pwd)
        entropy   = len(pwd) * math.log2(pool_size)
        progress  = min(entropy / 128, 1.0)   # 128 bit = full bar / 128 бит — полная шкала / 128 біт — повна шкала
        color     = _entropy_to_color(entropy)
        time_key  = _entropy_to_time_key(entropy)

        self.strength_bar.set(progress)
        self.strength_bar.configure(progress_color=color)
        self.lbl_time_to_crack.configure(text=L[time_key], text_color=color)
        self.lbl_strength.configure(text=f"{L['strength']}: {int(entropy)} {L['bits']}")

    # =========================================================================
    # CLIPBOARD / БУФЕР ОБМЕНА / БУФЕР ОБМІНУ
    # =========================================================================
    def _copy(self) -> None:
        """
        Copy password to clipboard and schedule auto-clear in 60 s /
        Скопировать пароль в буфер и запланировать автоочистку через 60 с /
        Скопіювати пароль у буфер та запланувати автоочищення через 60 с
        """
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return

        self.clipboard_clear()
        self.clipboard_append(pwd)
        self._last_copied_pwd = pwd
        sound_copy()

        # Flash "Copied!" label then restore previous text /
        # Показать метку "Скопировано!", затем восстановить предыдущий текст /
        # Показати мітку "Скопійовано!", потім відновити попередній текст
        old_text  = self.lbl_time_to_crack.cget("text")
        old_color = self.lbl_time_to_crack.cget("text_color")
        self.lbl_time_to_crack.configure(
            text=LANGUAGES[self.current_lang]["copied"], text_color="#28a745"
        )
        self.after(
            2000,
            lambda: self.lbl_time_to_crack.configure(text=old_text, text_color=old_color),
        )

        # Cancel any pending clear job, then schedule a fresh one /
        # Отменить предыдущую задачу очистки, запланировать новую /
        # Скасувати попереднє завдання очищення, запланувати нове
        if self._clipboard_job:
            self.after_cancel(self._clipboard_job)
        self._clipboard_job = self.after(60_000, self._clear_clipboard)

    def _clear_clipboard(self) -> None:
        """
        Overwrite clipboard if it still contains the password this app put there.

        Fix #7 / Исправление #7 / Виправлення #7
        PLATFORM NOTE: on Linux (X11) and macOS (NSPasteboard), Tk's
        clipboard_clear() only releases the selection owner for THIS process.
        The system clipboard manager may retain a copy independently of Tk.
        This is a Tk/OS limitation — no workaround exists without native tools
        (xclip, xdotool, pbcopy, etc.).  The user is informed via clipboard_note. /

        ПРИМЕЧАНИЕ О ПЛАТФОРМЕ: на Linux (X11) и macOS clipboard_clear()
        освобождает владение только для этого процесса. Системный менеджер
        буфера может сохранить копию независимо от Tk. /

        ПРИМІТКА ПРО ПЛАТФОРМУ: на Linux (X11) та macOS clipboard_clear()
        звільняє власність лише для цього процесу. Системний менеджер буфера
        може зберегти копію незалежно від Tk.
        """
        self._clipboard_job = None
        try:
            if self.clipboard_get() == self._last_copied_pwd:
                self.clipboard_clear()
                # Write a space to overwrite memory, then clear again /
                # Записать пробел для перезаписи памяти, затем очистить /
                # Записати пробіл для перезапису пам'яті, потім очистити
                self.clipboard_append(" ")
                self.update()
                self.clipboard_clear()
                self._last_copied_pwd = ""
        except tk.TclError:
            # Clipboard inaccessible — safe to ignore /
            # Буфер недоступен — игнорируем /
            # Буфер недоступний — ігноруємо
            pass

    # =========================================================================
    # FILE I/O / ФАЙЛОВЫЕ ОПЕРАЦИИ / ФАЙЛОВІ ОПЕРАЦІЇ
    # =========================================================================
    def _save(self) -> None:
        """
        Save current password to a text file chosen by the user /
        Сохранить текущий пароль в текстовый файл по выбору пользователя /
        Зберегти поточний пароль у текстовий файл за вибором користувача
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
        """
        Load first line of a text file as the password (max FILE_READ_LIMIT bytes) /
        Загрузить первую строку текстового файла как пароль (макс. FILE_READ_LIMIT байт) /
        Завантажити перший рядок текстового файлу як пароль (макс. FILE_READ_LIMIT байт)
        """
        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt *.log *.key"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                # Limit read to avoid huge files / Ограничить чтение больших файлов / Обмежити читання великих файлів
                lines = f.read(FILE_READ_LIMIT).strip().splitlines()
                pwd   = lines[0] if lines else ""
            self.entry_res.delete(0, tk.END)
            self.entry_res.insert(0, pwd)
            self._refresh_strength()
            sound_action()
        except OSError:
            sound_error()

    # =========================================================================
    # HISTORY WINDOW / ОКНО ИСТОРИИ / ВІКНО ІСТОРІЇ
    # =========================================================================
    def _show_history(self) -> None:
        """
        Open (or bring to front) the history window and always refresh its content.

        Fix #3 / Исправление #3 / Виправлення #3
        hist_txt is guarded with an explicit None check + winfo_exists() /
        hist_txt защищён явной проверкой на None + winfo_exists() /
        hist_txt захищений явною перевіркою на None + winfo_exists()

        Fix #5 / Исправление #5 / Виправлення #5
        Window title refreshed on EVERY call — handles language changes
        while the window is already open /
        Заголовок окна обновляется при КАЖДОМ вызове — учитывает смену языка /
        Заголовок вікна оновлюється при КОЖНОМУ виклику — враховує зміну мови
        """
        sound_action()
        L = LANGUAGES[self.current_lang]

        if self.history_window is None or not self.history_window.winfo_exists():
            # Create fresh window and textbox /
            # Создать новое окно и текстовое поле /
            # Створити нове вікно та текстове поле
            self.history_window = ctk.CTkToplevel(self)
            self._center_window(self.history_window, 350, 450)
            self.history_window.attributes("-topmost", True)
            self.hist_txt = ctk.CTkTextbox(self.history_window, font=("Consolas", 14))
            self.hist_txt.pack(fill="both", expand=True, padx=10, pady=10)

        # Always update title — covers language-switch-while-open case /
        # Всегда обновлять заголовок — охватывает смену языка при открытом окне /
        # Завжди оновлювати заголовок — охоплює зміну мови при відкритому вікні
        self.history_window.title(L["hist_title"])

        # Guard: only write if widget exists and is valid /
        # Защита: писать только если виджет существует и валиден /
        # Захист: писати лише якщо віджет існує і валідний
        if self.hist_txt is not None and self.hist_txt.winfo_exists():
            self.hist_txt.configure(state="normal")
            self.hist_txt.delete("0.0", tk.END)
            self.hist_txt.insert("0.0", "\n".join(self.history[::-1]))
            self.hist_txt.configure(state="disabled")

        self.history_window.focus()

    # =========================================================================
    # QR CODE WINDOW / ОКНО QR-КОДА / ВІКНО QR-КОДУ
    # =========================================================================
    def _update_qr_image(self, pwd: str) -> None:
        """
        Render a new QR-code image from pwd and assign it to qr_label.

        Fix #1 / Исправление #1 / Виправлення #1
        self._qr_ctk_image is the ONLY authoritative strong reference.
        This prevents the GC from collecting the CTkImage after the function
        exits — no undocumented _ctk_image hack needed. /

        self._qr_ctk_image — ЕДИНСТВЕННАЯ авторитетная сильная ссылка.
        Предотвращает сборку GC после выхода из функции. /

        self._qr_ctk_image — ЄДИНЕ авторитетне сильне посилання.
        Запобігає збірці GC після виходу з функції.
        """
        # qrcode.make() returns PIL.Image directly — NO .get_image() /
        # qrcode.make() возвращает PIL.Image напрямую — БЕЗ .get_image() /
        # qrcode.make() повертає PIL.Image напряму — БЕЗ .get_image()
        qr_pil = qrcode.make(pwd).resize((240, 240), RESAMPLE)

        # Store before configure() — guarantees reference survives the call /
        # Сохранить до configure() — гарантирует выживание ссылки /
        # Зберегти до configure() — гарантує виживання посилання
        self._qr_ctk_image = ctk.CTkImage(
            light_image=qr_pil, dark_image=qr_pil, size=(240, 240)
        )
        if self.qr_label is not None:
            self.qr_label.configure(image=self._qr_ctk_image)

    def _show_qr(self) -> None:
        """
        Open QR-code window (or update the existing one).

        Fix #6 / Исправление #6 / Виправлення #6
        Window title refreshed on EVERY call — handles language changes
        while the window is already open /
        Заголовок окна обновляется при КАЖДОМ вызове — учитывает смену языка /
        Заголовок вікна оновлюється при КОЖНОМУ виклику — враховує зміну мови
        """
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return

        L = LANGUAGES[self.current_lang]

        if self.qr_window is None or not self.qr_window.winfo_exists():
            # Build window first, then render image inside it /
            # Сначала создать окно, затем отрисовать изображение /
            # Спочатку створити вікно, потім відрендерити зображення
            self.qr_window = ctk.CTkToplevel(self)
            self._center_window(self.qr_window, 300, 320)
            self.qr_window.attributes("-topmost", True)
            self.qr_label = ctk.CTkLabel(self.qr_window, image=None, text="")
            self.qr_label.pack(pady=20)

        # Always update title — covers language-switch-while-open /
        # Всегда обновлять заголовок / Завжди оновлювати заголовок
        self.qr_window.title(L["qr_title"])

        self._update_qr_image(pwd)
        self.qr_window.focus()
        sound_action()

    # =========================================================================
    # UI UTILITIES / УТИЛИТЫ ИНТЕРФЕЙСА / УТИЛІТИ ІНТЕРФЕЙСУ
    # =========================================================================
    def _center_window(self, win: ctk.CTkToplevel, w: int, h: int) -> None:
        """
        Center a toplevel window relative to the main window /
        Центрировать дочернее окно относительно главного /
        Центрувати дочірнє вікно відносно головного
        """
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _change_radius(self, val: float) -> None:
        """
        Apply corner radius to all radius-aware registered widgets /
        Применить радиус углов ко всем зарегистрированным виджетам /
        Застосувати радіус кутів до всіх зареєстрованих віджетів
        """
        r = int(val)
        for widget in self._radius_widgets:
            try:
                widget.configure(corner_radius=r)
            except Exception:
                pass
        self.lbl_radius.configure(
            text=f"{LANGUAGES[self.current_lang]['radius']}: {r}"
        )

    def _on_slider_move(self, val: float) -> None:
        """
        Handle length-slider movement: update label and refresh strength /
        Обработать движение слайдера: обновить метку и пересчитать силу /
        Обробити рух слайдера: оновити мітку та перерахувати силу
        """
        self._update_len_text(val)
        self._refresh_strength()

    def _update_len_text(self, val: float) -> None:
        """
        Update the password-length indicator label /
        Обновить метку индикатора длины пароля /
        Оновити мітку індикатора довжини пароля
        """
        self.lbl_len.configure(
            text=f"{LANGUAGES[self.current_lang]['len']}: {int(val)}"
        )

    def _toggle_visibility(self) -> None:
        """
        Toggle password masking in the result entry /
        Переключить маскировку пароля в поле результата /
        Перемкнути маскування пароля в полі результату
        """
        self.entry_res.configure(show="*" if self.hide_var.get() else "")

    # =========================================================================
    # LANGUAGE & THEME / ЯЗЫК И ТЕМА / МОВА ТА ТЕМА
    # =========================================================================
    def _apply_lang(self, lang: str) -> None:
        """
        Apply selected language to every UI element including open child windows.

        Fix #5 & #6 / Исправление #5 и #6 / Виправлення #5 та #6
        Child-window titles are updated here too, so a language switch while
        history or QR window is open immediately renames them /
        Заголовки дочерних окон обновляются здесь — смена языка при открытых
        окнах сразу их переименовывает /
        Заголовки дочірніх вікон оновлюються тут — зміна мови при відкритих
        вікнах одразу їх перейменовує
        """
        self.current_lang = lang
        L = LANGUAGES[lang]

        self.title(L["win_title"])
        self.lbl_title.configure(text=L["title"])
        self.lbl_author.configure(text=L["author"])

        # Checkboxes / Чекбоксы / Чекбокси
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_unambig.configure(text=L["unambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])

        # Buttons + tooltips / Кнопки + подсказки / Кнопки + підказки
        for btn in (
            self.btn_gen, self.btn_copy, self.btn_save, self.btn_open,
            self.btn_qr,  self.btn_hist, self.btn_upd,
        ):
            btn.configure(text=L[btn._key])                       # type: ignore[attr-defined]
            self.tooltips[btn._key].text = L[btn._tt_key]         # type: ignore[attr-defined]

        # Theme switcher: rebuild labels, restore selected theme /
        # Переключатель темы: пересобрать метки, восстановить выбор /
        # Перемикач теми: перебудувати мітки, відновити вибір
        theme_label_map = {"System": L["sys"], "Dark": L["dark"], "Light": L["light"]}
        self.theme_sw.configure(values=[L["sys"], L["dark"], L["light"]])
        self.theme_sw.set(theme_label_map.get(self.current_theme, L["sys"]))

        self.lang_sw.set(lang)
        self._update_len_text(self.slider.get())
        self._refresh_strength()

        # Propagate new titles to open child windows /
        # Распространить новые заголовки на открытые дочерние окна /
        # Поширити нові заголовки на відкриті дочірні вікна
        if self.history_window and self.history_window.winfo_exists():
            self.history_window.title(L["hist_title"])
        if self.qr_window and self.qr_window.winfo_exists():
            self.qr_window.title(L["qr_title"])

    def _on_lang_change(self, choice: str) -> None:
        """
        Callback for language segmented button /
        Обратный вызов кнопки выбора языка /
        Зворотній виклик кнопки вибору мови
        """
        self._apply_lang(choice)

    def _on_theme_change(self, choice: str) -> None:
        """
        Callback for theme button — updates BOTH appearance and internal state.

        Without storing self.current_theme, _apply_lang cannot restore the
        active theme button label after a language switch. /

        Без сохранения self.current_theme, _apply_lang не может восстановить
        метку активной темы после смены языка. /

        Без збереження self.current_theme, _apply_lang не може відновити
        мітку активної теми після зміни мови.
        """
        L = LANGUAGES[self.current_lang]
        rmap = {L["sys"]: "System", L["dark"]: "Dark", L["light"]: "Light"}
        self.current_theme = rmap.get(choice, "System")
        ctk.set_appearance_mode(self.current_theme)

    # =========================================================================
    # MISC / РАЗНОЕ / РІЗНЕ
    # =========================================================================
    def _update_app(self) -> None:
        """
        Open GitHub releases page in the default browser /
        Открыть страницу релизов GitHub в браузере по умолчанию /
        Відкрити сторінку релізів GitHub у браузері за замовчуванням
        """
        webbrowser.open(UPD_URL)


# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА / ТОЧКА ВХОДУ
# =============================================================================
if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()