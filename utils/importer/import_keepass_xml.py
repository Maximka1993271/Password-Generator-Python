"""
Import utilities - KeePass XML format
Утилиты импорта - KeePass XML формат
Утиліти імпорту - KeePass XML формат
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import os
import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.importer.import_base import (
    PasswordImportError, InvalidFileFormatError, MalformedFileError,
    FileTooLargeError, safe_xml_parse,
    sanitize_password, sanitize_label,
    MAX_XML_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_keepass_xml")


def import_from_keepass_xml(file_path: str) -> List[Dict[str, Any]]:
    """
    Handle import from keepass xml.
    Обработать import from keepass xml.
    Обробити import from keepass xml.
    """
    try:
        if os.path.getsize(file_path) > MAX_XML_SIZE:
            raise FileTooLargeError(f"XML file too large: {os.path.getsize(file_path)} bytes (max: {MAX_XML_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")

    try:
        root = safe_xml_parse(file_path)

        passwords = []
        entries = root.findall('.//Entry') or root.findall('.//entry')

        for i, entry in enumerate(entries):
            try:
                title_elem = entry.find('.//Title') or entry.find('.//title')
                password_elem = entry.find('.//Password') or entry.find('.//password')
                username_elem = entry.find('.//UserName') or entry.find('.//username')
                url_elem = entry.find('.//URL') or entry.find('.//url')
                notes_elem = entry.find('.//Notes') or entry.find('.//notes')

                title = title_elem.text if title_elem is not None else ''
                password = password_elem.text if password_elem is not None else ''
                username = username_elem.text if username_elem is not None else ''
                url = url_elem.text if url_elem is not None else ''
                notes = notes_elem.text if notes_elem is not None else ''

                if password and password.strip():
                    password = sanitize_password(password)
                    label = sanitize_label(title, MAX_LABEL_LENGTH) if title else f"KeePass_{i+1}"

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
            except (AttributeError, ValueError, TypeError) as e:
                logger.warning(f"Error processing KeePass entry {i}: {e}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from KeePass XML")
        return passwords

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        raise InvalidFileFormatError(f"Invalid XML format: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error: {e}")
        raise PasswordImportError(f"Cannot read file: {e}")