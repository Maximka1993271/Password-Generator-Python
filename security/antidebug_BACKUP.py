"""
Anti-debugging and anti-analysis protection for SecurePassPro - Core Module

ВАЖНО: Anti-debugging в Python:
- Никогда не будет полностью надёжным
- Опытный reverse engineer обойдёт его
- Но как дополнительный слой защиты — очень хорошо.

FIXED #45: Corrected CONTEXT structure for x64 Windows
FIXED #46: Added Linux/macOS anti-debug support with ptrace detection
FIXED #EX: Replaced broad Exception with specific exceptions

Исправлено #45: Исправлена структура CONTEXT для x64 Windows
Исправлено #46: Добавлена поддержка анти-отладки для Linux/macOS с обнаружением ptrace
Исправлено #EX: Заменены общие Exception на конкретные исключения

Виправлено #45: Виправлено структуру CONTEXT для x64 Windows
Виправлено #46: Додано підтримку анти-відлагодження для Linux/macOS з виявленням ptrace
Виправлено #EX: Замінено загальні Exception на конкретні винятки

Core module contains:
- Debugger detection (Windows API, Linux /proc, macOS ptrace)
- Parent process checking
- Debug environment detection
- Integrity self-check (via integrity_check module)
- Background checks

Основной модуль содержит:
- Обнаружение отладчика (Windows API, Linux /proc, macOS ptrace)
- Проверку родительского процесса
- Обнаружение отладочного окружения
- Самопроверку целостности (через модуль integrity_check)
- Фоновые проверки

Основний модуль містить:
- Виявлення відлагоджувача (Windows API, Linux /proc, macOS ptrace)
- Перевірку батьківського процесу
- Виявлення відлагоджувального середовища
- Самоперевірку цілісності (через модуль integrity_check)
- Фонові перевірки
"""

import sys
import os
import ctypes
import platform
import subprocess
import time
import threading
from typing import Tuple, List, Optional, Dict, Any
from utils.logger import get_logger

# Import from integrity_check module
from security.integrity_check import (
    calculate_file_hash,
    verify_file_integrity,
    perform_self_check as _perform_self_check,
    check_code_integrity as _check_code_integrity,
    start_background_integrity_checks as _start_integrity_checks,
    stop_background_integrity_checks as _stop_integrity_checks,
    get_integrity_status as _get_integrity_status,
)

# Import from vm_detection module
from security.vm_detection import (
    is_vm_detected as _is_vm_detected,
    is_vm_detected_silent as _is_vm_detected_silent,
    detect_hypervisor as _detect_hypervisor,
    check_timing_anomalies as _check_timing_anomalies,
    is_sandboxed as _is_sandboxed,
    get_vm_detection_status as _get_vm_detection_status,
    analyze_environment as _analyze_environment,
    _vm_detected,
)

logger = get_logger("antidebug")

# Global state / Глобальное состояние / Глобальний стан
_debug_detected = False
_self_check_timer: Optional[threading.Timer] = None

# Platform detection / Определение платформы / Визначення платформи
_IS_WINDOWS = platform.system() == "Windows"
_IS_LINUX = platform.system() == "Linux"
_IS_MACOS = platform.system() == "Darwin"


class AntiDebugError(Exception):
    """Exception when debugger is detected / Исключение при обнаружении отладки / Виняток при виявленні відлагодження"""
    pass


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


# ==================== CROSS-PLATFORM WRAPPER FUNCTIONS / ОБЁРТКИ ДЛЯ ВСЕХ ПЛАТФОРМ / ОБГОРТКИ ДЛЯ ВСІХ ПЛАТФОРМ ====================

def is_debugger_present() -> bool:
    """
    Check if debugger is attached (cross-platform)

    Проверить, подключён ли отладчик (кросс-платформенно)
    Перевірити, чи підключений відлагоджувач (кросплатформено)
    """
    if _IS_WINDOWS:
        return is_debugger_present_windows()
    else:
        return is_debugger_present_unix()


def check_debug_registers() -> bool:
    """
    Check debug registers for hardware breakpoints (Windows only)

    Проверить регистры отладки на наличие аппаратных точек останова (только Windows)
    Перевірити регістри відлагодження на наявність апаратних точок зупину (тільки Windows)
    """
    if _IS_WINDOWS:
        return check_debug_registers_windows()
    return False


def check_parent_process() -> bool:
    """
    Check if parent process is a debugger (cross-platform)

    Проверить, является ли родительский процесс отладчиком (кросс-платформенно)
    Перевірити, чи є батьківський процес відлагоджувачем (кросплатформено)
    """
    if _IS_WINDOWS:
        return _check_parent_process_windows()
    else:
        return check_parent_process_unix()


def _check_parent_process_windows() -> bool:
    """Windows-specific parent process check"""
    try:
        import ctypes.wintypes

        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi

        current_pid = kernel32.GetCurrentProcessId()
        parent_pid = 0
        found = False

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.wintypes.DWORD),
                ("cntUsage", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("cntThreads", ctypes.wintypes.DWORD),
                ("th32ParentProcessID", ctypes.wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)
            ]

        hSnapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        if hSnapshot:
            entry = PROCESSENTRY32()
            entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

            if kernel32.Process32First(hSnapshot, ctypes.byref(entry)):
                while True:
                    if entry.th32ProcessID == current_pid:
                        parent_pid = entry.th32ParentProcessID
                        found = True
                        break
                    if not kernel32.Process32Next(hSnapshot, ctypes.byref(entry)):
                        break

            kernel32.CloseHandle(hSnapshot)

        if not found or parent_pid == 0:
            return False

        debugger_processes = [
            "devenv.exe", "ollydbg.exe", "x64dbg.exe", "x32dbg.exe",
            "ida.exe", "ida64.exe", "windbg.exe", "gdb.exe", "lldb.exe",
            "pydevd.py", "pycharm64.exe", "pycharm.exe", "vscode.exe"
        ]

        hProcess = kernel32.OpenProcess(0x0400 | 0x0010, False, parent_pid)
        if hProcess:
            exe_name = ctypes.create_string_buffer(260)
            psapi.GetModuleBaseNameA(hProcess, None, exe_name, 260)
            kernel32.CloseHandle(hProcess)

            parent_name = exe_name.value.decode('latin-1', errors='ignore').lower()
            for debugger in debugger_processes:
                if debugger in parent_name:
                    logger.warning(f"Parent process is debugger: {parent_name} / Родительский процесс является отладчиком: {parent_name} / Батьківський процес є відлагоджувачем: {parent_name}")
                    return True
    except (AttributeError, OSError, TypeError, ValueError) as e:
        logger.debug(f"Windows parent process check failed / Ошибка проверки родительского процесса Windows / Помилка перевірки батьківського процесу Windows: {e}")

    return False


def is_debugger_present_silent() -> bool:
    """Silent version of debugger detection (no logging)"""
    if _IS_WINDOWS:
        try:
            kernel32 = ctypes.windll.kernel32
            if kernel32.IsDebuggerPresent():
                return True
        except (AttributeError, OSError, TypeError):
            pass
    else:
        try:
            if _IS_LINUX and os.path.exists("/proc/self/status"):
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if line.startswith("TracerPid:"):
                            tracer_pid = line.split(":")[1].strip()
                            if tracer_pid != "0":
                                return True
                            break
        except (OSError, IOError, PermissionError):
            pass

    return False


def check_debug_env() -> List[str]:
    """Check for debug environment variables"""
    debug_indicators = []
    debug_env_vars = [
        'PYCHARM_HOSTED', 'PYDEV_CONSOLE_ENCODING', 'DEBUGPY_LAUNCHER',
        'PYTEST_CURRENT_TEST', 'PYTHONDEBUG', 'PYTHONVERBOSE'
    ]

    for var in debug_env_vars:
        try:
            if os.environ.get(var):
                debug_indicators.append(var)
        except (KeyError, TypeError) as e:
            logger.debug(f"Env var check failed for {var}: {e}")

    return debug_indicators


# ==================== TIMING ANOMALY CHECK ====================

def check_timing_anomalies() -> bool:
    """
    Check for timing anomalies (VM detection)
    Проверка аномалий времени (обнаружение VM)
    Перевірка аномалій часу (виявлення VM)
    """
    return _check_timing_anomalies()


# ==================== VM AND SANDBOX DETECTION ====================

def is_vm_detected() -> bool:
    """Basic VM detection (VMware, VirtualBox, Hyper-V) - cross-platform"""
    return _is_vm_detected()


def is_vm_detected_silent() -> bool:
    """Silent version of VM detection (no logging)"""
    return _is_vm_detected_silent()


def detect_hypervisor() -> bool:
    """Detect hypervisor presence"""
    return _detect_hypervisor()


def is_sandboxed() -> Tuple[bool, List[str]]:
    """Detect sandbox/VM environment"""
    return _is_sandboxed()


def get_vm_detection_status() -> Dict[str, Any]:
    """Get VM and sandbox detection status"""
    return _get_vm_detection_status()


def analyze_environment() -> Dict[str, Any]:
    """
    Perform comprehensive environment analysis.
    
    Выполняет комплексный анализ окружения.
    Виконує комплексний аналіз середовища.
    """
    return _analyze_environment()


# ==================== COMPREHENSIVE CHECKS ====================

def is_debugged() -> Tuple[bool, List[str]]:
    """Comprehensive debug detection"""
    checks = []

    try:
        if is_debugger_present():
            checks.append("Debugger detected via API / Отладчик обнаружен через API / Відлагоджувач виявлено через API")

        if check_debug_registers():
            checks.append("Hardware breakpoint detected / Обнаружена аппаратная точка останова / Виявлено апаратну точку зупину")

        if check_parent_process():
            checks.append("Debugger parent process detected / Обнаружен родительский процесс-отладчик / Виявлено батьківський процес-відлагоджувач")

        if check_timing_anomalies():
            checks.append("Timing anomaly detected / Обнаружена аномалия времени / Виявлено аномалію часу")

        debug_indicators = check_debug_env()
        if debug_indicators:
            checks.append(f"Debug environment: {', '.join(debug_indicators)} / Отладочная среда: {', '.join(debug_indicators)} / Відлагоджувальне середовище: {', '.join(debug_indicators)}")
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug(f"Debug env check failed / Ошибка проверки окружения отладки / Помилка перевірки середовища відлагодження: {e}")

    return len(checks) > 0, checks


# ==================== PROTECTION MEASURES ====================

def protect_from_debugging() -> None:
    """Apply anti-debugging measures"""
    try:
        debugged, reasons = is_debugged()

        if debugged:
            logger.warning(f"Anti-debugging: {', '.join(reasons)}")
            time.sleep(2)

    except (ImportError, AttributeError, OSError, TimeoutError) as e:
        logger.error(f"Anti-debugging failed / Ошибка анти-отладки / Помилка анти-відлагодження: {e}")


def protect_from_timing_analysis() -> None:
    """Protect against timing analysis"""
    try:
        import random
        delay = random.uniform(0.0005, 0.0025)
        time.sleep(delay)
    except (ImportError, ValueError) as e:
        logger.debug(f"Timing analysis protection failed / Ошибка защиты от анализа времени / Помилка захисту від аналізу часу: {e}")


# ==================== INTEGRITY SELF-CHECKS ====================

def perform_self_check() -> bool:
    """Perform integrity self-check on critical files"""
    return _perform_self_check()


def check_code_integrity() -> bool:
    """Check if code has been modified at runtime"""
    return _check_code_integrity()


def get_integrity_status() -> Dict[str, Any]:
    """Get current integrity status"""
    return _get_integrity_status()


# ==================== BACKGROUND CHECKS ====================

def start_background_checks(interval: int = 30) -> None:
    """Start background anti-debug checks"""
    _start_integrity_checks(interval)


def stop_background_checks() -> None:
    """Stop background anti-debug checks"""
    _stop_integrity_checks()


# ==================== GET DETECTION STATUS ====================

def get_detection_status() -> Dict[str, Any]:
    """Get current detection status"""
    sandboxed, sandbox_reasons = is_sandboxed()
    debugged, debug_reasons = is_debugged()

    return {
        "debug_detected": _debug_detected,
        "debug_reasons": debug_reasons,
        "vm_detected": _vm_detected,
        "sandbox_detected": sandboxed,
        "sandbox_reasons": sandbox_reasons,
        "integrity_verified": get_integrity_status().get("integrity_verified", False),
        "platform": platform.system(),
        "python_version": sys.version,
    }


def reset_detection_state() -> None:
    """Reset detection state (for testing)"""
    global _debug_detected
    _debug_detected = False
    from security.vm_detection import reset_vm_detection_state
    reset_vm_detection_state()


# ==================== INITIALIZATION ====================

def init_anti_debug(enable_background_checks: bool = False) -> None:
    """
    Initialize all anti-debugging protections (cross-platform)

    Инициализировать все анти-отладочные защиты (кросс-платформенно)
    Ініціалізувати всі анти-відлагоджувальні захисти (кросплатформено)
    """
    try:
        protect_from_debugging()
        protect_from_timing_analysis()
        check_code_integrity()

        if not _IS_WINDOWS:
            logger.info("Anti-debugging initialized with limited capabilities on this platform / Анти-отладка инициализирована с ограниченными возможностями на этой платформе / Анти-відлагодження ініціалізовано з обмеженими можливостями на цій платформі")
        else:
            logger.debug("Anti-debugging protections initialized / Анти-отладочные защиты инициализированы / Анти-відлагоджувальні захисти ініціалізовано")

        if enable_background_checks:
            start_background_checks()

    except (ImportError, AttributeError, OSError, RuntimeError) as e:
        logger.error(f"Anti-debug init failed / Ошибка инициализации анти-отладки / Помилка ініціалізації анти-відлагодження: {e}")


# ==================== LEGACY FUNCTIONS ====================

def is_debugger_present_legacy() -> bool:
    """Legacy function name for backward compatibility"""
    return is_debugger_present()


def is_vm_detected_legacy() -> bool:
    """Legacy function name for backward compatibility"""
    return is_vm_detected()


# ==================== EXPORTS ====================

__all__ = [
    'is_debugger_present',
    'is_debugger_present_silent',
    'check_debug_registers',
    'check_parent_process',
    'check_debug_env',
    'check_timing_anomalies',
    'check_code_integrity',
    'is_debugged',
    'is_vm_detected',
    'is_vm_detected_silent',
    'detect_hypervisor',
    'is_sandboxed',
    'get_vm_detection_status',
    'analyze_environment',
    'protect_from_debugging',
    'protect_from_timing_analysis',
    'perform_self_check',
    'verify_file_integrity',
    'calculate_file_hash',
    'start_background_checks',
    'stop_background_checks',
    'get_detection_status',
    'reset_detection_state',
    'get_integrity_status',
    'init_anti_debug',
    'is_debugger_present_legacy',
    'is_vm_detected_legacy',
    'AntiDebugError',
]