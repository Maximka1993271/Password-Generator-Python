"""
Export utilities - Main package
Утилиты экспорта - Главный пакет
Утиліти експорту - Головний пакет
"""
from __future__ import annotations

from utils.export.export_base import (
    ExportError,
    ExportEncryptionError,
    ValidationError,
    sanitize_export_data,
    validate_export_password,
    encrypt_export_file,
    verify_export_integrity,
    _csv_safe_value,
    MAX_EXPORT_SIZE,
    MAX_ENCRYPT_PASSWORD_LENGTH,
    MIN_ENCRYPT_PASSWORD_LENGTH,
)

from utils.export.export_json import export_json
from utils.export.export_csv import export_csv
from utils.export.export_html import export_html
from utils.export.export_dialog import show_export_dialog


class DataExporter:
    """Data export to JSON, CSV, HTML with advanced features (backward compatibility)"""
    
    @staticmethod
    def export_json(data, file_path, fields=None, encrypt=False, password=None) -> Any:
        """
        Handle export json.
        Обработать export json.
        Обробити export json.
        """
        return export_json(data, file_path, fields, encrypt, password)
    
    @staticmethod
    def export_csv(data, file_path, fields=None, encoding='utf-8-sig') -> Any:
        """
        Handle export csv.
        Обработать export csv.
        Обробити export csv.
        """
        return export_csv(data, file_path, fields, encoding)
    
    @staticmethod
    def export_html(data, file_path, lang="RU", fields=None) -> Any:
        """
        Handle export html.
        Обработать export html.
        Обробити export html.
        """
        return export_html(data, file_path, lang, fields)
    
    @staticmethod
    def show_export_dialog(data, parent, lang="RU") -> None:
        """
        Show export dialog.
        Показать export dialog.
        Показати export dialog.
        """
        return show_export_dialog(data, parent, lang)
    
    @staticmethod
    def export_all(data, parent, lang="RU") -> Any:
        """
        Handle export all.
        Обработать export all.
        Обробити export all.
        """
        return show_export_dialog(data, parent, lang)


__all__ = [
    'ExportError',
    'ExportEncryptionError',
    'ValidationError',
    'sanitize_export_data',
    'validate_export_password',
    'encrypt_export_file',
    'verify_export_integrity',
    '_csv_safe_value',
    'export_json',
    'export_csv',
    'export_html',
    'show_export_dialog',
    'DataExporter',
    'MAX_EXPORT_SIZE',
    'MAX_ENCRYPT_PASSWORD_LENGTH',
    'MIN_ENCRYPT_PASSWORD_LENGTH',
]
