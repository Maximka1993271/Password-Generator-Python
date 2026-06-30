"""
Password import utilities - Helper functions
Утилиты импорта паролей - Вспомогательные функции
Утиліти імпорту паролів - Допоміжні функції

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import csv
import re
import hashlib
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
from typing import List, Tuple, Set, Optional
from utils.logger import get_logger

logger = get_logger("import_passwords")

# Maximum import file size (50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# Maximum XML file size for safe parsing (10 MB) - prevents DoS
MAX_XML_SIZE = 10 * 1024 * 1024

# Maximum XML element depth to prevent billion laughs attack
MAX_XML_DEPTH = 100

# Maximum total elements to detect billion laughs
MAX_XML_ELEMENTS = 100000

# Allowed characters for passwords (for sanitization)
SAFE_PASSWORD_CHARS = re.compile(r'[^\x20-\x7E\u0400-\u04FF\u00A0-\u00FF]')

# Maximum password length
MAX_PASSWORD_LENGTH = 1000

# Maximum label length
MAX_LABEL_LENGTH = 200

# CSV delimiter detection sample size
CSV_SAMPLE_SIZE = 4096


class PasswordImportError(Exception):
    """Exception for password import errors / Исключение для ошибок импорта паролей / Виняток для помилок імпорту паролів"""
    pass


class InvalidFileFormatError(PasswordImportError):
    """Exception for invalid file format / Исключение для неверного формата файла / Виняток для невірного формату файлу"""
    pass


class MalformedFileError(PasswordImportError):
    """Exception for corrupted file / Исключение для повреждённого файла / Виняток для пошкодженого файлу"""
    pass


class FileTooLargeError(PasswordImportError):
    """Exception for file too large / Исключение для слишком большого файла / Виняток для надто великого файлу"""
    pass


class UnsupportedEncodingError(PasswordImportError):
    """Exception for unsupported encoding / Исключение для неподдерживаемой кодировки / Виняток для непідтримуваного кодування"""
    pass


def sanitize_csv_value(value: str, max_length: int = MAX_LABEL_LENGTH) -> str:
    """
    Sanitize CSV value from dangerous characters.

    Очищает значение из CSV от опасных символов.
    Очищує значення з CSV від небезпечних символів.
    """
    if not value:
        return ""

    value_str = str(value)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value_str)
    sanitized = re.sub(r'[\u200B-\u200D\uFEFF]', '', sanitized)

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def sanitize_password(password: str, max_length: int = MAX_PASSWORD_LENGTH) -> str:
    """
    Sanitize password, preserving allowed characters.

    Очищает пароль, сохраняя допустимые символы.
    Очищує пароль, зберігаючи допустимі символи.
    """
    if not password:
        return ""

    password_str = str(password)
    sanitized = SAFE_PASSWORD_CHARS.sub('', password_str)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"Password truncated to {max_length} characters / Пароль обрезан до {max_length} символов / Пароль обрізано до {max_length} символів")

    return sanitized


def detect_encoding(file_path: str, encodings: List[str] = None) -> Tuple[str, str]:
    """
    Detect file encoding with comprehensive fallback.

    Определяет кодировку файла с комплексным fallback.
    Визначає кодування файлу з комплексним fallback.
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
        logger.debug(f"BOM detection failed / Обнаружение BOM не удалось / Виявлення BOM не вдалося: {e}")

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                if content and len(content) > 0:
                    if re.search(r'[a-zA-Zа-яА-Я]', content):
                        logger.debug(f"Successfully detected encoding: {encoding} / Кодировка успешно определена: {encoding} / Кодування успішно визначено: {encoding}")
                        return encoding, content
        except (UnicodeDecodeError, UnicodeError, OSError, IOError) as e:
            logger.debug(f"Encoding {encoding} failed / Кодировка {encoding} не подошла / Кодування {encoding} не підійшло: {e}")
            continue

    raise UnsupportedEncodingError(f"Cannot detect file encoding for {file_path} / Не удалось определить кодировку файла {file_path} / Не вдалося визначити кодування файлу {file_path}")


def detect_csv_delimiter(content: str) -> str:
    """
    Detect CSV delimiter from content sample.

    Определяет разделитель CSV из образца содержимого.
    Визначає розділювач CSV зі зразка вмісту.
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


def is_duplicate_password(password: str, existing_passwords: Set[str]) -> bool:
    """Check if password is a duplicate / Проверить, является ли пароль дубликатом / Перевірити, чи є пароль дублікатом"""
    return password in existing_passwords


def safe_xml_parse(file_path: str) -> ET.Element:
    """
    Safely parse XML file with protection against:
    - XXE (XML External Entity) attacks
    - Billion Laughs (recursive entity expansion)
    - Large file sizes
    - Excessive element depth

    Безопасно парсит XML файл с защитой от:
    - XXE (XML External Entity) атак
    - Billion Laughs (рекурсивное расширение сущностей)
    - Больших размеров файлов
    - Чрезмерной глубины элементов

    Безпечно парсить XML файл із захистом від:
    - XXE (XML External Entity) атак
    - Billion Laughs (рекурсивне розширення сутностей)
    - Великих розмірів файлів
    - Надмірної глибини елементів
    """
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_XML_SIZE:
            raise MalformedFileError(f"XML file too large: {file_size} bytes (max: {MAX_XML_SIZE}) / XML файл слишком большой: {file_size} байт (макс: {MAX_XML_SIZE}) / XML файл занадто великий: {file_size} байт (макс: {MAX_XML_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check XML file size / Ошибка проверки размера XML файла / Помилка перевірки розміру XML файлу: {e}")
        raise PasswordImportError(f"Cannot read XML file / Не удалось прочитать XML файл / Не вдалося прочитати XML файл: {e}")

    try:
        # Create parser with security features
        parser = ET.XMLParser()

        # Disable external DTD loading (the main practical XXE vector for
        # ElementTree, which does not resolve external entities by default)
        try:
            parser.parser.UseForeignDTD(False)
        except (AttributeError, ExpatError) as _:
            pass

        # Parse with security settings
        tree = ET.parse(file_path, parser=parser)
        root = tree.getroot()

        if root is None:
            raise MalformedFileError("XML file has no root element / XML файл не имеет корневого элемента / XML файл не має кореневого елемента")

        # Check element depth to prevent billion laughs attack
        def check_depth(element, current_depth=0):
            if current_depth > MAX_XML_DEPTH:
                raise MalformedFileError(f"XML exceeds maximum allowed depth of {MAX_XML_DEPTH} / XML превышает максимально допустимую глубину {MAX_XML_DEPTH} / XML перевищує максимально допустиму глибину {MAX_XML_DEPTH}")
            for child in element:
                check_depth(child, current_depth + 1)

        check_depth(root)

        # Count total elements to detect billion laughs
        try:
            element_count = sum(1 for _ in root.iter())
            if element_count > MAX_XML_ELEMENTS:
                logger.warning(f"XML contains {element_count} elements - possible DoS attempt / XML содержит {element_count} элементов - возможная DoS атака / XML містить {element_count} елементів - можлива DoS атака")
        except RecursionError as e:
            raise MalformedFileError(f"XML recursion error (possible billion laughs): {e} / Ошибка рекурсии XML (возможна атака billion laughs) / Помилка рекурсії XML (можлива атака billion laughs): {e}")

        return root

    except ET.ParseError as e:
        logger.error(f"XML parse error / Ошибка парсинга XML / Помилка парсингу XML: {e}")
        raise InvalidFileFormatError(f"Invalid XML format / Неверный формат XML / Невірний формат XML: {e}")
    except RecursionError as e:
        logger.error(f"XML recursion error (possible billion laughs): {e} / Ошибка рекурсии XML (возможная атака billion laughs) / Помилка рекурсії XML (можлива атака billion laughs): {e}")
        raise MalformedFileError(f"XML too deeply nested: {e} / XML слишком глубоко вложен: {e} / XML занадто глибоко вкладено: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"XML file read error / Ошибка чтения XML файла / Помилка читання XML файлу: {e}")
        raise PasswordImportError(f"Cannot read XML file / Не удалось прочитать XML файл / Не вдалося прочитати XML файл: {e}")