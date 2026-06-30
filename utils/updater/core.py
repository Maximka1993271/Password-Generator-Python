"""
SecureUpdater — download, verify, install and roll back updates.
SecureUpdater — загрузка, проверка, установка и откат обновлений.
SecureUpdater — завантаження, перевірка, встановлення та відкат оновлень.
"""
from __future__ import annotations
import os
import sys
import json
import hashlib
import tempfile
import subprocess
from utils.subprocess_utils import silent_popen as _silent_popen, _no_window_kwargs
import platform
import shutil
import ssl
import time
import re
import binascii
from typing import Optional, Callable, Dict, Any, Tuple
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    import certifi
except ImportError:
    certifi = None

from utils.logger import get_logger
from utils.paths import get_base_dir, get_temp_dir
from utils.updater.models import (
    UpdateStatus, ReleaseInfo, UpdateManifest, CURRENT_VERSION,
)
from utils.updater.integrity import (
    IntegrityChecker, IntegrityManifest,
    DOWNLOAD_CHUNK_SIZE, NETWORK_ERRORS,
)

logger = get_logger("updater.core")

GITHUB_API          = "https://api.github.com/repos/Maximka1993271/Password-Generator-Python/releases/latest"
UPDATES_DIR         = os.path.join(get_base_dir(), "updates")
MAX_UPDATE_SIZE     = 100 * 1024 * 1024
UPDATE_CHECK_TIMEOUT = 30
ROLLBACK_DIR        = os.path.join(UPDATES_DIR, "rollback")
INTEGRITY_MANIFEST  = os.path.join(UPDATES_DIR, "integrity.json")
EXPECTED_SHA256     = ""

# ── Update security model ─────────────────────────────────────
# Downloads go through a chain of trust:
#  1. HTTPS enforced (ssl.create_default_context uses the OS trust store)
#  2. GitHub API release metadata signed by GitHub's TLS cert
#  3. Installer binary SHA-256 verified against a .sha256 sidecar file
#  4. Optional GPG signature check (if .sig file present in release)
#  5. Size sanity check (reject files >MAX_UPDATE_SIZE)
#
# On Windows, the installer is launched via subprocess.Popen() with
# CREATE_NO_WINDOW so no console flashes, then the current process exits.
class SecureUpdater:
    """Secure auto-updater with signature verification and rollback protection
    Безопасный автообновлятор с проверкой подписи и защитой отката
    Безпечний автооновлювач з перевіркою підпису та захистом відкату"""

    def __init__(self, parent=None, progress_callback: Optional[Callable[[float], None]] = None):
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.parent = parent
        self.current_version = CURRENT_VERSION
        self._update_in_progress = False
        self.progress_callback = progress_callback
        self._downloaded_size = 0
        self._total_size = 0

        # Ensure directories exist
        try:
            os.makedirs(UPDATES_DIR, exist_ok=True)
            os.makedirs(ROLLBACK_DIR, exist_ok=True)
        except (OSError, IOError, PermissionError) as e:
            logger.warning(f"Failed to create update directories / Ошибка создания директорий обновлений / Помилка створення директорій оновлень: {e}")

    def _create_tls_context(self) -> ssl.SSLContext:
        """Create TLS context with certificate verification
        Создать TLS контекст с проверкой сертификата
        Створити TLS контекст з перевіркою сертифіката"""
        if certifi:
            return ssl.create_default_context(cafile=certifi.where())
        return ssl.create_default_context()

    def _verify_https_connection(self) -> bool:
        """Verify HTTPS connection security
        Проверить безопасность HTTPS соединения
        Перевірити безпеку HTTPS з'єднання"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(GITHUB_API)
            hostname = parsed.hostname

            if not hostname:
                logger.error("Cannot extract hostname from GitHub API URL / Не удаётся извлечь имя хоста из URL GitHub API / Не вдається витягти ім'я хоста з URL GitHub API")
                return False

            context = self._create_tls_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            import socket
            with socket.create_connection((hostname, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if not cert:
                        logger.error("No certificate received from server / Сертификат не получен от сервера / Сертифікат не отримано від сервера")
                        return False
                    logger.debug("HTTPS certificate verification successful / Проверка HTTPS сертификата успешна / Перевірку HTTPS сертифіката успішно")
                    return True

        except (socket.timeout, socket.error, ssl.SSLError, OSError) as e:
            logger.error(f"HTTPS verification failed / Ошибка проверки HTTPS / Помилка перевірки HTTPS: {e}")
            return False

        # ── Version comparison ────────────────────────────────────
    # We compare semantic version tuples (major, minor, patch) rather than
    # strings to avoid lexicographic ordering bugs (e.g. "1.9" > "1.10").
    def check_for_updates(self) -> Tuple[UpdateStatus, Optional[ReleaseInfo]]:
        """Check for updates on GitHub (HTTPS only)
        Проверить наличие обновлений на GitHub (только HTTPS)
        Перевірити наявність оновлень на GitHub (тільки HTTPS)"""
        if not self._verify_https_connection():
            logger.error("HTTPS certificate verification failed - aborting update check / Проверка HTTPS сертификата не удалась - проверка обновлений прервана / Перевірку HTTPS сертифіката не вдалося - перевірку оновлень перервано")
            return UpdateStatus.CHECK_FAILED, None

        try:
            logger.info("Checking for updates... / Проверка обновлений... / Перевірка оновлень...")

            context = self._create_tls_context()
            req = Request(GITHUB_API, headers={'User-Agent': f'SecurePassPro/{CURRENT_VERSION}'})

            with urlopen(req, timeout=UPDATE_CHECK_TIMEOUT, context=context) as response:
                data = json.loads(response.read().decode('utf-8'))

            release = ReleaseInfo.from_api_response(data)

            if not release:
                logger.error("Failed to parse release info / Ошибка парсинга информации о релизе / Помилка парсингу інформації про реліз")
                return UpdateStatus.CHECK_FAILED, None

            if not release.is_valid_version_format():
                logger.error(f"Invalid version format: {release.version} / Неверный формат версии: {release.version} / Невірний формат версії: {release.version}")
                return UpdateStatus.CHECK_FAILED, None

            # Verify release hash
            if not IntegrityChecker.verify_release_hash(release):
                logger.error("Release hash verification failed / Проверка хеша релиза не удалась / Перевірку хеша релізу не вдалося")
                return UpdateStatus.VERIFY_FAILED, None

            if release.is_newer_than(CURRENT_VERSION):
                logger.info(f"Update available: {CURRENT_VERSION} -> {release.version} / Доступно обновление: {CURRENT_VERSION} -> {release.version} / Доступне оновлення: {CURRENT_VERSION} -> {release.version}")
                return UpdateStatus.UPDATE_AVAILABLE, release
            else:
                logger.info(f"No updates available (current: {CURRENT_VERSION}) / Обновления не найдены (текущая: {CURRENT_VERSION}) / Оновлень не знайдено (поточна: {CURRENT_VERSION})")
                return UpdateStatus.NO_UPDATE, None

        except NETWORK_ERRORS as e:
            logger.error(f"Network error checking updates / Ошибка сети при проверке обновлений / Помилка мережі при перевірці оновлень: {e}")
            return UpdateStatus.CHECK_FAILED, None
        except (ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as e:
            logger.error(f"Parse error / Ошибка парсинга / Помилка парсингу: {e}")
            return UpdateStatus.CHECK_FAILED, None

    def download_update(self, release: ReleaseInfo) -> Tuple[UpdateStatus, Optional[str]]:
        """Download update and verify integrity
        Загрузить обновление и проверить целостность
        Завантажити оновлення та перевірити цілісність"""
        if self._update_in_progress:
            logger.warning("Update already in progress / Обновление уже выполняется / Оновлення вже виконується")
            return UpdateStatus.DOWNLOAD_FAILED, None

        self._update_in_progress = True

        try:
            os.makedirs(UPDATES_DIR, exist_ok=True)

            fd, temp_path = tempfile.mkstemp(suffix='.tmp', prefix='update_', dir=UPDATES_DIR)
            os.close(fd)

            exe_path = os.path.join(UPDATES_DIR, f"SecurePassPro_{release.version}.exe")

            logger.info(f"Downloading update from {release.download_url} / Загрузка обновления из {release.download_url} / Завантаження оновлення з {release.download_url}")

            context = self._create_tls_context()
            req = Request(release.download_url, headers={'User-Agent': f'SecurePassPro/{CURRENT_VERSION}'})

            with urlopen(req, timeout=30, context=context) as response:
                self._total_size = int(response.headers.get('Content-Length', 0))
                self._downloaded_size = 0

                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        self._downloaded_size += len(chunk)
                        if self.progress_callback and self._total_size > 0:
                            try:
                                progress = self._downloaded_size / self._total_size
                                self.progress_callback(progress)
                            except (TypeError, AttributeError):
                                pass

            shutil.move(temp_path, exe_path)

            # Verify integrity
            if not IntegrityChecker.verify_update_integrity(exe_path, release):
                try:
                    os.remove(exe_path)
                except (OSError, IOError, PermissionError) as e:
                    logger.warning(f"Failed to remove corrupted update / Ошибка удаления повреждённого обновления / Помилка видалення пошкодженого оновлення: {e}")
                return UpdateStatus.INTEGRITY_FAILED, None

            manifest = UpdateManifest(
                version=release.version,
                timestamp=datetime.now().isoformat(),
                previous_version=CURRENT_VERSION,
                file_hash=IntegrityChecker.calculate_sha256(exe_path) or "",
                file_size=os.path.getsize(exe_path),
                signature=release.signature
            )
            manifest.save(os.path.join(UPDATES_DIR, "manifest.json"))

            logger.info("Update downloaded and verified successfully / Обновление загружено и проверено успешно / Оновлення завантажено та перевірено успішно")
            return UpdateStatus.SUCCESS, exe_path

        except NETWORK_ERRORS as e:
            logger.error(f"Network error downloading update / Ошибка сети при загрузке обновления / Помилка мережі при завантаженні оновлення: {e}")
            return UpdateStatus.DOWNLOAD_FAILED, None
        except (OSError, IOError, PermissionError, ValueError, RuntimeError, shutil.Error) as e:
            logger.error(f"Error downloading update / Ошибка загрузки обновления / Помилка завантаження оновлення: {e}")
            return UpdateStatus.DOWNLOAD_FAILED, None
        finally:
            self._update_in_progress = False

    def _create_rollback_backup(self, current_exe: str) -> Optional[str]:
        """Create backup of current executable for rollback
        Создать резервную копию текущего исполняемого файла для отката
        Створити резервну копію поточного виконуваного файлу для відкату"""
        try:
            if not os.path.exists(current_exe):
                logger.warning(f"Current executable not found: {current_exe} / Текущий исполняемый файл не найден: {current_exe} / Поточний виконуваний файл не знайдено: {current_exe}")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(ROLLBACK_DIR, f"SecurePassPro_v{CURRENT_VERSION}_{timestamp}.backup")

            shutil.copy2(current_exe, backup_path)
            logger.info(f"Rollback backup created: {backup_path} / Создана резервная копия для отката: {backup_path} / Створено резервну копію для відкату: {backup_path}")
            return backup_path
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Failed to create rollback backup / Ошибка создания резервной копии для отката / Помилка створення резервної копії для відкату: {e}")
            return None

    def _perform_rollback(self, backup_path: str, target_path: str) -> bool:
        """Perform rollback to previous version
        Выполнить откат к предыдущей версии
        Виконати відкат до попередньої версії"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Rollback backup not found: {backup_path} / Резервная копия для отката не найдена: {backup_path} / Резервну копію для відкату не знайдено: {backup_path}")
                return False

            shutil.copy2(backup_path, target_path)
            logger.info(f"Rollback completed: {backup_path} -> {target_path} / Откат выполнен: {backup_path} -> {target_path} / Відкат виконано: {backup_path} -> {target_path}")
            return True
        except (OSError, IOError, PermissionError, shutil.Error) as e:
            logger.error(f"Rollback failed / Ошибка отката / Помилка відкату: {e}")
            return False

    def install_update(self, update_path: str) -> UpdateStatus:
        """Install update with rollback protection
        Установить обновление с защитой отката
        Встановити оновлення з захистом відкату"""
        try:
            if not os.path.exists(update_path):
                logger.error(f"Update file not found: {update_path} / Файл обновления не найден: {update_path} / Файл оновлення не знайдено: {update_path}")
                return UpdateStatus.INSTALL_FAILED

            if os.path.getsize(update_path) == 0:
                logger.error("Update file is empty / Файл обновления пуст / Файл оновлення порожній")
                return UpdateStatus.INTEGRITY_FAILED

            current_exe = sys.executable
            backup_path = self._create_rollback_backup(current_exe)

            system = platform.system()
            if system == "Windows":
                result = self._install_update_windows(update_path, current_exe, backup_path)
            elif system == "Darwin":
                result = self._install_update_macos(update_path, current_exe, backup_path)
            else:
                result = self._install_update_linux(update_path, current_exe, backup_path)

            if result != UpdateStatus.SUCCESS and backup_path:
                logger.warning("Installation failed, attempting rollback... / Установка не удалась, попытка отката... / Встановлення не вдалося, спроба відкату...")
                if self._perform_rollback(backup_path, current_exe):
                    return UpdateStatus.ROLLBACK_SUCCESS
                return UpdateStatus.ROLLBACK_FAILED

            return result

        except (OSError, IOError, PermissionError, subprocess.SubprocessError, RuntimeError) as e:
            logger.error(f"Install update error / Ошибка установки обновления / Помилка встановлення оновлення: {e}")
            return UpdateStatus.INSTALL_FAILED

    def _install_update_windows(self, update_path: str, current_exe: str, backup_path: str = None) -> UpdateStatus:
        """Install update on Windows / Установить обновление на Windows / Встановити оновлення на Windows"""
        try:
            ps_script = os.path.join(UPDATES_DIR, "update.ps1")

            rollback_cmd = ""
            if backup_path:
                rollback_cmd = f"""
    if ($LASTEXITCODE -ne 0) {{
        try {{
            Copy-Item -Path "{backup_path}" -Destination "{current_exe}" -Force
            Start-Process -FilePath "{current_exe}"
        }} catch {{
            Write-Error $_.Exception.Message
        }}
    }}
"""

            with open(ps_script, 'w', encoding='utf-8') as f:
                f.write(f"""# Secure Pass Pro Updater
Start-Sleep -Seconds 2
try {{
    if (Test-Path "{update_path}") {{
        Copy-Item -Path "{update_path}" -Destination "{current_exe}" -Force
        {rollback_cmd}
        if ($LASTEXITCODE -eq 0) {{
            Start-Process -FilePath "{current_exe}"
        }}
    }}
}} catch {{
    Write-Error $_.Exception.Message
    Start-Sleep -Seconds 5
}}
try {{
    Remove-Item -Path $MyInvocation.MyCommand.Path -Force
    if (Test-Path "{backup_path}") {{
        Remove-Item -Path "{backup_path}" -Force
    }}
}} catch {{
    # Ignore cleanup errors
}}
""")

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            _silent_popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", ps_script],
                startupinfo=startupinfo
            )

            if self.parent:
                try:
                    self.parent.quit()
                except (AttributeError, RuntimeError):
                    pass

            return UpdateStatus.SUCCESS

        except (OSError, IOError, PermissionError, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"Windows install error / Ошибка установки на Windows / Помилка встановлення на Windows: {e}")
            return UpdateStatus.INSTALL_FAILED

    def _install_update_macos(self, update_path: str, current_exe: str, backup_path: str = None) -> UpdateStatus:
        """Install update on macOS / Установить обновление на macOS / Встановити оновлення на macOS"""
        try:
            script_path = os.path.join(UPDATES_DIR, "update.sh")

            rollback_cmd = ""
            if backup_path:
                rollback_cmd = f"""
if [ $? -ne 0 ]; then
    cp "{backup_path}" "{current_exe}"
    chmod +x "{current_exe}"
    open "{current_exe}"
fi
"""

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f"""#!/bin/bash
sleep 2
if [ -f "{update_path}" ]; then
    cp "{update_path}" "{current_exe}"
    chmod +x "{current_exe}"
    {rollback_cmd}
    open "{current_exe}"
fi
rm "$0"
if [ -f "{backup_path}" ]; then
    rm "{backup_path}"
fi
""")

            os.chmod(script_path, 0o755)
            _silent_popen(['open', script_path])

            if self.parent:
                try:
                    self.parent.quit()
                except (AttributeError, RuntimeError):
                    pass

            return UpdateStatus.SUCCESS

        except (OSError, IOError, PermissionError, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"macOS install error / Ошибка установки на macOS / Помилка встановлення на macOS: {e}")
            return UpdateStatus.INSTALL_FAILED

    def _install_update_linux(self, update_path: str, current_exe: str, backup_path: str = None) -> UpdateStatus:
        """Install update on Linux / Установить обновление на Linux / Встановити оновлення на Linux"""
        try:
            script_path = os.path.join(UPDATES_DIR, "update.sh")

            rollback_cmd = ""
            if backup_path:
                rollback_cmd = f"""
if [ $? -ne 0 ]; then
    cp "{backup_path}" "{current_exe}"
    chmod +x "{current_exe}"
    "{current_exe}" &
fi
"""

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(f"""#!/bin/bash
sleep 2
if [ -f "{update_path}" ]; then
    cp "{update_path}" "{current_exe}"
    chmod +x "{current_exe}"
    {rollback_cmd}
    "{current_exe}" &
fi
rm "$0"
if [ -f "{backup_path}" ]; then
    rm "{backup_path}"
fi
""")

            os.chmod(script_path, 0o755)
            _silent_popen(['bash', script_path])

            if self.parent:
                try:
                    self.parent.quit()
                except (AttributeError, RuntimeError):
                    pass

            return UpdateStatus.SUCCESS

        except (OSError, IOError, PermissionError, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"Linux install error / Ошибка установки на Linux / Помилка встановлення на Linux: {e}")
            return UpdateStatus.INSTALL_FAILED

    def perform_update(self) -> UpdateStatus:
        """Perform full update cycle / Выполнить полный цикл обновления / Виконати повний цикл оновлення"""
        status, release = self.check_for_updates()

        if status == UpdateStatus.NO_UPDATE:
            return status
        if status != UpdateStatus.UPDATE_AVAILABLE or not release:
            return UpdateStatus.CHECK_FAILED

        try:
            from gui.dialogs import CTkMessageBox
            from Langs.lang import LANGUAGES

            _lang = "RU"
            try:
                from storage.config import Config
                config = AppSettings.instance()
                _lang = config.get("LANG", "RU")
            except (ImportError, AttributeError, RuntimeError):
                pass

            L = LANGUAGES.get(_lang, LANGUAGES.get("RU", {}))

            message = L.get("update_available", "New version {0} available! / Доступна новая версия {0}! / Доступна нова версія {0}!").format(release.version) + "\n\n"
            message += L.get("update_info", f"Current version: {CURRENT_VERSION} / Текущая версия: {CURRENT_VERSION} / Поточна версія: {CURRENT_VERSION}") + "\n"
            message += L.get("update_size", f"Size: {release.size // 1024 // 1024} MB / Размер: {release.size // 1024 // 1024} МБ / Розмір: {release.size // 1024 // 1024} МБ") + "\n\n"
            message += L.get("update_confirm_message", "Install update? / Установить обновление? / Встановити оновлення?")

            if not CTkMessageBox.question(self.parent, L.get("update_available_title", "Update available / Доступно обновление / Доступне оновлення"), message):
                return UpdateStatus.NO_UPDATE
        except ImportError:
            pass
        except (AttributeError, TypeError, RuntimeError, KeyError, ImportError) as e:
            logger.debug(f"Message box error / Ошибка окна сообщения / Помилка вікна повідомлення: {e}")
            pass

        status, update_path = self.download_update(release)
        if status != UpdateStatus.SUCCESS or not update_path:
            return status

        return self.install_update(update_path)

    def rollback_to_previous(self) -> UpdateStatus:
        """Rollback to previous version if available
        Откат к предыдущей версии, если доступно
        Відкат до попередньої версії, якщо доступно"""
        try:
            backups = []
            if os.path.exists(ROLLBACK_DIR):
                for f in os.listdir(ROLLBACK_DIR):
                    if f.endswith('.backup'):
                        f_path = os.path.join(ROLLBACK_DIR, f)
                        backups.append((f_path, os.path.getmtime(f_path)))

            if not backups:
                logger.warning("No rollback backups found / Резервные копии для отката не найдены / Резервні копії для відкату не знайдено")
                return UpdateStatus.ROLLBACK_FAILED

            backups.sort(key=lambda x: x[1], reverse=True)
            latest_backup = backups[0][0]

            current_exe = sys.executable

            if self._perform_rollback(latest_backup, current_exe):
                logger.info("Rollback completed, restarting... / Откат выполнен, перезапуск... / Відкат виконано, перезапуск...")
                if platform.system() == "Windows":
                    _silent_popen([current_exe])
                elif platform.system() == "Darwin":
                    _silent_popen(['open', current_exe])
                else:
                    _silent_popen([current_exe])

                if self.parent:
                    try:
                        self.parent.quit()
                    except (AttributeError, RuntimeError):
                        pass

                return UpdateStatus.ROLLBACK_SUCCESS

            return UpdateStatus.ROLLBACK_FAILED

        except (OSError, IOError, PermissionError, subprocess.SubprocessError, ValueError) as e:
            logger.error(f"Rollback error / Ошибка отката / Помилка відкату: {e}")
            return UpdateStatus.ROLLBACK_FAILED
