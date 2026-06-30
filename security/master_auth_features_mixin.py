from __future__ import annotations
# security/master_auth_features_mixin.py
"""
Master auth features mixin module for Secure Pass Pro.
Модуль Master auth features mixin для Secure Pass Pro.
Модуль Master auth features mixin для Secure Pass Pro.
"""
"""
Master auth features mixin module for Secure Pass Pro.
Модуль Master auth features mixin для Secure Pass Pro.
Модуль Master auth features mixin для Secure Pass Pro.
"""
"""
Master password authentication - Features mixin (sessions, trusted devices, recovery, 2FA)
Миксин функций для аутентификации мастер-пароля (сессии, доверенные устройства, восстановление, 2FA)
Міксин функцій для аутентифікації майстер-пароля (сесії, довірені пристрої, відновлення, 2FA)
"""
import os
import sys
import hashlib
import hmac
import secrets
import time
import re
import base64
import binascii
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime

from security.master_auth_constants import (
    MASTER_FILE, CONFIG_DIR, PBKDF2_ITERATIONS, PBKDF2_SALT_SIZE,
    ARGON2_TIME_COST, ARGON2_MEMORY_COST, ARGON2_PARALLELISM, ARGON2_HASH_LEN,
    _ARGON2_OK, PASSWORD_HISTORY_MAX, PASSWORD_HISTORY_HASH_PREFIX,
    PASSWORD_HISTORY_HASH_ITERATIONS, PASSWORD_HISTORY_SALT_BYTES,
    AUDIT_LOG_MAX_ENTRIES, AUDIT_LOG_RETENTION_DAYS, SESSION_TIMEOUT_HOURS,
    MAX_TRUSTED_DEVICES, RECOVERY_CODES_COUNT, RECOVERY_CODE_LENGTH
)

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
except ImportError as e:
    PasswordHasher = None
    VerifyMismatchError = VerificationError = InvalidHashError = Exception

from utils.logger import get_logger

logger = get_logger("master_auth")

from security.master_auth_helpers import (
    _get_device_fingerprint, _get_ip_address, _hash_recovery_code, _verify_recovery_code_hash
)
from security.master_auth_types import Session, TrustedDevice, RecoveryCode

class MasterAuthFeaturesMixin:
    """Features methods for master password authentication (sessions, trusted devices, recovery, 2FA)
    Методы функций для аутентификации мастер-пароля (сессии, доверенные устройства, восстановление, 2FA)
    Методи функцій для аутентифікації майстер-пароля (сесії, довірені пристрої, відновлення, 2FA)"""

    # ==================== SESSION METHODS ====================

    @classmethod
    def _create_session(cls, source: str) -> Optional[str]:
        """Create new session for successful authentication
        Создать новую сессию для успешной аутентификации
        Створити нову сесію для успішної аутентифікації"""
        try:
            session_id = secrets.token_hex(32)
            now = datetime.now()
            expires_at = now.timestamp() + (SESSION_TIMEOUT_HOURS * 3600)

            session = Session(
                session_id=session_id,
                created_at=now.isoformat(),
                expires_at=datetime.fromtimestamp(expires_at).isoformat(),
                device_id=_get_device_fingerprint(),
                ip_address=_get_ip_address()
            )

            cls._sessions.append(session.to_dict())
            cls._current_session_id = session_id
            from security.master_auth_session import _save_sessions
            _save_sessions(cls)

            logger.debug(f"Session created: {session_id[:16]}... / Сессия создана: {session_id[:16]}... / Сесію створено: {session_id[:16]}...")
            return session_id
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.debug(f"Session creation error / Ошибка создания сессии / Помилка створення сесії: {e}")
            return None

    @classmethod
    def validate_session(cls, session_id: str) -> bool:
        """Validate if session is still active
        Проверить, активна ли сессия
        Перевірити, чи активна сесія"""
        try:
            from security.master_auth_session import _cleanup_expired_sessions
            _cleanup_expired_sessions(cls)
            for session in cls._sessions:
                if session.get("session_id") == session_id:
                    expires_at = datetime.fromisoformat(session.get("expires_at", "2000-01-01T00:00:00")).timestamp()
                    if expires_at > time.time():
                        return True
            return False
        except (ValueError, TypeError, KeyError, AttributeError) as e:
            logger.debug(f"Session validation error / Ошибка проверки сессии / Помилка перевірки сесії: {e}")
            return False

    @classmethod
    def end_session(cls, session_id: Optional[str] = None) -> bool:
        """End a session
        Завершить сессию
        Завершити сесію"""
        try:
            if session_id is None:
                session_id = cls._current_session_id

            cls._sessions = [s for s in cls._sessions if s.get("session_id") != session_id]
            if session_id == cls._current_session_id:
                cls._current_session_id = None
            from security.master_auth_session import _save_sessions
            _save_sessions(cls)
            logger.debug(f"Session ended: {session_id[:16] if session_id else 'None'}... / Сессия завершена: {session_id[:16] if session_id else 'None'}... / Сесію завершено: {session_id[:16] if session_id else 'None'}...")
            return True
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.debug(f"Session end error / Ошибка завершения сессии / Помилка завершення сесії: {e}")
            return False

    @classmethod
    def end_all_sessions(cls) -> int:
        """End all active sessions
        Завершить все активные сессии
        Завершити всі активні сесії"""
        count = len(cls._sessions)
        cls._sessions = []
        cls._current_session_id = None
        from security.master_auth_session import _save_sessions
        _save_sessions(cls)
        logger.info(f"Ended {count} sessions / Завершено {count} сессий / Завершено {count} сесій")
        return count

    @classmethod
    def get_sessions(cls) -> List[Dict[str, Any]]:
        """Get active sessions
        Получить активные сессии
        Отримати активні сесії"""
        from security.master_auth_session import _cleanup_expired_sessions
        _cleanup_expired_sessions(cls)
        return cls._sessions.copy()

    @classmethod
    def get_current_session_id(cls) -> Optional[str]:
        """Get current session ID
        Получить ID текущей сессии
        Отримати ID поточної сесії"""
        return cls._current_session_id

    # ==================== TRUSTED DEVICES METHODS ====================

    @classmethod
    def get_trusted_devices(cls) -> List[Dict[str, Any]]:
        """Get list of trusted devices
        Получить список доверенных устройств
        Отримати список довірених пристроїв"""
        return cls._trusted_devices.copy()

    @classmethod
    def add_trusted_device(cls, device_name: str) -> bool:
        """Add current device as trusted
        Добавить текущее устройство как доверенное
        Додати поточний пристрій як довірений"""
        try:
            if len(cls._trusted_devices) >= MAX_TRUSTED_DEVICES:
                logger.warning(f"Maximum trusted devices reached ({MAX_TRUSTED_DEVICES}) / Достигнуто максимальное количество доверенных устройств ({MAX_TRUSTED_DEVICES}) / Досягнуто максимальну кількість довірених пристроїв ({MAX_TRUSTED_DEVICES})")
                return False

            device = TrustedDevice(
                device_id=_get_device_fingerprint(),
                device_name=device_name,
                fingerprint=_get_device_fingerprint(),
                added_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                ip_address=_get_ip_address()
            )

            cls._trusted_devices.append(device.to_dict())
            from security.master_auth_trusted import _save_trusted_devices
            _save_trusted_devices(cls)
            logger.info(f"Trusted device added: {device_name} / Доверенное устройство добавлено: {device_name} / Довірений пристрій додано: {device_name}")
            return True
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.error(f"Failed to add trusted device / Ошибка добавления доверенного устройства / Помилка додавання довіреного пристрою: {e}")
            return False

    @classmethod
    def remove_trusted_device(cls, device_id: str) -> bool:
        """Remove trusted device
        Удалить доверенное устройство
        Видалити довірений пристрій"""
        try:
            original_count = len(cls._trusted_devices)
            cls._trusted_devices = [d for d in cls._trusted_devices if d.get("device_id") != device_id]
            if len(cls._trusted_devices) < original_count:
                from security.master_auth_trusted import _save_trusted_devices
                _save_trusted_devices(cls)
                logger.info(f"Trusted device removed: {device_id[:16]}... / Доверенное устройство удалено: {device_id[:16]}... / Довірений пристрій видалено: {device_id[:16]}...")
                return True
            return False
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.error(f"Failed to remove trusted device / Ошибка удаления доверенного устройства / Помилка видалення довіреного пристрою: {e}")
            return False

    @classmethod
    def is_device_trusted(cls) -> bool:
        """Check if current device is trusted
        Проверить, является ли текущее устройство доверенным
        Перевірити, чи є поточний пристрій довіреним"""
        current_fingerprint = _get_device_fingerprint()
        for device in cls._trusted_devices:
            if device.get("fingerprint") == current_fingerprint:
                device["last_used"] = datetime.now().isoformat()
                from security.master_auth_trusted import _save_trusted_devices
                _save_trusted_devices(cls)
                return True
        return False

    # ==================== RECOVERY CODES METHODS ====================

    @classmethod
    def generate_recovery_codes(cls, count: int = RECOVERY_CODES_COUNT,
                                length: int = RECOVERY_CODE_LENGTH) -> List[str]:
        """Generate new recovery codes
        Сгенерировать новые резервные коды
        Згенерувати нові резервні коди"""
        try:
            codes = []
            for _ in range(count):
                code = ''.join(str(secrets.randbelow(10)) for _ in range(length))
                code_formatted = f"{code[:4]}-{code[4:]}" if length == 8 else code

                recovery_code = RecoveryCode(
                    code_hash=_hash_recovery_code(code),
                    created_at=datetime.now().isoformat(),
                    used=False
                )
                codes.append(code_formatted)
                cls._recovery_codes.append(recovery_code.to_dict())

            from security.master_auth_recovery import _save_recovery_codes
            _save_recovery_codes(cls)
            logger.info(f"Generated {count} recovery codes / Сгенерировано {count} резервных кодов / Згенеровано {count} резервних кодів")
            return codes
        except (ValueError, TypeError, OSError, AttributeError) as e:
            logger.error(f"Failed to generate recovery codes / Ошибка генерации резервных кодов / Помилка генерації резервних кодів: {e}")
            return []

    @classmethod
    def verify_recovery_code(cls, code: str) -> bool:
        """Verify and consume a recovery code
        Проверить и использовать резервный код
        Перевірити та використати резервний код"""
        try:
            code_clean = code.replace("-", "").replace(" ", "")

            for i, rc in enumerate(cls._recovery_codes):
                if not rc.get("used", False) and _verify_recovery_code_hash(code_clean, rc.get("code_hash", "")):
                    rc["used"] = True
                    rc["used_at"] = datetime.now().isoformat()
                    from security.master_auth_recovery import _save_recovery_codes
                    _save_recovery_codes(cls)
                    logger.info("Recovery code used successfully / Резервный код успешно использован / Резервний код успішно використано")
                    return True

            logger.warning("Invalid or already used recovery code / Неверный или уже использованный резервный код / Невірний або вже використаний резервний код")
            return False
        except (ValueError, TypeError, OSError, AttributeError, KeyError) as e:
            logger.error(f"Recovery code verification error / Ошибка проверки резервного кода / Помилка перевірки резервного коду: {e}")
            return False

    @classmethod
    def get_recovery_codes_status(cls) -> Dict[str, Any]:
        """Get recovery codes status
        Получить статус резервных кодов
        Отримати статус резервних кодів"""
        total = len(cls._recovery_codes)
        used = sum(1 for rc in cls._recovery_codes if rc.get("used", False))
        return {
            "total": total,
            "used": used,
            "available": total - used,
            "max_codes": RECOVERY_CODES_COUNT
        }

    @classmethod
    def clear_recovery_codes(cls) -> bool:
        """Clear all recovery codes
        Очистить все резервные коды
        Очистити всі резервні коди"""
        try:
            cls._recovery_codes.clear()
            from security.master_auth_recovery import _save_recovery_codes
            _save_recovery_codes(cls)
            logger.info("Recovery codes cleared / Резервные коды очищены / Резервні коди очищено")
            return True
        except (OSError, IOError, PermissionError) as e:
            logger.error(f"Failed to clear recovery codes / Ошибка очистки резервных кодов / Помилка очищення резервних кодів: {e}")
            return False

    # ==================== 2FA METHODS ====================

    @classmethod
    def set_config(cls, config) -> None:
        """Set configuration object reference
        Установить ссылку на объект конфигурации
        Встановити посилання на об'єкт конфігурації"""
        cls._cached_config = config
        from security.master_auth_history import _load_password_history
        from security.master_auth_trusted import _load_trusted_devices
        from security.master_auth_recovery import _load_recovery_codes
        from security.master_auth_session import _load_sessions
        _load_password_history(cls)
        _load_trusted_devices(cls)
        _load_recovery_codes(cls)
        _load_sessions(cls)

    @classmethod
    def is_2fa_required(cls) -> bool:
        """Check if 2FA is required
        Проверить, требуется ли 2FA
        Перевірити, чи потрібна 2FA"""
        if cls._cached_config is None:
            return False
        try:
            return cls._cached_config.is_2fa_enabled()
        except AttributeError:
            return False

    @classmethod
    def set_skip_2fa_once(cls, skip: bool) -> None:
        """Set flag to skip 2FA for next authentication
        Установить флаг пропуска 2FA для следующей аутентификации
        Встановити прапорець пропуску 2FA для наступної аутентифікації"""
        cls._skip_2fa_once = skip

    @classmethod
    def should_skip_2fa(cls) -> bool:
        """Check if 2FA should be skipped for this authentication
        Проверить, следует ли пропустить 2FA для этой аутентификации
        Перевірити, чи слід пропустити 2FA для цієї аутентифікації"""
        if cls._skip_2fa_once:
            cls._skip_2fa_once = False
            return True
        return False

    @classmethod
    def verify_with_2fa(cls, password: str, source: str = "startup") -> Tuple[bool, Optional[str]]:
        """Verify master password with 2FA if enabled.
        Проверить мастер-пароль с 2FA, если включена.
        Перевірити майстер-пароль з 2FA, якщо ввімкнено."""
        if not cls.verify(password, source=source):
            return False, "master_password_incorrect"

        if not cls.is_2fa_required() or cls.should_skip_2fa():
            return True, None

        try:
            from security.totp import TOTP, get_totp_manager

            secret = cls._cached_config.get_2fa_secret()
            if not secret:
                logger.error("2FA enabled but no secret found / 2FA включена, но секрет не найден / 2FA увімкнено, але секрет не знайдено")
                cls._log_audit_event("2fa_verification_failed", {"reason": "no_secret", "source": source})
                return False, "2fa_missing_secret"

            totp = TOTP(secret)

            from gui.dialogs import CTkMessageBox
            from localization.lang import LANGUAGES
            import customtkinter as ctk

            lang = cls._cached_config.get("LANG", "RU")
            L = LANGUAGES.get(lang, LANGUAGES["RU"])

            from tkinter import simpledialog
            root = ctk.CTk()
            root.withdraw()
            code = simpledialog.askstring(
                L.get("2fa_title", "Two-Factor Authentication / Двухфакторная аутентификация / Двофакторна аутентифікація"),
                L.get("2fa_enter_code", "Enter verification code: / Введите код подтверждения: / Введіть код підтвердження:"),
                parent=root
            )
            root.destroy()

            if code is None:
                cls._log_audit_event("2fa_verification_failed", {"reason": "cancelled", "source": source})
                return False, "2fa_cancelled"

            code_clean = ''.join(filter(str.isdigit, str(code)))

            if totp.verify(code_clean)[0]:
                cls._log_audit_event("2fa_verification_success", {"source": source})
                return True, None

            manager = get_totp_manager()
            if manager.verify_backup_code(code_clean):
                cls._log_audit_event("2fa_backup_used", {"source": source})
                if cls._cached_config:
                    cls._cached_config.set_2fa_backup_hashes(manager.get_backup_codes_hashes())
                    cls._cached_config.save()
                return True, None

            cls._log_audit_event("2fa_verification_failed", {"reason": "invalid_code", "source": source})
            return False, "2fa_invalid_code"

        except ImportError as e:
            logger.error(f"Failed to import 2FA modules / Ошибка импорта модулей 2FA / Помилка імпорту модулів 2FA: {e}")
            return False, "2fa_module_error"
        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"2FA verification error / Ошибка верификации 2FA / Помилка верифікації 2FA: {e}")
            return False, "2fa_error"

    @classmethod
    def prompt_on_startup(cls, lang: str = "RU", theme: str = "dark") -> bool:
        """Show master password prompt on startup.
        Показать запрос мастер-пароля при запуске.
        Показати запит майстер-пароля при запуску."""
        from security.master_auth_lockout import _load_lockout_state
        from security.master_auth_audit import _load_audit_log
        from security.master_auth_history import _load_password_history
        from security.master_auth_trusted import _load_trusted_devices
        from security.master_auth_recovery import _load_recovery_codes
        from security.master_auth_session import _load_sessions
        
        _load_lockout_state(cls)
        _load_audit_log(cls)
        _load_password_history(cls)
        _load_trusted_devices(cls)
        _load_recovery_codes(cls)
        _load_sessions(cls)

        if not cls.is_set():
            return True

        try:
            import customtkinter as ctk
            import tkinter as tk
            from localization.lang import LANGUAGES
            from security.encryption import set_key_from_master
            from utils.helpers import center_screen
        except ImportError as e:
            logger.error(f"Failed to import GUI modules / Ошибка импорта GUI модулей / Помилка імпорту GUI модулів: {e}")
            return True

        L = LANGUAGES.get(lang, LANGUAGES.get("RU", {}))

        if theme == "light":
            bg_color = "#F3F3F3"
            fg_color = "#000000"
            entry_bg = "#FFFFFF"
            btn_fg = "#2d6a4f"
            btn_hover = "#40916c"
        else:
            bg_color = "#1d1e1e"
            fg_color = "#FFFFFF"
            entry_bg = "#2b2b2b"
            btn_fg = "#2d6a4f"
            btn_hover = "#40916c"

        root = ctk.CTk()
        root.title(L.get("master_title", "Master password / Мастер-пароль / Майстер-пароль"))
        root.resizable(False, False)
        root.configure(fg_color=bg_color)
        center_screen(root, 380, 280)

        result = {"ok": False}
        max_attempts = cls.get_max_attempts()
        is_closing = False

        main_frame = ctk.CTkFrame(root, fg_color="transparent")
        main_frame.pack(expand=True, fill="both", padx=25, pady=20)

        ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 32),
            text_color="#4EC9B0"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            main_frame,
            text=L.get("master_prompt", "Enter master password to access the program: / Введите мастер-пароль для доступа к программе: / Введіть майстер-пароль для доступу до програми:"),
            font=("Segoe UI", 13),
            text_color=fg_color,
        ).pack(pady=(0, 12))

        entry = ctk.CTkEntry(
            main_frame,
            width=280,
            height=38,
            show="*",
            fg_color=entry_bg,
            text_color=fg_color,
            corner_radius=12,
        )
        entry.pack(pady=(0, 12))
        entry.focus_set()

        status = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 11),
            text_color="#E24B4A",
            wraplength=300
        )
        status.pack(pady=(0, 8))

        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=(10, 0))

        def update_status():
            if is_closing:
                return
            try:
                info = cls.get_lockout_info()
                if info['is_locked']:
                    status.configure(text=f"{L.get('lock_wait', 'Please wait / Подождите / Зачекайте')} {info['lockout_seconds']} {L.get('seconds_short', 'sec / сек / сек')}...")
                    entry.configure(state="disabled")
                    submit_btn.configure(state="disabled")
                    cancel_btn.configure(state="disabled")
                    root.after(1000, update_status)
                elif info['is_permanently_locked']:
                    status.configure(text=L.get("master_blocked", "Too many attempts. Program closed. / Слишком много попыток. Программа закрыта. / Занадто багато спроб. Програму закрито."))
                    entry.configure(state="disabled")
                    submit_btn.configure(state="disabled")
                    cancel_btn.configure(state="disabled")
                    root.after(2000, _safe_exit)
                else:
                    entry.configure(state="normal")
                    submit_btn.configure(state="normal")
                    cancel_btn.configure(state="normal")
                    if info['attempts'] > 0:
                        status.configure(text=L["master_wrong"].format(info['attempts'], max_attempts))
                    else:
                        status.configure(text="")
            except (KeyError, AttributeError, tk.TclError, TypeError) as e:
                logger.debug(f"Update status error / Ошибка обновления статуса / Помилка оновлення статусу: {e}")

        def _safe_exit():
            nonlocal is_closing
            is_closing = True
            try:
                root.destroy()
            except tk.TclError:
                pass
            sys.exit(0)

        def finish_ok() -> None:
            if is_closing:
                return
            result["ok"] = True
            try:
                root.destroy()
            except tk.TclError:
                pass

        def cancel() -> None:
            nonlocal is_closing
            is_closing = True
            result["ok"] = False
            try:
                root.destroy()
            except tk.TclError:
                pass

        def submit() -> None:
            if is_closing:
                return

            if cls.get_remaining_lockout_time() > 0:
                update_status()
                return

            pwd = entry.get()
            if pwd:
                success, error_code = cls.verify_with_2fa(pwd, source="startup")

                if success:
                    try:
                        set_key_from_master(pwd)
                    except (ValueError, TypeError, RuntimeError) as e:
                        logger.error(f"Failed to set key from master / Ошибка установки ключа из мастер-пароля / Помилка встановлення ключа з майстер-пароля: {e}")
                        return
                    finish_ok()
                    return
                elif error_code == "2fa_missing_secret":
                    logger.warning("2FA secret missing, disabling 2FA as fallback / Секрет 2FA отсутствует, отключаем 2FA как fallback / Секрет 2FA відсутній, вимикаємо 2FA як fallback")
                    if cls._cached_config:
                        try:
                            cls._cached_config.set_2fa_enabled(False)
                            cls._cached_config.save()
                        except (AttributeError, OSError) as e:
                            logger.debug(f"Failed to disable 2FA / Ошибка отключения 2FA / Помилка вимкнення 2FA: {e}")
                    if cls.verify(pwd, source="startup"):
                        try:
                            set_key_from_master(pwd)
                        except (ValueError, TypeError, RuntimeError) as e:
                            logger.error(f"Failed to set key from master / Ошибка установки ключа из мастер-пароля / Помилка встановлення ключа з майстер-пароля: {e}")
                            return
                        finish_ok()
                        return
                elif error_code == "2fa_cancelled":
                    cancel()
                    return
                elif error_code == "2fa_invalid_code":
                    status.configure(text=L.get("2fa_invalid_code", "Invalid verification code / Неверный код подтверждения / Невірний код підтвердження"))
                    entry.delete(0, "end")
                    entry.focus_set()
                    return

            info = cls.get_lockout_info()
            if info['is_permanently_locked']:
                status.configure(text=L.get("master_blocked", "Too many attempts. Program closed. / Слишком много попыток. Программа закрыта. / Занадто багато спроб. Програму закрито."))
                entry.configure(state="disabled")
                submit_btn.configure(state="disabled")
                cancel_btn.configure(state="disabled")
                root.after(2000, _safe_exit)
            elif info['is_locked']:
                status.configure(text=f"{L.get('lock_wait', 'Please wait / Подождите / Зачекайте')} {info['lockout_seconds']} {L.get('seconds_short', 'sec / сек / сек')}...")
                entry.delete(0, "end")
                entry.configure(state="disabled")
                submit_btn.configure(state="disabled")
                cancel_btn.configure(state="disabled")
                root.after(1000, update_status)
            else:
                status.configure(text=L["master_wrong"].format(info['attempts'], max_attempts))
                entry.delete(0, "end")
                entry.focus_set()

        submit_btn = ctk.CTkButton(
            btn_frame,
            text=L.get("unlock", "Unlock / Разблокировать / Розблокувати"),
            width=100,
            height=34,
            corner_radius=17,
            fg_color=btn_fg,
            hover_color=btn_hover,
            font=("Segoe UI", 12, "bold"),
            command=submit,
        )
        submit_btn.pack(side="left", padx=6)

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=L.get("close", "Close / Закрыть / Закрити"),
            width=100,
            height=34,
            corner_radius=17,
            fg_color="#8b0000",
            hover_color="#cc0000",
            font=("Segoe UI", 12, "bold"),
            command=cancel,
        )
        cancel_btn.pack(side="left", padx=6)

        entry.bind("<Return>", lambda _e: submit())
        entry.bind("<Escape>", lambda _e: cancel())
        root.protocol("WM_DELETE_WINDOW", cancel)

        update_status()

        try:
            root.mainloop()
        except (KeyboardInterrupt, SystemExit) as e:
            logger.debug(f"Startup prompt interrupted / Запрос при запуске прерван / Запит при запуску перервано: {e}")
            return False

        return result["ok"]