"""
Dialogs mixin - History window
Миксин диалогов - Окно истории
Міксин діалогів - Вікно історії

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import tkinter as tk
import customtkinter as ctk
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.helpers import set_window_icon, apply_window_rounding
from gui.mixins.dialogs_helpers import _setup_window_style, _set_topmost_false, _center_window_relative_to_parent

logger = get_logger("dialogs")


class DialogsHistoryMixin:
    """Mixin for history dialog window

    Миксин для окна истории
    Міксин для вікна історії
    """

    def _show_history(self) -> None:
        """
        Show password history window

        Показывает окно истории паролей
        Показує вікно історії паролів
        """
        if self.history_window and self.history_window.winfo_exists():
            try:
                self.history_window.lift()
                self.history_window.focus_force()
            except tk.TclError:
                self.history_window = None
                self._show_history()
            return

        L = LANGUAGES[self.current_lang]

        self.history_window = ctk.CTkToplevel(self)
        self.history_window.title(L["btn_hist"])
        try:
            set_window_icon(self.history_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Set window icon error / Ошибка установки иконки окна / Помилка встановлення іконки вікна: {e}")

        self.history_window.transient(self)
        self.history_window.attributes('-topmost', True)
        self.history_window.after(100, lambda: _set_topmost_false(self.history_window))

        try:
            _setup_window_style(self.history_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Setup window style error / Ошибка настройки стиля окна / Помилка налаштування стилю вікна: {e}")

        try:
            self._center_window_relative_to_parent(self.history_window, 500, 580)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            self.history_window.geometry("500x580")

        try:
            apply_window_rounding(self.history_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Window rounding error / Ошибка скругления окна / Помилка заокруглення вікна: {e}")

        self.history_window.protocol("WM_DELETE_WINDOW", self._close_history)

        f = ctk.CTkFrame(self.history_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)

        try:
            ctk.CTkLabel(f, text=L["btn_hist"], font=("Segoe UI", 20, "bold")).pack(pady=10)
        except (tk.TclError, KeyError) as e:
            logger.debug(f"Label creation error / Ошибка создания метки / Помилка створення мітки: {e}")

        txt = ctk.CTkTextbox(f, font=("Consolas", 14), corner_radius=self.current_radius)
        txt.pack(fill="both", expand=True, pady=10)

        if not self.history:
            txt.insert("1.0", L["hist_empty"])
        else:
            history_snapshot = list(reversed(self.history))
            try:
                txt.insert("1.0", "\n".join(history_snapshot))
            except (tk.TclError, UnicodeEncodeError) as e:
                logger.error(f"History insert error / Ошибка вставки истории / Помилка вставки історії: {e}")
                txt.insert("1.0", L["hist_empty"])
        txt.configure(state="disabled")

        btn_f = ctk.CTkFrame(f, fg_color="transparent")
        btn_f.pack(fill="x")

        def clear_history() -> None:
            L_local = LANGUAGES[self.current_lang]
            if CTkMessageBox.question(self.history_window, L_local["btn_hist"], L_local.get("db_del_confirm", "Clear history? / Очистить историю? / Очистити історію?")):
                self.history.clear()
                try:
                    txt.configure(state="normal")
                    txt.delete("1.0", "end")
                    txt.insert("1.0", L_local["hist_empty"])
                    txt.configure(state="disabled")
                except tk.TclError as e:
                    logger.error(f"Clear history error / Ошибка очистки истории / Помилка очищення історії: {e}")

        clear_btn = ctk.CTkButton(
            btn_f, text=L["btn_clear_hist"], corner_radius=self.current_radius,
            fg_color="#d13438", command=clear_history
        )
        clear_btn.pack(side="left", padx=5)

        ok_btn = ctk.CTkButton(
            btn_f, text=L["ok"], corner_radius=self.current_radius,
            command=self._close_history
        )
        ok_btn.pack(side="right", padx=5)

        try:
            self.history_window.focus_force()
        except tk.TclError:
            pass

        self.history_textbox = txt

    def _close_history(self) -> None:
        """
        Close history window

        Закрывает окно истории
        Закриває вікно історії
        """
        if self.history_window:
            try:
                self.history_window.destroy()
            except tk.TclError as e:
                logger.debug(f"History window destroy error / Ошибка уничтожения окна истории / Помилка знищення вікна історії: {e}")
            finally:
                self.history_window = None
                self.history_textbox = None

    def _clear_history_textbox(self, textbox: ctk.CTkTextbox) -> None:
        """
        Clear history text field

        Очищает текстовое поле истории
        Очищує текстове поле історії
        """
        L = LANGUAGES[self.current_lang]
        self.history.clear()
        try:
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", L["hist_empty"])
            textbox.configure(state="disabled")
        except (tk.TclError, AttributeError) as e:
            logger.error(f"Clear history error / Ошибка очистки истории / Помилка очищення історії: {e}")
