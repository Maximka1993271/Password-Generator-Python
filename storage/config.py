"""
Configuration manager with schema validation, corruption recovery, and backup.
PORTABLE VERSION - all data is stored in the program's folder.
3 LANGUAGE SUPPORT: RU, EN, UA.

Менеджер конфигурации с проверкой схемы, восстановлением и резервным копированием.
ПОРТАТИВНАЯ ВЕРСИЯ - все данные хранятся в папке программы.
ПОДДЕРЖКА 3 ЯЗЫКОВ: RU, EN, UA.

Менеджер конфігурації з перевіркою схеми, відновленням та резервним копіюванням.
ПОРТАТИВНА ВЕРСІЯ - всі дані зберігаються в папці програми.
ПІДТРИМКА 3 МОВ: RU, EN, UA.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional, Union, cast
import threading
import json
import os

# ==================== IMPORTS ====================

# Paths
from storage.config_paths import (
    get_program_dir,
    get_config_dir,
    get_config_file,
    hide_dir
)

# File operations
from storage.config_file_ops import secure_write, secure_read

# Constants and schema
from storage.config_constants import (
    logger,
    SCHEMA_VERSION,
    CONFIG_SCHEMA,
    SENSITIVE_CONFIG_KEYS,
    _is_sensitive_config_key
)

# Encryption utilities
from storage.config_crypto import (
    _get_config_encryption_key,
    _encrypt_config_value,
    _decrypt_config_value
)

# Backup metadata
from storage.config_backup import ConfigBackup

# Exceptions
from storage.config_exceptions import (
    ConfigError,
    ConfigCorruptionError,
    ConfigMigrationError,
    ConfigValidationError
)

# Helper functions
from storage.config_helpers import (
    _atomic_write_json,
    _create_backup,
    _cleanup_old_backups,
    _get_available_backups,
    _validate_config,
    _migrate_config,
    _repair_config,
    _restore_from_backup
)

# Schema migrations
from storage.config_migrations import SCHEMA_MIGRATIONS, _save_config_on_exit

# ==================== MIXINS ====================

from storage.config_base import ConfigBase
from storage.config_accessors import ConfigAccessorsMixin
from storage.config_transfer import ConfigTransferMixin
from storage.config_2fa import Config2FAMixin


# ==================== MAIN CONFIG CLASS ====================

class Config(ConfigBase, ConfigAccessorsMixin, ConfigTransferMixin, Config2FAMixin):
    """
    Application settings manager with schema validation, recovery, and backup.
    
    Менеджер настроек приложения с проверкой схемы, восстановлением и резервным копированием.
    Менеджер налаштувань додатку з перевіркою схеми, відновленням та резервним копіюванням.
    """

    # ==================== SINGLETON ====================

    _instance: Optional['Config'] = None
    _lock: threading.RLock = threading.RLock()

    def __new__(cls) -> 'Config':
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._config_file = get_config_file()
                    cls._instance._backup_path = cls._instance._config_file + ".backup"
                    cls._instance._load()
        return cls._instance

    # ==================== PUBLIC METHODS ====================

    def get_schema_version(self) -> int:
        """Get current schema version."""
        return self._data.get("_schema_version", 1)

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information for UI."""
        info: Dict[str, Any] = {}
        for key, schema in CONFIG_SCHEMA.items():
            info[key] = {
                "type": schema["type"].__name__,
                "default": schema["default"],
                "current": self._data.get(key, schema["default"]),
                "encrypted": schema.get("encrypted", False)
            }
            if "allowed" in schema:
                info[key]["allowed"] = schema["allowed"]
            if "min" in schema:
                info[key]["min"] = schema["min"]
            if "max" in schema:
                info[key]["max"] = schema["max"]
        return info

    def get_validation_errors(self) -> List[str]:
        """Get last validation errors."""
        return self._validation_errors.copy()

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate entire config."""
        _, errors = _validate_config(self._data)
        return len(errors) == 0, errors

    def get_all(self) -> Dict[str, Any]:
        """Get a copy of all config data."""
        return self._data.copy()

    def has_key(self, key: str) -> bool:
        """Check if key exists in config."""
        return key in self._data

    def get_version(self) -> int:
        """Get current config schema version."""
        return self._data.get("_schema_version", 1)

    # ==================== BACKUP METHODS ====================

    def get_backup_available(self) -> bool:
        """Check if backup config is available."""
        backups: List[ConfigBackup] = _get_available_backups()
        return len(backups) > 0

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups."""
        return [b.to_dict() for b in _get_available_backups()]

    def restore_from_backup(self, backup_index: int = 0) -> bool:
        """Restore config from backup."""
        backups: List[ConfigBackup] = _get_available_backups()

        if backup_index >= len(backups):
            logger.warning(f"Backup index {backup_index} out of range")
            return False

        backup: ConfigBackup = backups[backup_index]

        try:
            with open(backup.path, 'r', encoding='utf-8') as f:
                backup_data: Dict[str, Any] = json.load(f)

            validated_data, errors = _validate_config(backup_data)
            self._data = validated_data
            self._data["_schema_version"] = SCHEMA_VERSION
            logger.info(f"Config restored from backup: {backup.path}")
            return self.save()
        except (OSError, IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Backup restore failed: {e}")
            return False

    # ==================== EXPORT/IMPORT METHODS ====================

    def export(self, file_path: str) -> bool:
        """Export config to another file."""
        try:
            content: bytes = json.dumps(self._data, indent=2, ensure_ascii=False).encode('utf-8')
            return secure_write(file_path, content, make_hidden=False)
        except (OSError, IOError, TypeError) as e:
            logger.error(f"Config export failed: {e}")
            return False

    def import_from(self, file_path: str) -> bool:
        """Import config from another file with validation."""
        try:
            content: Optional[bytes] = secure_read(file_path)
            if not content:
                return False

            raw_data: Dict[str, Any] = json.loads(content.decode('utf-8'))
            validated_data, errors = _validate_config(raw_data)
            if errors:
                logger.warning(f"Import config has {len(errors)} errors, but imported anyway")

            self._data = validated_data
            self._data["_schema_version"] = SCHEMA_VERSION
            return self.save()
        except (OSError, IOError, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Config import failed: {e}")
            return False

    # ==================== 2FA METHODS ====================

    def is_2fa_enabled(self) -> bool:
        """Check if 2FA is enabled."""
        return self.get("2fa_enabled", False)

    def get_2fa_secret(self) -> str:
        """Return 2FA secret (automatically decrypted)."""
        value: str = self._data.get("2fa_secret", "")
        if value and isinstance(value, str) and value.startswith("[enc"):
            return _decrypt_config_value(value)
        return value

    def get_2fa_backup_hashes(self) -> List[str]:
        """Return backup code hashes."""
        return self.get("2fa_backup_hashes", [])

    def get_2fa_account_name(self) -> str:
        """Return account name for 2FA."""
        return self.get("2fa_account_name", "")

    def is_2fa_setup_completed(self) -> bool:
        """Check if 2FA setup is completed."""
        return self.get("2fa_setup_completed", False)

    def set_2fa_enabled(self, enabled: bool) -> bool:
        """Enable/disable 2FA."""
        return self.set("2fa_enabled", enabled)

    def set_2fa_secret(self, secret: str) -> bool:
        """Set 2FA secret (will be encrypted automatically)."""
        if secret and not secret.startswith("[enc"):
            secret = _encrypt_config_value(secret)
        return self.set("2fa_secret", secret)

    def set_2fa_backup_hashes(self, hashes: List[str]) -> bool:
        """Set backup code hashes."""
        return self.set("2fa_backup_hashes", hashes)

    def set_2fa_account_name(self, name: str) -> bool:
        """Set account name for 2FA."""
        return self.set("2fa_account_name", name)

    def set_2fa_setup_completed(self, completed: bool) -> bool:
        """Mark 2FA setup as completed."""
        return self.set("2fa_setup_completed", completed)

    def set_2fa_last_verified(self, timestamp: Optional[str] = None) -> bool:
        """Set last 2FA verification time."""
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
        return self.set("2fa_last_verified", timestamp)

    def clear_2fa(self) -> bool:
        """Clear all 2FA settings."""
        success: bool = True
        success &= self.set("2fa_enabled", False)
        success &= self.set("2fa_secret", "")
        success &= self.set("2fa_backup_hashes", [])
        success &= self.set("2fa_setup_completed", False)
        success &= self.set("2fa_last_verified", "")
        return success

    # ==================== BACKWARD COMPATIBILITY ====================

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get singleton instance (backward compatibility)."""
        return cls()


# ==================== EXPORTS ====================

__all__: List[str] = [
    'Config',
    'ConfigError',
    'ConfigCorruptionError',
    'ConfigMigrationError',
    'ConfigValidationError',
    'get_config_file',
    'get_config_dir',
    'get_program_dir',

]
