import tkinter as tk
from tkinter import messagebox, filedialog
import secrets
import string
import webbrowser
import os
import threading
import time

# 1. Функция для определения системной темы
def get_system_theme():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return 'light' if value == 1 else 'dark'
    except:
        return 'light'

# Глобальная переменная для пути
current_file_path = None

# 2. Функция смены темы
def change_theme(mode):
    if mode == 'system':
        mode = get_system_theme()
    
    if mode == 'dark':
        bg, fg, btn, btn_h, entry_bg = '#252526', '#FFFFFF', '#3E3E42', '#454545', '#333333'
        res_bg, res_fg = '#1E1E1E', '#4EC9B0' 
        check_sel = '#3E3E42'
    else:
        bg, fg, btn, btn_h, entry_bg = '#F3F3F3', '#000000', '#E1E1E1', '#D0D0D0', '#FFFFFF'
        res_bg, res_fg = '#FFFFFF', '#005FB8'
        check_sel = '#FFFFFF'

    root.configure(bg=bg)
    result_entry.config(readonlybackground=res_bg, fg=res_fg, bg=res_bg)
    frame_checks.config(bg=bg)
    strength_canvas.config(bg=bg, highlightthickness=0)
    
    root.current_theme_colors = {'btn': btn, 'btn_h': btn_h}

    for widget in root.winfo_children():
        if isinstance(widget, tk.Label) and widget != author_label:
            widget.config(bg=bg, fg=fg)
        elif isinstance(widget, tk.Checkbutton):
            widget.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg, activeforeground=fg)
        elif isinstance(widget, tk.Button) and widget != author_label:
            widget.config(bg=btn, fg=fg, activebackground=btn_h)
        elif isinstance(widget, tk.Entry) and widget != result_entry:
            widget.config(bg=entry_bg, fg=fg, insertbackground=fg)

    for cb in frame_checks.winfo_children():
        if isinstance(cb, tk.Checkbutton):
            cb.config(bg=bg, fg=fg, selectcolor=check_sel, activebackground=bg)

    strength_label.config(bg=bg)
    author_label.config(bg=btn, fg=fg)

def setup_hover(widget):
    widget.bind("<Enter>", lambda e: widget.config(bg=root.current_theme_colors['btn_h']))
    widget.bind("<Leave>", lambda e: widget.config(bg=root.current_theme_colors['btn']))

# 3. Логика сложности
def update_strength_meter(score):
    strength_canvas.delete("all")
    colors = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71", "#27ae60", "#1abc9c"]
    labels = ["Очень слабый", "Слабый", "Средний", "Неплохой", "Сильный", "Очень сильный"]
    
    width = (score + 1) * 40 
    strength_canvas.create_rectangle(0, 0, 240, 8, fill="#333333", outline="")
    strength_canvas.create_rectangle(0, 0, width, 8, fill=colors[score], outline="")
    strength_var.set(f"Сложность: {labels[score]}")

def validate_digit_input(P):
    if P == "" or (P.isdigit() and len(P) <= 2):
        return True
    return False

# 4. Основные функции
def generate_password():
    try:
        val = length_var.get()
        if not val or int(val) < 4:
            messagebox.showwarning("Внимание", "Минимальная длина — 4")
            return
            
        length = int(val)
        chars = ''
        if upper_var.get(): chars += string.ascii_uppercase
        if lower_var.get(): chars += string.ascii_lowercase
        if digits_var.get(): chars += string.digits
        if symbols_var.get(): chars += string.punctuation
        
        if exclude_similar_var.get():
            for s in "Il1O0": chars = chars.replace(s, "")

        if not chars:
            messagebox.showerror("Ошибка", "Выберите наборы символов")
            return
        
        pwd = ''.join(secrets.choice(chars) for _ in range(length))
        result_var.set(pwd)
        
        score = sum([len(pwd) >= 12, any(c.isupper() for c in pwd), any(c.islower() for c in pwd), 
                     any(c.isdigit() for c in pwd), any(c in string.punctuation for c in pwd)])
        update_strength_meter(score)
    except:
        messagebox.showerror("Ошибка", "Проверьте ввод")

def copy_to_clipboard():
    pwd = result_var.get()
    if pwd:
        root.clipboard_clear()
        root.clipboard_append(pwd)
        threading.Thread(target=lambda: (time.sleep(60), root.clipboard_clear()), daemon=True).start()
        show_custom_info("Буфер", "Успешно!", "Пароль скопирован. Очистка через 60 сек.")

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

# Функции сохранения
def save_quick():
    global current_file_path
    if not result_var.get(): return
    if current_file_path and os.path.exists(current_file_path):
        with open(current_file_path, "w", encoding="utf-8") as f:
            f.write(result_var.get())
        show_custom_info("Сохранение", "Файл обновлен:", os.path.basename(current_file_path))
    else:
        save_as()

def save_as():
    global current_file_path
    if result_var.get():
        path = filedialog.asksaveasfilename(defaultextension=".txt", 
                                            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            current_file_path = path
            with open(path, "w", encoding="utf-8") as f:
                f.write(result_var.get())
            show_custom_info("Сохранение", "Успешно!", os.path.basename(path))

def open_github():
    webbrowser.open("https://github.com/Maximka1993271/Password-Generator-Python")

# 5. Интерфейс
root = tk.Tk()
root.title("Secure Pass Pro v1.8.3")
root.geometry("400x670")
root.resizable(False, False)
root.current_theme_colors = {}

if os.path.exists("icon.ico"):
    root.iconbitmap("icon.ico")

length_var = tk.StringVar(value="12")
upper_var, lower_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
digits_var, symbols_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
exclude_similar_var, hide_var = tk.BooleanVar(value=False), tk.BooleanVar(value=False)
result_var, strength_var = tk.StringVar(), tk.StringVar(value="Сложность: -")

# --- МЕНЮ ---
menubar = tk.Menu(root)

# МЕНЮ ФАЙЛ (ВОЗВРАЩЕНО)
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Сохранить", command=save_quick)
file_menu.add_command(label="Сохранить как...", command=save_as)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=root.quit)
menubar.add_cascade(label="Файл", menu=file_menu)

settings_menu = tk.Menu(menubar, tearoff=0)
theme_sub = tk.Menu(settings_menu, tearoff=0)
theme_sub.add_command(label="Светлая", command=lambda: change_theme('light'))
theme_sub.add_command(label="Тёмная", command=lambda: change_theme('dark'))
theme_sub.add_command(label="Системная", command=lambda: change_theme('system'))
settings_menu.add_cascade(label="Темы", menu=theme_sub)
menubar.add_cascade(label="Настройки", menu=settings_menu)

about_menu = tk.Menu(menubar, tearoff=0)
about_menu.add_command(label="Автор программы", command=lambda: show_custom_info("Автор", "Программу разработал:", "Maxim Melnikov"))
about_menu.add_command(label="Версия программы", command=lambda: show_custom_info("Версия", "Текущая сборка:", "v1.8.3 Stable"))
about_menu.add_command(label="Сайт проекта (GitHub)", command=open_github)
menubar.add_cascade(label="О программе", menu=about_menu)

root.config(menu=menubar)

# --- ГЛАВНЫЙ ЭКРАН ---
tk.Label(root, text="Настройки генерации", font=("Arial", 12, "bold")).pack(pady=15)
tk.Label(root, text="Длина пароля (4-64):").pack()
tk.Entry(root, textvariable=length_var, width=8, justify='center', font=("Arial", 11), 
         validate='key', validatecommand=(root.register(validate_digit_input), '%P')).pack(pady=5)

frame_checks = tk.Frame(root)
frame_checks.pack(pady=5)
for text, var in [("Заглавные буквы", upper_var), ("Строчные буквы", lower_var), 
                  ("Цифры", digits_var), ("Спецсимволы", symbols_var), 
                  ("Исключить похожие (i, l, 1, L, o, 0)", exclude_similar_var)]:
    tk.Checkbutton(frame_checks, text=text, variable=var).pack(anchor='w')

tk.Checkbutton(frame_checks, text="Скрывать символы", variable=hide_var, 
               command=lambda: result_entry.config(show="*" if hide_var.get() else "")).pack(anchor='w', pady=(5,0))

btn_gen = tk.Button(root, text="СГЕНЕРИРОВАТЬ", command=generate_password, width=25, height=2, font=("Arial", 10, "bold"), relief='flat', bd=0)
btn_gen.pack(pady=15)
setup_hover(btn_gen)

# Поле вывода пароля (Шрифт Consolas + Отступы)
result_entry = tk.Entry(root, textvariable=result_var, font=("Consolas", 14), width=25, 
                        state='readonly', justify='center')
result_entry.pack(pady=5, padx=20)

# Индикатор сложности
strength_canvas = tk.Canvas(root, width=240, height=8)
strength_canvas.pack(pady=(10, 0))
strength_label = tk.Label(root, textvariable=strength_var, font=("Arial", 10, "italic"))
strength_label.pack(pady=(0, 10))

btn_copy = tk.Button(root, text="КОПИРОВАТЬ ПАРОЛЬ", command=copy_to_clipboard, width=25, height=1, relief='flat', bd=0)
btn_copy.pack(pady=10)
setup_hover(btn_copy)

author_label = tk.Label(root, text="GitHub ©", cursor="hand2", font=("Arial", 9, "bold"), padx=10, pady=5)
author_label.pack(side='bottom', pady=20)
author_label.bind("<Button-1>", lambda e: open_github())

change_theme('system')
root.mainloop()