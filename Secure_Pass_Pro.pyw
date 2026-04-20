import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import os
import threading
import time

# =============================================================================
# [RU] СЛОВАРЬ ПЕРЕВОДОВ / [EN] TRANSLATION DICTIONARY / [UA] СЛОВНИК ПЕРЕКЛАДІВ
# =============================================================================
LANGUAGES = {
    'ru': {
        'menu_file': "Файл", 'menu_opts': "Опции", 'menu_about': "О программе",
        'save': "Сохранить", 'save_as': "Сохранить как...", 'exit': "Выход",
        'themes': "Темы", 'lang': "Язык", 'light': "Светлая", 'dark': "Тёмная", 'system': "Системная",
        'author_btn': "Автор программы", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Программу разработал:",
        'ver_btn': "Версия программы", 'ver_title': "Версия", 'ver_main': "v1.8.3 Stable", 'ver_label_text': "Текущая сборка:",
        'site_btn': "Сайт проекта (GitHub)",
        'header': "Настройки генерации", 'len_label': "Длина пароля (4-64):",
        'upper': "Заглавные буквы", 'lower': "Строчные буквы", 'digits': "Цифры", 'symb': "Спецсимволы",
        'exclude': "Исключить похожие (i, l, 1, L, o, 0)", 'ambiguous': "Исключить неоднозначные (.,:;()[]{})", 'hide': "Скрывать символы",
        'gen_btn': "СГЕНЕРИРОВАТЬ", 'copy_btn': "КОПИРОВАТЬ ПАРОЛЬ", 'strength': "Сложность",
        'strength_lvls': ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"],
        'warn': "Внимание", 'min_len': "Минимальная длина — 4", 'err': "Ошибка", 'choose_set': "Выберите наборы символов",
        'check_input': "Проверьте ввод", 'copied': "Пароль скопирован. Очистка через 60 сек.", 'success': "Успешно!",
        'save_title': "Сохранение", 'text_files': "Текстовые файлы", 'all_files': "Все файлы"
    },
    'en': {
        'menu_file': "File", 'menu_opts': "Options", 'menu_about': "About",
        'save': "Save", 'save_as': "Save as...", 'exit': "Exit",
        'themes': "Themes", 'lang': "Language", 'light': "Light", 'dark': "Dark", 'system': "System",
        'author_btn': "Program Author", 'author_title': "Author", 'author_main': "Maxim Melnikov", 'author_label_text': "Developed by:",
        'ver_btn': "Program Version", 'ver_title': "Version", 'ver_main': "v1.8.3 Stable", 'ver_label_text': "Current build:",
        'site_btn': "Project Site (GitHub)",
        'header': "Generation Settings", 'len_label': "Password Length (4-64):",
        'upper': "Uppercase", 'lower': "Lowercase", 'digits': "Digits", 'symb': "Symbols",
        'exclude': "Exclude similar (i, l, 1, L, o, 0)", 'ambiguous': "Exclude ambiguous (.,:;()[]{})", 'hide': "Hide symbols",
        'gen_btn': "GENERATE", 'copy_btn': "COPY PASSWORD", 'strength': "Strength",
        'strength_lvls': ["Very Weak", "Weak", "Medium", "Good", "Strong", "Very Strong"],
        'warn': "Warning", 'min_len': "Minimum length is 4", 'err': "Error", 'choose_set': "Select character sets",
        'check_input': "Check input", 'copied': "Password copied. Clear in 60 sec.", 'success': "Success!",
        'save_title': "Saving", 'text_files': "Text files", 'all_files': "All files"
    },
    'ua': {
        'menu_file': "Файл", 'menu_opts': "Опції", 'menu_about': "Про програму",
        'save': "Зберегти", 'save_as': "Зберегти як...", 'exit': "Вихід",
        'themes': "Теми", 'lang': "Мова", 'light': "Світла", 'dark': "Темна", 'system': "Системна",
        'author_btn': "Автор програми", 'author_title': "Автор", 'author_main': "Maxim Melnikov", 'author_label_text': "Програму розробив:",
        'ver_btn': "Версія програми", 'ver_title': "Версія", 'ver_main': "v1.8.3 Stable", 'ver_label_text': "Поточна збірка:",
        'site_btn': "Сайт проєкту (GitHub)",
        'header': "Налаштування генерації", 'len_label': "Довжина пароля (4-64):",
        'upper': "Великі літери", 'lower': "Малі літери", 'digits': "Цифри", 'symb': "Спецсимволи",
        'exclude': "Виключити схожі (i, l, 1, L, o, 0)", 'ambiguous': "Виключити неоднозначні (.,:;()[]{})", 'hide': "Приховати символи",
        'gen_btn': "ЗГЕНЕРУВАТИ", 'copy_btn': "КОПІЮВАТИ ПАРОЛЬ", 'strength': "Складність",
        'strength_lvls': ["Дуже слабкий", "Слабкий", "Середній", "Непоганий", "Сильний", "Дуже сильний"],
        'warn': "Увага", 'min_len': "Мінімальна довжина — 4", 'err': "Помилка", 'choose_set': "Оберіть набори символів",
        'check_input': "Перевірте введення", 'copied': "Пароль скопійовано. Очистка через 60 сек.", 'success': "Успішно!",
        'save_title': "Збереження", 'text_files': "Текстові файли", 'all_files': "Усі файли"
    }
}

current_lang = 'ru'
last_score = -1

# =============================================================================
# [RU] УТИЛИТЫ / [EN] UTILS / [UA] УТИЛІТИ
# =============================================================================
def get_system_theme():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return 'light' if value == 1 else 'dark'
    except: return 'light'

def on_closing():
    root.clipboard_clear()
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
    btn_copy.config(text=L['copy_btn'])
    cb_upper.config(text=L['upper'])
    cb_lower.config(text=L['lower'])
    cb_digits.config(text=L['digits'])
    cb_symb.config(text=L['symb'])
    cb_exclude.config(text=L['exclude'])
    cb_ambiguous.config(text=L['ambiguous'])
    cb_hide.config(text=L['hide'])
    update_strength_meter(last_score)

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
            if widget in [author_label, stars_label]: continue # Игнорируем спец-метки
            if isinstance(widget, tk.Label): widget.config(bg=bg, fg=fg)
            if isinstance(widget, tk.Button): widget.config(bg=btn, fg=fg, activebackground=btn_h)
            if isinstance(widget, tk.Checkbutton): widget.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)
            if isinstance(widget, tk.Entry) and widget != result_entry: widget.config(bg=entry_bg, fg=fg, insertbackground=fg)
    for cb in frame_checks.winfo_children():
        cb.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)
    strength_label.config(bg=bg)
    author_label.config(bg=btn, fg=fg)
    stars_label.config(bg=bg) # Звезды всегда на фоне окна

def setup_hover(widget):
    widget.bind("<Enter>", lambda e: widget.config(bg=root.current_theme_colors['btn_h']))
    widget.bind("<Leave>", lambda e: widget.config(bg=root.current_theme_colors['btn']))

# =============================================================================
# [RU] ЯДРО ГЕНЕРАТОРА / [EN] GENERATOR CORE / [UA] ЯДРО ГЕНЕРАТОРА
# =============================================================================
def update_strength_meter(score):
    global last_score
    last_score = score
    strength_canvas.delete("all")
    L = LANGUAGES[current_lang]
    if score == -1:
        strength_var.set("")
        return
    colors = ["#e74c3c", "#e74c3c", "#f39c12", "#f39c12", "#27ae60", "#27ae60"]
    width = (score + 1) * 40 
    strength_canvas.create_rectangle(0, 0, 240, 8, fill="#333333", outline="")
    strength_canvas.create_rectangle(0, 0, width, 8, fill=colors[score], outline="")
    strength_var.set(f"{L['strength']}: {L['strength_lvls'][score]}")

def generate_password():
    L = LANGUAGES[current_lang]
    try:
        raw_len = length_var.get().strip()
        if not raw_len.isdigit() or int(raw_len) < 4:
            messagebox.showwarning(L['warn'], L['min_len'])
            return
        length = int(raw_len)
        chars = ''
        if upper_var.get(): chars += string.ascii_uppercase
        if lower_var.get(): chars += string.ascii_lowercase
        if digits_var.get(): chars += string.digits
        if symbols_var.get(): chars += string.punctuation
        
        if exclude_similar_var.get():
            for s in "Il1O0": chars = chars.replace(s, "")
        if exclude_ambiguous_var.get():
            for s in ".,:;\'~\"/()[]{}|": chars = chars.replace(s, "")
            
        if not chars:
            messagebox.showerror(L['err'], L['choose_set'])
            return
        pwd = ''.join(secrets.choice(chars) for _ in range(length))
        result_var.set(pwd)
        
        variety = sum([any(c.isupper() for c in pwd), any(c.islower() for c in pwd), 
                       any(c.isdigit() for c in pwd), any(c in string.punctuation for c in pwd)])
        if length < 10: score = 0 if variety < 2 else 1
        elif 10 <= length < 14: score = 2 if variety < 3 else 3
        else: score = 4 if variety < 4 else 5
        update_strength_meter(score)
    except: messagebox.showerror(L['err'], L['check_input'])

def copy_to_clipboard():
    pwd = result_var.get()
    L = LANGUAGES[current_lang]
    if pwd:
        root.clipboard_clear()
        root.clipboard_append(pwd)
        def secure_wipe():
            time.sleep(60)
            root.clipboard_clear()
            result_var.set("")
        threading.Thread(target=secure_wipe, daemon=True).start()
        show_custom_info(L['success'], L['success'], L['copied'])

def show_custom_info(title, label_text, main_text):
    info_win = tk.Toplevel(root)
    info_win.title(title)
    info_win.geometry("320x160")
    info_win.resizable(False, False)
    x, y = root.winfo_x() + 40, root.winfo_y() + 150
    info_win.geometry(f"+{x}+{y}")
    current_bg = root.cget("bg")
    current_fg = "#FFFFFF" if current_bg == "#252526" else "#000000"
    btn_color = "#3E3E42" if current_bg == "#252526" else "#E1E1E1"
    info_win.configure(bg=current_bg)
    tk.Label(info_win, text=label_text, font=("Arial", 10), bg=current_bg, fg=current_fg).pack(pady=(25, 5))
    tk.Label(info_win, text=main_text, font=("Arial", 11, "bold"), bg=current_bg, fg=current_fg, wraplength=280).pack(pady=5)
    tk.Button(info_win, text="OK", command=info_win.destroy, width=12, bg=btn_color, fg=current_fg, relief='flat').pack(pady=15)

def save_as():
    L = LANGUAGES[current_lang]
    if result_var.get():
        path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                            filetypes=[(L['text_files'], "*.txt"), (L['all_files'], "*.*")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f: f.write(result_var.get())
                show_custom_info(L['save_title'], L['success'], os.path.basename(path))
            except: messagebox.showerror(L['err'], "Permission denied")

def open_github():
    webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python")

# =============================================================================
# [RU] ИНТЕРФЕЙС / [EN] UI / [UA] ІНТЕРФЕЙС
# =============================================================================
root = tk.Tk()
root.title("Secure Pass Pro v1.8.3")
root.geometry("400x730") # Увеличил высоту для звезд
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", on_closing)

length_var = tk.StringVar(value="12")
upper_var, lower_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
digits_var, symbols_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
exclude_similar_var, exclude_ambiguous_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
hide_var = tk.BooleanVar(value=False)
result_var, strength_var = tk.StringVar(), tk.StringVar()

menubar = tk.Menu(root)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="", command=save_as)
file_menu.add_command(label="", command=save_as)
file_menu.add_separator()
file_menu.add_command(label="", command=on_closing)
menubar.add_cascade(label="", menu=file_menu)

settings_menu = tk.Menu(menubar, tearoff=0)
theme_sub = tk.Menu(settings_menu, tearoff=0)
theme_sub.add_command(label="", command=lambda: change_theme('light'))
theme_sub.add_command(label="", command=lambda: change_theme('dark'))
theme_sub.add_command(label="", command=lambda: change_theme('system'))
settings_menu.add_cascade(label="", menu=theme_sub)

lang_sub = tk.Menu(settings_menu, tearoff=0)
lang_sub.add_command(label="Русский", command=lambda: change_lang('ru'))
lang_sub.add_command(label="English", command=lambda: change_lang('en'))
lang_sub.add_command(label="Українська", command=lambda: change_lang('ua'))
settings_menu.add_cascade(label="", menu=lang_sub)
menubar.add_cascade(label="", menu=settings_menu)

about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="", command=lambda: show_custom_info(LANGUAGES[current_lang]['author_title'], LANGUAGES[current_lang]['author_label_text'], LANGUAGES[current_lang]['author_main']))
about_menu.add_command(label="", command=lambda: show_custom_info(LANGUAGES[current_lang]['ver_title'], LANGUAGES[current_lang]['ver_label_text'], LANGUAGES[current_lang]['ver_main']))
about_menu.add_command(label="", command=open_github)
menubar.add_cascade(label="", menu=about_menu)
root.config(menu=menubar)

header_label = tk.Label(root, text="", font=("Arial", 12, "bold"))
header_label.pack(pady=15)
len_info_label = tk.Label(root, text="")
len_info_label.pack()
tk.Entry(root, textvariable=length_var, width=8, justify='center', font=("Arial", 11)).pack(pady=5)

frame_checks = tk.Frame(root)
frame_checks.pack(pady=5)
cb_upper = tk.Checkbutton(frame_checks, variable=upper_var)
cb_upper.pack(anchor='w')
cb_lower = tk.Checkbutton(frame_checks, variable=lower_var)
cb_lower.pack(anchor='w')
cb_digits = tk.Checkbutton(frame_checks, variable=digits_var)
cb_digits.pack(anchor='w')
cb_symb = tk.Checkbutton(frame_checks, variable=symbols_var)
cb_symb.pack(anchor='w')
cb_exclude = tk.Checkbutton(frame_checks, variable=exclude_similar_var)
cb_exclude.pack(anchor='w')
cb_ambiguous = tk.Checkbutton(frame_checks, variable=exclude_ambiguous_var)
cb_ambiguous.pack(anchor='w')
cb_hide = tk.Checkbutton(frame_checks, variable=hide_var, command=lambda: result_entry.config(show="*" if hide_var.get() else ""))
cb_hide.pack(anchor='w', pady=(5,0))

btn_gen = tk.Button(root, text="", command=generate_password, width=25, height=2, font=("Arial", 10, "bold"), relief='flat', bd=0)
btn_gen.pack(pady=15)
setup_hover(btn_gen)

result_entry = tk.Entry(root, textvariable=result_var, font=("Consolas", 14), width=25, state='readonly', justify='center')
result_entry.pack(pady=5, padx=20)

strength_canvas = tk.Canvas(root, width=240, height=8)
strength_canvas.pack(pady=(10, 0))
strength_label = tk.Label(root, textvariable=strength_var, font=("Arial", 10, "italic"))
strength_label.pack(pady=(0, 10))

btn_copy = tk.Button(root, text="", command=copy_to_clipboard, width=25, height=1, relief='flat', bd=0)
btn_copy.pack(pady=10)
setup_hover(btn_copy)

# Блок рейтинга и GitHub
stars_label = tk.Label(root, text="★★★★★", font=("Arial", 14, "bold"), fg="#FFD700") # Золотые звезды
stars_label.pack(side='bottom', pady=(20, 0))

author_label = tk.Label(root, text="GitHub ©", cursor="hand2", font=("Arial", 9, "bold"), padx=10, pady=5)
author_label.pack(side='bottom', pady=(5, 20))
author_label.bind("<Button-1>", lambda e: open_github())

change_theme('system')
change_lang('ru')
root.mainloop()