"""
Import utilities - Bitwarden JSON format
Утилиты импорта - Bitwarden JSON формат
Утиліти імпорту - Bitwarden JSON формат
"""
from __future__ import annotations

import json
import os
import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.importer.import_base import (
    PasswordImportError, InvalidFileFormatError, FileTooLargeError,
    UnsupportedEncodingError, detect_encoding,
    sanitize_password, sanitize_label,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_bitwarden")


def import_from_bitwarden_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from bitwarden json.
    Обработать import from bitwarden json.
    Обробити import from bitwarden json.
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

        if content.startswith('\ufeff'):
            content = content[1:]

        data = json.loads(content)
        passwords = []

        items = data.get('items', [])
        if not isinstance(items, list):
            raise InvalidFileFormatError("Bitwarden JSON: 'items' must be a list")

        for item in items:
            try:
                login = item.get('login', {})
                password = login.get('password', '')

                if password and password.strip():
                    password = sanitize_password(password)
                    name = item.get('name', '')
                    username = login.get('username', '')

                    label = sanitize_label(name, MAX_LABEL_LENGTH) if name else "Bitwarden"
                    if username:
                        label += f" ({sanitize_label(username, 50)})"

                    passwords.append({
                        'label': label[:MAX_LABEL_LENGTH],
                        'password': password,
                        'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': ''
                    })
            except (KeyError, ValueError, TypeError) as e:
                logger.warning(f"Error processing Bitwarden item: {e}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from Bitwarden JSON")
        return passwords

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise InvalidFileFormatError(f"Invalid JSON format: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error: {e}")
        raise PasswordImportError(f"Cannot detect file encoding: {e}")