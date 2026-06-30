"""
Password import utilities - JSON format
Утилиты импорта паролей - JSON формат
Утиліти імпорту паролів - JSON формат

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
    PasswordImportError, InvalidFileFormatError, MalformedFileError,
    FileTooLargeError, UnsupportedEncodingError,
    detect_encoding, sanitize_csv_value, sanitize_password,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_passwords")


def import_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Import from JSON format (Secure Pass Pro) with corruption check
    Импорт из JSON формата (Secure Pass Pro) с проверкой на повреждение
    Імпорт з JSON формату (Secure Pass Pro) з перевіркою на пошкодження"""
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE}) / Файл слишком большой: {file_size} байт (макс: {MAX_FILE_SIZE}) / Файл занадто великий: {file_size} байт (макс: {MAX_FILE_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        encoding, content = detect_encoding(file_path)
        logger.debug(f"Detected encoding: {encoding} / Определена кодировка: {encoding} / Визначено кодування: {encoding}")

        if content.startswith('\ufeff'):
            content = content[1:]

        if not content or not content.strip():
            raise MalformedFileError("Empty file / Пустой файл / Порожній файл")

        if content.rstrip().endswith(',') or content.rstrip().endswith('\\'):
            raise MalformedFileError("File appears truncated / Файл выглядит обрезанным / Файл виглядає обрізаним")

        data = json.loads(content)
        passwords = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                try:
                    if not isinstance(item, dict):
                        logger.warning(f"Skipping non-dictionary item at index {i} / Пропуск элемента не словаря на индексе {i} / Пропуск елемента не словника на індексі {i}")
                        continue

                    label = item.get('label', item.get('name', ''))
                    password = item.get('password', item.get('pwd', ''))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password and password.strip():
                        label = sanitize_csv_value(label, MAX_LABEL_LENGTH)
                        password = sanitize_password(password)

                        passwords.append({
                            'label': label if label else f"Imported_{i+1} / Импортировано_{i+1} / Імпортовано_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing item {i}: {e} / Ошибка обработки элемента {i} / Помилка обробки елемента {i}")
                    continue

        elif isinstance(data, dict):
            items = data.get('passwords', data.get('items', []))
            if not isinstance(items, list):
                raise InvalidFileFormatError("Invalid JSON structure: 'passwords' or 'items' must be a list / Неверная структура JSON: 'passwords' или 'items' должны быть списком / Невірна структура JSON: 'passwords' або 'items' повинні бути списком")

            for i, item in enumerate(items):
                try:
                    if not isinstance(item, dict):
                        continue

                    label = item.get('label', item.get('name', ''))
                    password = item.get('password', item.get('pwd', ''))
                    created = item.get('created', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    notes = item.get('notes', '')[:500] if item.get('notes') else ''

                    if password and password.strip():
                        label = sanitize_csv_value(label, MAX_LABEL_LENGTH)
                        password = sanitize_password(password)

                        passwords.append({
                            'label': label if label else f"Imported_{i+1} / Импортировано_{i+1} / Імпортовано_{i+1}",
                            'password': password,
                            'created': created,
                            'notes': notes
                        })
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing item {i}: {e} / Ошибка обработки элемента {i} / Помилка обробки елемента {i}")
                    continue
        else:
            raise InvalidFileFormatError(f"Unexpected JSON type: {type(data).__name__} / Неожиданный тип JSON: {type(data).__name__} / Неочікуваний тип JSON: {type(data).__name__}")

        logger.info(f"Imported {len(passwords)} passwords from JSON / Импортировано {len(passwords)} паролей из JSON / Імпортовано {len(passwords)} паролів з JSON")
        return passwords

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error / Ошибка декодирования JSON / Помилка декодування JSON: {e}")
        raise InvalidFileFormatError(f"Invalid JSON format / Неверный формат JSON / Невірний формат JSON: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
    except MalformedFileError:
        raise
    except InvalidFileFormatError:
        raise
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error / Ошибка кодировки / Помилка кодування: {e}")
        raise PasswordImportError(f"Cannot detect file encoding / Не удалось определить кодировку файла / Не вдалося визначити кодування файлу: {e}")