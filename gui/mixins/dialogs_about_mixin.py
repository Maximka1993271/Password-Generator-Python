"""
Dialogs mixin - About window
Миксин диалогов - Окно "О программе"
Міксин діалогів - Вікно "Про програму"

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import webbrowser
import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from Langs.lang import LANGUAGES
from utils.helpers import apply_window_rounding
from gui.mixins.dialogs_helpers import _set_topmost_false

logger = get_logger("dialogs")


class DialogsAboutMixin:
    """Mixin for about dialog window

    Миксин для окна "О программе"
    Міксин для вікна "Про програму"
    """

    def _show_about(self) -> None:
        """
        Show 'About' program window

        Показывает окно 'О программе'
        Показує вікно 'Про програму'
        """
        if self.about_window and self.about_window.winfo_exists():
            try:
                self.about_window.lift()
                self.about_window.focus_force()
            except tk.TclError:
                self.about_window = None
                self._show_about()
            return

        L = LANGUAGES[self.current_lang]
        wiki_url = "https://github.com/Maximka1993271/Password-Generator-Python/wiki"

        self.about_window = ctk.CTkToplevel(self)
        self.about_window.title(L["btn_about"])
        self.about_window.resizable(False, False)
        self.about_window.transient(self)
        self.about_window.attributes('-topmost', True)
        self.about_window.after(100, lambda: _set_topmost_false(self.about_window))

        try:
            self._center_window_relative_to_parent(self.about_window, 450, 380)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            self.about_window.geometry("450x380")

        try:
            apply_window_rounding(self.about_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Window rounding error / Ошибка скругления окна / Помилка заокруглення вікна: {e}")

        self.about_window.protocol("WM_DELETE_WINDOW", self._close_about)

        main_frame = ctk.CTkFrame(self.about_window, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=30, pady=25)

        try:
            ctk.CTkLabel(main_frame, text="Secure Pass Pro v4.0",
                        font=("Segoe UI", 26, "bold")).pack(pady=(0, 15))
        except tk.TclError as e:
            logger.debug(f"About label error / Ошибка метки 'О программе' / Помилка мітки 'Про програму': {e}")

        try:
            about_label = ctk.CTkLabel(main_frame, text=L["about_text"],
                                        wraplength=380, font=("Segoe UI", 13),
                                        justify="center")
            about_label.pack(pady=10)
        except (tk.TclError, KeyError) as e:
            logger.debug(f"About text error / Ошибка текста 'О программе' / Помилка тексту 'Про програму': {e}")

        # OK button / Кнопка OK / Кнопка OK
        try:
            ctk.CTkButton(main_frame, text=L["ok"], width=120, height=38,
                         command=self._close_about, corner_radius=self.current_radius,
                         fg_color="#2d6a4f", hover_color="#40916c",
                         font=("Segoe UI", 14, "bold")).pack(pady=(20, 15))
        except (tk.TclError, KeyError) as e:
            logger.debug(f"OK button error / Ошибка кнопки OK / Помилка кнопки OK: {e}")

        # Wiki button / Кнопка Wiki / Кнопка Wiki
        try:
            ctk.CTkButton(
                main_frame,
                text=L.get("wiki_link", "Wiki / Вики"),
                width=120,
                height=38,
                corner_radius=self.current_radius,
                fg_color="#1f538d",
                hover_color="#3a6ea5",
                font=("Segoe UI", 14, "bold"),
                command=lambda: webbrowser.open(wiki_url)
            ).pack(pady=(0, 5))
        except (tk.TclError, KeyError) as e:
            logger.debug(f"Wiki button error / Ошибка кнопки Wiki / Помилка кнопки Wiki: {e}")

        try:
            self.about_window.focus_force()
        except tk.TclError:
            pass

    def _close_about(self) -> None:
        """
        Close 'About' window

        Закрывает окно 'О программе'
        Закриває вікно 'Про програму'
        """
        if self.about_window:
            try:
                self.about_window.destroy()
            except tk.TclError as e:
                logger.debug(f"About window destroy error / Ошибка уничтожения окна 'О программе' / Помилка знищення вікна 'Про програму': {e}")
            finally:
                self.about_window = None