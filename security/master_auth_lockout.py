"""
Master password authentication - Lockout management
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
import time
from datetime import datetime
from typing import Tuple

from security.master_auth_constants import LOCKOUT_TIMES, LOCKOUT_FILE
from security.master_auth_helpers import _secure_write, _secure_read, _get_device_fingerprint, _get_ip_address

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_lockout_state(cls) -> None:
    """Save lockout state / Сохранить состояние блокировки / Зберегти стан блокування"""
    try:
        state = {
            "attempt_count": cls._attempt_count,
            "last_attempt_time": cls._last_attempt_time,
            "lockout_until": cls._lockout_until,
            "is_permanently_locked": cls._is_permanently_locked,
            "last_update": datetime.now().isoformat()
        }
        _secure_write(LOCKOUT_FILE, json.dumps(state, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save lockout state / Ошибка сохранения состояния блокировки / Помилка збереження стану блокування: {e}")


def _load_lockout_state(cls) -> None:
    """Load lockout state / Загрузить состояние блокировки / Завантажити стан блокування"""
    if not os.path.exists(LOCKOUT_FILE):
        return

    try:
        content = _secure_read(LOCKOUT_FILE)
        if content:
            state = json.loads(content.decode('utf-8'))

            cls._attempt_count = state.get("attempt_count", 0)
            cls._last_attempt_time = state.get("last_attempt_time", 0)
            cls._lockout_until = state.get("lockout_until", 0)
            cls._is_permanently_locked = state.get("is_permanently_locked", False)

            if cls._lockout_until > 0 and cls._lockout_until <= time.time():
                _reset_attempts(cls)

            logger.debug("Lockout state loaded / Состояние блокировки загружено / Стан блокування завантажено")
    except (json.JSONDecodeError, OSError, IOError, KeyError, UnicodeDecodeError) as e:
        logger.debug(f"Failed to load lockout state / Ошибка загрузки состояния блокировки / Помилка завантаження стану блокування: {e}")


def _get_lockout_delay(cls, attempts: int) -> int:
    """Get lockout delay for given attempt count
    Получить задержку блокировки для данного количества попыток
    Отримати затримку блокування для даної кількості спроб"""
    return LOCKOUT_TIMES.get(attempts, LOCKOUT_TIMES[min(attempts, max(LOCKOUT_TIMES.keys()))])


def _apply_rate_limit(cls) -> Tuple[bool, int]:
    """Apply rate limiting based on attempts
    Применить ограничение частоты на основе попыток
    Застосувати обмеження частоти на основі спроб"""
    current_time = time.time()
    max_attempts = cls.get_max_attempts()

    if cls._is_permanently_locked:
        return False, -1

    if cls._lockout_until > current_time:
        return False, int(cls._lockout_until - current_time)

    if current_time - cls._last_attempt_time > 600:
        cls._attempt_count = 0
        cls._lockout_until = 0
        _save_lockout_state(cls)

    return True, 0


def _record_failed_attempt(cls, source: str = "unknown") -> int:
    """Record a failed authentication attempt
    Записать неудачную попытку аутентификации
    Записати невдалу спробу аутентифікації"""
    max_attempts = cls.get_max_attempts()

    cls._attempt_count += 1
    cls._last_attempt_time = time.time()

    cls._log_audit_event("failed_attempt", {
        "attempts": cls._attempt_count,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "device_fingerprint": _get_device_fingerprint(),
        "ip_address": _get_ip_address()
    })

    if cls._attempt_count >= max_attempts:
        cls._is_permanently_locked = True
        _save_lockout_state(cls)
        logger.warning(f"Permanent lockout triggered after {cls._attempt_count} attempts / Постоянная блокировка после {cls._attempt_count} попыток / Постійне блокування після {cls._attempt_count} спроб")
        return -1

    delay = _get_lockout_delay(cls, cls._attempt_count)
    if delay > 0:
        cls._lockout_until = cls._last_attempt_time + delay
        logger.warning(f"Lockout for {delay} seconds after {cls._attempt_count} attempts / Блокировка на {delay} секунд после {cls._attempt_count} попыток / Блокування на {delay} секунд після {cls._attempt_count} спроб")

    _save_lockout_state(cls)
    return delay


def _reset_attempts(cls) -> None:
    """Reset all attempt counters
    Сбросить все счетчики попыток
    Скинути всі лічильники спроб"""
    cls._attempt_count = 0
    cls._lockout_until = 0
    cls._is_permanently_locked = False
    cls._last_attempt_time = 0
    _save_lockout_state(cls)
    logger.debug("Attempts reset / Счётчики попыток сброшены / Лічильники спроб скинуто")


def get_remaining_lockout_time(cls) -> int:
    """Get remaining lockout time in seconds
    Получить оставшееся время блокировки в секундах
    Отримати час блокування в секундах"""
    if cls._is_permanently_locked:
        return -1
    if cls._lockout_until <= time.time():
        return 0
    return int(cls._lockout_until - time.time())


def get_attempts_remaining(cls) -> int:
    """Get number of remaining attempts before lockout
    Получить количество оставшихся попыток до блокировки
    Отримати кількість спроб до блокування"""
    max_attempts = cls.get_max_attempts()
    if cls._is_permanently_locked:
        return 0
    if cls._attempt_count >= max_attempts:
        return 0
    return max_attempts - cls._attempt_count


def is_permanently_locked(cls) -> bool:
    """Check if permanently locked
    Проверить, заблокирована ли программа навсегда
    Перевірити, чи заблоковано програму назавжди"""
    return cls._is_permanently_locked


def get_lockout_info(cls) -> dict:
    """Get detailed lockout information
    Получить подробную информацию о блокировке
    Отримати детальну інформацію про блокування"""
    remaining = get_remaining_lockout_time(cls)
    max_attempts = cls.get_max_attempts()
    return {
        'attempts': cls._attempt_count,
        'max_attempts': max_attempts,
        'remaining_attempts': get_attempts_remaining(cls),
        'lockout_seconds': remaining if remaining > 0 else 0,
        'is_locked': remaining > 0,
        'is_permanently_locked': cls._is_permanently_locked
    }


def reset_lockout(cls) -> bool:
    """Reset lockout state (admin only)
    Сбросить состояние блокировки (только администратор)
    Скинути стан блокування (тільки адміністратор)"""
    if not cls.is_permanently_locked() and get_remaining_lockout_time(cls) == 0:
        return True

    _reset_attempts(cls)
    cls._log_audit_event("lockout_reset", {"source": "admin"})
    logger.info("Lockout state reset / Состояние блокировки сброшено / Стан блокування скинуто")
    return True