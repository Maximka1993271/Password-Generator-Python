"""
Database helper functions for database dialog
Вспомогательные функции базы данных для диалога БД
Допоміжні функції бази даних для діалогу БД

Contains helper functions for password strength calculation, password age, and badge display.
Содержит вспомогательные функции для расчета стойкости пароля, возраста пароля и отображения бейджей.
Містить допоміжні функції для розрахунку стійкості пароля, віку пароля та відображення бейджів.

FIXED: Added full type hints for all functions
"""
from __future__ import annotations

import datetime
import string
import math
from typing import Tuple, Optional, Dict, Any, List


def _calc_strength(password: str) -> Tuple[int, str, str]:
    """
    Calculate password strength.
    Return (score 0-4, label, colour) for a password.
    Pure-Python — no external libs.
    score: 0=empty 1=very_weak 2=weak 3=medium 4=strong

    Вычисляет стойкость пароля.
    Возвращает (оценка 0-4, метка, цвет) для пароля.
    Чистый Python — без внешних библиотек.
    оценка: 0=пусто 1=очень_слабый 2=слабый 3=средний 4=сильный

    Обчислює стійкість пароля.
    Повертає (оцінка 0-4, мітка, колір) для пароля.
    Чистий Python — без зовнішніх бібліотек.
    оцінка: 0=порожньо 1=дуже_слабкий 2=слабкий 3=середній 4=сильний
    """
    if not password:
        return 0, "", "#888888"
    
    p: str = password
    length: int = len(p)
    has_lower: bool = any(c.islower() for c in p)
    has_upper: bool = any(c.isupper() for c in p)
    has_digit: bool = any(c.isdigit() for c in p)
    has_symbol: bool = any(not c.isalnum() for c in p)
    variety: int = sum([has_lower, has_upper, has_digit, has_symbol])

    if length < 6:
        return 1, "Very weak", "#c0392b"
    if length < 8 or variety < 2:
        return 2, "Weak", "#e67e22"
    if length < 12 or variety < 3:
        return 3, "Medium", "#f1c40f"
    return 4, "Strong", "#27ae60"


def _pwd_age_days(date_str: str) -> int:
    """
    Days since date_str (YYYY-MM-DD HH:MM:SS).
    Returns 0 on any error.

    Дней с date_str (ГГГГ-ММ-ДД ЧЧ:ММ:СС).
    Возвращает 0 при любой ошибке.

    Днів з date_str (РРРР-ММ-ДД ГГ:ХХ:СС).
    Повертає 0 при будь-якій помилці.
    """
    if not date_str:
        return 0
    try:
        dt: datetime.datetime = datetime.datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
        return max(0, (datetime.datetime.now() - dt).days)
    except (ValueError, TypeError):
        return 0


def _age_badge(days: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (text, colour) for password-age badge.
    <90 d  → no badge (None, None)
    90-179 → amber warning
    180+   → red danger

    Возвращает (текст, цвет) для бейджа возраста пароля.
    <90 д  → без бейджа (None, None)
    90-179 → янтарное предупреждение
    180+   → красная опасность

    Повертає (текст, колір) для бейджа віку пароля.
    <90 д  → без бейджа (None, None)
    90-179 → бурштинове попередження
    180+   → червона небезпека
    """
    if days < 90:
        return None, None
    if days < 180:
        return f"{days}d", "#c8860a"
    return f"{days}d", "#c0392b"


__all__: List[str] = [
    '_calc_strength',
    '_pwd_age_days',
    '_age_badge',
]