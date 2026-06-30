"""
Master password authentication - Constants and settings
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import sys

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use .securepass/data to keep sensitive files hidden
_SECUREPASS = os.path.join(_BASE_DIR, ".securepass", "data")
CONFIG_DIR = _SECUREPASS if os.path.exists(_SECUREPASS) else os.path.join(_BASE_DIR, "data")
# Ensure CONFIG_DIR exists and is hidden on Windows
if not os.path.exists(CONFIG_DIR):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            import ctypes as _ct, platform as _pl
            if _pl.system() == "Windows":
                _ct.windll.kernel32.SetFileAttributesW(CONFIG_DIR, 0x02)
        except (AttributeError, OSError, TypeError, ImportError):
            pass
    except (OSError, PermissionError):
        pass
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")
LOCKOUT_FILE = os.path.join(CONFIG_DIR, "lockout.json")
AUDIT_LOG_FILE = os.path.join(CONFIG_DIR, "auth_audit.json")
PASSWORD_HISTORY_FILE = os.path.join(CONFIG_DIR, "password_history.json")
PASSWORD_HISTORY_HASH_PREFIX = "history_pbkdf2_sha256"
PASSWORD_HISTORY_HASH_ITERATIONS = 300000
PASSWORD_HISTORY_SALT_BYTES = 16
TRUSTED_DEVICES_FILE = os.path.join(CONFIG_DIR, "trusted_devices.json")
RECOVERY_CODES_FILE = os.path.join(CONFIG_DIR, "recovery_codes.json")
SESSIONS_FILE = os.path.join(CONFIG_DIR, "sessions.json")

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

# Password history max entries
# Максимальное количество записей в истории паролей
# Максимальна кількість записів в історії паролів
PASSWORD_HISTORY_MAX = 24

# Audit log settings
# Настройки журнала аудита
# Налаштування журналу аудиту
AUDIT_LOG_MAX_ENTRIES = 100
AUDIT_LOG_RETENTION_DAYS = 90

# Session settings
# Настройки сессий
# Налаштування сесій
SESSION_TIMEOUT_HOURS = 24

# Trusted devices
# Доверенные устройства
# Довірені пристрої
MAX_TRUSTED_DEVICES = 5

# Recovery codes
# Резервные коды
# Резервні коди
RECOVERY_CODES_COUNT = 10
RECOVERY_CODE_LENGTH = 8
RECOVERY_CODE_HASH_PREFIX = "pbkdf2_sha256"
RECOVERY_CODE_HASH_ITERATIONS = 200000
RECOVERY_CODE_SALT_BYTES = 16

# Argon2 parameters
# Параметры Argon2
# Параметри Argon2
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32

# Fallback PBKDF2 parameters
# Параметры PBKDF2 для fallback
# Параметри PBKDF2 для fallback
PBKDF2_ITERATIONS = 600000
PBKDF2_SALT_SIZE = 32
PBKDF2_HASH_LEN = 32

# Try to import Argon2 and set _ARGON2_OK flag
# Пытаемся импортировать Argon2 и установить флаг _ARGON2_OK
# Намагаємося імпортувати Argon2 та встановити прапорець _ARGON2_OK
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ARGON2_OK = True
except ImportError as e:
    PasswordHasher = None
    VerifyMismatchError = VerificationError = InvalidHashError = Exception
    _ARGON2_OK = False