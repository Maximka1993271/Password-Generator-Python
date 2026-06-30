from __future__ import annotations
# gui/main_window_helpers_ui_mixin.py
"""
Main window helpers ui mixin module for Secure Pass Pro.
Модуль Main window helpers ui mixin для Secure Pass Pro.
Модуль Main window helpers ui mixin для Secure Pass Pro.
"""
"""
Main window helpers ui mixin module for Secure Pass Pro.
Модуль Main window helpers ui mixin для Secure Pass Pro.
Модуль Main window helpers ui mixin для Secure Pass Pro.
"""
"""
Main window helper methods - UI operations
Методы-помощники главного окна - UI операции
Методи-помічники головного вікна - UI операції
"""
import tkinter as tk
import customtkinter as ctk

from utils.helpers import play_sound
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from gui.mixins.dialogs_helpers import _get_colors_for_theme as _get_colors_for_theme_func

logger = get_logger("main_window_helpers")


class MainWindowUIMixin:
    """UI helper methods for SecurePassPro main window

    UI методы-помощники для главного окна SecurePassPro
    UI методи-помічники для головного вікна SecurePassPro
    """

    def _update_len_label(self, val: float) -> None:
        """
        Update length label / Обновляет метку длины / Оновлює мітку довжини
        """
        L = LANGUAGES[self.current_lang]
        try:
            self.lbl_len.configure(text=f"{L['len']}: {int(val)}")
        except (tk.TclError, KeyError, AttributeError) as e:
            logger.debug(f"Update length label error / Ошибка обновления метки длины / Помилка оновлення мітки довжини: {e}")

    def _animate_password_field(self, strength_type: str = "medium") -> None:
        """
        Animate password field border based on strength

        Анимирует границу поля пароля в зависимости от стойкости
        Анімує границю поля пароля залежно від стійкості
        """
        try:
            original_border = self.entry_res.cget("border_color")
        except (tk.TclError, AttributeError):
            original_border = "#2b2b2b"

        if strength_type == "weak":
            neon_colors = ["#FF4444", "#FF6666", "#FF8888", "#FF6666", "#FF4444"]
        elif strength_type == "strong":
            neon_colors = ["#2ECC71", "#55DD88", "#88EEAA", "#55DD88", "#2ECC71"]
        else:
            neon_colors = ["#FFA500", "#FFBB33", "#FFCC66", "#FFBB33", "#FFA500"]

        def pulse_step(step: int = 0) -> None:
            if step < len(neon_colors):
                try:
                    self.entry_res.configure(border_color=neon_colors[step], border_width=3)
                    self._pulse_animation_id = self.after(60, lambda: pulse_step(step + 1))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Animation pulse error / Ошибка анимации / Помилка анімації: {e}")
            else:
                try:
                    self.entry_res.configure(border_color=original_border if original_border else "#2b2b2b", border_width=2)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Border reset error / Ошибка сброса границы / Помилка скидання межі: {e}")
                self._pulse_animation_id = None

        if self._pulse_animation_id:
            try:
                self.after_cancel(self._pulse_animation_id)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Animation cancel error / Ошибка отмены анимации / Помилка скасування анімації: {e}")
        pulse_step()

    def _animate_button(self, btn: ctk.CTkButton) -> None:
        """Animate button click with sound

        Анимирует нажатие кнопки со звуком
        Анімує натискання кнопки зі звуком
        """
        play_sound("click", self.sound_enabled.get())

    def _safe_button_restore(self, old_text: str) -> None:
        """
        Safely restore button text

        Безопасно восстанавливает текст кнопки
        Безпечно відновлює текст кнопки
        """
        try:
            if hasattr(self, 'btn_copy') and self.btn_copy and self.btn_copy.winfo_exists():
                self.btn_copy.configure(text=old_text)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Button restore error / Ошибка восстановления кнопки / Помилка відновлення кнопки: {e}")

    def _toggle_hide(self) -> None:
        """Toggle hide mode / Переключить режим скрытия / Перемкнути режим приховування"""
        self._sync_eye_to_hide_var()

    def _toggle_eye(self) -> None:
        """Toggle eye button / Переключить кнопку глаза / Перемкнути кнопку ока"""
        self.hide_var.set(not self.hide_var.get())
        self._sync_eye_to_hide_var()

    def _sync_eye_to_hide_var(self) -> None:
        """Sync eye button with hide variable

        Синхронизирует кнопку глаза с переменной скрытия
        Синхронізує кнопку ока зі змінною приховування
        """
        hidden = self.hide_var.get()
        L = LANGUAGES[self.current_lang]
        try:
            self.entry_res.configure(show="*" if hidden else "")
            if hidden:
                self.btn_eye.configure(text=L.get("btn_eye_closed", ""))
            else:
                self.btn_eye.configure(text=L.get("btn_eye", ""))
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Eye button sync error / Ошибка синхронизации кнопки глаза / Помилка синхронізації кнопки ока: {e}")

    def _open_update_url(self) -> None:
        """Open GitHub releases page

        Открыть страницу релизов GitHub
        Відкрити сторінку релізів GitHub
        """
        import webbrowser
        UPD_URL = "https://github.com/Maximka1993271/Password-Generator-Python/releases"
        try:
            webbrowser.open(UPD_URL)
        except webbrowser.Error as e:
            logger.error(f"Failed to open URL / Не удалось открыть URL / Не вдалося відкрити URL: {e}")

    def _get_actual_theme(self) -> str:
        """Return actual theme for lock screen

        Возвращает актуальную тему для lock screen
        Повертає актуальну тему для lock screen
        """
        if hasattr(self, 'current_theme'):
            if self.current_theme == "Light":
                return "light"
            elif self.current_theme == "Dark":
                return "dark"
        return "dark"

    def _get_colors_for_theme(self, theme: str) -> dict:
        """Return colors for theme

        Возвращает цвета для темы
        Повертає кольори для теми
        """
        return _get_colors_for_theme_func(theme)
        return {
            "bg": "#1d1e1e",
            "fg": "#FFFFFF",
            "entry_bg": "#2b2b2b",
            "label_text": "#FFFFFF",
            "button_fg": "#1f538d"
        }

    def _center_main_window(self) -> None:
        """Center main window on screen

        Центрирует главное окно на экране
        Центрує головне вікно на екрані
        """
        try:
            self.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (950 // 2)
            y = (self.winfo_screenheight() // 2) - (800 // 2)
            self.geometry(f"950x800+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Main window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            self.geometry("950x800")

    def _center_window_relative_to_parent(self, window, width: int, height: int) -> None:
        """
        Center window relative to parent

        Центрирует окно относительно родителя
        Центрує вікно відносно батька
        """
        try:
            window.update_idletasks()
            parent_x = self.winfo_x()
            parent_y = self.winfo_y()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            if x < 0:
                x = 10
            if y < 30:
                y = 30
            if x + width > screen_width:
                x = screen_width - width - 10
            if y + height > screen_height:
                y = screen_height - height - 10

            window.geometry(f"{width}x{height}+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")

    def _apply_theme_colors(self, actual_theme: str) -> None:
        """Apply theme colors to all widgets

        Применяет цвета темы ко всем виджетам
        Застосовує кольори теми до всіх віджетів
        """
        if actual_theme == "light":
            bg_main, fg_main, entry_bg = "#F3F3F3", "#000000", "#FFFFFF"
            panel_bg, _, checkmark_color = "#F3F3F3", "#d0d0d0", "#1f538d"
        else:
            bg_main, fg_main, entry_bg = "#1d1e1e", "#FFFFFF", "#2b2b2b"
            panel_bg, _, checkmark_color = "#1d1e1e", "#3a3a3a", "#4EC9B0"

        try:
            self.configure(fg_color=bg_main)
            self.left_panel.configure(fg_color=panel_bg)
            self.right_panel.configure(fg_color=panel_bg)
            self.entry_res.configure(fg_color=entry_bg, text_color=fg_main)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Theme color application error / Ошибка применения цветов темы / Помилка застосування кольорів теми: {e}")

        for cb in [self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb, self.cb_ambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat]:
            if cb and cb.winfo_exists():
                try:
                    cb.configure(fg_color=panel_bg, text_color=fg_main, checkmark_color=checkmark_color)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Checkbox color error / Ошибка цвета чекбокса / Помилка кольору чекбокса: {e}")

        try:
            self.lbl_title.configure(text_color=fg_main)
            self.lbl_author.configure(text_color=fg_main)
            self.lbl_len.configure(text_color=fg_main)
            self.lbl_strength.configure(text_color=fg_main)
            self.lbl_strength_text.configure(text_color=fg_main)
            self.lbl_crack.configure(text_color=fg_main)
            self.lbl_menu.configure(text_color=fg_main)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Label color error / Ошибка цвета метки / Помилка кольору мітки: {e}")

        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            if c:
                try:
                    c.configure(bg=bg_main)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Canvas color error / Ошибка цвета canvas / Помилка кольору canvas: {e}")

        self._update_rgb_speed_buttons()
        self._update_rgb_width_buttons()