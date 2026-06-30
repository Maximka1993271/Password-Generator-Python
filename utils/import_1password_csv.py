"""
Password import utilities - 1Password CSV format
Утилиты импорта паролей - 1Password CSV формат
Утиліти імпорту паролів - 1Password CSV формат

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
    UnsupportedEncodingError, detect_encoding, sanitize_csv_value, sanitize_password,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_passwords")


def import_from_1password_csv(file_path: str) -> List[Dict[str, Any]]:
    """Import from 1Password CSV format
    Импорт из 1Password CSV формата
    Імпорт з 1Password CSV формату"""
    try:
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes / Файл слишком большой: {os.path.getsize(file_path)} байт / Файл занадто великий: {os.path.getsize(file_path)} байт")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        encoding, content = detect_encoding(file_path, ['utf-8-sig', 'utf-8', 'cp1251'])
        logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

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
                    label = sanitize_csv_value(title, MAX_LABEL_LENGTH) if title else f"1Password_{line_number}"

                    if username:
                        label += f" ({sanitize_csv_value(username, 50)})"
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
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error / Ошибка кодировки / Помилка кодування: {e}")
        raise PasswordImportError(f"Cannot detect file encoding / Не удалось определить кодировку файла / Не вдалося визначити кодування файлу: {e}")