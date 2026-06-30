#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure Pass Pro v4.0 - Build Script
===================================
English: Cross-platform build script using PyInstaller
Русский: Кросс-платформенный скрипт сборки с использованием PyInstaller
Українська: Кросплатформений скрипт збірки з використанням PyInstaller

FIXED #EX4: Replaced broad Exception with specific exceptions (OSError, IOError, PermissionError, subprocess.CalledProcessError)
FIXED #EX4: Added proper error handling for file operations and subprocess calls
FIXED #TEST4: Fixed permission error handling during cleanup

Исправлено #EX4: Заменены общие except Exception на конкретные исключения (OSError, IOError, PermissionError, subprocess.CalledProcessError)
Исправлено #EX4: Добавлена правильная обработка ошибок для файловых операций и вызовов subprocess
Исправлено #TEST4: Исправлена обработка ошибок прав доступа при очистке

Виправлено #EX4: Замінено загальні except Exception на конкретні винятки (OSError, IOError, PermissionError, subprocess.CalledProcessError)
Виправлено #EX4: Додано правильну обробку помилок для файлових операцій та викликів subprocess
Виправлено #TEST4: Виправлено обробку помилок доступу при очищенні

Author: Maxim Melnikov
License: MIT
"""
from __future__ import annotations

import os
import sys
import platform
import shutil
import subprocess
import json
import argparse
from pathlib import Path
from datetime import datetime

# ==================== LANGUAGE DICTIONARIES ====================

TEXTS = {
    "RU": {
        "app_name": "Secure Pass Pro v4.0 - Скрипт сборки",
        "separator": "=" * 60,
        "cleaning": "🧹 Очистка предыдущих сборок...",
        "cleaned": "🧹 Очищено: {}",
        "cannot_clean": "⚠️ Не удалось очистить {}: {}",
        "building": "🏗️ Сборка для платформы: {}",
        "running": "📦 Запуск PyInstaller...",
        "command": "🔧 Команда: {}",
        "success": "✅ Сборка успешно завершена!",
        "failed": "❌ Ошибка сборки!",
        "output_dir": "📁 Папка вывода: {}",
        "generated_files": "📄 Сгенерированные файлы:",
        "file_info": "   📄 {} ({})",
        "version": "🔢 Версия: {}",
        "python_version": "🐍 Python: {}",
        "platform": "🖥️ Платформа: {}",
        "checking_deps": "📦 Проверка зависимостей...",
        "deps_missing": "⚠️ Отсутствуют зависимости: {}",
        "deps_ok": "✅ Все зависимости доступны",
        "install_deps": "💡 Выполните: pip install -r requirements.txt",
        "creating_resources": "📁 Создание папки resources...",
        "resources_ready": "✅ Папка resources готова",
        "no_resources": "⚠️ Папка resources не найдена",
        "missing_folders": "⚠️ Отсутствуют папки: {}",
        "build_start": "🔐 Запуск процесса сборки...",
        "build_end": "🏁 Процесс сборки завершён",
        "elapsed_time": "⏱️ Затрачено времени: {:.2f} секунд",
        "error_no_main": "❌ Ошибка: main.py не найден!",
        "error_no_pyinstaller": "❌ Ошибка: PyInstaller не установлен! Выполните: pip install pyinstaller",
        "error_build_failed": "❌ Ошибка сборки с кодом: {}",
        "help_clean": "Очистить папки сборки перед сборкой",
        "help_verbose": "Подробный вывод",
        "help_help": "Показать это сообщение",
        "continue_anyway": "⚠️ Продолжить? (д/н): ",
        "build_cancelled": "❌ Сборка отменена пользователем",
        "all_assets_found": "✅ Все папки ресурсов найдены",
        "error_pyinstaller_exec": "❌ Ошибка выполнения PyInstaller: {}",
    },
    "EN": {
        "app_name": "Secure Pass Pro v4.0 - Build Script",
        "separator": "=" * 60,
        "cleaning": "🧹 Cleaning previous builds...",
        "cleaned": "🧹 Cleaned: {}",
        "cannot_clean": "⚠️ Could not clean {}: {}",
        "building": "🏗️ Building for platform: {}",
        "running": "📦 Running PyInstaller...",
        "command": "🔧 Command: {}",
        "success": "✅ Build completed successfully!",
        "failed": "❌ Build failed!",
        "output_dir": "📁 Output directory: {}",
        "generated_files": "📄 Generated files:",
        "file_info": "   📄 {} ({})",
        "version": "🔢 Version: {}",
        "python_version": "🐍 Python: {}",
        "platform": "🖥️ Platform: {}",
        "checking_deps": "📦 Checking dependencies...",
        "deps_missing": "⚠️ Missing dependencies: {}",
        "deps_ok": "✅ All dependencies are available",
        "install_deps": "💡 Run: pip install -r requirements.txt",
        "creating_resources": "📁 Creating resources directory...",
        "resources_ready": "✅ Resources directory ready",
        "no_resources": "⚠️ No resources directory found",
        "missing_folders": "⚠️ Missing folders: {}",
        "build_start": "🔐 Starting build process...",
        "build_end": "🏁 Build process finished",
        "elapsed_time": "⏱️ Elapsed time: {:.2f} seconds",
        "error_no_main": "❌ Error: main.py not found!",
        "error_no_pyinstaller": "❌ Error: PyInstaller not installed! Run: pip install pyinstaller",
        "error_build_failed": "❌ Build failed with code: {}",
        "help_clean": "Clean build directories before building",
        "help_verbose": "Verbose output",
        "help_help": "Show this help message",
        "continue_anyway": "⚠️ Continue anyway? (y/n): ",
        "build_cancelled": "❌ Build cancelled by user",
        "all_assets_found": "✅ All asset folders found",
        "error_pyinstaller_exec": "❌ PyInstaller execution error: {}",
    },
    "UA": {
        "app_name": "Secure Pass Pro v4.0 - Скрипт збірки",
        "separator": "=" * 60,
        "cleaning": "🧹 Очищення попередніх збірок...",
        "cleaned": "🧹 Очищено: {}",
        "cannot_clean": "⚠️ Не вдалося очистити {}: {}",
        "building": "🏗️ Збірка для платформи: {}",
        "running": "📦 Запуск PyInstaller...",
        "command": "🔧 Команда: {}",
        "success": "✅ Збірка успішно завершена!",
        "failed": "❌ Помилка збірки!",
        "output_dir": "📁 Папка виведення: {}",
        "generated_files": "📄 Згенеровані файли:",
        "file_info": "   📄 {} ({})",
        "version": "🔢 Версія: {}",
        "python_version": "🐍 Python: {}",
        "platform": "🖥️ Платформа: {}",
        "checking_deps": "📦 Перевірка залежностей...",
        "deps_missing": "⚠️ Відсутні залежності: {}",
        "deps_ok": "✅ Всі залежності доступні",
        "install_deps": "💡 Виконайте: pip install -r requirements.txt",
        "creating_resources": "📁 Створення папки resources...",
        "resources_ready": "✅ Папка resources готова",
        "no_resources": "⚠️ Папка resources не знайдена",
        "missing_folders": "⚠️ Відсутні папки: {}",
        "build_start": "🔐 Запуск процесу збірки...",
        "build_end": "🏁 Процес збірки завершено",
        "elapsed_time": "⏱️ Витрачено часу: {:.2f} секунд",
        "error_no_main": "❌ Помилка: main.py не знайдено!",
        "error_no_pyinstaller": "❌ Помилка: PyInstaller не встановлено! Виконайте: pip install pyinstaller",
        "error_build_failed": "❌ Помилка збірки з кодом: {}",
        "help_clean": "Очистити папки збірки перед збіркою",
        "help_verbose": "Детальний вивід",
        "help_help": "Показати це повідомлення",
        "continue_anyway": "⚠️ Продовжити? (т/н): ",
        "build_cancelled": "❌ Збірка скасована користувачем",
        "all_assets_found": "✅ Всі папки ресурсів знайдено",
        "error_pyinstaller_exec": "❌ Помилка виконання PyInstaller: {}",
    }
}

DEFAULT_LANG = "RU"

# ==================== CONFIGURATION ====================

APP_NAME = "SecurePassPro"
VERSION = "4.0.1"  # Updated to 4.0.1
AUTHOR = "Maxim Melnikov"
COPYRIGHT = f"Copyright (c) 2024-2026 {AUTHOR}"


def get_language() -> str:
    """
    Detect language from config file or system

    Определяет язык из файла конфигурации или системы
    Визначає мову з файлу конфігурації або системи
    """
    config_paths = [
        "config.json",
        "data/config.json",
        ".securepass/config.json",
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    lang = config.get("LANG", "")
                    if lang in ["RU", "EN", "UA"]:
                        return lang
            except json.JSONDecodeError as e:
                # FIXED: Specific exception for JSON decode errors
                # ИСПРАВЛЕНО: Конкретное исключение для ошибок декодирования JSON
                # ВИПРАВЛЕНО: Конкретний виняток для помилок декодування JSON
                print(f"Warning: Failed to parse {config_path}: {e}")
                pass
            except (OSError, IOError, PermissionError) as e:
                # FIXED: Specific exception for file access errors
                # ИСПРАВЛЕНО: Конкретное исключение для ошибок доступа к файлам
                # ВИПРАВЛЕНО: Конкретний виняток для помилок доступу до файлів
                print(f"Warning: Failed to read {config_path}: {e}")
                pass

    system_lang = platform.system()

    if system_lang == "Windows":
        try:
            import ctypes
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            if lang_id == 0x419:
                return "RU"
            elif lang_id == 0x422:
                return "UA"
            else:
                return "EN"
        except (ImportError, AttributeError, OSError) as e:
            # FIXED: Specific exception for Windows API errors
            # ИСПРАВЛЕНО: Конкретное исключение для ошибок Windows API
            # ВИПРАВЛЕНО: Конкретний виняток для помилок Windows API
            print(f"Warning: Failed to detect Windows language: {e}")
            pass

    return DEFAULT_LANG


def get_text(key: str, lang: str = None) -> str:
    """
    Get localized text

    Получить локализованный текст
    Отримати локалізований текст
    """
    if lang is None:
        lang = get_language()
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)


# ==================== BUILD FUNCTIONS ====================

def clean_build_dirs(lang: str = "RU") -> None:
    """
    Clean previous build directories

    Очищает предыдущие папки сборки
    Очищує попередні папки збірки
    """
    texts = TEXTS.get(lang, TEXTS["RU"])
    dirs_to_clean = ["build", "dist", "__pycache__"]

    print(texts["cleaning"])

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
                print(texts["cleaned"].format(dir_name))
            except PermissionError as e:
                # FIXED: Handle permission errors separately
                # ИСПРАВЛЕНО: Обрабатываем ошибки доступа отдельно
                # ВИПРАВЛЕНО: Обробляємо помилки доступу окремо
                print(texts["cannot_clean"].format(dir_name, f"Permission denied: {e}"))
            except (OSError, IOError, shutil.Error) as e:
                # FIXED: Handle other file operation errors
                # ИСПРАВЛЕНО: Обрабатываем другие ошибки файловых операций
                # ВИПРАВЛЕНО: Обробляємо інші помилки файлових операцій
                print(texts["cannot_clean"].format(dir_name, e))


def check_dependencies(lang: str = "RU") -> bool:
    """
    Check if required dependencies are installed

    Проверяет установку необходимых зависимостей
    Перевіряє встановлення необхідних залежностей
    """
    texts = TEXTS.get(lang, TEXTS["RU"])

    print(texts["checking_deps"])

    missing = []
    
    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError as e:
        print(f"Debug: PyInstaller import failed: {e}")
        missing.append("pyinstaller")

    critical_modules = [
        ("customtkinter", "customtkinter"),
        ("PIL", "Pillow"),
        ("cryptography", "cryptography"),
    ]

    for module_name, package_name in critical_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            print(f"Debug: {module_name} import failed: {e}")
            missing.append(package_name)
        except (ValueError, TypeError, AttributeError, ModuleNotFoundError) as e:
            # FIXED: Added ModuleNotFoundError to exception list
            # ИСПРАВЛЕНО: Добавлен ModuleNotFoundError в список исключений
            # ВИПРАВЛЕНО: Додано ModuleNotFoundError до списку винятків
            print(f"Warning: Error checking {module_name}: {e}")
            missing.append(package_name)

    if missing:
        print(texts["deps_missing"].format(", ".join(missing)))
        print(texts["install_deps"])

        response = input(texts["continue_anyway"]).lower()
        if response in ['y', 'yes', 'д', 'да', 'yes', 'так', 'т']:
            return True
        else:
            print(texts["build_cancelled"])
            return False

    print(texts["deps_ok"])
    return True


def ensure_resources(lang: str = "RU") -> None:
    """
    Verify that required project asset folders exist.

    Проверяет наличие обязательных папок проекта.
    Перевіряє наявність обов'язкових папок проекту.
    """
    texts = TEXTS.get(lang, TEXTS["RU"])

    required = ["Icons", "Sounds", "Resources", "Langs",
                "core", "gui", "security", "storage", "utils"]
    missing = [d for d in required if not Path(d).exists()]

    if missing:
        print(texts.get("missing_folders", "⚠️ Missing folders: " + ", ".join(missing)))
    else:
        print(texts.get("all_assets_found", "✅ All asset folders found"))


def get_pyinstaller_command(lang: str = "RU") -> list:
    """
    Generate PyInstaller command based on platform

    Генерирует команду PyInstaller в зависимости от платформы
    Генерує команду PyInstaller залежно від платформи
    """
    sep = os.pathsep  # ";" on Windows, ":" on Linux/macOS

    if platform.system() == "Windows":
        main_script = "Secure_Pass_Pro.pyw"
        if not os.path.exists(main_script):
            main_script = "main.py"
    else:
        main_script = "main.py"
        if not os.path.exists(main_script):
            main_script = "Secure_Pass_Pro.pyw"

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--clean",
        "--name", APP_NAME,
    ]

    # ── Icon ──────────────────────────────────────────────────────────────
    if platform.system() == "Windows":
        if os.path.exists("Icons/icon.ico"):
            cmd.extend(["--icon", "Icons/icon.ico"])
    elif platform.system() == "Darwin":
        if os.path.exists("Icons/icon.icns"):
            cmd.extend(["--icon", "Icons/icon.icns"])
            cmd.append("--osx-bundle-identifier=com.securepasspro.app")
            cmd.append("--target-arch=universal2")
    elif platform.system() == "Linux":
        cmd.append("--strip")

    # ── Data files ────────────────────────────────────────────────────────
    data_files = [
        ("Icons/icon.ico",              "Icons"),
        ("Icons/app_icon.ico",          "Icons"),
        ("Icons/Shield_green.png",      "Icons"),
        ("Icons/Shield_red.png",        "Icons"),
        ("Icons/Shield_orange.png",     "Icons"),
        ("Icons/Shield_yellow.png",     "Icons"),
        ("Sounds/Mouse Click.mp3",      "Sounds"),
        ("Resources/DejaVuSansCondensed.ttf", "Resources"),
        ("config.example.json",         "."),
    ]
    # Whole package folders
    dir_data = [
        ("core",     "core"),
        ("gui",      "gui"),
        ("security", "security"),
        ("storage",  "storage"),
        ("utils",    "utils"),
        ("Langs",    "Langs"),
        ("Icons",    "Icons"),
        ("Sounds",   "Sounds"),
        ("Resources","Resources"),
    ]

    for src, dst in data_files:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{sep}{dst}"])

    for src, dst in dir_data:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{sep}{dst}"])

    # ── Hidden imports ────────────────────────────────────────────────────
    hidden_imports = [
        # UI
        "customtkinter", "tkinter",
        "PIL._tkinter_finder", "PIL.Image", "PIL.ImageTk",
        "PIL.ImageDraw", "PIL.ImageFilter", "PIL.ImageOps",
        # Crypto
        "argon2", "argon2._ffi", "argon2._legacy",
        "cryptography",
        "cryptography.hazmat.primitives.ciphers.aead",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "cryptography.hazmat.primitives.kdf.scrypt",
        "cryptography.hazmat.backends",
        "cryptography.hazmat.backends.openssl",
        "cryptography.hazmat.backends.openssl.aead",
        "cryptography.exceptions",
        "cryptography.hazmat.primitives.hashes",
        "cryptography.hazmat.primitives.asymmetric.padding",
        "cryptography.hazmat.primitives.asymmetric.rsa",
        "cryptography.hazmat.primitives.asymmetric.utils",
        "cryptography.hazmat.primitives.serialization",
        "cryptography.hazmat.primitives.constant_time",
        "cryptography.hazmat.primitives.keywrap",
        "cryptography.hazmat.primitives.padding",
        "cryptography.utils",
        # DB
        "sqlcipher3", "sqlite3",
        # Export / QR / PDF
        "fpdf", "qrcode", "qrcode.image.svg", "qrcode.image.pil",
        # Windows
        "ctypes", "ctypes.wintypes",
        "winshell", "win32com.client", "win32com",
        "win32api", "win32con", "win32gui", "win32process",
        # Network / email
        "webbrowser", "socket", "ssl",
        "urllib", "urllib.request", "urllib.parse", "urllib.error",
        "http.client",
        "email", "email.mime.text", "email.mime.multipart",
        "email.mime.base", "email.encoders",
        "requests", "psutil",
        # XML
        "xml", "xml.etree.ElementTree",
        "xml.dom", "xml.dom.minidom",
        "defusedxml",
        # Stdlib
        "secrets", "hashlib", "hmac", "datetime", "re",
        "subprocess", "threading", "time", "json",
        "tempfile", "shutil", "platform", "io", "base64",
        "zlib", "bz2", "lzma", "importlib", "importlib.util",
        "queue", "collections", "collections.abc", "abc",
        "copy", "copyreg", "struct", "array", "math",
        "random", "string", "logging", "logging.handlers",
        "traceback", "inspect", "pkgutil",
        "pkg_resources", "pkg_resources.extern",
        # Standard debugger (must NOT be the pdbpp variant)
        "pdb", "bdb", "cmd", "code", "codeop",
        # KDBX / pykeepass dependencies
        "pykeepass", "construct", "construct.lib",
        "lxml", "lxml.etree",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # ── Collect-all ────────────────────────────────────────────────────────
    for pkg in ["customtkinter", "qrcode", "PIL", "argon2", "cryptography", "fpdf", "pykeepass", "construct"]:
        cmd.extend(["--collect-all", pkg])

    # ── Exclude dev-only modules that break the frozen exe ──────────
    # pdbpp shadows stdlib pdb; if it is installed in the build env,
    # PyInstaller bundles the patched pdb.py but NOT pdbpp.py itself,
    # causing FileNotFoundError at runtime.
    for mod in ["pdbpp", "pdbpp_utils", "fancycompleter", "pyrepl"]:
        cmd.extend(["--exclude-module", mod])

    # Add the runtime hook that restores the clean stdlib pdb
    import os as _os
    _base = _os.path.dirname(_os.path.abspath(__file__))
    _hook = _os.path.join(_base, "rthooks", "rthook_pdb_fix.py")
    if _os.path.exists(_hook):
        cmd.extend(["--runtime-hook", _hook])
        print(f"  Runtime hook: {_hook}")

    # Point PyInstaller at our custom hooks/ folder
    _hooks_dir = _os.path.join(_base, "hooks")
    if _os.path.isdir(_hooks_dir):
        cmd.extend(["--additional-hooks-dir", _hooks_dir])
        print(f"  Custom hooks dir: {_hooks_dir}")

    cmd.append(main_script)
    return cmd


def get_file_size_str(size: int) -> str:
    """
    Format file size for display

    Форматирует размер файла для отображения
    Форматує розмір файлу для відображення
    """
    if size > 1024 * 1024:
        return f"{size / (1024*1024):.1f} MB"
    elif size > 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size} B"


def build(lang: str = "RU", clean: bool = True, verbose: bool = False) -> bool:
    """
    Main build function

    Основная функция сборки
    Головна функція збірки
    """
    texts = TEXTS.get(lang, TEXTS["RU"])
    start_time = datetime.now()

    print(texts["separator"])
    print(texts["app_name"])
    print(texts["separator"])

    print(texts["version"].format(VERSION))
    print(texts["python_version"].format(sys.version.split()[0]))
    print(texts["platform"].format(platform.system()))
    print(texts["separator"])

    if not os.path.exists("main.py") and not os.path.exists("Secure_Pass_Pro.pyw"):
        print(texts["error_no_main"])
        return False

    if not check_dependencies(lang):
        return False

    if clean:
        clean_build_dirs(lang)

    ensure_resources(lang)

    cmd = get_pyinstaller_command(lang)

    print(texts["separator"])
    print(texts["building"].format(platform.system()))
    print(texts["running"])

    if verbose:
        print(texts["command"].format(" ".join(cmd)))

    print(texts["separator"])

    # Run PyInstaller with proper error handling
    return_code = 1
    try:
        # Use Popen with stdout/stderr capture in verbose mode, otherwise silent
        if verbose:
            result = subprocess.run(cmd, capture_output=False)
        else:
            result = subprocess.run(cmd, capture_output=False)
        return_code = result.returncode
    except subprocess.CalledProcessError as e:
        # FIXED: Handle subprocess errors specifically
        # ИСПРАВЛЕНО: Обрабатываем ошибки subprocess конкретно
        # ВИПРАВЛЕНО: Обробляємо помилки subprocess конкретно
        print(texts["error_build_failed"].format(e.returncode))
        if verbose and e.stderr:
            print(e.stderr.decode('utf-8', errors='replace'))
        return False
    except FileNotFoundError as _:
        # FIXED: Handle PyInstaller not found
        # ИСПРАВЛЕНО: Обрабатываем случай, когда PyInstaller не найден
        # ВИПРАВЛЕНО: Обробляємо випадок, коли PyInstaller не знайдено
        print(texts["error_no_pyinstaller"])
        if verbose:
            print(f"Details: {_}")
        return False
    except (OSError, IOError, PermissionError) as e:
        # FIXED: Handle OS-level errors
        # ИСПРАВЛЕНО: Обрабатываем ошибки на уровне ОС
        # ВИПРАВЛЕНО: Обробляємо помилки на рівні ОС
        print(texts["error_pyinstaller_exec"].format(str(e)))
        return False

    elapsed = (datetime.now() - start_time).total_seconds()

    print(texts["separator"])

    if return_code == 0:
        print(texts["success"])
        print(texts["output_dir"].format("dist/"))

        if os.path.exists("dist"):
            try:
                files = os.listdir("dist")
                if files:
                    print(texts["generated_files"])
                    for f in files:
                        fpath = os.path.join("dist", f)
                        try:
                            size = os.path.getsize(fpath)
                            print(texts["file_info"].format(f, get_file_size_str(size)))
                        except (OSError, IOError, PermissionError) as e:
                            # FIXED: Handle file info errors gracefully
                            # ИСПРАВЛЕНО: Обрабатываем ошибки получения информации о файле
                            # ВИПРАВЛЕНО: Обробляємо помилки отримання інформації про файл
                            print(texts["file_info"].format(f, f"Error: {e}"))
            except (OSError, IOError, PermissionError) as e:
                print(f"Warning: Failed to list dist directory: {e}")

        print(texts["elapsed_time"].format(elapsed))
        print(texts["build_end"])
        print(texts["separator"])
        return True
    else:
        print(texts["failed"])
        print(texts["error_build_failed"].format(return_code))
        print(texts["separator"])
        return False


# ==================== MAIN ENTRY POINT ====================

def main():
    """
    Main entry point

    Главная точка входа
    Головна точка входу
    """
    parser = argparse.ArgumentParser(
        description="Secure Pass Pro - Build Script / Скрипт сборки / Скрипт збірки"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help=get_text("help_clean", "EN")
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help=get_text("help_verbose", "EN")
    )
    parser.add_argument(
        "--lang",
        choices=["RU", "EN", "UA"],
        default=None,
        help="Language / Язык / Мова"
    )

    try:
        args = parser.parse_args()
    except SystemExit as e:
        # FIXED: Handle argument parsing errors gracefully
        # ИСПРАВЛЕНО: Обрабатываем ошибки парсинга аргументов
        # ВИПРАВЛЕНО: Обробляємо помилки парсингу аргументів
        sys.exit(e.code)

    lang = args.lang if args.lang else get_language()

    success = build(
        lang=lang,
        clean=not args.no_clean,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":

    main()
