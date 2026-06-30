"""
TOTP trusted devices functionality
Доверенные устройства для TOTP
Довірені пристрої для TOTP

English:
- Trusted device token generation
- Token verification
- Trusted device management (add, remove, list)

Русский:
- Генерация токенов доверенных устройств
- Проверка токенов
- Управление доверенными устройствами

Українська:
- Генерація токенів довірених пристроїв
- Перевірка токенів
- Керування довіреними пристроями
"""
from __future__ import annotations

import os
import json
import time
import hashlib
import hmac
import secrets
import threading  # <-- FIXED: added missing import
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from utils.logger import get_logger

logger = get_logger("totp")

# Trusted devices / Доверенные устройства / Довірені пристрої
TRUSTED_DEVICE_TOKEN_EXPIRY = 30 * 24 * 3600  # 30 days / 30 дней / 30 днів
MAX_TRUSTED_DEVICES = 5

# Trusted devices file / Файл доверенных устройств / Файл довірених пристроїв
TRUSTED_DEVICES_FILE = "trusted_devices.json"


@dataclass
class TrustedDeviceToken:
    """Trusted device token structure / Структура токена доверенного устройства / Структура токена довіреного пристрою"""
    device_id: str
    device_name: str
    token_hash: str
    created_at: str
    expires_at: str
    last_used: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustedDeviceToken':
        """
        Handle from dict.
        Обработать from dict.
        Обробити from dict.
        """
        return cls(**data)


class TrustedDevicesMixin:
    """Mixin for trusted devices functionality
    Миксин для функциональности доверенных устройств
    Міксин для функціональності довірених пристроїв"""

    def __init__(self):
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self._trusted_devices: Dict[str, TrustedDeviceToken] = {}
        self._trusted_devices_lock = threading.RLock()
        self._trusted_devices_file: Optional[str] = None

    def set_trusted_devices_file(self, file_path: str) -> None:
        """Set file path for trusted devices storage
        Установить путь к файлу для хранения доверенных устройств
        Встановити шлях до файлу для зберігання довірених пристроїв"""
        self._trusted_devices_file = file_path
        self._load_trusted_devices()

    def _load_trusted_devices(self) -> None:
        """Load trusted devices from file / Загрузить доверенные устройства из файла / Завантажити довірені пристрої з файлу"""
        if not self._trusted_devices_file or not os.path.exists(self._trusted_devices_file):
            return

        try:
            with open(self._trusted_devices_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            with self._trusted_devices_lock:
                self._trusted_devices.clear()
                for device_data in data.get("devices", []):
                    device = TrustedDeviceToken.from_dict(device_data)
                    expiry_time = datetime.fromisoformat(device.expires_at).timestamp()
                    if expiry_time > time.time():
                        self._trusted_devices[device.device_id] = device
            logger.debug(f"Loaded {len(self._trusted_devices)} trusted devices / Загружено {len(self._trusted_devices)} доверенных устройств / Завантажено {len(self._trusted_devices)} довірених пристроїв")
        except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
            logger.debug(f"Failed to load trusted devices / Ошибка загрузки доверенных устройств / Помилка завантаження довірених пристроїв: {e}")

    def _save_trusted_devices(self) -> None:
        """Save trusted devices to file / Сохранить доверенные устройства в файл / Зберегти довірені пристрої у файл"""
        if not self._trusted_devices_file:
            return

        try:
            with self._trusted_devices_lock:
                devices_data = {
                    "devices": [device.to_dict() for device in self._trusted_devices.values()],
                    "last_update": datetime.now().isoformat()
                }

            os.makedirs(os.path.dirname(self._trusted_devices_file), exist_ok=True)
            with open(self._trusted_devices_file, 'w', encoding='utf-8') as f:
                json.dump(devices_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self._trusted_devices)} trusted devices / Сохранено {len(self._trusted_devices)} доверенных устройств / Збережено {len(self._trusted_devices)} довірених пристроїв")
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save trusted devices / Ошибка сохранения доверенных устройств / Помилка збереження довірених пристроїв: {e}")

    def generate_trusted_device_token(self, device_id: str, device_name: str) -> Optional[str]:
        """
        Generate token for trusted device.

        Генерирует токен для доверенного устройства.
        Генерує токен для довіреного пристрою.
        """
        try:
            if len(self._trusted_devices) >= MAX_TRUSTED_DEVICES:
                logger.warning(f"Maximum trusted devices reached ({MAX_TRUSTED_DEVICES}) / Достигнуто максимальное количество доверенных устройств ({MAX_TRUSTED_DEVICES}) / Досягнуто максимальну кількість довірених пристроїв ({MAX_TRUSTED_DEVICES})")
                return None

            token = secrets.token_urlsafe(32)
            now = datetime.now()
            expires_at = now.timestamp() + TRUSTED_DEVICE_TOKEN_EXPIRY

            token_hash = hashlib.sha256(token.encode()).hexdigest()

            device = TrustedDeviceToken(
                device_id=device_id,
                device_name=device_name,
                token_hash=token_hash,
                created_at=now.isoformat(),
                expires_at=datetime.fromtimestamp(expires_at).isoformat(),
                last_used=now.isoformat()
            )

            with self._trusted_devices_lock:
                self._trusted_devices[device_id] = device
            self._save_trusted_devices()

            logger.info(f"Trusted device token generated for: {device_name} / Токен доверенного устройства сгенерирован для: {device_name} / Токен довіреного пристрою згенеровано для: {device_name}")
            return token
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Failed to generate trusted device token / Ошибка генерации токена доверенного устройства / Помилка генерації токена довіреного пристрою: {e}")
            return None

    def verify_trusted_device_token(self, device_id: str, token: str) -> bool:
        """
        Verify trusted device token.

        Проверяет токен доверенного устройства.
        Перевіряє токен довіреного пристрою.
        """
        with self._trusted_devices_lock:
            device = self._trusted_devices.get(device_id)
            if not device:
                return False

            expiry_time = datetime.fromisoformat(device.expires_at).timestamp()
            if expiry_time <= time.time():
                del self._trusted_devices[device_id]
                self._save_trusted_devices()
                return False

            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if hmac.compare_digest(token_hash, device.token_hash):
                device.last_used = datetime.now().isoformat()
                self._save_trusted_devices()
                logger.debug(f"Trusted device token verified: {device_id[:16]}... / Токен доверенного устройства проверен: {device_id[:16]}... / Токен довіреного пристрою перевірено: {device_id[:16]}...")
                return True

        return False

    def remove_trusted_device(self, device_id: str) -> bool:
        """
        Remove trusted device.

        Удаляет доверенное устройство.
        Видаляє довірений пристрій.
        """
        with self._trusted_devices_lock:
            if device_id in self._trusted_devices:
                del self._trusted_devices[device_id]
                self._save_trusted_devices()
                logger.info(f"Trusted device removed: {device_id[:16]}... / Доверенное устройство удалено: {device_id[:16]}... / Довірений пристрій видалено: {device_id[:16]}...")
                return True
        return False

    def get_trusted_devices(self) -> List[Dict[str, Any]]:
        """Get list of trusted devices / Получить список доверенных устройств / Отримати список довірених пристроїв"""
        with self._trusted_devices_lock:
            return [device.to_dict() for device in self._trusted_devices.values()]