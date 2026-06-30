"""
Utils module - helper functions

Модуль утилит - вспомогательные функции
Модуль утиліт - допоміжні функції

FIXED: Added full type hints for all exports
FIXED: Added ErrorHandler exports
FIXED: Fixed importer imports
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple, Union, Callable, TypeVar, cast

from utils.helpers import (
    get_global_radius,
    set_global_radius,
    center_screen,
    get_resource_path,
    play_sound,
    is_windows,
    is_macos,
    is_linux,
    apply_window_rounding,
    set_window_icon
)
from utils.paths import (
    get_base_dir,
    get_config_dir,
    get_config_file,
    get_db_file,
    get_salt_file,
    get_master_file,
    get_uuid_file,
    get_logs_dir,
    hide_dir
)
from utils.logger import get_logger, log_exception, log_crash_report, SecureLogger

# ==================== ERROR HANDLER ====================

from utils.error_handler import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    ErrorEvent,
    get_error_handler,
    handle_error,
    handle_critical_error,
    log_warning,
    log_info,
    handle_errors,
)

# ==================== IMPORTER ====================

from utils.importer import PasswordImporter

# ==================== EXPORTS ====================

__all__: List[str] = [
    # Helpers
    'get_global_radius',
    'set_global_radius',
    'center_screen',
    'get_resource_path',
    'play_sound',
    'is_windows',
    'is_macos',
    'is_linux',
    'apply_window_rounding',
    'set_window_icon',
    # Paths
    'get_base_dir',
    'get_config_dir',
    'get_config_file',
    'get_db_file',
    'get_salt_file',
    'get_master_file',
    'get_uuid_file',
    'get_logs_dir',
    'hide_dir',
    # Logger
    'get_logger',
    'log_exception',
    'log_crash_report',
    'SecureLogger',
    # Error Handler
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
    # Importer
    'PasswordImporter',
]