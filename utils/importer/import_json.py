"""
Import utilities - JSON format
Утилиты импорта - JSON формат
Утиліти імпорту - JSON формат
"""
from __future__ import annotations

import json
import os
import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.importer.import_base import (
    PasswordImportError, InvalidFileFormatError, MalformedFileError,
    FileTooLargeError, UnsupportedEncodingError,
    detect_encoding, sanitize_password, sanitize_label,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_json")


def import_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from json.
    Обработать import from json.
    Обробити import from json.
    """
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")

    try:
        encoding, content = detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding}")

        if content.startswith('\ufeff'):
            content = content[1:]

        if not content or not content.strip():
            raise MalformedFileError("Empty file")

        if content.rstrip().endswith(',') or content.rstrip().endswith('\\'):
            raise MalformedFileError("File appears truncated")

        data = json.loads(content)
        passwords = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                try:
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dictionary item at index {i}")
                        continue

                    label = item.get('label', item.get('name', ''))
                    password = item.get('password', item.get('pwd', ''))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password and password.strip():
                        label = sanitize_label(label, MAX_LABEL_LENGTH)
                        password = sanitize_password(password)

                        passwords.append({
                            'label': label if label else f"Imported_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing item {i}: {e}")
                    continue

        elif isinstance(data, dict):
            items = data.get('passwords', data.get('items', []))
            if not isinstance(items, list):
                raise InvalidFileFormatError("Invalid JSON structure: 'passwords' or 'items' must be a list")

            for i, item in enumerate(items):
                try:
                    if not isinstance(item, dict):
                        continue

                    label = item.get('label', item.get('name', ''))
                    password = item.get('password', item.get('pwd', ''))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password and password.strip():
                        label = sanitize_label(label, MAX_LABEL_LENGTH)
                        password = sanitize_password(password)

                        passwords.append({
                            'label': label if label else f"Imported_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing item {i}: {e}")
                    continue
        else:
            raise InvalidFileFormatError(f"Unexpected JSON type: {type(data).__name__}")

        logger.info(f"Imported {len(passwords)} passwords from JSON")
        return passwords

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise InvalidFileFormatError(f"Invalid JSON format: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")
    except MalformedFileError:
        raise
    except InvalidFileFormatError:
        raise
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error: {e}")
        raise PasswordImportError(f"Cannot detect file encoding: {e}")