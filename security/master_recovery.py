"""
Master password recovery module - recovery codes, backup, restore

Модуль восстановления мастер-пароля - резервные коды, бэкап, восстановление
Модуль відновлення майстер-пароля - резервні коди, бекап, відновлення

This module contains recovery-related functionality:
- Recovery code generation and verification
- Backup and restore of master password data
- Emergency recovery procedures

Этот модуль содержит функциональность восстановления:
- Генерация и проверка резервных кодов
- Резервное копирование и восстановление данных мастер-пароля
- Аварийные процедуры восстановления

Цей модуль містить функціональність відновлення:
- Генерація та перевірка резервних кодів
- Резервне копіювання та відновлення даних майстер-пароля
- Аварійні процедури відновлення
"""
from __future__ import annotations

import os
import sys
import json
import hashlib
import hmac
import secrets
import time
import shutil
import ctypes
import tempfile
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_SECUREPASS_R = os.path.join(_BASE_DIR, ".securepass", "data")
CONFIG_DIR = _SECUREPASS_R if os.path.exists(_SECUREPASS_R) else os.path.join(_BASE_DIR, "data")
if not os.path.exists(CONFIG_DIR):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        try:
            import ctypes as _ct3, platform as _pl3
            if _pl3.system() == "Windows":
                _ct3.windll.kernel32.SetFileAttributesW(CONFIG_DIR, 0x02)
        except (AttributeError, OSError, TypeError, ImportError):
            pass
    except (OSError, PermissionError):
        pass
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")
RECOVERY_CODES_FILE = os.path.join(CONFIG_DIR, "recovery_codes.json")
BACKUP_DIR = os.path.join(CONFIG_DIR, "master_backups")
# =============================================================

# ==================== UNIFIED LOGGER ====================
from utils.logger import get_logger

logger = get_logger("master_recovery")

# ==================== CONSTANTS ====================
RECOVERY_CODES_COUNT = 10
RECOVERY_CODE_LENGTH = 8
RECOVERY_CODE_HASH_PREFIX = "pbkdf2_sha256"
RECOVERY_CODE_HASH_ITERATIONS = 200000
RECOVERY_CODE_SALT_BYTES = 16

MAX_BACKUPS = 5
BACKUP_RETENTION_DAYS = 90


def _hash_recovery_code(code: str) -> str:
    """Hash a recovery code for storage
    Хеширует резервный код для хранения
    Хешує резервний код для зберігання"""
    import base64
    code_clean = str(code).replace("-", "").replace(" ", "")
    salt = secrets.token_bytes(RECOVERY_CODE_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        code_clean.encode("utf-8"),
        salt,
        RECOVERY_CODE_HASH_ITERATIONS,
        dklen=32,
    )
    return (
        f"{RECOVERY_CODE_HASH_PREFIX}${RECOVERY_CODE_HASH_ITERATIONS}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(digest).decode('ascii')}"
    )


def _verify_recovery_code_hash(code: str, stored_hash: str) -> bool:
    """Verify a recovery code against its stored hash
    Проверяет резервный код по его сохранённому хешу
    Перевіряє резервний код за його збереженим хешем"""
    import base64
    import binascii
    try:
        code_clean = str(code).replace("-", "").replace(" ", "")
        stored_hash = str(stored_hash or "")
        if stored_hash.startswith(f"{RECOVERY_CODE_HASH_PREFIX}$"):
            _, iterations, salt_b64, digest_b64 = stored_hash.split("$", 3)
            salt = base64.b64decode(salt_b64, validate=True)
            expected = base64.b64decode(digest_b64, validate=True)
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                code_clean.encode("utf-8"),
                salt,
                int(iterations),
                dklen=len(expected),
            )
            return hmac.compare_digest(computed, expected)
        legacy_hash = hashlib.sha256(code_clean.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy_hash, stored_hash.lower())
    except (TypeError, ValueError, binascii.Error, KeyError, IndexError) as e:
        logger.debug(f"Recovery code hash verification error / Ошибка проверки хеша резервного кода / Помилка перевірки хеша резервного коду: {e}")
        return False


def _secure_write(path: str, data: bytes) -> None:
    """Secure atomic write / Безопасная атомарная запись / Безпечний атомарний запис"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            if sys.platform == "win32":
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
                except (AttributeError, OSError, TypeError):
                    pass
            else:
                try:
                    os.chmod(path, 0o600)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError, IOError) as e:
            try:
                os.remove(tmp_path)
            except (OSError, PermissionError):
                pass
            raise IOError(f"Cannot write to {path}: {e} / Невозможно записать в {path}: {e} / Неможливо записати в {path}: {e}")
    except (OSError, IOError, PermissionError) as e:
        raise IOError(f"Cannot create directory for {path}: {e} / Невозможно создать директорию для {path}: {e} / Неможливо створити директорію для {path}: {e}")


def _secure_read(path: str) -> Optional[bytes]:
    """Secure read / Безопасное чтение / Безпечне читання"""
    try:
        if not os.path.exists(path):
            return None
        with open(path, 'rb') as f:
            return f.read()
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to read {path}: {e} / Не удалось прочитать {path}: {e} / Не вдалося прочитати {path}: {e}")
        return None


@dataclass
class RecoveryCode:
    """Recovery code structure / Структура резервного кода / Структура резервного коду"""
    code_hash: str
    created_at: str
    used: bool = False
    used_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryCode':
        """
        Handle from dict.
        Обработать from dict.
        Обробити from dict.
        """
        return cls(**data)


@dataclass
class MasterBackup:
    """Master password backup metadata / Метаданные резервной копии мастер-пароля / Метадані резервної копії майстер-пароля"""
    path: str
    timestamp: float
    version: str
    size: int
    hash_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Handle to dict.
        Обработать to dict.
        Обробити to dict.
        """
        return asdict(self)


class MasterRecovery:
    """
    Master password recovery manager.
    
    Менеджер восстановления мастер-пароля.
    Менеджер відновлення майстер-пароля.
    """

    _instance = None
    
    _recovery_codes: List[Dict[str, Any]] = []
    _backups: List[MasterBackup] = []

    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_recovery_codes()
            cls._instance._load_backups()
        return cls._instance

    # ==================== RECOVERY CODES ====================

    def _load_recovery_codes(self) -> None:
        """Load recovery codes from file / Загрузить резервные коды из файла / Завантажити резервні коди з файлу"""
        if not os.path.exists(RECOVERY_CODES_FILE):
            return

        try:
            content = _secure_read(RECOVERY_CODES_FILE)
            if content:
                data = json.loads(content.decode('utf-8'))
                codes = data.get("codes", [])
                if isinstance(codes, list):
                    self._recovery_codes = codes
                logger.debug(f"Loaded {len(self._recovery_codes)} recovery codes / Загружено {len(self._recovery_codes)} резервных кодов / Завантажено {len(self._recovery_codes)} резервних кодів")
        except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
            logger.debug(f"Failed to load recovery codes / Ошибка загрузки резервных кодов / Помилка завантаження резервних кодів: {e}")

    def _save_recovery_codes(self) -> None:
        """Save recovery codes to file / Сохранить резервные коды в файл / Зберегти резервні коди у файл"""
        try:
            codes_data = {
                "codes": self._recovery_codes,
                "last_update": datetime.now().isoformat(),
                "version": 1
            }
            _secure_write(RECOVERY_CODES_FILE, json.dumps(codes_data, indent=2).encode('utf-8'))
        except (OSError, IOError, PermissionError, TypeError) as e:
            logger.debug(f"Failed to save recovery codes / Ошибка сохранения резервных кодов / Помилка збереження резервних кодів: {e}")

    def generate_recovery_codes(self, count: int = RECOVERY_CODES_COUNT,
                                length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """
        Generate new recovery codes.
        
        Args:
            count: Number of codes to generate / Количество кодов для генерации / Кількість кодів для генерації
            length: Length of each code / Длина каждого кода / Довжина кожного коду
            
        Returns:
            List of recovery codes / Список резервных кодов / Список резервних кодів
        """
        try:
            new_codes = []
            self._recovery_codes.clear()

            for i in range(count):
                code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
                if length == 8:
                    code = f"{code[:4]}-{code[4:]}"

                recovery_code = RecoveryCode(
                    code_hash=_hash_recovery_code(code),
                    created_at=datetime.now().isoformat(),
                    used=False
                )
                self._recovery_codes.append(recovery_code.to_dict())
                new_codes.append(code)

            self._save_recovery_codes()
            logger.info(f"Generated {count} recovery codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
            return new_codes

        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.error(f"Failed to generate recovery codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")
            return []

    def verify_recovery_code(self, code: str) -> bool:
        """
        Verify and consume a recovery code.
        
        Args:
            code: Recovery code to verify / Резервный код для проверки / Резервний код для перевірки
            
        Returns:
            True if code is valid and was consumed / True если код действителен и был потреблён / True якщо код дійсний і був спожитий
        """
        try:
            code_clean = code.replace("-", "").replace(" ", "")

            for i, rc in enumerate(self._recovery_codes):
                if not rc.get("used", False) and _verify_recovery_code_hash(code_clean, rc.get("code_hash", "")):
                    rc["used"] = True
                    rc["used_at"] = datetime.now().isoformat()
                    self._save_recovery_codes()
                    logger.info("Recovery code used successfully / Резервный код успешно использован / Резервний код успішно використано")
                    return True

            logger.warning("Invalid or already used recovery code / Неверный или уже использованный резервный код / Невірний або вже використаний резервний код")
            return False

        except (ValueError, TypeError, OSError, AttributeError, KeyError) as e:
            logger.error(f"Recovery code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
            return False

    def get_recovery_codes_status(self) -> Dict[str, Any]:
        """Get recovery codes status / Получить статус резервных кодов / Отримати статус резервних кодів"""
        total = len(self._recovery_codes)
        used = sum(1 for rc in self._recovery_codes if rc.get("used", False))
        return {
            "total": total,
            "used": used,
            "available": total - used,
            "max_codes": RECOVERY_CODES_COUNT
        }

    def clear_recovery_codes(self) -> bool:
        """Clear all recovery codes / Очистить все резервные коды / Очистити всі резервні коди"""
        try:
            self._recovery_codes.clear()
            self._save_recovery_codes()
            logger.info("Recovery codes cleared / Резервные коды очищены / Резервні коди очищено")
            return True
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to clear recovery codes / Ошибка очистки резервных кодов / Помилка очищення резервних кодів: {e}")
            return False

    # ==================== BACKUP AND RESTORE ====================

    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists / Убедиться, что директория бэкапов существует / Переконатися, що директорія бекапів існує"""
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            if sys.platform == "win32":
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(BACKUP_DIR, 0x02)
                except (AttributeError, OSError, TypeError):
                    pass
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to create backup directory / Ошибка создания директории бэкапов / Помилка створення директорії бекапів: {e}")

    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of a file / Вычисляет SHA256 хеш файла / Обчислює SHA256 хеш файлу"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to calculate hash / Ошибка вычисления хеша / Помилка обчислення хеша: {e}")
            return None

    def _load_backups(self) -> None:
        """Load backup metadata / Загрузить метаданные бэкапов / Завантажити метадані бекапів"""
        self._ensure_backup_dir()
        self._backups.clear()

        try:
            if not os.path.exists(BACKUP_DIR):
                return

            for f in os.listdir(BACKUP_DIR):
                if f.startswith("master_backup_") and f.endswith(".key"):
                    f_path = os.path.join(BACKUP_DIR, f)
                    try:
                        # Extract version from filename: master_backup_v4.0.1_20250101_120000.key
                        version_part = f.replace("master_backup_", "").replace(".key", "")
                        version = version_part.split("_")[0] if version_part else "unknown"
                        
                        backup = MasterBackup(
                            path=f_path,
                            timestamp=os.path.getmtime(f_path),
                            version=version,
                            size=os.path.getsize(f_path),
                            hash_sha256=self._calculate_file_hash(f_path) or ""
                        )
                        self._backups.append(backup)
                    except (OSError, ValueError, IndexError) as e:
                        logger.debug(f"Failed to parse backup file {f}: {e} / Ошибка парсинга файла бэкапа {f} / Помилка парсингу файлу бекапу {f}")
                        continue

            # Sort by timestamp descending (newest first)
            self._backups.sort(key=lambda x: x.timestamp, reverse=True)
            logger.debug(f"Loaded {len(self._backups)} master backups / Загружено {len(self._backups)} бэкапов мастер-пароля / Завантажено {len(self._backups)} бекапів майстер-пароля")

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to load backups / Ошибка загрузки бэкапов / Помилка завантаження бекапів: {e}")

    def _cleanup_old_backups(self) -> int:
        """Clean up old backups, keep only MAX_BACKUPS
        Очистить старые бэкапы, оставить только MAX_BACKUPS
        Очистити старі бекапи, залишити тільки MAX_BACKUPS"""
        removed = 0
        try:
            # Keep only MAX_BACKUPS newest backups
            while len(self._backups) > MAX_BACKUPS:
                oldest = self._backups.pop()
                try:
                    os.remove(oldest.path)
                    removed += 1
                    logger.debug(f"Removed old backup: {oldest.path} / Удалён старый бэкап: {oldest.path} / Видалено старий бекап: {oldest.path}")
                except (OSError, IOError, PermissionError) as e:
                    logger.warning(f"Failed to remove old backup / Ошибка удаления старого бэкапа / Помилка видалення старого бекапу: {e}")

            # Also remove backups older than BACKUP_RETENTION_DAYS
            current_time = time.time()
            cutoff = BACKUP_RETENTION_DAYS * 24 * 3600
            for backup in self._backups[:]:
                if current_time - backup.timestamp > cutoff:
                    try:
                        os.remove(backup.path)
                        self._backups.remove(backup)
                        removed += 1
                        logger.debug(f"Removed expired backup: {backup.path} / Удалён просроченный бэкап: {backup.path} / Видалено прострочений бекап: {backup.path}")
                    except (OSError, IOError, PermissionError, ValueError) as e:
                        logger.warning(f"Failed to remove expired backup / Ошибка удаления просроченного бэкапа / Помилка видалення простроченого бекапу: {e}")

        except (OSError, IOError, PermissionError, ValueError) as e:
            logger.error(f"Backup cleanup error / Ошибка очистки бэкапов / Помилка очищення бекапів: {e}")

        if removed > 0:
            logger.info(f"Cleaned up {removed} old backups / Очищено {removed} старых бэкапов / Очищено {removed} старих бекапів")

        return removed

    def create_backup(self, version: str = "unknown") -> Optional[str]:
        """
        Create a backup of the master password file.
        
        Args:
            version: Current version for backup metadata / Текущая версия для метаданных / Поточна версія для метаданих
            
        Returns:
            Path to backup file or None / Путь к файлу бэкапа или None / Шлях до файлу бекапу або None
        """
        if not os.path.exists(MASTER_FILE):
            logger.warning("Master password file not found, cannot create backup / Файл мастер-пароля не найден, невозможно создать бэкап / Файл майстер-пароля не знайдено, неможливо створити бекап")
            return None

        self._ensure_backup_dir()

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"master_backup_{version}_{timestamp}.key"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)

            shutil.copy2(MASTER_FILE, backup_path)
            
            # Calculate hash for integrity
            file_hash = self._calculate_file_hash(backup_path)
            
            backup = MasterBackup(
                path=backup_path,
                timestamp=time.time(),
                version=version,
                size=os.path.getsize(backup_path),
                hash_sha256=file_hash or ""
            )
            self._backups.insert(0, backup)  # Add at beginning (newest first)
            
            self._cleanup_old_backups()
            
            logger.info(f"Master backup created: {backup_path} / Создан бэкап мастер-пароля: {backup_path} / Створено бекап майстер-пароля: {backup_path}")
            return backup_path

        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to create backup / Ошибка создания бэкапа / Помилка створення бекапу: {e}")
            return None

    def restore_from_backup(self, backup_index: int = 0) -> bool:
        """
        Restore master password from backup.
        
        Args:
            backup_index: Index of backup to restore (0 = newest) / Индекс бэкапа для восстановления / Індекс бекапу для відновлення
            
        Returns:
            True if restore successful / True если восстановление успешно / True якщо відновлення успішне
        """
        if backup_index >= len(self._backups):
            logger.warning(f"Backup index {backup_index} out of range (total: {len(self._backups)}) / Индекс бэкапа {backup_index} вне диапазона (всего: {len(self._backups)}) / Індекс бекапу {backup_index} поза діапазоном (всього: {len(self._backups)})")
            return False

        backup = self._backups[backup_index]
        
        try:
            # Verify backup integrity
            current_hash = self._calculate_file_hash(backup.path)
            if current_hash != backup.hash_sha256:
                logger.error("Backup integrity check failed - file may be corrupted / Проверка целостности бэкапа не пройдена - файл может быть повреждён / Перевірку цілісності бекапу не пройдено - файл може бути пошкоджено")
                return False

            # Create backup of current master before restore (just in case)
            if os.path.exists(MASTER_FILE):
                self.create_backup(version="pre_restore")

            # Restore backup
            shutil.copy2(backup.path, MASTER_FILE)
            
            # Set secure permissions
            if sys.platform != "win32":
                os.chmod(MASTER_FILE, 0o600)
                
            logger.info(f"Master password restored from backup: {backup.path} / Мастер-пароль восстановлен из бэкапа: {backup.path} / Майстер-пароль відновлено з бекапу: {backup.path}")
            return True

        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to restore from backup / Ошибка восстановления из бэкапа / Помилка відновлення з бекапу: {e}")
            return False

    def get_backups(self) -> List[Dict[str, Any]]:
        """Get list of available backups / Получить список доступных бэкапов / Отримати список доступних бекапів"""
        self._load_backups()  # Refresh backup list
        return [b.to_dict() for b in self._backups]

    def get_backup_count(self) -> int:
        """Get number of available backups / Получить количество доступных бэкапов / Отримати кількість доступних бекапів"""
        return len(self._backups)

    def has_backups(self) -> bool:
        """Check if any backups exist / Проверить, существуют ли бэкапы / Перевірити, чи існують бекапи"""
        return len(self._backups) > 0

    def delete_backup(self, backup_index: int) -> bool:
        """Delete a specific backup / Удалить конкретный бэкап / Видалити конкретний бекап"""
        if backup_index >= len(self._backups):
            return False

        backup = self._backups[backup_index]
        try:
            os.remove(backup.path)
            self._backups.pop(backup_index)
            logger.info(f"Deleted backup: {backup.path} / Удалён бэкап: {backup.path} / Видалено бекап: {backup.path}")
            return True
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to delete backup / Ошибка удаления бэкапа / Помилка видалення бекапу: {e}")
            return False

    def verify_backup_integrity(self, backup_index: int = 0) -> Tuple[bool, str]:
        """
        Verify integrity of a backup file.
        
        Returns:
            (is_valid, message) / (is_valid, сообщение) / (is_valid, повідомлення)
        """
        if backup_index >= len(self._backups):
            return False, "Backup not found / Бэкап не найден / Бекап не знайдено"

        backup = self._backups[backup_index]
        
        if not os.path.exists(backup.path):
            return False, "Backup file does not exist / Файл бэкапа не существует / Файл бекапу не існує"

        current_hash = self._calculate_file_hash(backup.path)
        if current_hash is None:
            return False, "Failed to calculate hash / Ошибка вычисления хеша / Помилка обчислення хеша"

        if current_hash != backup.hash_sha256:
            return False, "Hash mismatch - backup may be corrupted / Несоответствие хеша - бэкап может быть повреждён / Невідповідність хеша - бекап може бути пошкоджено"

        # Try to read the file (basic validation)
        try:
            content = _secure_read(backup.path)
            if content is None or len(content) == 0:
                return False, "Backup file is empty / Файл бэкапа пуст / Файл бекапу порожній"
        except (OSError, IOError, PermissionError) as e:
            return False, f"Cannot read backup / Не удалось прочитать бэкап / Не вдалося прочитати бекап: {e}"

        return True, "Backup integrity verified / Целостность бэкапа подтверждена / Цілісність бекапу підтверджено"

    # ==================== EMERGENCY RECOVERY ====================

    def emergency_reset(self) -> bool:
        """
        Emergency reset of master password system.
        WARNING: This will delete ALL master password data including backup codes!
        
        Returns:
            True if reset successful
        """
        try:
            # Delete master file
            if os.path.exists(MASTER_FILE):
                # Overwrite with random data before deletion
                try:
                    size = os.path.getsize(MASTER_FILE)
                    if 0 < size < 1024 * 1024:
                        with open(MASTER_FILE, 'wb') as f:
                            for _ in range(3):
                                f.write(os.urandom(size))
                                f.flush()
                                f.seek(0)
                except (OSError, IOError, PermissionError):
                    pass
                os.remove(MASTER_FILE)

            # Delete recovery codes
            if os.path.exists(RECOVERY_CODES_FILE):
                os.remove(RECOVERY_CODES_FILE)

            # Delete all backups
            for backup in self._backups:
                try:
                    os.remove(backup.path)
                except (OSError, IOError, PermissionError):
                    pass
            self._backups.clear()

            # Reset in-memory state
            self._recovery_codes.clear()

            logger.warning("Emergency reset of master password system completed / Аварийный сброс системы мастер-пароля выполнен / Аварійне скидання системи майстер-пароля виконано")
            return True

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Emergency reset failed / Ошибка аварийного сброса / Помилка аварійного скидання: {e}")
            return False


# ==================== SINGLETON INSTANCE ====================

_recovery_manager = None

def get_recovery_manager() -> MasterRecovery:
    """Get the global recovery manager instance / Получить глобальный экземпляр менеджера восстановления / Отримати глобальний екземпляр менеджера відновлення"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = MasterRecovery()
    return _recovery_manager


# ==================== CONVENIENCE FUNCTIONS ====================

def generate_recovery_codes(count: int = RECOVERY_CODES_COUNT,
                           length: int = RECOVERY_CODE_LENGTH) -> List[str]:
    """Generate new recovery codes / Сгенерировать новые резервные коды / Згенерувати нові резервні коди"""
    return get_recovery_manager().generate_recovery_codes(count, length)

def verify_recovery_code(code: str) -> bool:
    """Verify and consume a recovery code / Проверить и использовать резервный код / Перевірити та використати резервний код"""
    return get_recovery_manager().verify_recovery_code(code)

def get_recovery_codes_status() -> Dict[str, Any]:
    """Get recovery codes status / Получить статус резервных кодов / Отримати статус резервних кодів"""
    return get_recovery_manager().get_recovery_codes_status()

def clear_recovery_codes() -> bool:
    """Clear all recovery codes / Очистить все резервные коды / Очистити всі резервні коди"""
    return get_recovery_manager().clear_recovery_codes()

def create_master_backup(version: str = "unknown") -> Optional[str]:
    """Create a backup of the master password file / Создать бэкап файла мастер-пароля / Створити бекап файлу майстер-пароля"""
    return get_recovery_manager().create_backup(version)

def restore_master_from_backup(backup_index: int = 0) -> bool:
    """Restore master password from backup / Восстановить мастер-пароль из бэкапа / Відновити майстер-пароль з бекапу"""
    return get_recovery_manager().restore_from_backup(backup_index)

def get_master_backups() -> List[Dict[str, Any]]:
    """Get list of available backups / Получить список доступных бэкапов / Отримати список доступних бекапів"""
    return get_recovery_manager().get_backups()

def has_master_backups() -> bool:
    """Check if any backups exist / Проверить, существуют ли бэкапы / Перевірити, чи існують бекапи"""
    return get_recovery_manager().has_backups()

def emergency_master_reset() -> bool:
    """Emergency reset of master password system / Аварийный сброс системы мастер-пароля / Аварійне скидання системи майстер-пароля"""
    return get_recovery_manager().emergency_reset()

def verify_master_backup(backup_index: int = 0) -> Tuple[bool, str]:
    """Verify integrity of a backup file / Проверить целостность файла бэкапа / Перевірити цілісність файлу бекапу"""
    return get_recovery_manager().verify_backup_integrity(backup_index)


__all__ = [
    'MasterRecovery',
    'get_recovery_manager',
    'generate_recovery_codes',
    'verify_recovery_code',
    'get_recovery_codes_status',
    'clear_recovery_codes',
    'create_master_backup',
    'restore_master_from_backup',
    'get_master_backups',
    'has_master_backups',
    'emergency_master_reset',
    'verify_master_backup',
    'RECOVERY_CODES_COUNT',
    'RECOVERY_CODE_LENGTH',
    'MAX_BACKUPS',
    'BACKUP_RETENTION_DAYS',
]