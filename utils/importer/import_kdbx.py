"""
KeePass .kdbx import для Secure Pass Pro
KeePass .kdbx import for Secure Pass Pro
KeePass .kdbx імпорт для Secure Pass Pro

Requires pykeepass (pip install pykeepass)
"""
from __future__ import annotations

import os
import tkinter as tk
import customtkinter as ctk
from datetime import datetime
from typing import Tuple
from utils.logger import get_logger

logger = get_logger("import_kdbx")

# ── pykeepass import guard ────────────────────────────────────────
# pykeepass depends on `construct` which imports `pdb`.
# In a PyInstaller-frozen EXE built on a machine with `pdbpp` installed,
# PyInstaller bundles the patched pdb.py but NOT pdbpp.py, causing:
#   FileNotFoundError: .../pdbpp.py
# We catch both ImportError and FileNotFoundError to handle both cases:
#  • ImportError     → pykeepass not installed (normal dev/user case)
#  • FileNotFoundError → pdbpp.py missing in frozen EXE (build env issue)
try:
    # Pre-block pdbpp so construct/pdb can load cleanly in the frozen EXE
    import sys as _sys
    class _BlockedModule:
        """Stub that prevents pdbpp from loading in the frozen EXE."""
        __all__: list = []
        def __getattr__(self, _): return None
    for _m in ('pdbpp', 'pdbpp_utils', 'fancycompleter', 'pyrepl'):
        if _m not in _sys.modules:
            _sys.modules[_m] = _BlockedModule()   # type: ignore[assignment]

    from pykeepass import PyKeePass
    from pykeepass.exceptions import CredentialsError
    PYKEEPASS_AVAILABLE = True
except (ImportError, FileNotFoundError, OSError) as _e:
    PYKEEPASS_AVAILABLE = False
    logger.warning(
        "pykeepass not available — .kdbx import disabled. "
        "Install with: pip install pykeepass  (%s: %s)",
        type(_e).__name__, _e,
    )
except Exception as _e:
    # Catch any other pdbpp/construct-related failure in frozen EXE
    PYKEEPASS_AVAILABLE = False
    logger.error("Unexpected error loading pykeepass: %s: %s", type(_e).__name__, _e)


def _ask_kdbx_password(parent, lang: str) -> str:
    """
    Handle ask kdbx password.
    Обработать ask kdbx password.
    Обробити ask kdbx password.
    """
    labels = {
        "RU": {
            "title": "Пароль KeePass",
            "text": "Введите мастер-пароль от .kdbx файла\n(оставьте пустым если без пароля):",
            "ok": "ОК",
            "cancel": "Отмена",
        },
        "UA": {
            "title": "Пароль KeePass",
            "text": "Введіть майстер-пароль від .kdbx файлу\n(залиште порожнім якщо без пароля):",
            "ok": "ОК",
            "cancel": "Скасувати",
        },
        "EN": {
            "title": "KeePass Password",
            "text": "Enter the master password for the .kdbx file\n(leave empty if no password):",
            "ok": "OK",
            "cancel": "Cancel",
        },
    }
    L = labels.get(lang, labels["RU"])

    result = {"value": None}

    win = ctk.CTkToplevel(parent)
    win.title(L["title"])
    win.resizable(False, False)

    win.update_idletasks()
    w, h = 400, 200
    if parent:
        px = parent.winfo_x()
        py = parent.winfo_y()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
    else:
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")

    win.grab_set()
    win.lift()
    win.focus_force()

    ctk.CTkLabel(win, text=L["text"],
                 font=("Segoe UI", 13),
                 justify="left").pack(padx=20, pady=(20, 10))

    pwd_var = tk.StringVar()
    entry = ctk.CTkEntry(win, textvariable=pwd_var, show="●",
                         width=360, height=38, font=("Segoe UI", 13))
    entry.pack(padx=20, pady=(0, 15))
    entry.focus()

    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack()

    def on_ok() -> None:
        """
        Handle the ok event.
        Обработчик ok.
        Обробник ok.
        """
        result["value"] = pwd_var.get()
        win.destroy()

    def on_cancel() -> None:
        """
        Handle the cancel event.
        Обработчик cancel.
        Обробник cancel.
        """
        result["value"] = None
        win.destroy()

    ctk.CTkButton(btn_row, text=L["ok"], command=on_ok,
                  width=120, height=36, fg_color="#2d6a4f",
                  font=("Segoe UI", 13, "bold")).pack(side="left", padx=(0, 10))

    ctk.CTkButton(btn_row, text=L["cancel"], command=on_cancel,
                  width=120, height=36, fg_color="#8b0000",
                  font=("Segoe UI", 13, "bold")).pack(side="left")

    entry.bind("<Return>", lambda e: on_ok())
    entry.bind("<Escape>", lambda e: on_cancel())

    win.wait_window()
    return result["value"]


def import_from_kdbx(file_path: str, parent=None, lang: str = "RU") -> Tuple[int, int]:
    """
    Handle import from kdbx.
    Обработать import from kdbx.
    Обробити import from kdbx.
    """
    from storage.database import PasswordDB
    from gui.dialogs import CTkMessageBox

    error_labels = {
        "RU": {
            "no_lib": "Библиотека pykeepass не установлена.\nУстановите: pip install pykeepass",
            "wrong_pass": "Неверный пароль от файла KeePass.",
            "cancelled": "Импорт отменён.",
            "error": "Ошибка импорта",
            "empty": "Не найдено записей для импорта.",
            "err_title": "Ошибка",
            "warn_title": "Предупреждение",
        },
        "UA": {
            "no_lib": "Бібліотека pykeepass не встановлена.\nВстановіть: pip install pykeepass",
            "wrong_pass": "Невірний пароль від файлу KeePass.",
            "cancelled": "Імпорт скасовано.",
            "error": "Помилка імпорту",
            "empty": "Не знайдено записів для імпорту.",
            "err_title": "Помилка",
            "warn_title": "Попередження",
        },
        "EN": {
            "no_lib": "pykeepass library is not installed.\nInstall with: pip install pykeepass",
            "wrong_pass": "Wrong password for the KeePass file.",
            "cancelled": "Import cancelled.",
            "error": "Import error",
            "empty": "No entries found to import.",
            "err_title": "Error",
            "warn_title": "Warning",
        },
    }
    LE = error_labels.get(lang, error_labels["RU"])

    if not PYKEEPASS_AVAILABLE:
        CTkMessageBox.error(parent, LE["err_title"], LE["no_lib"])
        return 0, 0

    db_password = None
    for attempt in range(3):
        db_password = _ask_kdbx_password(parent, lang)
        if db_password is None:
            return 0, 0

        try:
            kp = PyKeePass(file_path, password=db_password if db_password else None)
            break
        except CredentialsError:
            if attempt < 2:
                retry_labels = {
                    "RU": "Неверный пароль. Попробуйте ещё раз.",
                    "UA": "Невірний пароль. Спробуйте ще раз.",
                    "EN": "Wrong password. Please try again.",
                }
                CTkMessageBox.error(parent, LE["err_title"],
                                    retry_labels.get(lang, retry_labels["RU"]))
                continue
            else:
                CTkMessageBox.error(parent, LE["err_title"], LE["wrong_pass"])
                return 0, 0
        except FileNotFoundError as e:
            CTkMessageBox.error(parent, LE["err_title"], str(e))
            return 0, 0
        except (OSError, ValueError, RuntimeError, MemoryError) as e:
            CTkMessageBox.error(parent, LE["err_title"], f"{LE['error']}: {e}")
            return 0, 0
    else:
        return 0, 0

    imported = 0
    skipped = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for entry in kp.entries:
        try:
            label = (entry.title or "").strip()[:200]
            password = (entry.password or "").strip()
            username = (entry.username or "").strip()[:100]
            url = (entry.url or "").strip()[:500]
            notes = (entry.notes or "").strip()[:500]

            category = ""
            if entry.group and entry.group.name:
                category = entry.group.name.strip()[:100]
                if category.lower() in ("passwords", "root", "keepass", ""):
                    category = ""

            is_favorite = 0
            if hasattr(entry, "tags") and entry.tags:
                tags = entry.tags if isinstance(entry.tags, list) else [entry.tags]
                if any("favorit" in str(t).lower() or "избран" in str(t).lower() for t in tags):
                    is_favorite = 1

            if not password:
                skipped += 1
                continue

            if not label:
                label = username or url or f"KeePass_{imported + skipped + 1}"

            try:
                from core.validators import sanitize_label, sanitize_url, sanitize_notes, sanitize_text
                label    = sanitize_label(str(label or ''))[:255]
                password = str(password or '')[:1024]
                url      = sanitize_url(str(url or ''))[:2048]
                notes    = sanitize_notes(str(notes or ''))[:10000]
                username = sanitize_text(str(username or ''), max_len=255)
                if not label:
                    skipped += 1
                    continue
                PasswordDB.save(
                    label=label,
                    password=password,
                    notes=notes,
                    lang=lang,
                    url=url,
                    username=username,
                    email="",
                    category=category,
                )
                imported += 1
            except (ValueError, TypeError, OSError, RuntimeError) as e:
                logger.warning(f"Failed to save entry '{label}': {e}")
                skipped += 1

        except (AttributeError, ValueError, TypeError, RuntimeError) as e:
            logger.warning(f"Skipping KeePass entry due to error: {e}")
            skipped += 1

    logger.info(f"KDBX import: {imported} imported, {skipped} skipped from '{os.path.basename(file_path)}'")
    return imported, skipped
