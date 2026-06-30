"""
RGB effects mixin for SecurePassPro

Миксин RGB эффектов для SecurePassPro
Міксин RGB ефектів для SecurePassPro

FIXED #56: Added proper cleanup on window destroy
Исправлено #56: Добавлена правильная очистка при уничтожении окна
Виправлено #56: Додано правильне очищення при знищенні вікна
"""
from __future__ import annotations
import tkinter as tk
import math
import ctypes
import weakref
from utils.helpers import is_windows
from utils.logger import get_logger

logger = get_logger("rgb_mixin")


class RGBMixin:
    """Mixin class for RGB border animation and titlebar coloring
    Класс-миксин для RGB анимации границы и раскраски заголовка окна
    Клас-міксин для RGB анімації межі та розфарбування заголовка вікна"""

    # Animation speed (delay between frames in ms)
    # Скорость анимации (задержка между кадрами в мс)
    # Швидкість анімації (затримка між кадрами в мс)
    RGB_SPEEDS = {
        "slow": 50,      # slow / медленная / повільна
        "normal": 30,    # normal / нормальная / нормальна
        "fast": 15,      # fast / быстрая / швидка
    }

    # RGB border thickness in pixels
    # Толщина RGB подсветки в пикселях
    # Товщина RGB підсвітки в пікселях
    RGB_WIDTHS = {
        "thin": 1,       # thin / тонкая / тонка
        "normal": 3,     # normal / средняя / середня
        "thick": 5,      # thick / толстая / товста
    }

    def _create_rgb_canvases(self) -> None:
        """Create canvases for all 4 sides with initial thickness of 3px
        Создаёт canvas для всех 4 сторон с начальной толщиной 3px
        Створює canvas для всіх 4 сторін з початковою товщиною 3px"""
        self._rgb_c_top = tk.Canvas(self, height=3, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_bottom = tk.Canvas(self, height=3, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_left = tk.Canvas(self, width=3, bg="#1d1e1e", highlightthickness=0)
        self._rgb_c_right = tk.Canvas(self, width=3, bg="#1d1e1e", highlightthickness=0)
        for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
            c.place_forget()

        # FIXED #56: Track animation state for cleanup
        # Исправлено #56: Отслеживаем состояние анимации для очистки
        # Виправлено #56: Відстежуємо стан анімації для очищення
        self._rgb_anim_id = None
        self._rgb_active = False

    def _update_rgb_width(self) -> None:
        """Update RGB border thickness / Обновить толщину RGB подсветки / Оновити товщину RGB підсвітки"""
        width_setting = getattr(self, 'rgb_width_setting', 'normal')
        width = self.RGB_WIDTHS.get(width_setting, 3)

        if self._rgb_c_top:
            try:
                self._rgb_c_top.configure(height=width)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Update top width error / Ошибка обновления верхней толщины / Помилка оновлення верхньої товщини: {e}")
        if self._rgb_c_bottom:
            try:
                self._rgb_c_bottom.configure(height=width)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Update bottom width error / Ошибка обновления нижней толщины / Помилка оновлення нижньої товщини: {e}")
        if self._rgb_c_left:
            try:
                self._rgb_c_left.configure(width=width)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Update left width error / Ошибка обновления левой толщины / Помилка оновлення лівої товщини: {e}")
        if self._rgb_c_right:
            try:
                self._rgb_c_right.configure(width=width)
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Update right width error / Ошибка обновления правой толщины / Помилка оновлення правої товщини: {e}")

    def _rgb_color(self, phase_offset: float) -> str:
        """
        Handle rgb color.
        Обработать rgb color.
        Обробити rgb color.
        """
        f = self._rgb_t + phase_offset
        r = int((math.sin(f) + 1) / 2 * 255)
        g = int((math.sin(f + 2.1) + 1) / 2 * 255)
        b = int((math.sin(f + 4.2) + 1) / 2 * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _set_titlebar_color(self, hex_color: str) -> None:
        """
        Handle set titlebar color.
        Обработать set titlebar color.
        Обробити set titlebar color.
        """
        if not is_windows():
            return
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            colorref = r | (g << 8) | (b << 16)
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                DWMWA_CAPTION_COLOR = 35
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(colorref)), ctypes.sizeof(ctypes.c_int(colorref)))
        except (AttributeError, OSError, TypeError, ValueError, RuntimeError) as e:
            logger.debug(f"Titlebar color error / Ошибка цвета заголовка / Помилка кольору заголовка: {e}")

    def _reset_titlebar_color(self) -> None:
        """
        Handle reset titlebar color.
        Обработать reset titlebar color.
        Обробити reset titlebar color.
        """
        if not is_windows():
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if hwnd:
                DWMWA_CAPTION_COLOR = 35
                DWMWA_COLOR_DEFAULT = 0xFFFFFFFF
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(ctypes.c_int(DWMWA_COLOR_DEFAULT)), ctypes.sizeof(ctypes.c_int(DWMWA_COLOR_DEFAULT)))
        except (AttributeError, OSError, TypeError, ValueError, RuntimeError) as e:
            logger.debug(f"Titlebar reset error / Ошибка сброса заголовка / Помилка скидання заголовка: {e}")

    def _get_rgb_speed(self) -> int:
        """
        Handle get rgb speed.
        Обработать get rgb speed.
        Обробити get rgb speed.
        """
        speed_setting = getattr(self, 'rgb_speed_setting', 'normal')
        return self.RGB_SPEEDS.get(speed_setting, 30)

    def _animate_rgb(self) -> None:
        """Animate RGB border - safe version with existence check
        Анимирует RGB границу - безопасная версия с проверкой существования
        Анімує RGB границю - безпечна версія з перевіркою існування"""
        # FIXED #56: Check if window still exists and animation is active
        # Исправлено #56: Проверяем, существует ли окно и активна ли анимация
        # Виправлено #56: Перевіряємо, чи існує вікно та чи активна анімація
        if not self._rgb_active:
            return

        try:
            # Check if window still exists
            if not self.winfo_exists():
                logger.debug("RGB animation stopped - window destroyed / RGB анимация остановлена - окно уничтожено / RGB анімацію зупинено - вікно знищено")
                self._rgb_active = False
                self._rgb_anim_id = None
                return

            if not self.rgb_enabled.get():
                self._rgb_active = False
                self._rgb_anim_id = None
                return

            if self._rgb_c_top:
                self._rgb_c_top.configure(bg=self._rgb_color(0.0))
            if self._rgb_c_right:
                self._rgb_c_right.configure(bg=self._rgb_color(0.8))
            if self._rgb_c_bottom:
                self._rgb_c_bottom.configure(bg=self._rgb_color(1.6))
            if self._rgb_c_left:
                self._rgb_c_left.configure(bg=self._rgb_color(2.4))
            self._set_titlebar_color(self._rgb_color(3.2))
            self._rgb_t = (self._rgb_t + 0.08) % (2 * math.pi)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"RGB animation frame error / Ошибка кадра RGB анимации / Помилка кадру RGB анімації: {e}")
            self._rgb_active = False
            self._rgb_anim_id = None
            return

        if self._rgb_anim_id:
            try:
                self.after_cancel(self._rgb_anim_id)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Cancel animation error / Ошибка отмены анимации / Помилка скасування анімації: {e}")

        speed = self._get_rgb_speed()
        self._rgb_anim_id = self.after(speed, self._animate_rgb)

    def _start_rgb(self) -> None:
        """Start RGB animation / Запустить RGB анимацию / Запустити RGB анімацію"""
        # FIXED #56: Reset animation state before starting
        # Исправлено #56: Сбрасываем состояние анимации перед запуском
        # Виправлено #56: Скидаємо стан анімації перед запуском
        if not self.rgb_enabled.get():
            return

        try:
            # Stop any existing animation first
            self._stop_rgb()

            self._update_rgb_width()
            self._rgb_active = True
            self._rgb_t = 0.0

            if self._rgb_c_top:
                self._rgb_c_top.place(relx=0, rely=0, relwidth=1)
                self._rgb_c_bottom.place(relx=0, rely=1, anchor="sw", relwidth=1)
                self._rgb_c_left.place(relx=0, rely=0, relheight=1)
                self._rgb_c_right.place(relx=1, rely=0, anchor="ne", relheight=1)

            self._animate_rgb()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Start RGB error / Ошибка запуска RGB / Помилка запуску RGB: {e}")
            self._rgb_active = False

    def _stop_rgb(self) -> None:
        """Stop RGB animation / Остановить RGB анимацию / Зупинити RGB анімацію"""
        # FIXED #56: Properly stop animation and clean up
        # Исправлено #56: Корректно останавливаем анимацию и очищаем
        # Виправлено #56: Коректно зупиняємо анімацію та очищуємо
        self._rgb_active = False

        if self._rgb_anim_id:
            try:
                self.after_cancel(self._rgb_anim_id)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Cancel RGB animation error / Ошибка отмены RGB анимации / Помилка скасування RGB анімації: {e}")
            self._rgb_anim_id = None

        try:
            for c in (self._rgb_c_top, self._rgb_c_bottom, self._rgb_c_left, self._rgb_c_right):
                if c and c.winfo_exists():
                    c.place_forget()
            self._reset_titlebar_color()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Stop RGB cleanup error / Ошибка очистки при остановке RGB / Помилка очищення при зупинці RGB: {e}")

    def _set_rgb(self, state: bool) -> None:
        """Enable/disable RGB border / Включить/выключить RGB подсветку / Увімкнути/вимкнути RGB підсвітку"""
        if self.rgb_enabled.get() == state:
            return
        self.rgb_enabled.set(state)
        if state:
            self._start_rgb()
        else:
            self._stop_rgb()
        self._update_rgb_buttons()
        try:
            self.config.set("RGB", state)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.debug(f"Save RGB setting error / Ошибка сохранения настройки RGB / Помилка збереження налаштування RGB: {e}")

    def _set_rgb_speed(self, speed: str) -> None:
        """Set RGB animation speed / Установить скорость RGB анимации / Встановити швидкість RGB анімації"""
        if speed not in self.RGB_SPEEDS:
            return
        self.rgb_speed_setting = speed
        rgb_was_on = self.rgb_enabled.get()
        if rgb_was_on:
            self._stop_rgb()
            self._start_rgb()
        try:
            self.config.set("RGB_SPEED", speed)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.debug(f"Save RGB speed error / Ошибка сохранения скорости RGB / Помилка збереження швидкості RGB: {e}")
        self._update_rgb_speed_buttons()

    def _set_rgb_width(self, width: str) -> None:
        """Set RGB border thickness / Установить толщину RGB подсветки / Встановити товщину RGB підсвітки"""
        if width not in self.RGB_WIDTHS:
            return
        self.rgb_width_setting = width
        self._update_rgb_width()
        if self.rgb_enabled.get():
            self._stop_rgb()
            self._start_rgb()
        try:
            self.config.set("RGB_WIDTH", width)
        except (KeyError, ValueError, OSError, AttributeError) as e:
            logger.debug(f"Save RGB width error / Ошибка сохранения толщины RGB / Помилка збереження товщини RGB: {e}")
        self._update_rgb_width_buttons()

    def _update_rgb_speed_buttons(self) -> None:
        """Update RGB speed button states / Обновить состояние кнопок скорости RGB / Оновити стан кнопок швидкості RGB"""
        current_speed = getattr(self, 'rgb_speed_setting', 'normal')
        if hasattr(self, '_rgb_speed_btn_slow') and self._rgb_speed_btn_slow:
            try:
                self._rgb_speed_btn_slow.configure(
                    fg_color="#2d6a4f" if current_speed == "slow" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Speed button update error / Ошибка обновления кнопки скорости / Помилка оновлення кнопки швидкості: {e}")
        if hasattr(self, '_rgb_speed_btn_normal') and self._rgb_speed_btn_normal:
            try:
                self._rgb_speed_btn_normal.configure(
                    fg_color="#2d6a4f" if current_speed == "normal" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Speed button update error / Ошибка обновления кнопки скорости / Помилка оновлення кнопки швидкості: {e}")
        if hasattr(self, '_rgb_speed_btn_fast') and self._rgb_speed_btn_fast:
            try:
                self._rgb_speed_btn_fast.configure(
                    fg_color="#2d6a4f" if current_speed == "fast" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Speed button update error / Ошибка обновления кнопки скорости / Помилка оновлення кнопки швидкості: {e}")

    def _update_rgb_width_buttons(self) -> None:
        """Update RGB thickness button states / Обновить состояние кнопок толщины RGB / Оновити стан кнопок товщини RGB"""
        current_width = getattr(self, 'rgb_width_setting', 'normal')
        if hasattr(self, '_rgb_width_btn_thin') and self._rgb_width_btn_thin:
            try:
                self._rgb_width_btn_thin.configure(
                    fg_color="#2d6a4f" if current_width == "thin" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Width button update error / Ошибка обновления кнопки толщины / Помилка оновлення кнопки товщини: {e}")
        if hasattr(self, '_rgb_width_btn_normal') and self._rgb_width_btn_normal:
            try:
                self._rgb_width_btn_normal.configure(
                    fg_color="#2d6a4f" if current_width == "normal" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Width button update error / Ошибка обновления кнопки толщины / Помилка оновлення кнопки товщини: {e}")
        if hasattr(self, '_rgb_width_btn_thick') and self._rgb_width_btn_thick:
            try:
                self._rgb_width_btn_thick.configure(
                    fg_color="#2d6a4f" if current_width == "thick" else "#4b4b4b"
                )
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Width button update error / Ошибка обновления кнопки толщины / Помилка оновлення кнопки товщини: {e}")

    def _update_rgb_buttons(self) -> None:
        """Update On/Off RGB button states / Обновить состояние кнопок Вкл/Выкл RGB подсветки / Оновити стан кнопок Увімк/Вимк RGB підсвітки"""
        is_on = self.rgb_enabled.get()
        if self._rgb_on_btn_ref and self._rgb_on_btn_ref.winfo_exists():
            try:
                self._rgb_on_btn_ref.configure(fg_color="#2d6a4f" if is_on else "#4b4b4b")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"RGB on button update error / Ошибка обновления кнопки Вкл RGB / Помилка оновлення кнопки Увімк RGB: {e}")
        if self._rgb_off_btn_ref and self._rgb_off_btn_ref.winfo_exists():
            try:
                self._rgb_off_btn_ref.configure(fg_color="#8b0000" if not is_on else "#4b4b4b")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"RGB off button update error / Ошибка обновления кнопки Выкл RGB / Помилка оновлення кнопки Вимк RGB: {e}")