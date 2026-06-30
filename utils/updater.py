"""
Compatibility shim — re-exports from the utils.updater package.
Шим совместимости — реэкспортирует из пакета utils.updater.
Шим сумісності — реекспортує з пакету utils.updater.

The updater has been split into:
  utils/updater/models.py      — UpdateStatus, ReleaseInfo, UpdateManifest
  utils/updater/integrity.py   — IntegrityChecker, IntegrityManifest
  utils/updater/core.py        — SecureUpdater
  utils/updater/__init__.py    — convenience functions + re-exports
"""
from __future__ import annotations
# Prevent Python from picking up this file when the package directory exists.
# The package takes precedence when both exist in the same directory.
from utils.updater import (          # noqa: F401
    UpdateStatus, ReleaseInfo, UpdateManifest,
    IntegrityChecker, IntegrityManifest,
    SecureUpdater,
    check_for_updates, perform_update, rollback_update,
    verify_installation, get_current_version, get_update_status,
    CURRENT_VERSION, GITHUB_API, UPDATES_DIR,
    DOWNLOAD_CHUNK_SIZE, NETWORK_ERRORS,
    MAX_UPDATE_SIZE, UPDATE_CHECK_TIMEOUT, ROLLBACK_DIR,
    INTEGRITY_MANIFEST, EXPECTED_SHA256,
)
