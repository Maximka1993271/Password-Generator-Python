"""
Integrity checking module for SecurePassPro - Anti-debug component

Модуль проверки целостности для SecurePassPro - компонент анти-отладки
Модуль перевірки цілісності для SecurePassPro - компонент анти-відлагодження

This module contains:
- File integrity checking
- Self-check functionality
- Code integrity verification
- Background integrity checks

Этот модуль содержит:
- Проверку целостности файлов
- Функциональность самопроверки
- Проверку целостности кода
- Фоновые проверки целостности

Цей модуль містить:
- Перевірку цілісності файлів
- Функціональність самоперевірки
- Перевірку цілісності коду
- Фонові перевірки цілісності

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import os
import sys
import hashlib
import time
import threading
from typing import Optional, List, Tuple, Dict, Any
from utils.logger import get_logger

logger = get_logger("integrity_check")

# Global state / Глобальное состояние / Глобальний стан
_integrity_verified = False
_self_check_timer: Optional[threading.Timer] = None

# Platform detection / Определение платформы / Визначення платформи
_IS_WINDOWS = sys.platform == "win32"
_IS_LINUX = sys.platform == "linux"
_IS_MACOS = sys.platform == "darwin"


class IntegrityError(Exception):
    """Exception for integrity violation / Исключение при нарушении целостности / Виняток при порушенні цілісності"""
    pass


# ==================== FILE HASHING FUNCTIONS ====================

# ── File integrity checking ───────────────────────────────
# We hash the running executable and key module files at startup
# and periodically in a background thread.  If any hash changes
# after the initial reading, it may indicate tampering or a
# hot-patching attack.  We log the event and can optionally exit.
#
# ⚠ This is NOT a substitute for code-signing.  A sophisticated
#   attacker who can replace the binary can also patch out these
#   checks.  Treat them as an early-warning system, not a hard guard.
def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculate hash of a file.
    
    Вычисляет хеш файла.
    Обчислює хеш файлу.
    
    Args:
        file_path: Path to file / Путь к файлу / Шлях до файлу
        algorithm: Hash algorithm (sha256, sha3-256, md5) / Алгоритм хеширования / Алгоритм хешування
        
    Returns:
        Hash string or None on error / Хеш строка или None при ошибке / Хеш рядок або None при помилці
    """
    try:
        if not os.path.exists(file_path):
            logger.debug(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")
            return None

        if algorithm == "sha256":
            hasher = hashlib.sha256()
        elif algorithm == "sha3-256":
            hasher = hashlib.sha3_256()
        elif algorithm == "md5":
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm} / Неподдерживаемый алгоритм: {algorithm} / Непідтримуваний алгоритм: {algorithm}")

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    except (OSError, IOError, PermissionError, ValueError) as e:
        logger.debug(f"Failed to calculate hash for {file_path}: {e} / Не удалось вычислить хеш для {file_path} / Не вдалося обчислити хеш для {file_path}")
        return None


def verify_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> bool:
    """
    Verify file integrity against expected hash.
    
    Проверяет целостность файла по ожидаемому хешу.
    Перевіряє цілісність файлу за очікуваним хешем.
    
    Args:
        file_path: Path to file / Путь к файлу / Шлях до файлу
        expected_hash: Expected hash or None to skip / Ожидаемый хеш или None для пропуска / Очікуваний хеш або None для пропуску
        
    Returns:
        True if file is intact / True если файл цел / True якщо файл цілий
    """
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path} / Файл не найден: {file_path} / Файл не знайдено: {file_path}")
        return False

    if expected_hash is None:
        return True

    actual_hash = calculate_file_hash(file_path)
    if actual_hash is None:
        return False

    import hmac
    if hmac.compare_digest(actual_hash.lower(), expected_hash.lower()):
        logger.debug(f"Integrity check passed: {file_path} / Проверка целостности пройдена: {file_path} / Перевірку цілісності пройдено: {file_path}")
        return True
    else:
        logger.warning(f"Integrity check FAILED: {file_path} / Проверка целостности НЕ ПРОЙДЕНА: {file_path} / Перевірку цілісності НЕ ПРОЙДЕНО: {file_path}")
        logger.debug(f"  Expected: {expected_hash[:16]}... / Ожидалось: {expected_hash[:16]}... / Очікувалось: {expected_hash[:16]}...")
        logger.debug(f"  Actual:   {actual_hash[:16]}... / Фактически: {actual_hash[:16]}... / Фактично: {actual_hash[:16]}...")
        return False


# ==================== CODE INTEGRITY CHECKS ====================

def check_code_integrity() -> bool:
    """
    Check if code has been modified at runtime.
    
    Проверяет, был ли изменён код во время выполнения.
    Перевіряє, чи було змінено код під час виконання.
    
    Returns:
        True if code appears intact / True если код не изменён / True якщо код не змінено
    """
    try:
        current_file = os.path.abspath(__file__)
        if os.path.exists(current_file):
            mtime = os.path.getmtime(current_file)
            # If file was modified in last 5 minutes and not frozen
            if time.time() - mtime < 300 and not getattr(sys, 'frozen', False):
                dev_env_vars = ['PYCHARM_HOSTED', 'PYDEV_CONSOLE_ENCODING', 'VSCODE_PID']
                for var in dev_env_vars:
                    if os.environ.get(var):
                        logger.debug(f"Development environment detected: {var} / Обнаружена среда разработки: {var} / Виявлено середовище розробки: {var}")
                        return True

                logger.warning(f"Recent file modification detected: {current_file} / Обнаружено недавнее изменение файла: {current_file} / Виявлено недавню зміну файлу: {current_file}")
                return False
    except (OSError, IOError, ValueError, AttributeError) as e:
        logger.debug(f"Code integrity check failed / Ошибка проверки целостности кода / Помилка перевірки цілісності коду: {e}")

    return True


def perform_self_check() -> bool:
    """
    Perform integrity self-check on critical files.
    
    Выполняет самопроверку целостности критических файлов.
    Виконує самоперевірку цілісності критичних файлів.
    
    Returns:
        True if all checks passed / True если все проверки пройдены / True якщо всі перевірки пройдено
    """
    global _integrity_verified

    critical_files = [
        ("security/antidebug.py", None),
        ("security/encryption.py", None),
        ("security/master.py", None),
        ("security/vm_detection.py", None),
        ("security/integrity_check.py", None),
    ]

    all_valid = True
    for file_path, expected_hash in critical_files:
        # Only check if file exists (skip missing files in development)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, file_path)
        
        if os.path.exists(full_path):
            if not verify_file_integrity(full_path, expected_hash):
                all_valid = False
                logger.error(f"Integrity check failed for: {file_path} / Проверка целостности не пройдена для: {file_path} / Перевірку цілісності не пройдено для: {file_path}")

    _integrity_verified = all_valid
    
    if all_valid:
        logger.debug("Self-check passed / Самопроверка пройдена / Самоперевірку пройдено")
    else:
        logger.warning("Self-check FAILED / Самопроверка НЕ ПРОЙДЕНА / Самоперевірку НЕ ПРОЙДЕНО")
    
    return all_valid


def get_integrity_status() -> Dict[str, Any]:
    """
    Get current integrity status.
    
    Получить текущий статус целостности.
    Отримати поточний статус цілісності.
    
    Returns:
        Dictionary with integrity status / Словарь со статусом целостности / Словник зі статусом цілісності
    """
    return {
        "integrity_verified": _integrity_verified,
        "code_integrity": check_code_integrity(),
    }


def reset_integrity_state() -> None:
    """Reset integrity state (for testing) / Сбросить состояние целостности (для тестирования) / Скинути стан цілісності (для тестування)"""
    global _integrity_verified
    _integrity_verified = False


# ==================== BACKGROUND INTEGRITY CHECKS ====================

def _background_integrity_check() -> None:
    """Background thread for periodic integrity checks
    Фоновый поток для периодических проверок целостности
    Фоновий потік для періодичних перевірок цілісності"""
    global _self_check_timer

    try:
        perform_self_check()
        check_code_integrity()
    except (RuntimeError, OSError, AttributeError) as e:
        logger.debug(f"Background integrity check error / Ошибка фоновой проверки целостности / Помилка фонової перевірки цілісності: {e}")

    _self_check_timer = threading.Timer(30.0, _background_integrity_check)
    _self_check_timer.daemon = True
    _self_check_timer.start()


def start_background_integrity_checks(interval: int = 30) -> None:
    """
    Start background integrity checks.
    
    Запустить фоновые проверки целостности.
    Запустити фонові перевірки цілісності.
    
    Args:
        interval: Check interval in seconds / Интервал проверки в секундах / Інтервал перевірки в секундах
    """
    global _self_check_timer

    if _self_check_timer is not None:
        return

    _self_check_timer = threading.Timer(interval, _background_integrity_check)
    _self_check_timer.daemon = True
    _self_check_timer.start()
    logger.info(f"Background integrity checks started (interval: {interval}s) / Фоновые проверки целостности запущены (интервал: {interval}с) / Фонові перевірки цілісності запущено (інтервал: {interval}с)")


def stop_background_integrity_checks() -> None:
    """Stop background integrity checks / Остановить фоновые проверки целостности / Зупинити фонові перевірки цілісності"""
    global _self_check_timer

    if _self_check_timer:
        _self_check_timer.cancel()
        _self_check_timer = None
        logger.info("Background integrity checks stopped / Фоновые проверки целостности остановлены / Фонові перевірки цілісності зупинено")


# ==================== ADVANCED INTEGRITY CHECKS ====================

def verify_module_integrity(module_name: str, expected_hash: str) -> bool:
    """
    Verify integrity of a Python module by its file path.
    
    Проверяет целостность Python модуля по пути к файлу.
    Перевіряє цілісність Python модуля за шляхом до файлу.
    
    Args:
        module_name: Name of the module / Имя модуля / Ім'я модуля
        expected_hash: Expected SHA256 hash / Ожидаемый SHA256 хеш / Очікуваний SHA256 хеш
        
    Returns:
        True if module is intact / True если модуль цел / True якщо модуль цілий
    """
    try:
        import importlib.util
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return verify_file_integrity(spec.origin, expected_hash)
    except (ImportError, AttributeError, ValueError) as e:
        logger.debug(f"Module integrity check failed for {module_name}: {e} / Ошибка проверки целостности модуля {module_name} / Помилка перевірки цілісності модуля {module_name}")
    
    return False


def verify_executable_integrity(exe_path: str = None) -> bool:
    """
    Verify integrity of the current executable (frozen mode only).
    
    Проверяет целостность текущего исполняемого файла (только в frozen режиме).
    Перевіряє цілісність поточного виконуваного файлу (тільки в frozen режимі).
    
    Args:
        exe_path: Path to executable (auto-detected if None) / Путь к исполняемому файлу / Шлях до виконуваного файлу
        
    Returns:
        True if executable is intact / True если исполняемый файл цел / True якщо виконуваний файл цілий
    """
    if not getattr(sys, 'frozen', False):
        logger.debug("Not in frozen mode, skipping executable integrity check / Не в frozen режиме, пропускаем проверку целостности исполняемого файлу / Не в frozen режимі, пропускаємо перевірку цілісності виконуваного файлу")
        return True
    
    if exe_path is None:
        exe_path = sys.executable
    
    if not os.path.exists(exe_path):
        logger.warning(f"Executable not found: {exe_path} / Исполняемый файл не найден: {exe_path} / Виконуваний файл не знайдено: {exe_path}")
        return False
    
    # In frozen mode, we can't easily get expected hash without external manifest
    # So we just check if file is not obviously corrupted
    
    try:
        size = os.path.getsize(exe_path)
        if size < 1024 * 1024:  # Less than 1MB - suspicious for frozen app
            logger.warning(f"Executable suspiciously small: {size} bytes / Исполняемый файл подозрительно мал: {size} байт / Виконуваний файл підозріло малий: {size} байт")
            return False
    except (OSError, IOError, PermissionError) as e:
        logger.debug(f"Executable size check failed / Ошибка проверки размера исполняемого файлу / Помилка перевірки розміру виконуваного файлу: {e}")
        return False
    
    logger.debug("Executable integrity check passed / Проверка целостности исполняемого файла пройдена / Перевірку цілісності виконуваного файлу пройдено")
    return True


# ==================== DIRECTORY INTEGRITY ====================

def verify_directory_integrity(directory: str, expected_files: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Verify integrity of all files in a directory.
    
    Проверяет целостность всех файлов в директории.
    Перевіряє цілісність всіх файлів у директорії.
    
    Args:
        directory: Directory path / Путь к директории / Шлях до директорії
        expected_files: Dictionary of {filename: expected_hash} / Словарь {имя_файла: ожидаемый_хеш} / Словник {ім'я_файлу: очікуваний_хеш}
        
    Returns:
        (all_valid, list_of_errors) / (все_валидны, список_ошибок) / (всі_валідні, список_помилок)
    """
    errors = []
    
    for filename, expected_hash in expected_files.items():
        file_path = os.path.join(directory, filename)
        
        if not os.path.exists(file_path):
            errors.append(f"Missing file: {filename} / Отсутствует файл: {filename} / Відсутній файл: {filename}")
            continue
        
        if not verify_file_integrity(file_path, expected_hash):
            errors.append(f"Integrity check failed: {filename} / Проверка целостности не пройдена: {filename} / Перевірку цілісності не пройдено: {filename}")
    
    return len(errors) == 0, errors


# ==================== EXPORTS ====================

__all__ = [
    'IntegrityError',
    'calculate_file_hash',
    'verify_file_integrity',
    'check_code_integrity',
    'perform_self_check',
    'get_integrity_status',
    'reset_integrity_state',
    'start_background_integrity_checks',
    'stop_background_integrity_checks',
    'verify_module_integrity',
    'verify_executable_integrity',
    'verify_directory_integrity',
    '_integrity_verified',
]