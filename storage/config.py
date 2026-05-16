"""
Configuration manager
"""
import os
import sys
import json
import ctypes
from typing import Dict, Any

# Путь рядом с EXE или скриптом — тот же, что в main_window.py
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(_BASE_DIR, "data")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def _hide_dir(path: str) -> None:
    """Скрывает папку на Windows (атрибут Hidden)."""
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
        except Exception:
            pass


class Config:
    """Application settings manager"""

    _instance = None
    _data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load config from file"""
        if not os.path.exists(CONFIG_FILE):
            self._data = {}
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            self._data = {}

    def save(self) -> None:
        """Save config to file"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        _hide_dir(CONFIG_DIR)          # скрываем сразу после создания
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        """Get config value"""
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        """Set config value"""
        self._data[key] = value
        self.save()

    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple config values"""
        self._data.update(updates)
        self.save()
