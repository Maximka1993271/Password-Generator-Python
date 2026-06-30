"""
Database backup and recovery module for SecurePassPro

Модуль резервного копирования и восстановления базы данных для SecurePassPro
Модуль резервного копіювання та відновлення бази даних для SecurePassPro

This module contains:
- Database backup creation
- Database restoration from backup
- Backup directory management
- Backup cleanup (old backups)

Этот модуль содержит:
- Создание резервных копий базы данных
- Восстановление базы данных из резервной копии
- Управление директорией бэкапов
- Очистку старых резервных копий

Цей модуль містить:
- Створення резервних копій бази даних
- Відновлення бази даних з резервної копії
- Керування директорією бекапів
- Очищення старих резервних копій

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки

FIXED #SEC-3: Replaced broad ValueError with specific error handling in DatabaseBackup.from_path()
ИСПРАВЛЕНО #SEC-3: Заменён широкий ValueError на конкретную обработку ошибок в DatabaseBackup.from_path()
ВИПРАВЛЕНО #SEC-3: Замінено широкий ValueError на конкретну обробку помилок у DatabaseBackup.from_path()
"""
from __future__ import annotations

import os
import sys
import shutil
import datetime
import sqlite3
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict

# ==================== UNIFIED LOGGER ====================
from utils.logger import get_logger

logger = get_logger("database_backup")

# ==================== PORTABLE PATHS LOGIC ====================

def _get_base_dir() -> str:
    """
    Get the directory where the application is running

    Получить папку, где запущено приложение
    Отримати папку, де запущено додаток
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_db_path() -> str:
    """
    Get database file path inside application directory

    Получить путь к файлу БД в папке приложения
    Отримати шлях до файлу БД в папці додатку
    """
    base_dir = _get_base_dir()
    securepass_data = os.path.join(base_dir, ".securepass", "data")
    if os.path.exists(securepass_data):
        data_dir = securepass_data
    else:
        data_dir = os.path.join(base_dir, "data")

    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            try:
                import ctypes, platform as _plat
                if _plat.system() == "Windows":
                    ctypes.windll.kernel32.SetFileAttributesW(data_dir, 0x02)
            except (AttributeError, OSError, TypeError, ImportError):
                pass
        except (OSError, IOError, PermissionError) as _:
            return os.path.join(base_dir, "passwords.db")

    if os.access(data_dir, os.W_OK):
        return os.path.join(data_dir, "passwords.db")
    else:
        return os.path.join(base_dir, "passwords.db")


def get_db_path() -> str:
    """
    Public function to get database path

    Публичная функция для получения пути к БД
    Публічна функція для отримання шляху до БД
    """
    return _get_db_path()


@dataclass
class DatabaseBackup:
    """
    Database backup metadata structure

    Структура метаданных резервной копии базы данных
    Структура метаданих резервної копії бази даних
    """
    path: str
    timestamp: float
    size: int
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)

    @classmethod
    def from_path(cls, path: str) -> Optional['DatabaseBackup']:
        """
        Create backup metadata from file path

        Создать метаданные резервной копии из пути к файлу
        Створити метадані резервної копії зі шляху до файлу

        FIXED #SEC-3: Replaced broad ValueError with specific error handling
        ИСПРАВЛЕНО #SEC-3: Заменён широкий ValueError на конкретную обработку ошибок
        ВИПРАВЛЕНО #SEC-3: Замінено широкий ValueError на конкретну обробку помилок
        """
        try:
            if not os.path.exists(path):
                return None
            stat = os.stat(path)
            timestamp = stat.st_mtime
            size = stat.st_size
            filename = os.path.basename(path)
            if filename.startswith("passwords_backup_") and filename.endswith(".db"):
                date_part = filename.replace("passwords_backup_", "").replace(".db", "")
                try:
                    created_at = datetime.datetime.strptime(date_part, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError as e:
                    # FIXED: Log the specific ValueError before falling back to timestamp-based date
                    # ИСПРАВЛЕНО: Логируем конкретную ValueError перед откатом к дате на основе timestamp
                    # ВИПРАВЛЕНО: Логуємо конкретну ValueError перед відкатом до дати на основі timestamp
                    logger.debug(f"Failed to parse date from filename '{date_part}', using file modification time: {e} / Не удалось разобрать дату из имени файла '{date_part}', используется время изменения файла: {e} / Не вдалося розібрати дату з імені файлу '{date_part}', використовується час зміни файлу: {e}")
                    created_at = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            return cls(
                path=path,
                timestamp=timestamp,
                size=size,
                created_at=created_at
            )
        except OSError as e:
            # FIXED: Handle OSError separately with specific logging
            # ИСПРАВЛЕНО: Обрабатываем OSError отдельно с конкретным логированием
            # ВИПРАВЛЕНО: Обробляємо OSError окремо з конкретним логуванням
            logger.debug(f"OS error creating backup metadata for {path}: {e} / Ошибка ОС при создании метаданных резервной копии для {path}: {e} / Помилка ОС при створенні метаданих резервної копії для {path}: {e}")
            return None
        except IOError as e:
            # FIXED: Handle IOError separately
            # ИСПРАВЛЕНО: Обрабатываем IOError отдельно
            # ВИПРАВЛЕНО: Обробляємо IOError окремо
            logger.debug(f"IO error creating backup metadata for {path}: {e} / Ошибка ввода-вывода при создании метаданных резервной копии для {path}: {e} / Помилка введення-виведення при створенні метаданих резервної копії для {path}: {e}")
            return None
        except PermissionError as e:
            # FIXED: Handle PermissionError separately
            # ИСПРАВЛЕНО: Обрабатываем PermissionError отдельно
            # ВИПРАВЛЕНО: Обробляємо PermissionError окремо
            logger.debug(f"Permission error creating backup metadata for {path}: {e} / Ошибка доступа при создании метаданных резервной копии для {path}: {e} / Помилка доступу при створенні метаданих резервної копії для {path}: {e}")
            return None
        except TypeError as e:
            # FIXED: Handle TypeError separately
            # ИСПРАВЛЕНО: Обрабатываем TypeError отдельно
            # ВИПРАВЛЕНО: Обробляємо TypeError окремо
            logger.debug(f"Type error creating backup metadata for {path}: {e} / Ошибка типа при создании метаданных резервной копии для {path}: {e} / Помилка типу при створенні метаданих резервної копії для {path}: {e}")
            return None


class DatabaseBackupManager:
    """
    Database backup and recovery manager

    Менеджер резервного копирования и восстановления базы данных
    Менеджер резервного копіювання та відновлення бази даних
    """

    _instance = None
    _backup_dir: Optional[str] = None

    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_backup_dir()
        return cls._instance

    def _init_backup_dir(self) -> None:
        """Initialize backup directory / Инициализировать директорию бэкапов / Ініціалізувати директорію бекапів"""
        base_dir = _get_base_dir()
        backup_dir = os.path.join(base_dir, "backups")
        try:
            os.makedirs(backup_dir, exist_ok=True)
            self._backup_dir = backup_dir
            logger.debug(f"Backup directory initialized: {backup_dir} / Директория бэкапов инициализирована: {backup_dir} / Директорію бекапів ініціалізовано: {backup_dir}")
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to create backup directory / Ошибка создания директории бэкапов / Помилка створення директорії бекапів: {e}")
            self._backup_dir = None

    def get_backup_dir(self) -> Optional[str]:
        """Get backup directory path / Получить путь к директории бэкапов / Отримати шлях до директорії бекапів"""
        return self._backup_dir

    def create_backup(self, db_path: str = None) -> Optional[str]:
        """
        Create a backup of the database.

        Создаёт резервную копию базы данных.
        Створює резервну копію бази даних.

        Args:
            db_path: Path to database (auto-detected if None) / Путь к БД (авто-определение если None) / Шлях до БД (авто-визначення якщо None)

        Returns:
            Path to backup file or None / Путь к файлу бэкапа или None / Шлях до файлу бекапу або None
        """
        if self._backup_dir is None:
            logger.error("Backup directory not available / Директория бэкапов недоступна / Директорію бекапів недоступно")
            return None

        if db_path is None:
            db_path = get_db_path()

        if not os.path.exists(db_path):
            logger.warning(f"Database not found: {db_path} / База данных не найдена: {db_path} / Базу даних не знайдено: {db_path}")
            return None

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"passwords_backup_{timestamp}.db"
            backup_path = os.path.join(self._backup_dir, backup_filename)

            # Use sqlite3 backup API for consistent backup
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(backup_path)
            src_conn.backup(dst_conn)
            src_conn.close()
            dst_conn.close()

            logger.info(f"Database backup created: {backup_path} / Создана резервная копия БД: {backup_path} / Створено резервну копію БД: {backup_path}")
            return backup_path

        except sqlite3.Error as e:
            logger.error(f"SQLite backup error / Ошибка резервного копирования SQLite / Помилка резервного копіювання SQLite: {e}")
            # Fallback to simple copy
            try:
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backup created (copy): {backup_path} / Создана резервная копия БД (копия): {backup_path} / Створено резервну копію БД (копія): {backup_path}")
                return backup_path
            except (OSError, IOError, PermissionError, shutil.Error) as e2:
                logger.error(f"Failed to create backup copy / Ошибка создания копии бэкапа / Помилка створення копії бекапу: {e2}")
                return None
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to create backup / Ошибка создания бэкапа / Помилка створення бекапу: {e}")
            return None

    def restore_from_backup(self, backup_path: str, target_path: str = None) -> bool:
        """
        Restore database from backup.

        Восстанавливает базу данных из резервной копии.
        Відновлює базу даних з резервної копії.

        Args:
            backup_path: Path to backup file / Путь к файлу бэкапа / Шлях до файлу бекапу
            target_path: Target database path (auto-detected if None) / Целевой путь БД (авто-определение если None) / Цільовий шлях БД (авто-визначення якщо None)

        Returns:
            True if restore successful / True если восстановление успешно / True якщо відновлення успішне
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path} / Файл бэкапа не найден: {backup_path} / Файл бекапу не знайдено: {backup_path}")
            return False

        if target_path is None:
            target_path = get_db_path()

        # Verify backup integrity before restore
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            if result and result[0] != "ok":
                logger.error(f"Backup integrity check failed: {result} / Проверка целостности бэкапа не пройдена: {result} / Перевірку цілісності бекапу не пройдено: {result}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Backup integrity check error / Ошибка проверки целостности бэкапа / Помилка перевірки цілісності бекапу: {e}")
            return False

        # Create backup of current database before restore (just in case)
        if os.path.exists(target_path):
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                pre_restore_backup = os.path.join(self._backup_dir, f"pre_restore_{timestamp}.db")
                shutil.copy2(target_path, pre_restore_backup)
                logger.debug(f"Pre-restore backup created: {pre_restore_backup} / Создана резервная копия перед восстановлением: {pre_restore_backup} / Створено резервну копію перед відновленням: {pre_restore_backup}")
            except (OSError, IOError, PermissionError, shutil.Error) as e:
                logger.warning(f"Failed to create pre-restore backup / Ошибка создания бэкапа перед восстановлением / Помилка створення бекапу перед відновленням: {e}")

        # Restore backup
        try:
            shutil.copy2(backup_path, target_path)
            logger.info(f"Database restored from backup: {backup_path} / База данных восстановлена из бэкапа: {backup_path} / Базу даних відновлено з бекапу: {backup_path}")
            return True
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to restore database / Ошибка восстановления базы данных / Помилка відновлення бази даних: {e}")
            return False

    def get_backups(self) -> List[DatabaseBackup]:
        """
        Get list of available backups.

        Получить список доступных резервных копий.
        Отримати список доступних резервних копій.

        Returns:
            List of backup metadata / Список метаданных резервных копий / Список метаданих резервних копій
        """
        backups = []

        if self._backup_dir is None or not os.path.exists(self._backup_dir):
            return backups

        try:
            for f in os.listdir(self._backup_dir):
                if f.startswith("passwords_backup_") and f.endswith(".db"):
                    f_path = os.path.join(self._backup_dir, f)
                    backup = DatabaseBackup.from_path(f_path)
                    if backup:
                        backups.append(backup)

            # Sort by timestamp descending (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)
            return backups

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to list backups / Ошибка получения списка бэкапов / Помилка отримання списку бекапів: {e}")
            return backups

    def get_latest_backup(self) -> Optional[DatabaseBackup]:
        """
        Get the latest backup.

        Получить последнюю резервную копию.
        Отримати останню резервну копію.

        Returns:
            Latest backup metadata or None / Метаданные последней копии или None / Метадані останньої копії або None
        """
        backups = self.get_backups()
        if backups:
            return backups[0]
        return None

    def delete_old_backups(self, keep_count: int = 10, max_age_days: int = 90) -> int:
        """
        Delete old backups.

        Удаляет старые резервные копии.
        Видаляє старі резервні копії.

        Args:
            keep_count: Minimum number of backups to keep / Минимальное количество копий для хранения / Мінімальна кількість копій для зберігання
            max_age_days: Maximum age of backups in days / Максимальный возраст копий в днях / Максимальний вік копій в днях

        Returns:
            Number of deleted backups / Количество удалённых копий / Кількість видалених копій
        """
        backups = self.get_backups()
        deleted = 0
        current_time = datetime.datetime.now().timestamp()

        # Delete backups older than max_age_days
        for backup in backups:
            backup_age_days = (current_time - backup.timestamp) / (24 * 3600)
            if backup_age_days > max_age_days:
                try:
                    os.remove(backup.path)
                    deleted += 1
                    logger.debug(f"Deleted old backup: {backup.path} / Удалён старый бэкап: {backup.path} / Видалено старий бекап: {backup.path}")
                except (OSError, IOError, PermissionError) as e:
                    logger.warning(f"Failed to delete old backup / Ошибка удаления старого бэкапа / Помилка видалення старого бекапу: {e}")

        # Refresh list after age-based deletion
        backups = self.get_backups()

        # Keep only keep_count newest backups
        if len(backups) > keep_count:
            to_delete = backups[keep_count:]
            for backup in to_delete:
                try:
                    os.remove(backup.path)
                    deleted += 1
                    logger.debug(f"Deleted old backup (limit): {backup.path} / Удалён старый бэкап (лимит): {backup.path} / Видалено старий бекап (ліміт): {backup.path}")
                except (OSError, IOError, PermissionError) as e:
                    logger.warning(f"Failed to delete old backup / Ошибка удаления старого бэкапа / Помилка видалення старого бекапу: {e}")

        if deleted > 0:
            logger.info(f"Deleted {deleted} old backups / Удалено {deleted} старых бэкапов / Видалено {deleted} старих бекапів")

        return deleted

    def cleanup_all_backups(self) -> int:
        """
        Delete ALL backups.

        Удаляет ВСЕ резервные копии.
        Видаляє ВСІ резервні копії.

        Returns:
            Number of deleted backups / Количество удалённых копий / Кількість видалених копій
        """
        backups = self.get_backups()
        deleted = 0

        for backup in backups:
            try:
                os.remove(backup.path)
                deleted += 1
                logger.debug(f"Deleted backup: {backup.path} / Удалён бэкап: {backup.path} / Видалено бекап: {backup.path}")
            except (OSError, IOError, PermissionError) as e:
                logger.warning(f"Failed to delete backup / Ошибка удаления бэкапа / Помилка видалення бекапу: {e}")

        logger.info(f"Deleted {deleted} backups / Удалено {deleted} бэкапов / Видалено {deleted} бекапів")
        return deleted

    def get_backup_count(self) -> int:
        """
        Get number of available backups.

        Получить количество доступных резервных копий.
        Отримати кількість доступних резервних копій.

        Returns:
            Number of backups / Количество копий / Кількість копій
        """
        return len(self.get_backups())

    def has_backups(self) -> bool:
        """
        Check if any backups exist.

        Проверяет, существуют ли резервные копии.
        Перевіряє, чи існують резервні копії.

        Returns:
            True if backups exist / True если копии существуют / True якщо копії існують
        """
        return self.get_backup_count() > 0

    def verify_backup(self, backup_path: str) -> Tuple[bool, str]:
        """
        Verify backup file integrity.

        Проверяет целостность файла резервной копии.
        Перевіряє цілісність файлу резервної копії.

        Args:
            backup_path: Path to backup file / Путь к файлу бэкапа / Шлях до файлу бекапу

        Returns:
            (is_valid, message) / (is_valid, сообщение) / (is_valid, повідомлення)
        """
        if not os.path.exists(backup_path):
            return False, "Backup file not found / Файл бэкапа не найден / Файл бекапу не знайдено"

        try:
            # Check file size
            size = os.path.getsize(backup_path)
            if size == 0:
                return False, "Backup file is empty / Файл бэкапа пуст / Файл бекапу порожній"

            # Check SQLite integrity
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "ok":
                return True, "Backup integrity verified / Целостность бэкапа подтверждена / Цілісність бекапу підтверджено"
            else:
                return False, f"Integrity check failed: {result} / Проверка целостности не пройдена: {result} / Перевірку цілісності не пройдено: {result}"

        except sqlite3.Error as e:
            logger.error(f"SQLite verification error / Ошибка проверки SQLite / Помилка перевірки SQLite: {e}")
            return False, f"SQLite error / Ошибка SQLite / Помилка SQLite: {e}"
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File verification error / Ошибка проверки файла / Помилка перевірки файлу: {e}")
            return False, f"File error / Ошибка файла / Помилка файлу: {e}"


# ==================== SINGLETON INSTANCE ====================

_backup_manager = None

def get_backup_manager() -> DatabaseBackupManager:
    """Get the global backup manager instance / Получить глобальный экземпляр менеджера бэкапов / Отримати глобальний екземпляр менеджера бекапів"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = DatabaseBackupManager()
    return _backup_manager


# ==================== CONVENIENCE FUNCTIONS ====================

def create_database_backup(db_path: str = None) -> Optional[str]:
    """Create a database backup / Создать резервную копию БД / Створити резервну копію БД"""
    return get_backup_manager().create_backup(db_path)

def restore_database_from_backup(backup_path: str, target_path: str = None) -> bool:
    """Restore database from backup / Восстановить БД из бэкапа / Відновити БД з бекапу"""
    return get_backup_manager().restore_from_backup(backup_path, target_path)

def get_database_backups() -> List[DatabaseBackup]:
    """Get list of available backups / Получить список доступных бэкапов / Отримати список доступних бекапів"""
    return get_backup_manager().get_backups()

def get_latest_database_backup() -> Optional[DatabaseBackup]:
    """Get the latest backup / Получить последний бэкап / Отримати останній бекап"""
    return get_backup_manager().get_latest_backup()

def cleanup_old_database_backups(keep_count: int = 10, max_age_days: int = 90) -> int:
    """Delete old backups / Удалить старые бэкапы / Видалити старі бекапи"""
    return get_backup_manager().delete_old_backups(keep_count, max_age_days)

def get_database_backup_count() -> int:
    """Get number of available backups / Получить количество доступных бэкапов / Отримати кількість доступних бекапів"""
    return get_backup_manager().get_backup_count()

def has_database_backups() -> bool:
    """Check if any backups exist / Проверить, существуют ли бэкапы / Перевірити, чи існують бекапи"""
    return get_backup_manager().has_backups()

def verify_database_backup(backup_path: str) -> Tuple[bool, str]:
    """Verify backup file integrity / Проверить целостность файла бэкапа / Перевірити цілісність файлу бекапу"""
    return get_backup_manager().verify_backup(backup_path)

def get_backup_directory() -> Optional[str]:
    """Get backup directory path / Получить путь к директории бэкапов / Отримати шлях до директорії бекапів"""
    return get_backup_manager().get_backup_dir()


# ==================== EXPORTS ====================

__all__ = [
    'DatabaseBackup',
    'DatabaseBackupManager',
    'get_backup_manager',
    'create_database_backup',
    'restore_database_from_backup',
    'get_database_backups',
    'get_latest_database_backup',
    'cleanup_old_database_backups',
    'get_database_backup_count',
    'has_database_backups',
    'verify_database_backup',
    'get_backup_directory',
]