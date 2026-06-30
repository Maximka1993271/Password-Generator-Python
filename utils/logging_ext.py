"""
Compatibility shim — all symbols now live in utils.logger.
Шим совместимости — все символы перенесены в utils.logger.
Шим сумісності — всі символи перенесені в utils.logger.
"""
from __future__ import annotations

from utils.logger import (          # noqa: F401
    LogContext,
    log_operation,
    log_function_call,
    log_function_call_silent,
    log_crash_report,
    log_exception,
    get_logger,
)

# Backward-compatible aliases
log_error_with_context  = log_exception      # noqa: F401
log_critical_error      = log_crash_report   # noqa: F401

__all__ = [
    "LogContext",
    "log_operation",
    "log_function_call",
    "log_function_call_silent",
    "log_crash_report",
    "log_exception",
    "log_error_with_context",
    "log_critical_error",
    "get_logger",
]
