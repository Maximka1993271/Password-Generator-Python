"""
Master password management with Argon2id
"""
import os
import sys
import ctypes
import hashlib
import hmac
import secrets
import tempfile
try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ARGON2_OK = True
except ImportError:
    PasswordHasher = None
    VerifyMismatchError = VerificationError = InvalidHashError = Exception
    _ARGON2_OK = False

# ==================== PORTABLE PATH LOGIC ====================
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(_BASE_DIR, "data")
MASTER_FILE = os.path.join(CONFIG_DIR, "master.key")
# =============================================================

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32) if _ARGON2_OK else None


def _hide_dir(path: str) -> None:
    """Скрывает папку на Windows (атрибут Hidden)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


def _secure_write(path: str, data: bytes) -> None:
    """Write sensitive file atomically to avoid half-written master.key."""
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


class MasterPassword:
    """Master password handler with Argon2id hashing"""

    MAX_ATTEMPTS = 5
    SALT_SIZE = 32
    PBKDF2_ITERATIONS = 600000
    USE_ARGON2 = _ARGON2_OK

    @classmethod
    def _derive_key_pbkdf2(cls, password: bytes, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', password, salt, cls.PBKDF2_ITERATIONS, dklen=32)

    @classmethod
    def _hash_argon2(cls, password: str) -> str:
        if not _ARGON2_OK or _ph is None:
            raise RuntimeError("Argon2 is not available")
        return _ph.hash(password)

    @classmethod
    def _verify_argon2(cls, password: str, stored_hash: str) -> bool:
        try:
            if not _ARGON2_OK or _ph is None:
                return False
            _ph.verify(stored_hash, password)
            return True
        except (VerifyMismatchError, VerificationError, InvalidHashError):
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
                elif version == b'\x01':
                    salt = f.read(cls.SALT_SIZE)
                    stored_hash = f.read()
                    if len(salt) != cls.SALT_SIZE or len(stored_hash) != 32:
                        return False
                    derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
                    return hmac.compare_digest(derived, stored_hash)
                return False
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
            _secure_write(MASTER_FILE, b'\x02' + hashed.encode('utf-8'))
        else:
            salt = secrets.token_bytes(cls.SALT_SIZE)
            derived = cls._derive_key_pbkdf2(password.encode('utf-8'), salt)
            _secure_write(MASTER_FILE, b'\x01' + salt + derived)

    @classmethod
    def remove(cls) -> None:
        try:
            os.remove(MASTER_FILE)
        except Exception:
            pass

    @classmethod
    def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
        """Ask for the master password before the main window is created."""
        if not cls.is_set():
            return True

        try:
            import customtkinter as ctk
            from localization.lang import LANGUAGES
            from security.encryption import set_key_from_master
            from utils.helpers import center_screen, get_global_radius
        except Exception:
            return False

        L = LANGUAGES.get(lang, LANGUAGES.get("RU", {}))
        colors = {
            "light": {"bg": "#F3F3F3", "fg": "#000000", "entry": "#FFFFFF"},
            "dark": {"bg": "#1d1e1e", "fg": "#FFFFFF", "entry": "#2b2b2b"},
        }.get(theme, {"bg": "#1d1e1e", "fg": "#FFFFFF", "entry": "#2b2b2b"})

        root = ctk.CTk()
        root.title(L.get("master_title", "Master password"))
        root.resizable(False, False)
        root.configure(fg_color=colors["bg"])
        center_screen(root, 430, 245)

        result = {"ok": False, "attempts": 0}
        max_attempts = cls.MAX_ATTEMPTS

        ctk.CTkLabel(
            root,
            text=L.get("master_prompt", "Enter master password:"),
            font=("Segoe UI", 14),
            text_color=colors["fg"],
            wraplength=360,
        ).pack(padx=20, pady=(24, 10))

        entry = ctk.CTkEntry(
            root,
            width=350,
            height=40,
            show="*",
            fg_color=colors["entry"],
            text_color=colors["fg"],
            corner_radius=get_global_radius(),
        )
        entry.pack(padx=20, pady=(0, 8))

        status = ctk.CTkLabel(root, text="", font=("Segoe UI", 12), text_color="#E24B4A")
        status.pack(pady=(0, 10))

        def finish_ok() -> None:
            result["ok"] = True
            root.destroy()

        def cancel() -> None:
            result["ok"] = False
            root.destroy()

        def submit() -> None:
            pwd = entry.get()
            if cls.verify(pwd):
                set_key_from_master(pwd)
                finish_ok()
                return

            result["attempts"] += 1
            entry.delete(0, "end")
            if result["attempts"] >= max_attempts:
                status.configure(text=L.get("master_blocked", "Too many failed attempts."))
                root.after(1200, cancel)
                return
            status.configure(
                text=L.get("master_wrong", "Wrong master password! Attempt {0} of {1}.").format(
                    result["attempts"], max_attempts
                )
            )

        buttons = ctk.CTkFrame(root, fg_color="transparent")
        buttons.pack(pady=(0, 18))
        ctk.CTkButton(
            buttons,
            text=L.get("ok", "OK"),
            width=120,
            height=36,
            fg_color="#2d6a4f",
            command=submit,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            buttons,
            text=L.get("cancel", "Cancel"),
            width=120,
            height=36,
            fg_color="#8b0000",
            command=cancel,
        ).pack(side="left", padx=8)

        entry.bind("<Return>", lambda _e: submit())
        entry.bind("<Escape>", lambda _e: cancel())
        root.protocol("WM_DELETE_WINDOW", cancel)
        root.after(100, entry.focus_set)
        root.mainloop()
        return result["ok"]
