"""
Password import utilities for CSV, JSON, KeePass XML

Утилиты импорта паролей из CSV, JSON, KeePass XML
Утиліти імпорту паролів з CSV, JSON, KeePass XML
"""
from __future__ import annotations
import json
import csv
import xml.etree.ElementTree as ET
import os
import sqlite3
import datetime
import re
from typing import List, Dict, Any, Tuple
from tkinter import filedialog
from utils.logger import get_logger

logger = get_logger("import")

# Maximum file size for import (10 MB)
# Максимальный размер файла для импорта (10 MB)
# Максимальний розмір файлу для імпорту (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file extensions for import
# Допустимые расширения файлов для импорта
# Допустимі розширення файлів для імпорту
ALLOWED_EXTENSIONS = {
    "json": [".json"],
    "csv": [".csv"],
    "keepass": [".xml", ".kdbx"],
    "bitwarden": [".json"],
    "onepassword": [".csv", ".1pux"]
}

# Maximum password length
# Максимальная длина пароля
# Максимальна довжина пароля
MAX_PASSWORD_LENGTH = 1000

# Maximum label length
# Максимальная длина метки
# Максимальна довжина мітки
MAX_LABEL_LENGTH = 200


class ImportError(Exception):
    """Exception for import errors / Исключение для ошибок импорта / Виняток для помилок імпорту"""
    pass


class InvalidFileFormatError(ImportError):
    """Exception for invalid file format / Исключение для неверного формата файла / Виняток для невірного формату файлу"""
    pass


class FileTooLargeError(ImportError):
    """Exception for file too large / Исключение для слишком большого файла / Виняток для надто великого файлу"""
    pass


class MalformedFileError(ImportError):
    """Exception for malformed file / Исключение для повреждённого файла / Виняток для пошкодженого файлу"""
    pass


class UnsupportedEncodingError(ImportError):
    """Exception for unsupported encoding / Исключение для неподдерживаемой кодировки / Виняток для непідтримуваного кодування"""
    pass


def validate_file_extension(file_path: str, expected_format: str) -> bool:
    """
    Validate file extension against expected format.

    Проверяет расширение файла на соответствие ожидаемому формату.
    Перевіряє розширення файлу на відповідність очікуваному формату.

    Args:
        file_path: Path to file / Путь к файлу / Шлях до файлу
        expected_format: Expected format (json, csv, keepass, etc.) / Ожидаемый формат / Очікуваний формат

    Returns:
        True if extension is valid / True если расширение допустимо / True якщо розширення допустиме
    """
    ext = os.path.splitext(file_path)[1].lower()
    allowed = ALLOWED_EXTENSIONS.get(expected_format, [])
    return ext in allowed


def validate_file_size(file_path: str) -> bool:
    """
    Validate file size is within limits.

    Проверяет, что размер файла не превышает лимит.
    Перевіряє, що розмір файлу не перевищує ліміт.

    Args:
        file_path: Path to file / Путь к файлу / Шлях до файлу

    Returns:
        True if file size is acceptable / True если размер допустим / True якщо розмір допустимий
    """
    try:
        size = os.path.getsize(file_path)
        if size > MAX_FILE_SIZE:
            logger.error(f"File too large: {size} bytes (max: {MAX_FILE_SIZE}) / Файл слишком большой: {size} байт (макс: {MAX_FILE_SIZE}) / Файл занадто великий: {size} байт (макс: {MAX_FILE_SIZE})")
            return False
        return True
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        return False


def detect_encoding(file_path: str) -> Tuple[str, str]:
    """
    Detect file encoding with multiple fallbacks.

    Определяет кодировку файла с несколькими fallback.
    Визначає кодування файлу з кількома fallback.

    Returns:
        (encoding, content) - encoding and file content
        (encoding, content) - кодировка и содержимое файла
        (encoding, content) - кодування та вміст файлу
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp1251', 'latin-1', 'cp866', 'koi8-r']

    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                # Basic sanity check / Базовая проверка / Базова перевірка
                if content and len(content) > 0:
                    logger.debug(f"Successfully read file with encoding: {encoding} / Файл успешно прочитан с кодировкой: {encoding} / Файл успішно прочитано з кодуванням: {encoding}")
                    return encoding, content
        except (UnicodeDecodeError, UnicodeError, OSError, IOError) as e:
            logger.debug(f"Failed to read with {encoding}: {e} / Не удалось прочитать с {encoding} / Не вдалося прочитати з {encoding}")
            continue

    raise UnsupportedEncodingError(f"Could not detect file encoding for {file_path} / Не удалось определить кодировку файла {file_path} / Не вдалося визначити кодування файлу {file_path}")


def sanitize_imported_password(password: str) -> str:
    """
    Sanitize imported password (remove control characters, limit length).

    Очищает импортированный пароль (удаляет управляющие символы, ограничивает длину).
    Очищує імпортований пароль (видаляє керуючі символи, обмежує довжину).

    Args:
        password: Raw password / Исходный пароль / Вихідний пароль

    Returns:
        Sanitized password / Очищенный пароль / Очищений пароль
    """
    if not password:
        return ""

    # Remove control characters (except space, tab, newline)
    # Удаляем управляющие символы (кроме пробела, табуляции, перевода строки)
    # Видаляємо керуючі символи (крім пробілу, табуляції, переводу рядка)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(password))

    # Limit length / Ограничиваем длину / Обмежуємо довжину
    if len(sanitized) > MAX_PASSWORD_LENGTH:
        sanitized = sanitized[:MAX_PASSWORD_LENGTH]
        logger.warning(f"Password truncated to {MAX_PASSWORD_LENGTH} characters / Пароль обрезан до {MAX_PASSWORD_LENGTH} символов / Пароль обрізано до {MAX_PASSWORD_LENGTH} символів")

    return sanitized


def sanitize_imported_label(label: str) -> str:
    """
    Sanitize imported label.

    Очищает импортированную метку.
    Очищує імпортовану мітку.

    Args:
        label: Raw label / Исходная метка / Вихідна мітка

    Returns:
        Sanitized label / Очищенная метка / Очищена мітка
    """
    if not label:
        return "Imported / Импортировано / Імпортовано"

    # Remove control characters / Удаляем управляющие символы / Видаляємо керуючі символи
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', str(label))

    # Remove leading/trailing whitespace / Удаляем пробелы в начале и конце / Видаляємо пробіли на початку та в кінці
    sanitized = sanitized.strip()

    # Limit length / Ограничиваем длину / Обмежуємо довжину
    if len(sanitized) > MAX_LABEL_LENGTH:
        sanitized = sanitized[:MAX_LABEL_LENGTH]

    return sanitized if sanitized else "Imported / Импортировано / Імпортовано"


def safe_xml_parse(file_path: str) -> ET.Element:
    """
    Safely parse XML file (with protection against billion laughs attack).

    Безопасно парсит XML файл (с защитой от billion laughs атаки).
    Безпечно парсить XML файл (з захистом від billion laughs атаки).

    Args:
        file_path: Path to XML file / Путь к XML файлу / Шлях до XML файлу

    Returns:
        Root element / Корневой элемент / Кореневий елемент
    """
    try:
        # Parse with security features / Парсим с функциями безопасности / Парсимо з функціями безпеки
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Basic validation / Базовая валидация / Базова валідація
        if root is None:
            raise MalformedFileError("XML file has no root element / XML файл не имеет корневого элемента / XML файл не має кореневого елемента")

        return root
    except ET.ParseError as e:
        logger.error(f"XML parse error / Ошибка парсинга XML / Помилка парсингу XML: {e}")
        raise InvalidFileFormatError(f"Invalid XML format: {e} / Неверный формат XML: {e} / Невірний формат XML: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"XML file read error / Ошибка чтения XML файла / Помилка читання XML файлу: {e}")
        raise ImportError(f"Cannot read XML file / Не удалось прочитать XML файл / Не вдалося прочитати XML файл: {e}")


def safe_json_parse(content: str) -> Dict[str, Any]:
    """
    Safely parse JSON content.

    Безопасно парсит JSON содержимое.
    Безпечно парсить JSON вміст.

    Args:
        content: JSON string / JSON строка / JSON рядок

    Returns:
        Parsed JSON object / Распарсенный JSON объект / Розпарсений JSON об'єкт
    """
    try:
        # Remove BOM if present / Удаляем BOM если есть / Видаляємо BOM якщо є
        if content.startswith('\ufeff'):
            content = content[1:]

        # Check if content looks like JSON / Проверяем, похоже ли содержимое на JSON / Перевіряємо, чи схожий вміст на JSON
        content_stripped = content.strip()
        if not (content_stripped.startswith('{') or content_stripped.startswith('[')):
            raise InvalidFileFormatError("Content does not appear to be valid JSON / Содержимое не похоже на корректный JSON / Вміст не схожий на коректний JSON")

        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error / Ошибка декодирования JSON / Помилка декодування JSON: {e}")
        raise InvalidFileFormatError(f"Invalid JSON format: {e} / Неверный формат JSON: {e} / Невірний формат JSON: {e}")
    except (TypeError, ValueError) as e:
        logger.error(f"JSON parsing error / Ошибка парсинга JSON / Помилка парсингу JSON: {e}")
        raise InvalidFileFormatError(f"JSON parsing error / Ошибка парсинга JSON / Помилка парсингу JSON: {e}")


class PasswordImporter:
    """Import passwords from various formats
    Импорт паролей из различных форматов
    Імпорт паролів з різних форматів"""

    @staticmethod
    def import_from_json(file_path: str) -> List[Dict[str, Any]]:
        """Import from JSON format with validation
        Импорт из JSON формата с валидацией
        Імпорт з JSON формату з валідацією"""
        # Validate file / Проверяем файл / Перевіряємо файл
        if not os.path.exists(file_path):
            raise ImportError(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")

        if not validate_file_extension(file_path, "json"):
            logger.warning(f"File {file_path} does not have .json extension / Файл {file_path} не имеет расширения .json / Файл {file_path} не має розширення .json")

        if not validate_file_size(file_path):
            raise FileTooLargeError(f"File too large: {file_path} / Файл слишком большой: {file_path} / Файл занадто великий: {file_path}")

        try:
            # Detect encoding / Определяем кодировку / Визначаємо кодування
            encoding, content = detect_encoding(file_path)
            logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

            # Parse JSON / Парсим JSON / Парсимо JSON
            data = safe_json_parse(content)

            passwords = []

            if isinstance(data, list):
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dictionary item at index {i} / Пропуск элемента не словаря на индексе {i} / Пропуск елемента не словника на індексі {i}")
                        continue

                    label = sanitize_imported_label(item.get('label', item.get('name', '')))
                    password = sanitize_imported_password(item.get('password', item.get('pwd', '')))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password:
                        passwords.append({
                            'label': label if label else f"Imported_{i+1} / Импортировано_{i+1} / Імпортовано_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })

            elif isinstance(data, dict):
                # Secure Pass Pro export format / Формат экспорта Secure Pass Pro / Формат експорту Secure Pass Pro
                items = data.get('passwords', data.get('items', []))
                if not isinstance(items, list):
                    raise InvalidFileFormatError("Invalid JSON structure: 'passwords' or 'items' must be a list / Неверная структура JSON: 'passwords' или 'items' должны быть списком / Невірна структура JSON: 'passwords' або 'items' повинні бути списком")

                for i, item in enumerate(items):
                    if not isinstance(item, dict):
                        continue

                    label = sanitize_imported_label(item.get('label', item.get('name', '')))
                    password = sanitize_imported_password(item.get('password', item.get('pwd', '')))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password:
                        passwords.append({
                            'label': label if label else f"Imported_{i+1} / Импортировано_{i+1} / Імпортовано_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })
            else:
                raise InvalidFileFormatError(f"Unexpected JSON type: {type(data).__name__} / Неожиданный тип JSON: {type(data).__name__} / Неочікуваний тип JSON: {type(data).__name__}")

            logger.info(f"Imported {len(passwords)} passwords from JSON / Импортировано {len(passwords)} паролей из JSON / Імпортовано {len(passwords)} паролів з JSON")
            return passwords

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
            raise ImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
        except (InvalidFileFormatError, FileTooLargeError) as e:
            raise
        except (UnsupportedEncodingError, ValueError, TypeError) as e:
            logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
            raise ImportError(f"Import failed / Ошибка импорта / Помилка імпорту: {e}")

    @staticmethod
    def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
        """Import from CSV format with sanitization
        Импорт из CSV формата с санитизацией
        Імпорт з CSV формату з санітизацією"""
        # Validate file / Проверяем файл / Перевіряємо файл
        if not os.path.exists(file_path):
            raise ImportError(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")

        if not validate_file_extension(file_path, "csv"):
            logger.warning(f"File {file_path} does not have .csv extension / Файл {file_path} не имеет расширения .csv / Файл {file_path} не має розширення .csv")

        if not validate_file_size(file_path):
            raise FileTooLargeError(f"File too large: {file_path} / Файл слишком большой: {file_path} / Файл занадто великий: {file_path}")

        try:
            # Detect encoding / Определяем кодировку / Визначаємо кодування
            encoding, content = detect_encoding(file_path)
            logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

            passwords = []
            line_number = 0

            # Use StringIO for already read content / Используем StringIO для уже прочитанного содержимого / Використовуємо StringIO для вже прочитаного вмісту
            from io import StringIO
            f = StringIO(content)

            # Detect delimiter / Определяем разделитель / Визначаємо розділювач
            sample = content[:1024]
            delimiter = ','
            if ';' in sample and ',' not in sample:
                delimiter = ';'
            elif '\t' in sample:
                delimiter = '\t'

            reader = csv.DictReader(f, delimiter=delimiter)
            fieldnames = reader.fieldnames or []

            if not fieldnames:
                raise InvalidFileFormatError("CSV file has no headers / CSV файл не имеет заголовков / CSV файл не має заголовків")

            # Determine columns / Определяем колонки / Визначаємо колонки
            label_col = None
            pwd_col = None
            date_col = None
            notes_col = None

            for col in fieldnames:
                col_lower = col.lower().strip()
                if 'label' in col_lower or 'name' in col_lower or 'title' in col_lower:
                    label_col = col
                elif 'password' in col_lower or 'pwd' in col_lower or 'pass' in col_lower:
                    pwd_col = col
                elif 'created' in col_lower or 'date' in col_lower:
                    date_col = col
                elif 'notes' in col_lower or 'comment' in col_lower:
                    notes_col = col

            # Fallback: take first columns / Fallback: берём первые колонки / Fallback: беремо перші колонки
            if label_col is None and len(fieldnames) > 0:
                label_col = fieldnames[0]
                logger.debug(f"Using first column as label: {label_col} / Используем первую колонку как метку: {label_col} / Використовуємо першу колонку як мітку: {label_col}")
            if pwd_col is None and len(fieldnames) > 1:
                pwd_col = fieldnames[1]
                logger.debug(f"Using second column as password: {pwd_col} / Используем вторую колонку как пароль: {pwd_col} / Використовуємо другу колонку як пароль: {pwd_col}")

            if pwd_col is None:
                raise InvalidFileFormatError("Cannot find password column in CSV / Не удаётся найти колонку с паролями в CSV / Не вдається знайти колонку з паролями в CSV")

            for row in reader:
                line_number += 1
                try:
                    label = row.get(label_col, '') if label_col else ''
                    password = row.get(pwd_col, '') if pwd_col else ''
                    created = row.get(date_col, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')) if date_col else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    notes = row.get(notes_col, '')[:500] if notes_col else ''

                    # Sanitize / Санитизация / Санітизація
                    label = sanitize_imported_label(label)
                    password = sanitize_imported_password(password)

                    if password:
                        passwords.append({
                            'label': label if label else f"Imported_{line_number} / Импортировано_{line_number} / Імпортовано_{line_number}",
                            'password': password,
                            'created': created[:19] if len(created) > 19 else created,
                            'notes': notes
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing CSV line {line_number}: {e} / Ошибка обработки строки CSV {line_number} / Помилка обробки рядка CSV {line_number}")
                    continue

            logger.info(f"Imported {len(passwords)} passwords from CSV (encoding: {encoding}) / Импортировано {len(passwords)} паролей из CSV (кодировка: {encoding}) / Імпортовано {len(passwords)} паролів з CSV (кодування: {encoding})")
            return passwords

        except csv.Error as e:
            logger.error(f"CSV parse error at line {line_number}: {e} / Ошибка парсинга CSV на строке {line_number} / Помилка парсингу CSV на рядку {line_number}")
            raise InvalidFileFormatError(f"CSV parsing error / Ошибка парсинга CSV / Помилка парсингу CSV: {e}")
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
            raise ImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
        except (UnsupportedEncodingError, ValueError, TypeError) as e:
            logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
            raise ImportError(f"Import failed / Ошибка импорта / Помилка імпорту: {e}")

    @staticmethod
    def import_from_keepass_xml(file_path: str) -> List[Dict[str, Any]]:
        """Import from KeePass XML format with safe parsing
        Импорт из KeePass XML формата с безопасным парсингом
        Імпорт з KeePass XML формату з безпечним парсингом"""
        # Validate file / Проверяем файл / Перевіряємо файл
        if not os.path.exists(file_path):
            raise ImportError(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")

        if not validate_file_extension(file_path, "keepass"):
            logger.warning(f"File {file_path} does not have .xml or .kdbx extension / Файл {file_path} не имеет расширения .xml или .kdbx / Файл {file_path} не має розширення .xml або .kdbx")

        if not validate_file_size(file_path):
            raise FileTooLargeError(f"File too large: {file_path} / Файл слишком большой: {file_path} / Файл занадто великий: {file_path}")

        try:
            # Safe XML parsing / Безопасный парсинг XML / Безпечний парсинг XML
            root = safe_xml_parse(file_path)

            passwords = []

            # Find entry elements / Ищем элементы entry / Шукаємо елементи entry
            entries = root.findall('.//Entry') or root.findall('.//entry')

            for i, entry in enumerate(entries):
                try:
                    title_elem = entry.find('.//Title') or entry.find('.//title')
                    password_elem = entry.find('.//Password') or entry.find('.//password')
                    username_elem = entry.find('.//UserName') or entry.find('.//username')
                    url_elem = entry.find('.//URL') or entry.find('.//url')
                    notes_elem = entry.find('.//Notes') or entry.find('.//notes')

                    title = title_elem.text if title_elem is not None else ''
                    password = password_elem.text if password_elem is not None else ''
                    username = username_elem.text if username_elem is not None else ''
                    url = url_elem.text if url_elem is not None else ''
                    notes = notes_elem.text if notes_elem is not None else ''

                    if password:
                        # Sanitize / Санитизация / Санітизація
                        password = sanitize_imported_password(password)
                        label = sanitize_imported_label(title) if title else f"KeePass_{i+1}"

                        if username:
                            label += f" ({sanitize_imported_label(username)})"
                        if url:
                            label += f" - {url[:100]}"

                        passwords.append({
                            'label': label[:MAX_LABEL_LENGTH],
                            'password': password,
                            'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'notes': notes[:500] if notes else ''
                        })
                except (AttributeError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing KeePass entry {i}: {e} / Ошибка обработки записи KeePass {i} / Помилка обробки запису KeePass {i}")
                    continue

            logger.info(f"Imported {len(passwords)} passwords from KeePass XML / Импортировано {len(passwords)} паролей из KeePass XML / Імпортовано {len(passwords)} паролів з KeePass XML")
            return passwords

        except (InvalidFileFormatError, MalformedFileError, FileTooLargeError) as e:
            raise
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
            raise ImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
        except (ET.ParseError, ValueError, TypeError) as e:
            logger.error(f"XML parse error / Ошибка парсинга XML / Помилка парсингу XML: {e}")
            raise InvalidFileFormatError(f"Invalid XML format / Неверный формат XML / Невірний формат XML: {e}")

    @staticmethod
    def import_from_bitwarden_json(file_path: str) -> List[Dict[str, Any]]:
        """Import from Bitwarden JSON format with validation
        Импорт из Bitwarden JSON формата с валидацией
        Імпорт з Bitwarden JSON формату з валідацією"""
        # Validate file / Проверяем файл / Перевіряємо файл
        if not os.path.exists(file_path):
            raise ImportError(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")

        if not validate_file_extension(file_path, "bitwarden"):
            logger.warning(f"File {file_path} does not have .json extension / Файл {file_path} не имеет расширения .json / Файл {file_path} не має розширення .json")

        if not validate_file_size(file_path):
            raise FileTooLargeError(f"File too large: {file_path} / Файл слишком большой: {file_path} / Файл занадто великий: {file_path}")

        try:
            # Detect encoding / Определяем кодировку / Визначаємо кодування
            encoding, content = detect_encoding(file_path)
            logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

            # Parse JSON / Парсим JSON / Парсимо JSON
            data = safe_json_parse(content)

            passwords = []

            items = data.get('items', [])
            if not isinstance(items, list):
                raise InvalidFileFormatError("Bitwarden JSON: 'items' must be a list / Bitwarden JSON: 'items' должен быть списком / Bitwarden JSON: 'items' повинен бути списком")

            for item in items:
                try:
                    login = item.get('login', {})
                    password = login.get('password', '')

                    if password:
                        password = sanitize_imported_password(password)
                        name = item.get('name', '')
                        username = login.get('username', '')

                        label = sanitize_imported_label(name) if name else "Bitwarden"
                        if username:
                            label += f" ({sanitize_imported_label(username)})"

                        passwords.append({
                            'label': label[:MAX_LABEL_LENGTH],
                            'password': password,
                            'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'notes': ''
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing Bitwarden item: {e} / Ошибка обработки элемента Bitwarden / Помилка обробки елемента Bitwarden")
                    continue

            logger.info(f"Imported {len(passwords)} passwords from Bitwarden JSON / Импортировано {len(passwords)} паролей из Bitwarden JSON / Імпортовано {len(passwords)} паролів з Bitwarden JSON")
            return passwords

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
            raise ImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
        except (InvalidFileFormatError, FileTooLargeError, UnsupportedEncodingError) as e:
            raise
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"JSON parse error / Ошибка парсинга JSON / Помилка парсингу JSON: {e}")
            raise InvalidFileFormatError(f"Invalid JSON format / Неверный формат JSON / Невірний формат JSON: {e}")

    @staticmethod
    def import_from_1password_csv(file_path: str) -> List[Dict[str, Any]]:
        """Import from 1Password CSV format with sanitization
        Импорт из 1Password CSV формата с санитизацией
        Імпорт з 1Password CSV формату з санітизацією"""
        # Validate file / Проверяем файл / Перевіряємо файл
        if not os.path.exists(file_path):
            raise ImportError(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")

        if not validate_file_extension(file_path, "onepassword"):
            logger.warning(f"File {file_path} does not have .csv or .1pux extension / Файл {file_path} не имеет расширения .csv или .1pux / Файл {file_path} не має розширення .csv або .1pux")

        if not validate_file_size(file_path):
            raise FileTooLargeError(f"File too large: {file_path} / Файл слишком большой: {file_path} / Файл занадто великий: {file_path}")

        try:
            # Detect encoding / Определяем кодировку / Визначаємо кодування
            encoding, content = detect_encoding(file_path)
            logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

            passwords = []
            line_number = 0

            from io import StringIO
            f = StringIO(content)
            reader = csv.DictReader(f)

            for row in reader:
                line_number += 1
                try:
                    title = row.get('title', row.get('Title', ''))
                    password = row.get('password', row.get('Password', ''))
                    username = row.get('username', row.get('Username', ''))
                    url = row.get('url', row.get('URL', ''))

                    if password:
                        password = sanitize_imported_password(password)
                        label = sanitize_imported_label(title) if title else f"1Password_{line_number}"

                        if username:
                            label += f" ({sanitize_imported_label(username)})"
                        if url:
                            label += f" - {url[:100]}"

                        passwords.append({
                            'label': label[:MAX_LABEL_LENGTH],
                            'password': password,
                            'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'notes': ''
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing 1Password line {line_number}: {e} / Ошибка обработки строки 1Password {line_number} / Помилка обробки рядка 1Password {line_number}")
                    continue

            logger.info(f"Imported {len(passwords)} passwords from 1Password CSV / Импортировано {len(passwords)} паролей из 1Password CSV / Імпортовано {len(passwords)} паролів з 1Password CSV")
            return passwords

        except csv.Error as e:
            logger.error(f"CSV parse error at line {line_number}: {e} / Ошибка парсинга CSV на строке {line_number} / Помилка парсингу CSV на рядку {line_number}")
            raise InvalidFileFormatError(f"CSV parsing error / Ошибка парсинга CSV / Помилка парсингу CSV: {e}")
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
            raise ImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
        except (UnsupportedEncodingError, ValueError, TypeError) as e:
            logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
            raise ImportError(f"Import failed / Ошибка импорта / Помилка імпорту: {e}")

    @staticmethod
    def import_all(parent, lang: str = "RU") -> None:
        """Dialog for format selection and import with validation
        Диалог выбора формата и импорт с валидацией
        Діалог вибору формату та імпорт з валідацією"""
        from storage.database import PasswordDB
        from gui.dialogs import CTkMessageBox
        import customtkinter as ctk
        import tkinter as tk
        from localization.lang import LANGUAGES

        L = LANGUAGES.get(lang, LANGUAGES["RU"])

        # Create window / Создаём окно / Створюємо вікно
        win = ctk.CTkToplevel(parent)
        win.title(L.get("import_title", "Import Passwords / Импорт паролей / Імпорт паролів"))
        win.geometry("350x400")
        win.resizable(False, False)
        win.transient(parent)
        win.grab_set()
        win.lift()
        win.focus_force()
        win.after(100, lambda: win.attributes("-topmost", False) if win and win.winfo_exists() else None)
        win.attributes("-topmost", True)

        # Center window / Центрируем окно / Центруємо вікно
        win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 350) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        win.geometry(f"350x400+{x}+{y}")

        format_var = tk.StringVar(value="json")

        ctk.CTkLabel(win, text=L.get("import_format", "Import format: / Формат импорта: / Формат імпорту:"),
                    font=("Segoe UI", 14, "bold")).pack(pady=(20, 10))

        formats = [
            ("json", "JSON (Secure Pass Pro)"),
            ("csv", "CSV (Excel)"),
            ("keepass", "KeePass XML"),
            ("bitwarden", "Bitwarden JSON"),
            ("onepassword", "1Password CSV")
        ]

        for fmt, text in formats:
            ctk.CTkRadioButton(win, text=text, variable=format_var,
                              value=fmt, font=("Segoe UI", 12)).pack(anchor="w", padx=30, pady=3)

        ctk.CTkLabel(win, text="", font=("Segoe UI", 10), text_color="gray").pack(pady=5)
        ctk.CTkLabel(win, text=L.get("import_warning", "Import only from trusted sources! / Импортируйте только из доверенных источников! / Імпортуйте тільки з перевірених джерел!"),
                    font=("Segoe UI", 10), text_color="#FFA500").pack()

        def do_import():
            fmt = format_var.get()
            extensions = {
                "json": ("JSON files", "*.json"),
                "csv": ("CSV files", "*.csv"),
                "keepass": ("KeePass XML", "*.xml"),
                "bitwarden": ("Bitwarden JSON", "*.json"),
                "onepassword": ("1Password CSV", "*.csv")
            }

            try:
                win.attributes("-topmost", False)
                win.update_idletasks()
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError): pass
            path = filedialog.askopenfilename(
                parent=win,
                title="Select file to import / Выберите файл для импорта / Виберіть файл для імпорту",
                filetypes=[(extensions[fmt][0], extensions[fmt][1]), ("All files / Все файлы / Всі файли", "*.*")]
            )

            if not path:
                return

            try:
                # Validate file size first / Сначала проверяем размер файла / Спочатку перевіряємо розмір файлу
                if not validate_file_size(path):
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_file_too_large', 'File too large / Файл слишком большой / Файл занадто великий')}")
                    return

                if fmt == "json":
                    passwords = PasswordImporter.import_from_json(path)
                elif fmt == "csv":
                    passwords = PasswordImporter.import_from_csv(path)
                elif fmt == "keepass":
                    passwords = PasswordImporter.import_from_keepass_xml(path)
                elif fmt == "bitwarden":
                    passwords = PasswordImporter.import_from_bitwarden_json(path)
                elif fmt == "onepassword":
                    passwords = PasswordImporter.import_from_1password_csv(path)
                else:
                    passwords = []

                if not passwords:
                    CTkMessageBox.warning(win, L.get("import_title", "Import / Импорт / Імпорт"),
                                         L.get("import_no_passwords", "No passwords found in file! / В файле не найдено паролей! / У файлі не знайдено паролів!"))
                    return

                # Show preview / Показываем предпросмотр / Показуємо попередній перегляд
                preview_lines = []
                for p in passwords[:10]:
                    preview_lines.append(f"- {p['label'][:50]}")
                preview = "\n".join(preview_lines)
                if len(passwords) > 10:
                    preview += f"\n... and {len(passwords) - 10} more / ... и ещё {len(passwords) - 10} / ... та ще {len(passwords) - 10}"

                if not CTkMessageBox.question(win, L.get("import_title", "Import / Импорт / Імпорт"),
                    f"{L.get('import_found', 'Passwords found / Найдено паролів / Знайдено паролів')}: {len(passwords)}\n\n{preview}\n\n{L.get('import_confirm', 'Import? / Импортировать? / Імпортувати?')}"):
                    return

                # Import / Импортируем / Імпортуємо
                imported = 0
                failed = 0
                for pwd in passwords:
                    try:
                        from core.validators import sanitize_label, sanitize_notes
                        _lbl = sanitize_label(str(pwd.get('label', '') or ''))[:255]
                        _pwd = str(pwd.get('password', '') or '')[:1024]
                        _nts = sanitize_notes(str(pwd.get('notes', '') or ''))[:10000]
                        if not _lbl:
                            failed += 1
                            continue
                        PasswordDB.save(_lbl, _pwd, _nts)
                        imported += 1
                    except (OSError, IOError, sqlite3.Error, ValueError) as e:
                        logger.error(f"Import save error / Ошибка сохранения при импорте / Помилка збереження при імпорті: {e}")
                        failed += 1

                win.destroy()

                result_msg = L.get("import_success", "Imported: {0} / Импортировано: {0} / Імпортовано: {0}").format(imported)
                if failed > 0:
                    result_msg += f"\nFailed to import: {failed} / Не удалось импортировать: {failed} / Не вдалося імпортувати: {failed}"

                CTkMessageBox.info(parent, L.get("import_title", "Import / Импорт / Імпорт"), result_msg)

                # Refresh database window if open / Обновляем окно БД если открыто / Оновлюємо вікно БД якщо відкрито
                if hasattr(parent, '_refresh_db_window'):
                    parent._refresh_db_window()
                elif hasattr(parent, 'refresh'):
                    parent.refresh()

            except FileTooLargeError as e:
                logger.error(f"File too large / Файл слишком большой / Файл занадто великий: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_file_too_large', 'File too large / Файл слишком большой / Файл занадто великий')}")
            except InvalidFileFormatError as e:
                logger.error(f"Invalid format / Неверный формат / Невірний формат: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_invalid_format', 'Invalid file format / Неверный формат файла / Невірний формат файлу')}")
            except MalformedFileError as e:
                logger.error(f"Malformed file / Повреждённый файл / Пошкоджений файл: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_malformed', 'File corrupted / Файл повреждён / Файл пошкоджено')}")
            except UnsupportedEncodingError as e:
                logger.error(f"Unsupported encoding / Неподдерживаемая кодировка / Непідтримуване кодування: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_encoding', 'Unsupported file encoding / Неподдерживаемая кодировка файла / Непідтримуване кодування файлу')}")
            except ImportError as e:
                logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{str(e)}")
            except (ValueError, TypeError, AttributeError) as e:
                logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{str(e)}")
            except sqlite3.Error as e:
                logger.error(f"Database error during import / Ошибка БД при импорте / Помилка БД при імпорті: {e}")
                CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                   f"{L.get('err_database', 'Database error / Ошибка базы данных / Помилка бази даних')}:\n{str(e)}")

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text=L.get("ok", "Import / Импорт / Імпорт"), command=do_import,
                     width=120, fg_color="#2d6a4f", corner_radius=15).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text=L.get("cancel", "Cancel / Отмена / Скасувати"), command=win.destroy,
                     width=120, fg_color="#8b0000", corner_radius=15).pack(side="left", padx=5)

        win.after(100, lambda: win.attributes("-topmost", False))