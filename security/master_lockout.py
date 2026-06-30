"""
Master password lockout management module

Модуль управления блокировкой мастер-пароля
Модуль керування блокуванням майстер-пароля

This module contains lockout-related functionality:
- Rate limiting
- Lockout state management
- Attempt tracking
- Lockout time calculations

Этот модуль содержит функциональность блокировки:
- Ограничение частоты попыток
- Управление состоянием блокировки
- Отслеживание попыток
- Расчёт времени блокировки

Цей модуль містить функціональність блокування:
- Обмеження частоти спроб
- Керування станом блокування
- Відстеження спроб
- Розрахунок часу блокування
"""
from __future__ import annotations

import os
import sys
import json
import time
import threading
import ctypes
import tempfile
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SECUREPASS_L = os.path.join(_BASE_DIR, ".securepass", "data")
CONFIG_DIR = _SECUREPASS_L if os.path.exists(_SECUREPASS_L) else os.path.join(_BASE_DIR, "data")
if not os.path.exists(CONFIG_DIR):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            import ctypes as _ct2, platform as _pl2
            if _pl2.system() == "Windows":
                _ct2.windll.kernel32.SetFileAttributesW(CONFIG_DIR, 0x02)
        except (AttributeError, OSError, TypeError, ImportError):
            pass
    except (OSError, PermissionError):
        pass
LOCKOUT_FILE = os.path.join(CONFIG_DIR, "lockout.json")
# =============================================================

# ==================== UNIFIED LOGGER ====================
from utils.logger import get_logger

logger = get_logger("master_lockout")

# ==================== CONSTANTS ====================
DEFAULT_MAX_ATTEMPTS = 5
MAX_ATTEMPTS = int(int(__import__('core.config_manager', fromlist=['ConfigManager']).ConfigManager.instance().get('MAX_ATTEMPTS', DEFAULT_MAX_ATTEMPTS)))
if MAX_ATTEMPTS < 3:
    MAX_ATTEMPTS = 3
elif MAX_ATTEMPTS > 10:
    MAX_ATTEMPTS = 10

# Lockout times in seconds
# Время блокировки в секундах
# Час блокування в секундах
LOCKOUT_TIMES = {
    1: 2,
    2: 3,
    3: 10,
    4: 30,
    5: 60,
    6: 120,
    7: 300,
    8: 600,
    9: 1200,
    10: 1800,
}


def _get_max_attempts_configurable() -> int:
    """Get configurable MAX_ATTEMPTS value.
    Получить настраиваемое значение MAX_ATTEMPTS.
    Отримати налаштовуване значення MAX_ATTEMPTS."""
    try:
        from storage.config import Config
        config = AppSettings.instance()
        config_max = config.get("MAX_ATTEMPTS", DEFAULT_MAX_ATTEMPTS)
        if isinstance(config_max, int) and 3 <= config_max <= 10:
            return config_max
    except (ImportError, AttributeError, RuntimeError, OSError, IOError):
        pass
    return MAX_ATTEMPTS


def _secure_write(path: str, data: bytes) -> None:
    """Secure atomic write / Безопасная атомарная запись / Безпечний атомарний запис"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            if sys.platform == "win32":
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
                except (AttributeError, OSError, TypeError):
                    pass
            else:
                try:
                    os.chmod(path, 0o600)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError, IOError) as e:
            try:
                os.remove(tmp_path)
            except (OSError, PermissionError):
                pass
            raise IOError(f"Cannot write to {path}: {e} / Невозможно записать в {path}: {e} / Неможливо записати в {path}: {e}")
    except (OSError, IOError, PermissionError) as e:
        raise IOError(f"Cannot create directory for {path}: {e} / Невозможно создать директорию для {path}: {e} / Неможливо створити директорію для {path}: {e}")


def _secure_read(path: str) -> Optional[bytes]:
    """Secure read / Безопасное чтение / Безпечне читання"""
    try:
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return f.read()
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to read {path}: {e} / Не удалось прочитать {path}: {e} / Не вдалося прочитати {path}: {e}")
        return None


def _save_lockout_state(attempt_count: int, last_attempt_time: float,
                        lockout_until: float, is_permanently_locked: bool) -> None:
    """Save lockout state to file / Сохранить состояние блокировки в файл / Зберегти стан блокування у файл"""
    try:
        state = {
            "attempt_count": attempt_count,
            "last_attempt_time": last_attempt_time,
            "lockout_until": lockout_until,
            "is_permanently_locked": is_permanently_locked,
            "last_update": datetime.now().isoformat()
        }
        _secure_write(LOCKOUT_FILE, json.dumps(state, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save lockout state / Ошибка сохранения состояния блокировки / Помилка збереження стану блокування: {e}")


def _load_lockout_state() -> Tuple[int, float, float, bool]:
    """Load lockout state from file / Загрузить состояние блокировки из файла / Завантажити стан блокування з файлу"""
    if not os.path.exists(LOCKOUT_FILE):
        return 0, 0, 0, False

    try:
        content = _secure_read(LOCKOUT_FILE)
        if content:
            state = json.loads(content.decode('utf-8'))
            attempts = state.get("attempt_count", 0)
            last_time = state.get("last_attempt_time", 0)
            lockout = state.get("lockout_until", 0)
            locked = state.get("is_permanently_locked", False)
            return attempts, last_time, lockout, locked
    except (json.JSONDecodeError, OSError, IOError, KeyError, UnicodeDecodeError) as e:
        logger.debug(f"Failed to load lockout state / Ошибка загрузки состояния блокировки / Помилка завантаження стану блокування: {e}")
    
    return 0, 0, 0, False


class MasterLockout:
    """
    Master password lockout manager with rate limiting.

    Менеджер блокировки мастер-пароля с ограничением частоты попыток.
    Менеджер блокування майстер-пароля з обмеженням частоти спроб.
    """

    _instance = None
    _lock = threading.RLock()
    
    _attempt_count: int = 0
    _last_attempt_time: float = 0
    _lockout_until: float = 0
    _is_permanently_locked: bool = False
    
    _max_attempts: int = DEFAULT_MAX_ATTEMPTS

    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._max_attempts = _get_max_attempts_configurable()
                    cls._instance._load_state()
        return cls._instance

    def _load_state(self) -> None:
        """Load lockout state from file / Загрузить состояние блокировки из файла / Завантажити стан блокування з файлу"""
        with self._lock:
            attempts, last_time, lockout, locked = _load_lockout_state()
            self._attempt_count = attempts
            self._last_attempt_time = last_time
            self._lockout_until = lockout
            self._is_permanently_locked = locked
            
            # Auto-reset if lockout expired
            if self._lockout_until > 0 and self._lockout_until <= time.time():
                self._reset()
            logger.debug(f"Lockout state loaded: attempts={self._attempt_count}, locked={self._is_permanently_locked} / Состояние блокировки загружено: попытки={self._attempt_count}, заблокировано={self._is_permanently_locked} / Стан блокування завантажено: спроби={self._attempt_count}, заблоковано={self._is_permanently_locked}")

    def _save_state(self) -> None:
        """Save lockout state to file / Сохранить состояние блокировки в файл / Зберегти стан блокування у файл"""
        with self._lock:
            _save_lockout_state(self._attempt_count, self._last_attempt_time,
                                self._lockout_until, self._is_permanently_locked)

    @classmethod
    def _get_lockout_delay(cls, attempts: int) -> int:
        """Get lockout delay for given attempt count
        Получить задержку блокировки для данного количества попыток
        Отримати затримку блокування для даної кількості спроб"""
        return LOCKOUT_TIMES.get(attempts, LOCKOUT_TIMES[min(attempts, max(LOCKOUT_TIMES.keys()))])

    def apply_rate_limit(self) -> Tuple[bool, int]:
        """
        Apply rate limiting based on attempts.
        
        Returns:
            (is_allowed, remaining_seconds) - True if allowed, False if locked out
            (разрешено, осталось_секунд) - True если разрешено, False если заблокировано
            (дозволено, залишилось_секунд) - True якщо дозволено, False якщо заблоковано
        """
        with self._lock:
            current_time_val = time.time()
            max_attempts = self.get_max_attempts()

            if self._is_permanently_locked:
                return False, -1

            if self._lockout_until > current_time_val:
                return False, int(self._lockout_until - current_time_val)

            # Reset after 10 minutes of inactivity
            if current_time_val - self._last_attempt_time > 600:
                self._attempt_count = 0
                self._lockout_until = 0
                self._save_state()

            return True, 0

    def record_failed_attempt(self, source: str = "unknown") -> int:
        """
        Record a failed authentication attempt.
        
        Returns:
            Delay in seconds, or -1 for permanent lockout
            Задержка в секундах, или -1 при постоянной блокировке
            Затримка в секундах, або -1 при постійному блокуванні
        """
        with self._lock:
            max_attempts = self.get_max_attempts()

            self._attempt_count += 1
            self._last_attempt_time = time.time()

            if self._attempt_count >= max_attempts:
                self._is_permanently_locked = True
                self._save_state()
                logger.warning(f"Permanent lockout triggered after {self._attempt_count} attempts from {source} / Постоянная блокировка после {self._attempt_count} попыток от {source} / Постійне блокування після {self._attempt_count} спроб від {source}")
                return -1

            delay = self._get_lockout_delay(self._attempt_count)
            if delay > 0:
                self._lockout_until = self._last_attempt_time + delay
                logger.warning(f"Lockout for {delay} seconds after {self._attempt_count} attempts from {source} / Блокировка на {delay} секунд после {self._attempt_count} попыток от {source} / Блокування на {delay} секунд після {self._attempt_count} спроб від {source}")

            self._save_state()
            return delay

    def reset(self) -> None:
        """Reset all attempt counters / Сбросить все счетчики попыток / Скинути всі лічильники спроб"""
        with self._lock:
            self._attempt_count = 0
            self._lockout_until = 0
            self._is_permanently_locked = False
            self._last_attempt_time = 0
            self._save_state()
            logger.debug("Lockout attempts reset / Счётчики блокировки сброшены / Лічильники блокування скинуто")

    def get_remaining_lockout_time(self) -> int:
        """Get remaining lockout time in seconds
        Получить оставшееся время блокировки в секундах
        Отримати час блокування в секундах"""
        with self._lock:
            if self._is_permanently_locked:
                return -1
            if self._lockout_until <= time.time():
                return 0
            return int(self._lockout_until - time.time())

    def get_attempts_remaining(self) -> int:
        """Get number of remaining attempts before lockout
        Получить количество оставшихся попыток до блокировки
        Отримати кількість спроб до блокування"""
        with self._lock:
            max_attempts = self.get_max_attempts()
            if self._is_permanently_locked:
                return 0
            if self._attempt_count >= max_attempts:
                return 0
            return max_attempts - self._attempt_count

    def is_permanently_locked(self) -> bool:
        """Check if permanently locked
        Проверить, заблокирована ли программа навсегда
        Перевірити, чи заблоковано програму назавжди"""
        with self._lock:
            return self._is_permanently_locked

    def get_lockout_info(self) -> Dict[str, Any]:
        """Get detailed lockout information
        Получить подробную информацию о блокировке
        Отримати детальну інформацію про блокування"""
        with self._lock:
            remaining = self.get_remaining_lockout_time()
            max_attempts = self.get_max_attempts()
            return {
                'attempts': self._attempt_count,
                'max_attempts': max_attempts,
                'remaining_attempts': self.get_attempts_remaining(),
                'lockout_seconds': remaining if remaining > 0 else 0,
                'is_locked': remaining > 0,
                'is_permanently_locked': self._is_permanently_locked
            }

    def get_max_attempts(self) -> int:
        """Get configurable maximum attempts value
        Получить настраиваемое значение максимальных попыток
        Отримати налаштовуване значення максимальних спроб"""
        with self._lock:
            return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> bool:
        """
        Set maximum attempts value.
        
        Args:
            max_attempts: New max attempts value (3-10)
            
        Returns:
            True if set successfully
        """
        with self._lock:
            if max_attempts < 3:
                max_attempts = 3
            if max_attempts > 10:
                max_attempts = 10
            self._max_attempts = max_attempts
            logger.info(f"Max attempts set to: {max_attempts} / Максимальное количество попыток установлено: {max_attempts} / Максимальну кількість спроб встановлено: {max_attempts}")
            return True

    def get_attempt_count(self) -> int:
        """Get current attempt count / Получить текущее количество попыток / Отримати поточну кількість спроб"""
        with self._lock:
            return self._attempt_count

    def get_last_attempt_time(self) -> float:
        """Get last attempt time / Получить время последней попытки / Отримати час останньої спроби"""
        with self._lock:
            return self._last_attempt_time

    def force_unlock(self) -> bool:
        """Force unlock (admin override) / Принудительная разблокировка (администратор) / Примусове розблокування (адміністратор)"""
        with self._lock:
            was_locked = self._is_permanently_locked or self._lockout_until > time.time()
            self._attempt_count = 0
            self._lockout_until = 0
            self._is_permanently_locked = False
            self._last_attempt_time = 0
            self._save_state()
            if was_locked:
                logger.info("Lockout manually overridden / Блокировка принудительно снята / Блокування примусово знято")
            return True


# ==================== SINGLETON INSTANCE ====================

_lockout_manager = None

def get_lockout_manager() -> MasterLockout:
    """Get the global lockout manager instance / Получить глобальный экземпляр менеджера блокировки / Отримати глобальний екземпляр менеджера блокування"""
    global _lockout_manager
    if _lockout_manager is None:
        _lockout_manager = MasterLockout()
    return _lockout_manager


# ==================== CONVENIENCE FUNCTIONS ====================

def apply_rate_limit() -> Tuple[bool, int]:
    """Apply rate limiting / Применить ограничение частоты / Застосувати обмеження частоти"""
    return get_lockout_manager().apply_rate_limit()

def record_failed_attempt(source: str = "unknown") -> int:
    """Record a failed authentication attempt / Записать неудачную попытку аутентификации / Записати невдалу спробу аутентифікації"""
    return get_lockout_manager().record_failed_attempt(source)

def reset_lockout() -> None:
    """Reset all attempt counters / Сбросить все счетчики попыток / Скинути всі лічильники спроб"""
    get_lockout_manager().reset()

def get_remaining_lockout_time() -> int:
    """Get remaining lockout time in seconds / Получить оставшееся время блокировки в секундах / Отримати час блокування в секундах"""
    return get_lockout_manager().get_remaining_lockout_time()

def get_attempts_remaining() -> int:
    """Get number of remaining attempts before lockout / Получить количество оставшихся попыток до блокировки / Отримати кількість спроб до блокування"""
    return get_lockout_manager().get_attempts_remaining()

def is_permanently_locked() -> bool:
    """Check if permanently locked / Проверить, заблокирована ли программа навсегда / Перевірити, чи заблоковано програму назавжди"""
    return get_lockout_manager().is_permanently_locked()

def get_lockout_info() -> Dict[str, Any]:
    """Get detailed lockout information / Получить подробную информацию о блокировке / Отримати детальну інформацію про блокування"""
    return get_lockout_manager().get_lockout_info()

def get_max_attempts() -> int:
    """Get configurable maximum attempts value / Получить настраиваемое значение максимальных попыток / Отримати налаштовуване значення максимальних спроб"""
    return get_lockout_manager().get_max_attempts()

def set_max_attempts(max_attempts: int) -> bool:
    """Set maximum attempts value / Установить значение максимальных попыток / Встановити значення максимальних спроб"""
    return get_lockout_manager().set_max_attempts(max_attempts)

def force_unlock() -> bool:
    """Force unlock (admin override) / Принудительная разблокировка (администратор) / Примусове розблокування (адміністратор)"""
    return get_lockout_manager().force_unlock()


__all__ = [
    'MasterLockout',
    'get_lockout_manager',
    'apply_rate_limit',
    'record_failed_attempt',
    'reset_lockout',
    'get_remaining_lockout_time',
    'get_attempts_remaining',
    'is_permanently_locked',
    'get_lockout_info',
    'get_max_attempts',
    'set_max_attempts',
    'force_unlock',
    'LOCKOUT_TIMES',
]