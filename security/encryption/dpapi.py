"""
Windows DPAPI (hardware-backed) encryption helpers.
Вспомогательные функции Windows DPAPI.
Допоміжні функції Windows DPAPI.
"""
from __future__ import annotations
import sys
import ctypes
from typing import Optional

from utils.logger import get_logger

logger = get_logger("encryption.dpapi")

_DPAPI_AVAILABLE = False  # updated to True below if the ctypes setup succeeds

# ── Windows DPAPI setup ───────────────────────────────────────
# DPAPI (Data Protection API) is a Windows OS service that encrypts
# data using a key derived from the current user's login credentials
# and (optionally) the machine's TPM.  This means:
#   • No explicit key management — Windows handles it
#   • Ciphertext is automatically bound to the Windows user account
#   • Moving the encrypted file to another machine or user fails to decrypt
#
# We access it via ctypes rather than win32crypt to avoid a dependency
# on the pywin32 package which requires a separate installer.
# Only set up on Windows
if sys.platform == "win32":
    try:
        import ctypes.wintypes

        class DATA_BLOB(ctypes.Structure):
            """
            Data blob class.
            Класс DATA BLOB.
            Клас DATA BLOB.
            """
            _fields_ = [
                ("cbData", ctypes.wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char)),
            ]

        _crypt32  = ctypes.windll.crypt32
        _kernel32 = ctypes.windll.kernel32

        _crypt32.CryptProtectData.argtypes = [
            ctypes.POINTER(DATA_BLOB), ctypes.c_wchar_p,
            ctypes.POINTER(DATA_BLOB), ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(DATA_BLOB),
        ]
        _crypt32.CryptProtectData.restype = ctypes.c_bool

        _crypt32.CryptUnprotectData.argtypes = [
            ctypes.POINTER(DATA_BLOB), ctypes.POINTER(ctypes.c_wchar_p),
            ctypes.POINTER(DATA_BLOB), ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(DATA_BLOB),
        ]
        _crypt32.CryptUnprotectData.restype = ctypes.c_bool

        _DPAPI_AVAILABLE = True
        logger.info("DPAPI available for hardware-backed encryption")
    except (ImportError, AttributeError, OSError, TypeError) as e:
        logger.debug("DPAPI not available: %s", e)


# ── DATA_BLOB helper ─────────────────────────────────────────
# CryptProtectData / CryptUnprotectData both work with the Windows
# DATA_BLOB structure: {cbData: DWORD, pbData: BYTE*}.
# We create matching ctypes Structures so ctypes can marshal them.

def dpapi_encrypt(data: bytes) -> Optional[bytes]:
    """Encrypt *data* using Windows DPAPI.
    Шифрует данные с помощью Windows DPAPI.
    Шифрує дані за допомогою Windows DPAPI."""
    if not _DPAPI_AVAILABLE:
        return None
    try:
        blob_in = DATA_BLOB()
        blob_in.cbData = len(data)
        blob_in.pbData = ctypes.cast(
            ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_char))
        blob_out = DATA_BLOB()
        # Flags=0: use current user credentials (no extra entropy, no UI prompt).
        # Pass None for all optional parameters (description, entropy, prompt).
        if _crypt32.CryptProtectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            # MUST free the output buffer allocated by CryptProtectData
            # with LocalFree — not free() or del.  Failure leaks kernel memory.
            _kernel32.LocalFree(blob_out.pbData)
            return result
    except (OSError, TypeError, ValueError, AttributeError) as e:
        logger.error("DPAPI encrypt error: %s", e)
    return None

# Keep private alias
_dpapi_encrypt = dpapi_encrypt


def dpapi_decrypt(encrypted_data: bytes) -> Optional[bytes]:
    """Decrypt *encrypted_data* using Windows DPAPI.
    Дешифрует данные с помощью Windows DPAPI.
    Дешифрує дані за допомогою Windows DPAPI."""
    if not _DPAPI_AVAILABLE:
        return None
    try:
        blob_in = DATA_BLOB()
        blob_in.cbData = len(encrypted_data)
        blob_in.pbData = ctypes.cast(
            ctypes.create_string_buffer(encrypted_data), ctypes.POINTER(ctypes.c_char))
        blob_out = DATA_BLOB()
        if _crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
        ):
            result = ctypes.string_at(blob_out.pbData, blob_out.cbData)
            _kernel32.LocalFree(blob_out.pbData)
            return result
    except (OSError, TypeError, ValueError, AttributeError) as e:
        logger.error("DPAPI decrypt error: %s", e)
    return None

# Keep private alias
_dpapi_decrypt = dpapi_decrypt
