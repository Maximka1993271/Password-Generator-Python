import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import threading
import time
import os
import sys
import platform
import qrcode
from PIL import ImageTk, Image

# =============================================================================
# RESOURCE PATH / ПУТЬ К РЕСУРСАМ / ШЛЯХ ДО РЕСУРСІВ
# =============================================================================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =============================================================================
# TRANSLATIONS / ПЕРЕВОДЫ / ПЕРЕКЛАДИ
# =============================================================================
LANGUAGES = {
    'ru': {
        'menu_file': "Файл", 'menu_opts': "Опции", 'menu_about': "О программе",
        'save': "Сохранить", 'save_as': "Сохранить как...", 'exit': "Выход",
        'themes': "Темы", 'lang': "Язык", 'light': "Светлая", 'dark': "Тёмная", 'system': "Системная",
        'author_btn': "Автор программы", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Программу разработал:",
        'ver_btn': "Версия программы", 'ver_title': "Версия", 'ver_main': "v1.8.9 Stable", 'ver_label_text': "Текущая сборка:",
        'site_btn': "Сайт проекта (GitHub)",
        'header': "Настройки генерации", 'len_label': "Длина пароля (4-64):",
        'upper': "Заглавные буквы", 'lower': "Строчные буквы", 'digits': "Цифры", 'symb': "Спецсимволы",
        'exclude': "Исключить похожие (0/O, 1/l/I)", 'ambiguous': "Исключить неоднозначные", 'hide': "Скрывать символы",
        'at_least': "Минимум 1 из каждой категории",
        'gen_btn': "СГЕНЕРИРОВАТЬ", 'open_btn': "ОТКРЫТЬ ФАЙЛ", 'copy_btn': "КОПИРОВАТЬ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'strength': "Сложность",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],
        'warn': "Внимание", 'min_len': "Длина должна быть от 4 до 64", 'err': "Ошибка", 'choose_set': "Выберите наборы символов",
        'check_input': "Проверьте ввод", 'copied': "Пароль скопирован. Очистка через 60 сек.", 'success': "Успешно!",
        'save_title': "Сохранить как", 'open_title': "Открыть пароль", 'text_files': "Текстовые файлы", 'all_files': "Все файлы",
        'saved': "Файл сохранён.", 'no_pwd': "Нет пароля для сохранения.",
        'crack_instantly': "Взломают мгновенно", 'crack_seconds': "Взломают за ~{} сек.", 'crack_minutes': "Взломают за ~{} мин.",
        'crack_hours': "Взломают за ~{} ч.", 'crack_days': "Взломают за ~{} дн.", 'crack_years': "Взломают за ~{} лет",
        'crack_centuries': "Взломают за ~{} веков", 'crack_never': "Практически невозможно взломать"
    },
    'en': {
        'menu_file': "File", 'menu_opts': "Options", 'menu_about': "About",
        'save': "Save", 'save_as': "Save as...", 'exit': "Exit",
        'themes': "Themes", 'lang': "Language", 'light': "Light", 'dark': "Dark", 'system': "System",
        'author_btn': "Program Author", 'author_title': "Author", 'author_main': "Maxim Melnikov", 'author_label_text': "Developed by:",
        'ver_btn': "Program Version", 'ver_title': "Version", 'ver_main': "v1.8.9 Stable", 'ver_label_text': "Current build:",
        'site_btn': "Project Site (GitHub)",
        'header': "Generation Settings", 'len_label': "Password Length (4-64):",
        'upper': "Uppercase", 'lower': "Lowercase", 'digits': "Digits", 'symb': "Symbols",
        'exclude': "Exclude similar (0/O, 1/l/I)", 'ambiguous': "Exclude ambiguous", 'hide': "Hide symbols",
        'at_least': "At least 1 from each category",
        'gen_btn': "GENERATE", 'open_btn': "OPEN FILE", 'copy_btn': "COPY PASSWORD", 'qr_btn': "PASSWORD QR-CODE",
        'strength': "Strength",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],
        'warn': "Warning", 'min_len': "Length must be between 4 and 64", 'err': "Error", 'choose_set': "Select character sets",
        'check_input': "Check input", 'copied': "Password copied. Clear in 60 sec.", 'success': "Success!",
        'save_title': "Save as", 'open_title': "Open Password", 'text_files': "Text files", 'all_files': "All files",
        'saved': "File saved.", 'no_pwd': "No password to save.",
        'crack_instantly': "Cracked instantly", 'crack_seconds': "Cracked in ~{} sec.", 'crack_minutes': "Cracked in ~{} min.",
        'crack_hours': "Cracked in ~{} hrs.", 'crack_days': "Cracked in ~{} days", 'crack_years': "Cracked in ~{} years",
        'crack_centuries': "Cracked in ~{} centuries", 'crack_never': "Practically uncrackable"
    },
    'ua': {
        'menu_file': "Файл", 'menu_opts': "Опції", 'menu_about': "Про программу",
        'save': "Зберегти", 'save_as': "Зберегти як...", 'exit': "Вихід",
        'themes': "Теми", 'lang': "Мова", 'light': "Світла", 'dark': "Темна", 'system': "Системна",
        'author_btn': "Автор програми", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Програму розробив:",
        'ver_btn': "Версія програми", 'ver_title': "Версія", 'ver_main': "v1.8.9 Stable", 'ver_label_text': "Поточна збірка:",
        'site_btn': "Сайт проєкту (GitHub)",
        'header': "Налаштування генерації", 'len_label': "Довжина пароля (4-64):",
        'upper': "Великі літери", 'lower': "Малі літери", 'digits': "Цифри", 'symb': "Спецсимволи",
        'exclude': "Виключити схожі (0/O, 1/l/I)", 'ambiguous': "Виключити неоднозначні", 'hide': "Приховати символи",
        'at_least': "Мінімум 1 з кожної категорії",
        'gen_btn': "ЗГЕНЕРУВАТИ", 'open_btn': "ВІДКРИТИ ФАЙЛ", 'copy_btn': "КОПІЮВАТИ ПАРОЛЬ", 'qr_btn': "QR-КОД ПАРОЛЯ",
        'strength': "Складність",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],
        'warn': "Увага", 'min_len': "Довжина має бути від 4 до 64", 'err': "Помилка", 'choose_set': "Оберіть набори символів",
        'check_input': "Перевірте введення", 'copied': "Пароль скопійовано. Очистка через 60 сек.", 'success': "Успішно!",
        'save_title': "Зберегти як", 'open_title': "Відкрити пароль", 'text_files': "Текстові файлы", 'all_files': "Усі файли",
        'saved': "Файл збережено.", 'no_pwd': "Немає пароля для збереження.",
        'crack_instantly': "Зламають миттєво", 'crack_seconds': "Зламають за ~{} сек.", 'crack_minutes': "Зламають за ~{} хв.",
        'crack_hours': "Зламають за ~{} год.", 'crack_days': "Зламають за ~{} дн.", 'crack_years': "Зламають за ~{} років",
        'crack_centuries': "Зламають за ~{} віків", 'crack_never': "Практически неможливо зламати"
    }
}

# =============================================================================
# CROSS-PLATFORM SYSTEM THEME / СИСТЕМНА ТЕМА / СИСТЕМНА ТЕМА
# =============================================================================
def get_system_theme():
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return 'light' if value == 1 else 'dark'
        elif platform.system() == "Darwin":
            import subprocess
            cmd = 'defaults read -g AppleInterfaceStyle'
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            return 'dark' if p.communicate()[0].decode('utf-8').strip() == "Dark" else 'light'
    except: pass
    return 'light'

# =============================================================================
# APP LOGIC / ЛОГИКА / ЛОГІКА
# =============================================================================
current_lang = 'ru'
last_score = -1
current_file_path = None

def estimate_crack_time(password):
    if not password: return -1, ""
    charset = 0
    if any(c.islower() for c in password): charset += 26
    if any(c.isupper() for c in password): charset += 26
    if any(c.isdigit() for c in password): charset += 10
    if any(c in string.punctuation for c in password): charset += 32
    combinations = charset ** len(password)
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

def on_closing():
    try: root.clipboard_clear()
    except: pass
    root.destroy()

def change_lang(lang_code):
    global current_lang
    current_lang = lang_code
    L = LANGUAGES[lang_code]
    menubar.entryconfig(1, label=L['menu_file'])
    menubar.entryconfig(2, label=L['menu_opts'])
    menubar.entryconfig(3, label=L['menu_about'])
    file_menu.entryconfig(0, label=L['save'])
    file_menu.entryconfig(1, label=L['save_as'])
    file_menu.entryconfig(3, label=L['exit'])
    settings_menu.entryconfig(0, label=L['themes'])
    settings_menu.entryconfig(1, label=L['lang'])
    theme_sub.entryconfig(0, label=L['light'])
    theme_sub.entryconfig(1, label=L['dark'])
    theme_sub.entryconfig(2, label=L['system'])
    about_menu.entryconfig(0, label=L['author_btn'])
    about_menu.entryconfig(1, label=L['ver_btn'])
    about_menu.entryconfig(2, label=L['site_btn'])
    header_label.config(text=L['header'])
    len_info_label.config(text=L['len_label'])
    btn_gen.config(text=L['gen_btn'])
    btn_open.config(text=L['open_btn'])
    btn_copy.config(text=L['copy_btn'])
    btn_qr.config(text=L['qr_btn'])
    cb_upper.config(text=L['upper'])
    cb_lower.config(text=L['lower'])
    cb_digits.config(text=L['digits'])
    cb_symb.config(text=L['symb'])
    cb_exclude.config(text=L['exclude'])
    cb_ambiguous.config(text=L['ambiguous'])
    cb_hide.config(text=L['hide'])
    cb_at_least.config(text=L['at_least'])
    update_strength_meter(last_score, result_var.get())

def change_theme(mode):
    """ AMOLED BLACK THEME INTEGRATION / ЧЕРНЫЙ ЦВЕТ ADGUARD """
    if mode == 'system': mode = get_system_theme()
    if mode == 'dark':
        # Pure Black Style (AdGuard inspired)
        bg, fg, btn, btn_h, entry_bg = '#000000', '#FFFFFF', '#1A1A1A', '#2D2D2D', '#121212'
        res_bg, res_fg, check_sel = '#000000', '#4EC9B0', '#1A1A1A'
    else:
        bg, fg, btn, btn_h, entry_bg = '#F3F3F3', '#000000', '#E1E1E1', '#D0D0D0', '#FFFFFF'
        res_bg, res_fg, check_sel = '#FFFFFF', '#005FB8', '#FFFFFF'
    
    root.configure(bg=bg)
    result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
    frame_checks.config(bg=bg)
    strength_canvas.config(bg=bg, highlightthickness=0)
    crack_canvas.config(bg=bg, highlightthickness=0)
    root.current_theme_colors = {'btn': btn, 'btn_h': btn_h}
    
    def apply_style(parent):
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame): apply_style(widget)
            elif isinstance(widget, tk.Label):
                if widget not in [author_label, stars_label]: widget.config(bg=bg, fg=fg)
            elif isinstance(widget, tk.Button): widget.config(bg=btn, fg=fg, activebackground=btn_h)
            elif isinstance(widget, tk.Checkbutton): widget.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)
            elif isinstance(widget, tk.Entry) and widget != result_entry: widget.config(bg=entry_bg, fg=fg, insertbackground=fg)

    apply_style(root)
    strength_label_widget.config(bg=bg, fg=fg)
    crack_label_widget.config(bg=bg)
    author_label.config(bg=btn, fg=fg)
    stars_label.config(bg=bg)

def setup_hover(widget):
    widget.bind("<Enter>", lambda e: widget.config(bg=root.current_theme_colors['btn_h']))
    widget.bind("<Leave>", lambda e: widget.config(bg=root.current_theme_colors['btn']))

def generate_qr():
    pwd = result_var.get()
    if not pwd: return
    qr_win = tk.Toplevel(root)
    qr_win.title("QR Code")
    qr_win.geometry("250x250"); qr_win.resizable(False, False)
    current_bg = root.cget("bg")
    qr_win.configure(bg=current_bg)
    try:
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path): qr_win.iconbitmap(icon_path)
    except: pass

    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(pwd); qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    img_tk = ImageTk.PhotoImage(img_qr.resize((220, 220)))
    lbl = tk.Label(qr_win, image=img_tk, bg=current_bg)
    lbl.image = img_tk; lbl.pack(expand=True)

def update_strength_meter(score, password=""):
    global last_score
    last_score = score
    strength_canvas.delete("all"); crack_canvas.delete("all")
    L = LANGUAGES[current_lang]
    if score == -1: strength_var.set(""); crack_var.set(""); return
    colors = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]
    strength_canvas.create_rectangle(0, 0, 200, 6, fill="#333333", outline="")
    width = (score + 1) * 33.33 
    strength_canvas.create_rectangle(0, 0, width, 6, fill=colors[score], outline="")
    strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]}")
    if password:
        p_len = len(password)
        crack_score, crack_text = estimate_crack_time(password)
        crack_var.set(crack_text)
        bar_color = "#e74c3c" if p_len <= 4 else ("#f39c12" if p_len <= 10 else "#27ae60")
        crack_canvas.create_rectangle(0, 0, 200, 4, fill="#333333", outline="")
        crack_width = (crack_score + 1) * (200 / 8) 
        crack_canvas.create_rectangle(0, 0, crack_width, 4, fill=bar_color, outline="")

def generate_password():
    L = LANGUAGES[current_lang]
    try:
        raw_len = length_var.get().strip()
        if not raw_len.isdigit() or not (4 <= int(raw_len) <= 64):
            messagebox.showwarning(L['warn'], L['min_len']); return
        length = int(raw_len)
        categories = []
        if upper_var.get(): categories.append(string.ascii_uppercase)
        if lower_var.get(): categories.append(string.ascii_lowercase)
        if digits_var.get(): categories.append(string.digits)
        if symbols_var.get(): categories.append(string.punctuation)
        if not categories: messagebox.showerror(L['err'], L['choose_set']); return
        if exclude_similar_var.get(): categories = [''.join(c for c in cat if c not in "Il1O0") for cat in categories]
        if exclude_ambiguous_var.get(): categories = [''.join(c for c in cat if c not in ".,:;\'~\"/()[]{}|") for cat in categories]
        all_chars = "".join(categories)
        pwd_list = []
        if at_least_one_var.get() and length >= len(categories):
            for cat in categories: pwd_list.append(secrets.choice(cat))
            for _ in range(length - len(categories)): pwd_list.append(secrets.choice(all_chars))
        else:
            for _ in range(length): pwd_list.append(secrets.choice(all_chars))
        secrets.SystemRandom().shuffle(pwd_list)
        pwd = "".join(pwd_list)
        result_var.set(pwd)
        result_entry.config(show="*" if hide_var.get() else "")
        variety = sum([any(c.isupper() for c in pwd), any(c.islower() for c in pwd), any(c.isdigit() for c in pwd), any(c in string.punctuation for c in pwd)])
        if length < 10: score = 0 if variety < 2 else 1
        elif 10 <= length < 14: score = 2 if variety < 3 else 3
        else: score = 4 if variety < 4 else 5
        update_strength_meter(score, pwd)
    except Exception: messagebox.showerror(L['err'], L['check_input'])

def copy_to_clipboard():
    pwd = result_var.get()
    L = LANGUAGES[current_lang]
    if pwd:
        root.clipboard_clear(); root.clipboard_append(pwd)
        def safe_wipe():
            time.sleep(60)
            try:
                if root.winfo_exists(): root.clipboard_clear()
            except: pass
        threading.Thread(target=safe_wipe, daemon=True).start()
        show_custom_info(L['success'], L['success'], L['copied'])

def save_file():
    global current_file_path
    pwd = result_var.get()
    if not pwd: return
    if not current_file_path: current_file_path = "passwords.txt"
    try:
        with open(current_file_path, "w", encoding="utf-8") as f: f.write(pwd)
    except: pass

def save_as():
    global current_file_path
    L = LANGUAGES[current_lang]
    pwd = result_var.get()
    if pwd:
        path = filedialog.asksaveasfilename(title=L['save_title'], initialfile="SecurePass.txt", defaultextension=".txt", filetypes=[("Normal text file", "*.txt"), ("Python file", "*.py;*.pyw"), ("All files", "*.*")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f: f.write(pwd)
                current_file_path = path 
                show_custom_info(L['success'], L['success'], L['saved'])
            except Exception as e: messagebox.showerror(L['err'], str(e))

def open_file():
    global current_file_path
    L = LANGUAGES[current_lang]
    path = filedialog.askopenfilename(title=L['open_title'], filetypes=[("Normal text file", "*.txt"), ("Python file", "*.py;*.pyw"), ("All files", "*.*")])
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f: result_var.set(f.read().strip())
            current_file_path = path; update_strength_meter(-1)
        except Exception as e: messagebox.showerror(L['err'], str(e))

def show_custom_info(title_key, label_key, main_val, is_static_main=True):
    L = LANGUAGES[current_lang]
    info_win = tk.Toplevel(root)
    info_win.title(L.get(title_key, title_key))
    info_win.geometry("280x130"); info_win.resizable(False, False)
    try:
        icon_path = resource_path("app_icon.ico")
        if os.path.exists(icon_path): info_win.iconbitmap(icon_path)
    except: pass
    current_bg = root.cget("bg")
    current_fg = "#FFFFFF" if current_bg == "#000000" else "#000000"
    info_win.configure(bg=current_bg)
    main_text = main_val if is_static_main else L.get(main_val, main_val)
    tk.Label(info_win, text=L.get(label_key, label_key), bg=current_bg, fg=current_fg).pack(pady=(15, 2))
    tk.Label(info_win, text=main_text, font=("Arial", 10, "bold"), bg=current_bg, fg=current_fg).pack(pady=5)
    tk.Button(info_win, text="OK", command=info_win.destroy, width=10, bg="#1A1A1A" if current_bg == "#000000" else "#E1E1E1", fg=current_fg, relief='flat').pack(pady=10)

def open_github(): webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python")

# =============================================================================
# MAIN WINDOW / ГОЛОВНЕ ВІКНО
# =============================================================================
root = tk.Tk()
root.title("Secure Pass Pro")
root.geometry("340x650"); root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_closing)

try:
    icon_path = resource_path("app_icon.ico")
    if os.path.exists(icon_path): root.iconbitmap(icon_path)
except: pass

length_var = tk.StringVar(value="12")
upper_var, lower_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
digits_var, symbols_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
exclude_similar_var, exclude_ambiguous_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
at_least_one_var, hide_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
result_var, strength_var, crack_var = tk.StringVar(), tk.StringVar(), tk.StringVar()

menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save as...", command=save_as)
file_menu.add_separator(); file_menu.add_command(label="Exit", command=on_closing)
menubar.add_cascade(label="File", menu=file_menu)

settings_menu = tk.Menu(menubar, tearoff=0)
theme_sub = tk.Menu(settings_menu, tearoff=0)
theme_sub.add_command(label="Light", command=lambda: change_theme('light'))
theme_sub.add_command(label="Dark", command=lambda: change_theme('dark'))
theme_sub.add_command(label="System", command=lambda: change_theme('system'))
settings_menu.add_cascade(label="Themes", menu=theme_sub)

lang_sub = tk.Menu(settings_menu, tearoff=0)
lang_sub.add_command(label="Русский", command=lambda: change_lang('ru'))
lang_sub.add_command(label="English", command=lambda: change_lang('en'))
lang_sub.add_command(label="Українська", command=lambda: change_lang('ua'))
settings_menu.add_cascade(label="Language", menu=lang_sub)
menubar.add_cascade(label="Options", menu=settings_menu)

about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="Author", command=lambda: show_custom_info('author_title', 'author_label_text', 'author_main', False))
about_menu.add_command(label="Version", command=lambda: show_custom_info('ver_title', 'ver_label_text', 'ver_main', False))
about_menu.add_command(label="GitHub", command=open_github)
menubar.add_cascade(label="About", menu=about_menu)
root.config(menu=menubar)

header_label = tk.Label(root, text="", font=("Arial", 11, "bold"))
header_label.pack(pady=(10, 2))
len_info_label = tk.Label(root, font=("Arial", 9)); len_info_label.pack()
tk.Entry(root, textvariable=length_var, width=6, justify='center', font=("Arial", 10)).pack(pady=2)

frame_checks = tk.Frame(root); frame_checks.pack(pady=2)
cb_upper = tk.Checkbutton(frame_checks, variable=upper_var, font=("Arial", 9)); cb_upper.pack(anchor='w')
cb_lower = tk.Checkbutton(frame_checks, variable=lower_var, font=("Arial", 9)); cb_lower.pack(anchor='w')
cb_digits = tk.Checkbutton(frame_checks, variable=digits_var, font=("Arial", 9)); cb_digits.pack(anchor='w')
cb_symb = tk.Checkbutton(frame_checks, variable=symbols_var, font=("Arial", 9)); cb_symb.pack(anchor='w')
cb_at_least = tk.Checkbutton(frame_checks, variable=at_least_one_var, font=("Arial", 9)); cb_at_least.pack(anchor='w')
cb_exclude = tk.Checkbutton(frame_checks, variable=exclude_similar_var, font=("Arial", 9)); cb_exclude.pack(anchor='w')
cb_ambiguous = tk.Checkbutton(frame_checks, variable=exclude_ambiguous_var, font=("Arial", 9)); cb_ambiguous.pack(anchor='w')
cb_hide = tk.Checkbutton(frame_checks, variable=hide_var, font=("Arial", 9), command=lambda: result_entry.config(show="*" if hide_var.get() else ""))
cb_hide.pack(anchor='w')

btn_gen = tk.Button(root, text="", command=generate_password, width=22, font=("Arial", 9, "bold"), relief='flat')
btn_gen.pack(pady=(8, 2)); setup_hover(btn_gen)
btn_open = tk.Button(root, text="", command=open_file, width=22, font=("Arial", 9, "bold"), relief='flat')
btn_open.pack(pady=2); setup_hover(btn_open)

result_entry = tk.Entry(root, textvariable=result_var, font=("Consolas", 12), width=22, state='readonly', justify='center')
result_entry.pack(pady=4)

strength_canvas = tk.Canvas(root, width=200, height=6); strength_canvas.pack()
strength_label_widget = tk.Label(root, textvariable=strength_var, font=("Arial", 9, "italic")); strength_label_widget.pack()
crack_label_widget = tk.Label(root, textvariable=crack_var, font=("Arial", 8), fg="#888888"); crack_label_widget.pack(pady=(5, 0))
crack_canvas = tk.Canvas(root, width=200, height=4); crack_canvas.pack(pady=(0, 5))

btn_copy = tk.Button(root, text="", command=copy_to_clipboard, width=22, relief='flat')
btn_copy.pack(pady=5); setup_hover(btn_copy)
btn_qr = tk.Button(root, text="", command=generate_qr, width=22, relief='flat')
btn_qr.pack(pady=2); setup_hover(btn_qr)

stars_label = tk.Label(root, text="★★★★★", font=("Arial", 12, "bold"), fg="#FFD700"); stars_label.pack(side='bottom', pady=(0, 5))
author_label = tk.Label(root, text="GitHub ©", cursor="hand2", font=("Arial", 8, "bold"), padx=8, pady=3); author_label.pack(side='bottom', pady=2)
author_label.bind("<Button-1>", lambda e: open_github())

change_theme('system')
change_lang('ru')
root.mainloop()