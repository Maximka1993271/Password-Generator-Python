import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import secrets
import string
import webbrowser
import os
import sys
import math
import configparser
import platform

# =============================================================================
# SOUND ENGINE / ЗВУКОВОЙ ДВИЖОК / ЗВУКОВИЙ ДВИГУН
# =============================================================================
def _beep(freq: int, ms: int) -> None:
    """
    EN: System beep for Windows. Ignored on other OS.
    RU: Системный звук для Windows. Игнорируется на других ОС.
    UA: Системний звук для Windows. Ігнорується на інших ОС.
    """
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(freq, ms)
        except Exception:
            pass

def sound_generate(): _beep(800, 50); _beep(1200, 50)  # Success / Успех / Успіх
def sound_copy(): _beep(1500, 100)                    # Copy / Копирование / Копіювання
def sound_action(): _beep(1000, 60)                   # Action / Действие / Дія
def sound_error(): _beep(400, 150); _beep(300, 150)   # Error / Ошибка / Помилка

# =============================================================================
# DEPENDENCIES CHECK / ПРОВЕРКА ЗАВИСИМОСТЕЙ / ПЕРЕВІРКА ЗАЛЕЖНОСТЕЙ
# =============================================================================
try:
    import qrcode
    from PIL import Image, ImageTk
except ImportError:
    _error_root = tk.Tk()
    _error_root.withdraw()
    messagebox.showerror("Критическая ошибка", 
                         "Отсутствуют необходимые библиотеки!\n\n"
                         "Выполните в терминале:\n"
                         "pip install qrcode[pil] pillow customtkinter")
    sys.exit(1)

# =============================================================================
# TOOLTIP CLASS / КЛАСС ПОДСКАЗОК / КЛАС ПІДКАЗОК
# =============================================================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show_tip(self):
        """EN: Display tooltip. RU: Показать подсказку. UA: Показати підказку."""
        if self.tip_window or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 35
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self):
        """EN: Hide tooltip. RU: Скрыть подсказку. UA: Приховати підказку."""
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# =============================================================================
# GLOBAL SETTINGS / ГЛОБАЛЬНЫЕ НАСТРОЙКИ / ГЛОБАЛЬНІ НАЛАШТУВАННЯ
# =============================================================================
CONFIG_FILE = "config.ini"
HISTORY_MAX = 50
UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe"

LANGUAGES = {
    "RU": {
        "win_title": "Secure Pass Pro v3.9",
        "title": "Настройки генерации", "len": "Длина пароля", "author": "Автор: Максим Мельников",
        "upper": "Заглавные буквы", "lower": "Строчные буквы", "digits": "Цифры", "symb": "Спецсимволы",
        "ambig": "Исключить похожие (i, l, 1, L, o, 0, O)", "at_least": "Минимум 1 из каждой категории",
        "hide": "Скрывать символы", "btn_gen": "СГЕНЕРИРОВАТЬ", "btn_copy": "КОПИРОВАТЬ ПАРОЛЬ",
        "btn_save": "СОХРАНИТЬ В ФАЙЛ", "btn_open": "ОТКРЫТЬ ФАЙЛ", "btn_qr": "QR-КОД ПАРОЛЯ",
        "btn_hist": "ИСТОРИЯ", "btn_upd": "ОБНОВИТЬ ПРОГРАММУ", "strength": "Сложность",
        "radius": "Закругление углов", "sys": "Системная", "dark": "Тёмная", "light": "Светлая",
        "copied": "Скопировано!", "bits": "бит", "qr_title": "QR-код пароля", "hist_title": "История",
        "t4": "Меньше секунды", "t5": "Несколько секунд", "t6": "Несколько минут", "t7": "Часы",
        "t8": "Дни", "t10": "Года", "t12": "Десятилетия", "t14": "Столетия", "t15": "Тысячелетия",
        "tt_gen": "Создать новый случайный пароль", "tt_copy": "Копировать в буфер обмена",
        "tt_save": "Сохранить пароль в текстовый файл", "tt_open": "Загрузить пароль из файла",
        "tt_qr": "Создать QR-код для сканирования", "tt_hist": "Посмотреть последние пароли",
        "tt_upd": "Проверить наличие обновлений"
    },
    "EN": {
        "win_title": "Secure Pass Pro v3.9",
        "title": "Generation Settings", "len": "Password Length", "author": "Author: Maxim Melnikov",
        "upper": "Uppercase Letters", "lower": "Lowercase Letters", "digits": "Digits", "symb": "Special Symbols",
        "ambig": "Exclude ambiguous", "at_least": "At least one from each category",
        "hide": "Hide symbols", "btn_gen": "GENERATE", "btn_copy": "COPY PASSWORD",
        "btn_save": "SAVE TO FILE", "btn_open": "OPEN FILE", "btn_qr": "QR-CODE",
        "btn_hist": "HISTORY", "btn_upd": "UPDATE PROGRAM", "strength": "Strength",
        "radius": "Corner Radius", "sys": "System", "dark": "Dark", "light": "Light",
        "copied": "Copied!", "bits": "bits", "qr_title": "Password QR-Code", "hist_title": "History",
        "t4": "Less than a second", "t5": "Seconds", "t6": "Minutes", "t7": "Hours",
        "t8": "Days", "t10": "Years", "t12": "Decades", "t14": "Centuries", "t15": "Millennia",
        "tt_gen": "Create a new random password", "tt_copy": "Copy to clipboard",
        "tt_save": "Save password to a text file", "tt_open": "Load password from file",
        "tt_qr": "Generate QR-code for scanning", "tt_hist": "View recent passwords",
        "tt_upd": "Check for updates"
    },
    "UA": {
        "win_title": "Secure Pass Pro v3.9",
        "title": "Налаштування генерації", "len": "Довжина пароля", "author": "Автор: Максим Мельников",
        "upper": "Великі літери", "lower": "Малі літери", "digits": "Цифри", "symb": "Спецсимволи",
        "ambig": "Виключити схожі", "at_least": "Мінімум 1 з кожної категорії",
        "hide": "Приховати символи", "btn_gen": "ЗГЕНЕРУВАТИ", "btn_copy": "КОПІЮВАТИ ПАРОЛЬ",
        "btn_save": "ЗБЕРЕГТИ У ФАЙЛ", "btn_open": "ВІДКРИТИ ФАЙЛ", "btn_qr": "QR-КОД ПАРОЛЯ",
        "btn_hist": "ІСТОРІЯ", "btn_upd": "ОНОВИТИ ПРОГРАМУ", "strength": "Складність",
        "radius": "Закруглення кутів", "sys": "Системна", "dark": "Темна", "light": "Світла",
        "copied": "Скопійовано!", "bits": "біт", "qr_title": "QR-код пароля", "hist_title": "Історія",
        "t4": "Менше секунди", "t5": "Кілька секунд", "t6": "Кілька хвилин", "t7": "Години",
        "t8": "Дні", "t10": "Роки", "t12": "Десятиліття", "t14": "Століття", "t15": "Тисячоліття",
        "tt_gen": "Створити новий випадковий пароль", "tt_copy": "Копіювати в буфер обміну",
        "tt_save": "Зберегти пароль у текстовий файл", "tt_open": "Завантажити пароль з файлу",
        "tt_qr": "Створити QR-код для сканування", "tt_hist": "Переглянути останні паролі",
        "tt_upd": "Перевірити наявність оновлень"
    }
}

# =============================================================================
# MAIN APP CLASS / ОСНОВНОЙ КЛАСС / ОСНОВНИЙ КЛАС
# =============================================================================
class SecurePassPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "RU"
        self.current_theme = "System"
        self.history = []
        self._radius_widgets = []
        self.history_window = None
        self.qr_window = None
        self.tooltips = {}

        self.geometry("420x980")
        self.resizable(False, False)

        self._setup_vars()
        self._setup_ui()
        self._load_config()

    def _setup_vars(self):
        """EN: Initialize variables. RU: Инициализация переменных. UA: Ініціалізація змінних."""
        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symb_var = tk.BooleanVar(value=True)
        self.exclude_ambig_var = tk.BooleanVar(value=False)
        self.at_least_one_var = tk.BooleanVar(value=True)
        self.hide_var = tk.BooleanVar(value=False)

    def _setup_ui(self):
        """EN: Build interface. RU: Создание интерфейса. UA: Створення інтерфейсу."""
        self.lbl_title = ctk.CTkLabel(self, text="", font=("Segoe UI", 22, "bold"))
        self.lbl_title.pack(pady=(15, 0))
        self.lbl_author = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "italic"), text_color="gray")
        self.lbl_author.pack()

        self.opt_frame = ctk.CTkFrame(self)
        self.opt_frame.pack(pady=10, padx=20, fill="x")
        self._radius_widgets.append(self.opt_frame)

        self.lbl_len = ctk.CTkLabel(self.opt_frame, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_len.pack(pady=(10, 0))
        self.slider = ctk.CTkSlider(self.opt_frame, from_=4, to=64, command=self._update_len_text)
        self.slider.set(20)
        self.slider.pack(pady=10, padx=20)

        self.cb_upper = self._create_cb(self.upper_var)
        self.cb_lower = self._create_cb(self.lower_var)
        self.cb_digits = self._create_cb(self.digits_var)
        self.cb_symb = self._create_cb(self.symb_var)
        self.cb_ambig = self._create_cb(self.exclude_ambig_var)
        self.cb_at_least = self._create_cb(self.at_least_one_var)
        self.cb_hide = self._create_cb(self.hide_var, command=self._toggle_visibility)

        self.entry_res = ctk.CTkEntry(self, height=45, font=("Consolas", 18), justify="center")
        self.entry_res.pack(pady=10, padx=20, fill="x")
        self._radius_widgets.append(self.entry_res)

        self.strength_bar = ctk.CTkProgressBar(self, height=10)
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=5, padx=40, fill="x")
        
        self.lbl_time_to_crack = ctk.CTkLabel(self, text="", font=("Segoe UI", 12, "bold"))
        self.lbl_time_to_crack.pack()
        
        self.lbl_strength = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_strength.pack()

        self.btn_gen = self._create_btn(self._generate, "btn_gen", "#1f538d", "tt_gen", bold=True)
        self.btn_copy = self._create_btn(self._copy, "btn_copy", "#28a745", "tt_copy")
        self.btn_save = self._create_btn(self._save, "btn_save", "#17a2b8", "tt_save")
        self.btn_open = self._create_btn(self._open, "btn_open", "#17a2b8", "tt_open")
        self.btn_qr = self._create_btn(self._show_qr, "btn_qr", "#6f42c1", "tt_qr")
        self.btn_hist = self._create_btn(self._show_history, "btn_hist", "#6c757d", "tt_hist")
        self.btn_upd = self._create_btn(self._update_app, "btn_upd", "#f39c12", "tt_upd")

        self.lbl_radius = ctk.CTkLabel(self, text="", font=("Segoe UI", 10))
        self.lbl_radius.pack(pady=(5,0))
        self.slider_radius = ctk.CTkSlider(self, from_=0, to=25, height=14, command=self._change_radius)
        self.slider_radius.set(10)
        self.slider_radius.pack(pady=5, padx=60, fill="x")

        self.lbl_stars = ctk.CTkLabel(self, text="★★★★★", font=("Segoe UI", 20), text_color="#FFD700")
        self.lbl_stars.pack(side="bottom", pady=(0, 10))

        self.sw_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sw_frame.pack(side="bottom", fill="x", padx=20, pady=5)
        
        self.lang_sw = ctk.CTkSegmentedButton(self.sw_frame, values=["RU", "EN", "UA"], command=self._on_lang_change)
        self.lang_sw.pack(side="left")
        
        self.theme_sw = ctk.CTkSegmentedButton(self.sw_frame, values=[], command=self._on_theme_change)
        self.theme_sw.pack(side="right")

    def _create_cb(self, var, command=None):
        """EN: Helper for CheckBoxes. RU: Помощник для чекбоксов. UA: Помічник для чекбоксів."""
        cb = ctk.CTkCheckBox(self.opt_frame, text="", variable=var, font=("Segoe UI", 12), 
                             command=lambda: (command() if command else None, self._refresh_strength()))
        cb.pack(anchor="w", padx=35, pady=2)
        return cb

    def _create_btn(self, cmd, key, color, tt_key, bold=False):
        """EN: Helper for Buttons. RU: Помощник для кнопок. UA: Помічник для кнопок."""
        btn = ctk.CTkButton(self, text="", command=cmd, fg_color=color, height=35, 
                             font=("Segoe UI", 13 if bold else 12, "bold" if bold else "normal"))
        btn.pack(pady=3, padx=40, fill="x")
        btn._key = key
        btn._tt_key = tt_key
        self._radius_widgets.append(btn)
        self.tooltips[key] = ToolTip(btn, "")
        btn.bind("<Enter>", lambda e: self.tooltips[key].show_tip())
        btn.bind("<Leave>", lambda e: self.tooltips[key].hide_tip())
        return btn

    def _generate(self):
        """EN: Password generation logic. RU: Логика генерации пароля. UA: Логіка генерації пароля."""
        ambig = "il1Lo0O"
        def get_pool(var, src):
            if not var.get(): return ""
            return "".join(c for c in src if not (self.exclude_ambig_var.get() and c in ambig))

        pools = {'u': get_pool(self.upper_var, string.ascii_uppercase),
                 'l': get_pool(self.lower_var, string.ascii_lowercase),
                 'd': get_pool(self.digits_var, string.digits),
                 's': get_pool(self.symb_var, string.punctuation)}
        
        full_pool = "".join(pools.values())
        if not full_pool:
            sound_error()
            return

        length = int(self.slider.get())
        pwd = []
        if self.at_least_one_var.get():
            for p in pools.values():
                if p: pwd.append(secrets.choice(p))
        
        while len(pwd) < length:
            pwd.append(secrets.choice(full_pool))
            
        secrets.SystemRandom().shuffle(pwd)
        res = "".join(pwd[:length])
        
        self.entry_res.delete(0, tk.END)
        self.entry_res.insert(0, res)
        self.history.append(res)
        if len(self.history) > HISTORY_MAX: self.history.pop(0)
        
        sound_generate()
        self._refresh_strength()

    def _refresh_strength(self):
        """EN: Entropy and strength calculation. RU: Расчет энтропии и сложности. UA: Розрахунок ентропії та складності."""
        pwd = self.entry_res.get()
        L = LANGUAGES[self.current_lang]
        if not pwd:
            self.strength_bar.set(0)
            self.lbl_time_to_crack.configure(text="")
            return
            
        length = len(pwd)
        pool_size = sum([26 if any(c in string.ascii_lowercase for c in pwd) else 0,
                         26 if any(c in string.ascii_uppercase for c in pwd) else 0,
                         10 if any(c in string.digits for c in pwd) else 0,
                         32 if any(c in string.punctuation for c in pwd) else 0])
        
        entropy = length * math.log2(max(pool_size, 1))
        progress = min(entropy / 100, 1.0)
        self.strength_bar.set(progress)
        
        if length <= 4: time_txt, color = L["t4"], "#FF4B4B"
        elif length == 5: time_txt, color = L["t5"], "#FF4B4B"
        elif length == 6: time_txt, color = L["t6"], "#FF4B4B"
        elif length == 7: time_txt, color = L["t7"], "#FF4B4B"
        elif length <= 9: time_txt, color = L["t8"], "#FF4B4B"
        elif length <= 11: time_txt, color = L["t10"], "#FFD700"
        elif length <= 13: time_txt, color = L["t12"], "#FFD700"
        elif length == 14: time_txt, color = L["t14"], "#28A745"
        else: time_txt, color = L["t15"], "#28A745"

        self.strength_bar.configure(progress_color=color)
        self.lbl_time_to_crack.configure(text=time_txt, text_color=color)
        self.lbl_strength.configure(text=f"{L['strength']}: {int(entropy)} {L['bits']}")

    def _copy(self):
        """EN: Copy to clipboard. RU: Копирование в буфер. UA: Копіювання в буфер."""
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return
        self.clipboard_clear()
        self.clipboard_append(pwd)
        sound_copy()
        
        old_text = self.lbl_time_to_crack.cget("text")
        old_color = self.lbl_time_to_crack.cget("text_color")
        self.lbl_time_to_crack.configure(text=LANGUAGES[self.current_lang]["copied"], text_color="#28a745")
        self.after(2000, lambda: self.lbl_time_to_crack.configure(text=old_text, text_color=old_color))

    def _save(self):
        """EN: Save to file. RU: Сохранение в файл. UA: Збереження у файл."""
        pwd = self.entry_res.get()
        if not pwd: 
            sound_error()
            return
        file = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("Text File", "*.txt"), ("Log File", "*.log"), ("All Files", "*.*")])
        if file:
            with open(file, "w", encoding="utf-8") as f: f.write(pwd)
            sound_action()

    def _open(self):
        """EN: Open from file. RU: Открытие из файла. UA: Відкриття з файлу."""
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt *.log *.key"), ("All Files", "*.*")])
        if file:
            with open(file, "r", encoding="utf-8") as f:
                self.entry_res.delete(0, tk.END)
                self.entry_res.insert(0, f.read().strip())
                sound_action()
                self._refresh_strength()

    def _show_history(self):
        """EN: History window. RU: Окно истории. UA: Вікно історії."""
        sound_action()
        L = LANGUAGES[self.current_lang]
        if self.history_window is None or not self.history_window.winfo_exists():
            self.history_window = ctk.CTkToplevel(self)
            self.history_window.title(L["hist_title"])
            self._center_window(self.history_window, 350, 450)
            self.history_window.attributes("-topmost", True)
            txt = ctk.CTkTextbox(self.history_window, font=("Consolas", 14))
            txt.pack(fill="both", expand=True, padx=10, pady=10)
            txt.insert("0.0", "\n".join(self.history[::-1]))
            txt.configure(state="disabled")
        else:
            self.history_window.focus()

    def _show_qr(self):
        """EN: QR Code generation. RU: Генерация QR-кода. UA: Генератція QR-коду."""
        pwd = self.entry_res.get()
        if not pwd:
            sound_error()
            return
        sound_action()
        L = LANGUAGES[self.current_lang]
        if self.qr_window is None or not self.qr_window.winfo_exists():
            self.qr_window = ctk.CTkToplevel(self)
            self.qr_window.title(L["qr_title"])
            self._center_window(self.qr_window, 300, 320)
            self.qr_window.attributes("-topmost", True)
            qr_raw = qrcode.make(pwd).get_image().resize((240, 240), Image.Resampling.LANCZOS)
            img = ctk.CTkImage(light_image=qr_raw, dark_image=qr_raw, size=(240, 240))
            lbl = ctk.CTkLabel(self.qr_window, image=img, text="")
            lbl.pack(pady=20)
        else:
            self.qr_window.focus()

    def _center_window(self, win, w, h):
        """EN: Center top-level windows. RU: Центрирование окон. UA: Центрування вікон."""
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _change_radius(self, val):
        """EN: UI corner radius change. RU: Изменение радиуса углов. UA: Зміна радіусу кутів."""
        r = int(val)
        for w in self._radius_widgets: 
            try: w.configure(corner_radius=r)
            except: pass
        self.lbl_radius.configure(text=f"{LANGUAGES[self.current_lang]['radius']}: {r}")

    def _apply_lang(self, lang):
        """EN: Localization engine. RU: Движок локализации. UA: Двигун локалізації."""
        self.current_lang = lang
        L = LANGUAGES[lang]
        self.title(L["win_title"])
        self.lbl_title.configure(text=L["title"])
        self.lbl_author.configure(text=L["author"])
        self.cb_upper.configure(text=L["upper"])
        self.cb_lower.configure(text=L["lower"])
        self.cb_digits.configure(text=L["digits"])
        self.cb_symb.configure(text=L["symb"])
        self.cb_ambig.configure(text=L["ambig"])
        self.cb_at_least.configure(text=L["at_least"])
        self.cb_hide.configure(text=L["hide"])
        
        for btn in [self.btn_gen, self.btn_copy, self.btn_save, self.btn_open, self.btn_qr, self.btn_hist, self.btn_upd]:
            btn.configure(text=L[btn._key])
            self.tooltips[btn._key].text = L[btn._tt_key]

        self.theme_sw.configure(values=[L["sys"], L["dark"], L["light"]])
        self.lang_sw.set(lang)
        self._update_len_text(self.slider.get())
        self._refresh_strength()

    def _on_lang_change(self, choice):
        self._apply_lang(choice)
        self._save_config()

    def _on_theme_change(self, choice):
        """EN: Theme switcher. RU: Переключатель темы. UA: Перемикач теми."""
        L = LANGUAGES[self.current_lang]
        rmap = {L["sys"]: "System", L["dark"]: "Dark", L["light"]: "Light"}
        self.current_theme = rmap.get(choice, "System")
        ctk.set_appearance_mode(self.current_theme)
        self._save_config()

    def _load_config(self):
        """EN: Config loader. RU: Загрузка конфигурации. UA: Завантаження конфігурації."""
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            self.current_theme = config.get("Settings", "theme", fallback="System")
            self._apply_lang(config.get("Settings", "lang", fallback="RU"))
            ctk.set_appearance_mode(self.current_theme)
        else: 
            self._apply_lang("RU")

    def _save_config(self):
        """EN: Config saver. RU: Сохранение конфигурации. UA: Збереження конфігурації."""
        config = configparser.ConfigParser()
        config["Settings"] = {"lang": self.current_lang, "theme": self.current_theme}
        with open(CONFIG_FILE, "w") as f: 
            config.write(f)

    def _update_app(self): 
        webbrowser.open(UPD_URL)

    def _toggle_visibility(self): 
        self.entry_res.configure(show="*" if self.hide_var.get() else "")

    def _update_len_text(self, val): 
        self.lbl_len.configure(text=f"{LANGUAGES[self.current_lang]['len']}: {int(val)}")

# =============================================================================
# ENTRY POINT / ТОЧКА ВХОДА / ТОЧКА ВХОДУ
# =============================================================================
if __name__ == "__main__":
    app = SecurePassPro()
    app.mainloop()