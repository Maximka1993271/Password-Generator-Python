import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import os
import sys
import platform
import math

# =============================================================================
# HIDE CONSOLE WINDOW / СКРЫТИЕ КОНСОЛЬНОГО ОКНА / ПРИХОВАННЯ КОНСОЛЬНОГО ВІКНА
# =============================================================================
# This block hides the black console window on Windows when running as .py or .exe
# without needing to recompile with PyInstaller --noconsole flag every time.
#
# Этот блок скрывает чёрное консольное окно на Windows при запуске как .py или .exe,
# без необходимости каждый раз пересобирать с флагом PyInstaller --noconsole.
#
# Цей блок приховує чорне консольне вікно на Windows при запуску як .py або .exe,
# без необхідності щоразу перезбирати з прапором PyInstaller --noconsole.
if platform.system() == "Windows":
    try:
        import ctypes
        # SW_HIDE = 0 — hide the console window associated with this process
        # SW_HIDE = 0 — скрывает консольное окно, связанное с этим процессом
        # SW_HIDE = 0 — приховує консольне вікно, пов'язане з цим процесом
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0  # 0 = SW_HIDE
        )
    except Exception:
        pass  # Non-critical — app still works if this fails / Некритично — приложение работает и без этого / Некритично — програма працює і без цього

# =============================================================================
# DEPENDENCIES & PATHS / ЗАВИСИМОСТИ И ПУТИ / ЗАЛЕЖНОСТІ ТА ШЛЯХИ
# =============================================================================

def resource_path(relative_path):
    """
    Get absolute path to resource — works for dev and PyInstaller bundle.
    Получение пути к ресурсам — работает и в разработке, и в EXE-сборке.
    Отримання шляху до ресурсів — працює і в розробці, і в EXE-збірці.

    FIX #13: was `except Exception` — narrowed to `except AttributeError`
             because sys._MEIPASS only raises AttributeError when not bundled.
    ИСПРАВЛЕНИЕ #13: был `except Exception` — сужен до `except AttributeError`,
             т.к. sys._MEIPASS бросает только AttributeError вне PyInstaller.
    ВИПРАВЛЕННЯ #13: був `except Exception` — звужено до `except AttributeError`,
             бо sys._MEIPASS кидає лише AttributeError поза PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:      # ← FIX #13: was bare `except Exception`
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


try:
    import qrcode
    from PIL import ImageTk, Image
except ImportError:
    # Error message if libraries are missing / Ошибка при отсутствии библиотек / Помилка при відсутності бібліотек
    print("Missing dependencies! Please run: pip install qrcode[pil] pillow")
    sys.exit(1)

# High DPI support (Windows only) / Поддержка высокого DPI (только Windows) / Підтримка високого DPI (лише Windows)
if platform.system() == "Windows":
    # FIX #1: winsound is NOT imported here at module level.
    # It was previously imported globally inside the Windows-only block,
    # which left the name `winsound` undefined on Linux/macOS and caused
    # NameError when play_sound() was called on those platforms.
    # Solution: import winsound lazily inside play_sound() with try/except.
    #
    # ИСПРАВЛЕНИЕ #1: winsound НЕ импортируется здесь на уровне модуля.
    # Раньше он импортировался глобально внутри Windows-блока, что оставляло
    # имя `winsound` неопределённым на Linux/macOS и вызывало NameError
    # при вызове play_sound() на этих платформах.
    # Решение: импортировать winsound лениво внутри play_sound() через try/except.
    #
    # ВИПРАВЛЕННЯ #1: winsound НЕ імпортується тут на рівні модуля.
    # Раніше він імпортувався глобально всередині Windows-блоку, що залишало
    # ім'я `winsound` невизначеним на Linux/macOS і спричиняло NameError
    # при виклику play_sound() на цих платформах.
    # Рішення: імпортувати winsound ліниво всередині play_sound() через try/except.
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


# =============================================================================
# CONSTANTS & LANGUAGES / КОНСТАНТЫ И ЯЗЫКИ / КОНСТАНТИ ТА МОВИ
# =============================================================================

UPDATE_URL  = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv1.9.7/Secure_Pass_Pro.exe"
GITHUB_URL  = "https://github.com/Maximka1993271/Password-Generator-Python"

# MD5 brute-force speed on modern GPU / Скорость перебора MD5 на современном GPU / Швидкість перебору MD5 на сучасному GPU
CRACK_SPEED = 100_000_000_000

LANGUAGES = {
    'ru': {
        # Menu bar / Строка меню / Рядок меню
        'menu_file': "Файл",
        'menu_opts': "Опции",
        'menu_about': "О программе",

        # File menu / Меню файла / Меню файлу
        'save':    "Сохранить (Ctrl+S)",
        'save_as': "Сохранить как...",
        'exit':    "Выход",

        # Options menu / Меню параметров / Меню параметрів
        'themes': "Темы",
        'lang':   "Язык",
        'light':  "Светлая",
        'dark':   "Тёмная",
        'system': "Системная",

        # About menu / Меню «О программе» / Меню «Про програму»
        'author_btn':        "Автор программы",
        'author_title':      "Автор",
        'author_main':       "Максим Мельников",
        'author_label_text': "Программу разработал:",
        'ver_btn':           "Версия программы",
        'ver_title':         "Версия",
        'ver_main':          "v1.9.7 Stable",
        'ver_label_text':    "Текущая сборка:",
        'update_btn':        "Проверить обновления",
        'site_btn':          "Сайт проекта (GitHub)",

        # Main UI labels / Метки интерфейса / Мітки інтерфейсу
        'header':    "Настройки генерации",
        'len_label': "Длина пароля (4-64):",

        # Checkboxes / Флажки / Прапорці
        'upper':     "Заглавные буквы",
        'lower':     "Строчные буквы",
        'digits':    "Цифры",
        'symb':      "Спецсимволы",
        'exclude':   "Исключить похожие (0/O, 1/l/I)",
        'ambiguous': "Исключить неоднозначные",
        'hide':      "Скрывать символы",
        'at_least':  "Минимум 1 из каждой категории",

        # Buttons / Кнопки / Кнопки
        # FIX #5: placeholder {} added so .format(n) actually substitutes the count.
        # ИСПРАВЛЕНИЕ #5: добавлен {} чтобы .format(n) подставлял реальное количество.
        # ВИПРАВЛЕННЯ #5: додано {}, щоб .format(n) підставляв реальну кількість.
        'gen_btn':     "СГЕНЕРИРОВАТЬ (Ctrl+G)",
        'open_btn':    "ОТКРЫТЬ ФАЙЛ (Ctrl+O)",
        'copy_btn':    "КОПИРОВАТЬ ПАРОЛЬ",
        'qr_btn':      "QR-КОД ПАРОЛЯ",
        'history_btn': "ИСТОРИЯ ({})",   # ← FIX #5: was "ИСТОРИЯ (5)" — hardcoded, no {}

        # History window / Окно истории / Вікно історії
        'history_title': "История паролей",
        'history_empty': "История пуста",

        # Strength / QR / Сложность / QR / Складність / QR
        'strength': "Сложность",
        'qr_scan':  "Отсканируйте камерой",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],

        # Warnings / Предупреждения / Попередження
        'warn':        "Внимание",
        'min_len':     "Длина должна быть от 4 до 64",
        'err':         "Ошибка",
        'choose_set':  "Выберите наборы символов",
        'check_input': "Проверьте ввод",

        # Success / Успех / Успіх
        'success':  "Успешно!",
        'pwd_done': "Пароль скопирован в буфер",

        # File dialog strings / Строки диалога файла / Рядки діалогу файлу
        'save_title': "Сохранить как",
        'open_title': "Открыть пароль",
        'text_files': "Текстовые файлы",
        'all_files':  "Все файлы",
        'saved':      "Файл сохранён.",
        'no_pwd':     "Нет пароля для сохранения.",
        'empty_file': "Файл пуст!",

        # Crack time / Время взлома / Час злому
        'crack_instantly': "Мгновенно (MD5)",
        'crack_seconds':   "~{} сек. (MD5)",
        'crack_minutes':   "~{} мин. (MD5)",
        'crack_hours':     "~{} ч. (MD5)",
        'crack_days':      "~{} дн. (MD5)",
        'crack_years':     "~{} лет (MD5)",
        'crack_centuries': "~{} веков (MD5)",
        'crack_never':     "Почти невозможно (MD5)",

        # Window titles for info dialogs / Заголовки информационных окон / Заголовки інформаційних вікон
        # FIX #2 & #4: dedicated title keys so show_info() never does L['success'] as a window title
        # ИСПРАВЛЕНИЕ #2 и #4: отдельные ключи заголовков, чтобы show_info() не использовал L['success'] как заголовок окна
        # ВИПРАВЛЕННЯ #2 та #4: окремі ключі заголовків, щоб show_info() не використовував L['success'] як заголовок вікна
        'dlg_title_success': "Успешно!",
        'dlg_title_copied':  "Буфер обмена",
    },

    'en': {
        # Menu bar / Строка меню / Рядок меню
        'menu_file':  "File",
        'menu_opts':  "Options",
        'menu_about': "About",

        # File menu / Меню файла / Меню файлу
        'save':    "Save (Ctrl+S)",
        'save_as': "Save as...",
        'exit':    "Exit",

        # Options menu / Меню параметров / Меню параметрів
        'themes': "Themes",
        'lang':   "Language",
        'light':  "Light",
        'dark':   "Dark",
        'system': "System",

        # About menu / Меню About / Меню About
        'author_btn':        "Program Author",
        'author_title':      "Author",
        'author_main':       "Maxim Melnikov",
        'author_label_text': "Developed by:",
        'ver_btn':           "Program Version",
        'ver_title':         "Version",
        'ver_main':          "v1.9.7 Stable",
        'ver_label_text':    "Current build:",
        'update_btn':        "Check for Updates",
        'site_btn':          "Project Site (GitHub)",

        # Main UI labels / Метки интерфейса / Мітки інтерфейсу
        'header':    "Generation Settings",
        'len_label': "Password Length (4-64):",

        # Checkboxes / Флажки / Прапорці
        'upper':     "Uppercase",
        'lower':     "Lowercase",
        'digits':    "Digits",
        'symb':      "Symbols",
        'exclude':   "Exclude similar (0/O, 1/l/I)",
        'ambiguous': "Exclude ambiguous",
        'hide':      "Hide symbols",
        'at_least':  "At least 1 from each category",

        # Buttons / Кнопки / Кнопки
        'gen_btn':     "GENERATE (Ctrl+G)",
        'open_btn':    "OPEN FILE (Ctrl+O)",
        'copy_btn':    "COPY PASSWORD",
        'qr_btn':      "PASSWORD QR-CODE",
        'history_btn': "HISTORY ({})",   # ← FIX #5

        # History window / Окно истории / Вікно історії
        'history_title': "Password History",
        'history_empty': "History is empty",

        # Strength / QR / Сложность / QR / Складність / QR
        'strength': "Strength",
        'qr_scan':  "Scan with camera",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],

        # Warnings / Предупреждения / Попередження
        'warn':        "Warning",
        'min_len':     "Length must be 4-64",
        'err':         "Error",
        'choose_set':  "Select character sets",
        'check_input': "Check input",

        # Success / Успех / Успіх
        'success':  "Success!",
        'pwd_done': "Password copied to clipboard",

        # File dialog strings / Строки диалога файла / Рядки діалогу файлу
        'save_title': "Save as",
        'open_title': "Open Password",
        'text_files': "Text files",
        'all_files':  "All files",
        'saved':      "File saved.",
        'no_pwd':     "No password to save.",
        'empty_file': "File is empty!",

        # FIX #12: added (MD5) suffix for consistency with Russian locale
        # ИСПРАВЛЕНИЕ #12: добавлен суффикс (MD5) для единообразия с русской локалью
        # ВИПРАВЛЕННЯ #12: додано суфікс (MD5) для узгодженості з російською локаллю
        'crack_instantly': "Instantly (MD5)",
        'crack_seconds':   "~{} sec. (MD5)",
        'crack_minutes':   "~{} min. (MD5)",
        'crack_hours':     "~{} hrs. (MD5)",
        'crack_days':      "~{} days (MD5)",
        'crack_years':     "~{} years (MD5)",
        'crack_centuries': "~{} centuries (MD5)",
        'crack_never':     "Practically impossible (MD5)",

        # Window titles for info dialogs / Заголовки информационных окон / Заголовки інформаційних вікон
        'dlg_title_success': "Success!",
        'dlg_title_copied':  "Clipboard",
    },

    'ua': {
        # Menu bar / Строка меню / Рядок меню
        'menu_file':  "Файл",
        'menu_opts':  "Опції",
        'menu_about': "Про програму",

        # File menu / Меню файла / Меню файлу
        'save':    "Зберегти (Ctrl+S)",
        'save_as': "Зберегти як...",
        'exit':    "Вихід",

        # Options menu / Меню параметров / Меню параметрів
        'themes': "Теми",
        'lang':   "Мова",
        'light':  "Світла",
        'dark':   "Темна",
        'system': "Системна",

        # About menu / Меню «Про програму» / Меню «Про програму»
        'author_btn':        "Автор програми",
        'author_title':      "Автор",
        'author_main':       "Максим Мельников",
        'author_label_text': "Програму розробив:",
        'ver_btn':           "Версія програми",
        'ver_title':         "Версія",
        'ver_main':          "v1.9.7 Stable",
        'ver_label_text':    "Поточна збірка:",
        'update_btn':        "Перевірити оновлення",
        'site_btn':          "Сайт проєкту (GitHub)",

        # Main UI labels / Метки интерфейса / Мітки інтерфейсу
        'header':    "Налаштування генерації",
        'len_label': "Довжина пароля (4-64):",

        # Checkboxes / Флажки / Прапорці
        'upper':     "Великі літери",
        'lower':     "Малі літери",
        'digits':    "Цифри",
        'symb':      "Спецсимволи",
        'exclude':   "Виключити схожі (0/O, 1/l/I)",
        'ambiguous': "Виключити неоднозначні",
        'hide':      "Приховати символи",
        'at_least':  "Мінімум 1 з кожної категорії",

        # Buttons / Кнопки / Кнопки
        'gen_btn':     "ЗГЕНЕРУВАТИ (Ctrl+G)",
        'open_btn':    "ВІДКРИТИ ФАЙЛ (Ctrl+O)",
        'copy_btn':    "КОПІЮВАТИ ПАРОЛЬ",
        'qr_btn':      "QR-КОД ПАРОЛЯ",
        'history_btn': "ІСТОРІЯ ({})",   # ← FIX #5

        # History window / Окно истории / Вікно історії
        'history_title': "Історія паролів",
        'history_empty': "Історія порожня",

        # Strength / QR / Сложность / QR / Складність / QR
        'strength': "Складність",
        'qr_scan':  "Відскануйте камерою",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],

        # Warnings / Предупреждения / Попередження
        'warn':        "Увага",
        'min_len':     "Довжина має бути від 4 до 64",
        'err':         "Помилка",
        'choose_set':  "Оберіть набори символів",
        'check_input': "Перевірте введення",

        # Success / Успех / Успіх
        'success':  "Успішно!",
        'pwd_done': "Пароль скопійовано в буфер",

        # File dialog strings / Строки диалога файла / Рядки діалогу файлу
        'save_title': "Зберегти як",
        'open_title': "Відкрити пароль",
        'text_files': "Текстові файли",
        'all_files':  "Усі файли",
        'saved':      "Файл збережено.",
        'no_pwd':     "Немає пароля для збереження.",
        'empty_file': "Файл порожній!",

        # FIX #12: added (MD5) suffix for consistency
        # ИСПРАВЛЕНИЕ #12: добавлен суффикс (MD5)
        # ВИПРАВЛЕННЯ #12: додано суфікс (MD5)
        'crack_instantly': "Миттєво (MD5)",
        'crack_seconds':   "~{} сек. (MD5)",
        'crack_minutes':   "~{} хв. (MD5)",
        'crack_hours':     "~{} год. (MD5)",
        'crack_days':      "~{} дн. (MD5)",
        'crack_years':     "~{} років (MD5)",
        'crack_centuries': "~{} століть (MD5)",
        'crack_never':     "Майже неможливо (MD5)",

        # Window titles for info dialogs / Заголовки информационных окон / Заголовки інформаційних вікон
        'dlg_title_success': "Успішно!",
        'dlg_title_copied':  "Буфер обміну",
    },
}


# =============================================================================
# MAIN APPLICATION CLASS / ГЛАВНЫЙ КЛАСС / ГОЛОВНИЙ КЛАС
# =============================================================================

class SecurePassApp:
    def __init__(self, root):
        """
        Initialize app state, build UI, apply default theme/language.
        Инициализация состояния, построение интерфейса, применение темы/языка.
        Ініціалізація стану, побудова інтерфейсу, застосування теми/мови.
        """
        self.root = root
        self.root.title("Secure Pass Pro")
        self.root.geometry("340x680")
        self.root.resizable(False, False)

        # Application state / Состояние приложения / Стан програми
        self.current_lang   = 'ru'
        self.last_save_path = None
        self.history        = []
        self.current_theme  = 'system'

        # Resolve icon path once / Путь к иконке вычисляем один раз / Шлях до іконки обчислюємо один раз
        self.icon_path = resource_path("app_icon.ico")

        # Widget registry for bulk theme updates / Реестр виджетов для массового обновления темы / Реєстр віджетів для масового оновлення теми
        self.theme_registry = {'labels': [], 'checkbuttons': [], 'frames': [], 'entries': []}

        self.setup_variables()
        self.setup_ui()
        self.bind_shortcuts()   # MUST be after setup_ui — len_entry must exist / ДОЛЖЕН быть после setup_ui — len_entry уже должен существовать / МАЄ бути після setup_ui — len_entry вже має існувати
        self.set_icon(self.root)

        # Apply saved/default theme and language / Применяем тему и язык / Застосовуємо тему та мову
        self.change_theme('system')
        self.change_lang('ru')

    # =========================================================================
    # SOUND ENGINE / ЗВУКОВОЙ ДВИЖОК / ЗВУКОВИЙ РУШІЙ
    # =========================================================================

    def play_sound(self, sound_type="click"):
        """
        Windows-only sound feedback using winsound.
        Imported lazily here to avoid NameError on Linux/macOS.

        Звуковая обратная связь только для Windows через winsound.
        Импортируется лениво здесь, чтобы избежать NameError на Linux/macOS.

        Звуковий зворотний зв'язок тільки для Windows через winsound.
        Імпортується ліниво тут, щоб уникнути NameError на Linux/macOS.

        FIX #1: winsound imported lazily here, NOT at module level.
        ИСПРАВЛЕНИЕ #1: winsound импортируется лениво здесь, НЕ на уровне модуля.
        ВИПРАВЛЕННЯ #1: winsound імпортується ліниво тут, НЕ на рівні модуля.
        """
        if platform.system() != "Windows":
            return  # Silent on non-Windows / Тихо на не-Windows / Тихо на не-Windows
        try:
            import winsound  # lazy import — safe on all platforms / ленивый импорт — безопасен на всех платформах / лінивий імпорт — безпечний на всіх платформах
            if sound_type == "click":
                winsound.Beep(1000, 50)
            elif sound_type == "success":
                winsound.MessageBeep(winsound.MB_OK)
            elif sound_type == "error":
                winsound.MessageBeep(winsound.MB_ICONHAND)
        except Exception:
            pass  # Hardware may not support Beep / Железо может не поддерживать Beep / Залізо може не підтримувати Beep

    # =========================================================================
    # ICON / ИКОНКА / ІКОНКА
    # =========================================================================

    def set_icon(self, window):
        """
        Set window icon safely — silences TclError and OSError only.
        Устанавливает иконку окна — подавляет только TclError и OSError.
        Встановлює іконку вікна — пригнічує лише TclError та OSError.

        FIX #8: was bare `except: pass` — narrowed to specific exception types.
        ИСПРАВЛЕНИЕ #8: был голый `except: pass` — сужен до конкретных типов.
        ВИПРАВЛЕННЯ #8: був голий `except: pass` — звужено до конкретних типів.
        """
        if os.path.exists(self.icon_path):
            try:
                window.iconbitmap(self.icon_path)
            except (tk.TclError, OSError):   # ← FIX #8
                pass

    # =========================================================================
    # SHORTCUTS / ГОРЯЧИЕ КЛАВИШИ / ГАРЯЧІ КЛАВІШІ
    # =========================================================================

    def _handle_shortcut(self, callback):
        """
        Call callback and return "break" to stop event propagation into Entry.
        Вызывает callback и возвращает "break" для остановки распространения события в Entry.
        Викликає callback та повертає "break" для зупинки поширення події у Entry.
        """
        callback()
        return "break"

    def bind_shortcuts(self):
        """
        Bind Ctrl shortcuts to BOTH root and len_entry.

        WHY TWO TARGETS: when focus is on a tk.Entry, it consumes key events
        and they never reach root-level bindings. We bind on the entry directly
        too and return "break" so the Entry does not ALSO process the keystroke.

        ПОЧЕМУ ДВА ОБЪЕКТА: при фокусе на tk.Entry он поглощает события клавиш
        и они не доходят до root. Биндим прямо на Entry и возвращаем "break",
        чтобы Entry не обрабатывал нажатие дополнительно.

        ЧОМУ ДВА ОБ'ЄКТИ: при фокусі на tk.Entry він поглинає події клавіш
        і вони не доходять до root. Прив'язуємо напряму до Entry та повертаємо
        "break", щоб Entry не обробляв натискання додатково.
        """
        shortcuts = {
            "<Control-s>": self.save_password,
            "<Control-o>": self.open_file,
            "<Control-g>": self.generate_password,
        }
        for key, cb in shortcuts.items():
            self.root.bind(key,      lambda e, f=cb: self._handle_shortcut(f))
            self.len_entry.bind(key, lambda e, f=cb: self._handle_shortcut(f))

    # =========================================================================
    # VARIABLES / ПЕРЕМЕННЫЕ / ЗМІННІ
    # =========================================================================

    def setup_variables(self):
        """
        Initialise all tk variables used by UI controls.
        Инициализирует все tk-переменные, используемые элементами интерфейса.
        Ініціалізує всі tk-змінні, що використовуються елементами інтерфейсу.

        NOTE on FIX #6: trace fires before len_entry exists — validate_length
        handles this via `except AttributeError`.

        ПРИМЕЧАНИЕ к исправлению #6: trace срабатывает до создания len_entry —
        validate_length обрабатывает это через `except AttributeError`.

        ПРИМІТКА до виправлення #6: trace спрацьовує до створення len_entry —
        validate_length обробляє це через `except AttributeError`.
        """
        self.length_var            = tk.StringVar(value="12")
        self.upper_var             = tk.BooleanVar(value=True)
        self.lower_var             = tk.BooleanVar(value=True)
        self.digits_var            = tk.BooleanVar(value=True)
        self.symbols_var           = tk.BooleanVar(value=True)
        self.exclude_similar_var   = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        self.at_least_one_var      = tk.BooleanVar(value=True)
        self.hide_var              = tk.BooleanVar(value=False)
        self.result_var            = tk.StringVar()
        self.strength_var          = tk.StringVar()
        self.crack_var             = tk.StringVar()

        # Live validation as user types / Живая валидация при вводе / Жива валідація під час введення
        self.length_var.trace_add("write", self.validate_length)

    def validate_length(self, *args):
        """
        Colour len_entry: blue/teal when valid, red when out of range or non-numeric.

        FIX #6 (guard): trace fires before len_entry is built during __init__,
        so AttributeError is caught to silently skip that first call.

        Красит len_entry: синий/бирюзовый при допустимом значении, красный — при ошибке.
        ИСПРАВЛЕНИЕ #6 (защита): trace срабатывает до создания len_entry, AttributeError
        перехватывается для тихого пропуска первого вызова.

        Фарбує len_entry: синій/блакитний при допустимому значенні, червоний — при помилці.
        ВИПРАВЛЕННЯ #6 (захист): trace спрацьовує до створення len_entry, AttributeError
        перехоплюється для тихого пропуску першого виклику.
        """
        try:
            num = int(self.length_var.get().strip())
            color = "#4EC9B0" if self.current_theme == 'dark' else "#005FB8"
            self.len_entry.config(fg=color if 4 <= num <= 64 else "red")
        except ValueError:
            try:
                self.len_entry.config(fg="red")
            except AttributeError:
                pass  # len_entry not yet created / ещё не создан / ще не створено
        except AttributeError:
            pass  # len_entry not yet created / ещё не создан / ще не створено

    # =========================================================================
    # UI SETUP / ПОСТРОЕНИЕ ИНТЕРФЕЙСА / ПОБУДОВА ІНТЕРФЕЙСУ
    # =========================================================================

    def setup_ui(self):
        """
        Build the complete widget tree.
        Строит полное дерево виджетов.
        Будує повне дерево віджетів.
        """
        # ---- Menu bar / Строка меню / Рядок меню ----
        self.menubar = tk.Menu(self.root)

        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Save",      command=self.save_password)
        self.file_menu.add_command(label="Save as...", command=self.save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit",      command=self.root.destroy)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.theme_sub = tk.Menu(self.settings_menu, tearoff=0)
        self.theme_sub.add_command(label="Light",  command=lambda: self.change_theme('light'))
        self.theme_sub.add_command(label="Dark",   command=lambda: self.change_theme('dark'))
        self.theme_sub.add_command(label="System", command=lambda: self.change_theme('system'))
        self.settings_menu.add_cascade(label="Themes", menu=self.theme_sub)

        self.lang_sub = tk.Menu(self.settings_menu, tearoff=0)
        for code, name in [('ru', 'Русский'), ('en', 'English'), ('ua', 'Українська')]:
            self.lang_sub.add_command(label=name, command=lambda c=code: self.change_lang(c))
        self.settings_menu.add_cascade(label="Language", menu=self.lang_sub)
        self.menubar.add_cascade(label="Options", menu=self.settings_menu)

        self.about_menu = tk.Menu(self.menubar, tearoff=0)
        self.about_menu.add_command(label="Author",  command=lambda: self.show_info('author_title', 'author_label_text', 'author_main'))
        self.about_menu.add_command(label="Version", command=lambda: self.show_info('ver_title',    'ver_label_text',    'ver_main'))
        self.about_menu.add_command(label="Updates", command=lambda: webbrowser.open(UPDATE_URL))
        self.about_menu.add_command(label="GitHub",  command=lambda: webbrowser.open(GITHUB_URL))
        self.menubar.add_cascade(label="About", menu=self.about_menu)
        self.root.config(menu=self.menubar)

        # ---- Header / Заголовок / Заголовок ----
        self.header_label = tk.Label(self.root, font=("Arial", 11, "bold"))
        self.header_label.pack(pady=(10, 2))

        # ---- Length input / Поле длины / Поле довжини ----
        self.len_info_label = tk.Label(self.root, font=("Arial", 9))
        self.len_info_label.pack()
        self.len_entry = tk.Entry(self.root, textvariable=self.length_var, width=6, justify='center')
        self.len_entry.pack(pady=2)

        # ---- Checkboxes / Флажки / Прапорці ----
        self.frame_checks = tk.Frame(self.root)
        self.frame_checks.pack(pady=2)

        self.cb_upper     = tk.Checkbutton(self.frame_checks, variable=self.upper_var)
        self.cb_lower     = tk.Checkbutton(self.frame_checks, variable=self.lower_var)
        self.cb_digits    = tk.Checkbutton(self.frame_checks, variable=self.digits_var)
        self.cb_symb      = tk.Checkbutton(self.frame_checks, variable=self.symbols_var)
        self.cb_at_least  = tk.Checkbutton(self.frame_checks, variable=self.at_least_one_var)
        self.cb_exclude   = tk.Checkbutton(self.frame_checks, variable=self.exclude_similar_var)
        self.cb_ambiguous = tk.Checkbutton(self.frame_checks, variable=self.exclude_ambiguous_var)
        self.cb_hide      = tk.Checkbutton(
            self.frame_checks, variable=self.hide_var,
            command=lambda: self.result_entry.config(show="*" if self.hide_var.get() else "")
        )

        cbs = [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
               self.cb_at_least, self.cb_exclude, self.cb_ambiguous, self.cb_hide]
        for cb in cbs:
            cb.pack(anchor='w')

        # ---- Action buttons / Кнопки / Кнопки ----
        self.btn_gen  = tk.Button(self.root, command=self.generate_password, width=22, relief='flat', cursor="hand2")
        self.btn_gen.pack(pady=(8, 2))

        self.btn_open = tk.Button(self.root, command=self.open_file, width=22, relief='flat', cursor="hand2")
        self.btn_open.pack(pady=2)

        # ---- Password result / Поле результата / Поле результату ----
        self.result_entry = tk.Entry(
            self.root, textvariable=self.result_var,
            font=("Consolas", 12), width=22, state='readonly', justify='center'
        )
        self.result_entry.pack(pady=4)

        # ---- Strength meters / Индикаторы / Індикатори ----
        self.strength_canvas = tk.Canvas(self.root, width=200, height=6)
        self.strength_canvas.pack()
        self.strength_label_widget = tk.Label(self.root, textvariable=self.strength_var, font=("Arial", 9, "italic"))
        self.strength_label_widget.pack()
        self.crack_canvas = tk.Canvas(self.root, width=200, height=4)
        self.crack_canvas.pack(pady=(4, 0))
        self.crack_label_widget = tk.Label(self.root, textvariable=self.crack_var, font=("Arial", 8))
        self.crack_label_widget.pack()

        # ---- Secondary buttons / Вторичные кнопки / Вторинні кнопки ----
        self.btn_copy    = tk.Button(self.root, command=self.copy_to_clipboard, width=22, relief='flat', cursor="hand2")
        self.btn_copy.pack(pady=5)
        self.btn_qr      = tk.Button(self.root, command=self.generate_qr,       width=22, relief='flat', cursor="hand2")
        self.btn_qr.pack(pady=2)
        self.btn_history = tk.Button(self.root, command=self.show_history,       width=22, relief='flat', cursor="hand2")
        self.btn_history.pack(pady=2)

        # ---- Footer / Нижняя часть / Нижня частина ----
        self.stars_label = tk.Label(self.root, text="★★★★★", font=("Arial", 12, "bold"), fg="#FFD700")
        self.stars_label.pack(side='bottom', pady=(0, 5))
        self.author_label = tk.Label(self.root, text="GitHub ©", cursor="hand2", font=("Arial", 8, "bold"), padx=8, pady=3)
        self.author_label.pack(side='bottom', pady=2)
        self.author_label.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))

        # Register widgets for theme engine / Регистрация для движка тем / Реєстрація для рушія тем
        self.theme_registry['frames']       = [self.root, self.frame_checks]
        self.theme_registry['labels']       = [self.header_label, self.len_info_label, self.strength_label_widget]
        self.theme_registry['checkbuttons'] = cbs
        self.theme_registry['entries']      = [self.len_entry]

    # =========================================================================
    # LANGUAGE ENGINE / СИСТЕМА ЯЗЫКОВ / СИСТЕМА МОВ
    # =========================================================================

    def change_lang(self, lang_code):
        """
        Switch all UI text to the selected language.
        Переключает весь текст интерфейса на выбранный язык.
        Перемикає весь текст інтерфейсу на обрану мову.
        """
        self.current_lang = lang_code
        L = LANGUAGES[lang_code]

        # Menu bar / Строка меню / Рядок меню
        self.menubar.entryconfig(1, label=L['menu_file'])
        self.menubar.entryconfig(2, label=L['menu_opts'])
        self.menubar.entryconfig(3, label=L['menu_about'])

        # File menu / Меню файла / Меню файлу
        self.file_menu.entryconfig(0, label=L['save'])
        self.file_menu.entryconfig(1, label=L['save_as'])
        self.file_menu.entryconfig(3, label=L['exit'])

        # Options menu / Меню опций / Меню опцій
        self.settings_menu.entryconfig(0, label=L['themes'])
        self.settings_menu.entryconfig(1, label=L['lang'])
        self.theme_sub.entryconfig(0, label=L['light'])
        self.theme_sub.entryconfig(1, label=L['dark'])
        self.theme_sub.entryconfig(2, label=L['system'])

        # About menu / Меню «О программе» / Меню «Про програму»
        self.about_menu.entryconfig(0, label=L['author_btn'])
        self.about_menu.entryconfig(1, label=L['ver_btn'])
        self.about_menu.entryconfig(2, label=L['update_btn'])
        self.about_menu.entryconfig(3, label=L['site_btn'])

        # Labels / Метки / Мітки
        self.header_label.config(text=L['header'])
        self.len_info_label.config(text=L['len_label'])

        # Checkboxes / Флажки / Прапорці
        self.cb_upper.config(text=L['upper'])
        self.cb_lower.config(text=L['lower'])
        self.cb_digits.config(text=L['digits'])
        self.cb_symb.config(text=L['symb'])
        self.cb_exclude.config(text=L['exclude'])
        self.cb_ambiguous.config(text=L['ambiguous'])
        self.cb_at_least.config(text=L['at_least'])
        self.cb_hide.config(text=L['hide'])

        # Buttons / Кнопки / Кнопки
        self.btn_gen.config(text=L['gen_btn'])
        self.btn_open.config(text=L['open_btn'])
        self.btn_copy.config(text=L['copy_btn'])
        self.btn_qr.config(text=L['qr_btn'])

        # FIX #5: .format() now has a real {} placeholder to substitute into
        # ИСПРАВЛЕНИЕ #5: .format() теперь имеет реальный {} для подстановки
        # ВИПРАВЛЕННЯ #5: .format() тепер має реальний {} для підстановки
        self.btn_history.config(text=L['history_btn'].format(len(self.history)))

        # Refresh strength display in new language / Обновляем индикатор на новом языке / Оновлюємо індикатор новою мовою
        if self.result_var.get():
            self.update_strength_meter(self.result_var.get())

    # =========================================================================
    # THEME ENGINE / ДВИЖОК ТЕМ / РУШІЙ ТЕМ
    # =========================================================================

    def change_theme(self, mode):
        """
        Apply a colour theme (light / dark / system).
        Применяет цветовую тему (light / dark / system).
        Застосовує кольорову тему (light / dark / system).

        FIX #7: bare `except: pass` replaced with specific exception types.
        ИСПРАВЛЕНИЕ #7: голый `except: pass` заменён на конкретные типы.
        ВИПРАВЛЕННЯ #7: голий `except: pass` замінено на конкретні типи.
        """
        if mode == 'system':
            mode = 'light'
            if platform.system() == "Windows":
                try:
                    import winreg
                    key  = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                    )
                    mode = 'light' if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 1 else 'dark'
                except (OSError, ImportError, AttributeError):   # ← FIX #7
                    pass

        self.current_theme = mode

        if mode == 'dark':
            bg, fg, res_bg, res_fg      = '#000000', '#FFFFFF', '#000000', '#4EC9B0'
            c_gen, c_copy, c_qr, c_hist = '#005FB8', '#107C10', '#68217A', '#3E3E42'
            entry_bg, select_clr        = '#121212', '#1A1A1A'
        else:
            bg, fg, res_bg, res_fg      = '#F3F3F3', '#000000', '#FFFFFF', '#005FB8'
            c_gen, c_copy, c_qr, c_hist = '#CCE4F7', '#DFF6DD', '#F2E5F5', '#E1E1E1'
            entry_bg, select_clr        = '#FFFFFF', '#FFFFFF'

        # Bulk-apply via registry / Массовое применение через реестр / Масове застосування через реєстр
        for f  in self.theme_registry['frames']:       f.config(bg=bg)
        for l  in self.theme_registry['labels']:       l.config(bg=bg, fg=fg)
        for cb in self.theme_registry['checkbuttons']: cb.config(bg=bg, fg=fg, selectcolor=select_clr, activebackground=bg, activeforeground=fg)
        for e  in self.theme_registry['entries']:      e.config(bg=entry_bg, fg=fg, insertbackground=fg)

        self.strength_canvas.config(bg=bg, highlightthickness=0)
        self.crack_canvas.config(bg=bg, highlightthickness=0)
        self.result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
        self.stars_label.config(bg=bg)
        self.author_label.config(bg='#1A1A1A' if mode == 'dark' else '#E1E1E1', fg=fg)
        self.crack_label_widget.config(bg=bg, fg='#FFFFFF' if mode == 'dark' else '#888888')

        def apply_btn(btn, clr):
            btn.config(bg=clr, fg=fg if mode == 'dark' else '#000000', activebackground=clr)

        apply_btn(self.btn_gen,     c_gen)
        apply_btn(self.btn_copy,    c_copy)
        apply_btn(self.btn_qr,      c_qr)
        apply_btn(self.btn_history, c_hist)
        apply_btn(self.btn_open,    '#333333' if mode == 'dark' else '#E1E1E1')

        self.validate_length()

    # =========================================================================
    # PASSWORD GENERATION / ГЕНЕРАЦИЯ ПАРОЛЯ / ГЕНЕРАЦІЯ ПАРОЛЯ
    # =========================================================================

    def generate_password(self):
        """
        Core generation: validate → build charset → shuffle → store history.
        Основная логика: валидация → набор символов → перемешивание → история.
        Основна логіка: валідація → набір символів → перемішування → історія.
        """
        self.play_sound("click")
        L = LANGUAGES[self.current_lang]
        try:
            length = int(self.length_var.get().strip())
            if not (4 <= length <= 64):
                raise ValueError("Length out of range")

            # Collect selected categories / Собираем выбранные категории / Збираємо обрані категорії
            cats = []
            if self.upper_var.get():   cats.append(string.ascii_uppercase)
            if self.lower_var.get():   cats.append(string.ascii_lowercase)
            if self.digits_var.get():  cats.append(string.digits)
            if self.symbols_var.get(): cats.append(string.punctuation)

            if not cats:
                self.play_sound("error")
                messagebox.showerror(L['err'], L['choose_set'])
                return

            # Build exclusion set / Формируем исключаемые символы / Формуємо виключені символи
            excl = ""
            if self.exclude_similar_var.get():   excl += "Il1O0"
            if self.exclude_ambiguous_var.get():  excl += ".,:;'~\"/()[]{}|"

            filtered = [
                filtered_cat
                for cat in cats
                for filtered_cat in [''.join(c for c in cat if c not in excl)]
                if filtered_cat   # drop categories that became empty after filtering / убираем пустые категории / прибираємо порожні категорії
            ]

            if not filtered:
                self.play_sound("error")
                messagebox.showerror(L['err'], L['choose_set'])
                return

            pool = "".join(filtered)
            pwd_list = []

            # Guarantee at least one char from each non-empty category / Гарантируем минимум из каждой / Гарантуємо мінімум з кожної
            if self.at_least_one_var.get() and length >= len(filtered):
                for cat in filtered:
                    pwd_list.append(secrets.choice(cat))
                for _ in range(length - len(filtered)):
                    pwd_list.append(secrets.choice(pool))
            else:
                for _ in range(length):
                    pwd_list.append(secrets.choice(pool))

            secrets.SystemRandom().shuffle(pwd_list)
            password = "".join(pwd_list)

            # Store in history (cap at 5) / Сохраняем в историю (максимум 5) / Зберігаємо в історію (максимум 5)
            self.history.insert(0, password)
            if len(self.history) > 5:
                self.history.pop()

            self.result_var.set(password)
            self.update_strength_meter(password)

            # FIX #5: update history button with real count via {} placeholder
            # ИСПРАВЛЕНИЕ #5: обновляем кнопку истории с реальным счётчиком через {}
            # ВИПРАВЛЕННЯ #5: оновлюємо кнопку історії з реальним лічильником через {}
            self.btn_history.config(
                text=LANGUAGES[self.current_lang]['history_btn'].format(len(self.history))
            )

        except ValueError:
            # Only ValueError expected / Только ValueError ожидается / Лише ValueError очікується
            self.play_sound("error")
            messagebox.showerror(L['err'], L['check_input'])

    # =========================================================================
    # STRENGTH METER / ИНДИКАТОР СЛОЖНОСТИ / ІНДИКАТОР СКЛАДНОСТІ
    # =========================================================================

    def update_strength_meter(self, password):
        """
        Redraw canvas bars and update labels based on entropy.
        Перерисовывает полосы и обновляет метки на основе энтропии.
        Перемальовує смуги та оновлює мітки на основі ентропії.
        """
        self.strength_canvas.delete("all")
        self.crack_canvas.delete("all")
        L = LANGUAGES[self.current_lang]
        if not password:
            self.strength_var.set("")
            self.crack_var.set("")
            return

        entropy = self.calculate_entropy(password)
        score   = self.get_strength_score(entropy)
        colors  = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]

        # Strength bar / Полоса сложности / Смуга складності
        self.strength_canvas.create_rectangle(0, 0, 200, 6, fill="#333333", outline="")
        self.strength_canvas.create_rectangle(0, 0, (score + 1) * 33.33, 6, fill=colors[score], outline="")
        self.strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]} ({int(entropy)} bit)")

        # Crack time bar / Полоса времени взлома / Смуга часу зламу
        c_score, c_text = self.estimate_crack_time(password)
        self.crack_var.set(c_text)
        b_clr = "#e74c3c" if entropy < 40 else ("#f39c12" if entropy < 80 else "#27ae60")
        self.crack_canvas.create_rectangle(0, 0, 200, 4, fill="#333333", outline="")
        self.crack_canvas.create_rectangle(0, 0, min(200, (c_score + 1) * 25), 4, fill=b_clr, outline="")

    def calculate_entropy(self, password):
        """
        Shannon entropy estimate based on detected charset size.
        Оценка энтропии Шеннона по размеру обнаруженного набора символов.
        Оцінка ентропії Шеннона за розміром виявленого набору символів.
        """
        sz = 0
        if any(c.islower()             for c in password): sz += 26
        if any(c.isupper()             for c in password): sz += 26
        if any(c.isdigit()             for c in password): sz += 10
        if any(c in string.punctuation for c in password): sz += 32
        return len(password) * math.log2(sz) if sz > 0 else 0

    def get_strength_score(self, entropy):
        """
        Map entropy (bits) to a 0-5 score index.
        Отображает энтропию (биты) в индекс 0-5.
        Відображає ентропію (біти) в індекс 0-5.
        """
        if entropy < 28:  return 0
        if entropy < 36:  return 1
        if entropy < 60:  return 2
        if entropy < 80:  return 3
        if entropy < 100: return 4
        return 5

    def estimate_crack_time(self, password):
        """
        Estimate brute-force time assuming MD5 at CRACK_SPEED hashes/s.
        Оценивает время перебора для MD5 со скоростью CRACK_SPEED хэш/с.
        Оцінює час перебору для MD5 зі швидкістю CRACK_SPEED хеш/с.
        """
        entropy = self.calculate_entropy(password)
        sec     = (2 ** entropy) / CRACK_SPEED
        L       = LANGUAGES[self.current_lang]

        if   sec < 0.1:                 return 0, L['crack_instantly']
        elif sec < 60:                  return 1, L['crack_seconds'].format(int(sec))
        elif sec < 3_600:               return 2, L['crack_minutes'].format(int(sec // 60))
        elif sec < 86_400:              return 3, L['crack_hours'].format(int(sec // 3_600))
        elif sec < 86_400 * 365:        return 4, L['crack_days'].format(int(sec // 86_400))
        elif sec < 86_400 * 365 * 100:  return 5, L['crack_years'].format(int(sec // (86_400 * 365)))
        elif sec < 86_400 * 365 * 10000:return 6, L['crack_centuries'].format(int(sec // (86_400 * 365 * 100)))
        else:                           return 7, L['crack_never']

    # =========================================================================
    # FILE OPERATIONS / ФАЙЛОВЫЕ ОПЕРАЦИИ / ФАЙЛОВІ ОПЕРАЦІЇ
    # =========================================================================

    def save_password(self):
        """
        Quick save: overwrite last_save_path if exists, else open Save As dialog.
        Быстрое сохранение: перезаписывает файл если существует, иначе — диалог.
        Швидке збереження: перезаписує файл якщо існує, інакше — діалог.
        """
        p = self.result_var.get()
        L = LANGUAGES[self.current_lang]
        if not p:
            self.play_sound("error")
            messagebox.showwarning(L['warn'], L['no_pwd'])
            return

        if self.last_save_path and os.path.exists(os.path.dirname(self.last_save_path)):
            try:
                with open(self.last_save_path, "w", encoding="utf-8") as f:
                    f.write(p)
                self.play_sound("success")
                # FIX #2: pass pre-built string, not a LANGUAGES key, as window title
                # ИСПРАВЛЕНИЕ #2: передаём готовую строку, а не ключ LANGUAGES, как заголовок окна
                # ВИПРАВЛЕННЯ #2: передаємо готовий рядок, а не ключ LANGUAGES, як заголовок вікна
                self.show_info_msg(L['dlg_title_success'], L['success'], L['saved'])
            except OSError as e:
                messagebox.showerror(L['err'], str(e))
        else:
            self.save_as()

    def save_as(self):
        """
        Open Save As dialog and write password to chosen file.
        Открывает диалог «Сохранить как» и записывает пароль.
        Відкриває діалог «Зберегти як» та записує пароль.
        """
        L    = LANGUAGES[self.current_lang]
        p    = self.result_var.get()
        if not p:
            self.play_sound("error")
            messagebox.showwarning(L['warn'], L['no_pwd'])
            return
        path = filedialog.asksaveasfilename(
            title=L['save_title'], initialfile="Pass.txt",
            defaultextension=".txt",
            filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")]
        )
        if path:
            try:
                self.last_save_path = path
                with open(path, "w", encoding="utf-8") as f:
                    f.write(p)
                self.play_sound("success")
                self.show_info_msg(L['dlg_title_success'], L['success'], L['saved'])
            except OSError as e:
                messagebox.showerror(L['err'], str(e))

    def open_file(self):
        """
        Open a .txt file and load its content as the current password.
        Note: does NOT set last_save_path — avoids accidental overwrites of opened files.

        Открывает .txt-файл и загружает содержимое как пароль.
        Примечание: НЕ устанавливает last_save_path — избегает случайной перезаписи.

        Відкриває .txt-файл і завантажує вміст як пароль.
        Примітка: НЕ встановлює last_save_path — уникає випадкового перезапису.
        """
        L    = LANGUAGES[self.current_lang]
        path = filedialog.askopenfilename(
            title=L['open_title'],
            filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if not content:
                    messagebox.showinfo(L['warn'], L['empty_file'])
                    return
                self.result_var.set(content)
                self.update_strength_meter(content)
                self.play_sound("success")
            except OSError as e:
                messagebox.showerror(L['err'], str(e))

    # =========================================================================
    # CLIPBOARD / БУФЕР ОБМЕНА / БУФЕР ОБМІНУ
    # =========================================================================

    def copy_to_clipboard(self):
        """
        Copy password to clipboard; auto-clear after 60 s.
        Копирует пароль; автоочистка через 60 с.
        Копіює пароль; автоочищення через 60 с.
        """
        p = self.result_var.get()
        if p:
            L = LANGUAGES[self.current_lang]
            self.root.clipboard_clear()
            self.root.clipboard_append(p)
            # Schedule clipboard wipe / Планируем очистку / Плануємо очищення
            self.root.after(60_000, lambda: self.root.clipboard_clear() if self.root.winfo_exists() else None)
            self.play_sound("success")
            # FIX #2 & #3: use dedicated title key, not the content key as window title
            # ИСПРАВЛЕНИЕ #2 и #3: используем отдельный ключ заголовка, не ключ содержимого
            # ВИПРАВЛЕННЯ #2 та #3: використовуємо окремий ключ заголовка, не ключ вмісту
            self.show_info_msg(L['dlg_title_copied'], L['success'], L['pwd_done'])

    # =========================================================================
    # HISTORY / ИСТОРИЯ / ІСТОРІЯ
    # =========================================================================

    def show_history(self):
        """
        Open a window listing the last 5 generated passwords.
        Открывает окно со списком последних 5 паролей.
        Відкриває вікно зі списком останніх 5 паролів.
        """
        self.play_sound("click")
        L   = LANGUAGES[self.current_lang]
        win = tk.Toplevel(self.root)
        win.title(L['history_title'])
        win.resizable(False, False)
        self.set_icon(win)
        self.center_child(win, self.root, 300, 250)

        cur_bg  = self.root.cget("bg")
        cur_fg  = "#FFFFFF"  if self.current_theme == 'dark' else "#000000"
        btn_fg  = "#4EC9B0"  if self.current_theme == 'dark' else "#005FB8"
        btn_abg = "#1A1A1A"  if self.current_theme == 'dark' else "#E1E1E1"
        win.configure(bg=cur_bg)

        if not self.history:
            tk.Label(win, text=L['history_empty'], bg=cur_bg, fg=cur_fg, font=("Arial", 10)).pack(expand=True)
        else:
            for pwd in self.history:
                btn = tk.Button(
                    win, text=pwd, font=("Consolas", 10), relief='flat',
                    bg=cur_bg, fg=btn_fg, activebackground=btn_abg,
                    cursor="hand2",
                    command=lambda p=pwd, w=win: self.select_from_history(p, w)
                )
                btn.pack(pady=5, fill='x', padx=20)

    def select_from_history(self, pwd, window):
        """
        Load history entry, evaluate strength, copy it, close history window.
        Загружает запись, оценивает сложность, копирует, закрывает окно.
        Завантажує запис, оцінює складність, копіює, закриває вікно.
        """
        self.play_sound("click")
        self.result_var.set(pwd)
        self.update_strength_meter(pwd)
        self.copy_to_clipboard()
        window.destroy()

    # =========================================================================
    # QR CODE / QR-КОД / QR-КОД
    # =========================================================================

    def generate_qr(self):
        """
        Render a QR code of the current password in a new window.
        Рендерит QR-код текущего пароля в новом окне.
        Рендерить QR-код поточного пароля в новому вікні.
        """
        self.play_sound("click")
        pwd = self.result_var.get()
        L   = LANGUAGES[self.current_lang]
        if not pwd:
            self.play_sound("error")
            messagebox.showwarning(L['warn'], L['no_pwd'])
            return

        win = tk.Toplevel(self.root)
        win.title("QR Code")
        self.set_icon(win)
        self.center_child(win, self.root, 300, 380)
        cur_bg = self.root.cget("bg")
        win.configure(bg=cur_bg)
        qr_fg, qr_bg = ("white", "black") if self.current_theme == 'dark' else ("black", "white")

        try:
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(pwd)
            qr.make(fit=True)
            img    = qr.make_image(fill_color=qr_fg, back_color=qr_bg)
            img_tk = ImageTk.PhotoImage(img.resize((220, 220), Image.LANCZOS))

            tk.Label(win, text=L['qr_scan'], bg=cur_bg, fg=qr_fg).pack(pady=(10, 0))
            lbl = tk.Label(win, image=img_tk, bg=cur_bg)
            lbl.image = img_tk  # prevent GC / защита от GC / захист від GC
            lbl.pack(pady=10)
            tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat',
                      bg=self.author_label.cget("bg"), fg=qr_fg).pack(pady=5)
        except Exception as e:
            messagebox.showerror(L['err'], str(e))
            win.destroy()

    # =========================================================================
    # INFO WINDOWS / ИНФОРМАЦИОННЫЕ ОКНА / ІНФОРМАЦІЙНІ ВІКНА
    # =========================================================================

    def show_info(self, title_key, label_key, value_key):
        """
        Show About-style info window (Author, Version).
        All three args are LANGUAGES keys; the window title uses title_key.

        Показывает окно в стиле «О программе» (Автор, Версия).
        Все три аргумента — ключи LANGUAGES; заголовок окна использует title_key.

        Показує вікно у стилі «Про програму» (Автор, Версія).
        Всі три аргументи — ключі LANGUAGES; заголовок вікна використовує title_key.

        FIX #4: show_info is now separate from show_info_msg to eliminate
                the is_static flag confusion that caused incorrect key lookups.
        ИСПРАВЛЕНИЕ #4: show_info теперь отделён от show_info_msg для устранения
                путаницы с флагом is_static, приводившей к неверному поиску ключей.
        ВИПРАВЛЕННЯ #4: show_info тепер відокремлений від show_info_msg для усунення
                плутанини з прапором is_static, що призводила до хибного пошуку ключів.
        """
        L      = LANGUAGES[self.current_lang]
        win    = tk.Toplevel(self.root)
        win.title(L[title_key])         # e.g. "Автор" / "Версия"
        self.set_icon(win)
        self.center_child(win, self.root, 280, 180)
        cur_bg = self.root.cget("bg")
        cur_fg = "#FFFFFF" if self.current_theme == 'dark' else "#000000"
        win.configure(bg=cur_bg)

        tk.Label(win, text=L[label_key], bg=cur_bg, fg=cur_fg,
                 font=("Arial", 9)).pack(pady=(20, 5))
        tk.Label(win, text=L[value_key], bg=cur_bg,
                 fg="#4EC9B0" if self.current_theme == 'dark' else "#005FB8",
                 font=("Arial", 11, "bold")).pack(pady=5)
        tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat',
                  bg='#1A1A1A' if self.current_theme == 'dark' else '#E1E1E1',
                  fg=cur_fg).pack(pady=20)

    def show_info_msg(self, window_title, label_text, body_text, width=280):
        """
        Generic notification window — all args are already-localised strings.
        Универсальное окно уведомлений — все аргументы уже локализованные строки.
        Універсальне вікно сповіщень — всі аргументи вже локалізовані рядки.

        FIX #2 & #3: callers now pass pre-resolved strings (not LANGUAGES keys)
                     so there is no risk of L[key] KeyError on the window title.
        ИСПРАВЛЕНИЕ #2 и #3: вызывающий код теперь передаёт готовые строки (не ключи),
                     поэтому нет риска KeyError при использовании как заголовка окна.
        ВИПРАВЛЕННЯ #2 та #3: код, що викликає, тепер передає готові рядки (не ключі),
                     тому немає ризику KeyError при використанні як заголовка вікна.
        """
        win    = tk.Toplevel(self.root)
        win.title(window_title)         # plain string, never a LANGUAGES key / обычная строка, никогда не ключ / звичайний рядок, ніколи не ключ
        self.set_icon(win)
        self.center_child(win, self.root, width, 180)
        cur_bg = self.root.cget("bg")
        cur_fg = "#FFFFFF" if self.current_theme == 'dark' else "#000000"
        win.configure(bg=cur_bg)

        tk.Label(win, text=label_text, bg=cur_bg, fg=cur_fg,
                 font=("Arial", 9)).pack(pady=(20, 5))
        tk.Label(win, text=body_text,  bg=cur_bg,
                 fg="#4EC9B0" if self.current_theme == 'dark' else "#005FB8",
                 font=("Arial", 11, "bold")).pack(pady=5)
        tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat',
                  bg='#1A1A1A' if self.current_theme == 'dark' else '#E1E1E1',
                  fg=cur_fg).pack(pady=20)

    # =========================================================================
    # UTILITIES / УТИЛИТЫ / УТИЛІТИ
    # =========================================================================

    def center_child(self, child, parent, w, h):
        """
        Position child window centred over parent.
        Размещает дочернее окно по центру над родительским.
        Розміщує дочірнє вікно по центру над батьківським.
        """
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        child.geometry(f"{w}x{h}+{px + (pw - w) // 2}+{py + (ph - h) // 2}")


# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА / ТОЧКА ВХОДУ
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app  = SecurePassApp(root)
    root.mainloop()
