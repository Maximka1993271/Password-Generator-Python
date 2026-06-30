"""
Main application window - Event methods
Главное окно приложения - Методы обработки событий
Головне вікно програми - Методи обробки подій

This file contains main event handlers: _generate, _copy, _save, _open

Этот файл содержит основные обработчики событий: _generate, _copy, _save, _open
Цей файл містить основні обробники подій: _generate, _copy, _save, _open

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import os
import time
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from core.generator import SecurePasswordContext, _clear_string
from storage.database import PasswordDB
from gui.dialogs import CTkMessageBox
from utils.helpers import play_sound, is_windows, is_macos
from utils.logger import get_logger
from Langs.lang import LANGUAGES

try:
    import sqlite3
except ImportError:
    sqlite3 = None

try:
    from cryptography.exceptions import InvalidTag
except ImportError:
    InvalidTag = Exception

logger = get_logger("main_window_events")


class EventMethods:
    """Event handler methods for SecurePassPro

    Методы-обработчики событий для SecurePassPro
    Методи-обробники подій для SecurePassPro
    """

    # Attributes provided by the main SecurePassPro class (via MRO)
    # Declared here to satisfy pylint E1101 in mixin analysis
    if False:  # pragma: no cover  # pylint: disable=using-constant-test
        btn_gen: Optional[ctk.CTkButton] = None
        generator = None
        upper_var = None
        lower_var = None
        digits_var = None
        symb_var = None
        ambig_var = None
        unambig_var = None
        at_least_var = None
        no_repeat_var = None
        slider_len = None
        entry_res = None
        current_lang: str = "RU"
        sound_enabled = None
        auto_save_var = None
        history: List[str] = []

    def _generate(self) -> None:
        """
        Generate password with secure clearing and duplicate checking

        Генерация пароля с безопасной очисткой и проверкой дубликатов
        Генерація пароля з безпечним очищенням та перевіркою дублікатів
        """
        if hasattr(self, 'btn_gen') and self.btn_gen:
            self._animate_button(self.btn_gen)

        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])

        self.generator.use_upper = self.upper_var.get()
        self.generator.use_lower = self.lower_var.get()
        self.generator.use_digits = self.digits_var.get()
        self.generator.use_special = self.symb_var.get()
        self.generator.exclude_ambiguous = self.ambig_var.get()
        self.generator.exclude_unambiguous = self.unambig_var.get()
        self.generator.min_each = self.at_least_var.get()
        self.generator.no_repeat = self.no_repeat_var.get()
        self.generator.length = int(self.slider_len.get())

        if not (self.generator.use_upper or self.generator.use_lower or
                self.generator.use_digits or self.generator.use_special):
            CTkMessageBox.warning(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                L.get("err_cat", "Select at least one category! / Выберите хотя бы одну категорию! / Виберіть хоча б одну категорію!")
            )
            return

        try:
            with SecurePasswordContext() as ctx:
                secure_pwd = self.generator.generate_secure()

                if secure_pwd is None and self.generator.no_repeat:
                    CTkMessageBox.warning(
                        self,
                        L.get("err_title", "Error / Ошибка / Помилка"),
                        L.get("err_no_repeat", "Could not generate password without repeats") +
                        L.get("err_no_repeat_fallback", "\nPassword with repeats used")
                    )
                    self.generator.no_repeat = False
                    secure_pwd = self.generator.generate_secure()
                    self.generator.no_repeat = True

                if secure_pwd is None:
                    CTkMessageBox.warning(
                        self,
                        L.get("err_title", "Error / Ошибка / Помилка"),
                        L.get("err_pool_small", "Too few available characters! / Слишком мало доступных символов! / Занадто мало доступних символів!")
                    )
                    return

                password: str = secure_pwd.get_string()
                ctx.set_password(secure_pwd)

                if password:
                    is_valid, validation_msg = self._validate_password_strength(password)
                    if not is_valid:
                        L_local: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
                        if not CTkMessageBox.question(
                            self,
                            L_local.get("warn", "Warning / Предупреждение / Попередження"),
                            f"{validation_msg}\n\n{L_local.get('continue_anyway', 'Continue anyway? / Всё равно продолжить? / Все одно продовжити?')}"
                        ):
                            _clear_string(password)
                            return

                    if self.auto_save_var.get() and self._check_duplicate_password(password):
                        L_local = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
                        if not CTkMessageBox.question(
                            self,
                            L_local.get("warn", "Warning / Предупреждение / Попередження"),
                            L_local.get("duplicate_warning", "This password already exists in the database.\n\nSave anyway? / Этот пароль уже существует в базе.\n\nСохранить всё равно? / Цей пароль вже існує в базі.\n\nЗберегти все одно?")
                        ):
                            _clear_string(password)
                            return

                    try:
                        self.entry_res.delete(0, "end")
                        self.entry_res.insert(0, password)
                        self.history.append(password)
                        self._update_strength_meter(password)
                        play_sound("generate", self.sound_enabled.get())
                    except (tk.TclError, AttributeError, RuntimeError) as e:
                        logger.error(f"UI update error / Ошибка обновления интерфейса / Помилка оновлення інтерфейсу: {e}")

                    if self.auto_save_var.get():
                        import datetime
                        label: str = f"Auto {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        label = self._sanitize_label(label)
                        try:
                            from core.validators import validate, LabelValidator, PasswordValidator
                            _errs = validate(
                                label,    LabelValidator(required=True),
                                password, PasswordValidator(required=True, min_length=1),
                            )
                            if _errs:
                                logger.warning("AutoSave validation failed: %s", _errs)
                                return  # skip saving invalid data silently
                            PasswordDB.save(label, password)
                            logger.debug("[AutoSave] Saved password record / [Автосохранение] Запись пароля сохранена / [Автозбереження] Запис пароля збережено")
                        except (sqlite3.Error, ValueError, OSError, IOError) as exc:
                            logger.error(f"AutoSave error / Ошибка автосохранения / Помилка автозбереження: {exc}")
                            CTkMessageBox.error(
                                self,
                                L.get("err_title", "Error / Ошибка / Помилка"),
                                L.get("err_save", "Save failed: {0}").format(exc)
                            )

                    _clear_string(password)

        except InvalidTag as e:
            logger.error(f"Invalid authentication tag during generation / Неверный тег аутентификации при генерации / Невірний тег аутентифікації при генерації: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                "Encryption error: invalid authentication tag / Ошибка шифрования: неверный тег аутентификации / Помилка шифрування: невірний тег аутентифікації"
            )
        except (ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Value error during generation / Ошибка значения при генерації / Помилка значення при генерації: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"Generation error / Ошибка генерации / Помилка генерації: {e}"
            )
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"IO error during generation / Ошибка ввода-вывода при генерации / Помилка введення-виведення при генерації: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"IO error / Ошибка ввода-вывода / Помилка введення-виведення: {e}"
            )

    def _copy(self) -> None:
        """
        Copy password to clipboard with secure clearing

        Копировать пароль в буфер обмена с безопасной очисткой
        Копіювати пароль у буфер обміну з безпечним очищенням
        """
        if hasattr(self, 'btn_copy') and self.btn_copy:
            self._animate_button(self.btn_copy)

        pwd: str = self.entry_res.get().strip()

        if not pwd:
            CTkMessageBox.warning(
                self,
                "Warning / Внимание / Увага",
                "No password to copy! / Нет пароля для копирования! / Немає пароля для копіювання!"
            )
            return

        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])

        if hasattr(self, '_clipboard_timer') and self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Clipboard timer cancel error / Ошибка отмены таймера буфера / Помилка скасування таймера буфера: {e}")

        try:
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.update()

            logger.info(f"Password copied to clipboard (length: {len(pwd)}) / Пароль скопирован в буфер обмена (длина: {len(pwd)}) / Пароль скопійовано в буфер обміну (довжина: {len(pwd)})")
            play_sound("copy", self.sound_enabled.get())

        except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
            logger.error(f"Clipboard copy error / Ошибка копирования в буфер / Помилка копіювання в буфер: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"Could not copy / Не удалось скопировать / Не вдалося скопіювати: {e}"
            )
            _clear_string(pwd)
            return

        timeout_ms: int = self.clipboard_timeout * 1000
        self._clipboard_timer = self.after(timeout_ms, self._clear_clipboard)

        try:
            old_text: str = self.btn_copy.cget("text")
            self.btn_copy.configure(
                text=L.get("copied", "Copied! ({0}s) / Скопировано! ({0}с) / Скопійовано! ({0}с)").format(self.clipboard_timeout)
            )
            self.after(2000, lambda: self._safe_button_restore(old_text))
        except (tk.TclError, AttributeError, KeyError) as e:
            logger.debug(f"Button text update error / Ошибка обновления текста кнопки / Помилка оновлення тексту кнопки: {e}")

        CTkMessageBox.info(
            self,
            L.get("dlg_title_copied", "Clipboard / Буфер обмена / Буфер обміну"),
            L.get("pwd_done", "Password copied! / Пароль скопирован! / Пароль скопійовано!")
        )

        _clear_string(pwd)

    def _open(self) -> None:
        """
        Open password from file with content validation

        Открыть пароль из файла с проверкой содержимого
        Відкрити пароль з файлу з перевіркою вмісту
        """
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])

        from tkinter import filedialog
        self.attributes("-topmost", False)
        self.update_idletasks()
        path: str = filedialog.askopenfilename(
            parent=self,
            title=L.get("open_title", "Select password file / Выберите файл пароля / Виберіть файл пароля"),
            filetypes=[
                (L.get("export_all", "All Files / Все файлы / Всі файли"), "*.*"),
                (L.get("export_text", "Text Files / Текстовые файлы / Текстові файли"), "*.txt"),
                (L.get("export_password", "Password Files / Файлы паролей / Файли паролів"), "*.key"),
                (L.get("export_log", "Log Files / Файлы логов / Файли логів"), "*.log"),
                (L.get("export_pdf", "PDF Files / PDF файлы / PDF файли"), "*.pdf")
            ]
        )

        if not path:
            return

        try:
            ext: str = os.path.splitext(path)[1].lower()

            if path.lower().endswith(".sha256"):
                CTkMessageBox.error(
                    self,
                    L.get("err_title", "Error / Ошибка / Помилка"),
                    L.get("err_unsupported", "Unsupported file type: {0} / Неподдерживаемый тип файла: {0} / Непідтримуваний тип файлу: {0}").format(".sha256")
                )
                return

            if ext == ".pdf":
                if is_windows():
                    os.startfile(path)
                elif is_macos():
                    import subprocess
                    subprocess.run(["open", path], check=False)
                else:
                    import subprocess
                    subprocess.run(["xdg-open", path], check=False)
                play_sound("success", self.sound_enabled.get())
                return

            content: Optional[str] = None
            encodings: List[str] = ['utf-8', 'cp1251', 'latin-1', 'cp866', 'koi8-r']

            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as f:
                        content = f.read().strip()
                    break
                except (UnicodeDecodeError, UnicodeError) as e:
                    logger.debug(f"Encoding {encoding} failed / Кодировка {encoding} не подошла / Кодування {encoding} не підійшло: {e}")
                    continue

            if content is None:
                try:
                    with open(path, 'rb') as f:
                        raw_bytes: bytes = f.read()
                        content = raw_bytes.decode('utf-8', errors='replace').strip()
                except (OSError, IOError, PermissionError) as e:
                    logger.error(f"Binary read error / Ошибка бинарного чтения / Помилка бінарного читання: {e}")
                    raise ValueError("Cannot read file / Не удается прочитать файл / Не вдається прочитати файл") from e

            if not content:
                raise ValueError(L.get("err_file_empty", "File is empty / Файл пуст / Файл порожній"))

            if len(content) > 1000:
                L_local: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
                if not CTkMessageBox.question(
                    self,
                    L_local.get("warn", "Warning / Предупреждение / Попередження"),
                    f"File contains {len(content)} characters.\n{L_local.get('truncate_question', 'Truncate to {0} characters? / Обрезать до {0} символов? / Обрізати до {0} символів?').format(1000)}"
                ):
                    _clear_string(content)
                    return
                content = content[:1000]

            sanitized_content: str = self._sanitize_import_content(content)

            try:
                self.entry_res.delete(0, "end")
                self.entry_res.insert(0, sanitized_content)
                self._update_strength_meter(sanitized_content)
                play_sound("success", self.sound_enabled.get())
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.error(f"UI update error / Ошибка обновления интерфейса / Помилка оновлення інтерфейсу: {e}")

            _clear_string(content)
            _clear_string(sanitized_content)

        except PermissionError as e:
            logger.error(f"Permission error opening / Ошибка доступа при открытии / Помилка доступу при відкритті: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"No read permission / Нет прав на чтение / Немає прав на читання: {e}"
            )
        except (UnicodeDecodeError, UnicodeError) as e:
            logger.error(f"Encoding error opening / Ошибка кодировки при открытии / Помилка кодування при відкритті: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                L.get("err_open", "Could not read file: {0} / Не удалось прочитать файл: {0} / Не вдалося прочитати файл: {0}").format(f"Invalid encoding / Неверная кодировка / Невірне кодування: {e}")
            )
        except (ValueError, OSError, IOError, TypeError, RuntimeError) as e:
            logger.error(f"Error opening / Ошибка открытия / Помилка відкриття: {e}")
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error / Ошибка / Помилка"),
                L.get("err_open", "Could not read file: {0} / Не удалось прочитать файл: {0} / Не вдалося прочитати файл: {0}").format(str(e))
            )

    def _validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Validate password strength for saving

        Проверяет надёжность пароля для сохранения
        Перевіряє надійність пароля для збереження
        """
        if not password:
            return False, "Password is empty / Пароль пуст / Пароль порожній"

        if len(password) < 4:
            return False, "Password too short (minimum 4 characters) / Пароль слишком короткий (минимум 4 символа) / Пароль занадто короткий (мінімум 4 символи)"

        weak_patterns: List[str] = ['123456', 'password', 'qwerty', 'admin', 'letmein', 'welcome']
        for pattern in weak_patterns:
            if pattern.lower() in password.lower():
                return False, f"Password contains weak pattern: {pattern} / Пароль содержит слабый паттерн: {pattern} / Пароль містить слабкий патерн: {pattern}"

        return True, ""

    def _sanitize_label(self, label: str, max_length: int = 200) -> str:
        """Sanitize label for database storage

        Очищает метку для хранения в БД
        Очищує мітку для зберігання в БД
        """
        import re
        if not label:
            return "Без метки / No label / Без мітки"

        sanitized: str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(label))
        sanitized = sanitized.strip()

        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized if sanitized else "Без метки / No label / Без мітки"

    def _sanitize_import_content(self, content: str) -> str:
        """Sanitize imported content

        Очищает импортированное содержимое
        Очищує імпортований вміст
        """
        if not content:
            return ""
        import re
        sanitized: str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
        sanitized = re.sub(r'[\u200B-\u200D\uFEFF]', '', sanitized)
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        return sanitized

    def _check_duplicate_password(self, password: str) -> bool:
        """Check if password already exists in the database

        Проверяет, существует ли уже такой пароль в базе
        Перевіряє, чи вже існує такий пароль у базі
        """
        try:
            all_passwords: List[Dict[str, Any]] = PasswordDB.get_all()
            for record in all_passwords:
                if record.get("password") == password:
                    return True
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError) as e:
            logger.error(f"Duplicate check error / Ошибка проверки дубликата / Помилка перевірки дубліката: {e}")
        return False

    def _clear_clipboard(self) -> None:
        """Clear clipboard with multiple overwrites for security

        Очистить буфер обмена с многократной перезаписью для безопасности
        Очистити буфер обміну з багаторазовим перезаписом для безпеки
        """
        try:
            if not self.winfo_exists():
                return
            overwrite_passes: int = 5
            for i in range(overwrite_passes):
                try:
                    import secrets
                    junk: str = secrets.token_hex(512)
                    self.clipboard_clear()
                    self.clipboard_append(junk)
                    self.update()
                    time.sleep(0.01)
                    _clear_string(junk)
                except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Clipboard overwrite pass {i + 1} failed / Ошибка прохода перезаписи {i + 1} / Помилка проходу перезапису {i + 1}: {e}")
                    continue
            self.clipboard_clear()
            self.update()
            if is_windows():
                self._clear_clipboard_windows_api()
            logger.debug(f"Clipboard securely cleared with {overwrite_passes} overwrites / Буфер обмена безопасно очищен с {overwrite_passes} перезаписями / Буфер обміну безпечно очищено з {overwrite_passes} перезаписами")
        except (tk.TclError, OSError, AttributeError, RuntimeError) as e:
            logger.debug(f"Clipboard secure clear error / Ошибка безопасной очистки буфера / Помилка безпечного очищення буфера: {e}")
            try:
                self.clipboard_clear()
            except (tk.TclError, OSError, RuntimeError):
                pass
        finally:
            self._clipboard_timer = None

    def _clear_clipboard_windows_api(self) -> None:
        """Additional clipboard clearing via Windows API

        Дополнительная очистка буфера обмена через Windows API
        Додаткове очищення буфера обміну через Windows API
        """
        if not is_windows():
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            if user32.OpenClipboard(0):
                try:
                    user32.EmptyClipboard()
                    logger.debug("Clipboard cleared via Windows API / Буфер обмена очищен через Windows API / Буфер обміну очищено через Windows API")
                except (AttributeError, OSError) as e:
                    logger.debug(f"Windows API clipboard clear error / Ошибка очистки буфера через Windows API / Помилка очищення буфера через Windows API: {e}")
                finally:
                    try:
                        user32.CloseClipboard()
                    except (AttributeError, OSError):
                        pass
        except (ImportError, AttributeError, OSError, TypeError) as e:
            logger.debug(f"Windows API error / Ошибка Windows API / Помилка Windows API: {e}")

    def _safe_button_restore(self, old_text: str) -> None:
        """Safely restore button text

        Безопасно восстанавливает текст кнопки
        Безпечно відновлює текст кнопки
        """
        try:
            if hasattr(self, 'btn_copy') and self.btn_copy and self.btn_copy.winfo_exists():
                self.btn_copy.configure(text=old_text)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Button restore error / Ошибка восстановления кнопки / Помилка відновлення кнопки: {e}")

    def _animate_button(self, btn: ctk.CTkButton) -> None:
        """Animate button click with sound

        Анимирует нажатие кнопки со звуком
        Анімує натискання кнопки зі звуком
        """
        play_sound("click", self.sound_enabled.get())