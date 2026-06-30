"""
Core encrypt/decrypt operations (AES-GCM, fallback XOR-HMAC, DPAPI).
Основные операции шифрования/дешифрования.
Основні операції шифрування/дешифрування.

Wire-format layout
──────────────────
Every encrypted value is a prefix-tagged, Base64-encoded blob:

  enc1:<base64( 4B-header | 12B-nonce | AES-256-GCM-ciphertext )>
  enc2:<base64( 4B-header | 16B-nonce | 32B-HMAC-tag | XOR-stream )>
  enc3:<base64( 4B-header | DPAPI-blob )>

The 4-byte header (``>HH``) carries:
  bytes 0-1 → format version  (uint16 big-endian)
  bytes 2-3 → flags           (uint16 big-endian, reserved = 0)
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import os
import struct
from typing import Optional

from utils.logger import get_logger
from security.encryption.exceptions import (
    EncryptionError, TamperDetectedError, EncryptionVersionError,
)
from security.encryption.constants import (
    ENC_PREFIX, FALLBACK_PREFIX, DPAPI_PREFIX,
    ENC_VERSION, ENC_METADATA_SIZE,
)
from security.encryption.memory import (
    _clear_bytes, _clear_string,
)
from security.encryption.key_management import active_key as _active_key
from security.encryption.dpapi import _DPAPI_AVAILABLE, _dpapi_encrypt, _dpapi_decrypt

logger = get_logger("encryption.cipher")

# ── Optional AES-GCM from the cryptography package ────────────────
# We guard the import so the app can still run (with the XOR-HMAC
# fallback) even when the native cryptography wheel isn't installed.
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag
    _CRYPTO_OK = True
except ImportError:
    # Rare — normally installed via pip install cryptography
    _CRYPTO_OK = False
    InvalidTag = Exception  # type: ignore  # keeps except clauses valid

# ── Module-level prefix aliases (backward compat) ─────────────────
# The canonical values live in constants.py; these aliases let older
# import sites use the private names without changes.
_ENC_PREFIX        = ENC_PREFIX       # "enc1:" — AES-256-GCM
_FALLBACK_PREFIX   = FALLBACK_PREFIX  # "enc2:" — XOR-HMAC-SHA256
_DPAPI_PREFIX      = DPAPI_PREFIX     # "enc3:" — Windows DPAPI
_ENC_VERSION       = ENC_VERSION      # current format version
_ENC_METADATA_SIZE = ENC_METADATA_SIZE  # header size in bytes (4)


# ══════════════════════════════════════════════════════════════════
#  Header helpers
# ══════════════════════════════════════════════════════════════════

def _add_metadata(data: bytes, version: int = _ENC_VERSION, flags: int = 0) -> bytes:
    """Prepend a 4-byte tamper-evident header.
    Добавляет 4-байтный заголовок версии и флагов перед данными.
    Додає 4-байтний заголовок версії та прапорів перед даними."""
    try:
        # Pack two unsigned short (2 bytes each) in network (big-endian) order.
        # This gives us 65 535 possible versions and 16 flag bits — far more
        # than we'll ever need, but big-endian keeps the bytes human-readable
        # in a hex dump.
        return struct.pack(">HH", version, flags) + data
    except (struct.error, TypeError, ValueError) as e:
        raise EncryptionError(f"Metadata addition failed: {e}")


def _extract_metadata(data: bytes) -> tuple[bytes, int, int]:
    """Parse and remove the 4-byte header; return (payload, version, flags).
    Разбирает 4-байтный заголовок и возвращает (данные, версия, флаги).
    Розбирає 4-байтний заголовок і повертає (дані, версія, прапори)."""
    # Guard against truncated blobs — minimum viable blob is header + 1 byte
    if len(data) < _ENC_METADATA_SIZE:
        raise EncryptionVersionError("Data too short for metadata header")
    try:
        # Unpack each field individually to give clear error positions in tracebacks
        version = struct.unpack(">H", data[0:2])[0]  # bytes 0-1 → version
        flags   = struct.unpack(">H", data[2:4])[0]  # bytes 2-3 → flags
        return data[4:], version, flags               # slice off header, return payload
    except (struct.error, TypeError, ValueError, IndexError) as e:
        raise EncryptionVersionError(f"Metadata extraction failed: {e}")


# ══════════════════════════════════════════════════════════════════
#  Fallback cipher: XOR-HMAC-SHA256
# ══════════════════════════════════════════════════════════════════
# Used when the ``cryptography`` package is unavailable.
# Security properties:
#   • HMAC-SHA256(key, nonce‖ct) provides MAC-then-Encrypt authentication
#   • Counter-mode XOR stream avoids ECB block patterns
#   • 16-byte random nonce gives 2^128 nonce space — collision-resistant
#
# ⚠  This is NOT as strong as AES-256-GCM (no hardware acceleration,
#    slower, non-constant-time XOR loop).  Treat it as an emergency
#    fallback, not a primary cipher.

def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    """XOR-HMAC stream cipher used as a fallback.
    XOR-HMAC поток, используемый как запасной вариант.
    XOR-HMAC потік, що використовується як запасний варіант."""
    data_len = len(data)
    out      = bytearray(data_len)  # pre-allocate output buffer
    counter  = 0                     # block counter — incremented per HMAC block
    pos      = 0                     # current write position in output
    try:
        while pos < data_len:
            # Derive one keystream block: HMAC-SHA256(key, nonce ‖ counter).
            # Each block is 32 bytes (SHA-256 output size).
            # Counter is encoded as 8 bytes big-endian for unambiguous parsing.
            keystream  = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()

            # XOR at most one full block, or whatever bytes remain
            chunk_size = min(len(keystream), data_len - pos)
            for i in range(chunk_size):
                out[pos + i] = data[pos + i] ^ keystream[i]

            pos     += chunk_size
            counter += 1  # advance block counter for next iteration
        return bytes(out)
    except (TypeError, ValueError, MemoryError, OverflowError) as e:
        raise EncryptionError(f"XOR encryption failed: {e}")
    finally:
        # Always wipe the key from memory, even on exceptions
        _clear_bytes(key)


def _encrypt_fallback(plaintext: str, key: bytes) -> str:
    """Encrypt using XOR-HMAC fallback.
    Шифрование через XOR-HMAC запасной вариант.
    Шифрування через XOR-HMAC запасний варіант."""
    try:
        # 16-byte random nonce: unique per encryption, never reused
        nonce = os.urandom(16)

        # Encrypt: XOR plaintext with keystream derived from (key, nonce)
        ct = _xor_stream(plaintext.encode("utf-8"), key, nonce)

        # Authenticate: HMAC(key, nonce ‖ ciphertext) — covers both nonce
        # and ct so an attacker can't swap them independently
        tag = hmac.new(key, nonce + ct, hashlib.sha256).digest()

        # Wire format: nonce(16) | tag(32) | ciphertext(variable)
        encrypted = nonce + tag + ct

        # Prepend version header and Base64-encode the whole blob
        enc_meta = _add_metadata(encrypted, version=1, flags=0)
        result   = _FALLBACK_PREFIX + base64.b64encode(enc_meta).decode("ascii")

        # Wipe sensitive intermediate values before returning
        _clear_bytes(ct)
        _clear_bytes(tag)
        _clear_string(plaintext)
        return result
    except (TypeError, ValueError, MemoryError, OSError, struct.error) as e:
        raise EncryptionError(f"Fallback encryption failed: {e}")


def _decrypt_fallback(value: str, key: bytes) -> str:
    """Decrypt XOR-HMAC ciphertext.
    Дешифрование XOR-HMAC.
    Дешифрування XOR-HMAC."""
    # Pre-declare so the finally block can always wipe them
    ct = tag = expected = b""
    try:
        # Strip the "enc2:" prefix before decoding
        raw = base64.b64decode(value[len(_FALLBACK_PREFIX):], validate=True)

        # Strip the 4-byte metadata header added during encryption
        encrypted, _version, _flags = _extract_metadata(raw)

        # Minimum size check: 16B nonce + 32B tag = 48 bytes mandatory
        if len(encrypted) < 48:
            raise ValueError("Invalid encrypted value length")

        # Split the wire layout back into components
        nonce = encrypted[:16]       # bytes  0–15: random nonce
        tag   = encrypted[16:48]     # bytes 16–47: HMAC-SHA256 authentication tag
        ct    = encrypted[48:]       # bytes 48+  : XOR-stream ciphertext

        # ── Constant-time authentication check (MAC-then-decrypt) ──────
        # We MUST verify the MAC *before* decrypting to prevent chosen-
        # ciphertext attacks. hmac.compare_digest avoids timing side-channels.
        expected = hmac.new(key, nonce + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            # Raise before doing any decryption work to keep the attacker blind
            raise TamperDetectedError("Authentication failed — possible tampering")

        # Authentication passed — safe to decrypt
        return _xor_stream(ct, key, nonce).decode("utf-8")

    except (base64.binascii.Error, ValueError, UnicodeDecodeError, TypeError,
            struct.error, EncryptionVersionError) as e:
        raise EncryptionError(f"Invalid encrypted data: {e}") from e
    except TamperDetectedError:
        raise  # propagate without wrapping
    finally:
        # Wipe every sensitive buffer regardless of success or exception
        _clear_bytes(ct)
        _clear_bytes(tag)
        _clear_bytes(expected)
        _clear_bytes(key)


# ══════════════════════════════════════════════════════════════════
#  Windows DPAPI (hardware-backed)
# ══════════════════════════════════════════════════════════════════

def _encrypt_hardware(plaintext: str) -> str:
    """Encrypt via DPAPI (falls back to XOR-HMAC if unavailable).
    Шифрует через DPAPI.
    Шифрує через DPAPI."""
    if _DPAPI_AVAILABLE:
        try:
            # DPAPI binds the ciphertext to the current Windows user account
            # and (optionally) machine. No explicit key needed — Windows manages it.
            encrypted = _dpapi_encrypt(plaintext.encode("utf-8"))
            if encrypted:
                # Tag with version=2, flags=1 (bit-0 = "DPAPI was used")
                enc_meta = _add_metadata(encrypted, version=2, flags=1)
                result   = _DPAPI_PREFIX + base64.b64encode(enc_meta).decode("ascii")
                _clear_string(plaintext)
                return result
        except (OSError, TypeError, ValueError, AttributeError, struct.error) as e:
            # DPAPI can fail if the user's profile is corrupt or the machine key
            # changes (e.g. after re-imaging).  Log and fall through to XOR-HMAC.
            logger.error("Hardware encryption error: %s", e)

    # Fallback: use the machine-derived key so the value is at least tied to
    # this installation even without DPAPI
    from security.encryption.key_management import _get_machine_key
    return _encrypt_fallback(plaintext, bytes(_get_machine_key()))


def _decrypt_hardware(value: str) -> str:
    """Decrypt DPAPI ciphertext.
    Дешифрует DPAPI шифротекст.
    Дешифрує DPAPI шифротекст."""
    try:
        if value.startswith(_DPAPI_PREFIX):
            # Decode and strip our custom header before passing to DPAPI
            raw = base64.b64decode(value[len(_DPAPI_PREFIX):])
            encrypted, _version, _flags = _extract_metadata(raw)

            # DPAPI does the actual decryption — it validates the Windows user
            # context internally and returns None on failure
            decrypted = _dpapi_decrypt(encrypted)
            if decrypted:
                return decrypted.decode("utf-8")
    except (base64.binascii.Error, ValueError, UnicodeDecodeError, TypeError,
            EncryptionVersionError) as e:
        raise EncryptionError(f"Hardware decryption failed: {e}") from e
    raise EncryptionError("Hardware decryption failed")


# ══════════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════════

def encrypt(plaintext: str, use_hardware: bool = False) -> str:
    """Encrypt *plaintext* and return a portable encoded string.

    Uses AES-256-GCM when the ``cryptography`` library is available,
    or falls back to XOR-HMAC-SHA256. Optionally delegates to
    Windows DPAPI (hardware-backed) when *use_hardware* is True.

    Шифрует строку и возвращает переносимый закодированный результат.
    Шифрує рядок і повертає переносний закодований результат.

    Args:
        plaintext (str): The plaintext string to encrypt.
        use_hardware (bool): If True and DPAPI is available,
            use Windows hardware-backed encryption.

    Returns:
        str: Encoded ciphertext with a version prefix
            (``enc1:…``, ``enc2:…``, or ``enc3:…``).

    Raises:
        EncryptionError: If encryption fails.
        TamperDetectedError: If authentication fails during
            a decrypt-then-re-encrypt path.
    """
    # Short-circuit: empty string stays empty — avoids wasting entropy
    if not plaintext:
        return ""

    # ── Route to the appropriate cipher ───────────────────────────
    # Priority: DPAPI (hardware) > AES-256-GCM > XOR-HMAC fallback
    if use_hardware and _DPAPI_AVAILABLE:
        return _encrypt_hardware(plaintext)

    # Derive the active session key (master-derived or machine fallback)
    key = bytes(_active_key())

    # If the cryptography wheel isn't installed, drop to the pure-Python fallback
    if not _CRYPTO_OK:
        return _encrypt_fallback(plaintext, key)

    # ── AES-256-GCM (primary path) ────────────────────────────────
    aesgcm     = AESGCM(key)           # initialise with 256-bit key
    nonce      = os.urandom(12)        # 96-bit random nonce (GCM recommendation)
    ciphertext = None
    try:
        # AES-256-GCM produces: ciphertext ‖ 16-byte authentication tag
        # We pass None as AAD (no additional authenticated data needed here)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

        # Prepend 4-byte header then Base64-encode: nonce(12) | ct+tag(variable)
        enc_meta = _add_metadata(nonce + ciphertext, version=3, flags=0)
        return _ENC_PREFIX + base64.b64encode(enc_meta).decode("ascii")

    except InvalidTag as e:
        # GCM authentication failure during encrypt is extremely rare but possible
        # if the library implementation is defective
        raise TamperDetectedError(f"Encryption authentication failed: {e}")
    except (TypeError, ValueError, MemoryError, RuntimeError, struct.error) as e:
        raise EncryptionError(f"Encryption failed: {e}")
    finally:
        # ── Mandatory memory wipe ──────────────────────────────────
        # These run even if an exception propagates, preventing key material
        # from lingering in memory (important in a long-running GUI process)
        _clear_bytes(key)
        _clear_string(plaintext)
        if ciphertext:
            _clear_bytes(ciphertext)


def decrypt(value: str) -> str:
    """Decrypt *value* and return the original plaintext.

    Recognises ``enc1:`` (AES-GCM), ``enc2:`` (XOR-HMAC) and
    ``enc3:`` (DPAPI) prefixes. Unrecognised strings are returned
    as-is (allowing transparent use on already-plain values).

    Дешифрует строку; нераспознанные строки возвращаются как есть.
    Дешифрує рядок; нерозпізнані рядки повертаються як є.

    Args:
        value (str): The encoded ciphertext, or a plain string.

    Returns:
        str: Decrypted plaintext, or *value* unchanged.

    Raises:
        EncryptionError: If decryption fails for a known prefix.
        TamperDetectedError: If the authentication tag is invalid.
    """
    # Empty string fast-path
    if not value:
        return ""

    # ── Prefix detection — return plain strings unchanged ─────────
    # This allows callers to pass any string without knowing whether
    # it is encrypted, simplifying the read path for database fields
    # that might not have been encrypted in older schema versions.
    if (not value.startswith(_ENC_PREFIX)
            and not value.startswith(_FALLBACK_PREFIX)
            and not value.startswith(_DPAPI_PREFIX)):
        return value

    # Derive the active session key once — shared across all dispatch paths
    key    = bytes(_active_key())
    result = value  # initialise so the finally block has a valid reference

    try:
        # ── Dispatch by prefix ────────────────────────────────────
        if value.startswith(_DPAPI_PREFIX):
            # "enc3:" — Windows hardware-backed decryption
            result = _decrypt_hardware(value)
            return result

        if value.startswith(_FALLBACK_PREFIX):
            # "enc2:" — XOR-HMAC-SHA256 software fallback
            result = _decrypt_fallback(value, key)
            return result

        # ── AES-256-GCM (primary, "enc1:") ────────────────────────
        if not _CRYPTO_OK:
            # cryptography wheel missing — can't decrypt GCM blobs.
            # Return the raw value rather than raising so the UI degrades
            # gracefully (the field will show the ciphertext, not crash).
            logger.warning("Cryptography not available, cannot decrypt AES-GCM")
            return value

        # Strip "enc1:" prefix and Base64-decode the blob
        raw_b64 = value[len(_ENC_PREFIX):]
        data    = base64.b64decode(raw_b64)

        # Remove our custom 4-byte metadata header
        encrypted, _version, _flags = _extract_metadata(data)

        # Sanity check: minimum AES-GCM blob is 12B nonce + 16B tag = 28B
        if len(encrypted) < 12:
            raise ValueError("Invalid encrypted data length")

        # Split nonce from ciphertext+tag
        nonce, ct = encrypted[:12], encrypted[12:]

        # AES-256-GCM authentication + decryption in a single call.
        # Raises InvalidTag automatically if the tag doesn't match
        # (i.e. data was altered or the wrong key is being used).
        aesgcm = AESGCM(key)
        result = aesgcm.decrypt(nonce, ct, None).decode("utf-8")
        return result

    except InvalidTag as e:
        # Wrong key or tampered ciphertext — surface as TamperDetectedError
        # so callers can distinguish "bad data" from "bad format"
        raise TamperDetectedError("Authentication failed — data may have been tampered") from e
    except (base64.binascii.Error, ValueError, UnicodeDecodeError, TypeError,
            EncryptionVersionError, struct.error) as e:
        raise EncryptionError(f"Decryption failed: {e}") from e
    finally:
        # Wipe the key copy from memory regardless of outcome
        _clear_bytes(key)
        # Wipe the plaintext result only when decryption actually changed it
        # (i.e. when a real decrypt happened, not the pass-through path)
        if result != value:
            _clear_string(value)
