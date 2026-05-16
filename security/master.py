"""
Master password management with Argon2id
"""
import os
import sys
import ctypes
import hashlib
import hmac
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(_BASE_DIR, "data")
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")
# =============================================================

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32)


def _hide_dir(path: str) -> None:
    """Скрывает папку на Windows (атрибут Hidden)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


class MasterPassword:
    """Master password handler with Argon2id hashing"""

    MAX_ATTEMPTS = 5
    SALT_SIZE = 32
    PBKDF2_ITERATIONS = 600000
    USE_ARGON2 = True

    @classmethod
    def _derive_key_pbkdf2(cls, password: bytes, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', password, salt, cls.PBKDF2_ITERATIONS, dklen=32)

    @classmethod
    def _hash_argon2(cls, password: str) -> str:
        return _ph.hash(password)

    @classmethod
    def _verify_argon2(cls, password: str, stored_hash: str) -> bool:
        try:
            _ph.verify(stored_hash, password)
            return True
        except VerifyMismatchError:
            return False

    @classmethod
    def is_set(cls) -> bool:
        return os.path.exists(MASTER_FILE)

    @classmethod
    def verify(cls, password: str) -> bool:
        if not cls.is_set():
            return True
        try:
            with open(MASTER_FILE, 'rb') as f:
                version = f.read(1)
                if version == b'\x02':
                    stored_hash = f.read().decode('utf-8')
                    return cls._verify_argon2(password, stored_hash)
                else:
                    salt = f.read(cls.SALT_SIZE)
                    stored_hash = f.read()
                    derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
                    return hmac.compare_digest(derived, stored_hash)
        except Exception:
            return False

    @classmethod
    def set_password(cls, password: str) -> None:
        if not password:
            raise ValueError("Master password must not be empty")

        os.makedirs(CONFIG_DIR, exist_ok=True)
        _hide_dir(CONFIG_DIR)          # скрываем сразу после создания

        if cls.USE_ARGON2:
            hashed = cls._hash_argon2(password)
            with open(MASTER_FILE, 'wb') as f:
                f.write(b'\x02')
                f.write(hashed.encode('utf-8'))
        else:
            salt = secrets.token_bytes(cls.SALT_SIZE)
            derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
            with open(MASTER_FILE, 'wb') as f:
                f.write(b'\x01')
                f.write(salt)
                f.write(derived)

    @classmethod
    def remove(cls) -> None:
        try:
            os.remove(MASTER_FILE)
        except Exception:
            pass
