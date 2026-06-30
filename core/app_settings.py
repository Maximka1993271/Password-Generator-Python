"""
Centralized, type-safe application settings for Secure Pass Pro.
Централизованное, типобезопасное управление настройками Secure Pass Pro.
Централізоване, типобезпечне управління налаштуваннями Secure Pass Pro.

Single entry-point — replaces all direct «Config()» calls.

Usage
─────
    from core.app_settings import AppSettings

    s = AppSettings.instance()

    # Typed property read / write
    theme  = s.theme          # → "Dark" | "Light" | "System"
    s.theme = "Light"

    # Observer / change notification
    s.subscribe("theme", lambda old, new: apply_theme(new))

    # Bulk read / write (for migration / serialisation)
    snapshot = s.snapshot()
    s.restore(snapshot)

    # Generic fallback (original Config API still works)
    s.get("CLIP_TIMEOUT", 60)
    s.set("CLIP_TIMEOUT", 90)
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger("app_settings")

# ── Canonical key constants ───────────────────────────────────────
# Import once and re-export so callers never use raw strings.

class Key:
    """All valid config key names as typed constants.
    Все допустимые имена ключей конфигурации как типизированные константы.
    Усі допустимі імена ключів конфігурації як типізовані константи."""

    # ── Appearance ────────────────────────────────────────────
    THEME          = "THEME"        # "Dark" | "Light" | "System"
    LANGUAGE       = "LANG"         # "RU" | "EN" | "UA"
    RADIUS         = "RADIUS"       # int  0-50
    FONT_SIZE      = "font_size"    # int  10-28
    PDF_THEME      = "PDF_THEME"    # "light" | "dark"

    # ── Animations ────────────────────────────────────────────
    RGB            = "RGB"          # bool
    RGB_SPEED      = "RGB_SPEED"    # "slow" | "normal" | "fast"
    RGB_WIDTH      = "RGB_WIDTH"    # "thin" | "normal" | "thick"

    # ── Behaviour ─────────────────────────────────────────────
    SOUND          = "SOUND"        # bool
    CLIP_TIMEOUT   = "CLIP_TIMEOUT" # int seconds, 5-300
    AUTO_LOCK      = "AUTO_LOCK"    # bool
    AUTO_LOCK_TIMEOUT = "AUTO_LOCK_TIMEOUT"  # int minutes, 1-30
    AUTO_SAVE      = "auto_save"    # bool
    MAX_ATTEMPTS   = "MAX_ATTEMPTS" # int  3-10

    # ── 2-factor authentication ───────────────────────────────
    TFA_ENABLED         = "2fa_enabled"
    TFA_SECRET          = "2fa_secret"          # encrypted
    TFA_BACKUP_HASHES   = "2fa_backup_hashes"   # encrypted list
    TFA_ACCOUNT_NAME    = "2fa_account_name"
    TFA_SETUP_COMPLETED = "2fa_setup_completed"
    TFA_LAST_VERIFIED   = "2fa_last_verified"


# ── Type aliases ──────────────────────────────────────────────────
_Observer = Callable[[Any, Any], None]   # (old_value, new_value) → None


# ═════════════════════════════════════════════════════════════════
class AppSettings:
    """Singleton settings façade.

    Provides typed properties, change observers, snapshot/restore
    and delegates persistence to the existing Config backend.

    Одиночный фасад настроек с типизированными свойствами,
    наблюдателями изменений, снимками/восстановлением.

    Одиночний фасад налаштувань з типізованими властивостями,
    спостерігачами змін, знімками/відновленням.
    """

    _instance: Optional["AppSettings"] = None
    _lock: threading.Lock = threading.Lock()

    # ── Singleton ─────────────────────────────────────────────
    # ── Thread-safe singleton ─────────────────────────────────
    # __new__ is called before __init__ on every `AppSettings()` call.
    # The class-level lock guarantees that two threads cannot both
    # find _instance==None and each create a separate object.
    # object.__setattr__ bypasses any custom __setattr__ that subclasses
    # might add, keeping bootstrap state-writing safe.
    def __new__(cls) -> "AppSettings":
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        with cls._lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                object.__setattr__(obj, "_observers", {})  # key → List[_Observer]
                object.__setattr__(obj, "_config",    None)
                cls._instance = obj
        return cls._instance

    @classmethod
    def instance(cls) -> "AppSettings":
        """Return (or create) the singleton instance.
        Возвращает (или создаёт) единственный экземпляр.
        Повертає (або створює) єдиний екземпляр."""
        return cls()

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton — for unit tests only.
        Уничтожить синглтон — только для юнит-тестов.
        Знищити синглтон — лише для юніт-тестів."""
        with cls._lock:
            cls._instance = None

    # ── Internal Config backend ───────────────────────────────
    # ── Backend properties ────────────────────────────────────
    # _cm  → ConfigManager: used for ALL generic get/set/validate calls.
    #        Routes through the full 4-layer resolution stack.
    # _cfg → Config:        used only for 2FA helper methods that have
    #        no ConfigManager equivalent yet (set_2fa_secret, clear_2fa …).
    @property
    def _cm(self):
        """Layered ConfigManager — routes get/set through all layers."""
        from core.config_manager import ConfigManager
        return ConfigManager.instance()

    @property
    def _cfg(self):
        """Direct Config backend — for 2FA and schema helpers."""
        if self._config is None:
            try:
                from storage.config import Config
                object.__setattr__(self, "_config", Config())
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                logger.error("Cannot load Config backend: %s", exc)
                raise
        return self._config

    # ── Generic get / set (public, backward-compatible) ───────
    def get(self, key: str, default: Any = None) -> Any:
        """Return setting *key*, falling back to *default*.
        Возвращает настройку *key*, используя *default* при ошибке.
        Повертає налаштування *key*, використовуючи *default* при помилці."""
        try:
            return self._cm.get(key, default)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("get(%r): %s", key, exc)
            return default

    def set(self, key: str, value: Any) -> bool:
        """Persist *key = value* and notify observers.
        Сохраняет *key = value* и уведомляет наблюдателей.
        Зберігає *key = value* та сповіщає спостерігачів."""
        try:
            old = self.get(key)
            ok  = self._cm.set(key, value)
            if ok and old != value:
                self._notify(key, old, value)
            return ok
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("set(%r, %r): %s", key, value, exc)
            return False

    def has(self, key: str) -> bool:
        """Return True if *key* exists in the config store."""
        try:
            return self._cm.has_key(key)
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    # ── Observer / pub-sub ─────────────────────────────────────
    def subscribe(self, key: str, callback: _Observer) -> _Observer:
        """Register *callback(old, new)* for changes to *key*.

        Returns the callback so it can be used as a decorator::

            @settings.subscribe("theme")
            def _(old, new): apply_theme(new)

        Регистрирует *callback(old, new)* для изменений *key*.
        Реєструє *callback(old, new)* для змін *key*."""
        observers: Dict[str, List[_Observer]] = self._observers
        observers.setdefault(key, []).append(callback)
        return callback

    def unsubscribe(self, key: str, callback: _Observer) -> None:
        """Remove a previously registered observer.
        Удаляет ранее зарегистрированного наблюдателя.
        Видаляє раніше зареєстрованого спостерігача."""
        observers: Dict[str, List[_Observer]] = self._observers
        cbs = observers.get(key, [])
        if callback in cbs:
            cbs.remove(callback)

    # ── Observer notification ─────────────────────────────────
    # Iterating over a *copy* of the list (list(...)) means that a
    # callback can safely call unsubscribe() without mutating the list
    # while we are iterating it.
    def _notify(self, key: str, old: Any, new: Any) -> None:
        """
        Handle notify.
        Обработать notify.
        Обробити notify.
        """
        observers: Dict[str, List[_Observer]] = self._observers
        for cb in list(observers.get(key, [])):
            try:
                cb(old, new)
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                logger.error("Observer error for key %r: %s", key, exc)

    # ── Snapshot / restore ─────────────────────────────────────
    def snapshot(self) -> Dict[str, Any]:
        """Return a copy of the current config dict.
        Возвращает копию текущего словаря конфигурации.
        Повертає копію поточного словника конфігурації."""
        try:
            return dict(self._cfg.get_all())
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("snapshot(): %s", exc)
            return {}

    def restore(self, data: Dict[str, Any]) -> None:
        """Bulk-set all keys from *data* and notify observers.
        Устанавливает все ключи из *data* и уведомляет наблюдателей.
        Встановлює всі ключі з *data* та сповіщає спостерігачів."""
        for k, v in data.items():
            self.set(k, v)

    def save(self) -> bool:
        """Force an immediate write to disk.
        Немедленно записывает конфигурацию на диск.
        Негайно записує конфігурацію на диск."""
        try:
            return self._cfg.save()
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("save(): %s", exc)
            return False

    def reload(self) -> None:
        """Discard in-memory data and re-read from disk.
        Сбрасывает данные в памяти и перечитывает с диска.
        Скидає дані в пам'яті та перечитує з диска."""
        try:
            self._cfg._load()
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("reload(): %s", exc)

    # ═════════════════════════════════════════════════════════════
    #  Typed properties — one per setting key
    # ═════════════════════════════════════════════════════════════

    # ── Appearance ────────────────────────────────────────────
    @property
    def theme(self) -> str:
        """UI colour scheme: "Dark" | "Light" | "System"."""
        return str(self.get(Key.THEME, "Dark"))

    @theme.setter
    def theme(self, value: str) -> None:
        """
        Handle theme.
        Обработать theme.
        Обробити theme.
        """
        self.set(Key.THEME, value)

    @property
    def language(self) -> str:
        """Interface language: "RU" | "EN" | "UA"."""
        return str(self.get(Key.LANGUAGE, "RU"))

    @language.setter
    def language(self, value: str) -> None:
        """
        Handle language.
        Обработать language.
        Обробити language.
        """
        self.set(Key.LANGUAGE, value)

    # Backward-compat alias used in many places as config.get("LANG")
    @property
    def lang(self) -> str:
        """Alias for language."""
        return self.language

    @lang.setter
    def lang(self, value: str) -> None:
        """
        Handle lang.
        Обработать lang.
        Обробити lang.
        """
        self.language = value

    @property
    def radius(self) -> int:
        """Window corner radius (0-50)."""
        return int(self.get(Key.RADIUS, 25))

    @radius.setter
    def radius(self, value: int) -> None:
        """
        Handle radius.
        Обработать radius.
        Обробити radius.
        """
        self.set(Key.RADIUS, max(0, min(50, int(value))))

    @property
    def font_size(self) -> int:
        """UI font size in pt (10-28)."""
        return int(self.get(Key.FONT_SIZE, 14))

    @font_size.setter
    def font_size(self, value: int) -> None:
        """
        Handle font size.
        Обработать font size.
        Обробити font size.
        """
        self.set(Key.FONT_SIZE, max(10, min(28, int(value))))

    @property
    def pdf_theme(self) -> str:
        """PDF export colour scheme: "light" | "dark"."""
        return str(self.get(Key.PDF_THEME, "light"))

    @pdf_theme.setter
    def pdf_theme(self, value: str) -> None:
        """
        Handle pdf theme.
        Обработать pdf theme.
        Обробити pdf theme.
        """
        self.set(Key.PDF_THEME, value)

    # ── Animations ────────────────────────────────────────────
    @property
    def rgb(self) -> bool:
        """RGB border animation enabled."""
        return bool(self.get(Key.RGB, True))

    @rgb.setter
    def rgb(self, value: bool) -> None:
        """
        Handle rgb.
        Обработать rgb.
        Обробити rgb.
        """
        self.set(Key.RGB, bool(value))

    @property
    def rgb_speed(self) -> str:
        """RGB animation speed: "slow" | "normal" | "fast"."""
        return str(self.get(Key.RGB_SPEED, "normal"))

    @rgb_speed.setter
    def rgb_speed(self, value: str) -> None:
        """
        Handle rgb speed.
        Обработать rgb speed.
        Обробити rgb speed.
        """
        self.set(Key.RGB_SPEED, value)

    @property
    def rgb_width(self) -> str:
        """RGB border width: "thin" | "normal" | "thick"."""
        return str(self.get(Key.RGB_WIDTH, "normal"))

    @rgb_width.setter
    def rgb_width(self, value: str) -> None:
        """
        Handle rgb width.
        Обработать rgb width.
        Обробити rgb width.
        """
        self.set(Key.RGB_WIDTH, value)

    # ── Behaviour ─────────────────────────────────────────────
    @property
    def sound(self) -> bool:
        """UI sound effects enabled."""
        return bool(self.get(Key.SOUND, True))

    @sound.setter
    def sound(self, value: bool) -> None:
        """
        Handle sound.
        Обработать sound.
        Обробити sound.
        """
        self.set(Key.SOUND, bool(value))

    @property
    def clip_timeout(self) -> int:
        """Clipboard auto-clear timeout in seconds (5-300)."""
        return int(self.get(Key.CLIP_TIMEOUT, 60))

    @clip_timeout.setter
    def clip_timeout(self, value: int) -> None:
        """
        Handle clip timeout.
        Обработать clip timeout.
        Обробити clip timeout.
        """
        self.set(Key.CLIP_TIMEOUT, max(5, min(300, int(value))))

    @property
    def auto_lock(self) -> bool:
        """Automatic screen-lock enabled."""
        return bool(self.get(Key.AUTO_LOCK, False))

    @auto_lock.setter
    def auto_lock(self, value: bool) -> None:
        """
        Handle auto lock.
        Обработать auto lock.
        Обробити auto lock.
        """
        self.set(Key.AUTO_LOCK, bool(value))

    @property
    def auto_lock_timeout(self) -> int:
        """Auto-lock timeout in minutes (1-30)."""
        return int(self.get(Key.AUTO_LOCK_TIMEOUT, 5))

    @auto_lock_timeout.setter
    def auto_lock_timeout(self, value: int) -> None:
        """
        Handle auto lock timeout.
        Обработать auto lock timeout.
        Обробити auto lock timeout.
        """
        self.set(Key.AUTO_LOCK_TIMEOUT, max(1, min(30, int(value))))

    @property
    def auto_save(self) -> bool:
        """Auto-save enabled."""
        return bool(self.get(Key.AUTO_SAVE, False))

    @auto_save.setter
    def auto_save(self, value: bool) -> None:
        """
        Handle auto save.
        Обработать auto save.
        Обробити auto save.
        """
        self.set(Key.AUTO_SAVE, bool(value))

    @property
    def max_attempts(self) -> int:
        """Maximum login attempts before lockout (3-10)."""
        return int(self.get(Key.MAX_ATTEMPTS, 5))

    @max_attempts.setter
    def max_attempts(self, value: int) -> None:
        """
        Handle max attempts.
        Обработать max attempts.
        Обробити max attempts.
        """
        self.set(Key.MAX_ATTEMPTS, max(3, min(10, int(value))))

    # ── 2FA ───────────────────────────────────────────────────
    @property
    def tfa_enabled(self) -> bool:
        """Two-factor authentication enabled."""
        return bool(self.get(Key.TFA_ENABLED, False))

    @tfa_enabled.setter
    def tfa_enabled(self, value: bool) -> None:
        """
        Handle tfa enabled.
        Обработать tfa enabled.
        Обробити tfa enabled.
        """
        self.set(Key.TFA_ENABLED, bool(value))

    @property
    def tfa_secret(self) -> str:
        """TOTP secret (encrypted at rest)."""
        return str(self.get(Key.TFA_SECRET, ""))

    @tfa_secret.setter
    def tfa_secret(self, value: str) -> None:
        """
        Handle tfa secret.
        Обработать tfa secret.
        Обробити tfa secret.
        """
        self.set(Key.TFA_SECRET, value)

    @property
    def tfa_account_name(self) -> str:
        """Account name shown in authenticator apps."""
        return str(self.get(Key.TFA_ACCOUNT_NAME, "SecurePassPro_User"))

    @tfa_account_name.setter
    def tfa_account_name(self, value: str) -> None:
        """
        Handle tfa account name.
        Обработать tfa account name.
        Обробити tfa account name.
        """
        self.set(Key.TFA_ACCOUNT_NAME, value)

    @property
    def tfa_setup_completed(self) -> bool:
        """True once the 2FA setup wizard has been completed."""
        return bool(self.get(Key.TFA_SETUP_COMPLETED, False))

    @tfa_setup_completed.setter
    def tfa_setup_completed(self, value: bool) -> None:
        """
        Handle tfa setup completed.
        Обработать tfa setup completed.
        Обробити tfa setup completed.
        """
        self.set(Key.TFA_SETUP_COMPLETED, bool(value))


    # ══════════════════════════════════════════════════════════════
    #  Config-compatible API  (drop-in replacement for Config)
    # ══════════════════════════════════════════════════════════════

    def update(self, data: dict[str, Any]) -> int:
        """Bulk-set multiple key/value pairs — mirrors Config.update().
        Массово устанавливает несколько пар ключ/значение.
        Масово встановлює кілька пар ключ/значення."""
        success = 0
        for key, value in data.items():
            if self.set(key, value):
                success += 1
        return success

    def get_all(self) -> dict[str, Any]:
        """Return a copy of all settings — mirrors Config.get_all().
        Возвращает копию всех настроек.
        Повертає копію всіх налаштувань."""
        try:
            return dict(self._cfg.get_all())
        except (AttributeError, TypeError, RuntimeError):
            return {}

    def reset_to_defaults(self) -> bool:
        """Reset all settings to schema defaults — mirrors Config.reset_to_defaults().
        Сбрасывает все настройки к значениям по умолчанию.
        Скидає всі налаштування до значень за замовчуванням."""
        try:
            return self._cfg.reset_to_defaults()
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def validate_all(self) -> tuple[bool, list[str]]:
        """Validate all settings against schema — mirrors Config.validate_all().
        Проверяет все настройки по схеме.
        Перевіряє всі налаштування за схемою."""
        try:
            return self._cfg.validate_all()
        except (OSError, ValueError, TypeError, AttributeError):
            return True, []

    def get_schema_info(self) -> dict[str, Any]:
        """Return schema metadata — mirrors Config.get_schema_info().
        Возвращает метаданные схемы.
        Повертає метадані схеми."""
        try:
            return self._cfg.get_schema_info()
        except (AttributeError, RuntimeError):
            return {}

    # ── 2FA proxy methods ─────────────────────────────────────────
    # These delegate directly to the Config 2FA mixin so that code
    # using «self.config.is_2fa_enabled()» continues to work unchanged.

    def is_2fa_enabled(self) -> bool:
        """Return True if two-factor authentication is active.
        True, если двухфакторная аутентификация активна.
        True, якщо двофакторна аутентифікація активна."""
        try:
            return bool(self._cfg.is_2fa_enabled())
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def get_2fa_secret(self) -> str:
        """Return the (decrypted) TOTP secret.
        Возвращает (расшифрованный) TOTP-секрет.
        Повертає (розшифрований) TOTP-секрет."""
        try:
            return str(self._cfg.get_2fa_secret())
        except (AttributeError, RuntimeError, TypeError):
            return ""

    def get_2fa_backup_hashes(self) -> list[str]:
        """Return stored backup-code hashes.
        Возвращает хеши резервных кодов.
        Повертає хеші резервних кодів."""
        try:
            return list(self._cfg.get_2fa_backup_hashes())
        except (AttributeError, RuntimeError, TypeError):
            return []

    def get_2fa_account_name(self) -> str:
        """Return the account name shown in authenticator apps.
        Возвращает имя аккаунта для приложений аутентификации.
        Повертає ім'я акаунту для застосунків аутентифікації."""
        try:
            return str(self._cfg.get_2fa_account_name())
        except (AttributeError, TypeError, RuntimeError):
            return "SecurePassPro_User"

    def is_2fa_setup_completed(self) -> bool:
        """Return True once 2FA setup has been completed.
        True, когда настройка 2FA завершена.
        True, коли налаштування 2FA завершено."""
        try:
            return bool(self._cfg.is_2fa_setup_completed())
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_enabled(self, enabled: bool) -> bool:
        """Enable or disable 2FA.
        Включить или отключить 2FA.
        Увімкнути або вимкнути 2FA."""
        try:
            return bool(self._cfg.set_2fa_enabled(enabled))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_secret(self, secret: str) -> bool:
        """Store the TOTP secret (will be encrypted).
        Сохраняет TOTP-секрет (будет зашифрован).
        Зберігає TOTP-секрет (буде зашифровано)."""
        try:
            return bool(self._cfg.set_2fa_secret(secret))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_backup_hashes(self, hashes: list[str]) -> bool:
        """Store backup-code hashes.
        Сохраняет хеши резервных кодов.
        Зберігає хеші резервних кодів."""
        try:
            return bool(self._cfg.set_2fa_backup_hashes(hashes))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_account_name(self, name: str) -> bool:
        """Set the account name shown in authenticator apps.
        Устанавливает имя аккаунта для приложений аутентификации.
        Встановлює ім'я акаунту для застосунків аутентифікації."""
        try:
            return bool(self._cfg.set_2fa_account_name(name))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_setup_completed(self, completed: bool) -> bool:
        """Mark 2FA setup as complete.
        Отмечает настройку 2FA как завершённую.
        Позначає налаштування 2FA як завершене."""
        try:
            return bool(self._cfg.set_2fa_setup_completed(completed))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def set_2fa_last_verified(self, timestamp: str | None = None) -> bool:
        """Update the 2FA last-verified timestamp.
        Обновляет временную метку последней проверки 2FA.
        Оновлює мітку часу останньої перевірки 2FA."""
        try:
            return bool(self._cfg.set_2fa_last_verified(timestamp))
        except (OSError, ValueError, TypeError, AttributeError):
            return False

    def clear_2fa(self) -> bool:
        """Wipe all 2FA data from config.
        Удаляет все данные 2FA из конфигурации.
        Видаляє всі дані 2FA з конфігурації."""
        try:
            return bool(self._cfg.clear_2fa())
        except (OSError, ValueError, TypeError, AttributeError):
            return False


    def temp_override(self, **kwargs: Any):
        """Convenience: delegate temp_override to ConfigManager.
        Вспомогательный метод — делегирует temp_override в ConfigManager.
        Допоміжний метод — делегує temp_override до ConfigManager."""
        return self._cm.temp_override(**kwargs)

    def override(self, key: str, value: Any) -> None:
        """Set a runtime override without writing to disk.
        Устанавливает runtime-переопределение без записи на диск.
        Встановлює runtime-перевизначення без запису на диск."""
        self._cm.override(key, value)

    def clear_override(self, key: str) -> None:
        """Remove a runtime override.
        Удаляет runtime-переопределение.
        Видаляє runtime-перевизначення."""
        self._cm.clear_override(key)

    def change_history(self, key: str | None = None, limit: int = 50):
        """Return audit trail from ConfigManager.
        Возвращает журнал изменений из ConfigManager.
        Повертає журнал змін з ConfigManager."""
        return self._cm.change_history(key=key, limit=limit)

    def diff_from_defaults(self):
        """Return settings that differ from their defaults.
        Возвращает настройки, отличающиеся от значений по умолчанию.
        Повертає налаштування, що відрізняються від типових значень."""
        return self._cm.diff_from_defaults()

    def export_profile(self, path: str) -> bool:
        """Export current settings to a JSON profile file.
        Экспортирует настройки в JSON-файл профиля.
        Експортує налаштування у JSON-файл профілю."""
        return self._cm.export_profile(path)

    def import_profile(self, path: str):
        """Import settings from a JSON profile file.
        Импортирует настройки из JSON-файла профиля.
        Імпортує налаштування з JSON-файлу профілю."""
        return self._cm.import_profile(path)

    # ── Convenience / repr ────────────────────────────────────
    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation.
        Возвращает строковое представление для разработчиков.
        Повертає рядкове представлення для розробників.
        """
        try:
            return (f"AppSettings(theme={self.theme!r}, lang={self.language!r}, "
                    f"tfa={self.tfa_enabled})")
        except (AttributeError, RuntimeError, ImportError):
            return "AppSettings(<not loaded>)"


# ── Module-level singleton shortcut ──────────────────────────────
settings: AppSettings = AppSettings.instance()
"""Module-level singleton — ``from core.app_settings import settings``."""

__all__: List[str] = [
    "AppSettings",
    "Key",
    "settings",
]
