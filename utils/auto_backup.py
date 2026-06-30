"""
Automatic database backup utility for SecurePassPro.
Creates timestamped .bak copies of the DB file on each app start.
Keeps only the last N backups (default 7).
"""
from __future__ import annotations

import os
import shutil
import logging
import datetime
from pathlib import Path

logger = logging.getLogger("auto_backup")

_DEFAULT_KEEP = 7
_BACKUP_SUFFIX = ".bak"
_TS_FORMAT = "%Y%m%d_%H%M%S"


def run_backup(db_path: str, backup_dir: str = None, keep: int = _DEFAULT_KEEP) -> str | None:
    """
    Copy *db_path* to *backup_dir* with a timestamp suffix.
    If *backup_dir* is None, creates a 'backups/' folder next to the DB file.
    Prunes old backups, keeping the *keep* most recent.
    Returns the path of the new backup, or None on failure.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        logger.debug(f"DB not found, skipping backup: {db_path}")
        return None

    if backup_dir is None:
        backup_dir = db_path.parent / "backups"
    backup_dir = Path(backup_dir)

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Cannot create backup directory {backup_dir}: {e}")
        return None

    ts = datetime.datetime.now().strftime(_TS_FORMAT)
    stem = db_path.stem
    dest = backup_dir / f"{stem}_{ts}{_BACKUP_SUFFIX}"

    try:
        shutil.copy2(db_path, dest)
        logger.info(f"Backup created: {dest}")
    except (OSError, shutil.Error) as e:
        logger.error(f"Backup failed: {e}")
        return None

    # Prune old backups
    try:
        existing = sorted(
            backup_dir.glob(f"{stem}_*{_BACKUP_SUFFIX}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in existing[keep:]:
            try:
                old.unlink()
                logger.debug(f"Pruned old backup: {old.name}")
            except OSError as e:
                logger.warning(f"Cannot prune {old.name}: {e}")
    except OSError as e:
        logger.warning(f"Backup pruning error: {e}")

    return str(dest)


def get_backup_list(db_path: str, backup_dir: str = None) -> list:
    """Return sorted list of backup file paths (newest first)."""
    db_path = Path(db_path)
    if backup_dir is None:
        backup_dir = db_path.parent / "backups"
    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        return []
    stem = db_path.stem
    files = sorted(
        backup_dir.glob(f"{stem}_*{_BACKUP_SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [str(f) for f in files]


__all__ = ["run_backup", "get_backup_list"]
