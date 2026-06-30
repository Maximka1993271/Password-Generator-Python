"""
Shared TypedDict definitions used across the project.
Общие определения TypedDict для всего проекта.
Загальні визначення TypedDict для всього проекту.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


# ── Password records ──────────────────────────────────────────

class PasswordRecord(TypedDict):
    """A single password entry as returned by the database.
    Запись пароля, возвращаемая базой данных.
    Запис пароля, що повертається базою даних."""
    id:            int
    label:         str
    password:      str
    notes:         str
    url:           str
    username:      str
    email:         str
    category:      str
    favorite:      int
    created_at:    str
    updated_at:    str
    lang:          Optional[str]
    custom_fields: str          # JSON-encoded list
    tags:          str          # JSON-encoded list
    deleted_at:    Optional[str]


class PasswordRecordPartial(TypedDict, total=False):
    """Partial password record used for updates.
    Частичная запись пароля для обновлений.
    Частковий запис пароля для оновлень."""
    id:            int
    label:         str
    password:      str
    notes:         str
    url:           str
    username:      str
    email:         str
    category:      str
    favorite:      int
    lang:          Optional[str]
    custom_fields: str
    tags:          str


# ── Vault statistics ──────────────────────────────────────────

class VaultStats(TypedDict):
    """Statistics about the password vault.
    Статистика хранилища паролей.
    Статистика сховища паролів."""
    total:        int
    favorites:    int
    categories:   int
    weak:         int
    reused:       int
    old:          int
    with_2fa:     int
    last_updated: Optional[str]


# ── Crypto / security ─────────────────────────────────────────

class CryptoTestResults(TypedDict):
    """Results of the crypto self-test suite.
    Результаты самотестирования криптографии.
    Результати самотестування криптографії."""
    aesgcm:     bool
    xor:        bool
    metadata:   bool
    versioning: bool


class IntegrityStatus(TypedDict):
    """File integrity check status.
    Статус проверки целостности файлов.
    Статус перевірки цілісності файлів."""
    checked:     bool
    passed:      bool
    file_path:   str
    hash_algo:   str
    last_check:  Optional[str]


# ── Generator ─────────────────────────────────────────────────

class GeneratorConfig(TypedDict, total=False):
    """Password generator configuration.
    Конфигурация генератора паролей.
    Конфігурація генератора паролів."""
    length:          int
    use_upper:       bool
    use_lower:       bool
    use_digits:      bool
    use_symbols:     bool
    exclude_similar: bool
    exclude_ambiguous: bool
    custom_symbols:  str
    min_entropy:     float
    lang:            str


# ── Config ────────────────────────────────────────────────────

class AppConfig(TypedDict, total=False):
    """Application configuration dictionary.
    Словарь конфигурации приложения.
    Словник конфігурації застосунку."""
    LANG:                  str
    THEME:                 str
    FONT_SIZE:             int
    FONT_FAMILY:           str
    AUTO_LOCK_TIMEOUT:     int
    AUTO_LOCK_ENABLED:     bool
    CLIPBOARD_TIMEOUT:     int
    SHOW_STRENGTH_METER:   bool
    SOUND_ENABLED:         bool
    WINDOW_ROUNDING:       int
    CHECK_FOR_UPDATES:     bool
    SHOW_BREACH_WARNINGS:  bool
    TWO_FACTOR_ENABLED:    bool
    CUSTOM_SYMBOLS:        str
    MIN_PASSWORD_LENGTH:   int
    MAX_PASSWORD_LENGTH:   int


# ── Update system ─────────────────────────────────────────────

class UpdateStatus(TypedDict):
    """Status snapshot from the update system.
    Снимок состояния системы обновлений.
    Знімок стану системи оновлень."""
    current_version:      str
    updates_dir:          str
    rollback_dir:         str
    has_backups:          bool
    integrity_manifest:   bool


# ── Platform ──────────────────────────────────────────────────

class PlatformInfo(TypedDict):
    """Platform metadata dict returned by get_platform_info().
    Метаданные платформы.
    Метадані платформи."""
    system:     str
    release:    str
    version:    str
    machine:    str
    processor:  str
    python:     str
    is_admin:   bool
    is_wayland: bool
    de:         str


__all__: List[str] = [
    "PasswordRecord",
    "PasswordRecordPartial",
    "VaultStats",
    "CryptoTestResults",
    "IntegrityStatus",
    "GeneratorConfig",
    "AppConfig",
    "UpdateStatus",
    "PlatformInfo",
]
