"""
Password import utilities - Bitwarden JSON format
Утилиты импорта паролей - Bitwarden JSON формат
Утиліти імпорту паролів - Bitwarden JSON формат

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import json
import os
import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.import_helpers import (
    PasswordImportError, InvalidFileFormatError, FileTooLargeError,
    UnsupportedEncodingError, detect_encoding, sanitize_csv_value, sanitize_password,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_passwords")


def import_from_bitwarden_json(file_path: str) -> List[Dict[str, Any]]:
    """Import from Bitwarden JSON format
    Импорт из Bitwarden JSON формата
    Імпорт з Bitwarden JSON формату"""
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes / Файл слишком большой: {os.path.getsize(file_path)} байт / Файл занадто великий: {os.path.getsize(file_path)} байт")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        encoding, content = detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

        if content.startswith('\ufeff'):
            content = content[1:]

        data = json.loads(content)
        passwords = []

        items = data.get('items', [])
        if not isinstance(items, list):
            raise InvalidFileFormatError("Bitwarden JSON: 'items' must be a list / Bitwarden JSON: 'items' должен быть списком / Bitwarden JSON: 'items' повинен бути списком")

        for item in items:
            try:
                login = item.get('login', {})
                password = login.get('password', '')

                if password and password.strip():
                    password = sanitize_password(password)
                    name = item.get('name', '')
                    username = login.get('username', '')

                    label = sanitize_csv_value(name, MAX_LABEL_LENGTH) if name else "Bitwarden"
                    if username:
                        label += f" ({sanitize_csv_value(username, 50)})"

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

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error / Ошибка декодирования JSON / Помилка декодування JSON: {e}")
        raise InvalidFileFormatError(f"Invalid JSON format / Неверный формат JSON / Невірний формат JSON: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error / Ошибка кодировки / Помилка кодування: {e}")
        raise PasswordImportError(f"Cannot detect file encoding / Не удалось определить кодировку файла / Не вдалося визначити кодування файлу: {e}")