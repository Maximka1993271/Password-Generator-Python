"""
Master password authentication - Audit logging
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Dict, Any, List

from security.master_auth_constants import (
    AUDIT_LOG_FILE, AUDIT_LOG_MAX_ENTRIES, AUDIT_LOG_RETENTION_DAYS
)
from security.master_auth_helpers import _secure_write, _secure_read

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_audit_log(cls) -> None:
    """Save audit log / Сохранить журнал аудита / Зберегти журнал аудиту"""
    try:
        _cleanup_audit_log(cls)

        audit_data = {
            "entries": cls._audit_log,
            "last_update": datetime.now().isoformat(),
            "version": 3
        }
        _secure_write(AUDIT_LOG_FILE, json.dumps(audit_data, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save audit log / Ошибка сохранения журнала аудита / Помилка збереження журналу аудиту: {e}")


def _load_audit_log(cls) -> None:
    """Load audit log / Загрузить журнал аудита / Завантажити журнал аудиту"""
    if not os.path.exists(AUDIT_LOG_FILE):
        return

    try:
        content = _secure_read(AUDIT_LOG_FILE)
        if content:
            audit_data = json.loads(content.decode('utf-8'))
            entries = audit_data.get("entries", [])
            if isinstance(entries, list):
                cls._audit_log = entries[-AUDIT_LOG_MAX_ENTRIES:]
            logger.debug(f"Loaded {len(cls._audit_log)} audit entries / Загружено {len(cls._audit_log)} записей аудита / Завантажено {len(cls._audit_log)} записів аудиту")
    except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load audit log / Ошибка загрузки журнала аудита / Помилка завантаження журналу аудиту: {e}")


def _cleanup_audit_log(cls) -> None:
    """Clean old audit log entries / Очистить старые записи аудита / Очистити старі записи аудиту"""
    try:
        current_time = datetime.now()
        cutoff_time = current_time.timestamp() - (AUDIT_LOG_RETENTION_DAYS * 24 * 3600)

        filtered_log = []
        for entry in cls._audit_log:
            try:
                entry_time = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00")).timestamp()
                if entry_time > cutoff_time:
                    filtered_log.append(entry)
            except (ValueError, TypeError, KeyError) as e:
                filtered_log.append(entry)

        if len(filtered_log) > AUDIT_LOG_MAX_ENTRIES:
            filtered_log = filtered_log[-AUDIT_LOG_MAX_ENTRIES:]

        cls._audit_log = filtered_log
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.debug(f"Audit log cleanup error / Ошибка очистки журнала аудита / Помилка очищення журналу аудиту: {e}")


def _log_audit_event(cls, event_type: str, details: Dict[str, Any]) -> None:
    """Log an audit event / Записать событие аудита / Записати подію аудиту"""
    try:
        event = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details.copy() if details else {}
        }
        cls._audit_log.append(event)

        if len(cls._audit_log) > AUDIT_LOG_MAX_ENTRIES:
            cls._audit_log = cls._audit_log[-AUDIT_LOG_MAX_ENTRIES:]

        try:
            _save_audit_log(cls)
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"Audit log save error / Ошибка сохранения журнала аудита / Помилка збереження журналу аудиту: {e}")
    except (TypeError, ValueError, KeyError, AttributeError) as e:
        logger.debug(f"Audit logging error / Ошибка записи аудита / Помилка запису аудиту: {e}")


def get_audit_log(cls) -> List[Dict[str, Any]]:
    """Get audit log entries / Получить записи журнала аудита / Отримати записи журналу аудиту"""
    return cls._audit_log.copy()


def clear_audit_log(cls) -> bool:
    """Clear audit log / Очистить журнал аудита / Очистити журнал аудиту"""
    try:
        cls._audit_log = []
        _save_audit_log(cls)
        logger.info("Audit log cleared / Журнал аудита очищен / Журнал аудиту очищено")
        return True
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to clear audit log / Ошибка очистки журнала аудита / Помилка очищення журналу аудиту: {e}")
        return False