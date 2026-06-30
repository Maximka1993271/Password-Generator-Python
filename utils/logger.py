#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified, secure logging system for Secure Pass Pro.
Единая, безопасная система логирования для Secure Pass Pro.
Єдина, безпечна система логування для Secure Pass Pro.

Architecture
────────────
One root logger «spp» owns two handlers:
  • ConsoleHandler  — INFO+,   format: «HH:MM:SS [LEVEL] name: msg»
  • RotatingFile    — DEBUG+,  format: «YYYY-MM-DD HH:MM:SS [LEVEL] name (file:line): msg»
  • CrashFile       — CRITICAL, separate crash_<ts>.log per incident

SensitiveDataFilter is attached to every handler, never to individual loggers,
so it runs exactly once per record regardless of logger hierarchy depth.

Public API (unchanged — backward-compatible)
────────────────────────────────────────────
  get_logger(name)      → logging.Logger  (child of «spp» root)
  log_crash_report(exc) → str             (path to crash file)
  log_exception(lgr, e) → None
  cleanup_old_logs()    → int
  setup_logging()       → None            (call once at startup)
  LogContext            — thread-local context dict
  log_operation(name)   — context-manager with timing
  log_function_call()   — decorator
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import re
import sys
import threading
import traceback
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional

# ══════════════════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════════════════

ROOT_LOGGER_NAME = "spp"

# Single app log — all loggers write here
APP_LOG_FILENAME  = "app.log"
MAX_LOG_BYTES     = 5 * 1024 * 1024   # 5 MB per file
LOG_BACKUP_COUNT  = 5                  # keep 5 rotated files

# Format strings
_FMT_CONSOLE = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
_FMT_FILE    = "%(asctime)s [%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
_FMT_DATE_C  = "%H:%M:%S"
_FMT_DATE_F  = "%Y-%m-%d %H:%M:%S"

# ── Canonical flat-name → dotted-hierarchy mapping ────────────────
# «get_logger("database")» becomes «spp.storage.database» internally.
_NAME_MAP: Dict[str, str] = {
    # app
    "launcher":                 "app.launcher",
    "crash":                    "app.crash",
    "cleanup":                  "app.cleanup",
    "error_handler":            "app.error",
    "logging_ext":              "app.logging",
    "lang":                     "app.lang",
    # core
    "generator":                "core.generator",
    "passphrase_generator":     "core.passphrase",
    "name_generator":           "core.name_generator",
    # gui
    "main_window":              "gui.main_window",
    "main_window_cleanup":      "gui.main_window.cleanup",
    "main_window_events":       "gui.main_window.events",
    "main_window_helpers":      "gui.main_window.helpers",
    "main_window_helpers_2fa":  "gui.main_window.helpers.tfa",
    "main_window_helpers_data": "gui.main_window.helpers.data",
    "main_window_helpers_lang": "gui.main_window.helpers.lang",
    "main_window_helpers_ui":   "gui.main_window.helpers.ui",
    "main_window_ui":           "gui.main_window.ui",
    "dialogs":                  "gui.dialogs",
    "dialogs_about":            "gui.dialogs.about",
    "dialogs_base":             "gui.dialogs.base",
    "dialogs_db_actions":       "gui.dialogs.db.actions",
    "dialogs_db_bulk":          "gui.dialogs.db.bulk",
    "dialogs_db_core":          "gui.dialogs.db.core",
    "dialogs_db_extra":         "gui.dialogs.db.extra",
    "dialogs_input":            "gui.dialogs.input",
    "dialogs_messagebox":       "gui.dialogs.messagebox",
    "dialogs_tooltip":          "gui.dialogs.tooltip",
    "dialogs_widgets":          "gui.dialogs.widgets",
    "passphrase_dialog":        "gui.dialogs.passphrase",
    "settings":                 "gui.settings",
    "settings_window":          "gui.settings.window",
    "password_ops":             "gui.password_ops",
    "auto_lock":                "gui.auto_lock",
    "rgb_mixin":                "gui.rgb_mixin",
    "ui_setup":                 "gui.ui_setup",
    "updater_mixin":            "gui.updater_mixin",
    "widgets":                  "gui.widgets",
    # security
    "antidebug":                "security.antidebug",
    "clipboard":                "security.clipboard",
    "hibp":                     "security.hibp",
    "integrity":                "security.integrity",
    "integrity_check":          "security.integrity.check",
    "master":                   "security.master",
    "master_auth":              "security.master.auth",
    "master_lockout":           "security.master.lockout",
    "master_mixin":             "security.master.mixin",
    "master_recovery":          "security.master.recovery",
    "panic":                    "security.panic",
    "totp":                     "security.totp",
    "vm_detection":             "security.vm_detection",
    # encryption sub-package
    "encryption":               "security.encryption",
    "encryption.cipher":        "security.encryption.cipher",
    "encryption.dpapi":         "security.encryption.dpapi",
    "encryption.keys":          "security.encryption.keys",
    "encryption.memory":        "security.encryption.memory",
    "encryption.sqlcipher":     "security.encryption.sqlcipher",
    "encryption.verification":  "security.encryption.verification",
    # storage
    "config":                   "storage.config",
    "database":                 "storage.database",
    "database_backup":          "storage.database.backup",
    "database_base":            "storage.database.base",
    "database_crud":            "storage.database.crud",
    "database_health":          "storage.database.health",
    "database_migrations":      "storage.database.migrations",
    "database_queries":         "storage.database.queries",
    "database_search":          "storage.database.search",
    "db_diagnostics":           "storage.database.diagnostics",
    # utils
    "autotype":                 "utils.autotype",
    "cloud_sync":               "utils.cloud_sync",
    "export":                   "utils.export",
    "export_base":              "utils.export.base",
    "export_csv":               "utils.export.csv",
    "export_dialog":            "utils.export.dialog",
    "export_html":              "utils.export.html",
    "export_json":              "utils.export.json",
    "export_kdbx":              "utils.export.kdbx",
    "import":                   "utils.importer",
    "import_1password":         "utils.importer.onepassword",
    "import_1pux":              "utils.importer.onepux",
    "import_base":              "utils.importer.base",
    "import_bitwarden":         "utils.importer.bitwarden",
    "import_csv":               "utils.importer.csv",
    "import_dialog":            "utils.importer.dialog",
    "import_json":              "utils.importer.json",
    "import_kdbx":              "utils.importer.kdbx",
    "import_keepass_xml":       "utils.importer.keepass",
    "import_passwords":         "utils.importer.passwords",
    "qr_utils":                 "utils.qr",
    "secure_file_ops":          "utils.secure_file_ops",
    "secure_memory":            "utils.secure_memory",
    "theme_utils":              "utils.theme",
    "updater":                  "utils.updater",
    "hotkey_manager":           "utils.hotkey",
    # tests (low-priority, just namespace)
    "test_config":              "tests.config",
    "test_encryption":          "tests.encryption",
}

# ══════════════════════════════════════════════════════════════════
#  Sensitive-data filter  (applied to handlers, not loggers)
# ══════════════════════════════════════════════════════════════════

# ── Sensitive-data filter ─────────────────────────────────────
# Passwords, tokens, and base-64 blobs must NEVER appear in log files
# because logs are often forwarded to central aggregators (Splunk, ELK)
# or stored with looser permissions than the database itself.
#
# The filter is attached to the *handler*, not individual loggers, so:
#  1. It runs exactly once per record even with a deep logger hierarchy.
#  2. Third-party libraries that write to the root logger are also covered.
#  3. Adding a new logger never risks accidentally bypassing the filter.
class SensitiveDataFilter(logging.Filter):
    """Strip passwords, keys and base-64 blobs from log records.
    Удаляет пароли, ключи и base-64 из записей лога.
    Видаляє паролі, ключі та base-64 із записів логу."""

    # Patterns are applied in order — each is a (compiled_regex, replacement)
    # pair.  We use non-capturing groups where possible to avoid accidentally
    # capturing user data into match groups that might be logged elsewhere.
    _PATTERNS: List[tuple[re.Pattern[str], str]] = [
        (re.compile(r'(?i)(password|passwd|pwd|master_pass(?:word)?)\s*[=:]\s*[\'"]?(\S+)[\'"]?'),
         r'\1=[FILTERED]'),
        (re.compile(r'(?i)(token|api_key|secret|private_key|encryption_key|bearer|auth(?:orization)?)\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{8,})[\'"]?'),
         r'\1=[FILTERED]'),
        (re.compile(r'(?i)(salt|nonce|iv)\s*[=:]\s*[\'"]?([A-Za-z0-9+/=]+)[\'"]?'),
         r'\1=[FILTERED]'),
        (re.compile(r'[A-Za-z0-9+/]{48,}={0,2}'),
         '[BASE64_FILTERED]'),
    ]

    def _clean(self, text: str) -> str:
        """
        Handle clean.
        Обработать clean.
        Обробити clean.
        """
        for pattern, repl in self._PATTERNS:
            try:
                text = pattern.sub(repl, text)
            except (re.error, TypeError):
                pass
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Handle filter.
        Обработать filter.
        Обробити filter.
        """
        if isinstance(record.msg, str):
            record.msg = self._clean(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                self._clean(a) if isinstance(a, str) else a
                for a in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                k: self._clean(v) if isinstance(v, str) else v
                for k, v in record.args.items()
            }
        if record.exc_text:
            record.exc_text = self._clean(record.exc_text)
        return True


# ══════════════════════════════════════════════════════════════════
#  Central logging setup  (called once at startup)
# ══════════════════════════════════════════════════════════════════

_setup_done = False
_setup_lock = threading.Lock()


def get_logs_dir() -> str:
    """Return (and create) the logs directory.
    Возвращает (и создаёт) директорию логов.
    Повертає (і створює) директорію логів."""
    try:
        from utils.paths import get_logs_dir as _p
        return _p()
    except ImportError:
        base = Path(__file__).resolve().parent.parent
        d = base / "logs"
        d.mkdir(exist_ok=True)
        return str(d)


def setup_logging(
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
    log_dir: Optional[str] = None,
) -> None:
    """Configure the root «spp» logger with console + rotating-file handlers.

    Safe to call multiple times — initialises only once.
    Безопасно вызывать несколько раз — инициализирует только один раз.
    Безпечно викликати кілька разів — ініціалізує лише один раз.
    """
    global _setup_done
    with _setup_lock:
        if _setup_done:
            return

        root = logging.getLogger(ROOT_LOGGER_NAME)
        root.setLevel(level)
        root.propagate = False
        root.handlers.clear()

        sensitive = SensitiveDataFilter()

        # ── Console handler ───────────────────────────────────
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(console_level)
        ch.setFormatter(logging.Formatter(_FMT_CONSOLE, _FMT_DATE_C))
        ch.addFilter(sensitive)
        root.addHandler(ch)

        # ── Rotating file handler ─────────────────────────────
        try:
            logs = log_dir or get_logs_dir()
            log_path = os.path.join(logs, APP_LOG_FILENAME)
            fh = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=MAX_LOG_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
                delay=True,
            )
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(_FMT_FILE, _FMT_DATE_F))
            fh.addFilter(sensitive)
            root.addHandler(fh)
        except (OSError, PermissionError) as exc:
            root.warning("Cannot open log file: %s", exc)

        _setup_done = True


# ══════════════════════════════════════════════════════════════════
#  Public factory  — get_logger()
# ══════════════════════════════════════════════════════════════════

_logger_registry: Dict[str, logging.Logger] = {}
_registry_lock   = threading.Lock()


def get_logger(name: str) -> logging.Logger:
    """Return a child Logger of the «spp» root, using canonical dotted names.

    Возвращает дочерний Logger корня «spp» с каноническими именами.
    Повертає дочірній Logger кореня «spp» з канонічними іменами.

    Usage::

        logger = get_logger("database")      # → spp.storage.database
        logger = get_logger("storage.config") # → spp.storage.config
    """
    setup_logging()   # no-op after first call

    with _registry_lock:
        if name in _logger_registry:
            return _logger_registry[name]

        # Resolve canonical dotted name
        dotted = _NAME_MAP.get(name, name)
        full   = f"{ROOT_LOGGER_NAME}.{dotted}"

        lgr = logging.getLogger(full)
        lgr.propagate = True   # bubble up to spp root
        # No handlers, no filters — root handles everything
        _logger_registry[name] = lgr
        return lgr


# ══════════════════════════════════════════════════════════════════
#  Crash reporting
# ══════════════════════════════════════════════════════════════════

def log_crash_report(
    exc: BaseException,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Write a crash report file and return its path.
    Записывает файл отчёта о сбое и возвращает его путь.
    Записує файл звіту про збій і повертає його шлях."""
    ts     = datetime.now()
    stamp  = ts.strftime("%Y%m%d_%H%M%S")
    path   = os.path.join(get_logs_dir(), f"crash_{stamp}.log")

    lines: List[str] = [
        "=" * 64,
        "Secure Pass Pro — Crash Report",
        f"Time    : {ts.isoformat()}",
        f"Python  : {sys.version}",
        f"Platform: {sys.platform}",
        "=" * 64,
        "",
        f"Exception : {type(exc).__name__}",
        f"Message   : {exc}",
        "",
        "Traceback:",
        traceback.format_exc(),
    ]
    if context:
        lines += ["", "Context:"]
        lines += [f"  {k}: {v}" for k, v in context.items()]
    lines += ["", "=" * 64]

    try:
        Path(path).write_text("\n".join(lines), encoding="utf-8")
    except (OSError, PermissionError) as write_err:
        print(f"[logger] Cannot write crash report: {write_err}", file=sys.stderr)
        return ""

    _crash = get_logger("crash")
    _crash.critical("Crash report → %s  |  %s: %s", path, type(exc).__name__, exc)
    return path


def log_exception(
    logger: logging.Logger,
    exc: Exception,
    context: str = "",
) -> None:
    """Log *exc* at ERROR level with optional context prefix.
    Логирует exc на уровне ERROR с необязательным контекстом.
    Логує exc на рівні ERROR з необов'язковим контекстом."""
    msg = f"[{context}] " if context else ""
    logger.error("%s%s: %s", msg, type(exc).__name__, exc)
    logger.debug("Traceback:\n%s", traceback.format_exc())


# ══════════════════════════════════════════════════════════════════
#  Thread-local context  (absorbed from logging_ext.py)
# ══════════════════════════════════════════════════════════════════

class LogContext:
    """Thread-local key-value context that is appended to log records.
    Локальный для потока контекст ключ-значение для записей лога.
    Локальний для потоку контекст ключ-значення для записів логу."""

    _local: threading.local = threading.local()

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self._kw = kwargs
        self._old: Dict[str, Any] = {}

    def __enter__(self) -> "LogContext":
        """
        Enter the context manager.
        Войти в контекстный менеджер.
        Увійти в контекстний менеджер.
        """
        self._old = dict(getattr(LogContext._local, "data", {}))
        LogContext._local.data = {**self._old, **self._kw}
        return self

    def __exit__(self, *_: object) -> None:
        """
        Exit the context manager and clean up.
        Выйти из контекстного менеджера и освободить ресурсы.
        Вийти з контекстного менеджера та звільнити ресурси.
        """
        LogContext._local.data = self._old

    @classmethod
    def get(cls) -> Dict[str, Any]:
        """Return the current thread's context dict."""
        return dict(getattr(cls._local, "data", {}))

    @classmethod
    def add(cls, **kwargs: Any) -> "LogContext":
        """Convenience: ``with LogContext.add(user="alice"):``"""
        return cls(**kwargs)


# ══════════════════════════════════════════════════════════════════
#  Decorators & context managers  (absorbed from logging_ext.py)
# ══════════════════════════════════════════════════════════════════

@contextmanager
def log_operation(
    name: str,
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
) -> Generator[None, None, None]:
    """Context manager that logs start/end/error of an operation with timing.

    Usage::
        with log_operation("save config", logger):
            ...

    Контекстный менеджер, логирующий старт/конец/ошибку операции.
    Контекстний менеджер, що логує старт/кінець/помилку операції."""
    lgr  = logger or get_logger("app")
    t0   = datetime.now()
    lgr.debug("START %s", name)
    try:
        yield
        elapsed = (datetime.now() - t0).total_seconds()
        lgr.log(level, "DONE  %s  (%.3fs)", name, elapsed)
    except BaseException as exc:  # catch KeyboardInterrupt + SystemExit too
        elapsed = (datetime.now() - t0).total_seconds()
        lgr.error("FAIL  %s  (%.3fs)  %s: %s", name, elapsed, type(exc).__name__, exc)
        raise


def log_function_call(
    logger: Optional[logging.Logger] = None,
    *,
    log_args: bool = True,
    log_result: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that logs every call to the decorated function.

    Usage::
        @log_function_call(logger)
        def save(self, label: str) -> bool: ...

    Декоратор, логирующий каждый вызов декорируемой функции.
    Декоратор, що логує кожен виклик декорованої функції."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            lgr = logger or get_logger("app")
            if log_args:
                parts = [repr(a) for a in args[1:]] + [f"{k}={v!r}" for k, v in kwargs.items()]
                arg_str = ", ".join(parts)[:200]
                cls_name = type(args[0]).__name__ if args else ""
                lgr.debug("CALL %s%s(%s)",
                          f"{cls_name}." if cls_name else "",
                          fn.__name__, arg_str)
            try:
                result = fn(*args, **kwargs)
                if log_result:
                    lgr.debug("RETURN %s → %r", fn.__name__, result)
                return result
            except BaseException as exc:  # re-raised immediately; must catch all
                lgr.error("ERROR in %s: %s: %s", fn.__name__, type(exc).__name__, exc)
                raise
        return wrapper
    return decorator


def log_function_call_silent(
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Like *log_function_call* but logs only errors, not every call.
    Как log_function_call, но логирует только ошибки.
    Як log_function_call, але логує лише помилки."""
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            lgr = logger or get_logger("app")
            try:
                return fn(*args, **kwargs)
            except BaseException as exc:  # re-raised immediately
                cls  = type(args[0]).__name__ if args else ""
                name = f"{cls}.{fn.__name__}" if cls else fn.__name__
                lgr.error("ERROR in %s: %s: %s", name, type(exc).__name__, exc)
                raise
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════
#  House-keeping
# ══════════════════════════════════════════════════════════════════

def cleanup_old_logs(
    max_age_days: int = 30,
    max_total_mb: int = 100,
) -> int:
    """Delete log files older than *max_age_days* or when total > *max_total_mb*.
    Удаляет лог-файлы старше max_age_days или при превышении max_total_mb.
    Видаляє лог-файли старші max_age_days або при перевищенні max_total_mb."""
    logs_dir = get_logs_dir()
    lgr      = get_logger("cleanup")
    deleted  = 0
    now      = datetime.now().timestamp()
    cutoff   = max_age_days * 86_400
    limit    = max_total_mb * 1024 * 1024

    try:
        entries = [
            (os.path.join(logs_dir, f), os.path.getmtime(os.path.join(logs_dir, f)),
             os.path.getsize(os.path.join(logs_dir, f)))
            for f in os.listdir(logs_dir)
            if f.endswith(".log")
        ]
    except (OSError, PermissionError) as exc:
        lgr.error("Cannot list logs dir: %s", exc)
        return 0

    # Delete by age
    for path, mtime, _ in entries:
        if now - mtime > cutoff:
            try:
                os.remove(path)
                deleted += 1
            except (OSError, PermissionError):
                pass

    # Delete oldest until under size limit
    remaining = [(p, m, s) for p, m, s in entries
                 if not (now - m > cutoff) and os.path.exists(p)]
    remaining.sort(key=lambda x: x[1])
    total_size = sum(s for _, _, s in remaining)
    for path, _, size in remaining:
        if total_size <= limit:
            break
        try:
            os.remove(path)
            total_size -= size
            deleted    += 1
        except (OSError, PermissionError):
            pass

    if deleted:
        lgr.info("Cleaned %d old log file(s)", deleted)
    return deleted



# ── Backward-compatibility alias ─────────────────────────────────
# Old code imported SecureLogger; now it's just logging.Logger
SecureLogger = logging.Logger
# ══════════════════════════════════════════════════════════════════
#  Exports
# ══════════════════════════════════════════════════════════════════

__all__: List[str] = [
    "get_logger",
    "setup_logging",
    "log_crash_report",
    "log_exception",
    "cleanup_old_logs",
    "get_logs_dir",
    "SensitiveDataFilter",
    "LogContext",
    "log_operation",
    "log_function_call",
    "log_function_call_silent",
    "ROOT_LOGGER_NAME",
    "SecureLogger",
    "APP_LOG_FILENAME",
]
