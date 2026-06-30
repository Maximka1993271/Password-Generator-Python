from __future__ import annotations
# master_mixin_base.py
"""
Master mixin base module for Secure Pass Pro.
Модуль Master mixin base для Secure Pass Pro.
Модуль Master mixin base для Secure Pass Pro.
"""
"""
Master mixin base module for Secure Pass Pro.
Модуль Master mixin base для Secure Pass Pro.
Модуль Master mixin base для Secure Pass Pro.
"""
"""
Master password mixin - Base constants and helper functions
Миксин мастер-пароля - Базовые константы и вспомогательные функции
Міксин майстер-пароля - Базові константи та допоміжні функції
"""
import os
import tkinter as tk
from typing import Optional
import customtkinter as ctk
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from utils.paths import get_config_dir

logger = get_logger("master_mixin")

# Path to master password file / Путь к файлу мастер-пароля / Шлях до файлу майстер-пароля
CONFIG_DIR = get_config_dir()
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")


class MasterPasswordError(Exception):
    """Custom exception for master password operations

    Пользовательское исключение для операций с мастер-паролем
    Користувацький виняток для операцій з майстер-паролем
    """
    pass


# FIXED #C3, #H5: Create a custom input dialog function that doesn't depend on non-existent CTkInputDialog
# Исправлено #C3, #H5: Создаём функцию пользовательского диалога ввода, которая не зависит от несуществующего CTkInputDialog
# Виправлено #C3, #H5: Створюємо функцію власного діалогу введення, яка не залежить від неіснуючого CTkInputDialog

def _custom_input_dialog(parent, title: str, prompt: str, show: str = "", theme: str = "dark", lang: str = "RU") -> Optional[str]:
    """
    Custom input dialog that works without CTkInputDialog

    Пользовательский диалог ввода, работающий без CTkInputDialog
    Власний діалог введення, що працює без CTkInputDialog
    """
    L = LANGUAGES.get(lang, LANGUAGES["RU"])
    result = {"value": None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("400x220")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.lift()
    dialog.focus_force()
    dialog.after(100, lambda: dialog.attributes("-topmost", False) if dialog and dialog.winfo_exists() else None)
    dialog.attributes("-topmost", True)

    # Center window / Центрируем окно / Центруємо вікно
    try:
        dialog.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - 400) // 2
        y = parent_y + (parent_height - 220) // 2
        dialog.geometry(f"400x220+{x}+{y}")
    except (tk.TclError, AttributeError, RuntimeError) as e:
        logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")

    # Colors based on theme / Цвета в зависимости от теми / Кольори залежно від теми
    if theme == "light":
        bg_color = "#F3F3F3"
        fg_color = "#000000"
        entry_bg = "#FFFFFF"
    else:
        bg_color = "#1d1e1e"
        fg_color = "#FFFFFF"
        entry_bg = "#2b2b2b"

    dialog.configure(fg_color=bg_color)

    main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)

    # Icon (empty) / Иконка (пустая) / Іконка (порожня)
    ctk.CTkLabel(main_frame, text="", font=("Segoe UI", 32), text_color="#4EC9B0").pack(pady=(0, 5))

    # Prompt label / Метка с вопросом / Мітка з питанням
    ctk.CTkLabel(main_frame, text=prompt, font=("Segoe UI", 13), text_color=fg_color).pack(pady=(0, 10))

    # Entry field / Поле ввода / Поле введення
    entry = ctk.CTkEntry(main_frame, width=300, height=38, show=show, fg_color=entry_bg, text_color=fg_color)
    entry.pack(pady=(0, 15))
    entry.focus_set()

    # Button frame / Фрейм кнопок / Фрейм кнопок
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack()

    def on_ok():
        """
        Handle the ok event.
        Обработчик ok.
        Обробник ok.
        """
        result["value"] = entry.get()
        dialog.destroy()

    def on_cancel():
        """
        Handle the cancel event.
        Обработчик cancel.
        Обробник cancel.
        """
        dialog.destroy()

    ctk.CTkButton(btn_frame, text=L.get("ok", "OK / Хорошо / Гаразд"), width=100, height=34, command=on_ok,
                  fg_color="#2d6a4f", corner_radius=17, font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
    ctk.CTkButton(btn_frame, text=L.get("cancel", "Cancel / Отмена / Скасувати"), width=100, height=34, command=on_cancel,
                  fg_color="#8b0000", corner_radius=17, font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

    entry.bind("<Return>", lambda e: on_ok())
    entry.bind("<Escape>", lambda e: on_cancel())

    dialog.after(100, lambda: dialog.attributes("-topmost", False))

    parent.wait_window(dialog)
    return result["value"]