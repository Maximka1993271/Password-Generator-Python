"""
Linux/macOS anti-debug detection.
Функции обнаружения для Linux/macOS.
Функції виявлення для Linux/macOS.
"""
from __future__ import annotations
import ctypes
import hashlib
import os
import platform
import re
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger("antidebug")
_IS_WINDOWS = platform.system() == "Windows"
_IS_LINUX   = platform.system() == "Linux"
_IS_MACOS   = platform.system() == "Darwin"

# ==================== LINUX/MACOS DETECTION FUNCTIONS / ФУНКЦИИ ОБНАРУЖЕНИЯ ДЛЯ LINUX/MACOS / ФУНКЦІЇ ВИЯВЛЕННЯ ДЛЯ LINUX/MACOS ====================
# FIXED #46: Added Linux/macOS anti-debug support
# Исправлено #46: Добавлена поддержка анти-отладки для Linux/macOS
# Виправлено #46: Додано підтримку анти-відлагодження для Linux/macOS

def is_debugger_present_unix() -> bool:
    """
    Check if process is being traced (Linux/macOS)
    Uses ptrace detection and /proc/self/status checking.

    Проверяет, отслеживается ли процесс (Linux/macOS)
    Использует обнаружение ptrace и проверку /proc/self/status.

    Перевіряє, чи відстежується процес (Linux/macOS)
    Використовує виявлення ptrace та перевірку /proc/self/status.
    """
    global _debug_detected

    if not (_IS_LINUX or _IS_MACOS):
        return False

    try:
        # Method 1: Check /proc/self/status for TracerPid (Linux only)
        if _IS_LINUX and os.path.exists("/proc/self/status"):
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("TracerPid:"):
                        tracer_pid = line.split(":")[1].strip()
                        if tracer_pid != "0":
                            logger.warning(f"Debugger detected via /proc/self/status: TracerPid={tracer_pid} / Отладчик обнаружен через /proc/self/status: TracerPid={tracer_pid} / Відлагоджувач виявлено через /proc/self/status: TracerPid={tracer_pid}")
                            _debug_detected = True
                            return True
                        break

        # Method 2: Check for common debugger environment variables
        debug_env_vars = ['PYCHARM_HOSTED', 'PYDEV_CONSOLE_ENCODING', 'DEBUGPY_LAUNCHER']
        for var in debug_env_vars:
            if os.environ.get(var):
                logger.warning(f"Debug environment detected: {var} / Обнаружена отладочная среда: {var} / Виявлено відлагоджувальне середовище: {var}")
                _debug_detected = True
                return True

    except (OSError, IOError, PermissionError, ValueError) as e:
        logger.debug(f"Unix debugger check failed / Ошибка проверки отладчика Unix / Помилка перевірки відлагоджувача Unix: {e}")

    return False


def check_parent_process_unix() -> bool:
    """
    Check if parent process is a debugger (Linux/macOS)

    Проверяет, является ли родительский процесс отладчиком (Linux/macOS)
    Перевіряє, чи є батьківський процес відлагоджувачем (Linux/macOS)
    """
    if not (_IS_LINUX or _IS_MACOS):
        return False

    try:
        # Get parent PID
        ppid = os.getppid()

        # Get parent process name
        if _IS_LINUX and os.path.exists(f"/proc/{ppid}/comm"):
            with open(f"/proc/{ppid}/comm", "r") as f:
                parent_name = f.read().strip().lower()
        elif _IS_MACOS:
            result = subprocess.run(['ps', '-p', str(ppid), '-o', 'comm='],
                                    capture_output=True, text=True, timeout=5)
            parent_name = result.stdout.strip().lower() if result.returncode == 0 else ""
        else:
            return False

        # List of known debuggers
        debugger_names = [
            'gdb', 'lldb', 'rr', 'valgrind', 'strace', 'ltrace',
            'pycharm', 'idea', 'vscode', 'code', 'devenv'
        ]

        for debugger in debugger_names:
            if debugger in parent_name:
                logger.warning(f"Parent process is debugger: {parent_name} / Родительский процесс является отладчиком: {parent_name} / Батьківський процес є відлагоджувачем: {parent_name}")
                return True

    except (OSError, IOError, PermissionError, subprocess.SubprocessError, ValueError) as e:
        logger.debug(f"Unix parent process check failed / Ошибка проверки родительского процесса Unix / Помилка перевірки батьківського процесу Unix: {e}")

    return False


def check_ptrace_scope() -> bool:
    """
    Check ptrace_scope setting on Linux (security feature)

    Проверяет настройку ptrace_scope на Linux (функция безопасности)
    Перевіряє налаштування ptrace_scope на Linux (функція безпеки)
    """
    if not _IS_LINUX:
        return False

    try:
        if os.path.exists("/proc/sys/kernel/yama/ptrace_scope"):
            with open("/proc/sys/kernel/yama/ptrace_scope", "r") as f:
                scope = f.read().strip()
                if scope == "0":
                    logger.debug("ptrace_scope=0 (ptrace allowed for all processes) / ptrace_scope=0 (ptrace разрешён для всех процессов) / ptrace_scope=0 (ptrace дозволено для всіх процесів)")
                else:
                    logger.debug(f"ptrace_scope={scope} (ptrace restricted) / ptrace_scope={scope} (ptrace ограничен) / ptrace_scope={scope} (ptrace обмежено)")
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"ptrace_scope check failed / Ошибка проверки ptrace_scope / Помилка перевірки ptrace_scope: {e}")

    return False


