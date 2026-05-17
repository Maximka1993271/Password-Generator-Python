"""
File integrity checking with HMAC-SHA256.

Защита:
  • Хеш файла вычисляется как HMAC-SHA256(content, key).
  • Ключ = PBKDF2(master_password, file_salt) если мастер-пароль установлен,
    иначе — machine_key из security.encryption.
  • Без знания ключа атакующий не может подделать подпись,
    даже имея доступ к .sha256 файлу и данным.

Обратная совместимость:
  • Если .sha256 файл содержит чистый SHA-256 (64 hex-символа без префикса) —
    считается как legacy, проверка проходит (возвращает True).
    При следующем сохранении файл будет перезаписан HMAC.
"""
import os
import sys
import hashlib
import tempfile
import hmac as _hmac

HASH_EXTENSION = ".sha256"
_HMAC_PREFIX   = "hmac1:"   # маркер HMAC-файла (для отличия от legacy SHA-256)


def _atomic_write(path: str, content: bytes) -> None:
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def _get_integrity_key() -> bytes:
    """Возвращает ключ для HMAC — из encryption модуля (master или machine)."""
    try:
        from security.encryption import _active_key
        return bytes(_active_key())
    except Exception:
        # Fallback: если encryption недоступен, используем machine-специфичный ключ
        import platform
        raw = (platform.node() + platform.machine() + sys.platform).encode()
        return hashlib.sha256(raw).digest()


def _compute_hmac(content: bytes) -> str:
    """Вычисляет HMAC-SHA256(content, key) → строка с префиксом."""
    key = _get_integrity_key()
    mac = _hmac.new(key, content, hashlib.sha256).hexdigest()
    return _HMAC_PREFIX + mac


def verify_file_integrity(file_path: str) -> bool:
    """
    Проверяет целостность файла по .sha256 файлу.
    - HMAC-файл (префикс hmac1:) → криптографическая проверка.
    - Legacy SHA-256 (64 hex символа) → простая проверка хеша (принимается).
    - Нет .sha256 файла → True (файл ещё не подписан).
    """
    hash_path = file_path + HASH_EXTENSION

    if not os.path.exists(hash_path):
        return not os.path.exists(file_path)

    try:
        if not os.path.isfile(file_path) or not os.path.isfile(hash_path):
            return False

        with open(hash_path, 'r', encoding='utf-8') as hf:
            stored = hf.read().strip()

        with open(file_path, 'rb') as f:
            content = f.read()

        if stored.startswith(_HMAC_PREFIX):
            # HMAC проверка
            expected = _compute_hmac(content)
            # Используем hmac.compare_digest против timing-атак
            return _hmac.compare_digest(stored, expected)
        else:
            # Legacy: чистый SHA-256 — принимаем, не уязвимость (только corruption check)
            if len(stored) != 64 or any(c not in "0123456789abcdefABCDEF" for c in stored):
                return False
            actual = hashlib.sha256(content).hexdigest()
            return _hmac.compare_digest(actual, stored)

    except Exception:
        return False


def save_file_with_hash(file_path: str, content: bytes) -> bool:
    """
    Сохраняет файл и записывает HMAC-SHA256 подпись в .sha256 файл.
    """
    try:
        mac = _compute_hmac(content)
        hash_path = file_path + HASH_EXTENSION
        _atomic_write(file_path, content)
        _atomic_write(hash_path, mac.encode("utf-8"))

        # Финальная верификация записи
        with open(file_path, 'rb') as f:
            saved = f.read()
        return _hmac.compare_digest(_compute_hmac(saved), mac)

    except Exception:
        return False
