"""
Unified Configuration Manager for Secure Pass Pro.
Единый менеджер конфигурации для Secure Pass Pro.
Єдиний менеджер конфігурації для Secure Pass Pro.

Resolution order (highest priority first)
──────────────────────────────────────────
  Layer.OVERRIDE  — runtime overrides (testing, CLI flags)
  Layer.ENV       — SECUREPASS_<KEY>=value env variables
  Layer.FILE      — config file via Config backend
  Layer.DEFAULT   — schema default values

Usage
─────
    from core.config_manager import ConfigManager, Layer

    cm = ConfigManager.instance()

    # Read (respects all layers)
    theme = cm.get("THEME")          # → "Dark"

    # Write to file layer
    cm.set("THEME", "Light")

    # Temporary runtime override (no file write)
    cm.override("THEME", "System")
    cm.clear_override("THEME")

    # Context manager for tests
    with cm.temp_override(THEME="System", LANG="EN"):
        ...

    # Validation
    ok, errors = cm.validate_all()

    # Audit trail
    history = cm.change_history()

    # Profile import / export
    cm.export_profile("myprofile.json")
    cm.import_profile("myprofile.json")

    # Diff from defaults
    changed = cm.diff_from_defaults()
"""
from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from utils.logger import get_logger

logger = get_logger("config_manager")

# ── env-variable prefix ───────────────────────────────────────────
_ENV_PREFIX = "SECUREPASS_"

# ── Max audit-log entries kept in memory ─────────────────────────
_HISTORY_LIMIT = 200

# ── Type alias ────────────────────────────────────────────────────
_Observer = Callable[[str, Any, Any], None]   # key, old, new


# ══════════════════════════════════════════════════════════════════
class Layer(IntEnum):
    """Priority levels for configuration resolution.
    Уровни приоритета при разрешении конфигурации.
    Рівні пріоритету при вирішенні конфігурації."""
    DEFAULT  = 0   # schema hardcoded defaults
    FILE     = 1   # persisted config file
    ENV      = 2   # SECUREPASS_* environment variables
    OVERRIDE = 3   # runtime-only overrides (never persisted)


# ══════════════════════════════════════════════════════════════════
class ChangeRecord:
    """Single configuration change entry in the audit trail.
    Одна запись изменения конфигурации в журнале аудита.
    Один запис зміни конфігурації в журналі аудиту."""

    __slots__ = ("timestamp", "key", "old_value", "new_value", "layer", "source")

    def __init__(
        self,
        key: str,
        old_value: Any,
        new_value: Any,
        layer: Layer,
        source: str = "api",
    ) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.timestamp  = datetime.now().isoformat(timespec="seconds")
        self.key        = key
        self.old_value  = old_value
        self.new_value  = new_value
        self.layer      = layer
        self.source     = source

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to plain dict (for JSON export).
        Сериализовать в словарь.
        Серіалізувати у словник."""
        return {
            "timestamp": self.timestamp,
            "key":       self.key,
            "old":       "[FILTERED]" if _is_sensitive(self.key) else self.old_value,
            "new":       "[FILTERED]" if _is_sensitive(self.key) else self.new_value,
            "layer":     self.layer.name,
            "source":    self.source,
        }

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation.
        Возвращает строковое представление для разработчиков.
        Повертає рядкове представлення для розробників.
        """
        val = "[FILTERED]" if _is_sensitive(self.key) else f"{self.old_value!r} → {self.new_value!r}"
        return f"<ChangeRecord {self.timestamp} {self.key}: {val}>"


def _is_sensitive(key: str) -> bool:
    """Return True if *key* holds a secret (never log its value).
    True, если ключ содержит секрет.
    True, якщо ключ містить секрет."""
    return any(m in str(key).lower()
               for m in ("secret", "password", "token", "hash", "backup", "master"))


# ══════════════════════════════════════════════════════════════════
class ConfigManager:
    """Layered, singleton configuration manager.

    Responsible for:
    - Multi-layer value resolution (override → env → file → default)
    - Environment-variable mapping  (SECUREPASS_THEME → THEME)
    - Runtime overrides without touching the config file
    - Change audit trail
    - Schema validation across all keys
    - Profile import / export
    - Observer/pub-sub notifications

    Многоуровневый синглтон-менеджер конфигурации.
    Багаторівневий синглтон-менеджер конфігурації."""

    _instance: Optional["ConfigManager"] = None
    _lock: threading.Lock = threading.Lock()

    # ── Singleton ─────────────────────────────────────────────
    def __new__(cls) -> "ConfigManager":
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        with cls._lock:
            if cls._instance is None:
                obj = super().__new__(cls)
                # private state — init here to avoid __init__ re-runs
                object.__setattr__(obj, "_overrides",  {})   # key → value
                object.__setattr__(obj, "_env_cache",  None) # populated lazily
                object.__setattr__(obj, "_observers",  {})   # key → List[_Observer]
                object.__setattr__(obj, "_history",    [])   # List[ChangeRecord]
                object.__setattr__(obj, "_backend",    None) # Config instance (lazy)
                cls._instance = obj
        return cls._instance

    @classmethod
    def instance(cls) -> "ConfigManager":
        """Return (or create) the singleton.
        Вернуть (или создать) синглтон.
        Повернути (або створити) синглтон."""
        return cls()

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton — for unit tests only.
        Уничтожить синглтон — только для тестов.
        Знищити синглтон — лише для тестів."""
        with cls._lock:
            cls._instance = None

    # ── Backend ───────────────────────────────────────────────
    @property
    def _cfg(self):
        """Lazy-load the Config backend."""
        if self._backend is None:
            try:
                from storage.config import Config
                object.__setattr__(self, "_backend", Config())
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                logger.error("ConfigManager: cannot load Config backend: %s", exc)
                raise
        return self._backend

    @property
    def _schema(self) -> Dict[str, Any]:
        """Return the CONFIG_SCHEMA dict."""
        try:
            from storage.config_constants import CONFIG_SCHEMA
            return CONFIG_SCHEMA
        except ImportError:
            return {}

    # ── Environment variable mapping ─────────────────────────
    # ── Environment-variable layer ────────────────────────────
    # Any env var of the form SECUREPASS_<KEY>=<value> overrides the file
    # layer.  This is the standard 12-factor-app pattern and enables
    # containerised / CI deployments without touching config files.
    # Examples:
    #   SECUREPASS_THEME=Light  → overrides the colour scheme
    #   SECUREPASS_MAX_ATTEMPTS=3 → locks down login attempts
    #   SECUREPASS_SKIP_DB_INIT=true → CI/test mode, no real DB
    def _build_env_cache(self) -> Dict[str, Any]:
        """Scan os.environ for SECUREPASS_* keys and type-coerce them.
        Сканирует os.environ на ключи SECUREPASS_* и приводит типы.
        Сканує os.environ на ключі SECUREPASS_* та приводить типи."""
        cache: Dict[str, Any] = {}
        schema = self._schema
        for env_key, raw in os.environ.items():
            if not env_key.startswith(_ENV_PREFIX):
                continue
            cfg_key = env_key[len(_ENV_PREFIX):]  # strip prefix
            coerced = self._coerce_env(cfg_key, raw, schema)
            cache[cfg_key] = coerced
            logger.debug("Env override: %s=%r", cfg_key, coerced if not _is_sensitive(cfg_key) else "[FILTERED]")
        return cache

    @staticmethod
    def _coerce_env(key: str, raw: str, schema: Dict[str, Any]) -> Any:
        """Cast *raw* string to the type declared in schema for *key*.
        Приводит строку raw к типу из схемы для ключа key.
        Приводить рядок raw до типу зі схеми для ключа key."""
        entry = schema.get(key, {})
        expected = entry.get("type", str)
        try:
            if expected is bool:
                return raw.lower() in ("1", "true", "yes", "on")
            if expected is int:
                return int(raw)
            if expected is float:
                return float(raw)
            if expected is list:
                return json.loads(raw)
            return raw
        except (ValueError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("Cannot coerce env var %s=%r to %s: %s", key, raw, expected, exc)
            return raw

    @property
    def _env(self) -> Dict[str, Any]:
        """Cached env-var mapping (rebuilt on each call if empty).
        Кэшированное отображение env-переменных.
        Кешоване відображення env-змінних."""
        cache = self._env_cache
        if cache is None:
            cache = self._build_env_cache()
            object.__setattr__(self, "_env_cache", cache)
        return cache

    def reload_env(self) -> None:
        """Force a re-scan of environment variables.
        Принудительно пересканировать переменные среды.
        Примусово перескануватu змінні середовища."""
        object.__setattr__(self, "_env_cache", None)
        logger.debug("ENV cache invalidated")

    # ── Core get / set ────────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        """Resolve *key* across all layers (override → env → file → default).
        Разрешает ключ по всем слоям.
        Вирішує ключ по всіх шарах."""
        # ── Resolution order (highest priority first) ────────────
        # 4 OVERRIDE: set via override() — never persisted to disk
        # 3 ENV    : SECUREPASS_* environment variables
        # 2 FILE   : persisted config file (Config backend)
        # 1 DEFAULT: schema hardcoded defaults
        #
        # Layer 3: runtime overrides
        overrides: Dict[str, Any] = self._overrides
        if key in overrides:
            return overrides[key]

        # Layer 2: environment variables
        env = self._env
        if key in env:
            return env[key]

        # Layer 1: config file
        try:
            file_val = self._cfg.get(key, _SENTINEL := object())
            if file_val is not _SENTINEL:
                return file_val
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("get(%r) from file failed: %s", key, exc)

        # Layer 0: schema defaults / caller default
        schema = self._schema
        if key in schema:
            return schema[key]["default"]
        return default

    def set(self, key: str, value: Any, *, source: str = "api") -> bool:
        """Persist *key = value* to the file layer and notify observers.
        Сохраняет key = value в файловый слой и уведомляет наблюдателей.
        Зберігає key = value у файловий шар та сповіщає спостерігачів."""
        old = self.get(key)
        try:
            ok = self._cfg.set(key, value)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("set(%r, %r): %s", key, value, exc)
            return False
        if ok and old != value:
            self._record(key, old, value, Layer.FILE, source)
            self._notify(key, old, value)
        return ok

    def active_layer(self, key: str) -> Layer:
        """Return the layer currently supplying *key*'s value.
        Возвращает слой, который сейчас предоставляет значение key.
        Повертає шар, який зараз надає значення key."""
        if key in self._overrides:
            return Layer.OVERRIDE
        if key in self._env:
            return Layer.ENV
        try:
            val = self._cfg.get(key, _MISS := object())
            if val is not _MISS:
                return Layer.FILE
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        return Layer.DEFAULT

    # ── Runtime overrides (no file write) ────────────────────
    def override(self, key: str, value: Any, *, source: str = "override") -> None:
        """Set a runtime override that shadows all other layers.

        Does NOT write to disk.  Use :meth:`clear_override` to remove.

        Устанавливает runtime-переопределение, затеняющее все слои.
        Не записывает на диск. Используйте clear_override для удаления.

        Встановлює runtime-перевизначення, що затіняє всі шари.
        Не записує на диск. Використовуйте clear_override для видалення."""
        old = self.get(key)
        overrides: Dict[str, Any] = self._overrides
        overrides[key] = value
        if old != value:
            self._record(key, old, value, Layer.OVERRIDE, source)
            self._notify(key, old, value)

    def clear_override(self, key: str) -> None:
        """Remove a runtime override for *key*.
        Удаляет runtime-переопределение ключа.
        Видаляє runtime-перевизначення ключа."""
        overrides: Dict[str, Any] = self._overrides
        if key in overrides:
            old = overrides.pop(key)
            new = self.get(key)  # now resolves to lower layer
            self._record(key, old, new, Layer.FILE, "clear_override")
            self._notify(key, old, new)

    def clear_all_overrides(self) -> None:
        """Remove all runtime overrides.
        Удаляет все runtime-переопределения.
        Видаляє всі runtime-перевизначення."""
        overrides: Dict[str, Any] = self._overrides
        for key in list(overrides.keys()):
            self.clear_override(key)

    # ── Test / context helpers ────────────────────────────────
    # temp_override() is the canonical way to change settings in unit tests
    # without touching the real config file.  The original values are
    # snapshotted before the `with` block and restored in the `finally`
    # clause even if the body raises an exception.
    @contextmanager
    def temp_override(self, **kwargs: Any) -> Generator[None, None, None]:
        """Context manager for temporary overrides (ideal for unit tests).

        Usage::
            with cm.temp_override(THEME="System", LANG="EN"):
                ...  # overrides active here
            # overrides reverted automatically

        Контекстный менеджер для временных переопределений.
        Контекстний менеджер для тимчасових перевизначень."""
        prev: Dict[str, Any] = {}
        try:
            for key, value in kwargs.items():
                prev[key] = self.get(key)
                self.override(key, value, source="temp_override")
            yield
        finally:
            for key in kwargs:
                old_val = prev.get(key)
                overrides: Dict[str, Any] = self._overrides
                overrides.pop(key, None)
                new_val = self.get(key)
                self._notify(key, old_val, new_val)

    # ── Validation ────────────────────────────────────────────
    def validate(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate a single *key = value* against the schema.
        Проверяет одно значение ключа по схеме.
        Перевіряє одне значення ключа за схемою.

        Returns (True, "") or (False, error_message)."""
        schema = self._schema
        if key not in schema:
            return True, ""  # unknown keys pass by default
        entry    = schema[key]
        expected = entry["type"]
        if not isinstance(value, expected):
            return False, f"{key}: expected {expected.__name__}, got {type(value).__name__}"
        if "allowed" in entry and value not in entry["allowed"]:
            return False, f"{key}: {value!r} not in allowed {entry['allowed']}"
        if "min" in entry and isinstance(value, (int, float)) and value < entry["min"]:
            return False, f"{key}: {value} < min {entry['min']}"
        if "max" in entry and isinstance(value, (int, float)) and value > entry["max"]:
            return False, f"{key}: {value} > max {entry['max']}"
        return True, ""

    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate every known key's current effective value.
        Проверяет все известные ключи.
        Перевіряє всі відомі ключі."""
        errors: List[str] = []
        for key in self._schema:
            ok, msg = self.validate(key, self.get(key))
            if not ok:
                errors.append(msg)
        return len(errors) == 0, errors

    # ── Audit trail ───────────────────────────────────────────
    def _record(self, key: str, old: Any, new: Any, layer: Layer, source: str) -> None:
        """
        Handle record.
        Обработать record.
        Обробити record.
        """
        history: List[ChangeRecord] = self._history
        history.append(ChangeRecord(key, old, new, layer, source))
        if len(history) > _HISTORY_LIMIT:
            del history[: len(history) - _HISTORY_LIMIT]

    def change_history(
        self,
        key: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Return the most recent *limit* change records.

        Optionally filtered by *key*.

        Возвращает последние записи изменений, опционально по ключу.
        Повертає останні записи змін, опційно за ключем."""
        history: List[ChangeRecord] = self._history
        records = [r for r in history if key is None or r.key == key]
        return [r.to_dict() for r in records[-limit:]]

    def clear_history(self) -> None:
        """Erase the in-memory audit trail.
        Очищает журнал аудита.
        Очищує журнал аудиту."""
        history: List[ChangeRecord] = self._history
        history.clear()

    # ── Observer / pub-sub ─────────────────────────────────────
    def subscribe(
        self,
        key: str,
        callback: _Observer,
    ) -> _Observer:
        """Register *callback(key, old, new)* for changes to *key*.

        Returns *callback* so it works as a decorator.

        Регистрирует наблюдателя для изменений ключа.
        Реєструє спостерігача для змін ключа."""
        observers: Dict[str, List[_Observer]] = self._observers
        observers.setdefault(key, []).append(callback)
        return callback

    def unsubscribe(self, key: str, callback: _Observer) -> None:
        """Remove a registered observer.
        Удаляет наблюдателя.
        Видаляє спостерігача."""
        observers: Dict[str, List[_Observer]] = self._observers
        cbs = observers.get(key, [])
        if callback in cbs:
            cbs.remove(callback)

    def _notify(self, key: str, old: Any, new: Any) -> None:
        """
        Handle notify.
        Обработать notify.
        Обробити notify.
        """
        observers: Dict[str, List[_Observer]] = self._observers
        for cb in list(observers.get(key, [])):
            try:
                cb(key, old, new)
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                logger.error("Observer error for %r: %s", key, exc)

    # ── Schema defaults / diff ────────────────────────────────
    def defaults(self) -> Dict[str, Any]:
        """Return the schema's default values for every known key.
        Возвращает значения по умолчанию из схемы.
        Повертає значення за замовчуванням зі схеми."""
        return {k: v["default"] for k, v in self._schema.items()}

    def diff_from_defaults(self) -> Dict[str, Tuple[Any, Any]]:
        """Return keys whose current value differs from the schema default.

        Returns {key: (default, current)}.

        Возвращает ключи, значения которых отличаются от умолчаний.
        Повертає ключі, значення яких відрізняються від типових."""
        diff: Dict[str, Tuple[Any, Any]] = {}
        for key, entry in self._schema.items():
            default = entry["default"]
            current = self.get(key)
            if current != default:
                diff[key] = (default, current)
        return diff

    # ── Profile management ────────────────────────────────────
    def snapshot(self, *, include_sensitive: bool = False) -> Dict[str, Any]:
        """Return a dict of all current effective values.

        Sensitive keys are excluded by default.

        Возвращает текущий снимок всех настроек.
        Повертає поточний знімок усіх налаштувань."""
        out: Dict[str, Any] = {}
        for key in self._schema:
            if _is_sensitive(key) and not include_sensitive:
                continue
            out[key] = self.get(key)
        return out

    def restore(self, data: Dict[str, Any], *, source: str = "restore") -> int:
        """Bulk-apply *data* to the file layer.

        Returns the number of keys successfully written.

        Массово применяет данные к файловому слою.
        Масово застосовує дані до файлового шару."""
        ok = 0
        for key, value in data.items():
            if self.set(key, value, source=source):
                ok += 1
        logger.info("restore(): %d/%d keys written", ok, len(data))
        return ok

    def export_profile(self, path: str) -> bool:
        """Write current settings to a JSON profile file.
        Записывает текущие настройки в файл профиля JSON.
        Записує поточні налаштування у файл профілю JSON."""
        try:
            payload = {
                "exported_at":  datetime.now().isoformat(timespec="seconds"),
                "schema_version": self._cfg.get("_schema_version", 1),
                "settings":     self.snapshot(),
            }
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            logger.info("Profile exported → %s", path)
            return True
        except (OSError, TypeError, ValueError) as exc:
            logger.error("export_profile(%r): %s", path, exc)
            return False

    def import_profile(self, path: str, *, source: str = "import_profile") -> Tuple[int, List[str]]:
        """Read a JSON profile file and apply it.

        Returns (keys_applied, error_list).

        Читает файл профиля JSON и применяет его.
        Читає файл профілю JSON та застосовує його."""
        errors: List[str] = []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            settings: Dict[str, Any] = payload.get("settings", payload)
        except (OSError, json.JSONDecodeError, KeyError) as exc:
            msg = f"Cannot read profile {path!r}: {exc}"
            logger.error(msg)
            return 0, [msg]

        applied = 0
        for key, value in settings.items():
            ok_v, err = self.validate(key, value)
            if not ok_v:
                errors.append(err)
                continue
            if self.set(key, value, source=source):
                applied += 1
            else:
                errors.append(f"{key}: write failed")

        logger.info("import_profile(%r): %d applied, %d errors", path, applied, len(errors))
        return applied, errors

    def reset_to_defaults(self, *, source: str = "reset") -> bool:
        """Reset all settings to their schema defaults.
        Сбрасывает все настройки к значениям по умолчанию.
        Скидає всі налаштування до значень за замовчуванням."""
        try:
            ok = self._cfg.reset_to_defaults()
            if ok:
                self.clear_all_overrides()
                for key, entry in self._schema.items():
                    self._record(key, None, entry["default"], Layer.DEFAULT, source)
            return ok
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("reset_to_defaults(): %s", exc)
            return False

    # ── Persistence shortcuts ─────────────────────────────────
    def save(self) -> bool:
        """Force an immediate write to disk.
        Немедленно записывает данные на диск.
        Негайно записує дані на диск."""
        try:
            return self._cfg.save()
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("save(): %s", exc)
            return False

    def reload(self) -> None:
        """Re-read config file from disk and invalidate env cache.
        Перечитывает файл конфигурации и сбрасывает кэш env.
        Перечитує файл конфігурації та скидає кеш env."""
        try:
            self._cfg._load()
            self.reload_env()
            logger.info("Configuration reloaded from disk")
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            logger.error("reload(): %s", exc)


    # ── Config-compatible bridge methods ──────────────────────────
    # These let ConfigManager serve as a drop-in for Config
    # in any code that needs has_key(), get_schema_info(), or 2FA.

    def has_key(self, key: str) -> bool:
        """Return True if *key* has a non-default value in the file layer.
        True, если ключ имеет нестандартное значение.
        True, якщо ключ має не стандартне значення."""
        try:
            return self._cfg.has_key(key)
        except (AttributeError, RuntimeError):
            return key in self._schema

    def get_schema_info(self) -> Dict[str, Any]:
        """Return schema metadata for UI display.
        Возвращает метаданные схемы для UI.
        Повертає метадані схеми для UI."""
        try:
            return self._cfg.get_schema_info()
        except (AttributeError, RuntimeError):
            return {}

    # ── 2FA bridge (delegates to Config 2FA mixin) ───────────────
    def is_2fa_enabled(self) -> bool:
        """Return True if two-factor authentication is active."""
        try: return bool(self._cfg.is_2fa_enabled())
        except (ValueError, AttributeError, RuntimeError): return False

    def get_2fa_secret(self) -> str:
        """Return the (decrypted) TOTP secret."""
        try: return str(self._cfg.get_2fa_secret())
        except (ValueError, AttributeError, RuntimeError): return ""

    def get_2fa_backup_hashes(self) -> List[Any]:
        """Return stored backup-code hashes."""
        try: return list(self._cfg.get_2fa_backup_hashes())
        except (ValueError, AttributeError, RuntimeError): return []

    def get_2fa_account_name(self) -> str:
        """Return the account name shown in authenticator apps."""
        try: return str(self._cfg.get_2fa_account_name())
        except (ValueError, AttributeError, RuntimeError): return "SecurePassPro_User"

    def is_2fa_setup_completed(self) -> bool:
        """Return True once 2FA setup has been completed."""
        try: return bool(self._cfg.is_2fa_setup_completed())
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_enabled(self, enabled: bool) -> bool:
        """Enable or disable 2FA."""
        try: return bool(self._cfg.set_2fa_enabled(enabled))
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_secret(self, secret: str) -> bool:
        """Store the TOTP secret (will be encrypted)."""
        try: return bool(self._cfg.set_2fa_secret(secret))
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_backup_hashes(self, hashes: List[Any]) -> bool:
        """Store backup-code hashes."""
        try: return bool(self._cfg.set_2fa_backup_hashes(hashes))
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_account_name(self, name: str) -> bool:
        """Set the account name shown in authenticator apps."""
        try: return bool(self._cfg.set_2fa_account_name(name))
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_setup_completed(self, completed: bool) -> bool:
        """Mark 2FA setup as complete."""
        try: return bool(self._cfg.set_2fa_setup_completed(completed))
        except (ValueError, AttributeError, RuntimeError): return False

    def set_2fa_last_verified(self, timestamp: Optional[str] = None) -> bool:
        """Update the 2FA last-verified timestamp."""
        try: return bool(self._cfg.set_2fa_last_verified(timestamp))
        except (ValueError, AttributeError, RuntimeError): return False

    def clear_2fa(self) -> bool:
        """Wipe all 2FA data from config."""
        try: return bool(self._cfg.clear_2fa())
        except (ValueError, AttributeError, RuntimeError): return False

    # ── Repr ──────────────────────────────────────────────────
    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation.
        Возвращает строковое представление для разработчиков.
        Повертає рядкове представлення для розробників.
        """
        overrides: Dict[str, Any] = self._overrides
        env = self._env
        return (
            f"ConfigManager("
            f"overrides={list(overrides)}, "
            f"env_keys={list(env)}, "
            f"history={len(self._history)})"
        )


# ── Module-level singleton shortcut ──────────────────────────────
config_manager: ConfigManager = ConfigManager.instance()
"""Module-level singleton — ``from core.config_manager import config_manager``."""

__all__: List[str] = [
    "ConfigManager",
    "Layer",
    "ChangeRecord",
    "config_manager",
]
