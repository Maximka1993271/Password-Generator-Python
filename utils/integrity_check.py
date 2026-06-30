"""
Program integrity checker for SecurePassPro
Performs integrity verification at startup and runtime

FIXED: Removed auto-repair on missing integrity file - now fails closed
FIXED: Added thread safety with threading.RLock
FIXED: Added secure mode flag for production environments

Проверка целостности программы для SecurePassPro
Выполняет проверку целостности при запуске и во время работы
FIXED: Убран авторемонт при отсутствии файла целостности - теперь fail-closed
FIXED: Добавлена потокобезопасность с threading.RLock
FIXED: Добавлен флаг безопасного режима для production окружений

Перевірка цілісності програми для SecurePassPro
Виконує перевірку цілісності при запуску та під час роботи
FIXED: Прибрано авторемонт при відсутності файлу цілісності - тепер fail-closed
FIXED: Додано потокобезпечність з threading.RLock
FIXED: Додано прапорець безпечного режиму для production середовищ
"""
from __future__ import annotations
import os
import sys
import hashlib
import json
import platform
import threading
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from utils.logger import get_logger
from utils.paths import get_base_dir, get_config_dir

logger = get_logger("integrity_check")

# Integrity file with hashes / Файл с хешами для проверки / Файл з хешами для перевірки
INTEGRITY_FILE = os.path.join(get_base_dir(), "integrity.json")
BACKUP_INTEGRITY_FILE = os.path.join(get_config_dir(), "integrity_backup.json")

# SECURITY MODE: If True, missing integrity file is treated as FAILURE
# БЕЗОПАСНЫЙ РЕЖИМ: Если True, отсутствие файла целостности считается ОШИБКОЙ
# БЕЗПЕЧНИЙ РЕЖИМ: Якщо True, відсутність файлу цілісності вважається ПОМИЛКОЮ
# FIXED #20: Set to True for production - fail closed on missing integrity file
# Исправлено #20: Установлен в True для production - fail closed при отсутствии файла целостности
# Виправлено #20: Встановлено в True для production - fail closed при відсутності файлу цілісності
SECURE_MODE = True

# Critical files to check (relative to project root)
# Критические файлы для проверки (относительно корня проекта)
# Критичні файли для перевірки (відносно кореня проекту)
CRITICAL_FILES = [
    ("main.py", True),
    ("__main__.py", False),
    ("core/generator.py", True),
    ("core/__init__.py", True),
    ("security/master.py", True),
    ("security/encryption.py", True),
    ("security/__init__.py", True),
    ("storage/database.py", True),
    ("storage/config.py", True),
    ("gui/main_window.py", True),
    ("gui/__init__.py", True),
    ("utils/secure_memory.py", True),
    ("utils/logger.py", True),
    ("utils/paths.py", True),
]


class IntegrityChecker:
    """Program file integrity checker
    Проверка целостности файлов программы
    Перевірка цілісності файлів програми"""

    _instance = None
    _lock = threading.RLock()  # FIXED #22: Thread safety
    _hashes: Dict[str, str] = {}
    _verified = False
    _secure_mode = SECURE_MODE

    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def set_secure_mode(cls, enabled: bool) -> None:
        """
        Set secure mode. When enabled, missing integrity file causes verification to fail.

        Установить безопасный режим. При включении отсутствие файла целостности вызывает ошибку.
        Встановити безпечний режим. При ввімкненні відсутність файлу цілісності викликає помилку.
        """
        with cls._lock:
            cls._secure_mode = enabled
            logger.info(f"Secure mode set to: {enabled} / Безопасный режим установлен: {enabled} / Безпечний режим встановлено: {enabled}")

    @classmethod
    def _get_file_hash(cls, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of a file
        Вычисляет SHA-256 хеш файла
        Обчислює SHA-256 хеш файлу"""
        if not os.path.exists(file_path):
            return None

        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to hash {file_path}: {e} / Не удалось вычислить хеш {file_path} / Не вдалося обчислити хеш {file_path}")
            return None
        except (ValueError, TypeError) as e:
            logger.error(f"Hash computation error for {file_path}: {e} / Ошибка вычисления хеша для {file_path} / Помилка обчислення хеша для {file_path}")
            return None

    @classmethod
    def _get_absolute_path(cls, rel_path: str) -> str:
        """Get absolute path relative to project root
        Получает абсолютный путь относительно корня проекта
        Отримує абсолютний шлях відносно кореня проекту"""
        base_dir = get_base_dir()
        return os.path.join(base_dir, rel_path.replace('/', os.sep))

    @classmethod
    def generate_integrity_file(cls, force: bool = False) -> bool:
        """
        Generate file with hashes of all critical files.
        In secure mode, this requires explicit force=True.

        Генерирует файл с хешами всех критических файлов.
        В безопасном режиме требует явного force=True.

        Генерує файл з хешами всіх критичних файлів.
        У безпечному режимі вимагає явного force=True.
        """
        # FIXED #20: In secure mode, require force=True for generation
        # Исправлено #20: В безопасном режиме требуем force=True для генерации
        # Виправлено #20: У безпечному режимі вимагаємо force=True для генерації
        if cls._secure_mode and not force:
            logger.error("Cannot generate integrity file in secure mode without force=True / Нельзя генерировать файл целостности в безопасном режиме без force=True / Не можна генерувати файл цілісності у безпечному режимі без force=True")
            return False

        hashes = {}

        for file_path, required in CRITICAL_FILES:
            abs_path = cls._get_absolute_path(file_path)
            file_hash = cls._get_file_hash(abs_path)

            if file_hash:
                hashes[file_path] = file_hash
                logger.debug(f"Hash for {file_path}: {file_hash[:16]}... / Хеш для {file_path}: {file_hash[:16]}... / Хеш для {file_path}: {file_hash[:16]}...")
            elif required:
                logger.error(f"Required file not found: {file_path} / Обязательный файл не найден: {file_path} / Обов'язковий файл не знайдено: {file_path}")
                return False

        try:
            integrity_data = {
                "generated": datetime.now().isoformat(),
                "platform": platform.platform(),
                "python_version": sys.version,
                "files": hashes
            }

            with open(INTEGRITY_FILE, 'w', encoding='utf-8') as f:
                json.dump(integrity_data, f, indent=2, ensure_ascii=False)

            # Create backup / Создаём резервную копию / Створюємо резервну копію
            with open(BACKUP_INTEGRITY_FILE, 'w', encoding='utf-8') as f:
                json.dump(integrity_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Integrity file generated: {INTEGRITY_FILE} / Файл целостности сгенерирован: {INTEGRITY_FILE} / Файл цілісності згенеровано: {INTEGRITY_FILE}")
            return True

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to generate integrity file / Ошибка генерации файла целостности / Помилка генерації файлу цілісності: {e}")
            return False
        except TypeError as e:
            logger.error(f"JSON serialization error / Ошибка сериализации JSON / Помилка серіалізації JSON: {e}")
            return False

    @classmethod
    def _load_integrity_data(cls) -> Optional[Dict]:
        """Load integrity data from file / Загружает данные целостности из файла / Завантажує дані цілісності з файлу"""
        # Try main file / Пробуем основной файл / Пробуємо основний файл
        if os.path.exists(INTEGRITY_FILE):
            try:
                with open(INTEGRITY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse integrity file / Ошибка парсинга файла целостности / Помилка парсингу файлу цілісності: {e}")
            except (OSError, IOError, PermissionError) as e:
                logger.warning(f"Failed to load integrity file / Ошибка загрузки файла целостности / Помилка завантаження файлу цілісності: {e}")

        # Try backup file / Пробуем резервный файл / Пробуємо резервний файл
        if os.path.exists(BACKUP_INTEGRITY_FILE):
            try:
                with open(BACKUP_INTEGRITY_FILE, 'r', encoding='utf-8') as f:
                    logger.info("Using backup integrity file / Используется резервный файл целостности / Використовується резервний файл цілісності")
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse backup integrity file / Ошибка парсинга резервного файла целостности / Помилка парсингу резервного файлу цілісності: {e}")
            except (OSError, IOError, PermissionError) as e:
                logger.warning(f"Failed to load backup integrity file / Ошибка загрузки резервного файла целостности / Помилка завантаження резервного файлу цілісності: {e}")

        return None

    @classmethod
    def verify_integrity(cls, auto_repair: bool = False) -> Tuple[bool, List[str]]:
        """
        Verify program integrity.
        FIXED #20: auto_repair is now False by default and ignored in secure mode.

        Проверяет целостность программы.
        Исправлено #20: auto_repair теперь False по умолчанию и игнорируется в безопасном режиме.

        Перевіряє цілісність програми.
        Виправлено #20: auto_repair тепер False за замовчуванням і ігнорується в безпечному режимі.

        Args:
            auto_repair: DEPRECATED - ignored in secure mode. Use generate_integrity_file(force=True)
                         УСТАРЕЛО - игнорируется в безопасном режиме
                         ЗАСТАРІЛО - ігнорується в безпечному режимі

        Returns:
            (is_valid, list_of_errors) - status and list of errors
            (is_valid, list_of_errors) - статус и список ошибок
            (is_valid, list_of_errors) - статус та список помилок
        """
        with cls._lock:  # FIXED #22: Thread safety
            errors = []

            # Load saved hashes / Загружаем сохранённые хеши / Завантажуємо збережені хеші
            integrity_data = cls._load_integrity_data()

            # FIXED #20: In secure mode, missing integrity file is an ERROR
            # Исправлено #20: В безопасном режиме отсутствие файла целостности - ОШИБКА
            # Виправлено #20: У безпечному режимі відсутність файлу цілісності - ПОМИЛКА
            if not integrity_data:
                if cls._secure_mode:
                    errors.append("Integrity file not found and secure mode is enabled / Файл целостности не найден и включен безопасный режим / Файл цілісності не знайдено та увімкнено безпечний режим")
                    logger.critical("INTEGRITY CHECK FAILED: No integrity file found in secure mode! / ПРОВЕРКА ЦЕЛОСТНОСТИ НЕ ПРОЙДЕНА: Файл целостности не найден в безопасном режиме! / ПЕРЕВІРКУ ЦІЛІСНОСТІ НЕ ПРОЙДЕНО: Файл цілісності не знайдено у безпечному режимі!")
                    return False, errors
                else:
                    # In non-secure mode, generate new file (but this is discouraged)
                    # В небезопасном режиме генерируем новый файл (но это не рекомендуется)
                    # У небезпечному режимі генеруємо новий файл (але це не рекомендується)
                    logger.warning("Integrity file missing in non-secure mode, generating... / Файл целостности отсутствует в небезопасном режиме, генерируем... / Файл цілісності відсутній у небезпечному режимі, генеруємо...")
                    if cls.generate_integrity_file(force=True):
                        integrity_data = cls._load_integrity_data()
                    else:
                        errors.append("Failed to generate integrity file / Ошибка генерации файла целостности / Помилка генерації файлу цілісності")
                        return False, errors

            saved_hashes = integrity_data.get("files", {})
            if not isinstance(saved_hashes, dict):
                errors.append("Invalid integrity file format / Неверный формат файла целостности / Невірний формат файлу цілісності")
                return False, errors

            # Check each file / Проверяем каждый файл / Перевіряємо кожен файл
            for file_path, required in CRITICAL_FILES:
                abs_path = cls._get_absolute_path(file_path)
                current_hash = cls._get_file_hash(abs_path)
                expected_hash = saved_hashes.get(file_path)

                if current_hash is None:
                    if required:
                        errors.append(f"Missing required file: {file_path} / Отсутствует обязательный файл: {file_path} / Відсутній обов'язковий файл: {file_path}")
                    continue

                if expected_hash is None:
                    errors.append(f"New file not in integrity database: {file_path} / Новый файл отсутствует в базе целостности: {file_path} / Новий файл відсутній у базі цілісності: {file_path}")
                    continue

                if current_hash != expected_hash:
                    errors.append(f"File modified: {file_path} / Файл изменён: {file_path} / Файл змінено: {file_path}")
                    logger.warning(f"Hash mismatch for {file_path} / Несоответствие хеша для {file_path} / Невідповідність хеша для {file_path}")

            if errors:
                logger.warning(f"Integrity check failed with {len(errors)} errors / Проверка целостности не пройдена с {len(errors)} ошибками / Перевірку цілісності не пройдено з {len(errors)} помилками")
                for error in errors[:5]:  # Log first 5 errors / Логируем первые 5 ошибок / Логуємо перші 5 помилок
                    logger.debug(f"  - {error}")
            else:
                logger.info("Integrity check passed / Проверка целостности пройдена / Перевірку цілісності пройдено")
                cls._verified = True

            return len(errors) == 0, errors

    @classmethod
    def is_verified(cls) -> bool:
        """Return status of last check / Возвращает статус последней проверки / Повертає статус останньої перевірки"""
        with cls._lock:
            return cls._verified

    @classmethod
    def get_file_status(cls) -> Dict[str, Dict]:
        """
        Get status of each file.
        Returns a dictionary with information about each file.

        Получает статус каждого файла.
        Возвращает словарь с информацией о каждом файле.

        Отримує статус кожного файлу.
        Повертає словник з інформацією про кожен файл.
        """
        with cls._lock:
            status = {}

            integrity_data = cls._load_integrity_data()
            saved_hashes = integrity_data.get("files", {}) if integrity_data and isinstance(integrity_data, dict) else {}

            for file_path, required in CRITICAL_FILES:
                abs_path = cls._get_absolute_path(file_path)
                current_hash = cls._get_file_hash(abs_path)
                expected_hash = saved_hashes.get(file_path)

                status[file_path] = {
                    "exists": current_hash is not None,
                    "required": required,
                    "modified": current_hash is not None and expected_hash is not None and current_hash != expected_hash,
                    "in_database": expected_hash is not None
                }

            return status

    @classmethod
    def update_integrity(cls, force: bool = False) -> bool:
        """
        Update integrity file (after program update).
        Requires force=True in secure mode.

        Обновляет файл целостности (после обновления программы).
        Требует force=True в безопасном режиме.

        Оновлює файл цілісності (після оновлення програми).
        Вимагає force=True у безпечному режимі.
        """
        logger.info("Updating integrity database... / Обновление базы целостности... / Оновлення бази цілісності...")
        return cls.generate_integrity_file(force=force)


def verify_program_integrity(auto_repair: bool = False) -> bool:
    """
    Quick program integrity check.
    Returns True if check passed.

    Быстрая проверка целостности программы.
    Возвращает True если проверка пройдена.

    Швидка перевірка цілісності програми.
    Повертає True якщо перевірку пройдено.
    """
    # FIXED #20: auto_repair now defaults to False and is ignored in secure mode
    # Исправлено #20: auto_repair теперь False по умолчанию и игнорируется в безопасном режиме
    # Виправлено #20: auto_repair тепер False за замовчуванням і ігнорується в безпечному режимі
    is_valid, errors = IntegrityChecker.verify_integrity(auto_repair=auto_repair)

    if not is_valid:
        logger.error(f"Program integrity check failed with {len(errors)} errors / Проверка целостности программы не пройдена с {len(errors)} ошибками / Перевірку цілісності програми не пройдено з {len(errors)} помилками")
        for error in errors[:3]:
            logger.error(f"  - {error}")

    return is_valid


def get_integrity_status() -> Dict:
    """
    Get detailed integrity status.
    Used for display in UI.

    Получает детальный статус целостности.
    Используется для отображения в UI.

    Отримує детальний статус цілісності.
    Використовується для відображення в UI.
    """
    is_valid, errors = IntegrityChecker.verify_integrity(auto_repair=False)

    return {
        "is_valid": is_valid,
        "errors": errors,
        "file_status": IntegrityChecker.get_file_status(),
        "last_verified": IntegrityChecker.is_verified(),
        "secure_mode": IntegrityChecker._secure_mode
    }


def repair_integrity(force: bool = False) -> bool:
    """
    Attempt to repair integrity by regenerating file.
    Requires force=True in secure mode.

    Пытается восстановить целостность (перегенерирует файл).
    Требует force=True в безопасном режиме.

    Намагається відновити цілісність (перегенерує файл).
    Вимагає force=True у безпечному режимі.
    """
    logger.info("Attempting to repair integrity... / Попытка восстановления целостности... / Спроба відновлення цілісності...")
    return IntegrityChecker.generate_integrity_file(force=force)


def init_integrity_check(secure_mode: bool = True) -> None:
    """
    Initialize integrity check (at startup).

    Инициализация проверки целостности (при запуске).
    Ініціалізація перевірки цілісності (при запуску).

    Args:
        secure_mode: If True, missing integrity file causes failure
                     Если True, отсутствие файла целостности вызывает ошибку
                     Якщо True, відсутність файлу цілісності викликає помилку
    """
    IntegrityChecker.set_secure_mode(secure_mode)

    if not os.path.exists(INTEGRITY_FILE):
        if secure_mode:
            logger.critical("Integrity file missing in secure mode! Program may be compromised. / Файл целостности отсутствует в безопасном режиме! Программа может быть скомпрометирована. / Файл цілісності відсутній у безпечному режимі! Програма може бути скомпрометована.")
            # Do NOT auto-generate in secure mode
            # НЕ авто-генерируем в безопасном режиме
            # НЕ авто-генеруємо у безпечному режимі
        else:
            logger.warning("First run - generating integrity file (non-secure mode) / Первый запуск - генерация файла целостности (небезопасный режим) / Перший запуск - генерація файлу цілісності (небезпечний режим)")
            IntegrityChecker.generate_integrity_file(force=True)
    else:
        # Background check (non-critical) / Фоновая проверка (не критично) / Фонова перевірка (не критично)
        try:
            is_valid, errors = IntegrityChecker.verify_integrity(auto_repair=False)
            if not is_valid:
                logger.warning("Integrity check found issues / Проверка целостности обнаружила проблемы / Перевірка цілісності виявила проблеми")
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.debug(f"Background integrity check failed / Фоновая проверка целостности не удалась / Фонова перевірка цілісності не вдалася: {e}")


__all__ = [
    'IntegrityChecker',
    'verify_program_integrity',
    'get_integrity_status',
    'repair_integrity',
    'init_integrity_check',
    'SECURE_MODE',
]