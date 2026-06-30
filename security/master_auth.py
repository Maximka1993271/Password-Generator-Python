"""
Master password authentication module - core password management

Модуль аутентификации мастер-пароля - основное управление паролем
Модуль аутентифікації майстер-пароля - основне керування паролем

FIXED #SPLIT: Split into multiple files for maintainability
This file is a wrapper that re-exports everything from the split modules.

Этот файл является обёрткой, которая ре-экспортирует всё из разделённых модулей.
Цей файл є обгорткою, яка ре-експортує все з розділених модулів.
"""
from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional

# Import constants
from security.master_auth_constants import *

# Import helper functions
from security.master_auth_helpers import *

# Import core class and exceptions
from security.master_auth_core import (
    MasterPasswordError, LockoutError, AuditError, SessionError,
    TrustedDeviceError, RecoveryCodeError, AuditEvent, TrustedDevice,
    Session, RecoveryCode, MasterPassword as _MasterPasswordCore
)

# Import lockout methods
from security.master_auth_lockout import (
    get_remaining_lockout_time, get_attempts_remaining, is_permanently_locked,
    get_lockout_info, reset_lockout
)

# Import audit methods
from security.master_auth_audit import get_audit_log, clear_audit_log

# Import verify methods
from security.master_auth_verify import is_set, verify, set_password, change_password, remove

# Import history methods
from security.master_auth_history import add_to_history, is_password_reused, clear_history

# Import trusted devices methods
from security.master_auth_trusted import get_trusted_devices, add_trusted_device, remove_trusted_device, is_device_trusted

# Import session methods
from security.master_auth_session import validate_session, end_session, end_all_sessions, get_sessions, get_current_session_id

# Import recovery methods
from security.master_auth_recovery import generate_recovery_codes, verify_recovery_code, get_recovery_codes_status, clear_recovery_codes

# Import 2FA methods
from security.master_auth_2fa import set_config, is_2fa_required, set_skip_2fa_once, should_skip_2fa, verify_with_2fa, prompt_on_startup


class MasterPassword(_MasterPasswordCore):
    """
    Unified master password manager combining authentication,
    lockout management, and recovery functionality.
    
    Унифицированный менеджер мастер-пароля, объединяющий аутентификацию,
    управление блокировкой и функциональность восстановления.
    
    Уніфікований менеджер майстер-пароля, що поєднує аутентифікацію,
    керування блокуванням та функціональність відновлення.
    """

    # ==================== AUTHENTICATION METHODS ====================

    @classmethod
    def get_remaining_lockout_time(cls) -> int:
        """Get remaining lockout time in seconds.
        Получить оставшееся время блокировки в секундах.
        Отримати час блокування в секундах."""
        from security.master_auth_lockout import get_remaining_lockout_time
        return get_remaining_lockout_time(cls)

    @classmethod
    def get_attempts_remaining(cls) -> int:
        """Get number of remaining attempts before lockout.
        Получить количество оставшихся попыток до блокировки.
        Отримати кількість спроб до блокування."""
        from security.master_auth_lockout import get_attempts_remaining
        return get_attempts_remaining(cls)

    @classmethod
    def is_permanently_locked(cls) -> bool:
        """Check if permanently locked.
        Проверить, заблокирована ли программа навсегда.
        Перевірити, чи заблоковано програму назавжди."""
        from security.master_auth_lockout import is_permanently_locked
        return is_permanently_locked(cls)

    @classmethod
    def get_lockout_info(cls) -> dict:
        """Get detailed lockout information.
        Получить подробную информацию о блокировке.
        Отримати детальну інформацію про блокування."""
        from security.master_auth_lockout import get_lockout_info
        return get_lockout_info(cls)

    @classmethod
    def get_audit_log(cls) -> List[Dict[str, Any]]:
        """Get audit log entries.
        Получить записи журнала аудита.
        Отримати записи журналу аудиту."""
        from security.master_auth_audit import get_audit_log
        return get_audit_log(cls)

    @classmethod
    def clear_audit_log(cls) -> bool:
        """Clear audit log.
        Очистить журнал аудита.
        Очистити журнал аудиту."""
        from security.master_auth_audit import clear_audit_log
        return clear_audit_log(cls)

    @classmethod
    def reset_lockout(cls) -> bool:
        """Reset lockout state (admin only).
        Сбросить состояние блокировки (только администратор).
        Скинути стан блокування (тільки адміністратор)."""
        from security.master_auth_lockout import reset_lockout
        return reset_lockout(cls)

    @classmethod
    def is_set(cls) -> bool:
        """Check if master password is set.
        Проверить, установлен ли мастер-пароль.
        Перевірити, чи встановлено майстер-пароль."""
        from security.master_auth_verify import is_set
        return is_set(cls)

    @classmethod
    def verify(cls, password: str, record_attempt: bool = True, source: str = "unknown") -> bool:
        """Verify master password with rate limiting.
        Проверить мастер-пароль с ограничением частоты попыток.
        Перевірити майстер-пароль з обмеженням частоти спроб."""
        from security.master_auth_verify import verify
        return verify(cls, password, record_attempt, source)

    @classmethod
    def set_password(cls, password: str) -> None:
        """Set a new master password.
        Установить новый мастер-пароль.
        Встановити новий майстер-пароль."""
        from security.master_auth_verify import set_password
        set_password(cls, password)

    @classmethod
    def change_password(cls, old_password: str, new_password: str) -> bool:
        """Change master password.
        Изменить мастер-пароль.
        Змінити майстер-пароль."""
        from security.master_auth_verify import change_password
        return change_password(cls, old_password, new_password)

    @classmethod
    def remove(cls) -> None:
        """Remove master password and all related data.
        Удалить мастер-пароль и все связанные данные.
        Видалити майстер-пароль та всі пов'язані дані."""
        from security.master_auth_verify import remove
        remove(cls)

    @classmethod
    def add_to_history(cls, password_hash: str) -> None:
        """Add password hash to history.
        Добавить хеш пароля в историю.
        Додати хеш пароля в історію."""
        from security.master_auth_history import add_to_history
        add_to_history(cls, password_hash)

    @classmethod
    def is_password_reused(cls, password: str) -> bool:
        """Check if password was used before.
        Проверить, использовался ли пароль ранее.
        Перевірити, чи використовувався пароль раніше."""
        from security.master_auth_history import is_password_reused
        return is_password_reused(cls, password)

    @classmethod
    def clear_history(cls) -> None:
        """Clear password history.
        Очистить историю паролей.
        Очистити історію паролів."""
        from security.master_auth_history import clear_history
        clear_history(cls)

    @classmethod
    def get_trusted_devices(cls) -> List[Dict[str, Any]]:
        """Get list of trusted devices.
        Получить список доверенных устройств.
        Отримати список довірених пристроїв."""
        from security.master_auth_trusted import get_trusted_devices
        return get_trusted_devices(cls)

    @classmethod
    def add_trusted_device(cls, device_name: str) -> bool:
        """Add current device as trusted.
        Добавить текущее устройство как доверенное.
        Додати поточний пристрій як довірений."""
        from security.master_auth_trusted import add_trusted_device
        return add_trusted_device(cls, device_name)

    @classmethod
    def remove_trusted_device(cls, device_id: str) -> bool:
        """Remove trusted device.
        Удалить доверенное устройство.
        Видалити довірений пристрій."""
        from security.master_auth_trusted import remove_trusted_device
        return remove_trusted_device(cls, device_id)

    @classmethod
    def is_device_trusted(cls) -> bool:
        """Check if current device is trusted.
        Проверить, является ли текущее устройство доверенным.
        Перевірити, чи є поточний пристрій довіреним."""
        from security.master_auth_trusted import is_device_trusted
        return is_device_trusted(cls)

    @classmethod
    def get_sessions(cls) -> List[Dict[str, Any]]:
        """Get active sessions.
        Получить активные сессии.
        Отримати активні сесії."""
        from security.master_auth_session import get_sessions
        return get_sessions(cls)

    @classmethod
    def get_current_session_id(cls) -> Optional[str]:
        """Get current session ID.
        Получить ID текущей сессии.
        Отримати ID поточної сесії."""
        from security.master_auth_session import get_current_session_id
        return get_current_session_id(cls)

    @classmethod
    def validate_session(cls, session_id: str) -> bool:
        """Validate if session is still active.
        Проверить, активна ли сессия.
        Перевірити, чи активна сесія."""
        from security.master_auth_session import validate_session
        return validate_session(cls, session_id)

    @classmethod
    def end_session(cls, session_id: Optional[str] = None) -> bool:
        """End a session.
        Завершить сессию.
        Завершити сесію."""
        from security.master_auth_session import end_session
        return end_session(cls, session_id)

    @classmethod
    def end_all_sessions(cls) -> int:
        """End all active sessions.
        Завершить все активные сессии.
        Завершити всі активні сесії."""
        from security.master_auth_session import end_all_sessions
        return end_all_sessions(cls)

    @classmethod
    def set_config(cls, config) -> None:
        """Set configuration object reference.
        Установить ссылку на объект конфигурации.
        Встановити посилання на об'єкт конфігурації."""
        from security.master_auth_2fa import set_config
        set_config(cls, config)

    @classmethod
    def is_2fa_required(cls) -> bool:
        """Check if 2FA is required.
        Проверить, требуется ли 2FA.
        Перевірити, чи потрібна 2FA."""
        from security.master_auth_2fa import is_2fa_required
        return is_2fa_required(cls)

    @classmethod
    def set_skip_2fa_once(cls, skip: bool) -> None:
        """Set flag to skip 2FA for next authentication.
        Установить флаг пропуска 2FA для следующей аутентификации.
        Встановити прапорець пропуску 2FA для наступної аутентифікації."""
        from security.master_auth_2fa import set_skip_2fa_once
        set_skip_2fa_once(cls, skip)

    @classmethod
    def should_skip_2fa(cls) -> bool:
        """Check if 2FA should be skipped for this authentication.
        Проверить, следует ли пропустить 2FA для этой аутентификации.
        Перевірити, чи слід пропустити 2FA для цієї аутентифікації."""
        from security.master_auth_2fa import should_skip_2fa
        return should_skip_2fa(cls)

    @classmethod
    def verify_with_2fa(cls, password: str, source: str = "startup") -> Tuple[bool, Optional[str]]:
        """Verify master password with 2FA if enabled.
        Проверить мастер-пароль с 2FA, если включена.
        Перевірити майстер-пароль з 2FA, якщо ввімкнено."""
        from security.master_auth_2fa import verify_with_2fa
        return verify_with_2fa(cls, password, source)

    @classmethod
    def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
        """Show master password prompt on startup.
        Показать запрос мастер-пароля при запуске.
        Показати запит майстер-пароля при запуску."""
        from security.master_auth_2fa import prompt_on_startup
        return prompt_on_startup(cls, lang, theme)

    # ==================== RECOVERY METHODS ====================

    @classmethod
    def generate_recovery_codes(cls, count: int = RECOVERY_CODES_COUNT,
                                length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """Generate new recovery codes.
        Сгенерировать новые резервные коды.
        Згенерувати нові резервні коди."""
        from security.master_auth_recovery import generate_recovery_codes
        return generate_recovery_codes(cls, count, length)

    @classmethod
    def verify_recovery_code(cls, code: str) -> bool:
        """Verify and consume a recovery code.
        Проверить и использовать резервный код.
        Перевірити та використати резервний код."""
        from security.master_auth_recovery import verify_recovery_code
        return verify_recovery_code(cls, code)

    @classmethod
    def get_recovery_codes_status(cls) -> Dict[str, Any]:
        """Get recovery codes status.
        Получить статус резервных кодов.
        Отримати статус резервних кодів."""
        from security.master_auth_recovery import get_recovery_codes_status
        return get_recovery_codes_status(cls)

    @classmethod
    def clear_recovery_codes(cls) -> bool:
        """Clear all recovery codes.
        Очистить все резервные коды.
        Очистити всі резервні коди."""
        from security.master_auth_recovery import clear_recovery_codes
        return clear_recovery_codes(cls)


__all__ = [
    'MasterPassword',
    'MasterPasswordError',
    'LockoutError',
    'AuditError',
    'SessionError',
    'TrustedDeviceError',
    'RecoveryCodeError',
    'AuditEvent',
    'TrustedDevice',
    'Session',
    'RecoveryCode',
    'PASSWORD_HISTORY_MAX',
    'AUDIT_LOG_MAX_ENTRIES',
    'AUDIT_LOG_RETENTION_DAYS',
    'SESSION_TIMEOUT_HOURS',
    'MAX_TRUSTED_DEVICES',
    'RECOVERY_CODES_COUNT',
    'RECOVERY_CODE_LENGTH',
    'LOCKOUT_TIMES',
]