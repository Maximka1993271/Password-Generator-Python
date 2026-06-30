"""
Master password management module - unified interface

Модуль управления мастер-паролем - унифицированный интерфейс
Модуль керування майстер-паролем - уніфікований інтерфейс

This module provides a unified interface combining:
- Authentication (master_auth)
- Lockout management (master_lockout)
- Recovery management (master_recovery)

Этот модуль предоставляет унифицированный интерфейс, объединяющий:
- Аутентификацию (master_auth)
- Управление блокировкой (master_lockout)
- Управление восстановлением (master_recovery)

Цей модуль надає уніфікований інтерфейс, що поєднує:
- Аутентифікацію (master_auth)
- Керування блокуванням (master_lockout)
- Керування відновленням (master_recovery)

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import os
import sys
import json
import time
import hashlib
import hmac
import secrets
import re
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# ==================== IMPORT SPLIT MODULES ====================

from security.master_auth import (
    MasterPassword as _MasterPasswordAuth,
    MasterPasswordError,
    LockoutError,
    AuditError,
    SessionError,
    TrustedDeviceError,
    RecoveryCodeError,
    AuditEvent,
    TrustedDevice,
    Session,
    RecoveryCode,
)

from security.master_lockout import (
    MasterLockout,
    get_lockout_manager,
    apply_rate_limit,
    record_failed_attempt,
    reset_lockout as reset_lockout_state,
    get_remaining_lockout_time,
    get_attempts_remaining,
    is_permanently_locked as is_permanently_locked_state,
    get_lockout_info,
    get_max_attempts,
    set_max_attempts,
    force_unlock,
    LOCKOUT_TIMES,
)

from security.master_recovery import (
    MasterRecovery,
    get_recovery_manager,
    generate_recovery_codes,
    verify_recovery_code,
    get_recovery_codes_status,
    clear_recovery_codes,
    create_master_backup,
    restore_master_from_backup,
    get_master_backups,
    has_master_backups,
    emergency_master_reset,
    verify_master_backup,
    RECOVERY_CODES_COUNT,
    RECOVERY_CODE_LENGTH,
    MAX_BACKUPS,
    BACKUP_RETENTION_DAYS,
)

# ==================== UNIFIED LOGGER ====================
from utils.logger import get_logger
from core.app_settings import AppSettings  # centralised settings

logger = get_logger("master")

# ==================== CONSTANTS (RE-EXPORT) ====================

# Password history
PASSWORD_HISTORY_MAX = 24

# Audit log
AUDIT_LOG_MAX_ENTRIES = 100
AUDIT_LOG_RETENTION_DAYS = 90

# Session
SESSION_TIMEOUT_HOURS = 24

# Trusted devices
MAX_TRUSTED_DEVICES = 5


# ==================== UNIFIED MASTER PASSWORD CLASS ====================

class MasterPassword:
    """
    Unified master password manager combining authentication,
    lockout management, and recovery functionality.
    
    Унифицированный менеджер мастер-пароля, объединяющий аутентификацию,
    управление блокировкой и функциональность восстановления.
    
    Уніфікований менеджер майстер-пароля, що поєднує аутентифікацію,
    керування блокуванням та функціональність відновлення.
    """

    # ==================== AUTHENTICATION METHODS (delegated to _MasterPasswordAuth) ====================

    @classmethod
    def get_max_attempts(cls) -> int:
        """Get configurable maximum attempts value.
        Получить настраиваемое значение максимальных попыток.
        Отримати налаштовуване значення максимальних спроб."""
        return _MasterPasswordAuth.get_max_attempts()

    @classmethod
    def get_remaining_lockout_time(cls) -> int:
        """Get remaining lockout time in seconds.
        Получить оставшееся время блокировки в секундах.
        Отримати час блокування в секундах."""
        return _MasterPasswordAuth.get_remaining_lockout_time()

    @classmethod
    def get_attempts_remaining(cls) -> int:
        """Get number of remaining attempts before lockout.
        Получить количество оставшихся попыток до блокировки.
        Отримати кількість спроб до блокування."""
        return _MasterPasswordAuth.get_attempts_remaining()

    @classmethod
    def is_permanently_locked(cls) -> bool:
        """Check if permanently locked.
        Проверить, заблокирована ли программа навсегда.
        Перевірити, чи заблоковано програму назавжди."""
        return _MasterPasswordAuth.is_permanently_locked()

    @classmethod
    def get_lockout_info(cls) -> dict:
        """Get detailed lockout information.
        Получить подробную информацию о блокировке.
        Отримати детальну інформацію про блокування."""
        return _MasterPasswordAuth.get_lockout_info()

    @classmethod
    def get_audit_log(cls) -> List[Dict[str, Any]]:
        """Get audit log entries.
        Получить записи журнала аудита.
        Отримати записи журналу аудиту."""
        return _MasterPasswordAuth.get_audit_log()

    @classmethod
    def clear_audit_log(cls) -> bool:
        """Clear audit log.
        Очистить журнал аудита.
        Очистити журнал аудиту."""
        return _MasterPasswordAuth.clear_audit_log()

    @classmethod
    def reset_lockout(cls) -> bool:
        """Reset lockout state (admin only).
        Сбросить состояние блокировки (только администратор).
        Скинути стан блокування (тільки адміністратор)."""
        return _MasterPasswordAuth.reset_lockout()

    @classmethod
    def is_set(cls) -> bool:
        """Check if master password is set.
        Проверить, установлен ли мастер-пароль.
        Перевірити, чи встановлено майстер-пароль."""
        return _MasterPasswordAuth.is_set()

    @classmethod
    def verify(cls, password: str, record_attempt: bool = True, source: str = "unknown") -> bool:
        """Verify master password with rate limiting.
        Проверить мастер-пароль с ограничением частоты попыток.
        Перевірити майстер-пароль з обмеженням частоти спроб."""
        return _MasterPasswordAuth.verify(password, record_attempt, source)

    @classmethod
    def set_password(cls, password: str) -> None:
        """Set a new master password.
        Установить новый мастер-пароль.
        Встановити новий майстер-пароль."""
        _MasterPasswordAuth.set_password(password)

    @classmethod
    def change_password(cls, old_password: str, new_password: str) -> bool:
        """Change master password.
        Изменить мастер-пароль.
        Змінити майстер-пароль."""
        return _MasterPasswordAuth.change_password(old_password, new_password)

    @classmethod
    def remove(cls) -> None:
        """Remove master password and all related data.
        Удалить мастер-пароль и все связанные данные.
        Видалити майстер-пароль та всі пов'язані дані."""
        _MasterPasswordAuth.remove()

    @classmethod
    def add_to_history(cls, password_hash: str) -> None:
        """Add password hash to history.
        Добавить хеш пароля в историю.
        Додати хеш пароля в історію."""
        _MasterPasswordAuth.add_to_history(password_hash)

    @classmethod
    def is_password_reused(cls, password: str) -> bool:
        """Check if password was used before.
        Проверить, использовался ли пароль ранее.
        Перевірити, чи використовувався пароль раніше."""
        return _MasterPasswordAuth.is_password_reused(password)

    @classmethod
    def clear_history(cls) -> None:
        """Clear password history.
        Очистить историю паролей.
        Очистити історію паролів."""
        _MasterPasswordAuth.clear_history()

    @classmethod
    def get_trusted_devices(cls) -> List[Dict[str, Any]]:
        """Get list of trusted devices.
        Получить список доверенных устройств.
        Отримати список довірених пристроїв."""
        return _MasterPasswordAuth.get_trusted_devices()

    @classmethod
    def add_trusted_device(cls, device_name: str) -> bool:
        """Add current device as trusted.
        Добавить текущее устройство как доверенное.
        Додати поточний пристрій як довірений."""
        return _MasterPasswordAuth.add_trusted_device(device_name)

    @classmethod
    def remove_trusted_device(cls, device_id: str) -> bool:
        """Remove trusted device.
        Удалить доверенное устройство.
        Видалити довірений пристрій."""
        return _MasterPasswordAuth.remove_trusted_device(device_id)

    @classmethod
    def is_device_trusted(cls) -> bool:
        """Check if current device is trusted.
        Проверить, является ли текущее устройство доверенным.
        Перевірити, чи є поточний пристрій довіреним."""
        return _MasterPasswordAuth.is_device_trusted()

    @classmethod
    def get_sessions(cls) -> List[Dict[str, Any]]:
        """Get active sessions.
        Получить активные сессии.
        Отримати активні сесії."""
        return _MasterPasswordAuth.get_sessions()

    @classmethod
    def get_current_session_id(cls) -> Optional[str]:
        """Get current session ID.
        Получить ID текущей сессии.
        Отримати ID поточної сесії."""
        return _MasterPasswordAuth.get_current_session_id()

    @classmethod
    def validate_session(cls, session_id: str) -> bool:
        """Validate if session is still active.
        Проверить, активна ли сессия.
        Перевірити, чи активна сесія."""
        return _MasterPasswordAuth.validate_session(session_id)

    @classmethod
    def end_session(cls, session_id: Optional[str] = None) -> bool:
        """End a session.
        Завершить сессию.
        Завершити сесію."""
        return _MasterPasswordAuth.end_session(session_id)

    @classmethod
    def end_all_sessions(cls) -> int:
        """End all active sessions.
        Завершить все активные сессии.
        Завершити всі активні сесії."""
        return _MasterPasswordAuth.end_all_sessions()

    @classmethod
    def set_config(cls, config) -> None:
        """Set configuration object reference.
        Установить ссылку на объект конфигурации.
        Встановити посилання на об'єкт конфігурації."""
        _MasterPasswordAuth.set_config(config)

    @classmethod
    def is_2fa_required(cls) -> bool:
        """Check if 2FA is required.
        Проверить, требуется ли 2FA.
        Перевірити, чи потрібна 2FA."""
        return _MasterPasswordAuth.is_2fa_required()

    @classmethod
    def set_skip_2fa_once(cls, skip: bool) -> None:
        """Set flag to skip 2FA for next authentication.
        Установить флаг пропуска 2FA для следующей аутентификации.
        Встановити прапорець пропуску 2FA для наступної аутентифікації."""
        _MasterPasswordAuth.set_skip_2fa_once(skip)

    @classmethod
    def should_skip_2fa(cls) -> bool:
        """Check if 2FA should be skipped for this authentication.
        Проверить, следует ли пропустить 2FA для этой аутентификации.
        Перевірити, чи слід пропустити 2FA для цієї аутентифікації."""
        return _MasterPasswordAuth.should_skip_2fa()

    @classmethod
    def verify_with_2fa(cls, password: str, source: str = "startup") -> Tuple[bool, Optional[str]]:
        """Verify master password with 2FA if enabled.
        Проверить мастер-пароль с 2FA, если включена.
        Перевірити майстер-пароль з 2FA, якщо ввімкнено."""
        return _MasterPasswordAuth.verify_with_2fa(password, source)

    @classmethod
    def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
        """Show master password prompt on startup.
        Показать запрос мастер-пароля при запуске.
        Показати запит майстер-пароля при запуску."""
        return _MasterPasswordAuth.prompt_on_startup(lang, theme)

    # ==================== RECOVERY METHODS (delegated to MasterRecovery) ====================

    @classmethod
    def generate_recovery_codes(cls, count: int = RECOVERY_CODES_COUNT,
                                length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """Generate new recovery codes.
        Сгенерировать новые резервные коды.
        Згенерувати нові резервні коди."""
        return generate_recovery_codes(count, length)

    @classmethod
    def verify_recovery_code(cls, code: str) -> bool:
        """Verify and consume a recovery code.
        Проверить и использовать резервный код.
        Перевірити та використати резервний код."""
        return verify_recovery_code(code)

    @classmethod
    def get_recovery_codes_status(cls) -> Dict[str, Any]:
        """Get recovery codes status.
        Получить статус резервных кодов.
        Отримати статус резервних кодів."""
        return get_recovery_codes_status()

    @classmethod
    def clear_recovery_codes(cls) -> bool:
        """Clear all recovery codes.
        Очистить все резервные коды.
        Очистити всі резервні коди."""
        return clear_recovery_codes()

    @classmethod
    def create_master_backup(cls, version: str = "unknown") -> Optional[str]:
        """Create a backup of the master password file.
        Создать резервную копию файла мастер-пароля.
        Створити резервну копію файлу майстер-пароля."""
        return create_master_backup(version)

    @classmethod
    def restore_master_from_backup(cls, backup_index: int = 0) -> bool:
        """Restore master password from backup.
        Восстановить мастер-пароль из резервной копии.
        Відновити майстер-пароль з резервної копії."""
        return restore_master_from_backup(backup_index)

    @classmethod
    def get_master_backups(cls) -> List[Dict[str, Any]]:
        """Get list of available backups.
        Получить список доступных резервных копий.
        Отримати список доступних резервних копій."""
        return get_master_backups()

    @classmethod
    def has_master_backups(cls) -> bool:
        """Check if any backups exist.
        Проверить, существуют ли резервные копии.
        Перевірити, чи існують резервні копії."""
        return has_master_backups()

    @classmethod
    def emergency_master_reset(cls) -> bool:
        """Emergency reset of master password system.
        Аварийный сброс системы мастер-пароля.
        Аварійне скидання системи майстер-пароля."""
        return emergency_master_reset()

    @classmethod
    def verify_master_backup(cls, backup_index: int = 0) -> Tuple[bool, str]:
        """Verify integrity of a backup file.
        Проверить целостность файла резервной копии.
        Перевірити цілісність файлу резервної копії."""
        return verify_master_backup(backup_index)

    # ==================== LOCKOUT METHODS (delegated) ====================

    @classmethod
    def apply_rate_limit(cls) -> Tuple[bool, int]:
        """Apply rate limiting based on attempts.
        Применить ограничение частоты на основе попыток.
        Застосувати обмеження частоти на основі спроб."""
        return apply_rate_limit()

    @classmethod
    def record_failed_attempt(cls, source: str = "unknown") -> int:
        """Record a failed authentication attempt.
        Записать неудачную попытку аутентификации.
        Записати невдалу спробу аутентифікації."""
        return record_failed_attempt(source)

    @classmethod
    def force_unlock(cls) -> bool:
        """Force unlock (admin override).
        Принудительная разблокировка (администратор).
        Примусове розблокування (адміністратор)."""
        return force_unlock()

    @classmethod
    def get_lockout_manager(cls) -> MasterLockout:
        """Get the lockout manager instance.
        Получить экземпляр менеджера блокировки.
        Отримати екземпляр менеджера блокування."""
        return get_lockout_manager()

    @classmethod
    def get_recovery_manager(cls) -> MasterRecovery:
        """Get the recovery manager instance.
        Получить экземпляр менеджера восстановления.
        Отримати екземпляр менеджера відновлення."""
        return get_recovery_manager()


# ==================== RE-EXPORT ALL EXCEPTIONS AND CLASSES ====================

__all__ = [
    # Main class
    'MasterPassword',
    
    # Authentication exceptions
    'MasterPasswordError',
    'LockoutError',
    'AuditError',
    'SessionError',
    'TrustedDeviceError',
    'RecoveryCodeError',
    
    # Data classes
    'AuditEvent',
    'TrustedDevice',
    'Session',
    'RecoveryCode',
    
    # Lockout
    'MasterLockout',
    'get_lockout_manager',
    'apply_rate_limit',
    'record_failed_attempt',
    'reset_lockout_state',
    'get_remaining_lockout_time',
    'get_attempts_remaining',
    'is_permanently_locked_state',
    'get_lockout_info',
    'get_max_attempts',
    'set_max_attempts',
    'force_unlock',
    'LOCKOUT_TIMES',
    
    # Recovery
    'MasterRecovery',
    'get_recovery_manager',
    'generate_recovery_codes',
    'verify_recovery_code',
    'get_recovery_codes_status',
    'clear_recovery_codes',
    'create_master_backup',
    'restore_master_from_backup',
    'get_master_backups',
    'has_master_backups',
    'emergency_master_reset',
    'verify_master_backup',
    'RECOVERY_CODES_COUNT',
    'RECOVERY_CODE_LENGTH',
    'MAX_BACKUPS',
    'BACKUP_RETENTION_DAYS',
    
    # History constants
    'PASSWORD_HISTORY_MAX',
    'AUDIT_LOG_MAX_ENTRIES',
    'AUDIT_LOG_RETENTION_DAYS',
    'SESSION_TIMEOUT_HOURS',
    'MAX_TRUSTED_DEVICES',
]