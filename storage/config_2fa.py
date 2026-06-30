from __future__ import annotations
# storage/config_2fa.py
"""
Config 2fa module for Secure Pass Pro.
Модуль Config 2fa для Secure Pass Pro.
Модуль Config 2fa для Secure Pass Pro.
"""
"""
Config 2fa module for Secure Pass Pro.
Модуль Config 2fa для Secure Pass Pro.
Модуль Config 2fa для Secure Pass Pro.
"""
"""
2FA configuration methods for Config class
Методы 2FA для класса Config
Методи 2FA для класу Config

100% ORIGINAL CODE - DO NOT MODIFY
Copied from storage/config.py

100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
Скопировано из storage/config.py

100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
Скопійовано з storage/config.py
"""

from typing import List, Optional
from datetime import datetime

from storage.config_crypto import _encrypt_config_value, _decrypt_config_value


class Config2FAMixin:
    """
    2FA configuration methods mixin for Config class

    Миксин методов 2FA для класса Config
    Міксин методів 2FA для класу Config
    """

    # ==================== 2FA METHODS ====================

    def is_2fa_enabled(self) -> bool:
        """
        Check if 2FA is enabled

        Проверяет, включена ли 2FA
        Перевіряє, чи увімкнено 2FA
        """
        return self.get("2fa_enabled", False)

    def get_2fa_secret(self) -> str:
        """
        Return 2FA secret (automatically decrypted).

        Возвращает секрет 2FA (автоматически дешифруется).
        Повертає секрет 2FA (автоматично дешифрується).
        """
        value = self._data.get("2fa_secret", "")
        if value and isinstance(value, str) and value.startswith("[enc"):
            return _decrypt_config_value(value)
        return value

    def get_2fa_backup_hashes(self) -> List[str]:
        """
        Return backup code hashes

        Возвращает хеши резервных кодов
        Повертає хеші резервних кодів
        """
        return self.get("2fa_backup_hashes", [])

    def get_2fa_account_name(self) -> str:
        """
        Return account name for 2FA

        Возвращает имя аккаунта для 2FA
        Повертає ім'я акаунта для 2FA
        """
        return self.get("2fa_account_name", "")

    def is_2fa_setup_completed(self) -> bool:
        """
        Check if 2FA setup is completed

        Проверяет, завершена ли настройка 2FA
        Перевіряє, чи завершено налаштування 2FA
        """
        return self.get("2fa_setup_completed", False)

    def set_2fa_enabled(self, enabled: bool) -> bool:
        """
        Enable/disable 2FA

        Включает/выключает 2FA
        Увімкнює/вимикає 2FA
        """
        return self.set("2fa_enabled", enabled)

    def set_2fa_secret(self, secret: str) -> bool:
        """
        Set 2FA secret (will be encrypted automatically)

        Устанавливает секрет 2FA (будет зашифрован автоматически)
        Встановлює секрет 2FA (буде зашифровано автоматично)
        """
        if secret and not secret.startswith("[enc"):
            secret = _encrypt_config_value(secret)
        return self.set("2fa_secret", secret)

    def set_2fa_backup_hashes(self, hashes: List[str]) -> bool:
        """
        Set backup code hashes

        Устанавливает хеши резервных кодов
        Встановлює хеші резервних кодів
        """
        return self.set("2fa_backup_hashes", hashes)

    def set_2fa_account_name(self, name: str) -> bool:
        """
        Set account name for 2FA

        Устанавливает имя аккаунта для 2FA
        Встановлює ім'я акаунта для 2FA
        """
        return self.set("2fa_account_name", name)

    def set_2fa_setup_completed(self, completed: bool) -> bool:
        """
        Mark 2FA setup as completed

        Отмечает завершение настройки 2FA
        Позначає завершення налаштування 2FA
        """
        return self.set("2fa_setup_completed", completed)

    def set_2fa_last_verified(self, timestamp: str = None) -> bool:
        """
        Set last 2FA verification time

        Устанавливает время последней верификации 2FA
        Встановлює час останньої верифікації 2FA
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        return self.set("2fa_last_verified", timestamp)

    def clear_2fa(self) -> bool:
        """
        Clear all 2FA settings

        Очищает все 2FA настройки
        Очищує всі 2FA налаштування
        """
        success = True
        success &= self.set("2fa_enabled", False)
        success &= self.set("2fa_secret", "")
        success &= self.set("2fa_backup_hashes", [])
        success &= self.set("2fa_setup_completed", False)
        success &= self.set("2fa_last_verified", "")
        return success


__all__ = [
    'Config2FAMixin',

]
