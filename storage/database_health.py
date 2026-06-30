"""
Database health check and recovery module for SecurePassPro

Модуль проверки здоровья и восстановления базы данных для SecurePassPro
Модуль перевірки здоров'я та відновлення бази даних для SecurePassPro

This module contains:
- Database integrity checking
- Health diagnostics
- Database recovery
- Quick health checks

Этот модуль содержит:
- Проверку целостности базы данных
- Диагностику здоровья
- Восстановление базы данных
- Быстрые проверки здоровья

Цей модуль містить:
- Перевірку цілісності бази даних
- Діагностику здоров'я
- Відновлення бази даних
- Швидкі перевірки здоров'я

FIXED #EX: Replaced broad Exception with specific exceptions
Исправлено #EX: Заменены общие Exception на конкретные исключения
Виправлено #EX: Замінено загальні Exception на конкретні винятки
"""
from __future__ import annotations

import os
import sys
import sqlite3
import shutil
import tempfile
import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict

# ==================== UNIFIED LOGGER ====================
from utils.logger import get_logger

logger = get_logger("database_health")

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
    # Use .securepass/data for new installs; fall back to legacy data/ and hide it
    securepass_data = os.path.join(base_dir, ".securepass", "data")
    if os.path.exists(securepass_data):
        data_dir = securepass_data
    else:
        data_dir = os.path.join(base_dir, "data")

    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            # Hide the data directory on Windows
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


# ==================== DATABASE HEALTH CHECK ====================

class DatabaseHealthCheck:
    """Database health check and diagnostics
    Проверка здоровья базы данных и диагностика
    Перевірка здоров'я бази даних та діагностика"""

    @staticmethod
    def check_integrity(db_path: str) -> Dict[str, Any]:
        """
        Run PRAGMA integrity_check on database.

        Выполняет PRAGMA integrity_check для базы данных.
        Виконує PRAGMA integrity_check для бази даних.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "ok":
                logger.info("Database integrity check passed / Проверка целостности БД пройдена / Перевірку цілісності БД пройдено")
                return {"status": "ok", "message": "Integrity check passed / Проверка целостности пройдена / Перевірку цілісності пройдено"}
            else:
                logger.warning(f"Database integrity check failed: {result} / Проверка целостности БД не пройдена: {result} / Перевірку цілісності БД не пройдено: {result}")
                return {"status": "failed", "message": str(result) if result else "Unknown error / Неизвестная ошибка / Невідома помилка"}
        except sqlite3.Error as e:
            logger.error(f"Integrity check error / Ошибка проверки целостности / Помилка перевірки цілісності: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def check_foreign_keys(db_path: str) -> bool:
        """Check foreign key constraints / Проверить внешние ключи / Перевірити зовнішні ключі"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()
            conn.close()

            if violations:
                logger.warning(f"Foreign key violations: {len(violations)} / Нарушений внешних ключей: {len(violations)} / Порушень зовнішніх ключів: {len(violations)}")
                return False
            return True
        except sqlite3.Error as e:
            logger.error(f"Foreign key check error / Ошибка проверки внешних ключів / Помилка перевірки зовнішніх ключів: {e}")
            return False

    @staticmethod
    def get_database_size(db_path: str) -> int:
        """Get database file size in bytes / Получить размер файла БД в байтах / Отримати розмір файлу БД у байтах"""
        try:
            if os.path.exists(db_path):
                return os.path.getsize(db_path)
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"Failed to get DB size / Ошибка получения размера БД / Помилка отримання розміру БД: {e}")
        return 0

    @staticmethod
    def get_table_info(db_path: str, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information / Получить информацию о схеме таблицы / Отримати інформацію про схему таблиці"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return columns
        except sqlite3.Error as e:
            logger.error(f"Failed to get table info / Ошибка получения информации о таблице / Помилка отримання інформації про таблицю: {e}")
            return []

    @staticmethod
    def get_table_row_count(db_path: str, table_name: str) -> int:
        """Get number of rows in table / Получить количество строк в таблице / Отримати кількість рядків у таблиці"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except sqlite3.Error as e:
            logger.error(f"Failed to get row count / Ошибка получения количества строк / Помилка отримання кількості рядків: {e}")
            return -1

    @staticmethod
    def get_database_stats(db_path: str) -> Dict[str, Any]:
        """Get comprehensive database statistics / Получить полную статистику БД / Отримати повну статистику БД"""
        stats = {
            "exists": os.path.exists(db_path),
            "size_bytes": 0,
            "size_mb": 0,
            "table_count": 0,
            "tables": {},
            "integrity": None,
            "journal_mode": None,
            "page_size": None,
            "schema_version": None,
        }

        if not stats["exists"]:
            return stats

        stats["size_bytes"] = DatabaseHealthCheck.get_database_size(db_path)
        stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 2)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            stats["table_count"] = len(tables)

            for table in tables:
                table_name = table[0]
                row_count = DatabaseHealthCheck.get_table_row_count(db_path, table_name)
                stats["tables"][table_name] = {
                    "row_count": row_count,
                    "columns": len(DatabaseHealthCheck.get_table_info(db_path, table_name))
                }

            cursor.execute("PRAGMA journal_mode")
            stats["journal_mode"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size")
            stats["page_size"] = cursor.fetchone()[0]

            cursor.execute("PRAGMA schema_version")
            stats["schema_version"] = cursor.fetchone()[0]

            conn.close()

            stats["integrity"] = DatabaseHealthCheck.check_integrity(db_path)

        except sqlite3.Error as e:
            logger.error(f"Failed to get database stats / Ошибка получения статистики БД / Помилка отримання статистики БД: {e}")
            stats["error"] = str(e)

        return stats

    @staticmethod
    def quick_health_check(db_path: str) -> Tuple[bool, str]:
        """
        Quick health check - returns (is_healthy, message)

        Быстрая проверка здоровья - возвращает (здорова, сообщение)
        Швидка перевірка здоров'я - повертає (здорова, повідомлення)
        """
        if not os.path.exists(db_path):
            return False, "Database file does not exist / Файл БД не существует / Файл БД не існує"

        try:
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()

            cursor.execute("PRAGMA quick_check")
            result = cursor.fetchone()
            conn.close()

            if result and result[0] == "ok":
                return True, "Database is healthy / БД здорова / БД здорова"
            else:
                return False, f"Quick check failed: {result} / Быстрая проверка не пройдена: {result} / Швидку перевірку не пройдено: {result}"

        except sqlite3.Error as e:
            return False, f"Connection error / Ошибка подключения / Помилка підключення: {e}"


# ==================== DATABASE RECOVERY ====================

class DatabaseRecovery:
    """Automatic database recovery on corruption
    Автоматическое восстановление БД при повреждении
    Автоматичне відновлення БД при пошкодженні"""

    @staticmethod
    def create_backup(db_path: str) -> Optional[str]:
        """
        Create a backup of the database.

        Создаёт резервную копию базы данных.
        Створює резервну копію бази даних.
        """
        try:
            if not os.path.exists(db_path):
                return None

            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"passwords_backup_{timestamp}.db")

            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backup created: {backup_path} / Создана резервная копия БД: {backup_path} / Створено резервну копію БД: {backup_path}")
            return backup_path
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to create backup / Ошибка создания резервной копии / Помилка створення резервної копії: {e}")
            return None

    @staticmethod
    def attempt_repair(db_path: str) -> bool:
        """
        Attempt to repair corrupted database.

        Пытается восстановить повреждённую базу данных.
        Намагається відновити пошкоджену базу даних.
        """
        logger.warning(f"Attempting to repair database: {db_path} / Попытка восстановления БД: {db_path} / Спроба відновлення БД: {db_path}")

        backup_path = DatabaseRecovery.create_backup(db_path)
        if not backup_path:
            logger.error("Failed to create backup before repair / Ошибка создания резервной копии перед восстановлением / Помилка створення резервної копії перед відновленням")
            return False

        try:
            # Method 1: Dump and restore
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()

            try:
                conn_old = sqlite3.connect(db_path)
                conn_new = sqlite3.connect(temp_db.name)

                cursor = conn_old.cursor()
                cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    if table[0]:
                        try:
                            conn_new.execute(table[0])
                        except sqlite3.Error as e:
                            logger.warning(f"Failed to recreate table: {e} / Ошибка воссоздания таблицы: {e} / Помилка відтворення таблиці: {e}")

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for row in cursor.fetchall():
                    table_name = row[0]
                    try:
                        data = conn_old.execute(f"SELECT * FROM {table_name}").fetchall()
                        if data:
                            placeholders = ','.join(['?' for _ in range(len(data[0]))])
                            for row_data in data:
                                try:
                                    conn_new.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", row_data)
                                except sqlite3.Error as e:
                                    logger.debug(f"Failed to insert row into {table_name}: {e} / Ошибка вставки строки в {table_name} / Помилка вставки рядка в {table_name}")
                    except sqlite3.Error as e:
                        logger.warning(f"Failed to copy data from {table_name}: {e} / Ошибка копирования данных из {table_name} / Помилка копіювання даних з {table_name}")

                conn_new.commit()
                conn_old.close()
                conn_new.close()

                health_ok, msg = DatabaseHealthCheck.quick_health_check(temp_db.name)
                if health_ok:
                    shutil.move(temp_db.name, db_path)
                    logger.info("Database successfully repaired via dump/restore / БД успешно восстановлена через dump/restore / БД успішно відновлено через dump/restore")
                    return True
                else:
                    logger.error(f"Repaired database still corrupt: {msg} / Восстановленная БД всё ещё повреждена: {msg} / Відновлена БД все ще пошкоджена: {msg}")

            except sqlite3.Error as e:
                logger.error(f"Dump/restore repair failed / Ошибка восстановления dump/restore / Помилка відновлення dump/restore: {e}")
            finally:
                if os.path.exists(temp_db.name):
                    try:
                        os.remove(temp_db.name)
                    except (OSError, IOError, PermissionError) as _:
                        pass

            # Method 2: PRAGMA commands
            try:
                conn = sqlite3.connect(db_path)
                conn.execute("PRAGMA integrity_check")
                conn.execute("PRAGMA optimize")
                conn.close()
                logger.info("Database repair attempt with PRAGMA commands completed / Попытка восстановления БД с помощью команд PRAGMA завершена / Спроба відновлення БД за допомогою команд PRAGMA завершена")
                return True
            except sqlite3.Error as e:
                logger.error(f"PRAGMA repair failed / Ошибка восстановления PRAGMA / Помилка відновлення PRAGMA: {e}")

            logger.error("All repair attempts failed / Все попытки восстановления не удались / Всі спроби відновлення не вдалися")
            return False

        except (OSError, IOError, PermissionError, sqlite3.Error) as e:
            logger.error(f"Repair error / Ошибка восстановления / Помилка відновлення: {e}")
            return False

    @staticmethod
    def restore_from_backup(db_path: str) -> bool:
        """
        Restore database from latest backup.

        Восстанавливает базу данных из последней резервной копии.
        Відновлює базу даних з останньої резервної копії.
        """
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")

        if not os.path.exists(backup_dir):
            logger.warning("No backup directory found / Директория бэкапов не найдена / Директорію бекапів не знайдено")
            return False

        try:
            backups = []
            for f in os.listdir(backup_dir):
                if f.startswith("passwords_backup_") and f.endswith(".db"):
                    f_path = os.path.join(backup_dir, f)
                    backups.append((f_path, os.path.getmtime(f_path)))

            if not backups:
                logger.warning("No backups found / Бэкапы не найдены / Бекапи не знайдено")
                return False

            backups.sort(key=lambda x: x[1], reverse=True)
            latest_backup = backups[0][0]

            health_ok, msg = DatabaseHealthCheck.quick_health_check(latest_backup)
            if not health_ok:
                logger.error(f"Latest backup is corrupt: {msg} / Последний бэкап повреждён: {msg} / Останній бекап пошкоджено: {msg}")
                return False

            shutil.copy2(latest_backup, db_path)
            logger.info(f"Database restored from backup: {latest_backup} / БД восстановлена из бэкапа: {latest_backup} / БД відновлено з бекапу: {latest_backup}")
            return True

        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Restore from backup failed / Ошибка восстановления из бэкапа / Помилка відновлення з бекапу: {e}")
            return False


# ==================== CONVENIENCE FUNCTIONS ====================

def check_database_health() -> Dict[str, Any]:
    """
    Perform comprehensive database health check.

    Выполняет комплексную проверку здоровья базы данных.
    Виконує комплексну перевірку здоров'я бази даних.
    """
    db_path = get_db_path()
    return DatabaseHealthCheck.get_database_stats(db_path)


def quick_health_check() -> Tuple[bool, str]:
    """
    Quick health check for database.

    Быстрая проверка здоровья базы данных.
    Швидка перевірка здоров'я бази даних.
    """
    db_path = get_db_path()
    return DatabaseHealthCheck.quick_health_check(db_path)


def repair_database() -> bool:
    """
    Attempt to repair database.

    Пытается восстановить базу данных.
    Намагається відновити базу даних.
    """
    db_path = get_db_path()
    return DatabaseRecovery.attempt_repair(db_path)


def restore_database_from_backup() -> bool:
    """
    Restore database from latest backup.

    Восстанавливает базу данных из последней резервной копии.
    Відновлює базу даних з останньої резервної копії.
    """
    db_path = get_db_path()
    return DatabaseRecovery.restore_from_backup(db_path)


def vacuum_database() -> bool:
    """
    Optimize database with VACUUM.

    Оптимизирует базу данных с помощью VACUUM.
    Оптимізує базу даних за допомогою VACUUM.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("VACUUM")
        conn.close()
        logger.info("Database vacuum completed / VACUUM БД завершён / VACUUM БД завершено")
        return True
    except sqlite3.Error as e:
        logger.error(f"Vacuum error / Ошибка VACUUM / Помилка VACUUM: {e}")
        return False


# ==================== EXPORTS ====================

__all__ = [
    'DatabaseHealthCheck',
    'DatabaseRecovery',
    'check_database_health',
    'quick_health_check',
    'repair_database',
    'restore_database_from_backup',
    'vacuum_database',
]