import tkinter as tk
from tkinter import messagebox, filedialog
import random
import string

# Функция для изменения темы (темная/светлая)
def change_theme(mode):
    if mode == 'dark':
        root.configure(bg='#333333')
        text_color = '#f0f0f0'
        button_color = '#444444'
        button_hover_color = '#666666'
        entry_color = '#555555'
        checkbutton_fg = '#f0f0f0'
        checkbutton_bg = '#333333'
        checkbutton_selectcolor = '#ffffff'
        label_color = '#ffffff'
        strength_label_color = '#d1e8ff'
    else:
        root.configure(bg='white')
        text_color = 'black'
        button_color = '#e0e0e0'
        button_hover_color = '#c0c0c0'
        entry_color = '#ffffff'
        checkbutton_fg = 'black'
        checkbutton_bg = 'white'
        checkbutton_selectcolor = 'black'
        label_color = '#333333'
        strength_label_color = '#3333cc'

    # Обновляем элементы интерфейса с учетом новой темы
    for widget in root.winfo_children():
        if isinstance(widget, tk.Label):
            widget.config(fg=text_color, bg=root.cget('bg'), font=("Arial", 12))
        elif isinstance(widget, tk.Entry):
            widget.config(fg=text_color, bg=entry_color, font=("Arial", 12), bd=2, relief="solid", insertbackground="white")
        elif isinstance(widget, tk.Checkbutton):
            widget.config(fg=checkbutton_fg, bg=checkbutton_bg, selectcolor=checkbutton_selectcolor, font=("Arial", 10))
        elif isinstance(widget, tk.Button):
            widget.config(bg=button_color, fg=text_color, relief="flat", bd=2, font=("Arial", 12, "bold"))
            widget.bind("<Enter>", lambda event, btn=widget: on_hover(btn, button_hover_color))
            widget.bind("<Leave>", lambda event, btn=widget: on_leave(btn, button_color))

    # Изменяем цвет текста на кнопке, которая активирует темный/светлый режим
    theme_button.config(bg=button_color, fg=text_color)

    # Изменяем цвет лейбла с силой пароля
    strength_label.config(fg=strength_label_color)

def on_hover(btn, hover_color):
    """Эффект при наведении на кнопку"""
    btn.config(bg=hover_color)

def on_leave(btn, normal_color):
    """Восстановление цвета кнопки при убирании курсора"""
    btn.config(bg=normal_color)

def generate_password():
    try:
        length = int(length_var.get())
        if length > 64 or length < 1:
            raise ValueError

        use_upper = upper_var.get()
        use_lower = lower_var.get()
        use_digits = digits_var.get()
        use_symbols = symbols_var.get()

        characters = ''
        if use_upper:
            characters += string.ascii_uppercase
        if use_lower:
            characters += string.ascii_lowercase
        if use_digits:
            characters += string.digits
        if use_symbols:
            characters += string.punctuation

        if not characters:
            raise Exception("Выберите хотя бы один тип символов.")

        password = ''.join(random.choice(characters) for _ in range(length))
        result_var.set(password)
        evaluate_strength(password)
    except ValueError:
        messagebox.showerror("Ошибка", "Введите корректную длину от 1 до 64.")
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def copy_to_clipboard():
    password = result_var.get()
    if password:
        root.clipboard_clear()
        root.clipboard_append(password)
        messagebox.showinfo("Скопировано", "Пароль скопирован в буфер обмена.")

def save_to_file():
    password = result_var.get()
    if password:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(password)
            messagebox.showinfo("Сохранено", "Пароль сохранён в файл.")

def evaluate_strength(password):
    score = 0
    if len(password) >= 12:
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.islower() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in string.punctuation for c in password):
        score += 1

    strength = {
        0: "Очень слабый",
        1: "Слабый",
        2: "Средний",
        3: "Неплохой",
        4: "Сильный",
        5: "Очень сильный"
    }
    strength_var.set("Сложность: " + strength.get(score, "Неизвестно"))

# Создание окна
root = tk.Tk()
root.title("Генератор паролей")

# Переменные
length_var = tk.StringVar(value="12")
upper_var = tk.BooleanVar(value=True)
lower_var = tk.BooleanVar(value=True)
digits_var = tk.BooleanVar(value=True)
symbols_var = tk.BooleanVar(value=True)
result_var = tk.StringVar()
strength_var = tk.StringVar()

# Центрировать окно на экране
def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")

center_window(root)

# Интерфейс
tk.Label(root, text="Длина пароля (1-64):").grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
tk.Entry(root, textvariable=length_var, width=5).grid(row=0, column=1, sticky="w", padx=10, pady=5)

tk.Checkbutton(root, text="Верхний регистр (A-Z)", variable=upper_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
tk.Checkbutton(root, text="Нижний регистр (a-z)", variable=lower_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=10)
tk.Checkbutton(root, text="Цифры (0-9)", variable=digits_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=10)
tk.Checkbutton(root, text="Символы (!@#...)", variable=symbols_var).grid(row=4, column=0, columnspan=2, sticky="w", padx=10)

tk.Button(root, text="Сгенерировать", command=generate_password).grid(row=5, column=0, columnspan=2, pady=10, sticky="n", padx=10)

tk.Entry(root, textvariable=result_var, width=30, state='readonly').grid(row=6, column=0, columnspan=2, pady=5, padx=10)
strength_label = tk.Label(root, textvariable=strength_var, fg="#3333cc")
strength_label.grid(row=7, column=0, columnspan=2, pady=5, padx=10)

tk.Button(root, text="Скопировать", command=copy_to_clipboard).grid(row=8, column=0, pady=5, padx=10)
tk.Button(root, text="Сохранить", command=save_to_file).grid(row=8, column=1, pady=5, padx=10)

# Кнопки для изменения темы
def switch_to_dark():
    change_theme('dark')

def switch_to_light():
    change_theme('light')

# Кнопки для переключения темы
theme_button = tk.Button(root, text="Темный режим", command=switch_to_dark)
theme_button.grid(row=9, column=0, pady=5, padx=10)
light_button = tk.Button(root, text="Светлый режим", command=switch_to_light)
light_button.grid(row=9, column=1, pady=5, padx=10)

# Имя автора (ссылка на GitHub)
def open_github(event=None):
    import webbrowser
    webbrowser.open_new("https://github.com/Maxim1993271")

author_label = tk.Label(root, text="Автор: Максим (GitHub)", fg="blue", cursor="hand2")
author_label.grid(row=10, column=0, columnspan=2, pady=(10, 5))
author_label.bind("<Button-1>", open_github)

# Центрировать элементы в окне
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Устанавливаем минимальный размер окна
root.minsize(400, 300)

# Изначально устанавливаем светлый режим
change_theme('light')

# Запуск
root.mainloop()
