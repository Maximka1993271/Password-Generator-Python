"""
Master password authentication - Recovery codes
100% ORIGINAL CODE - DO NOT MODIFY
100% ОРИГИНАЛЬНЫЙ КОД - НЕ ИЗМЕНЯТЬ
100% ОРИГІНАЛЬНИЙ КОД - НЕ ЗМІНЮВАТИ
"""
from __future__ import annotations

import os
import json
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List

from security.master_auth_constants import RECOVERY_CODES_FILE, RECOVERY_CODES_COUNT, RECOVERY_CODE_LENGTH
from security.master_auth_helpers import _secure_write, _secure_read, _hash_recovery_code, _verify_recovery_code_hash
from security.master_auth_core import RecoveryCode

from utils.logger import get_logger

logger = get_logger("master_auth")


def _save_recovery_codes(cls) -> None:
    """Save recovery codes / Сохранить резервные коды / Зберегти резервні коди"""
    try:
        codes_data = {
            "codes": [c.to_dict() if hasattr(c, 'to_dict') else c for c in cls._recovery_codes],
            "last_update": datetime.now().isoformat()
        }
        _secure_write(RECOVERY_CODES_FILE, json.dumps(codes_data, indent=2).encode('utf-8'))
    except (OSError, IOError, PermissionError, TypeError) as e:
        logger.debug(f"Failed to save recovery codes / Ошибка сохранения резервных кодов / Помилка збереження резервних кодів: {e}")


def _load_recovery_codes(cls) -> None:
    """Load recovery codes / Загрузить резервные коды / Завантажити резервні коди"""
    if not os.path.exists(RECOVERY_CODES_FILE):
        return

    try:
        content = _secure_read(RECOVERY_CODES_FILE)
        if content:
            codes_data = json.loads(content.decode('utf-8'))
            codes = codes_data.get("codes", [])
            if isinstance(codes, list):
                cls._recovery_codes = codes
            logger.debug(f"Loaded {len(cls._recovery_codes)} recovery codes / Загружено {len(cls._recovery_codes)} резервных кодов / Завантажено {len(cls._recovery_codes)} резервних кодів")
    except (json.JSONDecodeError, OSError, IOError, UnicodeDecodeError, KeyError) as e:
        logger.debug(f"Failed to load recovery codes / Ошибка загрузки резервных кодов / Помилка завантаження резервних кодів: {e}")


def generate_recovery_codes(cls, count: int = RECOVERY_CODES_COUNT,
                            length: int = RECOVERY_CODE_LENGTH) -> List[str]:
    """Generate new recovery codes
    Сгенерировать новые резервные коды
    Згенерувати нові резервні коди"""
    try:
        codes = []
        for _ in range(count):
            code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
            code_formatted = f"{code[:4]}-{code[4:]}" if length == 8 else code

            recovery_code = RecoveryCode(
                code_hash=_hash_recovery_code(code),
                created_at=datetime.now().isoformat(),
                used=False
            )
            codes.append(code_formatted)
            cls._recovery_codes.append(recovery_code.to_dict())

        _save_recovery_codes(cls)
        logger.info(f"Generated {count} recovery codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
        return codes
    except (ValueError, TypeError, OSError, AttributeError) as e:
        logger.error(f"Failed to generate recovery codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")
        return []


def verify_recovery_code(cls, code: str) -> bool:
    """Verify and consume a recovery code
    Проверить и использовать резервный код
    Перевірити та використати резервний код"""
    try:
        code_clean = code.replace("-", "").replace(" ", "")

        for i, rc in enumerate(cls._recovery_codes):
            if not rc.get("used", False) and _verify_recovery_code_hash(code_clean, rc.get("code_hash", "")):
                rc["used"] = True
                rc["used_at"] = datetime.now().isoformat()
                _save_recovery_codes(cls)
                logger.info("Recovery code used successfully / Резервный код успешно использован / Резервний код успішно використано")
                return True

        logger.warning("Invalid or already used recovery code / Неверный или уже использованный резервный код / Невірний або вже використаний резервний код")
        return False
    except (ValueError, TypeError, OSError, AttributeError, KeyError) as e:
        logger.error(f"Recovery code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
        return False


def get_recovery_codes_status(cls) -> Dict[str, Any]:
    """Get recovery codes status
    Получить статус резервных кодов
    Отримати статус резервних кодів"""
    total = len(cls._recovery_codes)
    used = sum(1 for rc in cls._recovery_codes if rc.get("used", False))
    return {
        "total": total,
        "used": used,
        "available": total - used,
        "max_codes": RECOVERY_CODES_COUNT
    }


def clear_recovery_codes(cls) -> bool:
    """Clear all recovery codes
    Очистить все резервные коды
    Очистити всі резервні коди"""
    try:
        cls._recovery_codes.clear()
        _save_recovery_codes(cls)
        logger.info("Recovery codes cleared / Резервные коды очищены / Резервні коди очищено")
        return True
    except (OSError, IOError, PermissionError) as e:
        logger.error(f"Failed to clear recovery codes / Ошибка очистки резервных кодов / Помилка очищення резервних кодів: {e}")
        return False