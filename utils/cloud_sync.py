"""
Cloud Sync — WebDAV для Secure Pass Pro
Cloud Sync — WebDAV for Secure Pass Pro
Cloud Sync — WebDAV для Secure Pass Pro

Providers: Nextcloud, ownCloud, Yandex Disk, Box, any WebDAV
Strategies: upload | download | newest (timestamp-based)

Зашифрованный .db файл безопасен для любого облака —
ключ никогда не покидает устройство.

Usage / Использование:
    from utils.cloud_sync import WebDAVSync, create_sync_from_config
    sync = WebDAVSync("https://cloud.example.com/dav/", "user", "pass")
    ok, msg = sync.upload("/path/to/passwords.db")
"""
from __future__ import annotations
import os, sys, shutil, threading
from typing import Optional, Dict, Any, Tuple
from utils.logger import get_logger

logger = get_logger("cloud_sync")

try:
    import requests
    from requests.auth import HTTPBasicAuth
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed — cloud sync unavailable. pip install requests")


class WebDAVSync:
    """
    Webdavsync class.
    Класс WebDAVSync.
    Клас WebDAVSync.
    """
    DEFAULT_REMOTE = "securepass_db.encrypted"
    CHUNK = 1024 * 1024

    def __init__(self, url: str, username: str, password: str,
                 remote_filename: str = None, timeout: int = 30, verify_ssl: bool = True) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.url = url.rstrip("/") + "/"
        self.username = username
        self.password = password
        self.remote_filename = remote_filename or self.DEFAULT_REMOTE
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._lock = threading.Lock()

    @property
    def remote_url(self) -> str:
        """
        Handle remote url.
        Обработать remote url.
        Обробити remote url.
        """
        return self.url + self.remote_filename

    def _auth(self) -> Any:
        """
        Handle auth.
        Обработать auth.
        Обробити auth.
        """
        return HTTPBasicAuth(self.username, self.password)

    def test_connection(self) -> Tuple[bool, str]:
        """
        Handle test connection.
        Обработать test connection.
        Обробити test connection.
        """
        if not REQUESTS_AVAILABLE:
            return False, "requests not installed / Установите: pip install requests"
        try:
            r = requests.options(self.url, auth=self._auth(), timeout=self.timeout, verify=self.verify_ssl)
            if r.status_code in (200, 207):
                return True, "OK"
            return False, f"HTTP {r.status_code}"
        except requests.exceptions.ConnectionError as e:
            return False, f"Connection error: {e}"
        except requests.exceptions.Timeout:
            return False, "Timeout"
        except (requests.exceptions.RequestException, OSError) as e:
            return False, str(e)

    def upload(self, local_path: str) -> Tuple[bool, str]:
        """
        Handle upload.
        Обработать upload.
        Обробити upload.
        """
        if not REQUESTS_AVAILABLE:
            return False, "requests not installed"
        if not os.path.exists(local_path):
            return False, f"File not found: {local_path}"
        with self._lock:
            try:
                with open(local_path, "rb") as f:
                    data = f.read()
                r = requests.put(self.remote_url, data=data, auth=self._auth(),
                                 timeout=self.timeout, verify=self.verify_ssl,
                                 headers={"Content-Type": "application/octet-stream"})
                if r.status_code in (200, 201, 204):
                    kb = len(data) / 1024
                    msg = f"Uploaded {kb:.1f} KB → {self.remote_url}"
                    logger.info(msg)
                    return True, msg
                return False, f"HTTP {r.status_code}: {r.text[:100]}"
            except (requests.exceptions.RequestException, OSError, IOError) as e:
                return False, str(e)

    def download(self, local_path: str) -> Tuple[bool, str]:
        """
        Handle download.
        Обработать download.
        Обробити download.
        """
        if not REQUESTS_AVAILABLE:
            return False, "requests not installed"
        with self._lock:
            try:
                r = requests.get(self.remote_url, auth=self._auth(), timeout=self.timeout,
                                 verify=self.verify_ssl, stream=True)
                if r.status_code == 404:
                    return False, "Remote file not found (not synced yet?)"
                if r.status_code != 200:
                    return False, f"HTTP {r.status_code}"
                tmp = local_path + ".sync_tmp"
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(self.CHUNK):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(local_path):
                    shutil.copy2(local_path, local_path + ".before_sync")
                shutil.move(tmp, local_path)
                kb = os.path.getsize(local_path) / 1024
                msg = f"Downloaded {kb:.1f} KB ← {self.remote_url}"
                logger.info(msg)
                return True, msg
            except (requests.exceptions.RequestException, OSError, IOError) as e:
                if os.path.exists(local_path + ".sync_tmp"):
                    try:
                        os.remove(local_path + ".sync_tmp")
                    except OSError as _rm_err:
                        logger.debug(f"Failed to remove temp sync file: {_rm_err}")
                return False, str(e)

    def get_remote_info(self) -> Dict[str, Any]:
        """
        Return remote info.
        Возвращает remote info.
        Повертає remote info.
        """
        if not REQUESTS_AVAILABLE:
            return {"status": "error", "error": "requests not installed"}
        try:
            r = requests.request("PROPFIND", self.remote_url, auth=self._auth(),
                                 timeout=self.timeout, verify=self.verify_ssl, headers={"Depth": "0"})
            if r.status_code in (200, 207):
                return {"status": "found", "last_modified": r.headers.get("Last-Modified")}
            if r.status_code == 404:
                return {"status": "not_found"}
            return {"status": "error", "http_status": r.status_code}
        except (requests.exceptions.RequestException, OSError) as e:
            return {"status": "error", "error": str(e)}

    def sync(self, local_path: str, strategy: str = "upload") -> Tuple[bool, str]:
        """
        Handle sync.
        Обработать sync.
        Обробити sync.
        """
        if strategy == "upload":   return self.upload(local_path)
        if strategy == "download": return self.download(local_path)
        if strategy == "newest":   return self._sync_newest(local_path)
        return False, f"Unknown strategy: {strategy}"

    def _sync_newest(self, local_path: str) -> Tuple[bool, str]:
        """
        Handle sync newest.
        Обработать sync newest.
        Обробити sync newest.
        """
        info = self.get_remote_info()
        if info["status"] == "not_found":
            return self.upload(local_path)
        if info["status"] != "found":
            return False, f"Cannot determine remote status: {info}"
        local_mtime = os.path.getmtime(local_path) if os.path.exists(local_path) else None
        if local_mtime is None:
            return self.download(local_path)
        try:
            import email.utils
            remote_ts = email.utils.parsedate_to_datetime(info["last_modified"]).timestamp()
            if remote_ts > local_mtime + 5:
                return self.download(local_path)
            return self.upload(local_path)
        except (ValueError, TypeError, AttributeError):
            return self.upload(local_path)


class NextcloudSync(WebDAVSync):
    """
    Nextcloudsync class.
    Класс NextcloudSync.
    Клас NextcloudSync.
    """
    def __init__(self, base_url: str, username: str, password: str, **kw) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        url = f"{base_url.rstrip('/')}/remote.php/dav/files/{username}/"
        super().__init__(url, username, password, **kw)


class YandexDiskSync(WebDAVSync):
    """
    Yandexdisksync class.
    Класс YandexDiskSync.
    Клас YandexDiskSync.
    """
    def __init__(self, username: str, password: str, **kw) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__("https://webdav.yandex.ru/", username, password, **kw)


def load_sync_config(path: str = None) -> Dict[str, Any]:
    """
    Load sync config from storage.
    Загрузить sync config из хранилища.
    Завантажити sync config зі сховища.
    """
    import json
    if path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, ".securepass", "sync_config.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_sync_config(config: Dict[str, Any], path: str = None) -> bool:
    """
    Save sync config to persistent storage.
    Сохранить sync config в постоянное хранилище.
    Зберегти sync config у постійне сховище.
    """
    import json
    if path is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        d = os.path.join(base, ".securepass")
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, "sync_config.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        if sys.platform != "win32":
            os.chmod(path, 0o600)
        return True
    except (OSError, ValueError):
        return False


def create_sync_from_config(config: Dict[str, Any]) -> Optional[WebDAVSync]:
    """
    Create and return sync from config.
    Создать и вернуть sync from config.
    Створити і повернути sync from config.
    """
    url = config.get("url", "")
    username = config.get("username", "")
    password = config.get("password", "")
    if not url or not username:
        logger.warning("Sync config missing url or username")
        return None
    provider = config.get("provider", "webdav")
    kw = dict(
        remote_filename=config.get("remote_filename", WebDAVSync.DEFAULT_REMOTE),
        timeout=int(config.get("timeout", 30)),
        verify_ssl=bool(config.get("verify_ssl", True)),
    )
    if provider == "nextcloud": return NextcloudSync(url, username, password, **kw)
    if provider == "yandex":    return YandexDiskSync(username, password, **kw)
    return WebDAVSync(url, username, password, **kw)


__all__ = ["WebDAVSync", "NextcloudSync", "YandexDiskSync",
           "load_sync_config", "save_sync_config", "create_sync_from_config",
           "REQUESTS_AVAILABLE"]
