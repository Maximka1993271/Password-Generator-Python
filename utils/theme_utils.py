"""
Theme utilities for SecurePassPro
Утилиты для работы с темами оформления SecurePassPro
Утиліти для роботи з темами оформлення SecurePassPro

English:
This module provides theme detection and management utilities.

Русский:
Этот модуль предоставляет утилиты для определения и управления темами.

Українська:
Цей модуль надає утиліти для визначення та управління темами.
"""
from __future__ import annotations

import os
import sys
import json
import platform
from typing import Optional, Tuple
from pathlib import Path

import customtkinter as ctk

from utils.logger import get_logger
from utils.paths import get_config_file, get_config_dir
from utils.subprocess_utils import silent_run as _silent_run

logger = get_logger("theme_utils")


class ThemeManager:
    """
    Theme manager for SecurePassPro
    Менеджер тем для SecurePassPro
    Менеджер тем для SecurePassPro
    """

    THEMES = {
        "Dark": ("#2b2b2b", "#1f1f1f", "#3a3a3a", "#ffffff"),
        "Light": ("#ebebeb", "#f0f0f0", "#d9d9d9", "#000000"),
        "System": None  # Will be detected from OS
    }

    @staticmethod
    def get_system_theme() -> str:
        """
        Detect system theme (Windows, macOS, Linux)
        Определить системную тему (Windows, macOS, Linux)
        Визначити системну тему (Windows, macOS, Linux)
        """
        system = platform.system()

        # Windows
        if system == "Windows":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return "Light" if value == 1 else "Dark"
            except (ImportError, OSError, IOError, PermissionError, FileNotFoundError, ValueError, TypeError, AttributeError):
                # Key may not exist or error accessing registry
                return "Dark"
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Unexpected error detecting Windows theme: {e}")
                return "Dark"

        # macOS
        elif system == "Darwin":
            try:
                import subprocess
                result = _silent_run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and "Dark" in result.stdout:
                    return "Dark"
                return "Light"
            except (subprocess.SubprocessError, FileNotFoundError, OSError, TimeoutError) as e:
                logger.debug(f"Error detecting macOS theme: {e}")
                return "Dark"
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Unexpected error detecting macOS theme: {e}")
                return "Dark"

        # Linux (GNOME)
        elif system == "Linux":
            try:
                import subprocess
                result = _silent_run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    theme = result.stdout.strip().strip("'")
                    if "dark" in theme.lower() or "dark" in theme.lower():
                        return "Dark"
                return "Light"
            except (subprocess.SubprocessError, FileNotFoundError, OSError, TimeoutError) as e:
                logger.debug(f"Error detecting Linux theme: {e}")
                return "Dark"
            except (OSError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Unexpected error detecting Linux theme: {e}")
                return "Dark"

        # Fallback
        return "Dark"

    @staticmethod
    def get_current_theme() -> str:
        """
        Get current theme from config
        Получить текущую тему из конфига
        Отримати поточну тему з конфігу
        """
        config_file = get_config_file()

        if not os.path.exists(config_file):
            return "Dark"

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                theme = config.get("THEME", "Dark")
                if theme in ["Dark", "Light", "System"]:
                    return theme
                return "Dark"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in config: {e}")
            return "Dark"
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File read error in config: {e}")
            return "Dark"
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error(f"Config parsing error: {e}")
            return "Dark"
        except (KeyError, AttributeError, TypeError) as e:
            logger.debug(f"Unexpected error reading config: {e}")
            return "Dark"

    @staticmethod
    def apply_theme(widget: ctk.CTk, theme: str) -> None:
        """
        Apply theme to widget
        Применить тему к виджету
        Застосувати тему до віджета
        """
        if theme == "System":
            theme = ThemeManager.get_system_theme()

        if theme == "Dark":
            ctk.set_appearance_mode("dark")
        elif theme == "Light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

        if widget:
            try:
                widget.update_idletasks()
            except (RuntimeError, AttributeError, tkinter.TclError) as e:
                logger.debug(f"Error updating widget after theme change: {e}")

    @staticmethod
    def save_theme(theme: str) -> bool:
        """
        Save theme to config
        Сохранить тему в конфиг
        Зберегти тему в конфіг
        """
        config_file = get_config_file()

        try:
            # Ensure config directory exists
            config_dir = get_config_dir()
            os.makedirs(config_dir, exist_ok=True)

            # Load existing config or create new
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except json.JSONDecodeError:
                    config = {}
                except (OSError, IOError, PermissionError) as e:
                    logger.error(f"Error reading config: {e}")
                    config = {}
            else:
                config = {}

            config["THEME"] = theme

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except json.JSONDecodeError as e:
            logger.error(f"JSON encode error: {e}")
            return False
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"File write error: {e}")
            return False
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Config save error: {e}")
            return False
        except (KeyError, AttributeError, TypeError) as e:
            logger.debug(f"Unexpected error saving theme: {e}")
            return False

    @staticmethod
    def get_theme_colors(theme: str) -> Tuple[str, str, str, str]:
        """
        Get theme colors (bg, fg, button, text)
        Получить цвета темы (фон, передний план, кнопка, текст)
        Отримати кольори теми (фон, передній план, кнопка, текст)
        """
        if theme == "System":
            theme = ThemeManager.get_system_theme()

        if theme == "Dark":
            return ("#2b2b2b", "#1f1f1f", "#3a3a3a", "#ffffff")
        else:  # Light
            return ("#ebebeb", "#f0f0f0", "#d9d9d9", "#000000")


def get_theme_from_config() -> str:
    """
    Get theme from config file (backward compatibility)
    Получить тему из файла конфига (обратная совместимость)
    Отримати тему з файлу конфігу (зворотна сумісність)
    """
    config_file = get_config_file()

    if not os.path.exists(config_file):
        return "Dark"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            theme = config.get("THEME", "Dark")
            if theme in ["Dark", "Light", "System"]:
                return theme
            return "Dark"
    except json.JSONDecodeError:
        return "Dark"
    except (OSError, IOError, PermissionError):
        return "Dark"
    except (ValueError, TypeError, KeyError, AttributeError):
        return "Dark"
    except (KeyError, AttributeError, TypeError, ValueError):
        return "Dark"


def detect_system_theme() -> str:
    """
    Detect system theme (backward compatibility)
    Определить системную тему (обратная совместимость)
    Визначити системну тему (зворотна сумісність)
    """
    return ThemeManager.get_system_theme()


def apply_theme_from_config(widget: ctk.CTk) -> None:
    """
    Apply theme from config to widget
    Применить тему из конфига к виджету
    Застосувати тему з конфігу до віджета
    """
    theme = get_theme_from_config()
    ThemeManager.apply_theme(widget, theme)


def save_theme_to_config(theme: str) -> bool:
    """
    Save theme to config (backward compatibility)
    Сохранить тему в конфиг (обратная совместимость)
    Зберегти тему в конфіг (зворотна сумісність)
    """
    return ThemeManager.save_theme(theme)


def get_theme_variant() -> str:
    """
    Get actual theme variant (resolves System)
    Получить актуальный вариант темы (разрешает System)
    Отримати актуальний варіант теми (розв'язує System)
    """
    theme = get_theme_from_config()
    if theme == "System":
        return detect_system_theme()
    return theme


# Backward compatibility function
def get_system_theme() -> str:
    """
    Backward compatibility wrapper for get_system_theme
    Обёртка для обратной совместимости
    Обгортка для зворотної сумісності
    """
    return ThemeManager.get_system_theme()