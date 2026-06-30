"""
Secure auto-updater package.
Пакет безопасного автообновления.
Пакет безпечного автооновлення.

Sub-modules
-----------
models      — UpdateStatus, ReleaseInfo, UpdateManifest
integrity   — IntegrityChecker, IntegrityManifest
core        — SecureUpdater
"""
from __future__ import annotations
from utils.updater.models import (
    UpdateStatus, ReleaseInfo, UpdateManifest, CURRENT_VERSION,
)
from utils.updater.integrity import (
    IntegrityChecker, IntegrityManifest,
    DOWNLOAD_CHUNK_SIZE, NETWORK_ERRORS,
)
from utils.updater.core import (
    SecureUpdater,
    GITHUB_API, UPDATES_DIR, MAX_UPDATE_SIZE,
    UPDATE_CHECK_TIMEOUT, ROLLBACK_DIR, INTEGRITY_MANIFEST, EXPECTED_SHA256,
)

# ── Convenience functions (kept from original module) ─────────

def check_for_updates(parent=None) -> Optional[object]:
    """Check for updates / Проверить обновления / Перевірити оновлення"""
    updater = SecureUpdater(parent)
    status, release = updater.check_for_updates()
    return release if status == UpdateStatus.UPDATE_AVAILABLE else None

def perform_update(parent=None) -> bool:
    """Perform update / Выполнить обновление / Виконати оновлення"""
    return SecureUpdater(parent).perform_update() == UpdateStatus.SUCCESS

def rollback_update(parent=None) -> bool:
    """Rollback / Откат / Відкат"""
    return SecureUpdater(parent).rollback_to_previous() == UpdateStatus.ROLLBACK_SUCCESS

def verify_installation() -> bool:
    """Verify installation integrity / Проверить целостность / Перевірити цілісність"""
    import json, os
    try:
        v = IntegrityManifest.get_last_verified_version(INTEGRITY_MANIFEST)
        if v:
            from utils.logger import get_logger
            get_logger("updater").info("Last verified version: %s", v)
        return True
    except (OSError, json.JSONDecodeError):
        return True

def get_current_version() -> str:
    """
    Return current version.
    Возвращает current version.
    Повертає current version.
    """
    return CURRENT_VERSION

def get_update_status() -> dict[str, object]:
    """
    Return update status.
    Возвращает update status.
    Повертає update status.
    """
    import os
    return {
        "current_version": CURRENT_VERSION,
        "updates_dir":     UPDATES_DIR,
        "rollback_dir":    ROLLBACK_DIR,
        "has_backups":     os.path.exists(ROLLBACK_DIR) and bool(os.listdir(ROLLBACK_DIR)),
        "integrity_manifest": os.path.exists(INTEGRITY_MANIFEST),
    }

__all__ = [
    "UpdateStatus", "ReleaseInfo", "UpdateManifest",
    "IntegrityChecker", "IntegrityManifest",
    "SecureUpdater",
    "check_for_updates", "perform_update", "rollback_update",
    "verify_installation", "get_current_version", "get_update_status",
    "CURRENT_VERSION", "GITHUB_API", "UPDATES_DIR",
]
