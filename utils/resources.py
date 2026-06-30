"""
Resource-path helpers (bundled PyInstaller or dev tree).
Вспомогательные функции для путей к ресурсам.
Допоміжні функції для шляхів до ресурсів.
"""
from __future__ import annotations
import os
import sys
from typing import Optional

_resource_cache: dict = {}

def get_resource_path(filename: str, force_recheck: bool = False) -> Optional[str]:
    """Return the absolute path to *filename* in the resources folder."""
    if not force_recheck and filename in _resource_cache:
        return _resource_cache[filename]
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, filename))
        candidates.append(os.path.join(os.path.dirname(sys.executable), filename))
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for sub in ("Resources", "resources", "Icons", "Sounds", ""):
        candidates.append(os.path.join(base, sub, filename))
    for path in candidates:
        if os.path.exists(path):
            _resource_cache[filename] = path
            return path
    _resource_cache[filename] = ""
    return None

def clear_resource_cache() -> None:
    """Flush the resource-path cache."""
    _resource_cache.clear()
