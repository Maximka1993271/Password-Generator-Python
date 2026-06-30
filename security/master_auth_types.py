from __future__ import annotations
# security/master_auth_types.py
"""
Master auth types module for Secure Pass Pro.
Модуль Master auth types для Secure Pass Pro.
Модуль Master auth types для Secure Pass Pro.
"""
"""
Master auth types module for Secure Pass Pro.
Модуль Master auth types для Secure Pass Pro.
Модуль Master auth types для Secure Pass Pro.
"""
"""
Master password authentication - Data types and exceptions
Типы данных и исключения для аутентификации мастер-пароля
Типи даних та винятки для аутентифікації майстер-пароля
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AuditEvent:
    """Audit event structure / Структура события аудита / Структура події аудиту"""
    event: str
    timestamp: str
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


@dataclass
class TrustedDevice:
    """Trusted device structure / Структура доверенного устройства / Структура довіреного пристрою"""
    device_id: str
    device_name: str
    fingerprint: str
    added_at: str
    last_used: str
    ip_address: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


@dataclass
class Session:
    """Session structure / Структура сессии / Структура сесії"""
    session_id: str
    created_at: str
    expires_at: str
    device_id: str
    ip_address: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


@dataclass
class RecoveryCode:
    """Recovery code structure / Структура резервного кода / Структура резервного коду"""
    code_hash: str
    created_at: str
    used: bool = False
    used_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


class MasterPasswordError(Exception):
    """Master password exception / Исключение мастер-пароля / Виняток майстер-пароля"""
    pass


class LockoutError(MasterPasswordError):
    """Lockout exception / Исключение блокировки / Виняток блокування"""
    pass


class AuditError(MasterPasswordError):
    """Audit exception / Исключение аудита / Виняток аудиту"""
    pass


class SessionError(MasterPasswordError):
    """Session exception / Исключение сессии / Виняток сесії"""
    pass


class TrustedDeviceError(MasterPasswordError):
    """Trusted device exception / Исключение доверенного устройства / Виняток довіреного пристрою"""
    pass


class RecoveryCodeError(MasterPasswordError):
    """Recovery code exception / Исключение резервного кода / Виняток резервного коду"""
    pass