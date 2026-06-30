"""
SHA256 integrity checking for update files.
Проверка целостности файлов обновлений по SHA256.
Перевірка цілісності файлів оновлень за SHA256.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import re
import ssl
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from utils.logger import get_logger
from utils.updater.models import ReleaseInfo, CURRENT_VERSION

logger = get_logger("updater.integrity")

DOWNLOAD_CHUNK_SIZE = 8192
NETWORK_ERRORS = (URLError, HTTPError, ConnectionError, TimeoutError, ssl.SSLError)


class IntegrityChecker:
    """SHA256 integrity checker / Проверка SHA256 / Перевірка SHA256"""

    @staticmethod
        # ── Streaming SHA-256 ─────────────────────────────────────
    # We read in 8 kB chunks so large update binaries (>50 MB) do not
    # require loading the entire file into RAM at once.
    def calculate_sha256(file_path: str) -> Optional[str]:
        """
        Handle calculate sha256.
        Обработать calculate sha256.
        Обробити calculate sha256.
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(DOWNLOAD_CHUNK_SIZE), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, IOError, ValueError) as e:
            logger.error("SHA256 calc failed: %s", e)
            return None

    @staticmethod
    def verify_sha256(file_path: str, expected_hash: str) -> bool:
        """
        Verify sha256.
        Подтвердить sha256.
        Підтвердити sha256.
        """
        if not expected_hash or not re.match(r"^[a-fA-F0-9]{64}$", expected_hash):
            logger.error("Invalid or missing expected hash")
            return False
        actual = IntegrityChecker.calculate_sha256(file_path)
        if actual is None:
            return False
        ok = hmac.compare_digest(actual.lower(), expected_hash.lower())
        if not ok:
            logger.error("SHA256 mismatch: expected %.16s…, got %.16s…",
                         expected_hash, actual)
        return ok

    @staticmethod
    def verify_release_hash(release: ReleaseInfo) -> bool:
        """
        Verify release hash.
        Подтвердить release hash.
        Підтвердити release hash.
        """
        if not release.hash_url:
            return True
        try:
            req = Request(release.hash_url,
                          headers={"User-Agent": f"SecurePassPro/{CURRENT_VERSION}"})
            with urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8").strip()
            parts = content.split()
            expected = parts[0] if parts else ""
            if len(expected) == 64:
                release.hash_sha256 = expected
                return True
            logger.error("Invalid hash in release: %.50s", content)
            return False
        except NETWORK_ERRORS as e:
            logger.error("Hash download failed: %s", e)
            return False
        except (ValueError, IndexError) as e:
            logger.error("Hash parse error: %s", e)
            return False

    @staticmethod
    def verify_update_integrity(update_path: str, release: ReleaseInfo,
                                 integrity_manifest_path: str = "") -> bool:
        """
        Verify update integrity.
        Подтвердить update integrity.
        Підтвердити update integrity.
        """
        if not os.path.exists(update_path):
            logger.error("Update file not found: %s", update_path)
            return False
        try:
            file_size = os.path.getsize(update_path)
            if file_size == 0:
                logger.error("Update file is empty")
                return False
            if release.size > 0 and abs(file_size - release.size) > 1024:
                logger.error("Size mismatch: expected %d, got %d", release.size, file_size)
                return False
        except (OSError, ValueError) as e:
            logger.error("File size check failed: %s", e)
            return False

        if release.hash_sha256:
            if not IntegrityChecker.verify_sha256(update_path, release.hash_sha256):
                logger.error("SHA256 failed — update aborted")
                return False

        # Write integrity manifest if path supplied
        if integrity_manifest_path:
            IntegrityManifest(
                file_path=update_path,
                file_hash=IntegrityChecker.calculate_sha256(update_path) or "",
                file_size=file_size,
                verified_at=datetime.now().isoformat(),
                version=release.version,
            ).save(integrity_manifest_path)

        logger.info("Integrity verification passed")
        return True


class IntegrityManifest:
    """Integrity manifest / Манифест целостности / Маніфест цілісності"""

    def __init__(self, file_path: str, file_hash: str, file_size: int,
                 verified_at: str, version: str):
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.file_path  = file_path
        self.file_hash  = file_hash
        self.file_size  = file_size
        self.verified_at = verified_at
        self.version    = version

    def save(self, manifest_path: str = "") -> bool:
        """
        Handle save.
        Обработать save.
        Обробити save.
        """
        try:
            path = manifest_path
            manifests = []
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    manifests = json.load(f)
            manifests.append(self.__dict__)
            if len(manifests) > 10:
                manifests = manifests[-10:]
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(manifests, f, indent=2)
            return True
        except (OSError, TypeError, json.JSONDecodeError) as e:
            logger.error("Integrity manifest save failed: %s", e)
            return False

    @staticmethod
    def get_last_verified_version(manifest_path: str) -> Optional[str]:
        """
        Return last verified version.
        Возвращает last verified version.
        Повертає last verified version.
        """
        try:
            if not os.path.exists(manifest_path):
                return None
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data[-1].get("version") if data else None
        except (OSError, json.JSONDecodeError, KeyError):
            return None
