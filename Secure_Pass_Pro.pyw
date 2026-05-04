import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import os
import sys
import platform

# =============================================================================
# DEPENDENCIES / ЗАВИСИМОСТИ / ЗАЛЕЖНОСТІ
# =============================================================================
try:
    import qrcode
    from PIL import ImageTk, Image
except ImportError:
    # Critical for distribution / Критично для дистрибуции / Критично для дистрибуції
    print("Missing dependencies! Please run: pip install qrcode[pil] pillow")
    sys.exit(1)

# High DPI Support (Windows only) / Поддержка высокого разрешения
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

# =============================================================================
# RESOURCE PATH / ПУТЬ К РЕСУРСАМ / ШЛЯХ ДО РЕСУРСІВ
# =============================================================================
def resource_path(relative_path):
    """Essential for PyInstaller .exe / Важно для сборки в .exe / Важливо для збірки в .exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =============================================================================
# SOUND LOGIC / ЗВУКОВАЯ ЛОГИКА / ЗВУКОВА ЛОГІКА
# =============================================================================
def play_gen_sound():
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(1000, 50)
        except Exception: pass

def play_success_sound():
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(1500, 100)
            winsound.Beep(2000, 100)
        except Exception: pass

# =============================================================================
# CONSTANTS & TRANSLATIONS / КОНСТАНТЫ И ПЕРЕВОДЫ
# =============================================================================
UPDATE_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"

LANGUAGES = {
    'ru': {
        'menu_file': "Файл", 'menu_opts': "Опции", 'menu_about': "О программе",
        'save': "Сохранить", 'save_as': "Сохранить как...", 'exit': "Выход",
        'themes': "Темы", 'lang': "Язык", 'light': "Светлая", 'dark': "Тёмная", 'system': "Системная",
        'author_btn': "Автор программы", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Программу разработал:",
        'ver_btn': "Версия программы", 'ver_title': "Версия", 'ver_main': "v1.9.2 Stable", 'ver_label_text': "Текущая сборка:",
        'update_btn': "Проверить обновления", 'site_btn': "Сайт проекта (GitHub)",
        'header': "Настройки генерации", 'len_label': "Длина пароля (4-64):",
        'upper': "Заглавные буквы", 'lower': "Строчные буквы", 'digits': "Цифры", 'symb': "Спецсимволы",
        'exclude': "Исключить похожие (0/O, 1/l/I)", 'ambiguous': "Исключить неоднозначные", 'hide': "Скрывать символы",
        'at_least': "Минимум 1 из каждой категории",
        'gen_btn': "СГЕНЕРИРОВАТЬ", 'open_btn': "ОТКРЫТЬ ФАЙЛ", 'copy_btn': "КОПИРОВАТЬ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'strength': "Сложность", 'qr_scan': "Отсканируйте камерой",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],
        'warn': "Внимание", 'min_len': "Длина должна быть от 4 до 64", 'err': "Ошибка", 'choose_set': "Выберите наборы символов",
        'check_input': "Проверьте ввод", 'copied': "Пароль скопирован. Очистка через 60 сек.", 'success': "Успешно!",
        'save_title': "Сохранить как", 'open_title': "Открыть пароль", 'text_files': "Текстовые файлы", 'all_files': "Все файлы",
        'saved': "Файл сохранён.", 'no_pwd': "Нет пароля для сохранения.", 'empty_file': "Файл пуст!",
        'crack_instantly': "Взломают мгновенно", 'crack_seconds': "Взломают за ~{} сек.", 'crack_minutes': "Взломают за ~{} мин.",
        'crack_hours': "Взломают за ~{} ч.", 'crack_days': "Взломают за ~{} дн.", 'crack_years': "Взломают за ~{} лет",
        'crack_centuries': "Взломают за ~{} веков", 'crack_never': "Практически невозможно взломать"
    },
    'en': {
        'menu_file': "File", 'menu_opts': "Options", 'menu_about': "About",
        'save': "Save", 'save_as': "Save as...", 'exit': "Exit",
        'themes': "Themes", 'lang': "Language", 'light': "Light", 'dark': "Dark", 'system': "System",
        'author_btn': "Program Author", 'author_title': "Author", 'author_main': "Maxim Melnikov", 'author_label_text': "Developed by:",
        'ver_btn': "Program Version", 'ver_title': "Version", 'ver_main': "v1.9.2 Stable", 'ver_label_text': "Current build:",
        'update_btn': "Check for Updates", 'site_btn': "Project Site (GitHub)",
        'header': "Generation Settings", 'len_label': "Password Length (4-64):",
        'upper': "Uppercase", 'lower': "Lowercase", 'digits': "Digits", 'symb': "Symbols",
        'exclude': "Exclude similar (0/O, 1/l/I)", 'ambiguous': "Exclude ambiguous", 'hide': "Hide symbols",
        'at_least': "At least 1 from each category",
        'gen_btn': "GENERATE", 'open_btn': "OPEN FILE", 'copy_btn': "COPY PASSWORD", 'qr_btn': "PASSWORD QR-CODE",
        'strength': "Strength", 'qr_scan': "Scan with camera",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],
        'warn': "Warning", 'min_len': "Length must be between 4 and 64", 'err': "Error", 'choose_set': "Select character sets",
        'check_input': "Check input", 'copied': "Password copied. Clear in 60 sec.", 'success': "Success!",
        'save_title': "Save as", 'open_title': "Open Password", 'text_files': "Text files", 'all_files': "All files",
        'saved': "File saved.", 'no_pwd': "No password to save.", 'empty_file': "File is empty!",
        'crack_instantly': "Cracked instantly", 'crack_seconds': "Cracked in ~{} sec.", 'crack_minutes': "Cracked in ~{} min.",
        'crack_hours': "Cracked in ~{} hrs.", 'crack_days': "Cracked in ~{} days", 'crack_years': "Cracked in ~{} years",
        'crack_centuries': "Cracked in ~{} centuries", 'crack_never': "Practically uncrackable"
    },
    'ua': {
        'menu_file': "Файл", 'menu_opts': "Опції", 'menu_about': "Про программу",
        'save': "Зберегти", 'save_as': "Зберегти как...", 'exit': "Вихід",
        'themes': "Теми", 'lang': "Мова", 'light': "Світла", 'dark': "Темна", 'system': "Системна",
        'author_btn': "Автор програми", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Програму розробив:",
        'ver_btn': "Версія програми", 'ver_title': "Версія", 'ver_main': "v1.9.2 Stable", 'ver_label_text': "Поточна збірка:",
        'update_btn': "Перевірити оновлення", 'site_btn': "Сайт проєкту (GitHub)",
        'header': "Налаштування генерації", 'len_label': "Довжина пароля (4-64):",
        'upper': "Великі літери", 'lower': "Малі літери", 'digits': "Цифри", 'symb': "Спецсимволи",
        'exclude': "Виключити схожі (0/O, 1/l/I)", 'ambiguous': "Виключити неоднозначні", 'hide': "Приховати символи",
        'at_least': "Мінімум 1 з кожної категорії",
        'gen_btn': "ЗГЕНЕРУВАТИ", 'open_btn': "ВІДКРИТИ ФАЙЛ", 'copy_btn': "КОПІЮВАТИ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'strength': "Складність", 'qr_scan': "Відскануйте камерою",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],
        'warn': "Увага", 'min_len': "Довжина має бути від 4 до 64", 'err': "Помилка", 'choose_set': "Оберіть набори символів",
        'check_input': "Перевірте введення", 'copied': "Пароль копійовано. Очистка через 60 сек.", 'success': "Успішно!",
        'save_title': "Зберегти як", 'open_title': "Відкрити пароль", 'text_files': "Текстові файлы", 'all_files': "Усі файли",
        'saved': "Файл збережено.", 'no_pwd': "Немає пароля для збереження.", 'empty_file': "Файл порожній!",
        'crack_instantly': "Зламають миттєво", 'crack_seconds': "Зламають за ~{} сек.", 'crack_minutes': "Зламають за ~{} хв.",
        'crack_hours': "Зламають за ~{} год.", 'crack_days': "Зламають за ~{} дн.", 'crack_years': "Зламають за ~{} років",
        'crack_centuries': "Зламають за ~{} віків", 'crack_never': "Практично неможливо зламати"
    }
}

# =============================================================================
# UTILS / СЛУЖЕБНЫЕ / СЛУЖБОВІ
# =============================================================================
current_lang = 'ru'

def calculate_password_strength(password):
    """DRY: Unified strength logic / Единая логика оценки сложности"""
    if not password: return -1
    length = len(password)
    variety = sum([any(c.isupper() for c in password), any(c.islower() for c in password), 
                   any(c.isdigit() for c in password), any(c in string.punctuation for c in password)])
    if length < 10: return 0 if variety < 2 else 1
    elif 10 <= length < 14: return 2 if variety < 3 else 3
    else: return 4 if variety < 4 else 5

def set_icon(window):
    """App icon loader / Загрузка иконки приложения"""
    try:
        icon_p = resource_path("app_icon.ico")
        if os.path.exists(icon_p):
            window.iconbitmap(icon_p)
    except: pass

def center_child(child, width, height):
    root.update_idletasks()
    main_x, main_y = root.winfo_x(), root.winfo_y()
    main_width, main_height = root.winfo_width(), root.winfo_height()
    x = main_x + (main_width // 2) - (width // 2)
    y = main_y + (main_height // 2) - (height // 2)
    child.geometry(f"{width}x{height}+{x}+{y}")

# =============================================================================
# APP LOGIC / ЛОГИКА / ЛОГІКА
# =============================================================================
def estimate_crack_time(password):
    if not password: return -1, ""
    charset = 0
    if any(c.islower() for c in password): charset += 26
    if any(c.isupper() for c in password): charset += 26
    if any(c.isdigit() for c in password): charset += 10
    if any(c in string.punctuation for c in password): charset += 32
    
    combinations = (charset ** len(password)) if charset > 0 else 0
    seconds = combinations / 10_000_000_000 
    L = LANGUAGES[current_lang]
    if seconds < 1: return 0, L['crack_instantly']
    elif seconds < 60: return 1, L['crack_seconds'].format(int(seconds))
    elif seconds < 3600: return 2, L['crack_minutes'].format(int(seconds // 60))
    elif seconds < 86400: return 3, L['crack_hours'].format(int(seconds // 3600))
    elif seconds < 86400 * 365: return 4, L['crack_days'].format(int(seconds // 86400))
    elif seconds < 86400 * 365 * 100: return 5, L['crack_years'].format(int(seconds // (86400 * 365)))
    elif seconds < 86400 * 365 * 10000: return 6, L['crack_centuries'].format(int(seconds // (86400 * 365 * 100)))
    else: return 7, L['crack_never']

def change_lang(lang_code):
    global current_lang
    current_lang = lang_code
    L = LANGUAGES[lang_code]
    # Update menus / Обновление меню
    menubar.entryconfig(1, label=L['menu_file'])
    menubar.entryconfig(2, label=L['menu_opts'])
    menubar.entryconfig(3, label=L['menu_about'])
    file_menu.entryconfig(0, label=L['save']); file_menu.entryconfig(1, label=L['save_as']); file_menu.entryconfig(3, label=L['exit'])
    settings_menu.entryconfig(0, label=L['themes']); settings_menu.entryconfig(1, label=L['lang'])
    theme_sub.entryconfig(0, label=L['light']); theme_sub.entryconfig(1, label=L['dark']); theme_sub.entryconfig(2, label=L['system'])
    about_menu.entryconfig(0, label=L['author_btn']); about_menu.entryconfig(1, label=L['ver_btn'])
    about_menu.entryconfig(2, label=L['update_btn']); about_menu.entryconfig(3, label=L['site_btn'])
    # Update UI / Обновление интерфейса
    header_label.config(text=L['header']); len_info_label.config(text=L['len_label'])
    btn_gen.config(text=L['gen_btn']); btn_open.config(text=L['open_btn'])
    btn_copy.config(text=L['copy_btn']); btn_qr.config(text=L['qr_btn'])
    cb_upper.config(text=L['upper']); cb_lower.config(text=L['lower'])
    cb_digits.config(text=L['digits']); cb_symb.config(text=L['symb'])
    cb_exclude.config(text=L['exclude']); cb_ambiguous.config(text=L['ambiguous'])
    cb_hide.config(text=L['hide']); cb_at_least.config(text=L['at_least'])
    update_strength_meter(calculate_password_strength(result_var.get()), result_var.get())

def change_theme(mode):
    if mode == 'system':
        mode = 'light'
        if platform.system() == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                mode = 'light' if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] == 1 else 'dark'
            except: pass
    
    if mode == 'dark':
        bg, fg, res_bg, res_fg = '#000000', '#FFFFFF', '#000000', '#4EC9B0'
        c_gen, c_copy, c_qr = '#005FB8', '#107C10', '#68217A'
    else:
        bg, fg, res_bg, res_fg = '#F3F3F3', '#000000', '#FFFFFF', '#005FB8'
        c_gen, c_copy, c_qr = '#CCE4F7', '#DFF6DD', '#F2E5F5'

    root.configure(bg=bg)
    result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
    frame_checks.config(bg=bg)
    strength_canvas.config(bg=bg, highlightthickness=0); crack_canvas.config(bg=bg, highlightthickness=0)
    
    def apply_btn(btn, clr):
        btn.config(bg=clr, fg=fg if mode=='dark' else '#000000', activebackground=clr)
    
    apply_btn(btn_gen, c_gen); apply_btn(btn_copy, c_copy); apply_btn(btn_qr, c_qr)
    apply_btn(btn_open, '#333333' if mode=='dark' else '#E1E1E1')

    def style_recursive(parent):
        for w in parent.winfo_children():
            if isinstance(w, tk.Frame): style_recursive(w)
            elif isinstance(w, tk.Label) and w not in [author_label, stars_label]: w.config(bg=bg, fg=fg)
            elif isinstance(w, tk.Checkbutton): w.config(bg=bg, fg=fg, selectcolor='#1A1A1A' if mode=='dark' else '#FFFFFF', activebackground=bg)
            elif isinstance(w, tk.Entry) and w != result_entry: w.config(bg='#121212' if mode=='dark' else '#FFFFFF', fg=fg, insertbackground=fg)

    style_recursive(root)
    strength_label_widget.config(bg=bg, fg=fg); stars_label.config(bg=bg)
    author_label.config(bg='#1A1A1A' if mode=='dark' else '#E1E1E1', fg=fg)
    crack_label_widget.config(bg=bg, fg='#FFFFFF' if mode=='dark' else '#888888')

def generate_qr():
    pwd = result_var.get()
    L = LANGUAGES[current_lang]
    if not pwd: messagebox.showwarning(L['warn'], L['no_pwd']); return
    qr_win = tk.Toplevel(root); qr_win.title("QR Code"); qr_win.resizable(False, False)
    set_icon(qr_win) 
    center_child(qr_win, 300, 380)
    cur_bg = root.cget("bg")
    qr_win.configure(bg=cur_bg)
    qr_f = "white" if cur_bg == "#000000" else "black"
    qr_b = "black" if cur_bg == "#000000" else "white"
    
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(pwd); qr.make(fit=True)
    img = qr.make_image(fill_color=qr_f, back_color=qr_b)
    img_tk = ImageTk.PhotoImage(img.resize((220, 220), Image.LANCZOS))
    
    tk.Label(qr_win, text=L['qr_scan'], bg=cur_bg, fg=qr_f).pack(pady=(10, 0))
    l = tk.Label(qr_win, image=img_tk, bg=cur_bg); l.image = img_tk; l.pack(pady=10)
    tk.Button(qr_win, text="OK", command=qr_win.destroy, width=10, relief='flat', bg=author_label.cget("bg"), fg=qr_f).pack(pady=5)

def update_strength_meter(score, password=""):
    strength_canvas.delete("all"); crack_canvas.delete("all")
    L = LANGUAGES[current_lang]
    if score == -1: strength_var.set(""); crack_var.set(""); return
    
    clrs = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]
    strength_canvas.create_rectangle(0, 0, 200, 6, fill="#333333", outline="")
    strength_canvas.create_rectangle(0, 0, (score + 1) * 33.33, 6, fill=clrs[score], outline="")
    strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]}")
    
    if password:
        c_score, c_text = estimate_crack_time(password)
        crack_var.set(c_text)
        b_clr = "#e74c3c" if len(password) <= 4 else ("#f39c12" if len(password) <= 10 else "#27ae60")
        crack_canvas.create_rectangle(0, 0, 200, 4, fill="#333333", outline="")
        crack_canvas.create_rectangle(0, 0, (c_score + 1) * 25, 4, fill=b_clr, outline="")

def generate_password():
    L = LANGUAGES[current_lang]
    try:
        length = int(length_var.get().strip())
        if not (4 <= length <= 64): raise ValueError
        cats = []
        if upper_var.get(): cats.append(string.ascii_uppercase)
        if lower_var.get(): cats.append(string.ascii_lowercase)
        if digits_var.get(): cats.append(string.digits)
        if symbols_var.get(): cats.append(string.punctuation)
        if not cats: messagebox.showerror(L['err'], L['choose_set']); return
        
        if exclude_similar_var.get(): cats = [''.join(c for c in cat if c not in "Il1O0") for cat in cats]
        if exclude_ambiguous_var.get(): cats = [''.join(c for c in cat if c not in ".,:;\'~\"/()[]{}|") for cat in cats]
        
        all_c = "".join(cats)
        if not all_c: messagebox.showerror(L['err'], L['choose_set']); return
        
        p_list = []
        if at_least_one_var.get() and length >= len(cats):
            for c in cats: p_list.append(secrets.choice(c))
            for _ in range(length - len(cats)): p_list.append(secrets.choice(all_c))
        else:
            for _ in range(length): p_list.append(secrets.choice(all_c))
        
        secrets.SystemRandom().shuffle(p_list)
        pwd = "".join(p_list)
        result_var.set(pwd); result_entry.config(show="*" if hide_var.get() else "")
        play_gen_sound(); update_strength_meter(calculate_password_strength(pwd), pwd)
    except: messagebox.showerror(L['err'], L['check_input'])

def copy_to_clipboard():
    p = result_var.get()
    if p:
        root.clipboard_clear(); root.clipboard_append(p)
        play_success_sound()
        root.after(60000, lambda: root.clipboard_clear() if root.winfo_exists() else None)
        show_custom_info('success', 'success', LANGUAGES[current_lang]['copied'], width=320)

def save_as():
    L = LANGUAGES[current_lang]
    p = result_var.get()
    if not p: messagebox.showwarning(L['warn'], L['no_pwd']); return
    path = filedialog.asksaveasfilename(title=L['save_title'], initialfile="Pass.txt", defaultextension=".txt", 
                                       filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")])
    if path:
        try:
            with open(path, "w", encoding="utf-8") as f: f.write(p)
            play_success_sound(); show_custom_info('success', 'success', L['saved'])
        except Exception as e: messagebox.showerror(L['err'], str(e))

def open_file():
    L = LANGUAGES[current_lang]
    path = filedialog.askopenfilename(title=L['open_title'], filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")])
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                c = f.read().strip()
                if not c: messagebox.showinfo(L['warn'], L['empty_file']); return
                result_var.set(c); update_strength_meter(calculate_password_strength(c), c)
        except Exception as e: messagebox.showerror(L['err'], str(e))

def show_custom_info(title_key, label_key, main_val, is_static=True, width=280):
    L = LANGUAGES[current_lang]
    win = tk.Toplevel(root); win.title(L.get(title_key, title_key)); win.resizable(False, False)
    set_icon(win)
    center_child(win, width, 140)
    cur_bg = root.cget("bg")
    win.configure(bg=cur_bg)
    cur_fg = "#000000" if cur_bg == "#F3F3F3" else "#FFFFFF"
    tk.Label(win, text=L.get(label_key, label_key), bg=cur_bg, fg=cur_fg).pack(pady=(15, 2))
    tk.Label(win, text=main_val if is_static else L.get(main_val, main_val), font=("Arial", 10, "bold"), bg=cur_bg, fg=cur_fg).pack(pady=5)
    tk.Button(win, text="OK", command=win.destroy, width=10, relief='flat', bg=author_label.cget("bg"), fg=cur_fg).pack(pady=10)

# =============================================================================
# MAIN WINDOW / ГЛАВНОЕ ОКНО
# =============================================================================
root = tk.Tk()
root.title("Secure Pass Pro")
root.geometry("340x650"); root.resizable(False, False)
set_icon(root)

length_var = tk.StringVar(value="12")
upper_var, lower_var, digits_var, symbols_var = [tk.BooleanVar(value=True) for _ in range(4)]
exclude_similar_var, exclude_ambiguous_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
at_least_one_var, hide_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
result_var, strength_var, crack_var = tk.StringVar(), tk.StringVar(), tk.StringVar()

menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Save", command=save_as)
file_menu.add_command(label="Save as...", command=save_as)
file_menu.add_separator(); file_menu.add_command(label="Exit", command=root.destroy)
menubar.add_cascade(label="File", menu=file_menu)

settings_menu = tk.Menu(menubar, tearoff=0)
theme_sub = tk.Menu(settings_menu, tearoff=0)
theme_sub.add_command(label="Light", command=lambda: change_theme('light'))
theme_sub.add_command(label="Dark", command=lambda: change_theme('dark'))
theme_sub.add_command(label="System", command=lambda: change_theme('system'))
settings_menu.add_cascade(label="Themes", menu=theme_sub)

lang_sub = tk.Menu(settings_menu, tearoff=0)
for code, name in [('ru', 'Русский'), ('en', 'English'), ('ua', 'Українська')]:
    lang_sub.add_command(label=name, command=lambda c=code: change_lang(c))
settings_menu.add_cascade(label="Language", menu=lang_sub)
menubar.add_cascade(label="Options", menu=settings_menu)

about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="Author", command=lambda: show_custom_info('author_title', 'author_label_text', 'author_main', False))
about_menu.add_command(label="Version", command=lambda: show_custom_info('ver_title', 'ver_label_text', 'ver_main', False))
about_menu.add_command(label="Updates", command=lambda: webbrowser.open(UPDATE_URL))
about_menu.add_command(label="GitHub", command=lambda: webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python"))
menubar.add_cascade(label="About", menu=about_menu)
root.config(menu=menubar)

header_label = tk.Label(root, font=("Arial", 11, "bold")); header_label.pack(pady=(10, 2))
len_info_label = tk.Label(root, font=("Arial", 9)); len_info_label.pack()
tk.Entry(root, textvariable=length_var, width=6, justify='center').pack(pady=2)

frame_checks = tk.Frame(root); frame_checks.pack(pady=2)
cb_upper = tk.Checkbutton(frame_checks, variable=upper_var); cb_upper.pack(anchor='w')
cb_lower = tk.Checkbutton(frame_checks, variable=lower_var); cb_lower.pack(anchor='w')
cb_digits = tk.Checkbutton(frame_checks, variable=digits_var); cb_digits.pack(anchor='w')
cb_symb = tk.Checkbutton(frame_checks, variable=symbols_var); cb_symb.pack(anchor='w')
cb_at_least = tk.Checkbutton(frame_checks, variable=at_least_one_var); cb_at_least.pack(anchor='w')
cb_exclude = tk.Checkbutton(frame_checks, variable=exclude_similar_var); cb_exclude.pack(anchor='w')
cb_ambiguous = tk.Checkbutton(frame_checks, variable=exclude_ambiguous_var); cb_ambiguous.pack(anchor='w')
cb_hide = tk.Checkbutton(frame_checks, variable=hide_var, command=lambda: result_entry.config(show="*" if hide_var.get() else "")); cb_hide.pack(anchor='w')

btn_gen = tk.Button(root, command=generate_password, width=22, relief='flat', cursor="hand2"); btn_gen.pack(pady=(8, 2))
btn_open = tk.Button(root, command=open_file, width=22, relief='flat', cursor="hand2"); btn_open.pack(pady=2)
result_entry = tk.Entry(root, textvariable=result_var, font=("Consolas", 12), width=22, state='readonly', justify='center'); result_entry.pack(pady=4)
strength_canvas = tk.Canvas(root, width=200, height=6); strength_canvas.pack()
strength_label_widget = tk.Label(root, textvariable=strength_var, font=("Arial", 9, "italic")); strength_label_widget.pack()
crack_canvas = tk.Canvas(root, width=200, height=4); crack_canvas.pack(pady=(4, 0))
crack_label_widget = tk.Label(root, textvariable=crack_var, font=("Arial", 8)); crack_label_widget.pack()
btn_copy = tk.Button(root, command=copy_to_clipboard, width=22, relief='flat', cursor="hand2"); btn_copy.pack(pady=5)
btn_qr = tk.Button(root, command=generate_qr, width=22, relief='flat', cursor="hand2"); btn_qr.pack(pady=2)

stars_label = tk.Label(root, text="★★★★★", font=("Arial", 12, "bold"), fg="#FFD700"); stars_label.pack(side='bottom', pady=(0, 5))
author_label = tk.Label(root, text="GitHub ©", cursor="hand2", font=("Arial", 8, "bold"), padx=8, pady=3); author_label.pack(side='bottom', pady=2)
author_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python"))

change_theme('system'); change_lang('ru')
root.mainloop()