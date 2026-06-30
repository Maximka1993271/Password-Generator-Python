"""
Windows-specific anti-debug / VM detection.
Функции обнаружения для Windows.
Функції виявлення для Windows.
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

# ==================== WINDOWS DETECTION FUNCTIONS / ФУНКЦИИ ОБНАРУЖЕНИЯ ДЛЯ WINDOWS / ФУНКЦІЇ ВИЯВЛЕННЯ ДЛЯ WINDOWS ====================

def is_debugger_present_windows() -> bool:
    """Check if debugger is attached (Windows only)
    Проверить, подключён ли отладчик (только Windows)
    Перевірити, чи підключений відлагоджувач (тільки Windows)"""
    global _debug_detected

    if not _IS_WINDOWS:
        return False

    try:
        kernel32 = ctypes.windll.kernel32
        if kernel32.IsDebuggerPresent():
            logger.warning("Debugger detected via IsDebuggerPresent / Отладчик обнаружен через IsDebuggerPresent / Відлагоджувач виявлено через IsDebuggerPresent")
            _debug_detected = True
            return True

        ntdll = ctypes.windll.ntdll
        if ntdll.NtQueryInformationProcess:
            PROCESS_INFO_CLASS = 0x7
            debug_port = ctypes.c_void_p()
            size = ctypes.sizeof(debug_port)
            status = ntdll.NtQueryInformationProcess(
                ctypes.windll.kernel32.GetCurrentProcess(),
                PROCESS_INFO_CLASS,
                ctypes.byref(debug_port),
                size,
                None
            )
            if status == 0 and debug_port.value is not None:
                logger.warning("Debugger detected via NtQueryInformationProcess / Отладчик обнаружен через NtQueryInformationProcess / Відлагоджувач виявлено через NtQueryInformationProcess")
                _debug_detected = True
                return True
    except (AttributeError, OSError, TypeError, ValueError) as e:
        logger.debug(f"Windows debugger check failed / Ошибка проверки отладчика Windows / Помилка перевірки відлагоджувача Windows: {e}")

    return False


def check_debug_registers_windows() -> bool:
    """
    Check debug registers for hardware breakpoints (Windows only)
    Проверить регистры отладки на наличие аппаратных точек останова (только Windows)
    Перевірити регістри відлагодження на наявність апаратних точок зупину (тільки Windows)

    FIXED #45: Proper CONTEXT structure for x64 Windows
    Исправлено #45: Правильная структура CONTEXT для x64 Windows
    Виправлено #45: Правильна структура CONTEXT для x64 Windows
    """
    if not _IS_WINDOWS:
        return False

    try:
        import ctypes.wintypes

        is_64bit = sys.maxsize > 2**32

        if is_64bit:
            # x64 CONTEXT structure (debug registers part)
            class CONTEXT64(ctypes.Structure):
                _fields_ = [
                    ("P1Home", ctypes.c_uint64),
                    ("P2Home", ctypes.c_uint64),
                    ("P3Home", ctypes.c_uint64),
                    ("P4Home", ctypes.c_uint64),
                    ("P5Home", ctypes.c_uint64),
                    ("P6Home", ctypes.c_uint64),
                    ("ContextFlags", ctypes.c_uint32),
                    ("MxCsr", ctypes.c_uint32),
                    ("SegCs", ctypes.c_uint16),
                    ("SegDs", ctypes.c_uint16),
                    ("SegEs", ctypes.c_uint16),
                    ("SegFs", ctypes.c_uint16),
                    ("SegGs", ctypes.c_uint16),
                    ("SegSs", ctypes.c_uint16),
                    ("EFlags", ctypes.c_uint32),
                    ("Dr0", ctypes.c_uint64),
                    ("Dr1", ctypes.c_uint64),
                    ("Dr2", ctypes.c_uint64),
                    ("Dr3", ctypes.c_uint64),
                    ("Dr6", ctypes.c_uint64),
                    ("Dr7", ctypes.c_uint64),
                    ("Rax", ctypes.c_uint64),
                    ("Rcx", ctypes.c_uint64),
                    ("Rdx", ctypes.c_uint64),
                    ("Rbx", ctypes.c_uint64),
                    ("Rsp", ctypes.c_uint64),
                    ("Rbp", ctypes.c_uint64),
                    ("Rsi", ctypes.c_uint64),
                    ("Rdi", ctypes.c_uint64),
                    ("R8", ctypes.c_uint64),
                    ("R9", ctypes.c_uint64),
                    ("R10", ctypes.c_uint64),
                    ("R11", ctypes.c_uint64),
                    ("R12", ctypes.c_uint64),
                    ("R13", ctypes.c_uint64),
                    ("R14", ctypes.c_uint64),
                    ("R15", ctypes.c_uint64),
                    ("Rip", ctypes.c_uint64),
                ]

            CONTEXT_DEBUG_REGISTERS = 0x10010
            context = CONTEXT64()
        else:
            # x86 CONTEXT structure
            class CONTEXT86(ctypes.Structure):
                _fields_ = [
                    ("ContextFlags", ctypes.c_uint32),
                    ("Dr0", ctypes.c_uint32),
                    ("Dr1", ctypes.c_uint32),
                    ("Dr2", ctypes.c_uint32),
                    ("Dr3", ctypes.c_uint32),
                    ("Dr6", ctypes.c_uint32),
                    ("Dr7", ctypes.c_uint32),
                    ("FloatSave", ctypes.c_byte * 224),
                    ("SegGs", ctypes.c_uint32),
                    ("SegFs", ctypes.c_uint32),
                    ("SegEs", ctypes.c_uint32),
                    ("SegDs", ctypes.c_uint32),
                    ("Edi", ctypes.c_uint32),
                    ("Esi", ctypes.c_uint32),
                    ("Ebx", ctypes.c_uint32),
                    ("Edx", ctypes.c_uint32),
                    ("Ecx", ctypes.c_uint32),
                    ("Eax", ctypes.c_uint32),
                    ("Ebp", ctypes.c_uint32),
                    ("Eip", ctypes.c_uint32),
                    ("SegCs", ctypes.c_uint32),
                    ("EFlags", ctypes.c_uint32),
                    ("Esp", ctypes.c_uint32),
                    ("SegSs", ctypes.c_uint32),
                    ("ExtendedRegisters", ctypes.c_byte * 512),
                ]

            CONTEXT_DEBUG_REGISTERS = 0x10010
            context = CONTEXT86()

        context.ContextFlags = CONTEXT_DEBUG_REGISTERS
        kernel32 = ctypes.windll.kernel32
        current_thread = kernel32.GetCurrentThread()

        if kernel32.GetThreadContext(current_thread, ctypes.byref(context)):
            dr0 = context.Dr0 if is_64bit else context.Dr0
            dr1 = context.Dr1 if is_64bit else context.Dr1
            dr2 = context.Dr2 if is_64bit else context.Dr2
            dr3 = context.Dr3 if is_64bit else context.Dr3

            if dr0 != 0 or dr1 != 0 or dr2 != 0 or dr3 != 0:
                logger.warning("Hardware breakpoint detected in debug registers / Аппаратная точка останова обнаружена в регистрах отладки / Апаратна точка зупину виявлена в регістрах відлагодження")
                return True
    except (AttributeError, OSError, TypeError, ValueError) as e:
        logger.debug(f"Debug registers check failed / Ошибка проверки регистров отладки / Помилка перевірки регістрів відлагодження: {e}")

    return False


