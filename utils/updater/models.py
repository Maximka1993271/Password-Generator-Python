"""
Data models for the update system: UpdateStatus, ReleaseInfo, UpdateManifest.
Модели данных системы обновлений.
Моделі даних системи оновлень.
"""
from __future__ import annotations
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("updater.models")

CURRENT_VERSION = "4.0.1"


class UpdateStatus(Enum):
    """Update check status / Статус проверки обновлений / Статус перевірки оновлень"""
    NO_UPDATE        = "no_update"
    UPDATE_AVAILABLE = "update_available"
    CHECK_FAILED     = "check_failed"
    DOWNLOAD_FAILED  = "download_failed"
    VERIFY_FAILED    = "verify_failed"
    INSTALL_FAILED   = "install_failed"
    SIGNATURE_INVALID  = "signature_invalid"
    INTEGRITY_FAILED   = "integrity_failed"
    ROLLBACK_SUCCESS   = "rollback_success"
    ROLLBACK_FAILED    = "rollback_failed"
    SUCCESS          = "success"


@dataclass
class ReleaseInfo:
    """Release information / Информация о релизе / Інформація про реліз"""
    version:       str
    tag_name:      str
    published_at:  str
    download_url:  str
    signature_url: str
    hash_url:      str
    body:          str
    size:          int
    hash_sha256:   str = ""
    signature:     str = ""

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> Optional["ReleaseInfo"]:
        """
        Handle from api response.
        Обработать from api response.
        Обробити from api response.
        """
        try:
            assets    = data.get("assets", [])
            exe_asset = sig_asset = hash_asset = None
            for asset in assets:
                name         = asset.get("name", "")
                download_url = asset.get("browser_download_url", "")
                if not download_url.startswith("https://"):
                    continue
                if name.endswith(".exe") and "SecurePassPro" in name:
                    exe_asset = asset
                elif name.endswith(".exe.sig"):
                    sig_asset = asset
                elif name.endswith(".sha256"):
                    hash_asset = asset
            if not exe_asset:
                return None
            return cls(
                version      = data.get("tag_name", "").lstrip("v"),
                tag_name     = data.get("tag_name", ""),
                published_at = data.get("published_at", ""),
                download_url = exe_asset.get("browser_download_url", ""),
                signature_url= sig_asset.get("browser_download_url", "") if sig_asset else "",
                hash_url     = hash_asset.get("browser_download_url", "") if hash_asset else "",
                body         = data.get("body", ""),
                size         = exe_asset.get("size", 0),
            )
        except (KeyError, ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to parse release info: %s", e)
            return None

    def is_newer_than(self, current_version: str) -> bool:
        """
        Return True if newer than.
        True, если newer than.
        True, якщо newer than.
        """
        def parse(v: str) -> Tuple[int, ...]:
            try:
                return tuple(int(x) for x in v.split(".")[:3])
            except ValueError as e:
                logger.debug("Failed to parse version '%s': %s", v, e)
                return (0, 0, 0)
        try:
            return parse(self.version) > parse(current_version)
        except (TypeError, AttributeError) as e:
            logger.error("Version comparison error: %s", e)
            return False

    def is_valid_version_format(self) -> bool:
        """
        Return True if valid version format.
        True, если valid version format.
        True, якщо valid version format.
        """
        return bool(re.match(r"^\d+\.\d+\.\d+$", self.version))


@dataclass
class UpdateManifest:
    """Update manifest / Манифест обновления / Маніфест оновлення"""
    version:          str
    timestamp:        str
    previous_version: str
    file_hash:        str
    file_size:        int
    signature:        str

    def save(self, path: str) -> bool:
        """
        Handle save.
        Обработать save.
        Обробити save.
        """
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, indent=2)
            return True
        except (OSError, IOError, TypeError) as e:
            logger.error("Failed to save manifest: %s", e)
            return False

    @classmethod
    def load(cls, path: str) -> Optional["UpdateManifest"]:
        """
        Handle load.
        Обработать load.
        Обробити load.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            return cls(**{k: d.get(k, "") for k in cls.__dataclass_fields__})
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.error("Failed to load manifest: %s", e)
            return None
