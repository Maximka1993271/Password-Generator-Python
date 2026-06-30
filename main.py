#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure Pass Pro v4.0 — Cryptographically secure password generator
Author: Maxim Melnikov

English:
Secure Pass Pro v4.0 — Cryptographically secure password generator
Full 3-language support (RU, EN, UA)
Cross-platform: Windows, Linux, macOS

Русский:
Secure Pass Pro v4.0 — Криптографически безопасный генератор паролей
Полная поддержка 3 языков (RU, EN, UA)
Кросс-платформенность: Windows, Linux, macOS

Українська:
Secure Pass Pro v4.0 — Криптографічно безпечний генератор паролів
Повна підтримка 3 мов (RU, EN, UA)
Кросплатформеність: Windows, Linux, macOS

FIXED: Added --disable-vm-check command line argument to disable VM detection for dev/testing
FIXED: Added database diagnostics on startup
FIXED: Added improved logging with context
"""
from __future__ import annotations

import sys
import os
import json
import platform
import argparse
from typing import Dict, Optional, List, Any

# Setup logging early
from utils.logger import get_logger

logger = get_logger("launcher")
# ── Hide console window on Windows (prevents flash when run via .pyw / shortcut) ──
if platform.system() == "Windows":
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
    except (AttributeError, OSError, TypeError):
        pass



# Parse command line arguments BEFORE anti-debug
parser = argparse.ArgumentParser(description="Secure Pass Pro v4.0")
parser.add_argument("--disable-vm-check", action="store_true", 
                    help="Disable VM/sandbox detection (for development/testing)")
parser.add_argument("--disable-anti-debug", action="store_true",
                    help="Disable anti-debugging protection (for development)")
parser.add_argument("--no-db-diagnostics", action="store_true",
                    help="Skip database diagnostics on startup")
parser.add_argument("--db-repair", action="store_true",
                    help="Force database repair on startup")
parser.add_argument("--lang", choices=["RU", "EN", "UA"], default=None,
                    help="Force language (RU, EN, UA)")
parser.add_argument("--theme", choices=["light", "dark", "system"], default=None,
                    help="Force theme (light, dark, system)")
args, unknown = parser.parse_known_args()

# Anti-debugging protection (can be disabled for dev)
if not args.disable_anti_debug:
    try:
        from security.antidebug import init_anti_debug
        if hasattr(args, 'disable_vm_check') and args.disable_vm_check:
            os.environ['SECUREPASS_DISABLE_VM_CHECK'] = '1'
        init_anti_debug()
        logger.debug("Anti-debugging initialized")
    except ImportError as e:
        logger.warning(f"Anti-debug module not available: {e}")
    except (AttributeError, RuntimeError, OSError) as e:
        logger.error(f"Anti-debug error: {e}")
else:
    logger.warning("Anti-debugging disabled by command line flag")

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_startup_config() -> Dict[str, str]:
    """
    Load startup configuration from the same Config manager used by the GUI.
    Supports 3 languages: RU, EN, UA.
    """
    config: Dict[str, str] = {"lang": "RU", "theme": "dark"}

    if args.lang:
        config["lang"] = args.lang
        logger.info(f"Language forced via command line: {args.lang}")
    
    if args.theme:
        config["theme"] = args.theme
        logger.info(f"Theme forced via command line: {args.theme}")

    try:
        from core.app_settings import AppSettings as _AS
        _s = _AS.instance()
        lang  = _s.language
        theme = _s.theme

        if not args.lang and lang in ("RU", "EN", "UA"):
            config["lang"] = lang

        if not args.theme:
            if theme == "Light":
                config["theme"] = "light"
            elif theme == "Dark":
                config["theme"] = "dark"
            else:
                config["theme"] = "system"

        logger.info(f"Loaded startup config: lang={config['lang']}, theme={config['theme']}")
    except (ImportError, OSError, IOError, PermissionError, KeyError, ValueError, TypeError, AttributeError) as e:
        logger.error(f"Config load error: {e}")

    return config


def setup_early_environment() -> None:
    """
    Setup early environment settings (cross-platform).
    """
    try:
        sys.setrecursionlimit(10000)
    except (ValueError, RuntimeError) as e:
        logger.debug(f"Failed to set recursion limit: {e}")

    if platform.system() == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except (AttributeError, OSError, TypeError, ImportError) as e:
            logger.debug(f"Windows console setup error: {e}")

    elif platform.system() == "Linux":
        try:
            if "QT_SCALE_FACTOR" not in os.environ:
                os.environ["QT_SCALE_FACTOR"] = "1"
            if "GDK_SCALE" not in os.environ:
                os.environ["GDK_SCALE"] = "1"
        except (KeyError, TypeError, ValueError, OSError) as e:
            logger.debug(f"Linux environment setup error: {e}")

    elif platform.system() == "Darwin":
        try:
            if "NSHighResolutionCapable" not in os.environ:
                os.environ["NSHighResolutionCapable"] = "True"
        except (KeyError, TypeError, ValueError, OSError) as e:
            logger.debug(f"macOS environment setup error: {e}")


def check_python_version() -> bool:
    """
    Check python version and return the result.
    Проверить python version и вернуть результат.
    Перевірити python version і повернути результат.
    """
    if sys.version_info < (3, 8):
        error_msg = (
            "Secure Pass Pro requires Python 3.8 or higher!\n"
            "Secure Pass Pro требует Python 3.8 или выше!\n"
            "Secure Pass Pro вимагає Python 3.8 або вище!"
        )
        print(error_msg)
        logger.critical(error_msg)
        return False
    return True


def check_dependencies() -> bool:
    """
    Check dependencies and return the result.
    Проверить dependencies и вернуть результат.
    Перевірити dependencies і повернути результат.
    """
    import importlib.util
    missing: List[str] = []

    critical = [
        ('customtkinter', 'customtkinter'),
        ('PIL', 'Pillow'),
        ('cryptography', 'cryptography'),
    ]

    for module, package in critical:
        if importlib.util.find_spec(module) is None:
            missing.append(package)
            logger.debug(f"Missing dependency: {package}")

    if missing:
        error_msg = (
            "=" * 50 + "\n"
            "Secure Pass Pro - Missing Dependencies\n"
            "=" * 50 + "\n\n"
            "The following packages are required:\n\n"
        )
        for pkg in missing:
            error_msg += f"   - {pkg}\n"
        error_msg += "\nInstall with:\n"
        error_msg += f"   pip install {' '.join(missing)}\n"
        error_msg += "\n" + "=" * 50

        print(error_msg)
        logger.error(f"Missing dependencies: {missing}")
        return False

    logger.info("All dependencies are available")
    return True


def create_desktop_shortcut() -> None:
    """
    Create and return desktop shortcut.
    Создать и вернуть desktop shortcut.
    Створити і повернути desktop shortcut.
    """
    system = platform.system()

    try:
        if system == "Windows":
            import winshell
            from win32com.client import Dispatch

            desktop = winshell.desktop()
            path = os.path.join(desktop, "Secure Pass Pro.lnk")

            if os.path.exists(path):
                return

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = sys.executable
            shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            shortcut.IconLocation = sys.executable
            shortcut.save()

            print("Desktop shortcut created successfully (Windows)")
            logger.info("Desktop shortcut created on Windows")

        elif system == "Linux":
            desktop = os.path.expanduser("~/Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~/.local/share/applications")

            os.makedirs(desktop, exist_ok=True)

            path = os.path.join(desktop, "securepasspro.desktop")
            if os.path.exists(path):
                return

            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            icon_path = os.path.join(os.path.dirname(exe_path), "icon.png")
            if not os.path.exists(icon_path):
                icon_path = ""

            with open(path, 'w', encoding='utf-8') as f:
                f.write("[Desktop Entry]\n")
                f.write("Version=1.0\n")
                f.write("Type=Application\n")
                f.write("Name=Secure Pass Pro\n")
                f.write("Comment=Password generator and manager\n")
                f.write(f"Exec={exe_path}\n")
                if icon_path:
                    f.write(f"Icon={icon_path}\n")
                f.write("Terminal=false\n")
                f.write("Categories=Utility;Security;\n")
                f.write("StartupWMClass=SecurePassPro\n")

            os.chmod(path, 0o755)
            print("Desktop shortcut created successfully (Linux)")
            logger.info("Desktop shortcut created on Linux")

        elif system == "Darwin":
            desktop = os.path.expanduser("~/Desktop")
            os.makedirs(desktop, exist_ok=True)
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]

            path = os.path.join(desktop, "Secure Pass Pro.command")
            if os.path.exists(path):
                return

            with open(path, 'w', encoding='utf-8') as f:
                f.write("#!/bin/bash\n")
                f.write(f'cd "{os.path.dirname(exe_path)}"\n')
                f.write(f'"{exe_path}"\n')

            os.chmod(path, 0o755)
            print("Desktop shortcut created successfully (macOS)")
            logger.info("Desktop shortcut created on macOS")

    except ImportError as e:
        logger.debug(f"Desktop shortcut modules not available: {e}")
    except (AttributeError, OSError, RuntimeError, TypeError, PermissionError) as e:
        logger.warning(f"Could not create desktop shortcut: {e}")


def apply_platform_theme(app) -> None:
    """
    Apply platform theme.
    Применить platform theme.
    Застосувати platform theme.
    """
    system = platform.system()

    try:
        if system == "Linux":
            from utils.helpers import apply_linux_theme
            apply_linux_theme(app)
            logger.debug("Linux theme applied")
        elif system == "Darwin":
            from utils.helpers import apply_macos_theme
            apply_macos_theme(app)
            logger.debug("macOS theme applied")
    except ImportError as e:
        logger.debug(f"Platform theme module not available: {e}")
    except (AttributeError, RuntimeError, OSError) as e:
        logger.debug(f"Platform theme error: {e}")


def run_database_diagnostics_on_startup(
    lang: str,
    auto_repair: bool = True,
    force_repair: bool = False
) -> Dict[str, Any]:
    """
    Run database diagnostics on startup.
    Запустить database diagnostics on startup.
    Запустити database diagnostics on startup.
    """
    from storage.db_diagnostics import run_database_diagnostics, DIAGNOSTIC_OK, DIAGNOSTIC_WARNING, DIAGNOSTIC_ERROR, DIAGNOSTIC_CRITICAL
    from gui.dialogs import CTkMessageBox
    from Langs.lang import LANGUAGES

    L = LANGUAGES.get(lang, LANGUAGES["RU"])
    result = {"status": DIAGNOSTIC_OK, "errors": [], "recommendations": [], "repairs": []}

    try:
        diag_result = run_database_diagnostics(auto_repair=auto_repair)
        result = diag_result

        status = diag_result.get("status", DIAGNOSTIC_OK)

        if status in (DIAGNOSTIC_ERROR, DIAGNOSTIC_CRITICAL) or force_repair:
            errors = diag_result.get("errors", [])
            recommendations = diag_result.get("recommendations", [])

            if errors or force_repair:
                status_text = {
                    DIAGNOSTIC_ERROR: L.get("status_error", "Error / Ошибка / Помилка"),
                    DIAGNOSTIC_CRITICAL: L.get("status_warning", "Warning / Предупреждение / Попередження")
                }.get(status, L.get("status_warning", "Warning / Предупреждение / Попередження"))

                msg = f"{status_text}: {L.get('db_diagnostic_issues', 'Database issues detected')}.\n\n"

                if errors:
                    msg += L.get("db_errors", "Errors") + ":\n- " + "\n- ".join(errors) + "\n\n"

                if recommendations:
                    msg += L.get("db_recommendations", "Recommendations") + ":\n- " + "\n- ".join(recommendations)

                if force_repair and not diag_result.get("repairs"):
                    msg += "\n\n" + L.get("db_repair_forced", "Forced repair attempted.")

                CTkMessageBox.warning(None, L.get("db_diagnostics_title", "Database Diagnostics / Диагностика БД / Діагностика БД"), msg)

        elif status == DIAGNOSTIC_WARNING:
            recommendations = diag_result.get("recommendations", [])
            if recommendations:
                msg = L.get("db_warning", "Database warning") + ":\n\n- " + "\n- ".join(recommendations)
                CTkMessageBox.info(None, L.get("db_diagnostics_title", "Database Diagnostics / Диагностика БД / Діагностика БД"), msg)

        else:
            logger.info("Database diagnostics OK")

    except (ImportError, AttributeError, RuntimeError, OSError) as e:
        logger.warning(f"Database diagnostics startup error: {e}")
        result["errors"].append(str(e))

    return result


def run_application(startup_config: Dict[str, str]) -> int:
    """
    Run application.
    Запустить application.
    Запустити application.
    """
    try:
        from gui.main_window import SecurePassPro
        from security.master import MasterPassword
        import customtkinter as ctk
        from security.panic import init_panic_cleanup

        try:
            init_panic_cleanup()
            logger.info("Panic cleanup initialized")
        except (ImportError, AttributeError, RuntimeError, OSError) as e:
            logger.warning(f"Panic cleanup initialization failed: {e}")

        if not args.no_db_diagnostics:
            try:
                diag_result = run_database_diagnostics_on_startup(
                    lang=startup_config["lang"],
                    auto_repair=True,
                    force_repair=args.db_repair
                )
                if diag_result.get("status") in ("error", "critical"):
                    logger.warning(
                        f"Database diagnostics found issues: {diag_result.get('errors')}\n"
                        f"Рекомендации: {diag_result.get('recommendations')}\n"
                        f"Рекомендації: {diag_result.get('recommendations')}"
                    )
            except (ImportError, AttributeError, RuntimeError, OSError) as e:
                logger.warning(f"Database diagnostics startup error: {e}")

        try:
            if startup_config["theme"] == "system":
                try:
                    from utils.theme_utils import detect_system_theme
                    detected = detect_system_theme()
                    ctk.set_appearance_mode(detected.lower())
                    logger.debug(f"System theme detected: {detected}")
                except (ImportError, AttributeError, RuntimeError) as e:
                    logger.warning(f"System theme detection failed, using dark: {e}")
                    ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode(startup_config["theme"])
            ctk.set_default_color_theme("blue")
            logger.debug(f"Appearance mode set to: {startup_config['theme']}")
        except (ValueError, AttributeError, RuntimeError) as e:
            logger.error(f"Failed to set appearance mode: {e}")
            return 1

        try:
            if not MasterPassword.prompt_on_startup(startup_config["lang"], startup_config["theme"]):
                logger.info("Application closed by user during master password prompt")
                return 0
        except (ImportError, AttributeError, RuntimeError, OSError, ValueError) as e:
            logger.error(f"Master password prompt failed: {e}")
            return 1

        try:
            app = SecurePassPro()
            apply_platform_theme(app)
            logger.info("Application started successfully")

            try:
                create_desktop_shortcut()
            except (ImportError, AttributeError, OSError, RuntimeError, PermissionError) as e:
                logger.debug(f"Desktop shortcut creation skipped: {e}")

            app.mainloop()
            return 0

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            print("\n\nSecure Pass Pro closed.")
            print("\n\nSecure Pass Pro закрыт.")
            print("\n\nSecure Pass Pro закрито.")
            return 0
        except (RuntimeError, AttributeError, OSError, ImportError) as e:
            logger.exception(f"Application runtime error: {e}")
            return 1

    except ImportError as e:
        logger.critical(f"Failed to import application modules: {e}")
        return 1
    except (AttributeError, RuntimeError, OSError, ValueError) as e:
        logger.critical(f"Application initialization error: {e}")
        return 1


def main() -> int:
    """
    Handle main.
    Обработать main.
    Обробити main.
    """
    try:
        setup_early_environment()
    except (RuntimeError, OSError, AttributeError) as e:
        print(f"Warning: Early environment setup failed: {e}")

    if not check_python_version():
        return 1

    if not check_dependencies():
        return 1

    try:
        startup_config = get_startup_config()
    except (OSError, IOError, json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(f"Failed to load startup config: {e}, using defaults")
        startup_config = {"lang": "RU", "theme": "dark"}

    exit_code = run_application(startup_config)

    try:
        logger.info(f"Application exiting with code: {exit_code}")
    except (NameError, RuntimeError):
        pass

    return exit_code


if __name__ == "__main__":
    sys.exit(main())