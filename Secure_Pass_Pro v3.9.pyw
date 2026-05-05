import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import secrets
import string
import webbrowser
import os
import qrcode
from PIL import Image
import platform
import math

# =============================================================================
# LOCALIZATION DATA - Triple-Language Support (RU, EN, UA)
# =============================================================================
LANGUAGES = {
    "RU": {
        "title": "Настройки генерации", "len": "Длина пароля",
        "upper": "Заглавные буквы", "lower": "Строчные буквы",
        "digits": "Цифры", "symb": "Спецсимволы",
        "ambig": "Исключить похожие (i, l, 1, L, o, 0, O)",
        "at_least": "Минимум 1 из каждой категории", "hide": "Скрывать символы",
        "btn_gen": "СГЕНЕРИРОВАТЬ", "btn_copy": "КОПИРОВАТЬ ПАРОЛЬ",
        "btn_save": "СОХРАНИТЬ В ФАЙЛ", "btn_open": "ОТКРЫТЬ ФАЙЛ",
        "btn_qr": "QR-КОД ПАРОЛЯ", "btn_hist": "ИСТОРИЯ",
        "btn_upd": "ОБНОВИТЬ ПРОГРАММУ", "author": "Автор: Максим Мельников",
        "strength": "Сложность", "time": "Время взлома",
        "success": "Пароль", "copied": "Пароль скопирован!",
        "saved": "Пароль сохранен!", "theme": "Тема",
        "upd_msg": "Загрузка обновления v3.9...",
        "radius": "Закругление углов",
        "t_sec": "мгновенно", "t_min": "мин.", "t_hour": "час.", 
        "t_days": "дн.", "t_years": "лет", "t_cent": "века",
        "file_type": "Текстовый файл",
        "win_qr": "QR-код пароля", "win_upd": "Обновление программы",
        "sys": "Системная", "dark": "Темная", "light": "Светлая"
    },
    "EN": {
        "title": "Generation Settings", "len": "Password Length",
        "upper": "Uppercase Letters", "lower": "Lowercase Letters",
        "digits": "Digits", "symb": "Special Symbols",
        "ambig": "Exclude ambiguous (i, l, 1, L, o, 0, O)",
        "at_least": "At least one from each", "hide": "Hide symbols",
        "btn_gen": "GENERATE", "btn_copy": "COPY PASSWORD",
        "btn_save": "SAVE TO FILE", "btn_open": "OPEN FILE",
        "btn_qr": "PASSWORD QR-CODE", "btn_hist": "HISTORY",
        "btn_upd": "UPDATE PROGRAM", "author": "Author: Maxim Melnikov",
        "strength": "Complexity", "time": "Crack time",
        "success": "Password", "copied": "Password copied!",
        "saved": "Password saved!", "theme": "Theme",
        "upd_msg": "Downloading v3.9 update...",
        "radius": "Corner Radius",
        "t_sec": "instantly", "t_min": "min.", "t_hour": "hours", 
        "t_days": "days", "t_years": "years", "t_cent": "centuries",
        "file_type": "Text File",
        "win_qr": "Password QR-Code", "win_upd": "Software Update",
        "sys": "System", "dark": "Dark", "light": "Light"
    },
    "UA": {
        "title": "Налаштування генерації", "len": "Довжина пароля",
        "upper": "Великі літери", "lower": "Малі літери",
        "digits": "Цифри", "symb": "Спецсимволи",
        "ambig": "Виключити схожі (i, l, 1, L, o, 0, O)",
        "at_least": "Мінімум 1 з кожної категорії", "hide": "Приховати символи",
        "btn_gen": "ЗГЕНЕРУВАТИ", "btn_copy": "КОПІЮВАТИ ПАРОЛЬ",
        "btn_save": "ЗБЕРЕГТИ У ФАЙЛ", "btn_open": "ВІДКРИТИ ФАЙЛ",
        "btn_qr": "QR-КОД ПАРОЛЯ", "btn_hist": "ІСТОРІЯ",
        "btn_upd": "ОНОВИТИ ПРОГРАМУ", "author": "Автор: Максим Мельников",
        "strength": "Складність", "time": "Час зламу",
        "success": "Пароль", "copied": "Пароль скопійовано!",
        "saved": "Пароль збережено!", "theme": "Тема",
        "upd_msg": "Завантаження оновлення v3.9...",
        "radius": "Закруглення кутів",
        "t_sec": "миттєво", "t_min": "хв.", "t_hour": "год.", 
        "t_days": "дн.", "t_years": "років", "t_cent": "століття",
        "file_type": "Текстовий файл",
        "win_qr": "QR-код пароля", "win_upd": "Оновлення програми",
        "sys": "Системна", "dark": "Темная", "light": "Світла"
    }
}

class SecurePassPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.version = "v3.9"
        self.github_url = "https://github.com/Maximka1993271/Password-Generator-Python"
        # Прямая ссылка на EXE для обновлений
        self.update_exe_url = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe"
        
        self.title(f"Secure Pass Pro {self.version}")
        self.geometry("420x860")
        self.resizable(False, False)
        
        self.current_lang = "RU"
        self.history = []
        self.all_widgets = [] 

        self.setup_vars()
        self.setup_ui()

    def setup_vars(self):
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symb_var = tk.BooleanVar(value=True)
        self.exclude_ambig_var = tk.BooleanVar(value=False)
        self.at_least_one_var = tk.BooleanVar(value=True)
        self.hide_var = tk.BooleanVar(value=False)

    def setup_ui(self):
        self.lbl_title = ctk.CTkLabel(self, text="", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=(10, 0))

        self.lbl_author = ctk.CTkLabel(self, text="", font=("Segoe UI", 11, "italic"), text_color="gray")
        self.lbl_author.pack(pady=(0, 5))

        self.opt_frame = ctk.CTkFrame(self, corner_radius=10)
        self.opt_frame.pack(pady=5, padx=20, fill="x")
        self.all_widgets.append(self.opt_frame)

        self.lbl_len = ctk.CTkLabel(self.opt_frame, text="", font=("Segoe UI", 13, "bold"))
        self.lbl_len.pack(pady=(5, 0))
        
        self.slider = ctk.CTkSlider(self.opt_frame, from_=4, to=64, number_of_steps=60, height=16, command=self.update_slider_text)
        self.slider.set(20)
        self.slider.pack(pady=5, padx=15)

        self.cb_upper = self.create_cb(self.upper_var)
        self.cb_lower = self.create_cb(self.lower_var)
        self.cb_digits = self.create_cb(self.digits_var)
        self.cb_symb = self.create_cb(self.symb_var)
        self.cb_ambig = self.create_cb(self.exclude_ambig_var)
        self.cb_at_least = self.create_cb(self.at_least_one_var)
        self.cb_hide = self.create_cb(self.hide_var, command=self.toggle_visibility)

        self.entry_res = ctk.CTkEntry(self, height=38, font=("Consolas", 16), justify="center", corner_radius=8)
        self.entry_res.pack(pady=5, padx=20, fill="x")
        self.all_widgets.append(self.entry_res)

        self.strength_bar = ctk.CTkProgressBar(self, width=340, height=8)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=2)
        
        self.lbl_strength = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_strength.pack()
        self.lbl_time = ctk.CTkLabel(self, text="", font=("Segoe UI", 11))
        self.lbl_time.pack(pady=(0, 5))

        self.btn_gen = self.create_main_btn(self.generate, "", height=36, bold=True)
        self.btn_copy = self.create_main_btn(self.copy_password, "", fg="#28a745", hover="#218838")
        self.btn_save = self.create_main_btn(self.save_to_file, "", fg="#17a2b8", hover="#138496")
        self.btn_file = self.create_main_btn(self.open_file, "", fg="#17a2b8", hover="#138496")
        self.btn_qr = self.create_main_btn(self.show_qr_window, "", fg="#6f42c1", hover="#5a32a3")
        self.btn_hist = self.create_main_btn(self.show_history_window, "", fg="transparent", border=1, text_col=["#3b3b3b", "#ffffff"])
        self.btn_upd = self.create_main_btn(self.check_updates, "", fg="#f39c12", hover="#e67e22")

        self.lbl_radius = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_radius.pack(pady=(5, 0))
        self.slider_radius = ctk.CTkSlider(self, from_=0, to=20, number_of_steps=20, height=14, command=self.change_corner_radius)
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=(0, 5), padx=60, fill="x")

        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=5, padx=20, fill="x")

        self.lang_menu = ctk.CTkOptionMenu(self.bottom_frame, values=["RU", "EN", "UA"], width=70, height=22, command=self.change_lang)
        self.lang_menu.set("RU")
        self.lang_menu.pack(side="left")
        
        self.theme_menu = ctk.CTkOptionMenu(self.bottom_frame, values=["System", "Dark", "Light"], width=100, height=22, command=self.change_theme)
        self.theme_menu.pack(side="right")

        self.btn_github = ctk.CTkButton(self, text="GitHub ©", height=20, width=90, fg_color="#24292e", font=("Segoe UI", 10), command=self.open_github)
        self.btn_github.pack(pady=(5, 0))
        self.all_widgets.append(self.btn_github)

        self.lbl_stars = ctk.CTkLabel(self, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_stars.pack(pady=(0, 10))

        self.update_localization()

    def generate(self):
        """Security: Uses secrets (CSPRNG) for generation."""
        pools = []
        ambig = "il1Lo0O"
        def filter_chars(s): return "".join(c for c in s if c not in ambig) if self.exclude_ambig_var.get() else s

        if self.upper_var.get(): pools.append(filter_chars(string.ascii_uppercase))
        if self.lower_var.get(): pools.append(filter_chars(string.ascii_lowercase))
        if self.digits_var.get(): pools.append(filter_chars(string.digits))
        if self.symb_var.get(): pools.append(string.punctuation)

        pools = [p for p in pools if p]
        if not pools: return

        length = int(self.slider.get())
        full_pool = "".join(pools)

        if self.at_least_one_var.get() and length >= len(pools):
            res = [secrets.choice(p) for p in pools] + [secrets.choice(full_pool) for _ in range(length - len(pools))]
            secrets.SystemRandom().shuffle(res)
        else:
            res = [secrets.choice(full_pool) for _ in range(length)]

        pwd = "".join(res)
        self.entry_res.delete(0, tk.END)
        self.entry_res.insert(0, pwd)
        self.history.append(f"[{length}] {pwd}")
        self.update_complexity_labels()

    def check_updates(self):
        """Opens direct download link in browser."""
        self.show_custom_message(LANGUAGES[self.current_lang]["upd_msg"], "win_upd")
        webbrowser.open(self.update_exe_url)

    def update_localization(self):
        l = LANGUAGES[self.current_lang]
        self.lbl_title.configure(text=l["title"])
        self.lbl_author.configure(text=l["author"])
        self.lbl_len.configure(text=f"{l['len']}: {int(self.slider.get())}")
        self.lbl_radius.configure(text=f"{l['radius']}: {int(self.slider_radius.get())}")
        self.cb_upper.configure(text=l["upper"])
        self.cb_lower.configure(text=l["lower"])
        self.cb_digits.configure(text=l["digits"])
        self.cb_symb.configure(text=l["symb"])
        self.cb_ambig.configure(text=l["ambig"])
        self.cb_at_least.configure(text=l["at_least"])
        self.cb_hide.configure(text=l["hide"])
        self.btn_gen.configure(text=l["btn_gen"])
        self.btn_copy.configure(text=l["btn_copy"])
        self.btn_save.configure(text=l["btn_save"])
        self.btn_file.configure(text=l["btn_open"])
        self.btn_qr.configure(text=l["btn_qr"])
        self.btn_hist.configure(text=l["btn_hist"])
        self.btn_upd.configure(text=l["btn_upd"])
        self.theme_menu.configure(values=[l["sys"], l["dark"], l["light"]])
        self.update_complexity_labels()

    def create_cb(self, var, command=None):
        cb = ctk.CTkCheckBox(self.opt_frame, text="", variable=var, font=("Segoe UI", 11), checkbox_width=18, checkbox_height=18,
                             command=lambda: [command() if command else None, self.update_complexity_labels()])
        cb.pack(anchor="w", padx=30, pady=2)
        return cb

    def create_main_btn(self, cmd, txt, fg=None, hover=None, height=30, bold=False, border=0, text_col=None):
        btn = ctk.CTkButton(self, text=txt, height=height, command=cmd, border_width=border,
                           font=("Segoe UI", 12 if bold else 11, "bold"))
        if fg: btn.configure(fg_color=fg)
        if hover: btn.configure(hover_color=hover)
        if text_col: btn.configure(text_color=text_col)
        btn.pack(pady=2, padx=40, fill="x")
        self.all_widgets.append(btn)
        return btn

    def get_time_estimate(self, entropy):
        if entropy <= 0: return ""
        seconds = (2**entropy) / 10_000_000_000
        l = LANGUAGES[self.current_lang]
        if seconds < 60: return l['t_sec']
        if seconds < 3600: return f"~{int(seconds/60)} {l['t_min']}"
        if seconds < 86400: return f"~{int(seconds/3600)} {l['t_hour']}"
        return f">100 {l['t_cent']}"

    def update_complexity_labels(self):
        l = LANGUAGES[self.current_lang]
        alphabet = sum([26 if self.upper_var.get() else 0, 26 if self.lower_var.get() else 0, 10 if self.digits_var.get() else 0, 32 if self.symb_var.get() else 0])
        entropy = int(self.slider.get()) * math.log2(alphabet) if alphabet > 0 else 0
        color = "#ff4b4b" if entropy < 40 else "#ffcc00" if entropy < 60 else "#2ecc71"
        self.strength_bar.set(min(entropy / 100, 1.0))
        self.strength_bar.configure(progress_color=color)
        self.lbl_strength.configure(text=l["strength"], text_color=color)
        self.lbl_time.configure(text=f"{l['time']}: {self.get_time_estimate(entropy)}", text_color=color)

    def show_history_window(self):
        win = ctk.CTkToplevel(self)
        win.title(LANGUAGES[self.current_lang]["btn_hist"])
        win.attributes("-topmost", True)
        self.center_window(win, 380, 400)
        txt = ctk.CTkTextbox(win, font=("Consolas", 12), border_width=2)
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        txt.configure(state="normal") 
        if self.history: txt.insert("0.0", "\n".join(self.history[::-1]))
        else: txt.insert("0.0", "...")
        txt.configure(state="disabled")

    def show_qr_window(self):
        pwd = self.entry_res.get()
        if not pwd: return
        qr_win = ctk.CTkToplevel(self)
        qr_win.title(LANGUAGES[self.current_lang]["win_qr"])
        qr_win.attributes("-topmost", True)
        self.center_window(qr_win, 260, 260)
        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(pwd)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))
        ctk.CTkLabel(qr_win, image=ctk_img, text="").pack(pady=20)

    def copy_password(self):
        pwd = self.entry_res.get()
        if pwd: 
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.show_custom_message(LANGUAGES[self.current_lang]["copied"], "success")

    def save_to_file(self):
        pwd = self.entry_res.get()
        if not pwd: return
        l = LANGUAGES[self.current_lang]
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[(l["file_type"], "*.txt"), ("All Files", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f: f.write(f"SecurePassPro\n{l['success']}: {pwd}")
            self.show_custom_message(l["saved"], "success")

    def show_custom_message(self, message, title_key):
        l = LANGUAGES[self.current_lang]
        msg_win = ctk.CTkToplevel(self)
        msg_win.title(l[title_key])
        msg_win.attributes("-topmost", True)
        self.center_window(msg_win, 280, 130)
        ctk.CTkLabel(msg_win, text=message, font=("Segoe UI", 12), wraplength=240).pack(pady=15)
        ctk.CTkButton(msg_win, text="OK", width=80, height=26, command=msg_win.destroy).pack()

    def open_github(self): webbrowser.open(self.github_url)
    def change_lang(self, choice): self.current_lang = choice; self.update_localization()
    def change_theme(self, choice): 
        l = LANGUAGES[self.current_lang]
        theme_map = {l["sys"]: "System", l["dark"]: "Dark", l["light"]: "Light"}
        ctk.set_appearance_mode(theme_map.get(choice, "System"))
    def change_corner_radius(self, val): 
        for w in self.all_widgets: w.configure(corner_radius=int(val))
    def update_slider_text(self, val): 
        self.lbl_len.configure(text=f"{LANGUAGES[self.current_lang]['len']}: {int(val)}")
        self.update_complexity_labels()
    def toggle_visibility(self): self.entry_res.configure(show="*" if self.hide_var.get() else "")
    def open_file(self):
        path = filedialog.askopenfilename()
        if path: (os.startfile(path) if platform.system() == "Windows" else webbrowser.open(path))
    def center_window(self, win, w, h):
        self.update_idletasks()
        win.geometry(f"{w}x{h}+{self.winfo_x() + (self.winfo_width()//2) - (w//2)}+{self.winfo_y() + (self.winfo_height()//2) - (h//2)}")

if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()