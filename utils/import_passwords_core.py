"""
Password import utilities - Core class
Утилиты импорта паролей - Основной класс
Утиліти імпорту паролів - Основний клас

100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import hashlib
import datetime
import sqlite3
import tkinter as tk
from typing import List, Dict, Any, Set, Optional
from utils.logger import get_logger
from utils.import_helpers import (
    PasswordImportError, InvalidFileFormatError, MalformedFileError,
    FileTooLargeError, UnsupportedEncodingError, sanitize_password,
    PasswordImportError as ImportErrorClass
)
from utils.import_json import import_from_json
from utils.import_csv import import_from_csv
from utils.import_keepass_xml import import_from_keepass_xml
from utils.import_bitwarden_json import import_from_bitwarden_json
from utils.import_1password_csv import import_from_1password_csv
from utils.import_1pux import import_from_1pux

logger = get_logger("import_passwords")


class PasswordImporter:
    """Import passwords from various formats
    Импорт паролей из различных форматов
    Імпорт паролів з різних форматів"""

    _imported_hashes: Set[str] = set()

    @classmethod
    def reset_duplicate_tracking(cls) -> None:
        """Reset duplicate tracking / Сбросить отслеживание дубликатов / Скинути відстеження дублікатів"""
        cls._imported_hashes.clear()

    @classmethod
    def _get_password_hash(cls, password: str) -> str:
        """Return password hash for duplicate tracking
        Возвращает хеш пароля для отслеживания дубликатов
        Повертає хеш пароля для відстеження дублікатів"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()[:16]

    @classmethod
    def _check_and_add_duplicate(cls, password: str) -> bool:
        """
        Check and add password to duplicate tracking.

        Проверяет и добавляет пароль в отслеживание дубликатов.
        Перевіряє та додає пароль у відстеження дублікатів.

        Returns:
            True if duplicate, False if new
            True если дубликат, False если новый
            True якщо дублікат, False якщо новий
        """
        pwd_hash = cls._get_password_hash(password)
        if pwd_hash in cls._imported_hashes:
            return True
        cls._imported_hashes.add(pwd_hash)
        return False

    @classmethod
    def import_all(cls, parent, lang: str = "RU") -> None:
        """Dialog for format selection and import - with 1PUX support and duplicate checking
        Диалог выбора формата и импорт - с поддержкой 1PUX и проверкой дубликатов
        Діалог вибору формату та імпорт - з підтримкою 1PUX та перевіркою дублікатів"""
        from storage.database import PasswordDB
        from gui.dialogs import CTkMessageBox
        import customtkinter as ctk
        from localization.lang import LANGUAGES

        cls.reset_duplicate_tracking()

        L = LANGUAGES.get(lang, LANGUAGES["RU"])

        win = ctk.CTkToplevel(parent)
        win.title(L.get("import_title", "Import Passwords / Импорт паролей / Імпорт паролів"))
        win.geometry("500x650")
        win.resizable(False, False)
        win.transient(parent)
        win.grab_set()
        win.lift()
        win.focus_force()
        win.after(100, lambda: win.attributes("-topmost", False) if win and win.winfo_exists() else None)
        win.attributes("-topmost", True)

        try:
            win.update_idletasks()
            parent_x = parent.winfo_x()
            parent_y = parent.winfo_y()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            x = parent_x + (parent_width - 500) // 2
            y = parent_y + (parent_height - 650) // 2
            win.geometry(f"500x650+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Center window error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
            win.geometry("500x650")

        main_frame = ctk.CTkFrame(win, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)

        try:
            title_label = ctk.CTkLabel(main_frame, text=L.get("import_title", "Import Passwords / Импорт паролей / Імпорт паролів"),
                                       font=("Segoe UI", 22, "bold"))
            title_label.pack(pady=(0, 10))
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Title error / Ошибка заголовка / Помилка заголовка: {e}")

        separator = ctk.CTkFrame(main_frame, height=2, fg_color="#2d6a4f")
        separator.pack(fill="x", pady=(0, 15))

        try:
            format_label = ctk.CTkLabel(main_frame, text=L.get("import_format", "Import format: / Формат импорта: / Формат імпорту:"),
                                       font=("Segoe UI", 15, "bold"))
            format_label.pack(pady=(0, 10))
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Format label error / Ошибка метки формата / Помилка мітки формату: {e}")

        format_var = tk.StringVar(value="json")

        formats_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        formats_frame.pack(pady=(0, 15))

        formats = [
            ("json", "JSON (Secure Pass Pro)"),
            ("csv", "CSV (Excel / Google Sheets)"),
            ("keepass", "KeePass XML"),
            ("bitwarden", "Bitwarden JSON"),
            ("onepassword", "1Password CSV"),
            ("1pux", "1PUX (1Password Unified Export)")
        ]

        for fmt, text in formats:
            try:
                rb = ctk.CTkRadioButton(formats_frame, text=text, variable=format_var,
                                        value=fmt, font=("Segoe UI", 12))
                rb.pack(anchor="center", pady=4)
            except (tk.TclError, AttributeError, TypeError) as e:
                logger.debug(f"Radio button error for {fmt}: {e} / Ошибка радиокнопки для {fmt} / Помилка радіокнопки для {fmt}")

        separator2 = ctk.CTkFrame(main_frame, height=1, fg_color="#333333")
        separator2.pack(fill="x", pady=(10, 15))

        warning_frame = ctk.CTkFrame(main_frame, fg_color="#3a2a0a", corner_radius=10)
        warning_frame.pack(fill="x", pady=(0, 20))

        try:
            warning_label = ctk.CTkLabel(warning_frame,
                                        text=L.get("import_warning", "Import only from trusted sources! / Импортируйте только из доверенных источников! / Імпортуйте тільки з перевірених джерел!"),
                                        font=("Segoe UI", 11), text_color="#FFA500")
            warning_label.pack(pady=12, padx=15)
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Warning label error / Ошибка метки предупреждения / Помилка мітки попередження: {e}")

        skip_duplicates_var = tk.BooleanVar(value=True)
        try:
            skip_duplicates_cb = ctk.CTkCheckBox(
                main_frame,
                text=L.get("skip_duplicates", "Skip duplicate passwords / Пропускать дубликаты паролей / Пропускати дублікати паролів"),
                variable=skip_duplicates_var,
                font=("Segoe UI", 12)
            )
            skip_duplicates_cb.pack(pady=(0, 15))
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Skip duplicates checkbox error / Ошибка чекбокса пропуска дубликатов / Помилка чекбокса пропуску дублікатів: {e}")

        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))

        def do_import() -> None:
            fmt = format_var.get()
            extensions = {
                "json": ("JSON files", "*.json"),
                "csv": ("CSV files", "*.csv"),
                "keepass": ("KeePass XML", "*.xml"),
                "bitwarden": ("Bitwarden JSON", "*.json"),
                "onepassword": ("1Password CSV", "*.csv"),
                "1pux": ("1PUX files", "*.1pux")
            }

            from tkinter import filedialog
            try:
                win.attributes("-topmost", False)
                win.update_idletasks()
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError): pass
            path = filedialog.askopenfilename(
                parent=win,
                title="Select file to import / Выберите файл для импорта / Виберіть файл для імпорту",
                filetypes=[(extensions[fmt][0], extensions[fmt][1]), ("All files / Все файлы / Всі файли", "*.*")]
            )

            if path:
                try:
                    if fmt == "json":
                        passwords = import_from_json(path)
                    elif fmt == "csv":
                        passwords = import_from_csv(path)
                    elif fmt == "keepass":
                        passwords = import_from_keepass_xml(path)
                    elif fmt == "bitwarden":
                        passwords = import_from_bitwarden_json(path)
                    elif fmt == "onepassword":
                        passwords = import_from_1password_csv(path)
                    elif fmt == "1pux":
                        passwords = import_from_1pux(path)
                    else:
                        passwords = []

                    if not passwords:
                        CTkMessageBox.warning(win, L.get("import_title", "Import / Импорт / Імпорт"),
                                             L.get("import_no_passwords", "No passwords found in file! / В файле не найдено паролей! / У файлі не знайдено паролів!"))
                        return

                    skip_duplicates = skip_duplicates_var.get()
                    filtered_passwords = []
                    duplicates_count = 0

                    for pwd in passwords:
                        if skip_duplicates and cls._check_and_add_duplicate(pwd['password']):
                            duplicates_count += 1
                            logger.debug("Duplicate password skipped / Дубликат пароля пропущен / Дублікат пароля пропущено")
                        else:
                            filtered_passwords.append(pwd)

                    if duplicates_count > 0:
                        logger.info(f"Skipped {duplicates_count} duplicate passwords / Пропущено {duplicates_count} дубликатов паролей / Пропущено {duplicates_count} дублікатів паролів")

                    preview_lines = []
                    for p in filtered_passwords[:10]:
                        preview_lines.append(f"- {p['label'][:50]}")
                    preview = "\n".join(preview_lines)
                    if len(filtered_passwords) > 10:
                        preview += f"\n... and {len(filtered_passwords) - 10} more / ... и ещё {len(filtered_passwords) - 10} / ... та ще {len(filtered_passwords) - 10}"

                    if duplicates_count > 0:
                        preview += f"\n\nSkipped duplicates: {duplicates_count} / Пропущено дубликатов: {duplicates_count} / Пропущено дублікатів: {duplicates_count}"

                    if not CTkMessageBox.question(win, L.get("import_title", "Import / Импорт / Імпорт"),
                        f"{L.get('import_found', 'Passwords found / Найдено паролів / Знайдено паролів')}: {len(filtered_passwords)}\n\n{preview}\n\n{L.get('import_confirm', 'Import? / Импортировать? / Імпортувати?')}"):
                        return

                    imported = 0
                    failed = 0
                    for pwd in filtered_passwords:
                        try:
                            # Sanitise fields from external source
                            from core.validators import sanitize_label, sanitize_notes
                            _lbl = sanitize_label(str(pwd.get('label', '') or ''))
                            _pwd = str(pwd.get('password', '') or '')[:1024]
                            _nts = sanitize_notes(str(pwd.get('notes', '') or ''))
                            if not _lbl:  # skip empty labels
                                failed += 1
                                continue
                            PasswordDB.save(_lbl, _pwd, _nts)
                            imported += 1
                        except (OSError, IOError, sqlite3.Error, ValueError) as e:
                            logger.error(f"Import save error / Ошибка сохранения при импорте / Помилка збереження при імпорті: {e}")
                            failed += 1

                    win.destroy()

                    result_msg = L.get("import_success", "Imported: {0} / Импортировано: {0} / Імпортовано: {0}").format(imported)
                    if failed > 0:
                        result_msg += f"\nFailed to import: {failed} / Не удалось импортировать: {failed} / Не вдалося імпортувати: {failed}"
                    if duplicates_count > 0:
                        result_msg += f"\nSkipped duplicates: {duplicates_count} / Пропущено дубликатов: {duplicates_count} / Пропущено дублікатів: {duplicates_count}"

                    CTkMessageBox.info(parent, L.get("import_title", "Import / Импорт / Імпорт"), result_msg)

                    if hasattr(parent, '_refresh_db_window'):
                        parent._refresh_db_window()
                    elif hasattr(parent, 'refresh'):
                        parent.refresh()
                    elif hasattr(parent, 'parent') and hasattr(parent.parent, '_refresh_db_window'):
                        parent.parent._refresh_db_window()

                except FileTooLargeError as e:
                    logger.error(f"File too large / Файл слишком большой / Файл занадто великий: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_file_too_large', 'File too large / Файл слишком большой / Файл занадто великий')}")
                except InvalidFileFormatError as e:
                    logger.error(f"Invalid format / Неверный формат / Невірний формат: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_invalid_format', 'Invalid file format / Неверный формат файла / Невірний формат файлу')}")
                except MalformedFileError as e:
                    logger.error(f"Malformed file / Повреждённый файл / Пошкоджений файл: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_malformed', 'File corrupted / Файл повреждён / Файл пошкоджено')}")
                except UnsupportedEncodingError as e:
                    logger.error(f"Unsupported encoding / Неподдерживаемая кодировка / Непідтримуване кодування: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{L.get('err_encoding', 'Unsupported file encoding / Неподдерживаемая кодировка файла / Непідтримуване кодування файлу')}")
                except ImportErrorClass as e:
                    logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{str(e)}")
                except (ValueError, TypeError, AttributeError) as e:
                    logger.error(f"Import error / Ошибка импорта / Помилка імпорту: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('import_error', 'Import error / Ошибка импорта / Помилка імпорту')}:\n{str(e)}")
                except sqlite3.Error as e:
                    logger.error(f"Database error during import / Ошибка БД при импорте / Помилка БД при імпорті: {e}")
                    CTkMessageBox.error(win, L.get("err_title", "Error / Ошибка / Помилка"),
                                       f"{L.get('err_database', 'Database error / Ошибка базы данных / Помилка бази даних')}:\n{str(e)}")

        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.pack(expand=True)

        try:
            import_btn = ctk.CTkButton(button_container, text=L.get("ok", "Import / Импорт / Імпорт"),
                                      command=do_import, width=160, height=40,
                                      fg_color="#2d6a4f", hover_color="#40916c",
                                      corner_radius=20, font=("Segoe UI", 14, "bold"))
            import_btn.pack(side="left", padx=(0, 20))
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Import button error / Ошибка кнопки импорта / Помилка кнопки імпорту: {e}")

        try:
            cancel_btn = ctk.CTkButton(button_container, text=L.get("cancel", "Cancel / Отмена / Скасувати"),
                                      command=win.destroy, width=160, height=40,
                                      fg_color="#8b0000", hover_color="#cc0000",
                                      corner_radius=20, font=("Segoe UI", 14, "bold"))
            cancel_btn.pack(side="left")
        except (tk.TclError, KeyError, TypeError) as e:
            logger.debug(f"Cancel button error / Ошибка кнопки отмены / Помилка кнопки скасування: {e}")

        win.after(100, lambda: win.attributes("-topmost", False))
