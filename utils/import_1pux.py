"""
Password import utilities - 1PUX (1Password Unified Export) format
Утилиты импорта паролей - 1PUX формат
Утиліти імпорту паролів - 1PUX формат

100% ORIGINAL CODE - DO NOT MODIFY
"""
from __future__ import annotations

import json
import zipfile
import tempfile
import shutil
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


def import_from_1pux(file_path: str) -> List[Dict[str, Any]]:
    """Import from 1PUX (1Password Unified Export) format
    Импорт из 1PUX (1Password Unified Export) формата
    Імпорт з 1PUX (1Password Unified Export) формату"""
    temp_dir = None  # cleaned up in the finally block

    try:
        # ── Pre-flight file-size guard ────────────────────────
        # Reject files larger than MAX_FILE_SIZE before attempting
        # to parse them.  1PUX archives can contain binary attachments;
        # a 100 MB cap prevents memory exhaustion from malicious files.
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes / Файл слишком большой: {os.path.getsize(file_path)} байт / Файл занадто великий: {os.path.getsize(file_path)} байт")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        passwords = []

        # ── Extract .1pux archive ─────────────────────────────
        # A .1pux file is a standard ZIP archive containing
        # 'export.data' (JSON manifest) and optional attachment dirs.
        # We extract to a temp directory so we can read the manifest
        # with normal file I/O instead of zip stream reads.
        if zipfile.is_zipfile(file_path):
            temp_dir = tempfile.mkdtemp()  # will be wiped in finally
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # The mandatory manifest inside every .1pux archive
            export_file = os.path.join(temp_dir, 'export.data')
            if not os.path.exists(export_file):  # invalid / partial archive
                for f in os.listdir(temp_dir):
                    if f.endswith('.json'):
                        export_file = os.path.join(temp_dir, f)
                        break

            if not os.path.exists(export_file):
                raise InvalidFileFormatError("Cannot find export.data or .json in 1PUX archive / Не удаётся найти export.data или .json в архиве 1PUX / Не вдається знайти export.data або .json в архіві 1PUX")

            encoding, content = detect_encoding(export_file)
            data = json.loads(content)
        else:
            encoding, content = detect_encoding(file_path)
            if content.startswith('\ufeff'):
                content = content[1:]
            data = json.loads(content)

        logger.debug(f"1PUX detected encoding: {encoding} / Определена кодировка 1PUX: {encoding} / Визначено кодування 1PUX: {encoding}")

        items = data.get('items', [])
        if not isinstance(items, list):
            raise InvalidFileFormatError("1PUX: 'items' must be a list / 1PUX: 'items' должен быть списком / 1PUX: 'items' повинен бути списком")

        for item in items:
            try:
                title = item.get('title', '')

                password = ''
                username = ''
                url = ''
                notes = ''

                fields = item.get('fields', [])
                if isinstance(fields, list):
                    for field in fields:
                        field_type = field.get('type', '')
                        value = field.get('value', '')
                        purpose = field.get('purpose', '')

                        if field_type == 'PASSWORD' or purpose == 'PASSWORD':
                            password = value
                        elif field_type == 'USERNAME' or purpose == 'USERNAME':
                            username = value
                        elif field_type == 'URL' or purpose == 'URL':
                            url = value
                        elif field_type == 'NOTES' or purpose == 'NOTES':
                            notes = value

                if not password:
                    details = item.get('details', {})
                    if isinstance(details, dict):
                        password = details.get('password', '')
                        if not password:
                            password = details.get('passphrase', '')
                        if not password:
                            login_details = details.get('login', {})
                            password = login_details.get('password', '')

                if password and password.strip():
                    password = sanitize_password(password)
                    label = sanitize_csv_value(title, MAX_LABEL_LENGTH) if title else "1Password_import"

                    if username:
                        label += f" ({sanitize_csv_value(username, 50)})"
                    if url:
                        label += f" - {url[:100]}"

                    passwords.append({
                        'label': label[:MAX_LABEL_LENGTH],
                        'password': password,
                        'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': notes[:500] if notes else ''
                    })
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Error processing 1PUX item: {e} / Ошибка обработки элемента 1PUX / Помилка обробки елемента 1PUX")
                continue

        logger.info(f"Imported {len(passwords)} passwords from 1PUX / Импортировано {len(passwords)} паролей из 1PUX / Імпортовано {len(passwords)} паролів з 1PUX")
        return passwords

    except zipfile.BadZipFile:
        try:
            encoding, content = detect_encoding(file_path)
            if content.startswith('\ufeff'):
                content = content[1:]
            data = json.loads(content)

            passwords = []
            items = data.get('items', [])
            for item in items:
                try:
                    title = item.get('title', '')
                    password = ''
                    username = ''
                    url = ''

                    fields = item.get('fields', [])
                    for field in fields:
                        field_type = field.get('type', '')
                        value = field.get('value', '')
                        if field_type == 'PASSWORD':
                            password = value
                        elif field_type == 'USERNAME':
                            username = value
                        elif field_type == 'URL':
                            url = value

                    if not password:
                        details = item.get('details', {})
                        password = details.get('password', '')
                        if not password:
                            login_details = details.get('login', {})
                            password = login_details.get('password', '')

                    if password and password.strip():
                        password = sanitize_password(password)
                        label = sanitize_csv_value(title, MAX_LABEL_LENGTH) if title else "1Password_import"

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
                    continue

            return passwords
        except json.JSONDecodeError as e:
            raise InvalidFileFormatError(f"Invalid 1PUX/JSON format / Неверный формат 1PUX/JSON / Невірний формат 1PUX/JSON: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"1PUX JSON decode error / Ошибка декодирования JSON 1PUX / Помилка декодування JSON 1PUX: {e}")
        raise InvalidFileFormatError(f"Invalid 1PUX format / Неверный формат 1PUX / Невірний формат 1PUX: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"1PUX file read error / Ошибка чтения файла 1PUX / Помилка читання файлу 1PUX: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error / Ошибка кодировки / Помилка кодування: {e}")
        raise PasswordImportError(f"Cannot detect file encoding / Не удалось определить кодировку файла / Не вдалося визначити кодування файлу: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)