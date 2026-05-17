"""
AES-256-GCM field-level encryption for password storage.

Схема ключей:
  • Мастер-пароль установлен и проверен →
      key = PBKDF2(master_password, salt, 600 000 итераций)
  • Мастер-пароль не установлен →
      key = PBKDF2(machine_id + random_uuid, salt, 200 000 итераций)
      random_uuid хранится в data/machine.id (создаётся один раз)

  Соль (data/db.salt) и UUID (data/machine.id) хранятся раздельно от БД.
  Зашифрованное значение = "enc1:" + base64(nonce[12] + ciphertext + GCM-tag[16]).
  Старые незашифрованные записи читаются прозрачно (обратная совместимость).
"""
from __future__ import annotations
import os
import sys
import base64
import ctypes
import hashlib
import hmac
import platform
import tempfile
import uuid as _uuid_mod
from typing import Optional

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes as _hashes
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False


class CryptoUnavailableError(RuntimeError):
    """Encryption is required but the cryptography package is unavailable."""

# ── Paths ─────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_DATA_DIR   = os.path.join(_BASE_DIR, "data")
_SALT_FILE  = os.path.join(_DATA_DIR, "db.salt")
_UUID_FILE  = os.path.join(_DATA_DIR, "machine.id")   # случайный UUID машины

# ── In-memory keys (bytes) ────────────────────────────────────────────────────
_master_key:  Optional[bytearray] = None   # ключ из мастер-пароля
_machine_key: Optional[bytearray] = None   # ключ из machine-id (fallback)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hide_dir(path: str) -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


def _ensure_data_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    _hide_dir(_DATA_DIR)


def _secure_write(path: str, data: bytes) -> None:
    _ensure_data_dir()
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
            except Exception:
                pass
        else:
            try:
                os.chmod(path, 0o600)
            except Exception:
                pass
    except Exception:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


def _zero(buf: Optional[bytearray]) -> None:
    """Обнуляет bytearray через ctypes.memset, чтобы ключ не остался в RAM."""
    if buf is None:
        return
    try:
        ctypes.memset(
            (ctypes.c_char * len(buf)).from_buffer(buf), 0, len(buf))
    except Exception:
        for i in range(len(buf)):
            buf[i] = 0


def _get_salt() -> bytes:
    if os.path.exists(_SALT_FILE):
        with open(_SALT_FILE, 'rb') as f:
            salt = f.read()
        if len(salt) != 32:
            raise ValueError("Invalid encryption salt")
        return salt
    _ensure_data_dir()
    salt = os.urandom(32)
    _secure_write(_SALT_FILE, salt)
    return salt


def _get_machine_uuid() -> str:
    """Возвращает случайный UUID, хранящийся в data/machine.id.
    Создаётся один раз при первом запуске — непредсказуем для атакующего."""
    if os.path.exists(_UUID_FILE):
        with open(_UUID_FILE, 'r', encoding='utf-8') as f:
            value = f.read().strip()
        try:
            _uuid_mod.UUID(value)
        except ValueError as exc:
            raise ValueError("Invalid machine id") from exc
        return value
    _ensure_data_dir()
    new_uuid = str(_uuid_mod.uuid4())
    _secure_write(_UUID_FILE, new_uuid.encode("utf-8"))
    return new_uuid


def _pbkdf2(secret: bytes, salt: bytes, iterations: int = 600_000) -> bytearray:
    if _CRYPTO_OK:
        kdf = PBKDF2HMAC(
            algorithm=_hashes.SHA256(),
            length=32, salt=salt, iterations=iterations)
        return bytearray(kdf.derive(secret))
    return bytearray(
        hashlib.pbkdf2_hmac('sha256', secret, salt, iterations, dklen=32))


def _get_machine_key() -> bytearray:
    global _machine_key
    if _machine_key is None:
        # Случайный UUID + стабильные параметры машины
        machine_str = (
            _get_machine_uuid() + "|" +
            platform.node() + "|" +
            platform.machine() + "|" +
            sys.platform
        )
        _machine_key = _pbkdf2(
            machine_str.encode('utf-8', errors='replace'),
            _get_salt(), iterations=200_000)
    return _machine_key


# ── Public API ────────────────────────────────────────────────────────────────
def set_key_from_master(master_password: str) -> None:
    """Вызвать после успешной проверки мастер-пароля."""
    global _master_key
    _zero(_master_key)
    _master_key = _pbkdf2(
        master_password.encode('utf-8'), _get_salt())


def clear_master_key() -> None:
    """Обнуляет ключ в памяти через ctypes.memset и удаляет ссылку."""
    global _master_key
    _zero(_master_key)
    _master_key = None


def _active_key() -> bytearray:
    return _master_key if _master_key is not None else _get_machine_key()


# ── Encrypt / Decrypt ─────────────────────────────────────────────────────────
_ENC_PREFIX = "enc1:"
_FALLBACK_PREFIX = "enc2:"


def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < len(data):
        counter_bytes = counter.to_bytes(8, "big")
        out.extend(hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest())
        counter += 1
    return bytes(a ^ b for a, b in zip(data, out))


def _encrypt_fallback(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(16)
    ct = _xor_stream(plaintext.encode("utf-8"), key, nonce)
    tag = hmac.new(key, nonce + ct, hashlib.sha256).digest()
    return _FALLBACK_PREFIX + base64.b64encode(nonce + tag + ct).decode("ascii")


def _decrypt_fallback(value: str, key: bytes) -> str:
    raw = base64.b64decode(value[len(_FALLBACK_PREFIX):], validate=True)
    if len(raw) < 48:
        raise ValueError("Invalid encrypted value")
    nonce, tag, ct = raw[:16], raw[16:48], raw[48:]
    expected = hmac.new(key, nonce + ct, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("Encrypted value authentication failed")
    return _xor_stream(ct, key, nonce).decode("utf-8")


def encrypt(plaintext: str) -> str:
    """Шифрует строку AES-256-GCM → "enc1:<base64>"."""
    key = bytes(_active_key())   # копируем bytearray → bytes для AESGCM
    if not _CRYPTO_OK:
        return _encrypt_fallback(plaintext, key)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    return _ENC_PREFIX + base64.b64encode(nonce + ct).decode('ascii')


def decrypt(value: str) -> str:
    """Дешифрует строку. Если не зашифрована — возвращает как есть."""
    if not value.startswith(_ENC_PREFIX) and not value.startswith(_FALLBACK_PREFIX):
        return value
    key = bytes(_active_key())
    if value.startswith(_FALLBACK_PREFIX):
        try:
            return _decrypt_fallback(value, key)
        except Exception:
            raise ValueError("Encrypted value authentication failed")
    if not _CRYPTO_OK:
        raise CryptoUnavailableError("cryptography package is required to decrypt AES-GCM values")
    raw_b64 = value[len(_ENC_PREFIX):]
    try:
        data = base64.b64decode(raw_b64)
        nonce, ct = data[:12], data[12:]
        return AESGCM(key).decrypt(nonce, ct, None).decode('utf-8')
    except Exception:
        raise ValueError("Encrypted value authentication failed")


def reencrypt_all(old_master: Optional[str], new_master: Optional[str]) -> None:
    """
    Перешифровывает все пароли в БД одной атомарной SQLite-транзакцией.
    При любой ошибке — полный откат, БД не повреждается.
    """
    import sqlite3
    from storage.database import DB_FILE, CONFIG_DIR

    global _master_key

    # 1. Старый ключ — читаем все записи (расшифровываем)
    if old_master:
        set_key_from_master(old_master)
    else:
        _zero(_master_key)
        _master_key = None

    if not os.path.exists(DB_FILE):
        return

    read_conn = sqlite3.connect(DB_FILE)
    try:
        rows = read_conn.execute("SELECT id, password FROM passwords ORDER BY id").fetchall()
    finally:
        read_conn.close()
    records = [{"id": row_id, "password": decrypt(password)} for row_id, password in rows]

    # 2. Новый ключ
    if new_master:
        set_key_from_master(new_master)
    else:
        _zero(_master_key)
        _master_key = None

    # 3. Атомарная перезапись
    os.makedirs(CONFIG_DIR, exist_ok=True)
    _hide_dir(CONFIG_DIR)
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute("BEGIN EXCLUSIVE")
        for r in records:
            conn.execute(
                "UPDATE passwords SET password=? WHERE id=?",
                (encrypt(r["password"]), r["id"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
