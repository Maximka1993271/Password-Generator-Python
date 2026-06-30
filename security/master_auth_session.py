"""
Master password authentication - Sessions
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
import secrets
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

from security.master_auth_constants import SESSIONS_FILE, SESSION_TIMEOUT_HOURS
from security.master_auth_helpers import _secure_write, _secure_read, _get_device_fingerprint, _get_ip_address
from security.master_auth_core import Session

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_sessions(cls) -> None:
    """Save active sessions / Сохранить активные сессии / Зберегти активні сесії"""
    try:
        sessions_data = {
            "sessions": [s.to_dict() if hasattr(s, 'to_dict') else s for s in cls._sessions],
            "last_update": datetime.now().isoformat()
        }
        _secure_write(SESSIONS_FILE, json.dumps(sessions_data, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save sessions / Ошибка сохранения сессий / Помилка збереження сесій: {e}")


def _load_sessions(cls) -> None:
    """Load active sessions / Загрузить активные сессии / Завантажити активні сесії"""
    if not os.path.exists(SESSIONS_FILE):
        return

    try:
        content = _secure_read(SESSIONS_FILE)
        if content:
            sessions_data = json.loads(content.decode('utf-8'))
            sessions = sessions_data.get("sessions", [])
            if isinstance(sessions, list):
                cls._sessions = sessions
                _cleanup_expired_sessions(cls)
            logger.debug(f"Loaded {len(cls._sessions)} sessions / Загружено {len(cls._sessions)} сессий / Завантажено {len(cls._sessions)} сесій")
    except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load sessions / Ошибка загрузки сессий / Помилка завантаження сесій: {e}")


def _cleanup_expired_sessions(cls) -> None:
    """Clean up expired sessions / Очистить просроченные сессии / Очистити прострочені сесії"""
    try:
        current_time = datetime.now().timestamp()
        active_sessions = []

        for session in cls._sessions:
            try:
                expires_at = datetime.fromisoformat(session.get("expires_at", "2000-01-01T00:00:00")).timestamp()
                if expires_at > current_time:
                    active_sessions.append(session)
            except (ValueError, TypeError, KeyError) as e:
                active_sessions.append(session)

        if len(active_sessions) != len(cls._sessions):
            cls._sessions = active_sessions
            _save_sessions(cls)
            logger.debug(f"Cleaned up {len(cls._sessions) - len(active_sessions)} expired sessions / Очищено {len(cls._sessions) - len(active_sessions)} просроченных сессий / Очищено {len(cls._sessions) - len(active_sessions)} прострочених сесій")
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.debug(f"Session cleanup error / Ошибка очистки сессий / Помилка очищення сесій: {e}")


def _create_session(cls, source: str) -> Optional[str]:
    """Create new session for successful authentication
    Создать новую сессию для успешной аутентификации
    Створити нову сесію для успішної аутентифікації"""
    try:
        session_id = secrets.token_hex(32)
        now = datetime.now()
        expires_at = now.timestamp() + (SESSION_TIMEOUT_HOURS * 3600)

        session = Session(
            session_id=session_id,
            created_at=now.isoformat(),
            expires_at=datetime.fromtimestamp(expires_at).isoformat(),
            device_id=_get_device_fingerprint(),
            ip_address=_get_ip_address()
        )

        cls._sessions.append(session.to_dict())
        cls._current_session_id = session_id
        _save_sessions(cls)

        logger.debug(f"Session created: {session_id[:16]}... / Сессия создана: {session_id[:16]}... / Сесію створено: {session_id[:16]}...")
        return session_id
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.debug(f"Session creation error / Ошибка создания сессии / Помилка створення сесії: {e}")
        return None


def validate_session(cls, session_id: str) -> bool:
    """Validate if session is still active
    Проверить, активна ли сессия
    Перевірити, чи активна сесія"""
    try:
        _cleanup_expired_sessions(cls)
        for session in cls._sessions:
            if session.get("session_id") == session_id:
                expires_at = datetime.fromisoformat(session.get("expires_at", "2000-01-01T00:00:00")).timestamp()
                if expires_at > time.time():
                    return True
        return False
    except (ValueError, TypeError, KeyError, AttributeError) as e:
        logger.debug(f"Session validation error / Ошибка проверки сессии / Помилка перевірки сесії: {e}")
        return False


def end_session(cls, session_id: Optional[str] = None) -> bool:
    """End a session
    Завершить сессию
    Завершити сесію"""
    try:
        if session_id is None:
            session_id = cls._current_session_id

        cls._sessions = [s for s in cls._sessions if s.get("session_id") != session_id]
        if session_id == cls._current_session_id:
            cls._current_session_id = None
        _save_sessions(cls)
        logger.debug(f"Session ended: {session_id[:16] if session_id else 'None'}... / Сессия завершена: {session_id[:16] if session_id else 'None'}... / Сесію завершено: {session_id[:16] if session_id else 'None'}...")
        return True
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.debug(f"Session end error / Ошибка завершения сессии / Помилка завершення сесії: {e}")
        return False


def end_all_sessions(cls) -> int:
    """End all active sessions
    Завершить все активные сессии
    Завершити всі активні сесії"""
    count = len(cls._sessions)
    cls._sessions = []
    cls._current_session_id = None
    _save_sessions(cls)
    logger.info(f"Ended {count} sessions / Завершено {count} сессий / Завершено {count} сесій")
    return count


def get_sessions(cls) -> List[Dict[str, Any]]:
    """Get active sessions
    Получить активные сессии
    Отримати активні сесії"""
    _cleanup_expired_sessions(cls)
    return cls._sessions.copy()


def get_current_session_id(cls) -> Optional[str]:
    """Get current session ID
    Получить ID текущей сессии
    Отримати ID поточної сесії"""
    return cls._current_session_id