"""
Master password management with Argon2id
"""
import os
import hashlib
import hmac
import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

# Constants
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".securepasspro")
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32)


class MasterPassword:
    """Master password handler with Argon2id hashing"""
    
    MAX_ATTEMPTS = 5
    SALT_SIZE = 32
    PBKDF2_ITERATIONS = 600000
    USE_ARGON2 = True
    
    @classmethod
    def _derive_key_pbkdf2(cls, password: bytes, salt: bytes) -> bytes:
        """PBKDF2 key derivation (legacy)"""
        return hashlib.pbkdf2_hmac('sha256', password, salt, cls.PBKDF2_ITERATIONS, dklen=32)
    
    @classmethod
    def _hash_argon2(cls, password: str) -> str:
        """Hash password using Argon2id"""
        return _ph.hash(password)
    
    @classmethod
    def _verify_argon2(cls, password: str, stored_hash: str) -> bool:
        """Verify Argon2id hash"""
        try:
            _ph.verify(stored_hash, password)
            return True
        except VerifyMismatchError:
            return False
    
    @classmethod
    def is_set(cls) -> bool:
        """Check if master password is set"""
        return os.path.exists(MASTER_FILE)
    
    @classmethod
    def verify(cls, password: str) -> bool:
        """Verify master password"""
        if not cls.is_set():
            return True
        
        try:
            with open(MASTER_FILE, 'rb') as f:
                version = f.read(1)
                if version == b'\x02':
                    # Argon2id format
                    stored_hash = f.read().decode('utf-8')
                    return cls._verify_argon2(password, stored_hash)
                else:
                    # PBKDF2 format (legacy)
                    salt = f.read(cls.SALT_SIZE)
                    stored_hash = f.read()
                    derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
                    return hmac.compare_digest(derived, stored_hash)
        except Exception:
            return False
    
    @classmethod
    def set_password(cls, password: str) -> None:
        """Set or update master password"""
        if not password:
            raise ValueError("Master password must not be empty")
        
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        if cls.USE_ARGON2:
            hashed = cls._hash_argon2(password)
            with open(MASTER_FILE, 'wb') as f:
                f.write(b'\x02')  # Version 2 = Argon2id
                f.write(hashed.encode('utf-8'))
        else:
            # Legacy PBKDF2 fallback
            salt = secrets.token_bytes(cls.SALT_SIZE)
            derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
            with open(MASTER_FILE, 'wb') as f:
                f.write(b'\x01')  # Version 1 = PBKDF2
                f.write(salt)
                f.write(derived)
    
    @classmethod
    def remove(cls) -> None:
        """Remove master password file"""
        try:
            os.remove(MASTER_FILE)
        except Exception:
            pass