"""
TOTP Manager for 2FA state management

Менеджер TOTP для управления состоянием 2FA
Менеджер TOTP для керування станом 2FA

English:
This module provides TOTP Manager for 2FA state management including:
- Enabling/disabling 2FA
- Code verification with anti-replay protection
- Backup codes management
- Trusted devices management
- Rate limiting for verification attempts

Русский:
Этот модуль предоставляет менеджер TOTP для управления состоянием 2FA:
- Включение/отключение 2FA
- Проверка кодов с защитой от повторного воспроизведения
- Управление резервными кодами
- Управление доверенными устройствами
- Ограничение частоты попыток верификации

Українська:
Цей модуль надає менеджер TOTP для керування станом 2FA:
- Увімкнення/вимкнення 2FA
- Перевірка кодів із захистом від повторного відтворення
- Керування резервними кодами
- Керування довіреними пристроями
- Обмеження частоти спроб верифікації
"""
from __future__ import annotations

import os
from typing import Optional, List, Dict, Any, Tuple
from utils.logger import get_logger
from core.app_settings import AppSettings  # centralised settings

logger = get_logger("totp")


class TOTPManager:
    """
    TOTP Manager for 2FA state management

    Менеджер TOTP для управления состоянием 2FA
    Менеджер TOTP для керування станом 2FA
    """

    def __init__(self):
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self._enabled = False
        self._secret: Optional[str] = None
        self._backup_codes_hashes: List[str] = []
        self._backup_codes_used_count: int = 0
        self._account_name: str = "SecurePassPro_User"
        self._totp_instance = None
        self._trusted_devices_file: Optional[str] = None

    def enable_2fa(self, secret: Optional[str] = None) -> Tuple[str, str]:
        """
        Enable 2FA and return secret and provisioning URI

        Включить 2FA и вернуть секрет и URI для подготовки
        Увімкнути 2FA та повернути секрет та URI для підготовки

        Args:
            secret: Optional pre-generated secret / Опциональный предварительно сгенерированный секрет / Опціональний попередньо згенерований секрет

        Returns:
            Tuple of (secret, provisioning_uri) / Кортеж (секрет, URI для подготовки) / Кортеж (секрет, URI для підготовки)

        Raises:
            TOTPError: If 2FA enable fails / Если включение 2FA не удалось / Якщо увімкнення 2FA не вдалося
        """
        from security.totp_core import TOTP, TOTPError

        try:
            if secret is None:
                secret = TOTP.generate_secret()
            else:
                # User-supplied secret (e.g. imported from another authenticator) —
                # validate Base32 format before accepting it.
                from core.validators import validate_totp_secret
                _ok, _err = validate_totp_secret(secret)
                if not _ok:
                    raise TOTPError(f"Invalid TOTP secret: {_err}")
            self._secret = secret.upper().replace(" ", "").replace("-", "")
            self._enabled = True
            self._totp_instance = TOTP(self._secret)
            if self._trusted_devices_file:
                self._totp_instance.set_trusted_devices_file(self._trusted_devices_file)
            provisioning_uri = TOTP.get_provisioning_uri(self._secret, self._account_name, "SecurePassPro")
            logger.info("2FA enabled / 2FA включена / 2FA увімкнено")
            return self._secret, provisioning_uri
        except (ImportError, AttributeError, ValueError, TypeError, RuntimeError, OSError) as e:
            logger.error(f"Failed to enable 2FA / Ошибка включения 2FA / Помилка увімкнення 2FA: {e}")
            raise TOTPError(f"Cannot enable 2FA / Невозможно включить 2FA / Неможливо увімкнути 2FA: {e}")

    def disable_2fa(self) -> None:
        """
        Disable 2FA and clear all data

        Отключить 2FA и очистить все данные
        Вимкнути 2FA та очистити всі дані
        """
        self._secret = None
        self._enabled = False
        self._backup_codes_hashes = []
        self._backup_codes_used_count = 0
        self._totp_instance = None
        logger.info("2FA disabled / 2FA отключена / 2FA вимкнено")

    def is_enabled(self) -> bool:
        """
        Check if 2FA is enabled

        Проверить, включена ли 2FA
        Перевірити, чи ввімкнено 2FA

        Returns:
            True if 2FA is enabled / True если 2FA включена / True якщо 2FA увімкнено
        """
        return self._enabled

    def verify_code(self, code: str, window: int = 2, source: str = "unknown") -> bool:
        """
        Verify TOTP code

        Проверить TOTP код
        Перевірити TOTP код

        Args:
            code: 6-digit code to verify / 6-значный код для проверки / 6-значний код для перевірки
            window: Time window for verification (default 2) / Временное окно для проверки (по умолчанию 2) / Часове вікно для перевірки (за замовчуванням 2)
            source: Source identifier for rate limiting / Идентификатор источника для ограничения частоты / Ідентифікатор джерела для обмеження частоти

        Returns:
            True if code is valid / True если код действителен / True якщо код дійсний
        """
        from security.totp_core import TOTPRateLimitError, TOTPError, TOTPInvalidSecretError

        if not self._enabled or not self._secret:
            return False
        if self._totp_instance is None:
            from security.totp_core import TOTP
            try:
                self._totp_instance = TOTP(self._secret)
                if self._trusted_devices_file:
                    self._totp_instance.set_trusted_devices_file(self._trusted_devices_file)
            except (TOTPInvalidSecretError, ValueError, TypeError, RuntimeError) as e:
                logger.error(f"Failed to create TOTP instance / Ошибка создания экземпляра TOTP / Помилка створення екземпляра TOTP: {e}")
                return False
        try:
            is_valid, _ = self._totp_instance.verify(code, window=window, source=source)
            return is_valid
        except TOTPRateLimitError as e:
            logger.warning(f"Rate limit during verification / Ограничение частоты при проверке / Обмеження частоти при перевірці: {e}")
            return False
        except (TOTPError, ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"Verification error / Ошибка проверки / Помилка перевірки: {e}")
            return False

    def verify_backup_code(self, code: str) -> bool:
        """
        Verify backup code and remove it if valid

        Проверить резервный код и удалить его, если он действителен
        Перевірити резервний код та видалити його, якщо він дійсний

        Args:
            code: Backup code to verify / Резервный код для проверки / Резервний код для перевірки

        Returns:
            True if code is valid / True если код действителен / True якщо код дійсний
        """
        from security.totp_core import TOTP, TOTPError

        if not self._enabled or not self._backup_codes_hashes:
            return False
        try:
            code_clean = code.replace("-", "").replace(" ", "").upper()
        except (AttributeError, TypeError) as e:
            logger.debug(f"Backup code cleaning error / Ошибка очистки резервного коду / Помилка очищення резервного коду: {e}")
            return False
        for i, stored_hash in enumerate(self._backup_codes_hashes):
            try:
                if TOTP.verify_backup_code(code_clean, stored_hash):
                    self._backup_codes_hashes.pop(i)
                    self._backup_codes_used_count += 1
                    logger.info("Backup code used and removed / Резервный код использован и удалён / Резервний код використано та видалено")
                    return True
            except (TOTPError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Backup code verification error / Ошибка проверки резервного коду / Помилка перевірки резервного коду: {e}")
                continue
        return False

    def set_backup_codes(self, codes: List[str]) -> None:
        """
        Set backup codes (stores hashes)

        Установить резервные коды (сохраняет хеши)
        Встановити резервні коди (зберігає хеші)

        Args:
            codes: List of backup codes / Список резервных кодов / Список резервних кодів

        Raises:
            TOTPError: If setting backup codes fails / Если установка резервных кодов не удалась / Якщо встановлення резервних кодів не вдалося
        """
        from security.totp_core import TOTP, TOTPError

        try:
            self._backup_codes_hashes = [TOTP.hash_backup_code(c) for c in codes]
            self._backup_codes_used_count = 0
            logger.debug(f"Stored {len(codes)} backup code hashes / Сохранено {len(codes)} хешей резервных кодов / Збережено {len(codes)} хешів резервних кодів")
        except (TypeError, ValueError, TOTPError, AttributeError) as e:
            logger.error(f"Failed to set backup codes / Ошибка установки резервных кодов / Помилка встановлення резервних кодів: {e}")
            raise TOTPError(f"Cannot set backup codes / Ошибка установки резервных кодов / Помилка встановлення резервних кодів: {e}")

    def get_backup_codes_hashes(self) -> List[str]:
        """
        Get stored backup code hashes

        Получить сохранённые хеши резервных кодов
        Отримати збережені хеші резервних кодів

        Returns:
            List of backup code hashes / Список хешей резервных кодов / Список хешів резервних кодів
        """
        return self._backup_codes_hashes.copy()

    def get_backup_codes_count(self) -> int:
        """
        Get number of remaining backup codes

        Получить количество оставшихся резервных кодов
        Отримати кількість резервних кодів, що залишилися

        Returns:
            Number of remaining backup codes / Количество оставшихся резервных кодов / Кількість резервних кодів, що залишилися
        """
        return len(self._backup_codes_hashes)

    def get_secret(self) -> Optional[str]:
        """
        Get current TOTP secret

        Получить текущий секрет TOTP
        Отримати поточний секрет TOTP

        Returns:
            Current TOTP secret or None / Текущий секрет TOTP или None / Поточний секрет TOTP або None
        """
        return self._secret

    def set_secret(self, secret: str) -> None:
        """
        Set TOTP secret from config

        Установить секрет TOTP из конфига
        Встановити секрет TOTP з конфігу

        Args:
            secret: TOTP secret string / Секрет TOTP / Секрет TOTP
        """
        from security.totp_core import TOTP, TOTPInvalidSecretError

        try:
            self._secret = secret.upper().replace(" ", "").replace("-", "")
            if self._secret:
                self._enabled = True
                self._totp_instance = TOTP(self._secret)
                if self._trusted_devices_file:
                    self._totp_instance.set_trusted_devices_file(self._trusted_devices_file)
        except (TOTPInvalidSecretError, ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to set secret / Ошибка установки секрета / Помилка встановлення секрету: {e}")
            self._enabled = False
            self._secret = None

    def set_account_name(self, name: str) -> None:
        """
        Set account name for QR code

        Установить имя аккаунта для QR-кода
        Встановити ім'я акаунта для QR-коду

        Args:
            name: Account name / Имя аккаунта / Ім'я акаунта
        """
        self._account_name = name

    def get_provisioning_uri(self) -> Optional[str]:
        """
        Get provisioning URI for current secret

        Получить URI для подготовки для текущего секрета
        Отримати URI для підготовки для поточного секрету

        Returns:
            Provisioning URI or None / URI для подготовки или None / URI для підготовки або None
        """
        from security.totp_core import TOTP

        if self._secret:
            return TOTP.get_provisioning_uri(self._secret, self._account_name, "SecurePassPro")
        return None

    def generate_new_backup_codes(self, count: int = 10, length: int = 8) -> List[str]:
        """
        Generate new backup codes

        Сгенерировать новые резервные коды
        Згенерувати нові резервні коди

        Args:
            count: Number of codes to generate / Количество кодов для генерации / Кількість кодів для генерації
            length: Length of each code / Длина каждого кода / Довжина кожного коду

        Returns:
            List of generated backup codes / Список сгенерированных резервных кодов / Список згенерованих резервних кодів

        Raises:
            TOTPError: If 2FA is not enabled or generation fails / Если 2FA не включена или генерация не удалась / Якщо 2FA не ввімкнено або генерація не вдалася
        """
        from security.totp_core import TOTP, TOTPError

        if not self._enabled:
            raise TOTPError("2FA is not enabled / 2FA не включена / 2FA не ввімкнена")
        if self._totp_instance is None:
            from security.totp_core import TOTP
            try:
                self._totp_instance = TOTP(self._secret)
            except (ValueError, TypeError, AttributeError, RuntimeError) as e:
                logger.error(f"Failed to create TOTP instance / Ошибка создания экземпляра TOTP / Помилка створення екземпляра TOTP: {e}")
                raise TOTPError(f"Cannot create TOTP instance / Ошибка создания экземпляра TOTP / Помилка створення екземпляра TOTP: {e}")
        try:
            new_codes = self._totp_instance.get_backup_codes(count, length)
            self.set_backup_codes(new_codes)
            return new_codes
        except (ValueError, TypeError, AttributeError, RuntimeError, TOTPError) as e:
            logger.error(f"Failed to generate backup codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")
            raise TOTPError(f"Cannot generate backup codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")

    def get_recovery_codes_status(self) -> Dict[str, Any]:
        """
        Get recovery codes status

        Получить статус резервных кодов
        Отримати статус резервних кодів

        Returns:
            Dictionary with recovery codes status / Словарь со статусом резервных кодов / Словник зі статусом резервних кодів
        """
        # FIXED: Calculate status directly from stored backup codes
        total = len(self._backup_codes_hashes)
        used = self._backup_codes_used_count
        return {
            "total": total + used,
            "used": used,
            "available": total,
            "max_codes": 10
        }

    def force_cache_cleanup(self) -> int:
        """
        Force cache cleanup in TOTP instance

        Принудительная очистка кэша в экземпляре TOTP
        Примусове очищення кешу в екземплярі TOTP

        Returns:
            Number of removed entries / Количество удалённых записей / Кількість видалених записів
        """
        if self._totp_instance:
            return self._totp_instance.force_cleanup()
        return 0

    def reset_rate_limit(self, source: Optional[str] = None) -> None:
        """
        Reset rate limit for TOTP verification

        Сбросить ограничение частоты для верификации TOTP
        Скинути обмеження частоти для верифікації TOTP

        Args:
            source: Source identifier or None to reset all / Идентификатор источника или None для сброса всех / Ідентифікатор джерела або None для скидання всіх
        """
        if self._totp_instance:
            self._totp_instance.reset_rate_limit(source)

    def get_rate_limit_status(self, source: str) -> Dict[str, Any]:
        """
        Get rate limit status for source

        Получить статус ограничения частоты для источника
        Отримати статус обмеження частоти для джерела

        Args:
            source: Source identifier / Идентификатор источника / Ідентифікатор джерела

        Returns:
            Dictionary with rate limit status / Словарь со статусом ограничения частоты / Словник зі статусом обмеження частоти
        """
        if self._totp_instance:
            return self._totp_instance.get_rate_limit_status(source)
        return {"attempts": 0, "max_attempts": 5, "remaining": 5, "window_seconds": 60}

    def clear_used_codes_cache(self) -> None:
        """
        Clear anti-replay cache

        Очистить кэш защиты от повторного воспроизведения
        Очистити кеш захисту від повторного відтворення
        """
        if self._totp_instance:
            self._totp_instance.clear_used_codes_cache()

    # ==================== TRUSTED DEVICES METHODS / МЕТОДЫ ДОВЕРЕННЫХ УСТРОЙСТВ / МЕТОДИ ДОВІРЕНИХ ПРИСТРОЇВ ====================

    def get_trusted_devices(self) -> List[Dict[str, Any]]:
        """
        Get list of trusted devices

        Получить список доверенных устройств
        Отримати список довірених пристроїв

        Returns:
            List of trusted devices / Список доверенных устройств / Список довірених пристроїв
        """
        if self._totp_instance:
            return self._totp_instance.get_trusted_devices()
        return []

    def generate_trusted_device_token(self, device_id: str, device_name: str) -> Optional[str]:
        """
        Generate token for trusted device

        Генерировать токен для доверенного устройства
        Згенерувати токен для довіреного пристрою

        Args:
            device_id: Unique device identifier / Уникальный идентификатор устройства / Унікальний ідентифікатор пристрою
            device_name: Human-readable device name / Человекочитаемое имя устройства / Людиночитане ім'я пристрою

        Returns:
            Generated token or None / Сгенерированный токен или None / Згенерований токен або None
        """
        if self._totp_instance:
            return self._totp_instance.generate_trusted_device_token(device_id, device_name)
        return None

    def verify_trusted_device_token(self, device_id: str, token: str) -> bool:
        """
        Verify trusted device token

        Проверить токен доверенного устройства
        Перевірити токен довіреного пристрою

        Args:
            device_id: Device identifier / Идентификатор устройства / Ідентифікатор пристрою
            token: Token to verify / Токен для проверки / Токен для перевірки

        Returns:
            True if token is valid / True если токен действителен / True якщо токен дійсний
        """
        if self._totp_instance:
            return self._totp_instance.verify_trusted_device_token(device_id, token)
        return False

    def remove_trusted_device(self, device_id: str) -> bool:
        """
        Remove trusted device

        Удалить доверенное устройство
        Видалити довірений пристрій

        Args:
            device_id: Device identifier to remove / Идентификатор устройства для удаления / Ідентифікатор пристрою для видалення

        Returns:
            True if device was removed / True если устройство удалено / True якщо пристрій видалено
        """
        if self._totp_instance:
            return self._totp_instance.remove_trusted_device(device_id)
        return False

    def set_trusted_devices_file(self, file_path: str) -> None:
        """
        Set file path for trusted devices storage

        Установить путь к файлу для хранения доверенных устройств
        Встановити шлях до файлу для зберігання довірених пристроїв

        Args:
            file_path: Path to trusted devices file / Путь к файлу доверенных устройств / Шлях до файлу довірених пристроїв
        """
        self._trusted_devices_file = file_path
        if self._totp_instance:
            self._totp_instance.set_trusted_devices_file(file_path)


# ==================== GLOBAL INSTANCE AND FUNCTIONS ====================
# ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР И ФУНКЦИИ
# ГЛОБАЛЬНИЙ ЕКЗЕМПЛЯР ТА ФУНКЦІЇ

_totp_manager = TOTPManager()


def get_totp_manager() -> TOTPManager:
    """
    Get global TOTP manager instance

    Получить глобальный экземпляр менеджера TOTP
    Отримати глобальний екземпляр менеджера TOTP

    Returns:
        Global TOTP manager instance / Глобальный экземпляр менеджера TOTP / Глобальний екземпляр менеджера TOTP
    """
    return _totp_manager


def init_totp_from_config(config) -> None:
    """
    Initialize TOTP from saved configuration

    Инициализировать TOTP из сохранённой конфигурации
    Ініціалізувати TOTP зі збереженої конфігурації

    Args:
        config: Configuration object / Объект конфигурации / Об'єкт конфігурації
    """
    try:
        if config.get("2fa_enabled", False):
            secret = config.get("2fa_secret", "")
            if secret:
                _totp_manager.set_secret(secret)
                backup_hashes = config.get("2fa_backup_hashes", [])
                if isinstance(backup_hashes, list):
                    _totp_manager._backup_codes_hashes = backup_hashes
                account = config.get("2fa_account_name", "SecurePassPro_User")
                _totp_manager.set_account_name(account)
                logger.info("TOTP initialized from config / TOTP инициализирован из конфига / TOTP ініціалізовано з конфігу")

                from utils.paths import get_config_dir
                trusted_file = os.path.join(get_config_dir(), "trusted_devices_totp.json")
                _totp_manager.set_trusted_devices_file(trusted_file)
    except (AttributeError, TypeError, ValueError, OSError, KeyError) as e:
        logger.error(f"Failed to init TOTP from config / Ошибка инициализации TOTP из конфига / Помилка ініціалізації TOTP з конфігу: {e}")


def save_totp_to_config(config) -> None:
    """
    Save TOTP state to configuration

    Сохранить состояние TOTP в конфигурацию
    Зберегти стан TOTP у конфігурацію

    Args:
        config: Configuration object / Объект конфигурации / Об'єкт конфігурації
    """
    try:
        config.set("2fa_enabled", _totp_manager.is_enabled())
        if _totp_manager.get_secret():
            config.set("2fa_secret", _totp_manager.get_secret())
        config.set("2fa_backup_hashes", _totp_manager.get_backup_codes_hashes())
        config.save()
        logger.debug("TOTP state saved to config / Состояние TOTP сохранено в конфиг / Стан TOTP збережено у конфіг")
    except (AttributeError, TypeError, OSError, KeyError, ValueError) as e:
        logger.error(f"Failed to save TOTP to config / Ошибка сохранения TOTP в конфиг / Помилка збереження TOTP у конфіг: {e}")


def is_2fa_enabled() -> bool:
    """
    Check if 2FA is enabled

    Проверить, включена ли 2FA
    Перевірити, чи ввімкнено 2FA

    Returns:
        True if 2FA is enabled / True если 2FA включена / True якщо 2FA увімкнено
    """
    return _totp_manager.is_enabled()


def generate_2fa_qr_data(account_name: str = "SecurePassPro_User") -> Tuple[str, str]:
    """
    Generate data for 2FA setup

    Сгенерировать данные для настройки 2FA
    Згенерувати дані для налаштування 2FA

    Args:
        account_name: Account name for QR code / Имя аккаунта для QR-кода / Ім'я акаунта для QR-коду

    Returns:
        Tuple of (secret, provisioning_uri) / Кортеж (секрет, URI для подготовки) / Кортеж (секрет, URI для підготовки)

    Raises:
        TOTPError: If generation fails / Если генерация не удалась / Якщо генерація не вдалася
    """
    from security.totp_core import TOTP, TOTPError

    try:
        secret = TOTP.generate_secret()
        provisioning_uri = TOTP.get_provisioning_uri(secret, account_name, "SecurePassPro")
        return secret, provisioning_uri
    except (ValueError, TypeError, AttributeError, RuntimeError, OSError) as e:
        logger.error(f"Failed to generate 2FA QR data / Ошибка генерации QR-данных 2FA / Помилка генерації QR-даних 2FA: {e}")
        raise TOTPError(f"Cannot generate QR data / Невозможно сгенерировать QR-данные / Неможливо згенерувати QR-дані: {e}")


def verify_2fa_code(code: str, source: str = "unknown") -> bool:
    """
    Verify 2FA code (simplified function)

    Проверить 2FA код (упрощённая функция)
    Перевірити 2FA код (спрощена функція)

    Args:
        code: 6-digit code to verify / 6-значный код для проверки / 6-значний код для перевірки
        source: Source identifier for rate limiting / Идентификатор источника для ограничения частоты / Ідентифікатор джерела для обмеження частоти

    Returns:
        True if code is valid / True если код действителен / True якщо код дійсний
    """
    try:
        return _totp_manager.verify_code(code, source=source)
    except (ValueError, TypeError, AttributeError, RuntimeError) as e:
        logger.error(f"2FA verification error / Ошибка верификации 2FA / Помилка верифікації 2FA: {e}")
        return False


def reset_2fa_rate_limit(source: Optional[str] = None) -> None:
    """
    Reset rate limit for 2FA

    Сбросить ограничение частоты для 2FA
    Скинути обмеження частоти для 2FA

    Args:
        source: Source identifier or None to reset all / Идентификатор источника или None для сброса всех / Ідентифікатор джерела або None для скидання всіх
    """
    _totp_manager.reset_rate_limit(source)


def get_2fa_rate_limit_status(source: str) -> Dict[str, Any]:
    """
    Get rate limit status for 2FA

    Получить статус ограничения частоты для 2FA
    Отримати статус обмеження частоти для 2FA

    Args:
        source: Source identifier / Идентификатор источника / Ідентифікатор джерела

    Returns:
        Dictionary with rate limit status / Словарь со статусом ограничения частоты / Словник зі статусом обмеження частоти
    """
    return _totp_manager.get_rate_limit_status(source)


def clear_2fa_used_codes_cache() -> None:
    """Clear anti-replay cache for 2FA / Очистить кэш защиты от повторного воспроизведения для 2FA / Очистити кеш захисту від повторного відтворення для 2FA"""
    _totp_manager.clear_used_codes_cache()


def force_2fa_cache_cleanup() -> int:
    """
    Force immediate cache cleanup for 2FA

    Принудительная немедленная очистка кэша для 2FA
    Примусове негайне очищення кешу для 2FA

    Returns:
        Number of removed entries / Количество удалённых записей / Кількість видалених записів
    """
    return _totp_manager.force_cache_cleanup()


# ==================== TRUSTED DEVICES FUNCTIONS ====================
# ФУНКЦИИ ДОВЕРЕННЫХ УСТРОЙСТВ
# ФУНКЦІЇ ДОВІРЕНИХ ПРИСТРОЇВ


def get_trusted_devices() -> List[Dict[str, Any]]:
    """
    Get list of trusted devices

    Получить список доверенных устройств
    Отримати список довірених пристроїв

    Returns:
        List of trusted devices / Список доверенных устройств / Список довірених пристроїв
    """
    return _totp_manager.get_trusted_devices()


def generate_trusted_device_token(device_id: str, device_name: str) -> Optional[str]:
    """
    Generate token for trusted device

    Сгенерировать токен для доверенного устройства
    Згенерувати токен для довіреного пристрою

    Args:
        device_id: Unique device identifier / Уникальный идентификатор устройства / Унікальний ідентифікатор пристрою
        device_name: Human-readable device name / Человекочитаемое имя устройства / Людиночитане ім'я пристрою

    Returns:
        Generated token or None / Сгенерированный токен или None / Згенерований токен або None
    """
    return _totp_manager.generate_trusted_device_token(device_id, device_name)


def verify_trusted_device_token(device_id: str, token: str) -> bool:
    """
    Verify trusted device token

    Проверить токен доверенного устройства
    Перевірити токен довіреного пристрою

    Args:
        device_id: Device identifier / Идентификатор устройства / Ідентифікатор пристрою
        token: Token to verify / Токен для проверки / Токен для перевірки

    Returns:
        True if token is valid / True если токен действителен / True якщо токен дійсний
    """
    return _totp_manager.verify_trusted_device_token(device_id, token)


def remove_trusted_device(device_id: str) -> bool:
    """
    Remove trusted device

    Удалить доверенное устройство
    Видалити довірений пристрій

    Args:
        device_id: Device identifier to remove / Идентификатор устройства для удаления / Ідентифікатор пристрою для видалення

    Returns:
        True if device was removed / True если устройство удалено / True якщо пристрій видалено
    """
    return _totp_manager.remove_trusted_device(device_id)


# ==================== RECOVERY CODES FUNCTIONS ====================
# ФУНКЦИИ РЕЗЕРВНЫХ КОДОВ
# ФУНКЦІЇ РЕЗЕРВНИХ КОДІВ


def generate_recovery_codes(count: int = 10, length: int = 8) -> List[str]:
    """
    Generate new recovery codes

    Сгенерировать новые резервные коды
    Згенерувати нові резервні коди

    Args:
        count: Number of codes to generate / Количество кодов для генерации / Кількість кодів для генерації
        length: Length of each code / Длина каждого кода / Довжина кожного коду

    Returns:
        List of generated recovery codes / Список сгенерированных резервных кодов / Список згенерованих резервних кодів
    """
    return _totp_manager.generate_new_backup_codes(count, length)


def verify_recovery_code(code: str) -> bool:
    """
    Verify a recovery code

    Проверить резервный код
    Перевірити резервний код

    Args:
        code: Recovery code to verify / Резервный код для проверки / Резервний код для перевірки

    Returns:
        True if code is valid / True если код действителен / True якщо код дійсний
    """
    return _totp_manager.verify_backup_code(code)


def get_recovery_codes_status() -> Dict[str, Any]:
    """
    Get recovery codes status

    Получить статус резервных кодов
    Отримати статус резервних кодів

    Returns:
        Dictionary with recovery codes status / Словарь со статусом резервных кодов / Словник зі статусом резервних кодів
    """
    return _totp_manager.get_recovery_codes_status()


__all__ = [
    'TOTPManager',
    'get_totp_manager',
    'init_totp_from_config',
    'save_totp_to_config',
    'is_2fa_enabled',
    'generate_2fa_qr_data',
    'verify_2fa_code',
    'reset_2fa_rate_limit',
    'get_2fa_rate_limit_status',
    'clear_2fa_used_codes_cache',
    'force_2fa_cache_cleanup',
    'get_trusted_devices',
    'generate_trusted_device_token',
    'verify_trusted_device_token',
    'remove_trusted_device',
    'generate_recovery_codes',
    'verify_recovery_code',
    'get_recovery_codes_status',

]
