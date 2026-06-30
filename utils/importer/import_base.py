"""
Import utilities - Base functions (validation, encoding, sanitization)
Утилиты импорта - Базовые функции (валидация, кодировки, санитизация)
Утиліти імпорту - Базові функції (валідація, кодування, санітизація)
"""
from __future__ import annotations

import os
import re
import csv
import hashlib
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
from typing import List, Tuple, Set, Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger("import_base")

MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_XML_SIZE = 10 * 1024 * 1024
MAX_XML_DEPTH = 100
MAX_XML_ELEMENTS = 100000
SAFE_PASSWORD_CHARS = re.compile(r'[^\x20-\x7E\u0400-\u04FF\u00A0-\u00FF]')
MAX_PASSWORD_LENGTH = 1000
MAX_LABEL_LENGTH = 200
CSV_SAMPLE_SIZE = 4096

PASSWORD_PATTERNS = [
    'password', 'pass', 'pwd', 'пароль', 'п', 'heslo', 'senha', 'contraseña',
    'motdepasse', 'wachtwoord', 'hasło', 'password1', 'passwd'
]

LABEL_PATTERNS = [
    'label', 'name', 'title', 'site', 'service', 'account', 'login', 'username',
    'метка', 'название', 'сайт', 'сервис', 'аккаунт', 'логин', 'label1'
]


class PasswordImportError(Exception):
    """
    Passwordimporterror class.
    Класс PasswordImportError.
    Клас PasswordImportError.
    """
    pass


class InvalidFileFormatError(PasswordImportError):
    """
    Invalidfileformaterror class.
    Класс InvalidFileFormatError.
    Клас InvalidFileFormatError.
    """
    pass


class MalformedFileError(PasswordImportError):
    """
    Malformedfileerror class.
    Класс MalformedFileError.
    Клас MalformedFileError.
    """
    pass


class FileTooLargeError(PasswordImportError):
    """
    Filetoolargeerror class.
    Класс FileTooLargeError.
    Клас FileTooLargeError.
    """
    pass


class UnsupportedEncodingError(PasswordImportError):
    """
    Unsupportedencodingerror class.
    Класс UnsupportedEncodingError.
    Клас UnsupportedEncodingError.
    """
    pass


def sanitize_password(password: str, max_length: int = MAX_PASSWORD_LENGTH) -> str:
    """
    Handle sanitize password.
    Обработать sanitize password.
    Обробити sanitize password.
    """
    if not password:
        return ""
    password_str = str(password)
    sanitized = SAFE_PASSWORD_CHARS.sub('', password_str)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Password truncated to {max_length} characters")
    return sanitized


def sanitize_label(label: str, max_length: int = MAX_LABEL_LENGTH, default: str = "Imported") -> str:
    """
    Handle sanitize label.
    Обработать sanitize label.
    Обробити sanitize label.
    """
    if not label:
        return default
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', str(label))
    sanitized = sanitized.strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized if sanitized else default


def detect_encoding(file_path: str, encodings: List[str] = None) -> Tuple[str, str]:
    """
    Handle detect encoding.
    Обработать detect encoding.
    Обробити detect encoding.
    """
    if encodings is None:
        encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1', 'cp866', 'koi8-r', 'iso-8859-1']

    try:
        with open(file_path, 'rb') as f:
            raw = f.read(4)
            if raw.startswith(b'\xef\xbb\xbf'):
                encodings.insert(0, 'utf-8-sig')
            elif raw.startswith(b'\xff\xfe'):
                encodings.insert(0, 'utf-16-le')
            elif raw.startswith(b'\xfe\xff'):
                encodings.insert(0, 'utf-16-be')
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"BOM detection failed: {e}")

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                if content and len(content) > 0:
                    if re.search(r'[a-zA-Zа-яА-Я]', content):
                        logger.debug(f"Successfully detected encoding: {encoding}")
                        return encoding, content
        except (UnicodeDecodeError, UnicodeError, OSError, IOError) as e:
            logger.debug(f"Encoding {encoding} failed: {e}")
            continue

    raise UnsupportedEncodingError(f"Cannot detect file encoding for {file_path}")


def detect_csv_delimiter(content: str) -> str:
    """
    Handle detect csv delimiter.
    Обработать detect csv delimiter.
    Обробити detect csv delimiter.
    """
    sample = content[:CSV_SAMPLE_SIZE]
    delimiters = [',', ';', '\t', '|']
    counts = {}
    for delim in delimiters:
        counts[delim] = sample.count(delim)
    if counts:
        max_delim = max(counts, key=lambda k: counts[k])
        if counts[max_delim] > 0:
            return max_delim
    return ','


def find_password_column(fieldnames: List[str]) -> Optional[str]:
    """
    Handle find password column.
    Обработать find password column.
    Обробити find password column.
    """
    if not fieldnames:
        return None
    fieldnames_lower = [f.lower().strip() for f in fieldnames]
    for pattern in PASSWORD_PATTERNS:
        for i, fname in enumerate(fieldnames_lower):
            if fname == pattern or pattern in fname:
                return fieldnames[i]
    return None


def find_label_column(fieldnames: List[str]) -> Optional[str]:
    """
    Handle find label column.
    Обработать find label column.
    Обробити find label column.
    """
    if not fieldnames:
        return None
    fieldnames_lower = [f.lower().strip() for f in fieldnames]
    for pattern in LABEL_PATTERNS:
        for i, fname in enumerate(fieldnames_lower):
            if fname == pattern or pattern in fname:
                return fieldnames[i]
    return fieldnames[0] if fieldnames else None


def is_duplicate_password(password: str, existing_passwords: Set[str]) -> bool:
    """
    Return True if duplicate password.
    True, если duplicate password.
    True, якщо duplicate password.
    """
    return password in existing_passwords


def safe_xml_parse(file_path: str) -> ET.Element:
    """
    Handle safe xml parse.
    Обработать safe xml parse.
    Обробити safe xml parse.
    """
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_XML_SIZE:
            raise MalformedFileError(f"XML file too large: {file_size} bytes (max: {MAX_XML_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check XML file size: {e}")
        raise PasswordImportError(f"Cannot read XML file: {e}")

    try:
        parser = ET.XMLParser()
        try:
            parser.parser.UseForeignDTD(False)
        except (AttributeError, ExpatError):
            pass

        tree = ET.parse(file_path, parser=parser)
        root = tree.getroot()

        if root is None:
            raise MalformedFileError("XML file has no root element")

        def check_depth(element, current_depth=0):
            if current_depth > MAX_XML_DEPTH:
                raise MalformedFileError(f"XML exceeds maximum allowed depth of {MAX_XML_DEPTH}")
            for child in element:
                check_depth(child, current_depth + 1)

        check_depth(root)

        try:
            element_count = sum(1 for _ in root.iter())
            if element_count > MAX_XML_ELEMENTS:
                logger.warning(f"XML contains {element_count} elements - possible DoS attempt")
        except RecursionError as e:
            raise MalformedFileError(f"XML recursion error (possible billion laughs): {e}")

        return root

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        raise InvalidFileFormatError(f"Invalid XML format: {e}")
    except RecursionError as e:
        logger.error(f"XML recursion error (possible billion laughs): {e}")
        raise MalformedFileError(f"XML too deeply nested: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"XML file read error: {e}")
        raise PasswordImportError(f"Cannot read XML file: {e}")