"""
Import utilities - 1PUX (1Password Unified Export) format
Утилиты импорта - 1PUX формат
Утиліти імпорту - 1PUX формат
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
from utils.importer.import_base import (
    PasswordImportError, InvalidFileFormatError, FileTooLargeError,
    UnsupportedEncodingError, detect_encoding,
    sanitize_password, sanitize_label,
    MAX_FILE_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_1pux")


def import_from_1pux(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from 1pux.
    Обработать import from 1pux.
    Обробити import from 1pux.
    """
    temp_dir = None  # cleaned up in the finally block

    try:
        # ── Pre-flight file-size guard ────────────────────────
        # Reject files larger than MAX_FILE_SIZE before attempting
        # to parse them.  1PUX archives can contain binary attachments;
        # a 100 MB cap prevents memory exhaustion from malicious files.
        if os.path.getsize(file_path) > MAX_FILE_SIZE:
            raise FileTooLargeError(f"File too large: {os.path.getsize(file_path)} bytes")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")

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
                raise InvalidFileFormatError("Cannot find export.data or .json in 1PUX archive")

            encoding, content = detect_encoding(export_file)
            data = json.loads(content)
        else:
            encoding, content = detect_encoding(file_path)
            if content.startswith('\ufeff'):
                content = content[1:]
            data = json.loads(content)

        logger.debug(f"1PUX detected encoding: {encoding}")

        items = data.get('items', [])
        if not isinstance(items, list):
            raise InvalidFileFormatError("1PUX: 'items' must be a list")

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
                    label = sanitize_label(title, MAX_LABEL_LENGTH) if title else "1Password_import"

                    if username:
                        label += f" ({sanitize_label(username, 50)})"
                    if url:
                        label += f" - {url[:100]}"

                    passwords.append({
                        'label': label[:MAX_LABEL_LENGTH],
                        'password': password,
                        'created': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': notes[:500] if notes else ''
                    })
            except (KeyError, ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Error processing 1PUX item: {e}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from 1PUX")
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
                        label = sanitize_label(title, MAX_LABEL_LENGTH) if title else "1Password_import"

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
                    continue

            return passwords
        except json.JSONDecodeError as e:
            raise InvalidFileFormatError(f"Invalid 1PUX/JSON format: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"1PUX JSON decode error: {e}")
        raise InvalidFileFormatError(f"Invalid 1PUX format: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"1PUX file read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")
    except UnsupportedEncodingError as e:
        logger.error(f"Encoding error: {e}")
        raise PasswordImportError(f"Cannot detect file encoding: {e}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)