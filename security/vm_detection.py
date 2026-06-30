"""
VM (Virtual Machine) and Sandbox detection for SecurePassPro

Обнаружение виртуальных машин (VM) и песочниц для SecurePassPro
Виявлення віртуальних машин (VM) та пісочниць для SecurePassPro

This module contains:
- VM detection (VMware, VirtualBox, Hyper-V, QEMU, etc.)
- Sandbox detection (Cuckoo, Sandboxie, etc.)
- Timing analysis for VM detection
- Hypervisor detection
- Environment analysis

Этот модуль содержит:
- Обнаружение VM (VMware, VirtualBox, Hyper-V, QEMU и др.)
- Обнаружение песочниц (Cuckoo, Sandboxie и др.)
- Анализ времени для обнаружения VM
- Обнаружение гипервизора
- Анализ окружения

Цей модуль містить:
- Виявлення VM (VMware, VirtualBox, Hyper-V, QEMU та ін.)
- Виявлення пісочниць (Cuckoo, Sandboxie та ін.)
- Аналіз часу для виявлення VM
- Виявлення гіпервізора
- Аналіз середовища

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import os
import sys
import platform
import subprocess
import time
import hashlib
import uuid
import shutil
from typing import Tuple, List, Optional, Dict, Any
from utils.logger import get_logger

# ==================== DEV MODE BYPASS ====================
# Set SECUREPASS_DEV_MODE=1 to disable VM/sandbox detection in CI/WSL2/dev environments
# Установите SECUREPASS_DEV_MODE=1 для отключения обнаружения VM в CI/WSL2/dev-окружении
# Встановіть SECUREPASS_DEV_MODE=1 для вимкнення виявлення VM в CI/WSL2/dev-середовищі
import os as _os_dev
_DEV_MODE = _os_dev.environ.get("SECUREPASS_DEV_MODE", "0").strip() in ("1", "true", "yes", "on")
if _DEV_MODE:
    import logging as _log_dev
    _log_dev.getLogger("vm_detection").info(
        "DEV MODE active — VM/sandbox detection DISABLED "
        "(SECUREPASS_DEV_MODE=1) / DEV MODE активен / DEV MODE активний"
    )



logger = get_logger("vm_detection")

# Global state / Глобальное состояние / Глобальний стан
_vm_detected = False
_sandbox_detected = False

# Platform detection / Определение платформы / Визначення платформи
_IS_WINDOWS = platform.system() == "Windows"
_IS_LINUX = platform.system() == "Linux"
_IS_MACOS = platform.system() == "Darwin"


# ==================== VM DETECTION (CROSS-PLATFORM) ====================

def is_vm_detected() -> bool:
    """Basic VM detection (VMware, VirtualBox, Hyper-V) - cross-platform
    Базовое обнаружение VM (VMware, VirtualBox, Hyper-V) - кросс-платформенно
    Базове виявлення VM (VMware, VirtualBox, Hyper-V) - кросплатформено"""
    if _DEV_MODE: return False

    global _vm_detected

    if _vm_detected:
        return True

    vm_indicators = [
        "vbox", "vmware", "virtual", "hyper-v",
        "qemu", "bochs", "parallels", "xen",
        "kvm", "virtualbox", "oracle"
    ]

    # BIOS detection (Windows)
    if _IS_WINDOWS:
        try:
            result = subprocess.run(
                ["wmic", "bios", "get", "serialnumber"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bios = result.stdout.lower()
                for indicator in vm_indicators:
                    if indicator in bios:
                        logger.warning(f"VM detected via BIOS: {indicator} / VM обнаружена через BIOS: {indicator} / VM виявлено через BIOS: {indicator}")
                        _vm_detected = True
                        return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            logger.debug(f"BIOS VM detection failed / Ошибка обнаружения VM через BIOS / Помилка виявлення VM через BIOS: {e}")

    # MAC address detection (all platforms)
    try:
        mac = uuid.getnode()
        mac_str = format(mac, '012x')
        vm_macs = ['000569', '000c29', '001c42', '005056', '080027', '525400', '00ffaa']
        for vm_mac in vm_macs:
            if mac_str.startswith(vm_mac):
                logger.warning(f"VM detected via MAC: {vm_mac} / VM обнаружена через MAC: {vm_mac} / VM виявлено через MAC: {vm_mac}")
                _vm_detected = True
                return True
    except (ValueError, TypeError, AttributeError, OSError) as e:
        logger.debug(f"MAC VM detection failed / Ошибка обнаружения VM через MAC / Помилка виявлення VM через MAC: {e}")

    # DMI detection (Linux)
    if _IS_LINUX:
        try:
            result = subprocess.run(
                ['dmidecode', '-s', 'system-manufacturer'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                manufacturer = result.stdout.lower()
                for indicator in vm_indicators:
                    if indicator in manufacturer:
                        logger.warning(f"VM detected via DMI: {indicator} / VM обнаружена через DMI: {indicator} / VM виявлено через DMI: {indicator}")
                        _vm_detected = True
                        return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass

    # CPU count check
    try:
        cpu_count = os.cpu_count() or 0
        if cpu_count <= 1:
            logger.warning(f"VM detected via CPU count: {cpu_count} / VM обнаружена по количеству CPU: {cpu_count} / VM виявлено за кількістю CPU: {cpu_count}")
            _vm_detected = True
            return True
    except (ValueError, TypeError) as e:
        logger.debug(f"CPU count detection failed / Ошибка определения количества CPU / Помилка визначення кількості CPU: {e}")

    # Memory check
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.total < 2 * 1024 * 1024 * 1024:
            logger.warning(f"VM detected via low memory: {mem.total / (1024**3):.1f} GB / VM обнаружена по малому объёму памяти: {mem.total / (1024**3):.1f} ГБ / VM виявлено за малим обсягом пам'яті: {mem.total / (1024**3):.1f} ГБ")
            _vm_detected = True
            return True
    except ImportError:
        pass
    except (ValueError, AttributeError, OSError) as e:
        logger.debug(f"RAM detection failed / Ошибка определения ОЗУ / Помилка визначення ОЗУ: {e}")

    # Disk size check
    try:
        total, used, free = shutil.disk_usage("/")
        if total < 50 * 1024 * 1024 * 1024:
            logger.warning(f"VM detected via small disk: {total / (1024**3):.1f} GB / VM обнаружена по малому диску: {total / (1024**3):.1f} ГБ / VM виявлено за малим диском: {total / (1024**3):.1f} ГБ")
            _vm_detected = True
            return True
    except (OSError, ValueError, AttributeError) as e:
        logger.debug(f"Disk size detection failed / Ошибка определения размера диска / Помилка визначення розміру диска: {e}")

    # VM-specific files
    vm_files = [
        "C:\\Program Files\\VMware\\VMware Tools\\",
        "C:\\Program Files\\Oracle\\VirtualBox Guest Additions\\",
        "/usr/bin/VBoxClient",
        "/usr/bin/vmtoolsd"
    ]
    for vm_file in vm_files:
        try:
            if os.path.exists(vm_file):
                logger.warning(f"VM detected via file: {vm_file} / VM обнаружена по файлу: {vm_file} / VM виявлено за файлом: {vm_file}")
                _vm_detected = True
                return True
        except (OSError, IOError, PermissionError) as e:
            pass

    return False


def is_vm_detected_silent() -> bool:
    """Silent version of VM detection (no logging)
    Тихая версия обнаружения VM (без логирования)
    Тиха версія виявлення VM (без логування)"""
    if _DEV_MODE: return False

    vm_indicators = ["vbox", "vmware", "virtual", "hyper-v", "qemu", "bochs", "parallels", "xen"]

    try:
        if _IS_WINDOWS:
            result = subprocess.run(
                ["wmic", "bios", "get", "serialnumber"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                bios = result.stdout.lower()
                for indicator in vm_indicators:
                    if indicator in bios:
                        return True
    except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
        pass

    try:
        mac = uuid.getnode()
        mac_str = format(mac, '012x')
        vm_macs = ['000569', '000c29', '001c42', '005056', '080027']
        for vm_mac in vm_macs:
            if mac_str.startswith(vm_mac):
                return True
    except (ValueError, TypeError, AttributeError, OSError) as e:
        pass

    return False


def detect_hypervisor() -> bool:
    """Detect hypervisor presence / Обнаружение наличия гипервизора / Виявлення наявності гіпервізора"""
    if _DEV_MODE: return False

    try:
        if _IS_WINDOWS:
            result = subprocess.run(
                ["systeminfo"],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.lower() if result.returncode == 0 else ""
            if "hypervisor" in output or "hyper-v" in output:
                logger.warning("Hyper-V detected / Hyper-V обнаружен / Hyper-V виявлено")
                return True
        elif _IS_LINUX:
            result = subprocess.run(
                ['systemd-detect-virt'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip() not in ['none', '']:
                logger.warning(f"Hypervisor detected: {result.stdout.strip()} / Гипервизор обнаружен: {result.stdout.strip()} / Гіпервізор виявлено: {result.stdout.strip()}")
                return True
    except (subprocess.SubprocessError, TimeoutError, OSError) as e:
        logger.debug(f"Hypervisor detection failed / Ошибка обнаружения гипервизора / Помилка виявлення гіпервізора: {e}")

    return False


# ==================== TIMING ANALYSIS FOR VM DETECTION ====================

def check_timing_anomalies() -> bool:
    """Check for timing anomalies (VM detection)
    Проверка аномалий времени (обнаружение VM)
    Перевірка аномалій часу (виявлення VM)"""
    if _DEV_MODE: return False

    try:
        import timeit

        def rdtsc():
            if _IS_WINDOWS:
                try:
                    import ctypes
                    class PerformanceCounter(ctypes.Structure):
                        _fields_ = [("low", ctypes.c_ulong), ("high", ctypes.c_ulong)]

                    kernel32 = ctypes.windll.kernel32
                    counter = PerformanceCounter()
                    kernel32.QueryPerformanceCounter(ctypes.byref(counter))
                    return (counter.high << 32) | counter.low
                except (AttributeError, OSError, TypeError) as e:
                    pass
            return int(time.time() * 1000000)

        measurements = []
        for _ in range(10):
            start = rdtsc()
            _ = sum(range(100))
            end = rdtsc()
            measurements.append(end - start)

        if measurements:
            variance = max(measurements) - min(measurements)
            if variance > 10000:
                logger.warning(f"High timing variance detected: {variance} / Обнаружена высокая временная дисперсия: {variance} / Виявлено високу часову дисперсію: {variance}")
                return True

    except (ImportError, AttributeError, RuntimeError, OSError) as e:
        logger.debug(f"Timing anomaly check failed / Ошибка проверки временных аномалий / Помилка перевірки часових аномалій: {e}")

    return False


# ==================== SANDBOX DETECTION (CROSS-PLATFORM) ====================

def is_sandboxed() -> Tuple[bool, List[str]]:
    """Detect sandbox/VM environment / Обнаружение песочницы/VM / Виявлення пісочниці/VM"""
    if _DEV_MODE: return False, []

    global _sandbox_detected
    indicators = []

    # Disk size check
    try:
        total, used, free = shutil.disk_usage("/")
        if total < 50 * 1024 * 1024 * 1024:
            indicators.append("small_disk")
    except (OSError, ValueError, AttributeError) as e:
        logger.debug(f"Disk check failed / Ошибка проверки диска / Помилка перевірки диска: {e}")

    # Memory check
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.total < 2 * 1024 * 1024 * 1024:
            indicators.append("low_memory")
    except ImportError:
        pass
    except (ValueError, AttributeError, OSError) as e:
        logger.debug(f"Memory check failed / Ошибка проверки памяти / Помилка перевірки пам'яті: {e}")

    # CPU count check
    try:
        cpu_count = os.cpu_count() or 0
        if cpu_count <= 2:
            indicators.append("low_cpu_count")
    except (ValueError, TypeError) as e:
        logger.debug(f"CPU count check failed / Ошибка проверки количества CPU / Помилка перевірки кількості CPU: {e}")

    # Sandbox processes
    try:
        sandbox_processes = ['sandboxie', 'cuckoo', 'vmsrvc', 'vboxservice', 'vmtoolsd']
        if _IS_WINDOWS:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq *'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for proc in sandbox_processes:
                    if proc.lower() in result.stdout.lower():
                        indicators.append(f"sandbox_process_{proc}")
                        break
        elif _IS_LINUX:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for proc in sandbox_processes:
                    if proc.lower() in result.stdout.lower():
                        indicators.append(f"sandbox_process_{proc}")
                        break
    except (subprocess.SubprocessError, TimeoutError, OSError) as e:
        logger.debug(f"Process check failed / Ошибка проверки процессов / Помилка перевірки процесів: {e}")

    # Sandbox environment variables
    try:
        sandbox_env_vars = ['CUCKOO', 'SANDBOX', 'ANALYSIS', 'VIRUS_SHARE_API_KEY']
        for var in sandbox_env_vars:
            if os.environ.get(var):
                indicators.append(f"sandbox_env_{var}")
    except (KeyError, TypeError) as e:
        logger.debug(f"Sandbox env check failed / Ошибка проверки переменных окружения песочницы / Помилка перевірки змінних середовища пісочниці: {e}")

    # Sandbox usernames
    try:
        import getpass
        username = getpass.getuser().lower()
        sandbox_users = ['sandbox', 'malware', 'analysis', 'cuckoo', 'vmware']
        for user in sandbox_users:
            if user in username:
                indicators.append(f"sandbox_username_{user}")
    except (ImportError, OSError, AttributeError) as e:
        logger.debug(f"Username check failed / Ошибка проверки имени пользователя / Помилка перевірки імені користувача: {e}")

    if len(indicators) >= 2:
        _sandbox_detected = True
        logger.warning(f"Sandbox detected: {indicators} / Песочница обнаружена: {indicators} / Пісочницю виявлено: {indicators}")

    return len(indicators) >= 2, indicators


def is_sandboxed_silent() -> bool:
    """Silent version of sandbox detection (no logging)
    Тихая версия обнаружения песочницы (без логирования)
    Тиха версія виявлення пісочниці (без логування)"""
    indicators = 0

    try:
        total, used, free = shutil.disk_usage("/")
        if total < 50 * 1024 * 1024 * 1024:
            indicators += 1
    except (OSError, ValueError, AttributeError) as e:
        pass

    try:
        cpu_count = os.cpu_count() or 0
        if cpu_count <= 2:
            indicators += 1
    except (ValueError, TypeError) as e:
        pass

    return indicators >= 2


# ==================== ENVIRONMENT ANALYSIS ====================

def analyze_environment() -> Dict[str, Any]:
    """
    Perform comprehensive environment analysis.
    
    Выполняет комплексный анализ окружения.
    Виконує комплексний аналіз середовища.
    
    Returns:
        Dictionary with analysis results / Словарь с результатами анализа / Словник з результатами аналізу
    """
    results = {
        "is_vm": is_vm_detected(),
        "is_sandboxed": False,
        "sandbox_reasons": [],
        "hypervisor_detected": detect_hypervisor(),
        "timing_anomaly": check_timing_anomalies(),
        "cpu_count": os.cpu_count() or 0,
        "platform": platform.system(),
        "machine": platform.machine(),
    }
    
    sandboxed, reasons = is_sandboxed()
    results["is_sandboxed"] = sandboxed
    results["sandbox_reasons"] = reasons
    
    return results


def get_vm_detection_status() -> Dict[str, Any]:
    """
    Get VM and sandbox detection status.
    
    Получить статус обнаружения VM и песочницы.
    Отримати статус виявлення VM та пісочниці.
    """
    return {
        "vm_detected": _vm_detected,
        "sandbox_detected": _sandbox_detected,
        "hypervisor": detect_hypervisor(),
        "timing_anomaly": check_timing_anomalies(),
    }


# ==================== VM-SPECIFIC CHECKS ====================

def is_vmware() -> bool:
    """Check if running on VMware / Проверяет, запущено ли на VMware / Перевіряє, чи запущено на VMware"""
    if _IS_WINDOWS:
        try:
            result = subprocess.run(
                ["wmic", "bios", "get", "serialnumber"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bios = result.stdout.lower()
                if "vmware" in bios:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass
    elif _IS_LINUX:
        try:
            result = subprocess.run(
                ['dmidecode', '-s', 'system-manufacturer'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                manufacturer = result.stdout.lower()
                if "vmware" in manufacturer:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass
    return False


def is_virtualbox() -> bool:
    """Check if running on VirtualBox / Проверяет, запущено ли на VirtualBox / Перевіряє, чи запущено на VirtualBox"""
    if _IS_WINDOWS:
        try:
            result = subprocess.run(
                ["wmic", "bios", "get", "serialnumber"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                bios = result.stdout.lower()
                if "vbox" in bios or "virtualbox" in bios:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass
    elif _IS_LINUX:
        try:
            result = subprocess.run(
                ['systemd-detect-virt'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                virt = result.stdout.lower()
                if "oracle" in virt or "vbox" in virt:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass
    return False


def is_hyperv() -> bool:
    """Check if running on Hyper-V / Проверяет, запущено ли на Hyper-V / Перевіряє, чи запущено на Hyper-V"""
    if not _IS_WINDOWS:
        return False
    
    try:
        result = subprocess.run(
            ["systeminfo"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower() if result.returncode == 0 else ""
        if "hyper-v" in output or "hypervisor" in output:
            return True
    except (subprocess.SubprocessError, TimeoutError, OSError) as e:
        pass
    return False


def is_qemu() -> bool:
    """Check if running on QEMU / Проверяет, запущено ли на QEMU / Перевіряє, чи запущено на QEMU"""
    if _IS_LINUX:
        try:
            result = subprocess.run(
                ['systemd-detect-virt'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                virt = result.stdout.lower()
                if "qemu" in virt:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, OSError) as e:
            pass
    return False


# ==================== RESET FUNCTIONS ====================

def reset_vm_detection_state() -> None:
    """Reset VM detection state (for testing) / Сбросить состояние обнаружения VM (для тестирования) / Скинути стан виявлення VM (для тестування)"""
    global _vm_detected, _sandbox_detected
    _vm_detected = False
    _sandbox_detected = False


# ==================== EXPORTS ====================

__all__ = [
    'is_vm_detected',
    'is_vm_detected_silent',
    'detect_hypervisor',
    'check_timing_anomalies',
    'is_sandboxed',
    'is_sandboxed_silent',
    'analyze_environment',
    'get_vm_detection_status',
    'is_vmware',
    'is_virtualbox',
    'is_hyperv',
    'is_qemu',
    'reset_vm_detection_state',
    '_vm_detected',
    '_sandbox_detected',
]


def is_dev_mode() -> bool:
    """Check if dev mode is active / Проверить активен ли dev-режим"""
    return _DEV_MODE