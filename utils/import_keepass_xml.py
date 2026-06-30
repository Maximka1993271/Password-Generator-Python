"""
Password import utilities - KeePass XML format
Утилиты импорта паролей - KeePass XML формат
Утиліти імпорту паролів - KeePass XML формат

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import os
import datetime
from typing import List, Dict, Any
from utils.logger import get_logger
from utils.import_helpers import (
    PasswordImportError, InvalidFileFormatError, MalformedFileError,
    FileTooLargeError, safe_xml_parse, sanitize_csv_value, sanitize_password,
    MAX_XML_SIZE, MAX_LABEL_LENGTH
)

logger = get_logger("import_passwords")


def import_from_keepass_xml(file_path: str) -> List[Dict[str, Any]]:
    """Import from KeePass XML format with safe parsing (XXE protected)
    Импорт из KeePass XML формата с безопасным парсингом (защита от XXE)
    Імпорт з KeePass XML формату з безпечним парсингом (захист від XXE)"""
    try:
        if os.path.getsize(file_path) > MAX_XML_SIZE:
            raise FileTooLargeError(f"XML file too large: {os.path.getsize(file_path)} bytes (max: {MAX_XML_SIZE}) / XML файл слишком большой: {os.path.getsize(file_path)} байт (макс: {MAX_XML_SIZE}) / XML файл занадто великий: {os.path.getsize(file_path)} байт (макс: {MAX_XML_SIZE})")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to check file size / Ошибка проверки размера файла / Помилка перевірки розміру файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")

    try:
        # Safe XML parsing with XXE protection
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
                    label = sanitize_csv_value(title, MAX_LABEL_LENGTH) if title else f"KeePass_{i+1}"

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
            except (AttributeError, ValueError, TypeError) as e:
                logger.warning(f"Error processing KeePass entry {i}: {e} / Ошибка обработки записи KeePass {i} / Помилка обробки запису KeePass {i}")
                continue

        logger.info(f"Imported {len(passwords)} passwords from KeePass XML / Импортировано {len(passwords)} паролей из KeePass XML / Імпортовано {len(passwords)} паролів з KeePass XML")
        return passwords

    except ET.ParseError as e:
        logger.error(f"XML parse error / Ошибка парсинга XML / Помилка парсингу XML: {e}")
        raise InvalidFileFormatError(f"Invalid XML format / Неверный формат XML / Невірний формат XML: {e}")
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"File read error / Ошибка чтения файла / Помилка читання файлу: {e}")
        raise PasswordImportError(f"Cannot read file / Не удалось прочитать файл / Не вдалося прочитати файл: {e}")