import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import os
import threading
import time

# =============================================================================
# TRANSLATION DICTIONARY / СЛОВАРЬ ПЕРЕВОДОВ / СЛОВНИК ПЕРЕКЛАДІВ
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
        'gen_btn': "СГЕНЕРИРОВАТЬ", 'open_btn': "ОТКРЫТЬ ФАЙЛ", 'copy_btn': "КОПИРОВАТЬ ПАРОЛЬ", 'strength': "Сложность",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],
        'warn': "Внимание", 'min_len': "Минимальная длина — 4", 'err': "Ошибка", 'choose_set': "Выберите наборы символов",
        'check_input': "Проверьте ввод", 'copied': "Пароль скопирован. Очистка через 60 сек.", 'success': "Успешно!",
        'save_title': "Сохранить как", 'open_title': "Открыть пароль", 'text_files': "Текстовые файлы", 'all_files': "Все файлы"
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
        'gen_btn': "GENERATE", 'open_btn': "OPEN FILE", 'copy_btn': "COPY PASSWORD", 'strength': "Strength",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],
        'warn': "Warning", 'min_len': "Minimum length is 4", 'err': "Error", 'choose_set': "Select character sets",
        'check_input': "Check input", 'copied': "Password copied. Clear in 60 sec.", 'success': "Success!",
        'save_title': "Save as", 'open_title': "Open Password", 'text_files': "Text files", 'all_files': "All files"
    },
    'ua': {
        'menu_file': "Файл", 'menu_opts': "Опції", 'menu_about': "Про програму",
        'save': "Зберегти", 'save_as': "Зберегти як...", 'exit': "Вихід",
        'themes': "Теми", 'lang': "Мова", 'light': "Світла", 'dark': "Темна", 'system': "Системна",
        'author_btn': "Автор програми", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Програму розробив:",
        'ver_btn': "Версія програми", 'ver_title': "Версія", 'ver_main': "v1.8.9 Stable", 'ver_label_text': "Поточна збірка:",
        'site_btn': "Сайт проєкту (GitHub)",
        'header': "Налаштування генерації", 'len_label': "Довжина пароля (4-64):",
        'upper': "Великі літери", 'lower': "Малі літери", 'digits': "Цифри", 'symb': "Спецсимволи",
        'exclude': "Виключити схожі (0/O, 1/l/I)", 'ambiguous': "Виключити неоднозначні", 'hide': "Приховати символи",
        'at_least': "Мінімум 1 з кожної категорії",
        'gen_btn': "ЗГЕНЕРУВАТИ", 'open_btn': "ВІДКРИТИ ФАЙЛ", 'copy_btn': "КОПІЮВАТИ ПАРОЛЬ", 'strength': "Складність",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],
        'warn': "Увага", 'min_len': "Мінімальна довжина — 4", 'err': "Помилка", 'choose_set': "Оберіть набори символів",
        'check_input': "Перевірте введення", 'copied': "Пароль скопійовано. Очистка через 60 сек.", 'success': "Успішно!",
        'save_title': "Зберегти як", 'open_title': "Відкрити пароль", 'text_files': "Текстові файли", 'all_files': "Усі файли"
    }
}

# Full formats list from your screenshots / Полный список форматов со скриншотов / Повний список форматів зі скріншотів
FULL_FILETYPES = [
    ("Python file", "*.py;*.pyw;*.pyx;*.pxd;*.pxi;*.pyi"),
    ("GDScript file", "*.gd"),
    ("R programming language", "*.r;*.s;*.splus"),
    ("Raku source file", "*.raku;*.rakumod;*.rakudoc;*.rakutest;*.p6;*.pm6;*.pod6"),
    ("REBOL file", "*.r2;*.r3;*.reb"),
    ("registry file", "*.reg"),
    ("Windows Resource file", "*.rc"),
    ("Ruby file", "*.rb;*.rbw"),
    ("Rust file", "*.rs"),
    ("SAS file", "*.sas"),
    ("Scheme file", "*.scm;*.smd;*.ss"),
    ("Smalltalk file", "*.st"),
    ("spice file", "*.scp;*.out"),
    ("Structured Query Language file", "*.sql"),
    ("Motorola S-Record binary data", "*.mot;*.srec"),
    ("Swift file", "*.swift"),
    ("Tool Command Language file", "*.tcl;*.itcl"),
    ("Tektronix extended HEX binary data", "*.tek"),
    ("TeX file", "*.tex"),
    ("Tom's Obvious Minimal Language file", "*.toml"),
    ("Visual Basic file", "*.vb;*.vba;*.vbs"),
    ("txt2tags file", "*.t2t"),
    ("TypeScript file", "*.ts;*.tsx"),
    ("Verilog file", "*.v;*.sv;*.vh;*.svh"),
    ("VHDL Source file", "*.vhd;*.vhdl"),
    ("Visual Prolog file", "*.pro;*.cl;*.i;*.pack;*.ph"),
    ("eXtensible Markup Language file", "*.xml;*.xaml;*.xslt;*.xsl;*.xsd;*.xul;*.kml;*.svg;*.mxml;*.xsml"),
    ("YAML Ain't Markup Language", "*.yml;*.yaml"),
    ("Markdown", "*.md;*.markdown"),
    ("Normal text file", "*.txt"),
    ("Flash ActionScript file", "*.as;*.mx"),
    ("Ada file", "*.ada;*.ads;*.adb"),
    ("Assembly language source file", "*.asm"),
    ("Abstract Syntax Notation One file", "*.mib"),
    ("Active Server Pages script file", "*.asp;*.aspx"),
    ("AutoIt", "*.au3"),
    ("AviSynth scripts files", "*.avs;*.avsi"),
    ("BaanC File", "*.bc;*.cln"),
    ("Unix script file", "*.bash;*.sh;*.bsh;*.bash_profile;*.bashrc;*.profile"),
    ("Batch file", "*.bat;*.cmd;*.nt"),
    ("BlitzBasic file", "*.bb"),
    ("C source file", "*.c;*.lex"),
    ("C++ source file", "*.cpp;*.cxx;*.cc;*.h;*.hh;*.hpp;*.hxx;*.ino"),
    ("C# source file", "*.cs"),
    ("Categorical Abstract Machine Language", "*.ml;*.mli;*.sml;*.thy"),
    ("CMake file", "*.cmake"),
    ("COBOL", "*.cbl;*.cbd;*.cdb;*.cdc;*.cob;*.cpy;*.lst"),
    ("Csound file", "*.orc;*.sco;*.csd"),
    ("CoffeeScript file", "*.coffee;*.litcoffee"),
    ("Cascade Style Sheets File", "*.css"),
    ("D programming language", "*.d"),
    ("Diff file", "*.patch;*.diff"),
    ("Erlang file", "*.erl;*.hrl"),
    ("ErrorList", "*.err"),
    ("ESCRIPT file", "*.src;*.em"),
    ("Forth file", "*.forth"),
    ("Fortran free form source file", "*.f;*.for;*.f90;*.f95;*.f2k;*.f23"),
    ("Fortran fixed form source file", "*.f77"),
    ("FreeBasic file", "*.bas;*.bi"),
    ("Go source file", "*.go"),
    ("Gui4Cli file", "*.gui"),
    ("Haskell", "*.hs;*.lhs;*.las"),
    ("Hollywood script", "*.hws"),
    ("Hyper Text Markup Language file", "*.html;*.htm;*.shtml;*.shtm;*.xhtml;*.xht;*.hta"),
    ("MS ini file", "*.ini;*.inf;*.url;*.wer"),
    ("Inno Setup script", "*.iss"),
    ("Intel HEX binary data", "*.hex"),
    ("Java source file", "*.java"),
    ("JavaScript file", "*.js;*.jsm;*.jsx;*.mjs"),
    ("JSON file", "*.json"),
    ("JSON5 file", "*.json5;*.jsonc"),
    ("JavaServer Pages script file", "*.jsp"),
    ("KiXtart file", "*.kix"),
    ("LISP file", "*.lsp;*.lisp"),
    ("LaTeX file", "*.tex;*.sty"),
    ("Lua source File", "*.lua"),
    ("Makefile", "*.mak;*.mk"),
    ("MATrix LABoratory", "*.m"),
    ("Microsoft Transact-SQL", "*.tsql"),
    ("MMIXAL file", "*.mms"),
    ("Nim file", "*.nim"),
    ("extended crontab file", "*.tab;*.spf"),
    ("MSDOS Style/ASCII Art", "*.nfo"),
    ("Nullsoft Scriptable Install System script", "*.nsi;*.nsh"),
    ("OScript source file", "*.osx"),
    ("Objective-C source file", "*.mm"),
    ("Pascal source file", "*.pas;*.pp;*.inc;*.lpr"),
    ("Perl source file", "*.pl;*.pm;*.plx;*.t"),
    ("PHP Hypertext Preprocessor file", "*.php;*.php3;*.php4;*.php5;*.phps;*.phpt;*.phtml"),
    ("PostScript file", "*.ps"),
    ("Windows PowerShell", "*.ps1;*.psm1;*.psd1"),
    ("Properties file", "*.properties;*.conf;*.cfg;*.gitattributes;*.gitconfig"),
    ("PureBasic file", "*.pb"),
    ("All types", "*.*")
]

current_lang = 'ru'
last_score = -1

# =============================================================================
# FUNCTIONS / ФУНКЦИИ / ФУНКЦІЇ
# =============================================================================

# System theme detection / Определение системной темы / Визначення системної теми
def get_system_theme():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return 'light' if value == 1 else 'dark'
    except: return 'light'

# Shutdown protocol / Протокол закрытия / Протокол закриття
def on_closing():
    root.clipboard_clear()
    root.destroy()

# Localization engine / Движок локализации / Двигун локалізації
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
    cb_upper.config(text=L['upper'])
    cb_lower.config(text=L['lower'])
    cb_digits.config(text=L['digits'])
    cb_symb.config(text=L['symb'])
    cb_exclude.config(text=L['exclude'])
    cb_ambiguous.config(text=L['ambiguous'])
    cb_hide.config(text=L['hide'])
    cb_at_least.config(text=L['at_least'])
    update_strength_meter(last_score)

# Visual themes / Темы оформления / Теми оформлення
def change_theme(mode):
    if mode == 'system': mode = get_system_theme()
    if mode == 'dark':
        bg, fg, btn, btn_h, entry_bg = '#252526', '#FFFFFF', '#3E3E42', '#454545', '#333333'
        res_bg, res_fg, check_sel = '#1E1E1E', '#4EC9B0', '#3E3E42'
    else:
        bg, fg, btn, btn_h, entry_bg = '#F3F3F3', '#000000', '#E1E1E1', '#D0D0D0', '#FFFFFF'
        res_bg, res_fg, check_sel = '#FFFFFF', '#005FB8', '#FFFFFF'
    root.configure(bg=bg)
    result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
    frame_checks.config(bg=bg)
    strength_canvas.config(bg=bg, highlightthickness=0)
    root.current_theme_colors = {'btn': btn, 'btn_h': btn_h}
    for widget in root.winfo_children():
        if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton, tk.Entry)):
            if widget in [author_label, stars_label]: continue 
            if isinstance(widget, tk.Label): widget.config(bg=bg, fg=fg)
            if isinstance(widget, tk.Button): widget.config(bg=btn, fg=fg, activebackground=btn_h)
            if isinstance(widget, tk.Checkbutton): widget.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)
            if isinstance(widget, tk.Entry) and widget != result_entry: widget.config(bg=entry_bg, fg=fg, insertbackground=fg)
    for cb in frame_checks.winfo_children(): cb.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)
    strength_label_widget.config(bg=bg, fg=fg)
    author_label.config(bg=btn, fg=fg)
    stars_label.config(bg=bg)

# Hover logic / Логика наведения / Логіка наведення
def setup_hover(widget):
    widget.bind("<Enter>", lambda e: widget.config(bg=root.current_theme_colors['btn_h']))
    widget.bind("<Leave>", lambda e: widget.config(bg=root.current_theme_colors['btn']))

# Strength meter / Анализ сложности / Аналіз складності
def update_strength_meter(score):
    global last_score
    last_score = score
    strength_canvas.delete("all")
    L = LANGUAGES[current_lang]
    if score == -1:
        strength_var.set("")
        return
    colors = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]
    width = (score + 1) * 33.3
    strength_canvas.create_rectangle(0, 0, 200, 6, fill="#333333", outline="")
    strength_canvas.create_rectangle(0, 0, width, 6, fill=colors[score], outline="")
    strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]}")

# Password Generation / Генерация / Генерація
def generate_password():
    L = LANGUAGES[current_lang]
    try:
        raw_len = length_var.get().strip()
        if not raw_len.isdigit() or int(raw_len) < 4:
            messagebox.showwarning(L['warn'], L['min_len'])
            return
        length = int(raw_len)
        categories = []
        if upper_var.get(): categories.append(string.ascii_uppercase)
        if lower_var.get(): categories.append(string.ascii_lowercase)
        if digits_var.get(): categories.append(string.digits)
        if symbols_var.get(): categories.append(string.punctuation)
        if exclude_similar_var.get(): categories = [''.join(c for c in cat if c not in "Il1O0") for cat in categories]
        if exclude_ambiguous_var.get(): categories = [''.join(c for c in cat if c not in ".,:;\'~\"/()[]{}|") for cat in categories]
        categories = [c for c in categories if c]
        if not categories:
            messagebox.showerror(L['err'], L['choose_set'])
            return
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
        variety = sum([any(c.isupper() for c in pwd), any(c.islower() for c in pwd), 
                       any(c.isdigit() for c in pwd), any(c in string.punctuation for c in pwd)])
        if length < 10: score = 0 if variety < 2 else 1
        elif 10 <= length < 14: score = 2 if variety < 3 else 3
        else: score = 4 if variety < 4 else 5
        update_strength_meter(score)
    except: messagebox.showerror(L['err'], L['check_input'])

# Clipboard / Буфер обмена / Буфер обміну
def copy_to_clipboard():
    pwd = result_var.get()
    L = LANGUAGES[current_lang]
    if pwd:
        root.clipboard_clear()
        root.clipboard_append(pwd)
        threading.Thread(target=lambda: (time.sleep(60), root.clipboard_clear()), daemon=True).start()
        show_custom_info(L['success'], L['success'], L['copied'])

# Files / Файлы / Файли
def save_as():
    L = LANGUAGES[current_lang]
    pwd = result_var.get()
    if pwd:
        path = filedialog.asksaveasfilename(title=L['save_title'], initialfile="SecurePass.pyw", defaultextension=".pyw", filetypes=FULL_FILETYPES)
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(pwd)

def open_file():
    L = LANGUAGES[current_lang]
    path = filedialog.askopenfilename(title=L['open_title'], filetypes=FULL_FILETYPES)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            result_var.set(f.read().strip())
            update_strength_meter(-1)

# Modal Windows / Модальные окна / Модальні вікна
def show_custom_info(title_key, label_key, main_val, is_static_main=True):
    L = LANGUAGES[current_lang]
    info_win = tk.Toplevel(root)
    info_win.title(L.get(title_key, title_key))
    info_win.geometry("280x130"); info_win.resizable(False, False)
    current_bg = root.cget("bg")
    current_fg = "#FFFFFF" if current_bg == "#252526" else "#000000"
    info_win.configure(bg=current_bg)
    main_text = main_val if is_static_main else L.get(main_val, main_val)
    tk.Label(info_win, text=L.get(label_key, label_key), font=("Arial", 9), bg=current_bg, fg=current_fg).pack(pady=(15, 2))
    tk.Label(info_win, text=main_text, font=("Arial", 10, "bold"), bg=current_bg, fg=current_fg, wraplength=250).pack(pady=5)
    tk.Button(info_win, text="OK", command=info_win.destroy, width=10, bg="#3E3E42" if current_bg == "#252526" else "#E1E1E1", fg=current_fg, relief='flat').pack(pady=10)

def open_github():
    webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python")

# =============================================================================
# UI CONSTRUCTION / СБОРКА ИНТЕРФЕЙСА / ЗБИРАННЯ ІНТЕРФЕЙСУ
# =============================================================================
root = tk.Tk()
root.title("Secure Pass Pro")
root.geometry("340x580") 
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_closing)

length_var = tk.StringVar(value="12")
upper_var, lower_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
digits_var, symbols_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
exclude_similar_var, exclude_ambiguous_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
at_least_one_var, hide_var = tk.BooleanVar(value=True), tk.BooleanVar(value=False)
result_var, strength_var = tk.StringVar(), tk.StringVar()

menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Save", command=save_as)
file_menu.add_command(label="Save as...", command=save_as)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=on_closing)
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
len_info_label = tk.Label(root, font=("Arial", 9))
len_info_label.pack()
tk.Entry(root, textvariable=length_var, width=6, justify='center', font=("Arial", 10)).pack(pady=2)

frame_checks = tk.Frame(root)
frame_checks.pack(pady=2)
cb_font = ("Arial", 9)
cb_upper = tk.Checkbutton(frame_checks, variable=upper_var, font=cb_font); cb_upper.pack(anchor='w')
cb_lower = tk.Checkbutton(frame_checks, variable=lower_var, font=cb_font); cb_lower.pack(anchor='w')
cb_digits = tk.Checkbutton(frame_checks, variable=digits_var, font=cb_font); cb_digits.pack(anchor='w')
cb_symb = tk.Checkbutton(frame_checks, variable=symbols_var, font=cb_font); cb_symb.pack(anchor='w')
cb_at_least = tk.Checkbutton(frame_checks, variable=at_least_one_var, font=cb_font); cb_at_least.pack(anchor='w')
cb_exclude = tk.Checkbutton(frame_checks, variable=exclude_similar_var, font=cb_font); cb_exclude.pack(anchor='w')
cb_ambiguous = tk.Checkbutton(frame_checks, variable=exclude_ambiguous_var, font=cb_font); cb_ambiguous.pack(anchor='w')
cb_hide = tk.Checkbutton(frame_checks, variable=hide_var, font=cb_font, command=lambda: result_entry.config(show="*" if hide_var.get() else "")); cb_hide.pack(anchor='w')

btn_gen = tk.Button(root, text="", command=generate_password, width=22, height=1, font=("Arial", 9, "bold"), relief='flat', bd=0)
btn_gen.pack(pady=(8, 2)); setup_hover(btn_gen)
btn_open = tk.Button(root, text="", command=open_file, width=22, height=1, font=("Arial", 9, "bold"), relief='flat', bd=0)
btn_open.pack(pady=2); setup_hover(btn_open)

result_entry = tk.Entry(root, textvariable=result_var, font=("Consolas", 12), width=22, state='readonly', justify='center')
result_entry.pack(pady=4, padx=15)
strength_canvas = tk.Canvas(root, width=200, height=6)
strength_canvas.pack(pady=(2, 0))
strength_label_widget = tk.Label(root, textvariable=strength_var, font=("Arial", 9, "italic"))
strength_label_widget.pack(pady=(0, 2))

btn_copy = tk.Button(root, text="", command=copy_to_clipboard, width=22, height=1, font=("Arial", 9), relief='flat', bd=0)
btn_copy.pack(pady=5); setup_hover(btn_copy)

stars_label = tk.Label(root, text="★★★★★", font=("Arial", 12, "bold"), fg="#FFD700")
stars_label.pack(side='bottom', pady=(0, 5))
author_label = tk.Label(root, text="GitHub ©", cursor="hand2", font=("Arial", 8, "bold"), padx=8, pady=3)
author_label.pack(side='bottom', pady=2)
author_label.bind("<Button-1>", lambda e: open_github())

# App Launch / Запуск / Запуск
change_theme('system')
change_lang('ru')
root.mainloop()