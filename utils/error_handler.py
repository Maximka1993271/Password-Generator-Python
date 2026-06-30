"""
Centralized error handling for Secure Pass Pro v4.0
Единый обработчик ошибок для Secure Pass Pro v4.0
Єдиний обробник помилок для Secure Pass Pro v4.0

FIXED: Added full type hints, 3-language support, and context-aware error handling
"""
from __future__ import annotations

import sys
import traceback
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, TypeVar, cast
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from utils.logger import get_logger, log_crash_report
from Langs.lang import LANGUAGES

logger = get_logger("error_handler")


# ==================== ERROR SEVERITY ====================

class ErrorSeverity(Enum):
    """Error severity levels / Уровни серьезности ошибок / Рівні серйозності помилок"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Error categories / Категории ошибок / Категорії помилок"""
    # Core
    GENERATOR = "generator"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    INTEGRITY = "integrity"
    MASTER_PASSWORD = "master_password"
    
    # Storage
    DATABASE = "database"
    CONFIG = "config"
    BACKUP = "backup"
    
    # GUI
    UI = "ui"
    DIALOG = "dialog"
    WIDGET = "widget"
    
    # Network
    NETWORK = "network"
    API = "api"
    HIBP = "hibp"
    UPDATE = "update"
    
    # Import/Export
    IMPORT = "import"
    EXPORT = "export"
    
    # Security
    SECURITY = "security"
    ANTI_DEBUG = "anti_debug"
    VM_DETECTION = "vm_detection"
    CLIPBOARD = "clipboard"
    
    # System
    SYSTEM = "system"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    MEMORY = "memory"
    FILE = "file"
    
    # Unknown
    UNKNOWN = "unknown"


# ==================== ERROR EVENT ====================

@dataclass
class ErrorEvent:
    """Error event data structure / Структура данных события ошибки / Структура даних події помилки"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    user_message: str = ""
    handled: bool = False
    recoverable: bool = True
    suggestion: str = ""


# ==================== ERROR HANDLER ====================

class ErrorHandler:
    """
    Centralized error handler for Secure Pass Pro v4.0
    Единый обработчик ошибок для Secure Pass Pro v4.0
    Єдиний обробник помилок для Secure Pass Pro v4.0
    """
    
    _instance: Optional['ErrorHandler'] = None
    _lock = None  # Will be initialized in __new__
    
    # Error messages in 3 languages
    _error_messages: Dict[str, Dict[str, str]] = {
        "RU": {
            "generic": "Произошла ошибка: {0}",
            "unexpected": "Неожиданная ошибка: {0}",
            "contact_support": "Пожалуйста, свяжитесь с поддержкой.",
            "try_again": "Попробуйте еще раз.",
            "restart_app": "Перезапустите приложение.",
            "check_logs": "Проверьте логи для получения дополнительной информации.",
            "recoverable": "Ошибка может быть исправлена автоматически.",
            "critical": "Критическая ошибка! Программа будет закрыта.",
            "fatal": "Фатальная ошибка! Невозможно продолжить работу.",
            "db_error": "Ошибка базы данных. Данные могут быть повреждены.",
            "encrypt_error": "Ошибка шифрования. Проверьте мастер-пароль.",
            "decrypt_error": "Ошибка дешифрования. Данные могут быть повреждены.",
            "network_error": "Ошибка сети. Проверьте подключение к интернету.",
            "permission_error": "Недостаточно прав доступа.",
            "timeout_error": "Превышено время ожидания.",
            "memory_error": "Недостаточно памяти.",
            "file_error": "Ошибка файловой системы.",
            "hibp_error": "Ошибка проверки утечек. Попробуйте позже.",
            "update_error": "Ошибка обновления. Проверьте подключение к интернету.",
            "import_error": "Ошибка импорта. Проверьте формат файла.",
            "export_error": "Ошибка экспорта. Проверьте права доступа.",
            "master_error": "Ошибка мастер-пароля. Проверьте правильность ввода.",
            "generator_error": "Ошибка генерации пароля. Попробуйте изменить настройки.",
            "integrity_error": "Нарушена целостность файла! Программа может работать некорректно.",
            "ui_error": "Ошибка интерфейса. Попробуйте перезапустить приложение.",
            "clipboard_error": "Ошибка работы с буфером обмена.",
            "2fa_error": "Ошибка двухфакторной аутентификации.",
            "qr_error": "Ошибка создания QR-кода.",
            "sync_error": "Ошибка синхронизации. Проверьте настройки облачного хранилища.",
        },
        "EN": {
            "generic": "An error occurred: {0}",
            "unexpected": "Unexpected error: {0}",
            "contact_support": "Please contact support.",
            "try_again": "Please try again.",
            "restart_app": "Please restart the application.",
            "check_logs": "Check logs for more information.",
            "recoverable": "Error may be automatically recoverable.",
            "critical": "Critical error! The program will be closed.",
            "fatal": "Fatal error! Cannot continue execution.",
            "db_error": "Database error. Data may be corrupted.",
            "encrypt_error": "Encryption error. Check master password.",
            "decrypt_error": "Decryption error. Data may be corrupted.",
            "network_error": "Network error. Check internet connection.",
            "permission_error": "Insufficient permissions.",
            "timeout_error": "Timeout exceeded.",
            "memory_error": "Out of memory.",
            "file_error": "File system error.",
            "hibp_error": "Breach check error. Please try again later.",
            "update_error": "Update error. Check internet connection.",
            "import_error": "Import error. Check file format.",
            "export_error": "Export error. Check permissions.",
            "master_error": "Master password error. Check your input.",
            "generator_error": "Password generation error. Try changing settings.",
            "integrity_error": "File integrity violation! Program may work incorrectly.",
            "ui_error": "UI error. Try restarting the application.",
            "clipboard_error": "Clipboard error.",
            "2fa_error": "Two-Factor Authentication error.",
            "qr_error": "QR code generation error.",
            "sync_error": "Sync error. Check cloud storage settings.",
        },
        "UA": {
            "generic": "Сталася помилка: {0}",
            "unexpected": "Неочікувана помилка: {0}",
            "contact_support": "Будь ласка, зв'яжіться з підтримкою.",
            "try_again": "Спробуйте ще раз.",
            "restart_app": "Перезапустіть додаток.",
            "check_logs": "Перевірте логи для отримання додаткової інформації.",
            "recoverable": "Помилка може бути виправлена автоматично.",
            "critical": "Критична помилка! Програма буде закрита.",
            "fatal": "Фатальна помилка! Неможливо продовжити роботу.",
            "db_error": "Помилка бази даних. Дані можуть бути пошкоджені.",
            "encrypt_error": "Помилка шифрування. Перевірте майстер-пароль.",
            "decrypt_error": "Помилка дешифрування. Дані можуть бути пошкоджені.",
            "network_error": "Помилка мережі. Перевірте підключення до інтернету.",
            "permission_error": "Недостатньо прав доступу.",
            "timeout_error": "Перевищено час очікування.",
            "memory_error": "Недостатньо пам'яті.",
            "file_error": "Помилка файлової системи.",
            "hibp_error": "Помилка перевірки витоків. Спробуйте пізніше.",
            "update_error": "Помилка оновлення. Перевірте підключення до інтернету.",
            "import_error": "Помилка імпорту. Перевірте формат файлу.",
            "export_error": "Помилка експорту. Перевірте права доступу.",
            "master_error": "Помилка майстер-пароля. Перевірте правильність введення.",
            "generator_error": "Помилка генерації пароля. Спробуйте змінити налаштування.",
            "integrity_error": "Порушено цілісність файлу! Програма може працювати некоректно.",
            "ui_error": "Помилка інтерфейсу. Спробуйте перезапустити додаток.",
            "clipboard_error": "Помилка роботи з буфером обміну.",
            "2fa_error": "Помилка двофакторної аутентифікації.",
            "qr_error": "Помилка створення QR-коду.",
            "sync_error": "Помилка синхронізації. Перевірте налаштування хмарного сховища.",
        }
    }
    
    # Error code to user message mapping
    _error_map: Dict[str, Tuple[ErrorSeverity, ErrorCategory, str, str]] = {
        # Database errors
        "sqlite3.OperationalError": (ErrorSeverity.ERROR, ErrorCategory.DATABASE, "db_error", "try_again"),
        "sqlite3.IntegrityError": (ErrorSeverity.CRITICAL, ErrorCategory.DATABASE, "db_error", "restart_app"),
        "sqlite3.DatabaseError": (ErrorSeverity.ERROR, ErrorCategory.DATABASE, "db_error", "check_logs"),
        
        # Encryption errors
        "InvalidTag": (ErrorSeverity.CRITICAL, ErrorCategory.ENCRYPTION, "encrypt_error", "check_logs"),
        "EncryptionError": (ErrorSeverity.ERROR, ErrorCategory.ENCRYPTION, "encrypt_error", "try_again"),
        "DecryptionError": (ErrorSeverity.ERROR, ErrorCategory.DECRYPTION, "decrypt_error", "check_logs"),
        "TamperDetectedError": (ErrorSeverity.CRITICAL, ErrorCategory.INTEGRITY, "integrity_error", "restart_app"),
        
        # Network errors
        "URLError": (ErrorSeverity.WARNING, ErrorCategory.NETWORK, "network_error", "try_again"),
        "HTTPError": (ErrorSeverity.WARNING, ErrorCategory.NETWORK, "network_error", "try_again"),
        "ConnectionError": (ErrorSeverity.WARNING, ErrorCategory.NETWORK, "network_error", "try_again"),
        "TimeoutError": (ErrorSeverity.WARNING, ErrorCategory.TIMEOUT, "timeout_error", "try_again"),
        
        # Permission errors
        "PermissionError": (ErrorSeverity.ERROR, ErrorCategory.PERMISSION, "permission_error", "restart_app"),
        "OSError": (ErrorSeverity.ERROR, ErrorCategory.SYSTEM, "file_error", "try_again"),
        "IOError": (ErrorSeverity.ERROR, ErrorCategory.FILE, "file_error", "try_again"),
        
        # Memory errors
        "MemoryError": (ErrorSeverity.FATAL, ErrorCategory.MEMORY, "memory_error", "restart_app"),
        
        # Master password errors
        "MasterPasswordError": (ErrorSeverity.ERROR, ErrorCategory.MASTER_PASSWORD, "master_error", "try_again"),
        "LockoutError": (ErrorSeverity.WARNING, ErrorCategory.MASTER_PASSWORD, "master_error", "try_again"),
        
        # Generator errors
        "ValueError": (ErrorSeverity.WARNING, ErrorCategory.GENERATOR, "generator_error", "try_again"),
        "TypeError": (ErrorSeverity.WARNING, ErrorCategory.GENERATOR, "generator_error", "try_again"),
        
        # Import/Export errors
        "ExportError": (ErrorSeverity.ERROR, ErrorCategory.EXPORT, "export_error", "try_again"),
        "ExportEncryptionError": (ErrorSeverity.ERROR, ErrorCategory.EXPORT, "export_error", "try_again"),
        "ImportError": (ErrorSeverity.ERROR, ErrorCategory.IMPORT, "import_error", "try_again"),
        "InvalidFileFormatError": (ErrorSeverity.ERROR, ErrorCategory.IMPORT, "import_error", "try_again"),
        
        # HIBP errors
        "hibp_error": (ErrorSeverity.WARNING, ErrorCategory.HIBP, "hibp_error", "try_again"),
        
        # Update errors
        "UpdateError": (ErrorSeverity.WARNING, ErrorCategory.UPDATE, "update_error", "try_again"),
        
        # Clipboard errors
        "ClipboardError": (ErrorSeverity.WARNING, ErrorCategory.CLIPBOARD, "clipboard_error", "try_again"),
        
        # 2FA errors
        "TOTPError": (ErrorSeverity.ERROR, ErrorCategory.SECURITY, "2fa_error", "try_again"),
        "TOTPRateLimitError": (ErrorSeverity.WARNING, ErrorCategory.SECURITY, "2fa_error", "try_again"),
        "TOTPInvalidSecretError": (ErrorSeverity.ERROR, ErrorCategory.SECURITY, "2fa_error", "check_logs"),
        
        # QR errors
        "QRCodeError": (ErrorSeverity.WARNING, ErrorCategory.API, "qr_error", "try_again"),
        
        # UI errors
        "TclError": (ErrorSeverity.ERROR, ErrorCategory.UI, "ui_error", "restart_app"),
        
        # Sync errors
        "SyncError": (ErrorSeverity.WARNING, ErrorCategory.NETWORK, "sync_error", "try_again"),
    }
    
    def __new__(cls) -> 'ErrorHandler':
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            import threading
            cls._lock = threading.RLock()
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._callbacks: List[Callable[[ErrorEvent], None]] = []
                    cls._instance._last_error: Optional[ErrorEvent] = None
                    cls._instance._error_history: List[ErrorEvent] = []
                    cls._instance._max_history: int = 100
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'ErrorHandler':
        """Get singleton instance / Получить экземпляр синглтона / Отримати екземпляр синглтона"""
        return cls()
    
    def register_callback(self, callback: Callable[[ErrorEvent], None]) -> None:
        """
        Register a callback for error events.
        
        Регистрирует callback для событий ошибок.
        Реєструє callback для подій помилок.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[ErrorEvent], None]) -> None:
        """Unregister a callback / Отменить регистрацию callback / Скасувати реєстрацію callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def handle(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        show_dialog: bool = True,
        parent_widget: Optional[tk.Widget] = None,
        lang: str = "RU"
    ) -> ErrorEvent:
        """
        Handle an error with full context and optional user notification.
        
        Обрабатывает ошибку с полным контекстом и опциональным уведомлением пользователя.
        Обробляє помилку з повним контекстом та опціональним сповіщенням користувача.
        
        Args:
            error: Exception to handle / Исключение для обработки / Виняток для обробки
            context: Additional context / Дополнительный контекст / Додатковий контекст
            user_message: Custom user message / Пользовательское сообщение / Користувацьке повідомлення
            show_dialog: Show error dialog / Показать диалог ошибки / Показати діалог помилки
            parent_widget: Parent widget for dialog / Родительский виджет для диалога / Батьківський віджет для діалогу
            lang: Language code / Код языка / Код мови
        
        Returns:
            ErrorEvent object / Объект ErrorEvent / Об'єкт ErrorEvent
        """
        error_type: str = type(error).__name__
        error_message: str = str(error)
        stack_trace: str = traceback.format_exc()
        
        # Get severity, category, and user message from map
        severity, category, msg_key, suggestion_key = self._map_error(error_type)
        
        # Get localized messages
        L = LANGUAGES.get(lang, LANGUAGES["RU"])
        msg_template = self._error_messages.get(lang, self._error_messages["RU"])
        
        if user_message is None:
            user_message = msg_template.get(msg_key, msg_template["generic"]).format(error_message)
        
        suggestion = msg_template.get(suggestion_key, "")
        
        # Create error event
        event = ErrorEvent(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            category=category,
            stack_trace=stack_trace,
            context=context or {},
            user_message=user_message,
            handled=True,
            recoverable=severity not in (ErrorSeverity.CRITICAL, ErrorSeverity.FATAL),
            suggestion=suggestion
        )
        
        # Store last error and history
        self._last_error = event
        self._error_history.append(event)
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
        
        # Log error
        self._log_error(event)
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except BaseException as e:  # top-level handler must catch everything
                logger.error(f"Error callback failed: {e}")
        
        # Show dialog if requested
        if show_dialog:
            self._show_error_dialog(event, parent_widget, lang)
        
        return event
    
    def _map_error(self, error_type: str) -> Tuple[ErrorSeverity, ErrorCategory, str, str]:
        """Map error type to severity, category, and message keys"""
        for key, (severity, category, msg_key, suggestion_key) in self._error_map.items():
            if key in error_type or error_type in key:
                return severity, category, msg_key, suggestion_key
        
        # Default mapping for unknown errors
        if error_type in ("KeyboardInterrupt", "SystemExit"):
            return ErrorSeverity.INFO, ErrorCategory.SYSTEM, "generic", "try_again"
        
        return ErrorSeverity.ERROR, ErrorCategory.UNKNOWN, "generic", "check_logs"
    
    def _log_error(self, event: ErrorEvent) -> None:
        """Log error to file with appropriate level"""
        log_message = f"[{event.category.value.upper()}] {event.error_type}: {event.error_message}"
        
        if event.context:
            log_message += f"\nContext: {event.context}"
        
        if event.stack_trace:
            log_message += f"\n{event.stack_trace}"
        
        if event.severity == ErrorSeverity.DEBUG:
            logger.debug(log_message)
        elif event.severity == ErrorSeverity.INFO:
            logger.info(log_message)
        elif event.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        elif event.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif event.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.FATAL):
            logger.critical(log_message)
            # Generate crash report
            try:
                log_crash_report(Exception(event.error_message), event.context)
            except (OSError, RuntimeError, AttributeError):
                pass
    
    def _show_error_dialog(
        self,
        event: ErrorEvent,
        parent_widget: Optional[tk.Widget] = None,
        lang: str = "RU"
    ) -> None:
        """Show error dialog to user if GUI is available"""
        try:
            from gui.dialogs import CTkMessageBox
            
            L = LANGUAGES.get(lang, LANGUAGES["RU"])
            
            # Determine dialog type based on severity
            if event.severity == ErrorSeverity.FATAL:
                title = L.get("err_title", "Fatal Error / Фатальная ошибка / Фатальна помилка")
                icon = "error"
            elif event.severity == ErrorSeverity.CRITICAL:
                title = L.get("err_title", "Critical Error / Критическая ошибка / Критична помилка")
                icon = "error"
            elif event.severity == ErrorSeverity.ERROR:
                title = L.get("err_title", "Error / Ошибка / Помилка")
                icon = "error"
            elif event.severity == ErrorSeverity.WARNING:
                title = L.get("warn", "Warning / Предупреждение / Попередження")
                icon = "warning"
            else:
                title = L.get("status_ok", "Information / Информация / Інформація")
                icon = "info"
            
            # Build message
            message = event.user_message
            
            if event.suggestion:
                message += f"\n\n{L.get('status_warning', 'Suggestion: / Рекомендация: / Рекомендація:')} {event.suggestion}"
            
            # Show dialog
            if icon == "error":
                CTkMessageBox.error(parent_widget, title, message)
            elif icon == "warning":
                CTkMessageBox.warning(parent_widget, title, message)
            else:
                CTkMessageBox.info(parent_widget, title, message)
            
        except (ImportError, AttributeError, RuntimeError) as e:
            # Fallback to print if GUI not available
            print(f"[ERROR] {event.user_message}")
            logger.error(f"Failed to show error dialog: {e}")
    
    def get_last_error(self) -> Optional[ErrorEvent]:
        """Get the last handled error / Получить последнюю обработанную ошибку / Отримати останню оброблену помилку"""
        return self._last_error
    
    def get_error_history(self) -> List[ErrorEvent]:
        """Get error history / Получить историю ошибок / Отримати історію помилок"""
        return self._error_history.copy()
    
    def clear_history(self) -> None:
        """Clear error history / Очистить историю ошибок / Очистити історію помилок"""
        self._error_history.clear()
        self._last_error = None


# ==================== CONVENIENCE FUNCTIONS ====================

_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler / Получить глобальный обработчик ошибок / Отримати глобальний обробник помилок"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler.get_instance()
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
    show_dialog: bool = True,
    parent_widget: Optional[tk.Widget] = None,
    lang: str = "RU"
) -> ErrorEvent:
    """Convenience function to handle an error / Удобная функция для обработки ошибки / Зручна функція для обробки помилки"""
    return get_error_handler().handle(
        error, context, user_message, show_dialog, parent_widget, lang
    )


def handle_critical_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    lang: str = "RU"
) -> None:
    """Handle critical error and exit / Обработать критическую ошибку и выйти / Обробити критичну помилку та вийти"""
    handler = get_error_handler()
    event = handler.handle(
        error, context, show_dialog=True, lang=lang
    )
    
    # For fatal errors, exit after showing dialog
    if event.severity in (ErrorSeverity.CRITICAL, ErrorSeverity.FATAL):
        try:
            import sys
            sys.exit(1)
        except SystemExit:
            raise


def log_warning(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    lang: str = "RU"
) -> None:
    """Log a warning / Записать предупреждение / Записати попередження"""
    handler = get_error_handler()
    event = ErrorEvent(
        error_type="Warning",
        error_message=message,
        severity=ErrorSeverity.WARNING,
        category=category,
        context=context or {},
        user_message=message,
        handled=True,
        recoverable=True
    )
    handler._log_error(event)


def log_info(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    category: ErrorCategory = ErrorCategory.SYSTEM
) -> None:
    """Log an info message / Записать информационное сообщение / Записати інформаційне повідомлення"""
    handler = get_error_handler()
    event = ErrorEvent(
        error_type="Info",
        error_message=message,
        severity=ErrorSeverity.INFO,
        category=category,
        context=context or {},
        user_message=message,
        handled=True,
        recoverable=True
    )
    handler._log_error(event)


# ==================== DECORATORS ====================

def handle_errors(
    show_dialog: bool = True,
    lang: str = "RU",
    context: Optional[Dict[str, Any]] = None,
    user_message: Optional[str] = None,
    reraise: bool = False,
    default_return: Any = None
) -> Callable:
    """
    Decorator for automatic error handling.
    
    Декоратор для автоматической обработки ошибок.
    Декоратор для автоматичної обробки помилок.
    
    Args:
        show_dialog: Show error dialog / Показать диалог ошибки / Показати діалог помилки
        lang: Language code / Код языка / Код мови
        context: Additional context / Дополнительный контекст / Додатковий контекст
        user_message: Custom user message / Пользовательское сообщение / Користувацьке повідомлення
        reraise: Re-raise exception after handling / Повторно поднять исключение / Повторно підняти виняток
        default_return: Default return value on error / Значение по умолчанию при ошибке / Значення за замовчуванням при помилці
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseException as e:  # top-level handler must catch everything
                ctx = context or {}
                if args:
                    ctx["function_args"] = str(args[:5])  # Limit for safety
                if kwargs:
                    ctx["function_kwargs"] = {k: str(v)[:50] for k, v in kwargs.items()}
                ctx["function_name"] = func.__name__
                
                handle_error(
                    e,
                    context=ctx,
                    user_message=user_message,
                    show_dialog=show_dialog,
                    parent_widget=args[0] if args and hasattr(args[0], 'winfo_exists') else None,
                    lang=lang
                )
                
                if reraise:
                    raise
                return default_return
        return wrapper
    return decorator


# ==================== EXPORTS ====================

__all__ = [
    'ErrorHandler',
    'ErrorSeverity',
    'ErrorCategory',
    'ErrorEvent',
    'get_error_handler',
    'handle_error',
    'handle_critical_error',
    'log_warning',
    'log_info',
    'handle_errors',
]