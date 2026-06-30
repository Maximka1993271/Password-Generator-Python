"""
Import utilities - Main package
Утилиты импорта - Главный пакет
Утиліти імпорту - Головний пакет
"""
from __future__ import annotations

from utils.importer.import_base import (
    PasswordImportError,
    InvalidFileFormatError,
    MalformedFileError,
    FileTooLargeError,
    UnsupportedEncodingError,
    sanitize_password,
    sanitize_label,
    detect_encoding,
    detect_csv_delimiter,
    find_password_column,
    find_label_column,
    is_duplicate_password,
    safe_xml_parse,
    MAX_FILE_SIZE,
    MAX_XML_SIZE,
    MAX_PASSWORD_LENGTH,
    MAX_LABEL_LENGTH,
)

from utils.importer.import_json import import_from_json
from utils.importer.import_csv import import_from_csv
from utils.importer.import_keepass_xml import import_from_keepass_xml
from utils.importer.import_bitwarden_json import import_from_bitwarden_json
from utils.importer.import_1password_csv import import_from_1password_csv
from utils.importer.import_1pux import import_from_1pux
from utils.importer.import_kdbx import import_from_kdbx
from utils.importer.import_dialog import show_import_dialog


class PasswordImporter:
    """Main password importer class / Основной класс импорта паролей / Основний клас імпорту паролів"""
    
    SUPPORTED_FORMATS = {
        "CSV (.csv)": ("csv", import_from_csv),
        "JSON (.json)": ("json", import_from_json),
        "KeePass XML (.xml)": ("xml", import_from_keepass_xml),
        "Bitwarden JSON (.json)": ("bitwarden", import_from_bitwarden_json),
        "1Password CSV (.csv)": ("1password_csv", import_from_1password_csv),
        "1Password 1PUX (.1pux)": ("1pux", import_from_1pux),
        "KeePass KDBX (.kdbx)": ("kdbx", import_from_kdbx),
    }
    
    @classmethod
    def import_all(cls, parent=None, lang: str = "RU") -> None:
        """Show import dialog and import passwords"""
        from utils.importer.import_dialog import show_import_dialog
        show_import_dialog(parent, lang)


__all__ = [
    'PasswordImportError',
    'InvalidFileFormatError',
    'MalformedFileError',
    'FileTooLargeError',
    'UnsupportedEncodingError',
    'sanitize_password',
    'sanitize_label',
    'detect_encoding',
    'detect_csv_delimiter',
    'find_password_column',
    'find_label_column',
    'is_duplicate_password',
    'safe_xml_parse',
    'import_from_json',
    'import_from_csv',
    'import_from_keepass_xml',
    'import_from_bitwarden_json',
    'import_from_1password_csv',
    'import_from_1pux',
    'import_from_kdbx',
    'PasswordImporter',
    'MAX_FILE_SIZE',
    'MAX_XML_SIZE',
    'MAX_PASSWORD_LENGTH',
    'MAX_LABEL_LENGTH',
]