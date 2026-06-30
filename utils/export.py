"""
Data export utilities for JSON, CSV, HTML with encryption support

Утилиты экспорта данных в JSON, CSV, HTML с поддержкой шифрования
Утиліти експорту даних у JSON, CSV, HTML з підтримкою шифрування

FIXED #49: Renamed EncryptionError to ExportEncryptionError to avoid conflict with security.encryption
FIXED #EX: Replaced broad Exception with specific exceptions
FIXED: Added 3-language support for all messages

Исправлено #49: Переименован EncryptionError в ExportEncryptionError во избежание конфликта с security.encryption
Исправлено #EX: Заменены общие Exception на конкретные исключения
Исправлено: Добавлена поддержка 3 языков для всех сообщений

Виправлено #49: Перейменовано EncryptionError в ExportEncryptionError для уникнення конфлікту з security.encryption
Виправлено #EX: Замінено загальні Exception на конкретні винятки
Виправлено: Додано підтримку 3 мов для всіх повідомлень
"""
from __future__ import annotations

import json
import csv
import os
import datetime
import tkinter as tk
import tempfile
import shutil
import re
import hashlib
import hmac
import html
import secrets
from typing import List, Dict, Any, Optional, Tuple
from tkinter import filedialog
from utils.logger import get_logger
from Langs.lang import LANGUAGES

# Try to import cryptography for export encryption
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = get_logger("export")

# Maximum export file size (50 MB)
MAX_EXPORT_SIZE = 50 * 1024 * 1024

# Maximum password length for encryption
MAX_ENCRYPT_PASSWORD_LENGTH = 128

# Minimum password length for encryption
MIN_ENCRYPT_PASSWORD_LENGTH = 8


class ExportError(Exception):
    """Exception for export errors / Исключение для ошибок экспорта / Виняток для помилок експорту"""
    pass


class ExportEncryptionError(ExportError):
    """Exception for export encryption errors / Исключение для ошибок шифрования экспорта / Виняток для помилок шифрування експорту"""
    pass


class ValidationError(ExportError):
    """Exception for validation errors / Исключение для ошибок валидации / Виняток для помилок валідації"""
    pass


def sanitize_export_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize data before export (remove sensitive patterns, limit size).

    Очищает данные перед экспортом (удаляет чувствительные паттерны, ограничивает размер).
    Очищує дані перед експортом (видаляє чутливі патерни, обмежує розмір).
    """
    sanitized = []

    for item in data:
        sanitized_item = {}
        for key, value in item.items():
            if value is None:
                sanitized_item[key] = ""
            elif isinstance(value, str):
                cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
                if len(cleaned) > 10000:
                    cleaned = cleaned[:10000] + "...[TRUNCATED]"
                sanitized_item[key] = cleaned
            else:
                sanitized_item[key] = value
        sanitized.append(sanitized_item)

    return sanitized


def _csv_safe_value(value: Any) -> Any:
    """Prevent spreadsheet formula injection in CSV exports.
    Предотвращает внедрение формул электронных таблиц в CSV экспорт.
    Запобігає впровадженню формул електронних таблиць у CSV експорт."""
    if not isinstance(value, str):
        return value
    stripped = value.lstrip()
    if stripped.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def validate_export_password(password: str) -> Tuple[bool, str]:
    """
    Validate encryption password strength.

    Проверяет надёжность пароля для шифрования.
    Перевіряє надійність пароля для шифрування.
    """
    if not password:
        return False, "Password cannot be empty / Пароль не может быть пустым / Пароль не може бути порожнім"

    if len(password) < MIN_ENCRYPT_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_ENCRYPT_PASSWORD_LENGTH} characters / Пароль должен содержать не менее {MIN_ENCRYPT_PASSWORD_LENGTH} символов / Пароль повинен містити не менше {MIN_ENCRYPT_PASSWORD_LENGTH} символів"

    if len(password) > MAX_ENCRYPT_PASSWORD_LENGTH:
        return False, f"Password must be at most {MAX_ENCRYPT_PASSWORD_LENGTH} characters / Пароль должен содержать не более {MAX_ENCRYPT_PASSWORD_LENGTH} символов / Пароль повинен містити не більше {MAX_ENCRYPT_PASSWORD_LENGTH} символів"

    return True, ""


def encrypt_export_file(data: bytes, password: str) -> bytes:
    """
    Encrypt exported data with password.

    Зашифровать экспортированные данные паролем.
    Зашифрувати експортовані дані паролем.
    """
    if not CRYPTO_AVAILABLE:
        raise ExportEncryptionError("Cryptography module not available for encryption / Модуль cryptography недоступен для шифрования / Модуль cryptography недоступний для шифрування")

    is_valid, error = validate_export_password(password)
    if not is_valid:
        raise ExportEncryptionError(f"Invalid encryption password: {error} / Неверный пароль шифрования: {error} / Невірний пароль шифрування: {error}")

    try:
        salt = os.urandom(16)
        nonce = os.urandom(12)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,
        )
        key = kdf.derive(password.encode('utf-8'))

        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        result = salt + nonce + ciphertext

        key = None
        kdf = None

        return result

    except (ValueError, TypeError, MemoryError, RuntimeError) as e:
        logger.error(f"Encryption error / Ошибка шифрования / Помилка шифрування: {e}")
        raise ExportEncryptionError(f"Failed to encrypt export / Ошибка шифрования экспорта / Помилка шифрування експорту: {e}")


def verify_export_integrity(file_path: str, expected_size: Optional[int] = None) -> bool:
    """
    Verify exported file integrity.

    Проверяет целостность экспортированного файла.
    Перевіряє цілісність експортованого файлу.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"Export file not found: {file_path} / Файл экспорта не найден: {file_path} / Файл експорту не знайдено")
            return False

        size = os.path.getsize(file_path)
        if size == 0:
            logger.error("Export file is empty / Файл экспорта пуст / Файл експорту порожній")
            return False

        if expected_size and abs(size - expected_size) > 1024:
            logger.warning(f"File size mismatch: expected {expected_size}, got {size} / Несоответствие размера файла: ожидалось {expected_size}, получено {size} / Невідповідність розміру файлу: очікувалось {expected_size}, отримано {size}")

        return True
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Integrity check failed / Ошибка проверки целостности / Помилка перевірки цілісності: {e}")
        return False


class DataExporter:
    """Data export to JSON, CSV, HTML with advanced features
    Экспорт данных в JSON, CSV, HTML с расширенными функциями
    Експорт даних у JSON, CSV, HTML з розширеними функціями"""

    @staticmethod
    def export_json(data: List[Dict[str, Any]], file_path: str,
                    fields: List[str] = None, encrypt: bool = False,
                    password: str = None) -> bool:
        """Export to JSON with field selection and encryption
        Экспорт в JSON с выбором полей и шифрованием
        Експорт у JSON з вибором полів та шифруванням"""
        try:
            export_data = sanitize_export_data(data)

            filtered_data = []
            for item in export_data:
                if fields:
                    filtered_item = {k: v for k, v in item.items() if k in fields}
                else:
                    filtered_item = item.copy()
                filtered_item = {k: v for k, v in filtered_item.items() if v is not None}
                filtered_data.append(filtered_item)

            export_wrapper = {
                "export_date": datetime.datetime.now().isoformat(),
                "app": "Secure Pass Pro v4.0",
                "count": len(data),
                "fields": fields if fields else list(data[0].keys()) if data else [],
                "passwords": filtered_data
            }

            json_data = json.dumps(export_wrapper, indent=2, ensure_ascii=False).encode('utf-8')

            if encrypt and password:
                json_data = encrypt_export_file(json_data, password)
                file_path = file_path.replace('.json', '.enc.json')

            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', prefix='export_')
            os.close(temp_fd)

            try:
                with open(temp_path, 'wb') as f:
                    f.write(json_data)
                    f.flush()
                    os.fsync(f.fileno())

                shutil.move(temp_path, file_path)

                if not verify_export_integrity(file_path, len(json_data)):
                    raise ExportError("Export file integrity check failed / Проверка целостности файла экспорта не пройдена / Перевірку цілісності файлу експорту не пройдено")

                logger.info(f"JSON export successful: {file_path} / JSON экспорт успешен: {file_path} / JSON експорт успішний: {file_path}")
                return True
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except (OSError, IOError, PermissionError):
                        pass

        except (OSError, IOError, TypeError, json.JSONDecodeError, shutil.Error) as e:
            logger.error(f"JSON export error / Ошибка JSON экспорта / Помилка JSON експорту: {e}")
            return False
        except ExportEncryptionError as e:
            logger.error(f"Encryption error during JSON export / Ошибка шифрования при JSON экспорте / Помилка шифрування при JSON експорті: {e}")
            return False
        except ExportError as e:
            logger.error(f"Export error / Ошибка экспорта / Помилка експорту: {e}")
            return False

    @staticmethod
    def export_csv(data: List[Dict[str, Any]], file_path: str,
                   fields: List[str] = None, encoding: str = 'utf-8-sig') -> bool:
        """Export to CSV with field selection and encoding
        Экспорт в CSV с выбором полей и кодировкой
        Експорт у CSV з вибором полів та кодуванням"""
        try:
            if not data:
                logger.warning("No data to export to CSV / Нет данных для экспорта в CSV / Немає даних для експорту в CSV")
                return False

            export_data = sanitize_export_data(data)

            if fields is None:
                fields = ['id', 'label', 'password', 'created', 'notes']

            existing_fields = [f for f in fields if f in export_data[0] or f == 'id']

            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', prefix='export_')
            os.close(temp_fd)

            try:
                with open(temp_path, 'w', encoding=encoding, newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=existing_fields)
                    writer.writeheader()
                    for row in export_data:
                        filtered_row = {k: row.get(k, '') for k in existing_fields}
                        filtered_row = {k: _csv_safe_value(v if v is not None else '') for k, v in filtered_row.items()}
                        writer.writerow(filtered_row)

                shutil.move(temp_path, file_path)

                if not verify_export_integrity(file_path):
                    raise ExportError("Export file integrity check failed / Проверка целостности файла экспорта не пройдена / Перевірку цілісності файлу експорту не пройдено")

                logger.info(f"CSV export successful: {file_path} / CSV экспорт успешен: {file_path} / CSV експорт успішний: {file_path}")
                return True
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except (OSError, IOError, PermissionError) as e:
                        pass

        except (OSError, IOError, csv.Error, shutil.Error) as e:
            logger.error(f"CSV export error / Ошибка CSV экспорта / Помилка CSV експорту: {e}")
            return False
        except ExportError as e:
            logger.error(f"Export error / Ошибка экспорта / Помилка експорту: {e}")
            return False

    @staticmethod
    def export_html(data: List[Dict[str, Any]], file_path: str, lang: str = "RU",
                    fields: List[str] = None) -> bool:
        """Export to HTML with interactive search, sorting, highlighting and printing
        Экспорт в HTML с интерактивным поиском, сортировкой, подсветкой и печатью
        Експорт у HTML з інтерактивним пошуком, сортуванням, підсвіткою та друком"""
        try:
            from Langs.lang import LANGUAGES

            export_data = sanitize_export_data(data)

            L = LANGUAGES.get(lang, LANGUAGES["RU"])
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            no_label_text = L.get("db_no_label", "No label / Без метки / Без мітки")

            if fields is None:
                fields = ['id', 'label', 'password', 'created', 'notes']

            headers = {
                'id': '#',
                'label': L.get('db_edit_label', 'Label / Метка / Мітка'),
                'password': L.get('pdf_pass', 'Password / Пароль'),
                'created': L.get('pdf_date', 'Date / Дата'),
                'notes': L.get('db_notes', 'Notes / Заметки / Нотатки')
            }

            rows = ""
            copy_title = html.escape(str(L.get("db_copy", "Copy / Копировать / Копіювати")), quote=True)
            for i, row in enumerate(export_data, 1):
                row_html = "<tr>"
                for field in fields:
                    raw_value = row.get(field, '')
                    if raw_value is None:
                        raw_value = ''

                    if field == 'id':
                        value = str(i)
                    else:
                        value = str(raw_value)

                    if field == "label":
                        if not value or value.strip() == "" or value in ["??? ?????", "No label", "??? ?????"]:
                            value = no_label_text

                    escaped_value = html.escape(value, quote=True)
                    safe_field = html.escape(str(field), quote=True)
                    safe_class = re.sub(r'[^a-zA-Z0-9_-]', '-', str(field))

                    if field == "password":
                        row_html += f'<td class="password-cell" data-field="{safe_field}" data-value="{escaped_value}"><span class="password" title="{copy_title}">{escaped_value}</span></td>'
                    elif field == "label":
                        row_html += f'<td class="label-cell" data-field="{safe_field}" data-value="{escaped_value}"><strong>{escaped_value}</strong></td>'
                    elif field == "created":
                        row_html += f'<td class="date-cell" data-field="{safe_field}" data-value="{escaped_value}">{escaped_value}</td>'
                    else:
                        row_html += f'<td class="{safe_class}-cell" data-field="{safe_field}" data-value="{escaped_value}">{escaped_value}</td>'
                row_html += "</tr>"
                rows += row_html

            header_html = ""
            sort_title = html.escape(str(L.get("export_sort_title", "Sort by / Сортировать по / Сортувати за")), quote=True)
            for index, field in enumerate(fields):
                header_text = html.escape(str(headers.get(field, field.capitalize())), quote=True)
                header_html += f'<th onclick="sortTable({index})" title="{sort_title} {header_text}">{header_text}<span class="sort-icon"></span></th>'

            temp_fd, temp_path = tempfile.mkstemp(suffix='.tmp', prefix='export_')
            os.close(temp_fd)

            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(DataExporter._generate_html_content(
                        lang, L, now, no_label_text, fields, headers, rows, header_html, len(export_data)
                    ))

                shutil.move(temp_path, file_path)

                if not verify_export_integrity(file_path):
                    raise ExportError("Export file integrity check failed / Проверка целостности файла экспорта не пройдена / Перевірку цілісності файлу експорту не пройдено")

                logger.info(f"HTML export successful: {file_path} / HTML экспорт успешен: {file_path} / HTML експорт успішний: {file_path}")
                return True
            finally:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except (OSError, IOError, PermissionError) as e:
                        pass

        except (OSError, IOError, shutil.Error) as e:
            logger.error(f"HTML export error / Ошибка HTML экспорта / Помилка HTML експорту: {e}")
            return False
        except ExportError as e:
            logger.error(f"Export error / Ошибка экспорта / Помилка експорту: {e}")
            return False

    @staticmethod
    def _generate_html_content(lang: str, L, now: str, no_label_text: str,
                                fields: List[str], headers: Dict[str, str],
                                rows: str, header_html: str, data_count: int) -> str:
        """Generate HTML content (helper method) / Генерирует HTML содержимое (вспомогательный метод) / Генерує HTML вміст (допоміжний метод)"""
        return DataExporter._generate_html_content_impl(lang, L, now, no_label_text, fields, headers, rows, header_html, data_count)

    @staticmethod
    def _generate_html_content_impl(lang: str, L, now: str, no_label_text: str,
                                     fields: List[str], headers: Dict[str, str],
                                     rows: str, header_html: str, data_count: int) -> str:
        """Internal implementation of HTML generation / Внутренняя реализация генерации HTML / Внутрішня реалізація генерації HTML"""
        texts = {
            'search_placeholder': {
                'RU': "Поиск по названию метки, значению пароля или дате создания...",
                'EN': "Search by label, password or date...",
                'UA': "Пошук за назвою мітки, значенням пароля або датою створення..."
            },
            'reset_btn': {'RU': "Сбросить", 'EN': "Reset", 'UA': "Скинути"},
            'print_btn': {'RU': "Печать отчёта", 'EN': "Print report", 'UA': "Друк звіту"},
            'copy_hint': {
                'RU': "Нажмите на пароль для копирования в буфер обмена",
                'EN': "Click on password to copy to clipboard",
                'UA': "Натисніть на пароль для копіювання в буфер обміну"
            },
            'copied_toast': {
                'RU': "Пароль скопирован!",
                'EN': "Password copied!",
                'UA': "Пароль скопійовано!"
            },
            'footer_copyright': {
                'RU': "Данные экспортированы в защищенном режиме.",
                'EN': "Data exported in secure mode.",
                'UA': "Дані експортовано в захищеному режимі."
            }
        }

        search_placeholder = texts['search_placeholder'].get(lang, texts['search_placeholder']['RU'])
        reset_btn_text = texts['reset_btn'].get(lang, texts['reset_btn']['RU'])
        print_btn_text = texts['print_btn'].get(lang, texts['print_btn']['RU'])
        copy_hint_text = texts['copy_hint'].get(lang, texts['copy_hint']['RU'])
        copied_toast_text = texts['copied_toast'].get(lang, texts['copied_toast']['RU'])
        footer_text = texts['footer_copyright'].get(lang, texts['footer_copyright']['RU'])

        return f"""<!DOCTYPE html>
<html lang="{lang.lower()}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Pass Pro - {L.get('export_passwords', 'Passwords / Пароли / Паролі')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0b0f19;
            color: #f1f5f9;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #111827;
            border-radius: 16px;
            border: 1px solid #1f2937;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
            padding: 30px;
            text-align: center;
            border-bottom: 1px solid #065f46;
        }}
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            color: #10b981;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .header p {{
            color: #a7f3d0;
            font-size: 14px;
            opacity: 0.85;
        }}
        .control-panel {{
            background: #1f2937;
            padding: 20px 30px;
            border-bottom: 1px solid #374151;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .search-row {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        .search-wrapper {{
            position: relative;
            flex: 1;
        }}
        .search-box {{
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid #4b5563;
            background: #0f172a;
            color: #fff;
            font-size: 14px;
            transition: all 0.2s ease;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #10b981;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        }}
        .btn {{
            background: #059669;
            border: none;
            color: #fff;
            padding: 10px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            user-select: none;
        }}
        .btn:hover {{ background: #10b981; }}
        .btn-secondary {{
            background: #374151;
            border: 1px solid #4b5563;
        }}
        .btn-secondary:hover {{ background: #4b5563; }}
        .meta-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            color: #9ca3af;
            border-top: 1px solid #374151;
            padding-top: 14px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .meta-item span {{
            color: #f3f4f6;
            font-weight: 600;
        }}
        .hint-badge {{
            background: #111827;
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid #374151;
            color: #10b981;
            font-size: 12px;
        }}
        .content {{
            padding: 0;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
        }}
        th {{
            background: #1f2937;
            color: #9ca3af;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 16px 24px;
            border-bottom: 2px solid #374151;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s ease;
        }}
        th:hover {{
            background: #2563eb;
            color: #fff;
        }}
        th .sort-icon {{
            margin-left: 8px;
            display: inline-block;
            font-size: 11px;
            opacity: 0.5;
        }}
        th.sort-asc, th.sort-desc {{
            color: #fff;
            background: #2563eb;
        }}
        td {{
            padding: 16px 24px;
            border-bottom: 1px solid #1f2937;
            color: #e5e7eb;
            vertical-align: middle;
        }}
        tr:hover td {{
            background: #1f2937;
        }}
        .label-cell strong {{
            color: #60a5fa;
            font-size: 15px;
        }}
        .password-cell .password {{
            font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
            color: #34d399;
            font-weight: bold;
            cursor: pointer;
            background: rgba(52, 211, 153, 0.1);
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(52, 211, 153, 0.2);
            display: inline-block;
            transition: all 0.2s ease;
            font-size: 13px;
            word-break: break-all;
            max-width: 400px;
        }}
        .password-cell .password:hover {{
            color: #fbbf24;
            background: rgba(251, 191, 36, 0.1);
            border-color: rgba(251, 191, 36, 0.3);
            transform: translateY(-1px);
        }}
        .date-cell {{
            color: #9ca3af;
            font-size: 13px;
            font-family: monospace;
        }}
        .id-cell {{
            color: #6b7280;
            font-weight: 600;
            width: 60px;
        }}
        mark.highlight {{
            background: #b45309;
            color: #fff;
            padding: 2px 4px;
            border-radius: 4px;
        }}
        .footer {{
            background: #111827;
            padding: 20px 30px;
            text-align: center;
            color: #6b7280;
            font-size: 13px;
            border-top: 1px solid #1f2937;
        }}
        .toast {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #10b981;
            color: #fff;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.3);
            transform: translateY(100px);
            opacity: 0;
            pointer-events: none;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .toast.show {{
            transform: translateY(0);
            opacity: 1;
        }}

        @media print {{
            body {{ background: #fff; color: #000; padding: 0; margin: 0; }}
            .container {{ border: none; box-shadow: none; max-width: 100%; background: #fff; }}
            .control-panel, .hint-badge, th .sort-icon {{ display: none !important; }}
            .header {{ background: #f3f4f6 !important; border-bottom: 2px solid #000; padding: 15px; color: #000; }}
            .header h1 {{ color: #000; }}
            .header p {{ color: #374151; }}
            th {{ background: #e5e7eb !important; color: #000 !important; border-bottom: 2px solid #000; padding: 10px 12px; }}
            td {{ color: #000 !important; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; background: transparent !important; }}
            .password-cell .password {{ background: none !important; border: none !important; padding: 0; color: #000 !important; }}
            .label-cell strong {{ color: #000 !important; }}
        }}

        @media (max-width: 768px) {{
            td, th {{ padding: 12px 16px; }}
            .password-cell .password {{ font-size: 11px; padding: 4px 8px; max-width: 200px; }}
            .container {{ margin: 10px; }}
            body {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{L.get('export_app', 'Secure Pass Pro v4.0')}</h1>
            <p>{L.get('export_passwords', 'Passwords Export / Экспорт паролей / Експорт паролів')}</p>
        </div>
        <div class="control-panel">
            <div class="search-row">
                <div class="search-wrapper">
                    <input type="text" id="searchInput" class="search-box" placeholder="{search_placeholder}" oninput="filterTable()">
                </div>
                <button class="btn btn-secondary" onclick="clearSearch()">{reset_btn_text}</button>
                <button class="btn" onclick="window.print()">{print_btn_text}</button>
            </div>
            <div class="meta-row">
                <div class="meta-item">{L.get('db_count', 'Records / Записей / Записів')}: <span id="recordCount">{data_count}</span></div>
                <div class="meta-item">{L.get('export_date', 'Export date / Дата экспорта / Дата експорту')}: <span>{now}</span></div>
                <div class="meta-item hint-badge">{copy_hint_text}</div>
            </div>
        </div>
        <div class="content">
            <table id="passwordTable">
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody id="tableBody">{rows}</tbody>
            </table>
        </div>
        <div class="footer">
            {L.get('export_app', 'Secure Pass Pro v4.0')} (c) {datetime.datetime.now().year} | {footer_text}
        </div>
    </div>

    <div id="copyToast" class="toast">{copied_toast_text}</div>

    <script>
        let currentSortCol = -1;
        let isSortAsc = true;

        function filterTable() {{
            const input = document.getElementById('searchInput');
            const query = input.value.trim().toLowerCase();
            const tbody = document.getElementById('tableBody');
            const rows = tbody.querySelectorAll('tr');
            let matchedCount = 0;

            rows.forEach(row => {{
                let rowMatches = false;
                const cells = row.querySelectorAll('td');

                cells.forEach(cell => {{
                    const targetElement = cell.querySelector('[data-value]') || cell;
                    const originalText = targetElement.getAttribute('data-value') || targetElement.innerText || '';

                    if (query === '') {{
                        targetElement.innerHTML = originalText;
                        rowMatches = true;
                    }} else if (originalText.toLowerCase().includes(query)) {{
                        rowMatches = true;
                        const regex = new RegExp('(' + escapeRegExp(query) + ')', 'gi');
                        targetElement.innerHTML = originalText.replace(regex, '<mark class="highlight">$1</mark>');
                    }} else {{
                        targetElement.innerHTML = originalText;
                    }}
                }});

                if (rowMatches) {{
                    row.style.display = '';
                    matchedCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            document.getElementById('recordCount').innerText = matchedCount;
        }}

        function clearSearch() {{
            document.getElementById('searchInput').value = '';
            filterTable();
        }}

        function escapeRegExp(string) {{
            return string.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        }}

        function sortTable(colIndex) {{
            const tbody = document.getElementById('tableBody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = document.querySelectorAll('th');

            if (currentSortCol === colIndex) {{
                isSortAsc = !isSortAsc;
            }} else {{
                currentSortCol = colIndex;
                isSortAsc = true;
            }}

            headers.forEach((th, idx) => {{
                th.classList.remove('sort-asc', 'sort-desc');
                if (idx === colIndex) {{
                    th.classList.add(isSortAsc ? 'sort-asc' : 'sort-desc');
                }}
            }});

            rows.sort((rowA, rowB) => {{
                const cellA = rowA.cells[colIndex];
                const cellB = rowB.cells[colIndex];

                const targetA = cellA.querySelector('[data-value]') || cellA;
                const targetB = cellB.querySelector('[data-value]') || cellB;

                const valA = targetA.getAttribute('data-value') || targetA.innerText;
                const valB = targetB.getAttribute('data-value') || targetB.innerText;
                const fieldType = targetA.getAttribute('data-field') || cellA.getAttribute('class');

                if (fieldType === 'id-cell' || (colIndex === 0 && !isNaN(valA) && !isNaN(valB))) {{
                    return isSortAsc ? parseInt(valA) - parseInt(valB) : parseInt(valB) - parseInt(valA);
                }}

                if (fieldType === 'date-cell' && valA.includes('-') && valB.includes('-')) {{
                    return isSortAsc ? new Date(valA) - new Date(valB) : new Date(valB) - new Date(valA);
                }}

                return isSortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}

        document.getElementById('tableBody').addEventListener('click', function(e) {{
            const target = e.target.closest('.password');
            if (!target) return;

            const textToCopy = target.getAttribute('data-value') || target.innerText;

            navigator.clipboard.writeText(textToCopy).then(() => {{
                const toast = document.getElementById('copyToast');
                toast.classList.add('show');
                setTimeout(() => {{
                    toast.classList.remove('show');
                }}, 2000);
            }}).catch(err => {{
                console.error('Copy failed: ', err);
            }});
        }});
    </script>
</body>
</html>"""

    @staticmethod
    def show_export_dialog(data: List[Dict[str, Any]], parent, lang: str = "RU") -> None:
        """Extended dialog for export format selection
        Расширенный диалог выбора формата экспорта
        Розширений діалог вибору формату експорту"""
        from storage.database import PasswordDB
        from gui.dialogs import CTkMessageBox
        import customtkinter as ctk
        from Langs.lang import LANGUAGES

        if not data:
            data = PasswordDB.get_all()

        if not data:
            CTkMessageBox.warning(parent, "Export / Экспорт / Експорт", LANGUAGES.get(lang, LANGUAGES["RU"]).get("export_no_data", "No data to export! / Нет данных для экспорта! / Немає даних для експорту!"))
            return

        L = LANGUAGES.get(lang, LANGUAGES["RU"])

        win = ctk.CTkToplevel(parent)
        win.title(L.get("export_title", "Export Data / Экспорт данных / Експорт даних"))
        win.geometry("750x700")
        win.resizable(False, False)
        win.transient(parent)
        win.grab_set()
        win.attributes("-topmost", True)

        win.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 750) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 700) // 2
        win.geometry(f"750x700+{x}+{y}")

        format_var = tk.StringVar(value="json")
        encrypt_var = tk.BooleanVar(value=False)
        encrypt_password = tk.StringVar()
        encrypt_error_label = None

        # ── Формат экспорта ───────────────────────────────────────
        ctk.CTkLabel(win, text=L.get("export_format", "Формат экспорта:"),
                    font=("Segoe UI", 14, "bold"), anchor="center").pack(pady=(18, 6))

        FORMATS = [
            ("JSON",              "json"),
            ("CSV",               "csv"),
            ("HTML",              "html"),
            ("🔐 KeePass (.kdbx)", "kdbx"),
        ]

        def _pick_format(display, value) -> None:
            """
            Handle pick format.
            Обработать pick format.
            Обробити pick format.
            """
            format_var.set(value)
            fmt_btn.configure(text=f"  {display}  ▾")

        def _show_format_menu() -> None:
            """
            Show format menu.
            Показать format menu.
            Показати format menu.
            """
            m_kw = dict(tearoff=0, font=("Segoe UI", 12),
                        bg="#2b2b2b", fg="white",
                        activebackground="#3a7bd5", activeforeground="white",
                        bd=0, relief="flat")
            menu = tk.Menu(win, **m_kw)
            for display, value in FORMATS:
                menu.add_command(label=f"  {display}",
                    command=lambda d=display, v=value: _pick_format(d, v))
            menu.tk_popup(fmt_btn.winfo_rootx(),
                          fmt_btn.winfo_rooty() + fmt_btn.winfo_height())

        fmt_btn = ctk.CTkButton(win, text="  JSON  ▾",
            width=220, height=38, font=("Segoe UI", 13, "bold"),
            fg_color="#2b2b2b", hover_color="#3a3a3a",
            text_color="white", border_color="#555", border_width=1,
            corner_radius=8, anchor="center", command=_show_format_menu)
        fmt_btn.pack(anchor="center", pady=(0, 8))

        ctk.CTkFrame(win, height=2, fg_color="gray").pack(fill="x", padx=20, pady=8)

        # ── Поля экспорта ─────────────────────────────────────────
        field_names = {
            'id':       ("#",                                     "🔢"),
            'label':    (L.get("db_edit_label",    "Метка"),     "📝"),
            'password': (L.get("pdf_pass",         "Пароль"),    "🔑"),
            'url':      (L.get("export_url",       "URL"),       "🌐"),
            'username': (L.get("export_username",  "Логин"),     "👤"),
            'email':    (L.get("export_email",     "Email"),     "📧"),
            'category': (L.get("export_category",  "Категория"), "🗂"),
            'created':  (L.get("pdf_date",         "Дата"),      "📅"),
            'notes':    (L.get("db_notes",         "Заметки"),   "📋"),
        }
        field_vars = {
            'id':       tk.BooleanVar(value=True),
            'label':    tk.BooleanVar(value=True),
            'password': tk.BooleanVar(value=True),
            'url':      tk.BooleanVar(value=True),
            'username': tk.BooleanVar(value=True),
            'email':    tk.BooleanVar(value=False),
            'category': tk.BooleanVar(value=True),
            'created':  tk.BooleanVar(value=True),
            'notes':    tk.BooleanVar(value=False),
        }

        fields_preview = ctk.CTkLabel(win, text="", font=("Segoe UI", 11),
            text_color="gray", anchor="center", wraplength=680)
        fields_preview.pack(pady=(0, 4))

        def _update_preview() -> None:
            """
            Update preview.
            Обновить preview.
            Оновити preview.
            """
            selected = [f"{field_names[k][1]} {field_names[k][0]}"
                        for k, v in field_vars.items() if v.get()]
            fields_preview.configure(text="  ".join(selected) if selected else "—")

        def _show_fields_popup() -> None:
            """
            Show fields popup.
            Показать fields popup.
            Показати fields popup.
            """
            popup = ctk.CTkToplevel(win)
            popup.title(L.get("export_fields_btn", "Поля экспорта"))
            popup.resizable(False, False)
            popup.grab_set()
            popup.lift()
            popup.focus_force()
            pw, ph = 300, 520
            popup.after(10, lambda: (
                popup.update_idletasks(),
                popup.geometry(
                    f"{pw}x{ph}+"
                    f"{win.winfo_rootx() + (win.winfo_width() - pw) // 2}+"
                    f"{win.winfo_rooty() + (win.winfo_height() - ph) // 2}")))

            ctk.CTkLabel(popup,
                text=L.get("export_fields_btn", "Выберите поля:"),
                font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=20, pady=(16, 8))
            ctk.CTkFrame(popup, height=1, fg_color="gray").pack(fill="x", padx=20, pady=(0, 8))

            for field, (name, icon) in field_names.items():
                ctk.CTkCheckBox(popup, text=f"{icon}  {name}",
                    variable=field_vars[field], font=("Segoe UI", 13),
                    command=_update_preview, height=32,
                    checkbox_width=20, checkbox_height=20,
                ).pack(anchor="w", padx=24, pady=3)

            ctk.CTkFrame(popup, height=1, fg_color="gray").pack(fill="x", padx=20, pady=(8, 0))

            btn_row = ctk.CTkFrame(popup, fg_color="transparent")
            btn_row.pack(pady=10)
            def _all() -> None:
                """
                Handle all.
                Обработать all.
                Обробити all.
                """
                for v in field_vars.values(): v.set(True); _update_preview()
            def _none() -> None:
                """
                Handle none.
                Обработать none.
                Обробити none.
                """
                for v in field_vars.values(): v.set(False); _update_preview()
            ctk.CTkButton(btn_row, text="✔ " + L.get("select_all", "Все"),
                command=_all, width=80, height=32, font=("Segoe UI", 12),
                fg_color="#1565C0", hover_color="#1976D2").pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text="✖ " + L.get("select_none", "Снять"),
                command=_none, width=80, height=32, font=("Segoe UI", 12),
                fg_color="#555", hover_color="#666").pack(side="left", padx=5)
            ctk.CTkButton(popup, text="✔  OK",
                command=popup.destroy, width=200, height=38,
                font=("Segoe UI", 13, "bold"),
                fg_color="#107c10", hover_color="#159e15").pack(pady=(0, 14))

        ctk.CTkButton(win,
            text="📋 " + L.get("export_fields_btn", "Выбрать поля для экспорта"),
            width=240, height=36, font=("Segoe UI", 12, "bold"),
            fg_color="#1565C0", hover_color="#1976D2",
            command=_show_fields_popup).pack(anchor="center", pady=(0, 6))
        _update_preview()

        ctk.CTkFrame(win, height=2, fg_color="gray").pack(fill="x", padx=20, pady=8)

        # ── Кодировка — каскадное меню как Notepad++ ──────────────
        ctk.CTkLabel(win, text=L.get("export_encoding_short", "Кодировка:"),
            font=("Segoe UI", 13, "bold"), anchor="center").pack(pady=(4, 6))

        encoding_var  = tk.StringVar(value="utf-8-sig")

        ENCODING_GROUPS = {
            "Арабский": [("ISO 8859-6","iso-8859-6"),("OEM 720","cp720"),("Windows-1256","cp1256")],
            "Балтийский": [("ISO 8859-4","iso-8859-4"),("ISO 8859-13","iso-8859-13"),("OEM 775","cp775"),("Windows-1257","cp1257")],
            "Кельтский": [("ISO 8859-14","iso-8859-14")],
            "Кириллица": [("ISO 8859-5","iso-8859-5"),("KOI8-R","koi8-r"),("KOI8-U","koi8-u"),("Mac Cyrillic","mac-cyrillic"),("OEM 855","cp855"),("OEM 866","cp866"),("Windows-1251","cp1251")],
            "Центрально-Европейский": [("OEM 852","cp852"),("Windows-1250","cp1250")],
            "Китайский": [("Big5 (Традиционный)","big5"),("GB2312 (Упрощённый)","gb2312")],
            "Восточно-Европейский": [("ISO 8859-2","iso-8859-2")],
            "Греческий": [("ISO 8859-7","iso-8859-7"),("OEM 737","cp737"),("OEM 869","cp869"),("Windows-1253","cp1253")],
            "Иврит": [("ISO 8859-8","iso-8859-8"),("OEM 862","cp862"),("Windows-1255","cp1255")],
            "Японский": [("Shift-JIS","shift-jis")],
            "Корейский": [("Windows-949","cp949"),("EUC-KR","euc-kr")],
            "Северо-Европейский": [("OEM 861: Исландский","cp861"),("OEM 865: Нордический","cp865")],
            "Тайский": [("TIS-620","tis-620")],
            "Турецкий": [("ISO 8859-3","iso-8859-3"),("ISO 8859-9","iso-8859-9"),("OEM 857","cp857"),("Windows-1254","cp1254")],
            "Западно-Европейский": [("ISO 8859-1","iso-8859-1"),("ISO 8859-15","iso-8859-15"),("OEM 850","cp850"),("OEM 858","cp858"),("OEM 860: Португальский","cp860"),("OEM 863: Французский","cp863"),("OEM-US","cp437"),("Windows-1252","cp1252")],
            "Вьетнамский": [("Windows-1258","cp1258")],
        }

        def _pick_enc(display, codec) -> None:
            """
            Handle pick enc.
            Обработать pick enc.
            Обробити pick enc.
            """
            encoding_var.set(codec)
            enc_btn.configure(text=f"  {display}  ▾")

        def _show_enc_menu() -> None:
            """
            Show enc menu.
            Показать enc menu.
            Показати enc menu.
            """
            m_kw = dict(tearoff=0, font=("Segoe UI", 11),
                        bg="#2b2b2b", fg="white",
                        activebackground="#3a7bd5", activeforeground="white",
                        bd=0, relief="flat")
            menu = tk.Menu(win, **m_kw)
            for display, codec in [
                ("Кодировка ANSI",           "cp1252"),
                ("Кодировка UTF-8",          "utf-8"),
                ("Кодировка UTF-8 с BOM",    "utf-8-sig"),
                ("Кодировка UTF-16 BE с BOM","utf-16-be"),
                ("Кодировка UTF-16 LE с BOM","utf-16"),
            ]:
                menu.add_command(label=display,
                    command=lambda d=display, c=codec: _pick_enc(d, c))
            menu.add_separator()
            sub_groups = tk.Menu(menu, **m_kw)
            for group_name, items in ENCODING_GROUPS.items():
                sub = tk.Menu(sub_groups, **m_kw)
                for display, codec in items:
                    sub.add_command(label=display,
                        command=lambda d=display, c=codec: _pick_enc(d, c))
                sub_groups.add_cascade(label=group_name, menu=sub)
            menu.add_cascade(label="Кодировки", menu=sub_groups)
            menu.add_separator()
            for display, codec in [
                ("Преобразовать в ANSI",             "cp1252"),
                ("Преобразовать в UTF-8",            "utf-8"),
                ("Преобразовать в UTF-8 с BOM",      "utf-8-sig"),
                ("Преобразовать в UTF-16 BE с BOM",  "utf-16-be"),
                ("Преобразовать в UTF-16 LE с BOM",  "utf-16"),
            ]:
                menu.add_command(label=display,
                    command=lambda d=display, c=codec: _pick_enc(d, c))
            menu.tk_popup(enc_btn.winfo_rootx(),
                          enc_btn.winfo_rooty() + enc_btn.winfo_height())

        enc_btn = ctk.CTkButton(win, text="  Кодировка UTF-8 с BOM  ▾",
            width=260, height=36, font=("Segoe UI", 12),
            fg_color="#2b2b2b", hover_color="#3a3a3a",
            text_color="white", border_color="#555", border_width=1,
            corner_radius=6, anchor="center", command=_show_enc_menu)
        enc_btn.pack(anchor="center", pady=(0, 8))

        if CRYPTO_AVAILABLE:
            encrypt_check = ctk.CTkCheckBox(win, text=L.get("export_encrypt", "Encrypt export (requires password) / Шифровать экспорт (требуется пароль) / Шифрувати експорт (потрібен пароль)"),
                                           variable=encrypt_var, font=("Segoe UI", 12))
            encrypt_check.pack(pady=(10, 5))

            encrypt_frame = ctk.CTkFrame(win, fg_color="transparent")
            encrypt_frame.pack(pady=5, fill="x", padx=20)

            center_frame = ctk.CTkFrame(encrypt_frame, fg_color="transparent")
            center_frame.pack(anchor="center")

            ctk.CTkLabel(center_frame, text=L.get("export_encrypt_password", "Encryption password: / Пароль шифрования: / Пароль шифрування:"),
                        font=("Segoe UI", 12)).pack(anchor="center", pady=(0, 5))
            encrypt_entry = ctk.CTkEntry(center_frame, textvariable=encrypt_password,
                                         show="*", width=300, height=35)
            encrypt_entry.pack(anchor="center")

            encrypt_error_label = ctk.CTkLabel(encrypt_frame, text="", font=("Segoe UI", 11), text_color="#E24B4A")
            encrypt_error_label.pack(pady=(5, 0))

            def validate_password(*args) -> None:
                """
                Handle validate password.
                Обработать validate password.
                Обробити validate password.
                """
                if encrypt_var.get():
                    pwd = encrypt_password.get()
                    is_valid, error = validate_export_password(pwd)
                    if not is_valid and pwd:
                        encrypt_error_label.configure(text=error)
                    else:
                        encrypt_error_label.configure(text="")

            encrypt_password.trace_add("write", validate_password)

            def on_encrypt_change() -> None:
                """
                Handle the encrypt change event.
                Обработчик encrypt change.
                Обробник encrypt change.
                """
                if encrypt_var.get():
                    encrypt_entry.configure(state="normal")
                    validate_password()
                else:
                    encrypt_entry.configure(state="disabled")
                    encrypt_password.set("")
                    encrypt_error_label.configure(text="")

            encrypt_var.trace_add("write", lambda *args: on_encrypt_change())
            on_encrypt_change()
        else:
            ctk.CTkLabel(win, text="Encryption not available (install cryptography) / Шифрование недоступно (установите cryptography) / Шифрування недоступне (встановіть cryptography)",
                        font=("Segoe UI", 11), text_color="#FFA500").pack(pady=5)

        def do_export() -> None:
            """
            Handle do export.
            Обработать do export.
            Обробити do export.
            """
            fmt = format_var.get()
            selected_fields = [k for k, v in field_vars.items() if v.get()]

            if not selected_fields:
                CTkMessageBox.warning(win, L.get("export_title", "Export / Экспорт / Експорт"),
                                     L.get("err_cat", "Select at least one category! / Выберите хотя бы одну категорию! / Виберіть хоча б одну категорію!"))
                return

            if encrypt_var.get():
                pwd = encrypt_password.get().strip()
                is_valid, error = validate_export_password(pwd)
                if not is_valid:
                    CTkMessageBox.warning(win, L.get("export_title", "Export / Экспорт / Експорт"), error)
                    return

            extensions = {
                "json": ("JSON files", "*.json"),
                "csv": ("CSV files", "*.csv"),
                "html": ("HTML files", "*.html"),
                "kdbx": ("KeePass files", "*.kdbx"),
            }

            default_ext = f".{fmt}"
            if encrypt_var.get() and fmt == "json":
                default_ext = ".enc.json"

            file_path = filedialog.asksaveasfilename(
                defaultextension=default_ext,
                filetypes=[(extensions[fmt][0], extensions[fmt][1]), ("All files / Все файлы / Всі файли", "*.*")]
            )

            if file_path:
                success = False
                try:
                    export_data = sanitize_export_data(data)

                    if fmt == "json":
                        success = DataExporter.export_json(
                            export_data, file_path, selected_fields,
                            encrypt_var.get(), encrypt_password.get().strip()
                        )
                    elif fmt == "csv":
                        success = DataExporter.export_csv(
                            export_data, file_path, selected_fields, encoding_var.get()
                        )
                    elif fmt == "kdbx":
                        try:
                            from utils.export_kdbx import export_kdbx, export_keepass_xml, PYKEEPASS_AVAILABLE
                            if PYKEEPASS_AVAILABLE:
                                success = export_kdbx(export_data, file_path)
                            else:
                                xml_path = file_path.replace(".kdbx", ".keepass.xml")
                                success = export_keepass_xml(export_data, xml_path)
                                if success:
                                    file_path = xml_path
                        except ImportError:
                            from utils.export_kdbx import export_keepass_xml
                            xml_path = file_path.replace(".kdbx", ".keepass.xml")
                            success = export_keepass_xml(export_data, xml_path)
                            if success:
                                file_path = xml_path
                    elif fmt == "html":
                        if encrypt_var.get():
                            CTkMessageBox.warning(win, L.get("export_title", "Export / Экспорт / Експорт"),
                                                 "Encryption available only for JSON format! / Шифрование доступно только для формата JSON! / Шифрування доступне тільки для формату JSON!")
                            return
                        success = DataExporter.export_html(
                            export_data, file_path, lang, selected_fields
                        )

                    win.destroy()

                    if success:
                        # Main message in 3 languages
                        if lang == "RU":
                            msg = f"Данные экспортированы: {os.path.basename(file_path)}"
                        elif lang == "UA":
                            msg = f"Дані експортовано: {os.path.basename(file_path)}"
                        else:
                            msg = f"Data exported: {os.path.basename(file_path)}"
                        
                        if encrypt_var.get() and fmt == "json":
                            if lang == "RU":
                                msg += "\nФайл зашифрован паролем"
                            elif lang == "UA":
                                msg += "\nФайл зашифровано паролем"
                            else:
                                msg += "\nFile encrypted with password"
                            msg += "\nСохраните пароль - без него расшифровка невозможна!"
                        
                        CTkMessageBox.info(parent, L.get("export_title", "Export / Экспорт / Експорт"), msg)
                    else:
                        CTkMessageBox.error(parent, L.get("err_title", "Error / Ошибка / Помилка"),
                                           L.get("export_error", "Export error / Ошибка экспорта / Помилка експорту"))
                except ExportEncryptionError as e:
                    logger.error(f"Encryption error / Ошибка шифрования / Помилка шифрування: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('export_error', 'Export error / Ошибка экспорта / Помилка експорту')}:\n{str(e)}")
                except (OSError, IOError, PermissionError, ValueError, TypeError) as e:
                    logger.error(f"Export error / Ошибка экспорта / Помилка експорту: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('export_error', 'Export error / Ошибка экспорта / Помилка експорту')}:\n{str(e)}")

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text=L.get("ok", "Export / Экспорт / Експорт"), command=do_export,
                     width=140, height=40, fg_color="#2d6a4f", corner_radius=15,
                     font=("Segoe UI", 13, "bold")).pack(side="left", padx=15)
        ctk.CTkButton(btn_frame, text=L.get("cancel", "Cancel / Отмена / Скасувати"), command=win.destroy,
                     width=140, height=40, fg_color="#8b0000", corner_radius=15,
                     font=("Segoe UI", 13, "bold")).pack(side="left", padx=15)

        win.after(100, lambda: win.attributes("-topmost", False))

    @staticmethod
    def export_all(data: List[Dict[str, Any]], parent, lang: str = "RU") -> None:
        """Simplified dialog for backward compatibility - calls the extended one
        Упрощённый диалог для обратной совместимости - вызывает расширенный
        Спрощений діалог для зворотної сумісності - викликає розширений"""
        DataExporter.show_export_dialog(data, parent, lang)
