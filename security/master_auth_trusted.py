"""
Master password authentication - Trusted devices
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from security.master_auth_constants import TRUSTED_DEVICES_FILE, MAX_TRUSTED_DEVICES
from security.master_auth_helpers import _secure_write, _secure_read, _get_device_fingerprint, _get_ip_address
from security.master_auth_core import TrustedDevice

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_trusted_devices(cls) -> None:
    """Save trusted devices / Сохранить доверенные устройства / Зберегти довірені пристрої"""
    try:
        devices_data = {
            "devices": [d.to_dict() if hasattr(d, 'to_dict') else d for d in cls._trusted_devices],
            "last_update": datetime.now().isoformat()
        }
        _secure_write(TRUSTED_DEVICES_FILE, json.dumps(devices_data, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save trusted devices / Ошибка сохранения доверенных устройств / Помилка збереження довірених пристроїв: {e}")


def _load_trusted_devices(cls) -> None:
    """Load trusted devices / Загрузить доверенные устройства / Завантажити довірені пристрої"""
    if not os.path.exists(TRUSTED_DEVICES_FILE):
        return

    try:
        content = _secure_read(TRUSTED_DEVICES_FILE)
        if content:
            devices_data = json.loads(content.decode('utf-8'))
            devices = devices_data.get("devices", [])
            if isinstance(devices, list):
                cls._trusted_devices = devices
            logger.debug(f"Loaded {len(cls._trusted_devices)} trusted devices / Загружено {len(cls._trusted_devices)} доверенных устройств / Завантажено {len(cls._trusted_devices)} довірених пристроїв")
    except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load trusted devices / Ошибка загрузки доверенных устройств / Помилка завантаження довірених пристроїв: {e}")


def get_trusted_devices(cls) -> List[Dict[str, Any]]:
    """Get list of trusted devices / Получить список доверенных устройств / Отримати список довірених пристроїв"""
    return cls._trusted_devices.copy()


def add_trusted_device(cls, device_name: str) -> bool:
    """Add current device as trusted
    Добавить текущее устройство как доверенное
    Додати поточний пристрій як довірений"""
    try:
        if len(cls._trusted_devices) >= MAX_TRUSTED_DEVICES:
            logger.warning(f"Maximum trusted devices reached ({MAX_TRUSTED_DEVICES}) / Достигнуто максимальное количество доверенных устройств ({MAX_TRUSTED_DEVICES}) / Досягнуто максимальну кількість довірених пристроїв ({MAX_TRUSTED_DEVICES})")
            return False

        device = TrustedDevice(
            device_id=_get_device_fingerprint(),
            device_name=device_name,
            fingerprint=_get_device_fingerprint(),
            added_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            ip_address=_get_ip_address()
        )

        cls._trusted_devices.append(device.to_dict())
        _save_trusted_devices(cls)
        logger.info(f"Trusted device added: {device_name} / Доверенное устройство добавлено: {device_name} / Довірений пристрій додано: {device_name}")
        return True
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.error(f"Failed to add trusted device / Ошибка добавления доверенного устройства / Помилка додавання довіреного пристрою: {e}")
        return False


def remove_trusted_device(cls, device_id: str) -> bool:
    """Remove trusted device
    Удалить доверенное устройство
    Видалити довірений пристрій"""
    try:
        original_count = len(cls._trusted_devices)
        cls._trusted_devices = [d for d in cls._trusted_devices if d.get("device_id") != device_id]
        if len(cls._trusted_devices) < original_count:
            _save_trusted_devices(cls)
            logger.info(f"Trusted device removed: {device_id[:16]}... / Доверенное устройство удалено: {device_id[:16]}... / Довірений пристрій видалено: {device_id[:16]}...")
            return True
        return False
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.error(f"Failed to remove trusted device / Ошибка удаления доверенного устройства / Помилка видалення довіреного пристрою: {e}")
        return False


def is_device_trusted(cls) -> bool:
    """Check if current device is trusted
    Проверить, является ли текущее устройство доверенным
    Перевірити, чи є поточний пристрій довіреним"""
    current_fingerprint = _get_device_fingerprint()
    for device in cls._trusted_devices:
        if device.get("fingerprint") == current_fingerprint:
            device["last_used"] = datetime.now().isoformat()
            _save_trusted_devices(cls)
            return True
    return False