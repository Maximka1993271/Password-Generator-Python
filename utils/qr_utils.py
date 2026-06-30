"""
QR code utilities for 2FA setup and display
FIXED: Убраны broad exceptions, добавлена безопасная обработка изображений, очистка временных файлов
FIXED: Корректное отображение длинного секрета (показывается нормально)

Утилиты QR-кода для настройки и отображения 2FA
FIXED: Убраны broad exceptions, добавлена безопасная обработка изображений, очистка временных файлов
FIXED: Корректное отображение длинного секрета (показывается нормально)

Утиліти QR-коду для налаштування та відображення 2FA
FIXED: Прибрано broad exceptions, додано безпечну обробку зображень, очищення тимчасових файлів
FIXED: Коректне відображення довгого секрету (показується нормально)
"""
from __future__ import annotations
import os
import tempfile
import atexit
import tkinter as tk
from io import BytesIO
from typing import Optional, List, TYPE_CHECKING

from PIL import Image, ImageDraw
from utils.logger import get_logger

if TYPE_CHECKING:
    import customtkinter as ctk

logger = get_logger("qr_utils")

# Check for qrcode (optional) / Проверяем наличие qrcode (опционально) / Перевіряємо наявність qrcode (опціонально)
QRCODE_AVAILABLE = False
try:
    import qrcode
    QRCODE_AVAILABLE = True
    logger.info("qrcode module available - QR codes will be shown / Модуль qrcode доступен - QR-коды будут показываться / Модуль qrcode доступний - QR-коди будуть показуватися")
except ImportError as e:
    logger.warning(f"qrcode module not available - using text fallback for 2FA setup: {e} / Модуль qrcode недоступен - используется текстовый fallback для настройки 2FA / Модуль qrcode недоступний - використовується текстовий fallback для налаштування 2FA")

# List of temporary files for cleanup / Список временных файлов для очистки / Список тимчасових файлів для очищення
_temp_qr_files: List[str] = []

# Maximum secret display length / Максимальная длина отображаемого секрета / Максимальна довжина секрету, що відображається
MAX_SECRET_DISPLAY_LENGTH = 60

# QR code size / Размер QR кода / Розмір QR коду
QR_CODE_SIZE = 280


def _cleanup_temp_files() -> None:
    """Cleans up all temporary QR files on exit
    Очищает все временные QR-файлы при завершении
    Очищує всі тимчасові QR-файли при завершенні"""
    for file_path in _temp_qr_files[:]:
        try:
            if os.path.exists(file_path):
                try:
                    size = os.path.getsize(file_path)
                    if 0 < size < 1024 * 1024:  # Only files up to 1MB
                        with open(file_path, 'wb') as f:
                            f.write(os.urandom(size))
                            f.flush()
                except (OSError, IOError, PermissionError, ValueError) as e:
                    logger.debug(f"Temp file overwrite error / Ошибка перезаписи временного файла / Помилка перезапису тимчасового файлу: {e}")
                try:
                    os.remove(file_path)
                except (OSError, IOError, PermissionError) as e:
                    logger.debug(f"Temp file remove error / Ошибка удаления временного файла / Помилка видалення тимчасового файлу: {e}")
        except (OSError, IOError, PermissionError, AttributeError) as e:
            logger.debug(f"Failed to cleanup temp QR file {file_path}: {e} / Не удалось очистить временный QR файл {file_path} / Не вдалося очистити тимчасовий QR файл {file_path}")
    _temp_qr_files.clear()


atexit.register(_cleanup_temp_files)


def _register_temp_file(file_path: str) -> None:
    """Registers a temporary file for cleanup
    Регистрирует временный файл для очистки
    Реєструє тимчасовий файл для очищення"""
    if file_path and file_path not in _temp_qr_files:
        _temp_qr_files.append(file_path)


def _format_secret_for_display(secret: str, max_length: int = MAX_SECRET_DISPLAY_LENGTH) -> str:
    """Format secret for display with group spacing
    Форматирует секрет для отображения с группировкой
    Форматує секрет для відображення з групуванням"""
    if not secret:
        return ""

    # Remove spaces and dashes first / Сначала убираем пробелы и дефисы / Спочатку прибираємо пробіли та дефіси
    clean_secret = secret.replace(" ", "").replace("-", "")

    # Format by 4 characters / Форматируем по 4 символа / Форматуємо по 4 символи
    formatted = ' '.join([clean_secret[i:i+4] for i in range(0, len(clean_secret), 4)])

    # Truncate if too long / Обрезаем если слишком длинный / Обрізаємо якщо занадто довгий
    if len(formatted) > max_length:
        formatted = formatted[:max_length - 3] + "..."

    return formatted


class QRUtils:
    """Utilities for creating and displaying QR codes for 2FA (with fallback)
    Утилиты для создания и отображения QR кодов для 2FA (с fallback)
    Утиліти для створення та відображення QR кодів для 2FA (з fallback)"""

    @staticmethod
    def is_available() -> bool:
        """Check if qrcode module is available / Проверяет, доступен ли модуль qrcode / Перевіряє, чи доступний модуль qrcode"""
        return QRCODE_AVAILABLE

    @staticmethod
    def generate_qr_image(data: str, size: int = QR_CODE_SIZE) -> Optional[Image.Image]:
        """Generate QR code from data / Генерирует QR код из данных / Генерує QR код з даних"""
        try:
            if QRCODE_AVAILABLE:
                qr = qrcode.QRCode(
                    version=5,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=10,
                    border=2,
                )
                qr.add_data(data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                # Resize with high-quality interpolation / Изменяем размер с высококачественной интерполяцией
                try:
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                except AttributeError:
                    # Fallback for older PIL versions / Fallback для старых версий PIL
                    img = img.resize((size, size), Image.ANTIALIAS)
                return img
            else:
                # Create fallback image with text instructions
                # Создаём fallback изображение с текстовыми инструкциями
                # Створюємо fallback зображення з текстовими інструкціями
                img = Image.new('RGB', (size, size), color='white')
                draw = ImageDraw.Draw(img)
                draw.rectangle([2, 2, size-3, size-3], outline='black', width=2)
                draw.text((size//2 - 100, 30), "QR CODE NOT AVAILABLE", fill='black')
                draw.text((size//2 - 80, 55), "Install qrcode module:", fill='black')
                draw.text((size//2 - 100, 80), "pip install qrcode[pil]", fill='black')
                draw.line([(40, 110), (size-40, 110)], fill='black', width=1)
                draw.text((size//2 - 100, 130), "MANUAL SETUP:", fill='black')
                draw.text((size//2 - 100, 155), "Open Google Authenticator or", fill='black')
                draw.text((size//2 - 100, 175), "other TOTP app and enter this code:", fill='black')
                return img
        except ImportError as e:
            logger.error(f"Failed to import QR modules / Ошибка импорта QR модулей / Помилка імпорту QR модулів: {e}")
            return None
        except (ValueError, AttributeError, OSError, TypeError, IndexError) as e:
            logger.error(f"Failed to generate QR image / Ошибка генерации QR изображения / Помилка генерації QR зображення: {e}")
            return None

    @staticmethod
    def qr_image_to_ctk(image: Image.Image) -> Optional['ctk.CTkImage']:
        """Convert PIL Image to CTkImage / Конвертирует PIL Image в CTkImage / Конвертує PIL Image в CTkImage"""
        try:
            import customtkinter as ctk
            ctk_image = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(image.width, image.height)
            )
            return ctk_image
        except ImportError as e:
            logger.error(f"customtkinter not available / customtkinter недоступен / customtkinter недоступний: {e}")
            return None
        except (AttributeError, TypeError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to convert image / Ошибка конвертации изображения / Помилка конвертації зображення: {e}")
            return None

    @staticmethod
    def save_qr_temp(image: Image.Image) -> Optional[str]:
        """Save QR image to temporary file / Сохраняет QR изображение во временный файл / Зберігає QR зображення у тимчасовий файл"""
        temp_path = None
        try:
            fd, temp_path = tempfile.mkstemp(suffix='.png', prefix='qr_')
            os.close(fd)
            image.save(temp_path, 'PNG', optimize=True)
            _register_temp_file(temp_path)
            return temp_path
        except (OSError, IOError, PermissionError, AttributeError, ValueError) as e:
            logger.error(f"Failed to save QR temp file / Ошибка сохранения временного QR файла / Помилка збереження тимчасового QR файлу: {e}")
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except (OSError, IOError, PermissionError):
                    pass
            return None

    @staticmethod
    def cleanup_temp_qr_files() -> None:
        """Forcefully clean up all temporary QR files
        Принудительно очищает все временные QR-файлы
        Примусово очищує всі тимчасові QR-файли"""
        _cleanup_temp_files()

    @staticmethod
    def show_qr_window(parent, provisioning_uri: str, secret: str,
                       lang: str = "RU", title: str = "2FA Setup") -> None:
        """Show window with QR code for 2FA setup
        Показывает окно с QR кодом для настройки 2FA
        Показує вікно з QR кодом для налаштування 2FA"""
        try:
            import customtkinter as ctk
            import tkinter as tk
            from Langs.lang import LANGUAGES

            L = LANGUAGES.get(lang, LANGUAGES["RU"])

            window = ctk.CTkToplevel(parent)
            window.title(title)
            window.geometry("480x650")
            window.resizable(False, False)
            window.transient(parent)
            window.grab_set()
            window.lift()
            window.focus_force()
            window.after(100, lambda: window.attributes("-topmost", False) if window and window.winfo_exists() else None)
            window.attributes("-topmost", True)

            # Center window / Центрируем окно / Центруємо вікно
            try:
                window.update_idletasks()
                parent_x = parent.winfo_x()
                parent_y = parent.winfo_y()
                parent_width = parent.winfo_width()
                parent_height = parent.winfo_height()
                x = parent_x + (parent_width - 480) // 2
                y = parent_y + (parent_height - 650) // 2
                if x < 0:
                    x = 10
                if y < 30:
                    y = 30
                window.geometry(f"480x650+{x}+{y}")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Window centering error / Ошибка центрирования окна / Помилка центрування вікна: {e}")
                window.geometry("480x650")

            main_frame = ctk.CTkFrame(window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Title / Заголовок / Заголовок
            try:
                ctk.CTkLabel(
                    main_frame,
                    text=L.get("2fa_setup_title", "Two-Factor Authentication Setup / Настройка двухфакторной аутентификации / Налаштування двофакторної аутентифікації"),
                    font=("Segoe UI", 18, "bold")
                ).pack(pady=(0, 10))
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Title label error / Ошибка заголовка / Помилка заголовка: {e}")

            # Explanation / Пояснение / Пояснення
            try:
                ctk.CTkLabel(
                    main_frame,
                    text=L.get("2fa_scan_qr", "Scan this QR code with Google Authenticator, Authy, or any other TOTP app: / Отсканируйте этот QR-код с помощью Google Authenticator, Authy или любого другого TOTP приложения: / Відскануйте цей QR-код за допомогою Google Authenticator, Authy або будь-якого іншого TOTP додатку:"),
                    wraplength=400,
                    justify="center",
                    font=("Segoe UI", 12)
                ).pack(pady=(0, 15))
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Instruction label error / Ошибка инструкции / Помилка інструкції: {e}")

            # QR code / QR код / QR код
            try:
                img = QRUtils.generate_qr_image(provisioning_uri, size=250)
                if img:
                    ctk_img = QRUtils.qr_image_to_ctk(img)
                    if ctk_img:
                        qr_label = ctk.CTkLabel(main_frame, image=ctk_img, text="")
                        qr_label.image = ctk_img
                        qr_label.pack(pady=10)
            except (ValueError, AttributeError, OSError, TypeError) as e:
                logger.error(f"QR image display error / Ошибка отображения QR изображения / Помилка відображення QR зображення: {e}")

            # Secret key / Секретный ключ / Секретний ключ
            try:
                ctk.CTkLabel(
                    main_frame,
                    text=L.get("2fa_or_enter_manually", "Or enter this code manually: / Или введите этот код вручную: / Або введіть цей код вручну:"),
                    font=("Segoe UI", 11),
                    text_color="gray"
                ).pack(pady=(10, 5))
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Manual entry label error / Ошибка метки ручного ввода / Помилка мітки ручного введення: {e}")

            secret_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            secret_frame.pack(pady=5)

            # ========== DISPLAY SECRET (NORMAL) / ОТОБРАЖЕНИЕ СЕКРЕТА (НОРМАЛЬНОЕ) / ВІДОБРАЖЕННЯ СЕКРЕТУ (НОРМАЛЬНЕ) ==========
            try:
                # Get current theme for styling / Получаем текущую тему для стилизации / Отримуємо поточну тему для стилізації
                try:
                    is_dark = ctk.get_appearance_mode() == "Dark"
                except (AttributeError, tk.TclError):
                    is_dark = True

                display_text = _format_secret_for_display(secret)

                secret_label = ctk.CTkLabel(
                    secret_frame,
                    text=display_text,
                    font=("Consolas", 12, "bold"),
                    fg_color=("#2b2b2b" if is_dark else "#e0e0e0"),
                    corner_radius=8,
                    padx=15,
                    pady=8
                )
                secret_label.pack()
            except (ValueError, AttributeError, tk.TclError, IndexError, TypeError) as e:
                logger.debug(f"Secret label error / Ошибка метки секрета / Помилка мітки секрету: {e}")
                # Fallback: show short version / Fallback: показываем короткую версию / Fallback: показуємо коротку версію
                try:
                    short_secret = secret[:16] + "..." if len(secret) > 16 else secret
                    ctk.CTkLabel(
                        secret_frame,
                        text=short_secret,
                        font=("Consolas", 12),
                        fg_color=("#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#e0e0e0"),
                        corner_radius=8,
                        padx=15,
                        pady=8
                    ).pack()
                except (tk.TclError, AttributeError, ValueError) as e2:
                    logger.debug(f"Fallback secret label error / Ошибка fallback метки секрета / Помилка fallback мітки секрету: {e2}")

            # Copy button (copies full secret) / Кнопка копирования (копирует полный секрет) / Кнопка копіювання (копіює повний секрет)
            def copy_secret() -> None:
                try:
                    window.clipboard_clear()
                    window.clipboard_append(secret)
                    copy_btn.configure(text=L.get("copied", "Copied! / Скопировано! / Скопійовано!"))
                    window.after(2000, lambda: copy_btn.configure(text=L.get("copy", "Copy / Копировать / Копіювати")))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Copy secret error / Ошибка копирования секрета / Помилка копіювання секрету: {e}")

            try:
                copy_btn = ctk.CTkButton(
                    secret_frame,
                    text=L.get("copy", "Copy / Копировать / Копіювати"),
                    command=copy_secret,
                    width=100,
                    height=30,
                    fg_color="#2d6a4f",
                    corner_radius=15
                )
                copy_btn.pack(pady=5)
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Copy button error / Ошибка кнопки копирования / Помилка кнопки копіювання: {e}")

            # Warning / Предупреждение / Попередження
            try:
                ctk.CTkLabel(
                    main_frame,
                    text=L.get("2fa_backup_warning", "Save backup codes! They are required to recover access. / Сохраните резервные коды! Они необходимы для восстановления доступа. / Збережіть резервні коди! Вони необхідні для відновлення доступу."),
                    font=("Segoe UI", 11),
                    text_color="#FFA500"
                ).pack(pady=(10, 5))
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Warning label error / Ошибка метки предупреждения / Помилка мітки попередження: {e}")

            # Close button / Кнопка закрытия / Кнопка закриття
            try:
                ctk.CTkButton(
                    main_frame,
                    text=L.get("close", "Close / Закрыть / Закрити"),
                    command=window.destroy,
                    width=120,
                    height=35,
                    fg_color="#8b0000",
                    corner_radius=15
                ).pack(pady=15)
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Close button error / Ошибка кнопки закрытия / Помилка кнопки закриття: {e}")

            window.after(100, lambda: QRUtils._set_topmost_false(window))

        except ImportError as e:
            logger.error(f"Failed to import GUI modules for QR window / Ошибка импорта GUI модулей для QR окна / Помилка імпорту GUI модулів для QR вікна: {e}")
            from gui.dialogs import CTkMessageBox
            from Langs.lang import LANGUAGES
            L = LANGUAGES.get(lang, LANGUAGES["RU"])
            CTkMessageBox.error(parent, title, f"{L.get('err_title', 'Error / Ошибка / Помилка')}: {str(e)}")
        except (tk.TclError, AttributeError, RuntimeError, KeyError, TypeError) as e:
            logger.error(f"Failed to show QR window / Ошибка отображения QR окна / Помилка відображення QR вікна: {e}")
            from gui.dialogs import CTkMessageBox
            from Langs.lang import LANGUAGES
            L = LANGUAGES.get(lang, LANGUAGES["RU"])
            CTkMessageBox.error(parent, title, f"{L.get('err_title', 'Error / Ошибка / Помилка')}: {str(e)}")

    @staticmethod
    def _set_topmost_false(window) -> None:
        """Safely remove topmost flag / Безопасно снимает флаг topmost / Безпечно знімає прапор topmost"""
        try:
            window.attributes("-topmost", False)
        except (tk.TclError, AttributeError, RuntimeError):
            pass

    @staticmethod
    def verify_2fa_code(parent, lang: str = "RU", title: str = "2FA Verification") -> Optional[str]:
        """Show dialog for entering 2FA code
        Показывает диалог для ввода 2FA кода
        Показує діалог для введення 2FA коду"""
        try:
            import customtkinter as ctk
            import tkinter as tk
            from Langs.lang import LANGUAGES

            L = LANGUAGES.get(lang, LANGUAGES["RU"])

            result = {"code": None}

            dialog = ctk.CTkToplevel(parent)
            dialog.title(title)
            dialog.geometry("400x300")
            dialog.resizable(False, False)
            dialog.transient(parent)
            dialog.grab_set()
            dialog.attributes("-topmost", True)

            try:
                dialog.update_idletasks()
                parent_x = parent.winfo_x()
                parent_y = parent.winfo_y()
                parent_width = parent.winfo_width()
                parent_height = parent.winfo_height()
                x = parent_x + (parent_width - 400) // 2
                y = parent_y + (parent_height - 300) // 2
                dialog.geometry(f"400x300+{x}+{y}")
            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Center dialog error / Ошибка центрирования диалога / Помилка центрування діалогу: {e}")
                dialog.geometry("400x300")

            try:
                theme = "dark" if ctk.get_appearance_mode() == "Dark" else "light"
            except (AttributeError, tk.TclError):
                theme = "dark"

            if theme == "light":
                bg_color = "#F3F3F3"
                fg_color = "#000000"
                entry_bg = "#FFFFFF"
            else:
                bg_color = "#1d1e1e"
                fg_color = "#FFFFFF"
                entry_bg = "#2b2b2b"

            dialog.configure(fg_color=bg_color)

            main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)

            # Icon (empty) / Иконка (пустая) / Іконка (порожня)
            try:
                ctk.CTkLabel(
                    main_frame,
                    text="",
                    font=("Segoe UI", 36),
                    text_color="#4EC9B0"
                ).pack(pady=(0, 10))
            except (tk.TclError, AttributeError, TypeError) as e:
                logger.debug(f"Icon label error / Ошибка иконки / Помилка іконки: {e}")

            # Text / Текст / Текст
            try:
                ctk.CTkLabel(
                    main_frame,
                    text=L.get("2fa_enter_code", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:"),
                    font=("Segoe UI", 14, "bold"),
                    text_color=fg_color
                ).pack(pady=(0, 15))
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Prompt label error / Ошибка метки запроса / Помилка мітки запиту: {e}")

            # Input field / Поле ввода / Поле введення
            entry = ctk.CTkEntry(
                main_frame,
                width=200,
                height=45,
                font=("Consolas", 20, "bold"),
                justify="center",
                fg_color=entry_bg,
                text_color=fg_color
            )
            entry.pack(pady=(0, 15))
            entry.focus_set()

            status_label = ctk.CTkLabel(
                main_frame,
                text="",
                font=("Segoe UI", 11),
                text_color="#E24B4A"
            )
            status_label.pack()

            def on_verify() -> None:
                try:
                    code = entry.get().strip()
                    if len(code) == 6 and code.isdigit():
                        result["code"] = code
                        dialog.destroy()
                    else:
                        try:
                            status_label.configure(text=L.get("2fa_invalid_code", "Please enter a valid 6-digit code / Пожалуйста, введите корректный 6-значный код / Будь ласка, введіть коректний 6-значний код"))
                        except (tk.TclError, KeyError, TypeError):
                            pass
                        entry.delete(0, "end")
                        entry.focus_set()
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Verify function error / Ошибка функции проверки / Помилка функції перевірки: {e}")

            def on_cancel() -> None:
                dialog.destroy()

            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(pady=10)

            try:
                ctk.CTkButton(
                    btn_frame,
                    text=L.get("ok", "Verify / Подтвердить / Підтвердити"),
                    command=on_verify,
                    width=110,
                    height=35,
                    fg_color="#2d6a4f",
                    corner_radius=17
                ).pack(side="left", padx=10)
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Verify button error / Ошибка кнопки проверки / Помилка кнопки перевірки: {e}")

            try:
                ctk.CTkButton(
                    btn_frame,
                    text=L.get("cancel", "Cancel / Отмена / Скасувати"),
                    command=on_cancel,
                    width=110,
                    height=35,
                    fg_color="#8b0000",
                    corner_radius=17
                ).pack(side="left", padx=10)
            except (tk.TclError, KeyError, TypeError) as e:
                logger.debug(f"Cancel button error / Ошибка кнопки отмены / Помилка кнопки скасування: {e}")

            entry.bind("<Return>", lambda e: on_verify())
            entry.bind("<Escape>", lambda e: on_cancel())

            dialog.after(100, lambda: QRUtils._set_topmost_false(dialog))

            parent.wait_window(dialog)

            return result["code"]

        except ImportError as e:
            logger.error(f"Failed to import GUI modules for verification / Ошибка импорта GUI модулей для верификации / Помилка імпорту GUI модулів для верифікації: {e}")
            return None
        except (tk.TclError, AttributeError, RuntimeError, KeyError, TypeError) as e:
            logger.error(f"Failed to show verification dialog / Ошибка отображения диалога верификации / Помилка відображення діалогу верифікації: {e}")
            return None


__all__ = ['QRUtils', 'QRCODE_AVAILABLE', 'cleanup_temp_qr_files']


def cleanup_temp_qr_files() -> None:
    """Module-level wrapper for QRUtils.cleanup_temp_qr_files()
    Модульная обёртка для QRUtils.cleanup_temp_qr_files()
    Модульна обгортка для QRUtils.cleanup_temp_qr_files()"""
    _cleanup_temp_files()
