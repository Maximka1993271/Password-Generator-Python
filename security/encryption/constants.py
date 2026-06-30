"""
Encryption constants and module-level configuration.
Константы шифрования и конфигурация модуля.
Константи шифрування та конфігурація модуля.
"""
from __future__ import annotations
import os
import sys

# SCrypt parameters for key derivation (balanced security/performance)
# Параметры SCrypt для вывода ключа (баланс безопасности/производительности)
# Параметри SCrypt для виведення ключа (баланс безпеки/продуктивності)
SCRYPT_N = 2**15       # CPU/memory cost factor (32 768 — 32 MB)
SCRYPT_R = 8           # Block size
SCRYPT_P = 1           # Parallelization factor

# Stronger SCrypt for master password (more memory-hard)
# Более сильные параметры для мастер-пароля
# Сильніші параметри для майстер-пароля
SCRYPT_MASTER_N = 2**16  # 65 536 — 64 MB
SCRYPT_MASTER_R = 8
SCRYPT_MASTER_P = 2

# Lighter SCrypt for SQLCipher (performance during DB operations)
# Ослабленные параметры для SQLCipher
# Ослаблені параметри для SQLCipher
SCRYPT_SQLCIPHER_N = 2**14  # 16 384 — 16 MB
SCRYPT_SQLCIPHER_R = 8
SCRYPT_SQLCIPHER_P = 1

# PBKDF2 fallback iterations
# Итерации PBKDF2 для fallback
# Ітерації PBKDF2 для fallback
PBKDF2_ITERATIONS = 600_000
PBKDF2_ITERATIONS_SQLCIPHER = 64_000

# Encrypted-value prefix markers
# Маркеры зашифрованных значений
# Маркери зашифрованих значень
ENC_PREFIX      = "enc1:"
FALLBACK_PREFIX = "enc2:"
DPAPI_PREFIX    = "enc3:"
ENC_VERSION     = 3
ENC_METADATA_SIZE = 4

# ── Paths / Пути / Шляхи ─────────────────────────────────────
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR             = os.path.join(_BASE_DIR, ".securepass", "data")
SALT_FILE            = os.path.join(DATA_DIR, "db.salt")
UUID_FILE            = os.path.join(DATA_DIR, "machine.id")
KEY_VERSION_FILE     = os.path.join(DATA_DIR, "key.version")
KEY_ROTATION_LOG     = os.path.join(DATA_DIR, "key_rotation.json")
SQLCIPHER_SALT_FILE  = os.path.join(DATA_DIR, "sqlcipher.salt")
