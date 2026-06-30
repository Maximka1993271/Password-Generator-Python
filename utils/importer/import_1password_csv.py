"""
Import utilities - 1Password CSV format
Утилиты импорта - 1Password CSV формат
Утиліти імпорту - 1Password CSV формат
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
    UnsupportedEncodingError, detect_encoding,
    sanitize_password, sanitize_label,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_1password")


def import_from_1password_csv(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from 1password csv.
    Обработать import from 1password csv.
    Обробити import from 1password csv.
    """
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")

    try:
        encoding, content = detect_encoding(file_path, ['utf-8-sig', 'utf-8', 'cp1251'])
        logger.debug(f"Detected encoding: {encoding}")

        passwords = []
        line_number = 0

        f = StringIO(content)
        reader = csv.DictReader(f)

        for row in reader:
            line_number += 1
            try:
                title = row.get('title', row.get('Title', ''))
                password = row.get('password', row.get('Password', ''))
                username = row.get('username', row.get('Username', ''))
                url = row.get('url', row.get('URL', ''))

                if password and password.strip():
                    password = sanitize_password(password)
                    label = sanitize_label(title, MAX_LABEL_LENGTH) if title else f"1Password_{line_number}"

                    if username:
                        label += f" ({sanitize_label(username, 50)})"
                    if url:
                        label += f" - {url[:100]}"

                    passwords.append({
                        'label': label[:MAX_LABEL_LENGTH],
                        'password': password,
                        'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': ''
                    })
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing 1Password line {line_number}: {e}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from 1Password CSV")
        return passwords

    except csv.Error as e:
        logger.error(f"CSV parse error at line {line_number}: {e}")
        raise InvalidFileFormatError(f"CSV parsing error: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error: {e}")
        raise PasswordImportError(f"Cannot detect file encoding: {e}")