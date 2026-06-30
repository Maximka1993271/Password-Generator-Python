"""
Import utilities - CSV format
Утилиты импорта - CSV формат
Утиліти імпорту - CSV формат
"""
from __future__ import annotations

import csv
import os
import datetime
from io import StringIO
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.importer.import_base import (
    PasswordImportError, InvalidFileFormatError, FileTooLargeError,
    UnsupportedEncodingError, detect_encoding, detect_csv_delimiter,
    sanitize_password, sanitize_label, find_password_column, find_label_column,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_csv")


def import_from_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from csv.
    Обработать import from csv.
    Обробити import from csv.
    """
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")

    try:
        encoding, content = detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding detection failed: {e}")
        raise PasswordImportError(f"Cannot detect file encoding: {e}")

    passwords = []
    line_number = 0

    try:
        f = StringIO(content)
        delimiter = detect_csv_delimiter(content)
        logger.debug(f"Detected CSV delimiter: '{delimiter}'")

        reader = csv.DictReader(f, delimiter=delimiter)
        fieldnames = reader.fieldnames or []

        if not fieldnames:
            raise InvalidFileFormatError("CSV file has no headers")

        pwd_col = find_password_column(fieldnames)
        label_col = find_label_column(fieldnames)

        if pwd_col is None:
            raise InvalidFileFormatError("Cannot find password column in CSV")

        for row in reader:
            line_number += 1
            try:
                label = row.get(label_col, '') if label_col else ''
                password = row.get(pwd_col, '') if pwd_col else ''
                created = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                notes = ''

                if not password or not password.strip():
                    continue

                label = sanitize_label(label, MAX_LABEL_LENGTH)
                password = sanitize_password(password)

                passwords.append({
                    'label': label if label.strip() else f"Imported_{line_number}",
                    'password': password,
                    'created': created,
                    'notes': notes
                })
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Error processing CSV line {line_number}: {e}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from CSV (encoding: {encoding})")
        return passwords

    except csv.Error as e:
        logger.error(f"CSV parse error at line {line_number}: {e}")
        raise InvalidFileFormatError(f"CSV parsing error: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")