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
# DEPENDENCIES & PATHS / ЗАВИСИМОСТИ И ПУТИ / ЗАЛЕЖНОСТІ ТА ШЛЯХИ
# =============================================================================

def resource_path(relative_path):
    """ 
    Get absolute path to resource, works for dev and for PyInstaller 
    Получение пути к ресурсам для корректной работы внутри EXE
    Отримання шляху до ресурсів для коректної роботи всередині EXE
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    import qrcode
    from PIL import ImageTk, Image
except ImportError:
    # Error message if libraries are missing / Ошибка при отсутствии библиотек / Помилка при відсутності бібліотек
    print("Missing dependencies! Please run: pip install qrcode[pil] pillow")
    sys.exit(1)

# High DPI support / Поддержка высокого разрешения / Підтримка високої роздільної здатності
if platform.system() == "Windows":
    import winsound
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass

# =============================================================================
# CONSTANTS & LANGUAGES / КОНСТАНТЫ И ЯЗЫКИ / КОНСТАНТИ ТА МОВИ
# =============================================================================

UPDATE_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv1.9.7/Secure_Pass_Pro.exe"
GITHUB_URL = "https://github.com/Maximka1993271/Password-Generator-Python"
CRACK_SPEED = 100_000_000_000 # Keys per second for MD5 / Ключей в секунду / Ключів на секунду

LANGUAGES = {
    'ru': {
        'menu_file': "Файл", 'menu_opts': "Опции", 'menu_about': "О программе",
        'save': "Сохранить (Ctrl+S)", 'save_as': "Сохранить как...", 'exit': "Выход",
        'themes': "Темы", 'lang': "Язык", 'light': "Светлая", 'dark': "Тёмная", 'system': "Системная",
        'author_btn': "Автор программы", 'author_title': "Автор", 'author_main': "Максим Мельников", 'author_label_text': "Программу разработал:",
        'ver_btn': "Версия программы", 'ver_title': "Версия", 'ver_main': "v1.9.7 Stable", 'ver_label_text': "Текущая сборка:",
        'update_btn': "Проверить обновления", 'site_btn': "Сайт проекта (GitHub)",
        'header': "Настройки генерации", 'len_label': "Длина пароля (4-64):",
        'upper': "Заглавные буквы", 'lower': "Строчные буквы", 'digits': "Цифры", 'symb': "Спецсимволы",
        'exclude': "Исключить похожие (0/O, 1/l/I)", 'ambiguous': "Исключить неоднозначные", 'hide': "Скрывать символы",
        'at_least': "Минимум 1 из каждой категории",
        'gen_btn': "СГЕНЕРИРОВАТЬ (Ctrl+G)", 'open_btn': "ОТКРЫТЬ ФАЙЛ (Ctrl+O)", 'copy_btn': "КОПИРОВАТЬ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'history_btn': "ИСТОРИЯ (5)", 'history_title': "История паролей", 'history_empty': "История пуста",
        'strength': "Сложность", 'qr_scan': "Отсканируйте камерой",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],
        'warn': "Внимание", 'min_len': "Длина должна быть от 4 до 64", 'err': "Ошибка", 'choose_set': "Выберите наборы символов",
        'check_input': "Проверьте ввод", 'success': "Успешно!", 'pwd_done': "Пароль скопирован в буфер",
        'save_title': "Сохранить как", 'open_title': "Открыть пароль", 'text_files': "Текстовые файлы", 'all_files': "Все файлы",
        'saved': "Файл сохранён.", 'no_pwd': "Нет пароля для сохранения.", 'empty_file': "Файл пуст!",
        'crack_instantly': "Мгновенно (MD5)", 'crack_seconds': "~{} сек. (MD5)", 'crack_minutes': "~{} мин. (MD5)",
        'crack_hours': "~{} ч. (MD5)", 'crack_days': "~{} дн. (MD5)", 'crack_years': "~{} лет (MD5)",
        'crack_centuries': "~{} веков (MD5)", 'crack_never': "Почти невозможно (MD5)"
    },
    'en': {
        'menu_file': "File", 'menu_opts': "Options", 'menu_about': "About",
        'save': "Save (Ctrl+S)", 'save_as': "Save as...", 'exit': "Exit",
        'themes': "Themes", 'lang': "Language", 'light': "Light", 'dark': "Dark", 'system': "System",
        'author_btn': "Program Author", 'author_title': "Author", 'author_main': "Maxim Melnikov", 'author_label_text': "Developed by:",
        'ver_btn': "Program Version", 'ver_title': "Version", 'ver_main': "v1.9.7 Stable", 'ver_label_text': "Current build:",
        'update_btn': "Check for Updates", 'site_btn': "Project Site (GitHub)",
        'header': "Generation Settings", 'len_label': "Password Length (4-64):",
        'upper': "Uppercase", 'lower': "Lowercase", 'digits': "Digits", 'symb': "Symbols",
        'exclude': "Exclude similar", 'ambiguous': "Exclude ambiguous", 'hide': "Hide symbols",
        'at_least': "At least 1 from each category",
        'gen_btn': "GENERATE (Ctrl+G)", 'open_btn': "OPEN FILE (Ctrl+O)", 'copy_btn': "COPY PASSWORD", 'qr_btn': "PASSWORD QR-CODE",
        'history_btn': "HISTORY (5)", 'history_title': "Password History", 'history_empty': "History is empty",
        'strength': "Strength", 'qr_scan': "Scan with camera",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],
        'warn': "Warning", 'min_len': "Length 4-64", 'err': "Error", 'choose_set': "Select character sets",
        'check_input': "Check input", 'success': "Success!", 'pwd_done': "Password copied to clipboard",
        'save_title': "Save as", 'open_title': "Open Password", 'text_files': "Text files", 'all_files': "All files",
        'saved': "File saved.", 'no_pwd': "No password.", 'empty_file': "Empty file!",
        'crack_instantly': "Instantly", 'crack_seconds': "~{} sec.", 'crack_minutes': "~{} min.",
        'crack_hours': "~{} hrs.", 'crack_days': "~{} days.", 'crack_years': "~{} years",
        'crack_centuries': "~{} centuries", 'crack_never': "Practically impossible"
    },
    'ua': {
        'menu_file': "Файл", 'menu_opts': "Опції", 'menu_about': "Про програму",
        'save': "Зберегти (Ctrl+S)", 'save_as': "Зберегти як...", 'exit': "Вихід",
        'themes': "Теми", 'lang': "Мова", 'light': "Світла", 'dark': "Темна", 'system': "Системна",
        'author_btn': "Автор програми", 'author_title': "Автор", 'author_main': "Максим Мельников", 'author_label_text': "Програму розробив:",
        'ver_btn': "Версія програми", 'ver_title': "Версія", 'ver_main': "v1.9.7 Stable", 'ver_label_text': "Поточна збірка:",
        'update_btn': "Перевірити оновлення", 'site_btn': "Сайт проєкту (GitHub)",
        'header': "Налаштування генерації", 'len_label': "Довжина пароля (4-64):",
        'upper': "Великі літери", 'lower': "Малі літери", 'digits': "Цифри", 'symb': "Спецсимволи",
        'exclude': "Виключити схожі", 'ambiguous': "Виключити неоднозначні", 'hide': "Приховати символи",
        'at_least': "Мінімум 1 з кожної категорії",
        'gen_btn': "ЗГЕНЕРУВАТИ (Ctrl+G)", 'open_btn': "ВІДКРИТИ ФАЙЛ (Ctrl+O)", 'copy_btn': "КОПІЮВАТИ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'history_btn': "ІСТОРІЯ (5)", 'history_title': "Історія паролів", 'history_empty': "Історія порожня",
        'strength': "Складність", 'qr_scan': "Відскануйте камерою",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],
        'warn': "Увага", 'min_len': "Довжина від 4 до 64", 'err': "Помилка", 'choose_set': "Оберіть набори символів",
        'check_input': "Перевірте введення", 'success': "Успішно!", 'pwd_done': "Пароль копійовано",
        'save_title': "Зберегти як", 'open_title': "Відкрити пароль", 'text_files': "Текстові файли", 'all_files': "Усі файли",
        'saved': "Файл збережено.", 'no_pwd': "Немає пароля.", 'empty_file': "Файл порожній!",
        'crack_instantly': "Миттєво", 'crack_seconds': "~{} сек.", 'crack_minutes': "~{} хв.",
        'crack_hours': "~{} год.", 'crack_days': "~{} дн.", 'crack_years': "~{} років",
        'crack_centuries': "~{} століть", 'crack_never': "Майже неможливо"
    }
}

# =============================================================================
# MAIN APPLICATION CLASS / ГЛАВНЫЙ КЛАСС / ГОЛОВНИЙ КЛАС
# =============================================================================

class SecurePassApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Pass Pro")
        self.root.geometry("340x680")
        self.root.resizable(False, False)

        self.current_lang = 'ru'
        self.last_save_path = None
        self.history = []
        self.current_theme = 'system'
        # Correct path for icon / Корректный путь к иконке / Коректний шлях до іконки
        self.icon_path = resource_path("app_icon.ico")
        self.theme_registry = {'labels': [], 'checkbuttons': [], 'frames': [], 'entries': []}

        self.setup_variables()
        self.setup_ui()
        self.bind_shortcuts()
        self.set_icon(self.root)

        # Default theme without config / Тема по умолчанию без конфига / Тема за замовчуванням
        self.change_theme('system')
        self.change_lang('ru')

    def play_sound(self, sound_type="click"):
        """ Windows-specific sound feedback / Звуки для Windows / Звуки для Windows """
        if platform.system() == "Windows":
            try:
                if sound_type == "click": winsound.Beep(1000, 50)
                elif sound_type == "success": winsound.MessageBeep(winsound.MB_OK)
                elif sound_type == "error": winsound.MessageBeep(winsound.MB_ICONHAND)
            except: pass

    def set_icon(self, window):
        """ Set window icon safely / Установка иконки окна / Встановлення іконки вікна """
        if os.path.exists(self.icon_path):
            try: 
                window.iconbitmap(self.icon_path)
            except: 
                pass

    def _handle_shortcut(self, callback):
        callback()
        return "break"

    def bind_shortcuts(self):
        """ Hotkeys setup / Настройка горячих клавиш / Налаштування гарячих клавіш """
        shortcuts = {"<Control-s>": self.save_password, "<Control-o>": self.open_file, "<Control-g>": self.generate_password}
        for key, callback in shortcuts.items():
            self.root.bind(key, lambda e, cb=callback: self._handle_shortcut(cb))
            self.len_entry.bind(key, lambda e, cb=callback: self._handle_shortcut(cb))

    def setup_variables(self):
        """ App state variables / Переменные состояния / Змінні стану """
        self.length_var = tk.StringVar(value="12")
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_similar_var = tk.BooleanVar(value=True)
        self.exclude_ambiguous_var = tk.BooleanVar(value=False)
        self.at_least_one_var = tk.BooleanVar(value=True)
        self.hide_var = tk.BooleanVar(value=False)
        self.result_var = tk.StringVar()
        self.strength_var = tk.StringVar()
        self.crack_var = tk.StringVar()
        self.length_var.trace_add("write", self.validate_length)

    def validate_length(self, *args):
        """ Password length validation / Валидация длины / Валідація довжини """
        try:
            val = self.length_var.get().strip()
            num = int(val)
            color = "#4EC9B0" if self.current_theme == 'dark' else "#005FB8"
            self.len_entry.config(fg=color if 4 <= num <= 64 else "red")
        except (ValueError, AttributeError):
            try: self.len_entry.config(fg="red")
            except: pass

    def setup_ui(self):
        """ UI Construction / Построение интерфейса / Побудова інтерфейсу """
        self.menubar = tk.Menu(self.root)
        
        # Menu: File / Меню: Файл
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="Save", command=self.save_password)
        self.file_menu.add_command(label="Save as...", command=self.save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.destroy)
        self.menubar.add_cascade(label="File", menu=self.file_menu)

        # Menu: Options / Меню: Опции / Меню: Опції
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.theme_sub = tk.Menu(self.settings_menu, tearoff=0)
        self.theme_sub.add_command(label="Light", command=lambda: self.change_theme('light'))
        self.theme_sub.add_command(label="Dark", command=lambda: self.change_theme('dark'))
        self.theme_sub.add_command(label="System", command=lambda: self.change_theme('system'))
        self.settings_menu.add_cascade(label="Themes", menu=self.theme_sub)

        self.lang_sub = tk.Menu(self.settings_menu, tearoff=0)
        for code, name in [('ru', 'Русский'), ('en', 'English'), ('ua', 'Українська')]:
            self.lang_sub.add_command(label=name, command=lambda c=code: self.change_lang(c))
        self.settings_menu.add_cascade(label="Language", menu=self.lang_sub)
        self.menubar.add_cascade(label="Options", menu=self.settings_menu)

        # Menu: About / Меню: Про програму
        self.about_menu = tk.Menu(self.menubar, tearoff=0)
        self.about_menu.add_command(label="Author", command=lambda: self.show_custom_info('author_title', 'author_label_text', 'author_main', True))
        self.about_menu.add_command(label="Version", command=lambda: self.show_custom_info('ver_title', 'ver_label_text', 'ver_main', True))
        self.about_menu.add_command(label="Updates", command=lambda: webbrowser.open(UPDATE_URL))
        self.about_menu.add_command(label="GitHub", command=lambda: webbrowser.open(GITHUB_URL))
        self.menubar.add_cascade(label="About", menu=self.about_menu)
        self.root.config(menu=self.menubar)

        # Main elements
        self.header_label = tk.Label(self.root, font=("Arial", 11, "bold"))
        self.header_label.pack(pady=(10, 2))
        self.len_info_label = tk.Label(self.root, font=("Arial", 9))
        self.len_info_label.pack()
        self.len_entry = tk.Entry(self.root, textvariable=self.length_var, width=6, justify='center')
        self.len_entry.pack(pady=2)

        self.frame_checks = tk.Frame(self.root)
        self.frame_checks.pack(pady=2)
        self.cb_upper = tk.Checkbutton(self.frame_checks, variable=self.upper_var)
        self.cb_lower = tk.Checkbutton(self.frame_checks, variable=self.lower_var)
        self.cb_digits = tk.Checkbutton(self.frame_checks, variable=self.digits_var)
        self.cb_symb = tk.Checkbutton(self.frame_checks, variable=self.symbols_var)
        self.cb_at_least = tk.Checkbutton(self.frame_checks, variable=self.at_least_one_var)
        self.cb_exclude = tk.Checkbutton(self.frame_checks, variable=self.exclude_similar_var)
        self.cb_ambiguous = tk.Checkbutton(self.frame_checks, variable=self.exclude_ambiguous_var)
        self.cb_hide = tk.Checkbutton(self.frame_checks, variable=self.hide_var, command=lambda: self.result_entry.config(show="*" if self.hide_var.get() else ""))
        cbs = [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb, self.cb_at_least, self.cb_exclude, self.cb_ambiguous, self.cb_hide]
        for cb in cbs: cb.pack(anchor='w')

        self.btn_gen = tk.Button(self.root, command=self.generate_password, width=22, relief='flat', cursor="hand2")
        self.btn_gen.pack(pady=(8, 2))
        self.btn_open = tk.Button(self.root, command=self.open_file, width=22, relief='flat', cursor="hand2")
        self.btn_open.pack(pady=2)

        self.result_entry = tk.Entry(self.root, textvariable=self.result_var, font=("Consolas", 12), width=22, state='readonly', justify='center')
        self.result_entry.pack(pady=4)

        self.strength_canvas = tk.Canvas(self.root, width=200, height=6)
        self.strength_canvas.pack()
        self.strength_label_widget = tk.Label(self.root, textvariable=self.strength_var, font=("Arial", 9, "italic"))
        self.strength_label_widget.pack()
        self.crack_canvas = tk.Canvas(self.root, width=200, height=4)
        self.crack_canvas.pack(pady=(4, 0))
        self.crack_label_widget = tk.Label(self.root, textvariable=self.crack_var, font=("Arial", 8))
        self.crack_label_widget.pack()

        self.btn_copy = tk.Button(self.root, command=self.copy_to_clipboard, width=22, relief='flat', cursor="hand2")
        self.btn_copy.pack(pady=5)
        self.btn_qr = tk.Button(self.root, command=self.generate_qr, width=22, relief='flat', cursor="hand2")
        self.btn_qr.pack(pady=2)
        self.btn_history = tk.Button(self.root, command=self.show_history, width=22, relief='flat', cursor="hand2")
        self.btn_history.pack(pady=2)

        self.stars_label = tk.Label(self.root, text="★★★★★", font=("Arial", 12, "bold"), fg="#FFD700")
        self.stars_label.pack(side='bottom', pady=(0, 5))
        self.author_label = tk.Label(self.root, text="GitHub ©", cursor="hand2", font=("Arial", 8, "bold"), padx=8, pady=3)
        self.author_label.pack(side='bottom', pady=2)
        self.author_label.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))

        self.theme_registry['frames'] = [self.root, self.frame_checks]
        self.theme_registry['labels'] = [self.header_label, self.len_info_label, self.strength_label_widget]
        self.theme_registry['checkbuttons'] = cbs
        self.theme_registry['entries'] = [self.len_entry]

    def change_lang(self, lang_code):
        """ Multi-language engine / Система языков / Система мов """
        self.current_lang = lang_code
        L = LANGUAGES[lang_code]
        self.menubar.entryconfig(1, label=L['menu_file'])
        self.menubar.entryconfig(2, label=L['menu_opts'])
        self.menubar.entryconfig(3, label=L['menu_about'])
        self.file_menu.entryconfig(0, label=L['save'])
        self.file_menu.entryconfig(1, label=L['save_as'])
        self.file_menu.entryconfig(3, label=L['exit'])
        self.settings_menu.entryconfig(0, label=L['themes'])
        self.settings_menu.entryconfig(1, label=L['lang'])
        self.theme_sub.entryconfig(0, label=L['light'])
        self.theme_sub.entryconfig(1, label=L['dark'])
        self.theme_sub.entryconfig(2, label=L['system'])
        self.about_menu.entryconfig(0, label=L['author_btn'])
        self.about_menu.entryconfig(1, label=L['ver_btn'])
        self.about_menu.entryconfig(2, label=L['update_btn'])
        self.about_menu.entryconfig(3, label=L['site_btn'])
        self.header_label.config(text=L['header'])
        self.len_info_label.config(text=L['len_label'])
        self.cb_upper.config(text=L['upper'])
        self.cb_lower.config(text=L['lower'])
        self.cb_digits.config(text=L['digits'])
        self.cb_symb.config(text=L['symb'])
        self.cb_exclude.config(text=L['exclude'])
        self.cb_ambiguous.config(text=L['ambiguous'])
        self.cb_at_least.config(text=L['at_least'])
        self.cb_hide.config(text=L['hide'])
        self.btn_gen.config(text=L['gen_btn'])
        self.btn_open.config(text=L['open_btn'])
        self.btn_copy.config(text=L['copy_btn'])
        self.btn_qr.config(text=L['qr_btn'])
        self.btn_history.config(text=L['history_btn'].format(len(self.history)))
        if self.result_var.get(): self.update_strength_meter(self.result_var.get())

    def change_theme(self, mode):
        """ Visual themes engine / Смена визуальных тем / Зміна візуальних тем """
        if mode == 'system':
            mode = 'light'
            if platform.system() == "Windows":
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    mode = 'light' if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 1 else 'dark'
                except: pass
        self.current_theme = mode
        if mode == 'dark':
            bg, fg, res_bg, res_fg = '#000000', '#FFFFFF', '#000000', '#4EC9B0'
            c_gen, c_copy, c_qr, c_hist = '#005FB8', '#107C10', '#68217A', '#3E3E42'
            entry_bg, select_clr = '#121212', '#1A1A1A'
        else:
            bg, fg, res_bg, res_fg = '#F3F3F3', '#000000', '#FFFFFF', '#005FB8'
            c_gen, c_copy, c_qr, c_hist = '#CCE4F7', '#DFF6DD', '#F2E5F5', '#E1E1E1'
            entry_bg, select_clr = '#FFFFFF', '#FFFFFF'
        
        for f in self.theme_registry['frames']: f.config(bg=bg)
        for l in self.theme_registry['labels']: l.config(bg=bg, fg=fg)
        for cb in self.theme_registry['checkbuttons']: cb.config(bg=bg, fg=fg, selectcolor=select_clr, activebackground=bg, activeforeground=fg)
        for e in self.theme_registry['entries']: e.config(bg=entry_bg, fg=fg, insertbackground=fg)
        
        self.strength_canvas.config(bg=bg, highlightthickness=0)
        self.crack_canvas.config(bg=bg, highlightthickness=0)
        self.result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
        self.stars_label.config(bg=bg)
        self.author_label.config(bg='#1A1A1A' if mode == 'dark' else '#E1E1E1', fg=fg)
        self.crack_label_widget.config(bg=bg, fg='#FFFFFF' if mode == 'dark' else '#888888')
        
        def apply_btn(btn, clr): btn.config(bg=clr, fg=fg if mode == 'dark' else '#000000', activebackground=clr)
        apply_btn(self.btn_gen, c_gen)
        apply_btn(self.btn_copy, c_copy)
        apply_btn(self.btn_qr, c_qr)
        apply_btn(self.btn_history, c_hist)
        apply_btn(self.btn_open, '#333333' if mode == 'dark' else '#E1E1E1')
        self.validate_length()

    def generate_password(self):
        """ Core password generation / Генерация пароля / Генерація пароля """
        self.play_sound("click")
        L = LANGUAGES[self.current_lang]
        try:
            length = int(self.length_var.get().strip())
            if not (4 <= length <= 64): raise ValueError()
            cats = []
            if self.upper_var.get(): cats.append(string.ascii_uppercase)
            if self.lower_var.get(): cats.append(string.ascii_lowercase)
            if self.digits_var.get(): cats.append(string.digits)
            if self.symbols_var.get(): cats.append(string.punctuation)
            if not cats:
                self.play_sound("error")
                messagebox.showerror(L['err'], L['choose_set'])
                return
            
            ex = ("Il1O0" if self.exclude_similar_var.get() else "") + (".,:;'~\"/()[]{}|" if self.exclude_ambiguous_var.get() else "")
            f_cats = [''.join(c for c in cat if c not in ex) for cat in cats if any(c not in ex for c in cat)]
            if not f_cats:
                self.play_sound("error")
                messagebox.showerror(L['err'], L['choose_set'])
                return
            
            all_chars = "".join(f_cats)
            pwd_list = []
            if self.at_least_one_var.get() and length >= len(f_cats):
                for c in f_cats: pwd_list.append(secrets.choice(c))
                for _ in range(length - len(f_cats)): pwd_list.append(secrets.choice(all_chars))
            else:
                for _ in range(length): pwd_list.append(secrets.choice(all_chars))
            
            secrets.SystemRandom().shuffle(pwd_list)
            password = "".join(pwd_list)
            self.history.insert(0, password)
            if len(self.history) > 5: self.history.pop()
            self.result_var.set(password)
            self.update_strength_meter(password)
            self.btn_history.config(text=L['history_btn'].format(len(self.history)))
        except ValueError:
            self.play_sound("error")
            messagebox.showerror(L['err'], L['check_input'])

    def update_strength_meter(self, password):
        """ Password analysis UI / Анализ сложности / Аналіз складності """
        self.strength_canvas.delete("all")
        self.crack_canvas.delete("all")
        L = LANGUAGES[self.current_lang]
        if not password: return
        
        entropy = self.calculate_entropy(password)
        score = self.get_strength_score(entropy)
        colors = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]
        
        self.strength_canvas.create_rectangle(0, 0, 200, 6, fill="#333333", outline="")
        self.strength_canvas.create_rectangle(0, 0, (score + 1) * 33.33, 6, fill=colors[score], outline="")
        self.strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]} ({int(entropy)} bit)")
        
        c_score, c_text = self.estimate_crack_time(password)
        self.crack_var.set(c_text)
        b_clr = "#e74c3c" if entropy < 40 else ("#f39c12" if entropy < 80 else "#27ae60")
        self.crack_canvas.create_rectangle(0, 0, 200, 4, fill="#333333", outline="")
        self.crack_canvas.create_rectangle(0, 0, min(200, (c_score + 1) * 25), 4, fill=b_clr, outline="")

    def calculate_entropy(self, password):
        """ Math entropy calculation / Расчет энтропии / Розрахунок ентропії """
        sz = 0
        if any(c.islower() for c in password): sz += 26
        if any(c.isupper() for c in password): sz += 26
        if any(c.isdigit() for c in password): sz += 10
        if any(c in string.punctuation for c in password): sz += 32
        return len(password) * math.log2(sz) if sz > 0 else 0

    def get_strength_score(self, entropy):
        if entropy < 28: return 0
        if entropy < 36: return 1
        if entropy < 60: return 2
        if entropy < 80: return 3
        if entropy < 100: return 4
        return 5

    def estimate_crack_time(self, password):
        """ Crack time estimation (MD5) / Оценка времени взлома / Оцінка часу злому """
        entropy = self.calculate_entropy(password)
        sec = (2 ** entropy) / CRACK_SPEED
        L = LANGUAGES[self.current_lang]
        if sec < 0.1: return 0, L['crack_instantly']
        elif sec < 60: return 1, L['crack_seconds'].format(int(sec))
        elif sec < 3600: return 2, L['crack_minutes'].format(int(sec // 60))
        elif sec < 86400: return 3, L['crack_hours'].format(int(sec // 3600))
        elif sec < 86400 * 365: return 4, L['crack_days'].format(int(sec // 86400))
        elif sec < 86400 * 365 * 100: return 5, L['crack_years'].format(int(sec // (86400 * 365)))
        elif sec < 86400 * 365 * 10000: return 6, L['crack_centuries'].format(int(sec // (86400 * 365 * 100)))
        else: return 7, L['crack_never']

    def save_password(self):
        """ Save to file / Сохранение в файл / Збереження у файл """
        p = self.result_var.get()
        L = LANGUAGES[self.current_lang]
        if not p:
            self.play_sound("error")
            messagebox.showwarning(L['warn'], L['no_pwd'])
            return
        if self.last_save_path and os.path.exists(os.path.dirname(self.last_save_path)):
            try:
                with open(self.last_save_path, "w", encoding="utf-8") as f: f.write(p)
                self.play_sound("success")
                self.show_custom_info('success', 'success', 'saved', is_static=True)
            except OSError as e: messagebox.showerror(L['err'], str(e))
        else: self.save_as()

    def save_as(self):
        L = LANGUAGES[self.current_lang]
        p = self.result_var.get()
        if not p:
            self.play_sound("error")
            messagebox.showwarning(L['warn'], L['no_pwd'])
            return
        path = filedialog.asksaveasfilename(title=L['save_title'], initialfile="Pass.txt", defaultextension=".txt", filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")])
        if path:
            try:
                self.last_save_path = path
                with open(path, "w", encoding="utf-8") as f: f.write(p)
                self.play_sound("success")
                self.show_custom_info('success', 'success', 'saved', is_static=True)
            except OSError as e: messagebox.showerror(L['err'], str(e))

    def open_file(self):
        """ Open from file / Открытие файла / Відкриття файлу """
        L = LANGUAGES[self.current_lang]
        path = filedialog.askopenfilename(title=L['open_title'], filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f: content = f.read().strip()
                if not content:
                    messagebox.showinfo(L['warn'], L['empty_file'])
                    return
                self.result_var.set(content)
                self.update_strength_meter(content)
                self.play_sound("success")
            except OSError as e: messagebox.showerror(L['err'], str(e))

    def show_history(self):
        """ History window / Окно истории / Вікно історії """
        self.play_sound("click")
        L = LANGUAGES[self.current_lang]
        win = tk.Toplevel(self.root)
        win.title(L['history_title'])
        win.resizable(False, False)
        self.set_icon(win)
        self.center_child(win, self.root, 300, 250)
        cur_bg = self.root.cget("bg")
        win.configure(bg=cur_bg)
        cur_fg = "#FFFFFF" if self.current_theme == 'dark' else "#000000"
        if not self.history:
            tk.Label(win, text=L['history_empty'], bg=cur_bg, fg=cur_fg, font=("Arial", 10)).pack(expand=True)
        else:
            for pwd in self.history:
                btn = tk.Button(win, text=pwd, font=("Consolas", 10), relief='flat', bg=cur_bg, fg="#4EC9B0" if self.current_theme == 'dark' else "#005FB8", activebackground='#1A1A1A' if self.current_theme == 'dark' else '#E1E1E1', cursor="hand2", command=lambda p=pwd, w=win: self.select_from_history(p, w))
                btn.pack(pady=5, fill='x', padx=20)

    def select_from_history(self, pwd, window):
        self.play_sound("click")
        self.result_var.set(pwd)
        self.update_strength_meter(pwd)
        self.copy_to_clipboard()
        window.destroy()

    def generate_qr(self):
        """ QR Generator / Создание QR-кода / Створення QR-коду """
        self.play_sound("click")
        pwd = self.result_var.get()
        L = LANGUAGES[self.current_lang]
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
        qr_f, qr_b = ("white", "black") if self.current_theme == 'dark' else ("black", "white")
        try:
            qr = qrcode.QRCode(box_size=8, border=2)
            qr.add_data(pwd)
            qr.make(fit=True)
            img = qr.make_image(fill_color=qr_f, back_color=qr_b)
            img_tk = ImageTk.PhotoImage(img.resize((220, 220), Image.LANCZOS))
            tk.Label(win, text=L['qr_scan'], bg=cur_bg, fg=qr_f).pack(pady=(10, 0))
            lbl = tk.Label(win, image=img_tk, bg=cur_bg)
            lbl.image = img_tk
            lbl.pack(pady=10)
            tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat', bg=self.author_label.cget("bg"), fg=qr_f).pack(pady=5)
        except Exception as e:
            messagebox.showerror(L['err'], str(e))
            win.destroy()

    def copy_to_clipboard(self):
        """ Copy to clipboard / Копирование / Копіювання """
        p = self.result_var.get()
        if p:
            L = LANGUAGES[self.current_lang]
            self.play_sound("success")
            self.root.clipboard_clear()
            self.root.clipboard_append(p)
            self.root.after(60000, lambda: self.root.clipboard_clear() if self.root.winfo_exists() else None)
            self.show_custom_info('pwd_done', 'success', 'pwd_done', is_static=True, width=320)

    def show_custom_info(self, title_key, label_key, main_val_key, is_static=True, width=280):
        """ Custom info windows / Инфо-окна / Інфо-вікна """
        L = LANGUAGES[self.current_lang]
        win = tk.Toplevel(self.root)
        win.title(L[title_key] if is_static else title_key)
        self.set_icon(win)
        self.center_child(win, self.root, width, 180)
        cur_bg = self.root.cget("bg")
        win.configure(bg=cur_bg)
        cur_fg = "#FFFFFF" if self.current_theme == 'dark' else "#000000"
        tk.Label(win, text=L[label_key] if is_static else label_key, bg=cur_bg, fg=cur_fg, font=("Arial", 9)).pack(pady=(20, 5))
        tk.Label(win, text=L[main_val_key] if is_static else main_val_key, bg=cur_bg, fg="#4EC9B0" if self.current_theme == 'dark' else "#005FB8", font=("Arial", 11, "bold")).pack(pady=5)
        tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat', bg='#1A1A1A' if self.current_theme == 'dark' else '#E1E1E1', fg=cur_fg).pack(pady=20)

    def center_child(self, child, parent, w, h):
        """ UI Helper / Центрирование окон / Центрування вікон """
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        child.geometry(f"{w}x{h}+{px + (pw - w)//2}+{py + (ph - h)//2}")

# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА / ТОЧКА ВХОДУ
# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurePassApp(root)
    root.mainloop()