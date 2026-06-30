"""
Cross-platform wrappers, VM, comprehensive checks, protection, integrity, background.
Обёртки для всех платформ, VM, комплексные проверки.
Обгортки для всіх платформ, VM, комплексні перевірки.
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
from typing import Any, Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("antidebug")
_IS_WINDOWS = platform.system() == "Windows"
_IS_LINUX   = platform.system() == "Linux"
_IS_MACOS   = platform.system() == "Darwin"

# ── Module-level global state ─────────────────────────────────
_debug_detected: bool = False
_self_check_timer: Optional[threading.Timer] = None


class AntiDebugError(Exception):
    """Raised when a debugger or hostile environment is detected.
    Поднимается при обнаружении отладчика или враждебной среды.
    Підіймається при виявленні відлагоджувача або ворожого середовища."""
    pass


# ── Platform-specific detectors ───────────────────────────────
from security.antidebug.windows import (  # noqa: F401
    is_debugger_present_windows,
    check_debug_registers_windows,
)
from security.antidebug.unix import (  # noqa: F401
    is_debugger_present_unix,
    check_parent_process_unix,
    check_ptrace_scope,
)

# ── VM / sandbox detection (delegates to security.vm_detection) ──
try:
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
except ImportError:
    _vm_detected = False
    """
    Handle is vm detected.
    Обработать is vm detected.
    Обробити is vm detected.
    """
    """
    Return True if vm detected.
    True, если vm detected.
    True, якщо vm detected.
    """
    def _is_vm_detected() -> bool: return False
    """
    Handle is vm detected silent.
    Обработать is vm detected silent.
    Обробити is vm detected silent.
    """
    """
    Return True if vm detected silent.
    True, если vm detected silent.
    True, якщо vm detected silent.
    """
    def _is_vm_detected_silent() -> bool: return False
    """
    Handle detect hypervisor.
    Обработать detect hypervisor.
    Обробити detect hypervisor.
    """
    """
    Handle detect hypervisor.
    Обработать detect hypervisor.
    Обробити detect hypervisor.
    """
    def _detect_hypervisor() -> bool: return False
    """
    Handle check timing anomalies.
    Обработать check timing anomalies.
    Обробити check timing anomalies.
    """
    """
    Check timing anomalies.
    Проверить timing anomalies.
    Перевірити timing anomalies.
    """
    def _check_timing_anomalies() -> bool: return False
    """
    Handle is sandboxed.
    Обработать is sandboxed.
    Обробити is sandboxed.
    """
    """
    Return True if sandboxed.
    True, если sandboxed.
    True, якщо sandboxed.
    """
    def _is_sandboxed() -> "Tuple[bool, List[str]]": return False, []
    """
    Handle get vm detection status.
    Обработать get vm detection status.
    Обробити get vm detection status.
    """
    """
    Return vm detection status.
    Возвращает vm detection status.
    Повертає vm detection status.
    """
    def _get_vm_detection_status() -> "Dict[str, Any]": return {}
    """
    Handle analyze environment.
    Обработать analyze environment.
    Обробити analyze environment.
    """
    """
    Handle analyze environment.
    Обработать analyze environment.
    Обробити analyze environment.
    """
    def _analyze_environment() -> "Dict[str, Any]": return {}

# ── Integrity checks (delegates to security.integrity_check) ──
try:
    from security.integrity_check import (
        calculate_file_hash,                                           # public
        verify_file_integrity,                                         # public
        perform_self_check as _perform_self_check,
        check_code_integrity as _check_code_integrity,
        start_background_integrity_checks as _start_integrity_checks,
        stop_background_integrity_checks as _stop_integrity_checks,
        get_integrity_status as _get_integrity_status,
    )
except ImportError:
    def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> "Optional[str]":
        """Fallback: compute SHA-256 without integrity_check module."""
        import hashlib
        try:
            h = hashlib.new(algorithm)
            with open(file_path, "rb") as _f:
                for chunk in iter(lambda: _f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except (OSError, IOError, ValueError):
            return None

    def verify_file_integrity(file_path: str, expected_hash: "Optional[str]" = None) -> bool:
        """Fallback: basic file-exists check without integrity_check module."""
        return os.path.isfile(file_path)

    """
    Handle perform self check.
    Обработать perform self check.
    Обробити perform self check.
    """
    """
    Handle perform self check.
    Обработать perform self check.
    Обробити perform self check.
    """
    def _perform_self_check() -> bool: return True
    """
    Handle check code integrity.
    Обработать check code integrity.
    Обробити check code integrity.
    """
    """
    Check code integrity.
    Проверить code integrity.
    Перевірити code integrity.
    """
    def _check_code_integrity() -> bool: return True
    """
    Handle start integrity checks.
    Обработать start integrity checks.
    Обробити start integrity checks.
    """
    """
    Start integrity checks.
    Запустить integrity checks.
    Запустити integrity checks.
    """
    def _start_integrity_checks(interval: int = 30) -> None: pass
    """
    Handle stop integrity checks.
    Обработать stop integrity checks.
    Обробити stop integrity checks.
    """
    """
    Stop integrity checks.
    Остановить integrity checks.
    Зупинити integrity checks.
    """
    def _stop_integrity_checks() -> None: pass
    """
    Handle get integrity status.
    Обработать get integrity status.
    Обробити get integrity status.
    """
    """
    Return integrity status.
    Возвращает integrity status.
    Повертає integrity status.
    """
    def _get_integrity_status() -> "Dict[str, Any]": return {}

# ==================== CROSS-PLATFORM WRAPPER FUNCTIONS / ОБЁРТКИ ДЛЯ ВСЕХ ПЛАТФОРМ / ОБГОРТКИ ДЛЯ ВСІХ ПЛАТФОРМ ====================

# ── Cross-platform debugger detection ────────────────────────
# The detection functions below use OS-level APIs that are hard to
# spoof without kernel access.  However, a determined attacker with
# ring-0 access (rootkit/hypervisor) can patch them.  We use them as
# a deterrent against casual reverse-engineering, not as a security
# guarantee.  The app functions normally even when a debugger is found;
# it just logs the event for audit purposes.
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