"""
Dialogs mixin - QR code window
Миксин диалогов - Окно QR кода
Міксин діалогів - Вікно QR коду

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import qrcode
import tkinter as tk
import customtkinter as ctk
from PIL import Image
from utils.logger import get_logger
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.helpers import set_window_icon, apply_window_rounding
from gui.mixins.dialogs_helpers import _setup_window_style, _set_topmost_false, _center_window_relative_to_parent

logger = get_logger("dialogs")


class DialogsQRMixin:
    """Mixin for QR dialog window

    Миксин для окна QR-кода
    Міксин для вікна QR-коду
    """

    def _show_qr(self) -> None:
        """
        Show QR code window for password

        Показывает окно с QR-кодом для пароля
        Показує вікно з QR-кодом для пароля
        """
        pwd = self.entry_res.get()
        if not pwd:
            CTkMessageBox.warning(
                self,
                LANGUAGES[self.current_lang].get("warn", "Warning / Предупреждение / Попередження"),
                LANGUAGES[self.current_lang].get("no_pwd", "No password to show QR code / Нет пароля для показа QR-кода / Немає пароля для показу QR-коду")
            )
            return

        if self.qr_window and self.qr_window.winfo_exists():
            try:
                self.qr_window.lift()
                self.qr_window.focus_force()
            except tk.TclError:
                self.qr_window = None
                self._show_qr()
            return

        L = LANGUAGES[self.current_lang]
        QR_TIMEOUT = 30

        self.qr_window = ctk.CTkToplevel(self)
        self.qr_window.title(L["btn_qr"])
        try:
            set_window_icon(self.qr_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Set window icon error / Ошибка установки иконки окна / Помилка встановлення іконки вікна: {e}")

        self.qr_window.transient(self)
        self.qr_window.attributes("-topmost", True)
        self.qr_window.after(100, lambda: _set_topmost_false(self.qr_window))

        try:
            _setup_window_style(self.qr_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Setup window style error / Ошибка настройки стиля окна / Помилка налаштування стилю вікна: {e}")

        try:
            self._center_window_relative_to_parent(self.qr_window, 380, 500)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            self.qr_window.geometry("380x500")

        try:
            apply_window_rounding(self.qr_window)
        except (AttributeError, OSError) as e:
            logger.debug(f"Window rounding error / Ошибка скругления окна / Помилка заокруглення вікна: {e}")

        self.qr_window.protocol("WM_DELETE_WINDOW", self._close_qr)

        try:
            img = qrcode.make(pwd).resize((280, 280))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(280, 280))
        except (ValueError, OSError, TypeError, ImportError) as e:
            logger.error(f"QR generation error / Ошибка генерации QR-кода / Помилка генерації QR-коду: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"{L.get('err_qr', 'Could not create QR code / Не удалось создать QR-код / Не вдалося створити QR-код')}: {e}"
            )
            self._close_qr()
            return

        f = ctk.CTkFrame(self.qr_window, fg_color="transparent")
        f.pack(expand=True, fill="both", padx=20, pady=20)

        try:
            ctk.CTkLabel(f, text=L["btn_qr"], font=("Segoe UI", 18, "bold")).pack()
        except (tk.TclError, KeyError) as e:
            logger.debug(f"Label creation error / Ошибка создания метки / Помилка створення мітки: {e}")

        disp = ctk.CTkFrame(f, fg_color="white", corner_radius=self.current_radius,
                            border_width=2, border_color="gray")
        disp.pack(pady=10)
        qr_label = ctk.CTkLabel(disp, image=ctk_img, text="")
        qr_label.image = ctk_img
        qr_label.pack(padx=10, pady=10)

        countdown_lbl = ctk.CTkLabel(f, text="", font=("Segoe UI", 12), text_color="#888888")
        countdown_lbl.pack(pady=(0, 4))

        def _tick(s: int) -> None:
            """
            Handle tick.
            Обработать tick.
            Обробити tick.
            """
            if not self.qr_window or not self.qr_window.winfo_exists():
                return
            if s <= 0:
                self._close_qr()
                return
            closes_in_text = L.get("qr_closes_in", "Window closes in / Окно закроется через / Вікно закриється через")
            seconds_text = L.get("seconds_short", "sec / сек / сек")
            try:
                countdown_lbl.configure(text=f"{closes_in_text} {s} {seconds_text}")
            except tk.TclError:
                return
            self.qr_window.after(1000, lambda: _tick(s - 1))

        _tick(QR_TIMEOUT)

        try:
            ctk.CTkButton(f, text=L["ok"], command=self._close_qr,
                         corner_radius=self.current_radius).pack(pady=6)
        except (tk.TclError, KeyError) as e:
            logger.debug(f"Button creation error / Ошибка создания кнопки / Помилка створення кнопки: {e}")

        try:
            self.qr_window.focus_force()
        except tk.TclError:
            pass

    def _close_qr(self) -> None:
        """
        Close QR code window

        Закрывает окно QR-кода
        Закриває вікно QR-коду
        """
        if self.qr_window:
            try:
                self.qr_window.destroy()
            except tk.TclError as e:
                logger.debug(f"QR window destroy error / Ошибка уничтожения окна QR-кода / Помилка знищення вікна QR-коду: {e}")
            finally:
                self.qr_window = None