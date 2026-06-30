"""
Main window helper methods - Data operations
Методы-помощники главного окна - Операции с данными
Методи-помічники головного вікна - Операції з даними

FIXED: Added full type hints for all methods
FIXED: Syntax error in docstring
"""
from __future__ import annotations

import os
import re
import tkinter as tk
import json
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

from storage.database import PasswordDB
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from core.generator import StrengthCalculator

logger = get_logger("main_window_helpers_data")


class MainWindowDataMixin:
    """Data helper methods for SecurePassPro main window."""

    def _update_strength_meter(self, password: str) -> None:
        """
        Update password strength meter with 3-language support (RU, EN, UA).
        Обновляет индикатор стойкости пароля с поддержкой 3 языков.
        Оновлює індикатор стійкості пароля з підтримкою 3 мов.
        """
        if not password:
            try:
                self.lbl_strength_text.configure(text="")
                self.lbl_strength.configure(text="")
                self.lbl_crack.configure(text="")
                self.lbl_stars_top.configure(text="")
            except (tk.TclError, AttributeError, RuntimeError):
                pass
            return

        L: Dict[str, str] = LANGUAGES[self.current_lang]
        try:
            stats: Dict[str, Any] = self.strength_calc.calculate(password)
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Strength calculation error / Ошибка расчета стойкости / Помилка розрахунку стійкості: {e}")
            return

        try:
            self.lbl_strength.configure(text=L["strength"].format(stats['combinations']))
        except (tk.TclError, KeyError, AttributeError) as e:
            logger.debug(f"Strength label update error: {e}")

        # Determine strength level and display
        strength_level: str = stats.get('strength_level', 'medium')
        entropy_bits: float = stats.get('entropy_bits', 0.0)

        if strength_level == 'weak':
            stars_display: str = "Weak"
            stars_color: str = "#FF4C4C"
            st_text: str = L.get("st_low", "Weak password / Слабый пароль / Слабкий пароль")
            strength_display: str = L.get("strength_weak", "Weak / Слабый / Слабкий")
        elif strength_level == 'medium':
            if entropy_bits < 60:
                stars_display = "Medium"
                stars_color = "#FFA500"
                strength_display = L.get("strength_medium", "Medium / Средний / Середній")
            else:
                stars_display = "Medium+"
                stars_color = "#FFD700"
                strength_display = L.get("strength_medium_plus", "Medium+ / Средний+ / Середній+")
            st_text = L.get("st_mid", "Medium password / Средний пароль / Середній пароль")
        else:
            stars_display = L.get("strength_strong", "Strong / Надёжный / Надійний")
            stars_color = "#2ECC71"
            st_text = L.get("st_high", "Strong password / Надёжный пароль / Надійний пароль")
            strength_display = stars_display

        try:
            self.lbl_stars_top.configure(text=strength_display, text_color=stars_color)
            self.lbl_strength_text.configure(text=st_text, text_color=stars_color)
            self.lbl_crack.configure(
                text=L["crack_time"].format(L[stats['crack_time_label']]),
                text_color=stars_color
            )
        except (tk.TclError, KeyError, AttributeError) as e:
            logger.debug(f"Strength indicators update error: {e}")

        self._animate_password_field(strength_level)

    def _check_duplicate_password(self, password: str) -> bool:
        """
        Check if password already exists in the database.
        Проверяет, существует ли уже такой пароль в базе.
        Перевіряє, чи вже існує такий пароль у базі.
        """
        try:
            import sqlite3
            all_passwords: List[Dict[str, Any]] = PasswordDB.get_all()
            for record in all_passwords:
                if record.get("password") == password:
                    return True
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError) as e:
            logger.error(f"Duplicate check error / Ошибка проверки дубликата / Помилка перевірки дубліката: {e}")
        return False

    def _sanitize_import_content(self, content: str) -> str:
        """
        Sanitize imported content.
        Removes potentially dangerous characters.

        Санитизация импортируемого содержимого.
        Удаляет потенциально опасные символы.

        Санітизація імпортованого вмісту.
        Видаляє потенційно небезпечні символи.
        """
        if not content:
            return ""

        sanitized: str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
        sanitized = re.sub(r'[\u200B-\u200D\uFEFF]', '', sanitized)

        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]

        return sanitized

    def _validate_export_path(self, path: str) -> bool:
        """
        Check if export path is safe.
        Проверяет, что путь для экспорта безопасен.
        Перевіряє, що шлях для експорту безпечний.
        """
        try:
            directory: str = os.path.dirname(path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            test_file: str = path + ".test"
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)

            return True
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Export path validation error / Ошибка валидации пути экспорта / Помилка валідації шляху експорту: {e}")
            return False

    def _verify_pdf(self, path: str) -> bool:
        """
        Verify PDF file integrity.
        Проверяет целостность PDF файла.
        Перевіряє цілісність PDF файлу.
        """
        try:
            with open(path, "rb") as f:
                header: bytes = f.read(5)
                return header == b"%PDF-"
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"PDF verification error / Ошибка проверки PDF / Помилка перевірки PDF: {e}")
            return False


__all__: List[str] = [
    'MainWindowDataMixin',
]