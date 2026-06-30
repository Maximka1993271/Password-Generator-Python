from __future__ import annotations
# storage/config_transfer.py
"""
Config transfer module for Secure Pass Pro.
Модуль Config transfer для Secure Pass Pro.
Модуль Config transfer для Secure Pass Pro.
"""
"""
Config transfer module for Secure Pass Pro.
Модуль Config transfer для Secure Pass Pro.
Модуль Config transfer для Secure Pass Pro.
"""
"""
Configuration transfer methods - export, import, backup management
Методы переноса конфигурации - экспорт, импорт, управление резервными копиями
Методи перенесення конфігурації - експорт, імпорт, керування резервними копіями
"""
import json
from typing import Dict, Any, List
from storage.config_constants import logger, SCHEMA_VERSION
from storage.config_file_ops import secure_write, secure_read
from storage.config_helpers import _validate_config, _get_available_backups


class ConfigTransferMixin:
    """Configuration transfer methods (export, import, backup management)
    Методы переноса конфигурации (экспорт, импорт, управление резервными копиями)
    Методи перенесення конфігурації (експорт, імпорт, керування резервними копіями)"""

    def export(self, file_path: str) -> bool:
        """
        Export config to another file
        
        Экспортировать конфигурацию в другой файл
        Експортувати конфігурацію в інший файл
        """
        try:
            content = json.dumps(self._data, indent=2, ensure_ascii=False).encode('utf-8')
            return secure_write(file_path, content, make_hidden=False)
        except (OSError, IOError, TypeError) as e:
            logger.error(f"Config export failed / Ошибка экспорта конфигурации / Помилка експорту конфігурації: {e}")
            return False

    def import_from(self, file_path: str) -> bool:
        """
        Import config from another file with validation
        
        Импортировать конфигурацию из другого файла с проверкой
        Імпортувати конфігурацію з іншого файлу з перевіркою
        """
        try:
            content = secure_read(file_path)
            if not content:
                return False

            raw_data = json.loads(content.decode('utf-8'))
            validated_data, errors = _validate_config(raw_data)
            if errors:
                logger.warning(f"Import config has {len(errors)} errors, but imported anyway / Импортируемая конфигурация имеет {len(errors)} ошибок, но импортирована / Імпортована конфігурація має {len(errors)} помилок, але імпортована")

            self._data = validated_data
            self._data["_schema_version"] = SCHEMA_VERSION
            return self.save()
        except (OSError, IOError, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Config import failed / Ошибка импорта конфигурации / Помилка імпорту конфігурації: {e}")
            return False

    def get_backup_available(self) -> bool:
        """
        Check if backup config is available
        
        Проверить, доступна ли резервная копия конфигурации
        Перевірити, чи доступна резервна копія конфігурації
        """
        backups = _get_available_backups()
        return len(backups) > 0

    def restore_from_backup(self, backup_index: int = 0) -> bool:
        """
        Restore config from backup
        
        Восстановить конфигурацию из резервной копии
        Відновити конфігурацію з резервної копії
        """
        backups = _get_available_backups()

        if backup_index >= len(backups):
            logger.warning(f"Backup index {backup_index} out of range / Индекс резервной копии {backup_index} вне диапазона / Індекс резервної копії {backup_index} поза діапазоном")
            return False

        backup = backups[backup_index]

        try:
            with open(backup.path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            validated_data, errors = _validate_config(backup_data)
            self._data = validated_data
            self._data["_schema_version"] = SCHEMA_VERSION
            logger.info(f"Config restored from backup: {backup.path} / Конфигурация восстановлена из резервной копии: {backup.path} / Конфігурацію відновлено з резервної копії: {backup.path}")
            return self.save()
        except (OSError, IOError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Backup restore failed / Ошибка восстановления из резервной копии / Помилка відновлення з резервної копії: {e}")
            return False

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Список доступных резервных копий
        Список доступних резервних копій
        """
        return [b.to_dict() for b in _get_available_backups()]