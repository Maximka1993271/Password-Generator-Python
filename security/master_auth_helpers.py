"""
Master password authentication - Helper functions
100% ORIGINAL CODE - DO NOT MODIFY (except security fixes)
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ (кроме исправлений безопасности)
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ (крім виправлень безпеки)
"""
from __future__ import annotations

import os
import sys
import ctypes
import hashlib
import hmac
import secrets
import tempfile
import json
import platform
import socket
import uuid
from typing import Optional
from datetime import datetime

from security.master_auth_constants import (
    CONFIG_DIR, LOCKOUT_FILE, RECOVERY_CODE_HASH_PREFIX, RECOVERY_CODE_HASH_ITERATIONS,
    RECOVERY_CODE_SALT_BYTES, DEFAULT_MAX_ATTEMPTS, MAX_ATTEMPTS
)

from utils.logger import get_logger

logger = get_logger("master_auth")


def _hide_dir(path: str) -> None:
    """Hide directory on Windows / Скрыть директорию на Windows / Приховати директорію на Windows"""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except (AttributeError, OSError, TypeError) as e:
            logger.debug(f"Hide dir failed / Ошибка скрытия директории / Помилка приховування директорії: {e}")


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


def _get_device_fingerprint() -> str:
    """Get unique device fingerprint for trusted device tracking.
    Получить уникальный отпечаток устройства для отслеживания доверенных устройств.
    Отримати унікальний відбиток пристрою для відстеження довірених пристроїв."""
    try:
        identifiers = []

        try:
            identifiers.append(platform.node())
        except (OSError, PermissionError, FileNotFoundError, ConnectionError) as e:
            logger.debug(f"Hostname detection error / Ошибка определения hostname / Помилка визначення hostname: {e}")
            identifiers.append("unknown_host")

        try:
            identifiers.append(platform.machine())
        except (OSError, PermissionError, FileNotFoundError) as e:
            logger.debug(f"Machine type detection error / Ошибка определения типа машины / Помилка визначення типу машини: {e}")
            identifiers.append("unknown_machine")

        identifiers.append(sys.platform)

        mac = None
        try:
            mac = uuid.getnode()
            if mac and mac != 0xffffffffffff:
                identifiers.append(f"mac_{mac:x}")
        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.debug(f"MAC detection error / Ошибка определения MAC / Помилка визначення MAC: {e}")

        if mac is None or mac == 0xffffffffffff:
            try:
                import netifaces
                for iface in netifaces.interfaces():
                    try:
                        addrs = netifaces.ifaddresses(iface)
                        if netifaces.AF_LINK in addrs:
                            for addr in addrs[netifaces.AF_LINK]:
                                if 'addr' in addr and addr['addr'] != '00:00:00:00:00:00':
                                    mac = addr['addr'].replace(':', '')
                                    identifiers.append(f"mac_{mac}")
                                    break
                        if mac:
                            break
                    except (ValueError, KeyError, OSError, AttributeError):
                        continue
            except ImportError:
                pass

        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
                install_date, _ = winreg.QueryValueEx(key, "InstallDate")
                winreg.CloseKey(key)
                identifiers.append(f"win_install_{install_date}")
            except (ImportError, OSError, WindowsError, TypeError, ValueError, OSError) as e:
                logger.debug(f"Windows install date detection error / Ошибка определения даты установки Windows / Помилка визначення дати встановлення Windows: {e}")
        else:
            try:
                machine_id_paths = ["/etc/machine-id", "/var/lib/dbus/machine-id"]
                for path in machine_id_paths:
                    if os.path.exists(path):
                        with open(path, 'r') as f:
                            machine_id = f.read().strip()
                            if machine_id:
                                identifiers.append(f"machine_id_{machine_id[:16]}")
                                break
            except (OSError, IOError, PermissionError) as e:
                logger.debug(f"Machine ID detection error / Ошибка определения ID машины / Помилка визначення ID машини: {e}")

        try:
            identifiers.append(platform.processor() or "unknown_processor")
        except (OSError, AttributeError) as e:
            logger.debug(f"Processor detection error / Ошибка определения процессора / Помилка визначення процесора: {e}")
            identifiers.append("unknown_processor")

        identifiers = [str(i) for i in identifiers if i]

        fingerprint_string = "|".join(identifiers)
        result = hashlib.sha256(fingerprint_string.encode('utf-8')).hexdigest()[:32]
        logger.debug(f"Device fingerprint generated (length: {len(result)}) / Отпечаток устройства сгенерирован (длина: {len(result)}) / Відбиток пристрою згенеровано (довжина: {len(result)})")
        return result

    except (OSError, ValueError, TypeError, AttributeError) as e:
        logger.error(f"Device fingerprint error / Ошибка отпечатка устройства / Помилка відбитку пристрою: {e}")
        return hashlib.sha256(str(uuid.uuid4()).encode('utf-8')).hexdigest()[:32]


def _get_ip_address() -> str:
    """Get local IP address / Получить локальный IP-адрес / Отримати локальну IP-адресу"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError, AttributeError) as e:
        logger.debug(f"IP address detection error / Ошибка определения IP-адреса / Помилка визначення IP-адреси: {e}")
        return "unknown"


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


def _get_max_attempts_configurable() -> int:
    """Get configurable MAX_ATTEMPTS value.
    Получить настраиваемое значение MAX_ATTEMPTS.
    Отримати налаштовуване значення MAX_ATTEMPTS."""
    try:
        from core.app_settings import AppSettings as _AS
        config_max = _AS.instance().max_attempts
        if isinstance(config_max, int) and 3 <= config_max <= 10:
            return config_max
    except (ImportError, AttributeError, RuntimeError, PermissionError, FileNotFoundError) as e:
        logger.debug(f"Failed to read MAX_ATTEMPTS from config / Не удалось прочитать MAX_ATTEMPTS из конфига / Не вдалося прочитати MAX_ATTEMPTS з конфігу: {e}")
        pass
    return MAX_ATTEMPTS