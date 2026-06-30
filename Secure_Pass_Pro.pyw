#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure Pass Pro v4.0 — Cryptographically secure password generator
Author: Maxim Melnikov

Запуск (Windows): double-click Secure_Pass_Pro.pyw
Запуск (Linux/macOS): python3 Secure_Pass_Pro.pyw
"""

# ══════════════════════════════════════════════════════════════════
#  STEP 0  —  bootstrap: must work before ANY local import
# ══════════════════════════════════════════════════════════════════
import sys
import os
import traceback

# Fix working directory & sys.path so local packages are always found
# (critical when launched by double-click — CWD is often wrong)
_HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(_HERE)                          # make CWD = project root
for _p in (_HERE, os.path.dirname(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Early error reporter (works before tkinter/customtkinter) ────
def _fatal(title: str, message: str, exc: BaseException = None) -> None:
    """Show an error dialog and exit.  Works even if the app never started."""
    import tkinter as _tk
    from tkinter import messagebox as _mb
    _root = _tk.Tk()
    _root.withdraw()
    _root.attributes("-topmost", True)
    full_msg = message
    if exc:
        full_msg += f"\n\n{type(exc).__name__}: {exc}"
        full_msg += f"\n\n{traceback.format_exc()}"
    _mb.showerror(title, full_msg)
    _root.destroy()
    sys.exit(1)

# ── Verify Python version ──────────────────────────────────────
if sys.version_info < (3, 8):
    _fatal("Python version error",
           f"Secure Pass Pro requires Python 3.8+.\n"
           f"Current: {sys.version}\n\n"
           f"Interpreter: {sys.executable}")

# ══════════════════════════════════════════════════════════════════
#  STEP 1  —  logger (safe fallback so crashes are always logged)
# ══════════════════════════════════════════════════════════════════
try:
    from utils.logger import get_logger, log_crash_report, setup_logging as _setup_logging
    _setup_logging()      # configure root «spp» logger once at startup
    # Initialise ConfigManager (scans SECUREPASS_* env vars)
    from core.config_manager import ConfigManager as _CM
    _CM.instance()        # singleton created here, env vars cached
    # Hide all sensitive data directories immediately (Windows)
    try:
        from utils.paths import hide_all_app_dirs as _hide_dirs
        _hide_dirs()
    except Exception:
        pass
    logger = get_logger("launcher")
except Exception as _log_err:           # noqa: BLE001
    # stdlib fallback — keeps the rest of the code working
    import logging as _logging
    _logging.basicConfig(
        level=_logging.DEBUG,
        filename=os.path.join(_HERE, "startup_error.log"),
        filemode="w",
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = _logging.getLogger("launcher")
    logger.error("Could not import utils.logger: %s", _log_err)

    def log_crash_report(exc, ctx=None):   # type: ignore[override]
        logger.exception("CRASH: %s | context=%s", exc, ctx)

    _fatal(
        "Import error",
        "Could not load utils.logger.\n\n"
        f"Project folder:\n  {_HERE}\n\n"
        f"Python:\n  {sys.executable}\n\n"
        "Make sure you are running this file from the Secure Pass Pro folder "
        "and that all dependencies are installed.\n\n"
        f"Error: {_log_err}",
        _log_err,
    )

logger.info("Launcher started  |  Python %s  |  cwd=%s", sys.version, _HERE)
logger.info("sys.executable = %s", sys.executable)

# ══════════════════════════════════════════════════════════════════
#  STEP 2  —  optional modules (non-fatal if missing)
# ══════════════════════════════════════════════════════════════════
try:
    from security.antidebug import init_anti_debug
    init_anti_debug()
    logger.debug("Anti-debug initialized")
except ImportError:
    logger.warning("Anti-debug module not available")
except Exception as _e:                 # noqa: BLE001
    logger.error("Anti-debug init error: %s", _e)

# ══════════════════════════════════════════════════════════════════
#  STEP 3  —  check critical dependencies before importing the GUI
# ══════════════════════════════════════════════════════════════════
def _check_deps() -> None:
    import importlib.util
    missing = []
    for mod, pkg in [
        ("customtkinter", "customtkinter"),
        ("PIL",           "Pillow"),
        ("cryptography",  "cryptography"),
    ]:
        if importlib.util.find_spec(mod) is None:
            missing.append(pkg)

    if missing:
        _fatal(
            "Missing dependencies",
            "The following packages are not installed:\n\n"
            + "".join(f"  • {p}\n" for p in missing)
            + "\nRun in a terminal:\n\n"
            f"  pip install {' '.join(missing)}\n\n"
            f"(Python: {sys.executable})",
        )

_check_deps()

# ══════════════════════════════════════════════════════════════════
#  STEP 4  —  load config (lang / theme)
# ══════════════════════════════════════════════════════════════════
import json

_CONFIG_DIR  = os.path.join(_HERE, ".securepass")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "config.json")

def _load_config():
    try:
        os.makedirs(_CONFIG_DIR, exist_ok=True)
    except (OSError, PermissionError):
        pass
    lang, theme = "RU", "dark"
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, "r", encoding="utf-8") as _f:
                _cfg = json.load(_f)
            if _cfg.get("LANG") in ("RU", "EN", "UA"):
                lang = _cfg["LANG"]
            if _cfg.get("THEME") == "Light":
                theme = "light"
            elif _cfg.get("THEME") == "Dark":
                theme = "dark"
    except (json.JSONDecodeError, OSError, PermissionError, KeyError, ValueError) as _e:
        logger.warning("Config load error: %s", _e)
    return lang, theme

# ══════════════════════════════════════════════════════════════════
#  STEP 5  —  main application
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        import customtkinter as ctk
        from gui.main_window import SecurePassPro
        from security.master import MasterPassword

        from core.app_settings import AppSettings as _AS
        _s = _AS.instance()
        startup_lang  = _s.language
        startup_theme = _s.theme
        logger.info("Config loaded: lang=%s theme=%s", startup_lang, startup_theme)

        # Apply appearance before any window is created
        try:
            ctk.set_appearance_mode(startup_theme)
            ctk.set_default_color_theme("blue")
        except (ValueError, AttributeError, RuntimeError) as _e:
            logger.error("Appearance mode error: %s", _e)

        # Master-password prompt
        try:
            if not MasterPassword.prompt_on_startup(startup_lang, startup_theme):
                logger.info("Closed at master-password screen")
                sys.exit(0)
        except (ImportError, AttributeError, RuntimeError, OSError) as _e:
            logger.error("Master password error: %s", _e)
            _fatal("Master password error",
                   "Could not open the master password dialog.", _e)

        # Main window
        try:
            import tkinter as tk
            app = SecurePassPro()
            logger.info("Application started")
            app.mainloop()
        except (RuntimeError, OSError, tk.TclError, AttributeError) as _e:
            logger.critical("Runtime error: %s", _e)
            log_crash_report(_e, {"stage": "main"})
            _fatal("Runtime error", "The application encountered a fatal error.", _e)

    except SystemExit:
        raise                           # honour sys.exit() calls

    except Exception as _e:             # noqa: BLE001  — true catch-all
        logger.critical("Unhandled exception: %s", _e, exc_info=True)
        log_crash_report(_e, {"stage": "startup"})
        _fatal(
            "Fatal startup error",
            "Secure Pass Pro failed to start.\n\n"
            f"Project folder:\n  {_HERE}\n\n"
            f"Python:\n  {sys.executable}",
            _e,
        )
