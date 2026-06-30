"""
Password import utilities - CSV format
Утилиты импорта паролей - CSV формат
Утиліти імпорту паролів - CSV формат

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import csv
import os
import datetime
from io import StringIO
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.import_helpers import (
    PasswordImportError, InvalidFileFormatError, FileTooLargeError,
    UnsupportedEncodingError, detect_encoding, detect_csv_delimiter,
    sanitize_csv_value, sanitize_password, MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_passwords")


def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """Import from CSV format (Excel, Google Sheets) with sanitization
    Импорт из CSV формата (Excel, Google Sheets) с санитизацией
    Імпорт з CSV формату (Excel, Google Sheets) з санітизацією"""
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes / Файл слишком большой: {os.path.getsize(file_path)} байт / Файл занадто великий: {os.path.getsize(file_path)} байт")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        encoding, content = detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding detection failed / Ошибка определения кодировки / Помилка визначення кодування: {e}")
        raise PasswordImportError(f"Cannot detect file encoding / Не удалось определить кодировку файла / Не вдалося визначити кодування файлу: {e}")

    passwords = []
    line_number = 0

    try:
        f = StringIO(content)

        delimiter = detect_csv_delimiter(content)
        logger.debug(f"Detected CSV delimiter: '{delimiter}' / Определён разделитель CSV: '{delimiter}' / Визначено розділювач CSV: '{delimiter}'")

        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = reader.fieldnames or []

        if not fieldnames:
            raise InvalidFileFormatError("CSV file has no headers / CSV файл не имеет заголовков / CSV файл не має заголовків")

        label_col = None
        pwd_col = None
        date_col = None
        notes_col = None

        for col in fieldnames:
            col_lower = col.lower().strip()
            if 'label' in col_lower or 'name' in col_lower or 'title' in col_lower or 'site' in col_lower:
                label_col = col
            elif 'password' in col_lower or 'pwd' in col_lower or 'pass' in col_lower:
                pwd_col = col
            elif 'created' in col_lower or 'date' in col_lower or 'time' in col_lower:
                date_col = col
            elif 'notes' in col_lower or 'comment' in col_lower or 'description' in col_lower:
                notes_col = col

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

                if not password or not password.strip():
                    continue

                label = sanitize_csv_value(label, MAX_LABEL_LENGTH)
                password = sanitize_password(password)

                passwords.append({
                    'label': label if label.strip() else f"Imported_{line_number} / Импортировано_{line_number} / Імпортовано_{line_number}",
                    'password': password,
                    'created': created[:19] if len(created) > 19 else created,
                    'notes': notes
                })
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Error processing CSV line {line_number}: {e} / Ошибка обработки строки CSV {line_number} / Помилка обробки рядка CSV {line_number}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from CSV (encoding: {encoding}) / Импортировано {len(passwords)} паролей из CSV (кодировка: {encoding}) / Імпортовано {len(passwords)} паролів з CSV (кодування: {encoding})")
        return passwords

    except csv.Error as e:
        logger.error(f"CSV parse error at line {line_number}: {e} / Ошибка парсинга CSV на строке {line_number} / Помилка парсингу CSV на рядку {line_number}")
        raise InvalidFileFormatError(f"CSV parsing error / Ошибка парсинга CSV / Помилка парсингу CSV: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")