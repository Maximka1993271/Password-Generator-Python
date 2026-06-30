"""
Centralized input validation for Secure Pass Pro.
Централизованная проверка ввода для Secure Pass Pro.
Централізована перевірка введення для Secure Pass Pro.

All user-supplied text MUST pass through this module before it touches
the database, the file system, or any security-sensitive API.

Public API
──────────
:func:`validate`          — run any number of validators, collect errors
:func:`sanitize_text`     — strip dangerous characters, normalize whitespace
:class:`PasswordValidator` — password strength + policy rules
:class:`FieldValidator`   — generic field rules (required, length, regex …)
:class:`URLValidator`     — URL format check
:class:`EmailValidator`   — e-mail format check
:class:`FilePathValidator` — safe file-path check
:class:`LabelValidator`   — entry label (site name) rules
:class:`MasterPasswordValidator` — master-password strength requirements

Example::

    from core.validators import validate, FieldValidator, LabelValidator

    errors = validate(
        label,    LabelValidator(),
        password, PasswordValidator(min_length=8),
        url,      URLValidator(required=False),
    )
    if errors:
        show_errors(errors)
        return
"""
from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from utils.logger import get_logger

logger = get_logger("validators")

# ── Constants ─────────────────────────────────────────────────────
MAX_LABEL_LEN      = 255
MAX_PASSWORD_LEN   = 1024
MAX_URL_LEN        = 2048
MAX_USERNAME_LEN   = 255
MAX_EMAIL_LEN      = 254        # RFC 5321
MAX_NOTES_LEN      = 10_000
MAX_CATEGORY_LEN   = 100
MAX_TAG_LEN        = 50
MAX_TAGS           = 20
MAX_MASTER_LEN     = 512
MIN_MASTER_LEN     = 8

# Characters forbidden in labels / category names (OS / SQL injection defence)
_FORBIDDEN_LABEL_CHARS = re.compile(r'[<>"\x00-\x1f\x7f]')
# Characters that could enable SQL injection even through parameterised queries
# in edge-case SQLite extensions  — we just strip them from notes/labels
_SQL_DANGEROUS = re.compile(r"(--|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bEXEC\b|\bUNION\b)",
                             re.IGNORECASE)
# Minimal URL scheme whitelist
_ALLOWED_SCHEMES = {'http', 'https', 'ftp', 'ftps', 'ssh', 'sftp', 'rdp', 'vnc', ''}

_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)
_URL_RE = re.compile(
    r'^(?:(?:https?|ftps?|ssh|sftp|rdp|vnc)://)?'
    r'(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+)$'
)


# ══════════════════════════════════════════════════════════════════
#  Sanitisation helpers
# ══════════════════════════════════════════════════════════════════

def sanitize_text(
    text: str,
    *,
    strip_html: bool = True,
    normalize_unicode: bool = True,
    max_len: Optional[int] = None,
) -> str:
    """Strip dangerous characters and normalize *text*.

    Удаляет опасные символы и нормализует текст.
    Видаляє небезпечні символи та нормалізує текст.

    Args:
        text (str): Raw user input.
        strip_html (bool): HTML-escape ``< > & " '`` characters.
        normalize_unicode (bool): Apply NFC normalization.
        max_len (int | None): Truncate to this length after sanitising.

    Returns:
        str: Sanitised string.
    """
    if not isinstance(text, str):
        text = str(text)
    # Normalise Unicode to prevent homograph attacks
    # (e.g. Cyrillic 'а' looks identical to Latin 'a')
    if normalize_unicode:
        text = unicodedata.normalize("NFC", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Remove ASCII control characters (null bytes, escape sequences, etc.)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # HTML-escape to prevent stored-XSS if the data is ever rendered as HTML
    if strip_html:
        text = html.escape(text, quote=True)
    # Truncate
    if max_len is not None:
        text = text[:max_len]
    return text


def sanitize_label(label: str) -> str:
    """Sanitise an entry label (site/service name).
    Очищает метку записи (название сайта/сервиса).
    Очищує мітку запису (назва сайту/сервісу)."""
    return sanitize_text(label, max_len=MAX_LABEL_LEN)


def sanitize_url(url: str) -> str:
    """Normalise a URL: strip whitespace, lowercase scheme.
    Нормализует URL: убирает пробелы, приводит схему к нижнему регистру.
    Нормалізує URL: прибирає пробіли, приводить схему до нижнього регістру."""
    url = url.strip()
    # Lowercase the scheme portion only
    if '://' in url:
        scheme, rest = url.split('://', 1)
        url = scheme.lower() + '://' + rest
    return url[:MAX_URL_LEN]


def sanitize_notes(notes: str) -> str:
    """Sanitise free-text notes: strip dangerous sequences.
    Очищает заметки: убирает опасные последовательности.
    Очищує нотатки: видаляє небезпечні послідовності."""
    notes = sanitize_text(notes, strip_html=False, max_len=MAX_NOTES_LEN)
    # Warn but do NOT silently strip SQL keywords — they can appear legitimately in notes
    if _SQL_DANGEROUS.search(notes):
        logger.debug("Notes contain SQL-like keywords — stored as-is (parameterised queries protect the DB)")
    return notes


# ══════════════════════════════════════════════════════════════════
#  Validation result
# ══════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Holds the outcome of one or more validation checks.
    Содержит результат одной или нескольких проверок валидации.
    Містить результат однієї або кількох перевірок валідації."""
    valid:  bool        = True
    errors: List[str]   = field(default_factory=list)
    field_errors: Dict[str, List[str]] = field(default_factory=dict)

    def add_error(self, message: str, field_name: str = "") -> None:
        """Record an error, optionally tied to *field_name*.
        Записывает ошибку, опционально привязанную к полю.
        Записує помилку, опційно прив'язану до поля."""
        self.valid = False
        self.errors.append(message)
        if field_name:
            self.field_errors.setdefault(field_name, []).append(message)

    def merge(self, other: "ValidationResult") -> None:
        """Merge *other* into this result.
        Объединяет другой результат с текущим.
        Об'єднує інший результат з поточним."""
        if not other.valid:
            self.valid = False
            self.errors.extend(other.errors)
            for k, v in other.field_errors.items():
                self.field_errors.setdefault(k, []).extend(v)

    def __bool__(self) -> bool:
        return self.valid

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid}, errors={self.errors})"


# ══════════════════════════════════════════════════════════════════
#  Base validator
# ══════════════════════════════════════════════════════════════════

class BaseValidator:
    """Abstract base for all validators.
    Абстрактная база для всех валидаторов.
    Абстрактна база для всіх валідаторів."""

    def __init__(self, required: bool = True, field_name: str = "") -> None:
        """Initialise the validator.
        Инициализировать валидатор.
        Ініціалізувати валідатор."""
        self.required   = required
        self.field_name = field_name

    def validate(self, value: Any) -> ValidationResult:
        """Validate *value* and return a :class:`ValidationResult`.
        Проверяет значение и возвращает ValidationResult.
        Перевіряє значення та повертає ValidationResult."""
        result = ValidationResult()
        value = self._coerce(value)

        # Empty-value check
        if not value:
            if self.required:
                result.add_error(
                    f"{self.field_name or 'Field'} is required. / "
                    f"{self.field_name or 'Поле'} обязательно. / "
                    f"{self.field_name or 'Поле'} обов'язкове.",
                    self.field_name,
                )
            return result

        # Delegate to subclass
        self._check(value, result)
        return result

    def _coerce(self, value: Any) -> str:
        """Convert *value* to str and strip whitespace.
        Привести значение к str и убрать пробелы.
        Привести значення до str та прибрати пробіли."""
        return str(value).strip() if value is not None else ""

    def _check(self, value: str, result: ValidationResult) -> None:
        """Override in subclasses to add specific rules.
        Переопределить в подклассах для специфических правил.
        Перевизначити в підкласах для специфічних правил."""

    def __call__(self, value: Any) -> ValidationResult:
        """Allow using the validator as a callable.
        Позволяет использовать валидатор как callable.
        Дозволяє використовувати валідатор як callable."""
        return self.validate(value)


# ══════════════════════════════════════════════════════════════════
#  Concrete validators
# ══════════════════════════════════════════════════════════════════

class FieldValidator(BaseValidator):
    """Generic text-field validator: required, length, pattern.
    Общий валидатор текстового поля: обязательность, длина, шаблон.
    Загальний валідатор текстового поля: обов'язковість, довжина, шаблон."""

    def __init__(
        self,
        *,
        required:  bool           = True,
        min_len:   int            = 0,
        max_len:   int            = 10_000,
        pattern:   Optional[str]  = None,
        pattern_msg: str          = "Invalid format.",
        field_name: str           = "",
        forbidden_chars: Optional[str] = None,
    ) -> None:
        """Initialise FieldValidator with constraints.
        Инициализировать FieldValidator с ограничениями.
        Ініціалізувати FieldValidator з обмеженнями."""
        super().__init__(required=required, field_name=field_name)
        self.min_len        = min_len
        self.max_len        = max_len
        self.pattern        = re.compile(pattern) if pattern else None
        self.pattern_msg    = pattern_msg
        self.forbidden_re   = re.compile(f"[{re.escape(forbidden_chars)}]") if forbidden_chars else None

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check length, forbidden chars, and regex pattern.
        Проверяет длину, запрещённые символы и шаблон.
        Перевіряє довжину, заборонені символи та шаблон."""
        fname = self.field_name or "Value"

        if self.min_len and len(value) < self.min_len:
            result.add_error(
                f"{fname} must be at least {self.min_len} characters. / "
                f"{fname} должно быть не менее {self.min_len} символов. / "
                f"{fname} повинно бути не менше {self.min_len} символів.",
                self.field_name,
            )
        if len(value) > self.max_len:
            result.add_error(
                f"{fname} must be at most {self.max_len} characters. / "
                f"{fname} должно быть не более {self.max_len} символов. / "
                f"{fname} повинно бути не більше {self.max_len} символів.",
                self.field_name,
            )
        if self.forbidden_re and self.forbidden_re.search(value):
            bad = set(self.forbidden_re.findall(value))
            result.add_error(
                f"{fname} contains forbidden characters: {', '.join(sorted(bad))}.",
                self.field_name,
            )
        if self.pattern and not self.pattern.match(value):
            result.add_error(self.pattern_msg, self.field_name)


class LabelValidator(FieldValidator):
    """Validator for entry labels (site/service names).
    Валидатор меток записей (названий сайтов/сервисов).
    Валідатор міток записів (назв сайтів/сервісів)."""

    def __init__(self, required: bool = True) -> None:
        """Initialise LabelValidator.
        Инициализировать LabelValidator.
        Ініціалізувати LabelValidator."""
        super().__init__(
            required=required,
            min_len=1,
            max_len=MAX_LABEL_LEN,
            field_name="Label",
        )

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check label length and forbidden characters.
        Проверяет длину метки и запрещённые символы.
        Перевіряє довжину мітки та заборонені символи."""
        super()._check(value, result)
        if _FORBIDDEN_LABEL_CHARS.search(value):
            result.add_error(
                "Label contains forbidden characters (< > \" or control codes). / "
                "Метка содержит запрещённые символы. / "
                "Мітка містить заборонені символи.",
                "Label",
            )
        # Detect suspiciously long repeated characters (e.g. 'aaaaaaa...' spam)
        if re.search(r'(.)\1{49,}', value):
            result.add_error(
                "Label appears invalid (too many repeated characters). / "
                "Метка выглядит недействительной (слишком много повторяющихся символов). / "
                "Мітка виглядає недійсною.",
                "Label",
            )


class PasswordValidator(BaseValidator):
    """Validate password strength and policy compliance.
    Проверяет надёжность пароля и соответствие политике.
    Перевіряє надійність пароля та відповідність політиці."""

    def __init__(
        self,
        *,
        required:       bool = True,
        min_length:     int  = 6,
        max_length:     int  = MAX_PASSWORD_LEN,
        require_upper:  bool = False,
        require_lower:  bool = False,
        require_digit:  bool = False,
        require_symbol: bool = False,
        field_name:     str  = "Password",
    ) -> None:
        """Initialise PasswordValidator with policy rules.
        Инициализировать PasswordValidator с правилами политики.
        Ініціалізувати PasswordValidator з правилами політики."""
        super().__init__(required=required, field_name=field_name)
        self.min_length     = min_length
        self.max_length     = max_length
        self.require_upper  = require_upper
        self.require_lower  = require_lower
        self.require_digit  = require_digit
        self.require_symbol = require_symbol

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check password length and character-class requirements.
        Проверяет длину пароля и требования к символам.
        Перевіряє довжину пароля та вимоги до символів."""
        fname = self.field_name

        # Length bounds
        if len(value) < self.min_length:
            result.add_error(
                f"{fname} must be at least {self.min_length} characters. / "
                f"{fname} должен быть не менее {self.min_length} символов. / "
                f"{fname} повинен бути не менше {self.min_length} символів.",
                fname,
            )
        if len(value) > self.max_length:
            result.add_error(
                f"{fname} exceeds maximum length of {self.max_length}. / "
                f"{fname} превышает максимальную длину {self.max_length}. / "
                f"{fname} перевищує максимальну довжину {self.max_length}.",
                fname,
            )
        # Character-class checks
        if self.require_upper and not re.search(r'[A-Z]', value):
            result.add_error(
                f"{fname} must contain at least one uppercase letter. / "
                f"{fname} должен содержать хотя бы одну заглавную букву. / "
                f"{fname} повинен містити хоча б одну велику літеру.",
                fname,
            )
        if self.require_lower and not re.search(r'[a-z]', value):
            result.add_error(
                f"{fname} must contain at least one lowercase letter. / "
                f"{fname} должен содержать хотя бы одну строчную букву. / "
                f"{fname} повинен містити хоча б одну малу літеру.",
                fname,
            )
        if self.require_digit and not re.search(r'\d', value):
            result.add_error(
                f"{fname} must contain at least one digit. / "
                f"{fname} должен содержать хотя бы одну цифру. / "
                f"{fname} повинен містити хоча б одну цифру.",
                fname,
            )
        if self.require_symbol and not re.search(r'[^a-zA-Z0-9]', value):
            result.add_error(
                f"{fname} must contain at least one special character. / "
                f"{fname} должен содержать хотя бы один специальный символ. / "
                f"{fname} повинен містити хоча б один спеціальний символ.",
                fname,
            )
        # Null-byte injection guard
        if '\x00' in value:
            result.add_error(
                f"{fname} contains invalid characters (null bytes).",
                fname,
            )


class MasterPasswordValidator(PasswordValidator):
    """Stricter validator for the master password.
    Более строгий валидатор для мастер-пароля.
    Суворіший валідатор для майстер-пароля."""

    def __init__(self) -> None:
        """Initialise MasterPasswordValidator.
        Инициализировать MasterPasswordValidator.
        Ініціалізувати MasterPasswordValidator."""
        super().__init__(
            required=True,
            min_length=MIN_MASTER_LEN,
            max_length=MAX_MASTER_LEN,
            field_name="Master password",
        )

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check master-password strength.
        Проверяет надёжность мастер-пароля.
        Перевіряє надійність майстер-пароля."""
        super()._check(value, result)
        if not result.valid:
            return  # don't pile on

        # Warn about very weak master passwords (not enforced — user can still proceed)
        has_upper  = bool(re.search(r'[A-Z]', value))
        has_lower  = bool(re.search(r'[a-z]', value))
        has_digit  = bool(re.search(r'\d',    value))
        has_symbol = bool(re.search(r'[^a-zA-Z0-9]', value))
        classes = sum([has_upper, has_lower, has_digit, has_symbol])

        if len(value) < 12 and classes < 3:
            result.add_error(
                "Master password is weak. Use at least 12 characters with mixed case, "
                "digits, and symbols. / "
                "Мастер-пароль слабый. Используйте не менее 12 символов с разными регистрами. / "
                "Майстер-пароль слабкий. Використовуйте не менше 12 символів з різними регістрами.",
                "Master password",
            )


class URLValidator(BaseValidator):
    """Validate a URL field.
    Проверяет поле URL.
    Перевіряє поле URL."""

    def __init__(self, required: bool = False, field_name: str = "URL") -> None:
        """Initialise URLValidator.
        Инициализировать URLValidator.
        Ініціалізувати URLValidator."""
        super().__init__(required=required, field_name=field_name)

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check URL length, scheme, and format.
        Проверяет длину URL, схему и формат.
        Перевіряє довжину URL, схему та формат."""
        fname = self.field_name

        if len(value) > MAX_URL_LEN:
            result.add_error(
                f"{fname} exceeds maximum length of {MAX_URL_LEN} characters.",
                fname,
            )
            return

        # Check for disallowed schemes (javascript:, data:, vbscript: etc.)
        if '://' in value:
            scheme = value.split('://')[0].lower().strip()
            if scheme not in _ALLOWED_SCHEMES and scheme:
                result.add_error(
                    f"{fname} has an unsupported scheme: {scheme!r}. "
                    f"Allowed: {', '.join(sorted(_ALLOWED_SCHEMES) or ['(none)'])}. / "
                    f"Схема {scheme!r} не поддерживается. / "
                    f"Схема {scheme!r} не підтримується.",
                    fname,
                )
                return

        # Basic format check
        if not _URL_RE.match(value):
            result.add_error(
                f"{fname} contains invalid characters. / "
                f"{fname} содержит недопустимые символы. / "
                f"{fname} містить неприпустимі символи.",
                fname,
            )


class EmailValidator(BaseValidator):
    """Validate an e-mail address field.
    Проверяет поле адреса электронной почты.
    Перевіряє поле адреси електронної пошти."""

    def __init__(self, required: bool = False, field_name: str = "Email") -> None:
        """Initialise EmailValidator.
        Инициализировать EmailValidator.
        Ініціалізувати EmailValidator."""
        super().__init__(required=required, field_name=field_name)

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check e-mail length and RFC 5321 format.
        Проверяет длину e-mail и формат RFC 5321.
        Перевіряє довжину e-mail та формат RFC 5321."""
        fname = self.field_name

        if len(value) > MAX_EMAIL_LEN:
            result.add_error(
                f"{fname} exceeds maximum length of {MAX_EMAIL_LEN} characters.",
                fname,
            )
            return

        if not _EMAIL_RE.match(value):
            result.add_error(
                f"{fname} is not a valid e-mail address. / "
                f"{fname} не является допустимым адресом электронной почты. / "
                f"{fname} не є допустимою адресою електронної пошти.",
                fname,
            )


class FilePathValidator(BaseValidator):
    """Validate a file-system path (no traversal, no null bytes).
    Проверяет путь файловой системы.
    Перевіряє шлях файлової системи."""

    TRAVERSAL = re.compile(r'\.\.[/\\]|[/\\]\.\.')
    NULL_BYTE  = re.compile(r'\x00')

    def __init__(
        self,
        *,
        required:         bool         = True,
        allowed_extensions: Optional[List[str]] = None,
        max_len:          int          = 4096,
        field_name:       str          = "File path",
        must_exist:       bool         = False,
    ) -> None:
        """Initialise FilePathValidator.
        Инициализировать FilePathValidator.
        Ініціалізувати FilePathValidator."""
        super().__init__(required=required, field_name=field_name)
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.max_len    = max_len
        self.must_exist = must_exist

    def _check(self, value: str, result: ValidationResult) -> None:
        """Check path for traversal, null bytes, length, and extension.
        Проверяет путь на попытки обхода, нулевые байты, длину и расширение.
        Перевіряє шлях на спроби обходу, нульові байти, довжину та розширення."""
        import os
        fname = self.field_name

        # Null-byte injection (classic UNIX path-truncation attack)
        if self.NULL_BYTE.search(value):
            result.add_error(f"{fname} contains a null byte.", fname)
            return

        # Path-traversal prevention
        if self.TRAVERSAL.search(value):
            result.add_error(
                f"{fname} contains path-traversal sequences (../ or ..\\). / "
                f"{fname} содержит последовательности обхода пути. / "
                f"{fname} містить послідовності обходу шляху.",
                fname,
            )
            return

        if len(value) > self.max_len:
            result.add_error(f"{fname} path is too long (max {self.max_len}).", fname)

        if self.allowed_extensions:
            ext = os.path.splitext(value)[1].lower()
            if ext not in self.allowed_extensions:
                result.add_error(
                    f"{fname}: extension {ext!r} not allowed. "
                    f"Allowed: {', '.join(self.allowed_extensions)}.",
                    fname,
                )

        if self.must_exist and not os.path.exists(value):
            result.add_error(f"{fname} does not exist: {value!r}.", fname)


class CategoryValidator(FieldValidator):
    """Validate an entry category name.
    Проверяет название категории записи.
    Перевіряє назву категорії запису."""

    def __init__(self, required: bool = False) -> None:
        """Initialise CategoryValidator.
        Инициализировать CategoryValidator.
        Ініціалізувати CategoryValidator."""
        super().__init__(
            required=required,
            min_len=0,
            max_len=MAX_CATEGORY_LEN,
            field_name="Category",
            forbidden_chars='<>"',
        )


class TagValidator(BaseValidator):
    """Validate a list of tag strings.
    Проверяет список тегов.
    Перевіряє список тегів."""

    def __init__(self, required: bool = False) -> None:
        """Initialise TagValidator.
        Инициализировать TagValidator.
        Ініціалізувати TagValidator."""
        super().__init__(required=required, field_name="Tags")

    def validate_list(self, tags: List[str]) -> ValidationResult:
        """Validate a list of tag strings.
        Проверяет список строк тегов.
        Перевіряє список рядків тегів."""
        result = ValidationResult()
        if len(tags) > MAX_TAGS:
            result.add_error(
                f"Too many tags (max {MAX_TAGS}). / "
                f"Слишком много тегов (макс. {MAX_TAGS}). / "
                f"Забагато тегів (макс. {MAX_TAGS}).",
                "Tags",
            )
        for tag in tags:
            if len(tag) > MAX_TAG_LEN:
                result.add_error(
                    f"Tag {tag!r} exceeds maximum length of {MAX_TAG_LEN}.",
                    "Tags",
                )
            if _FORBIDDEN_LABEL_CHARS.search(tag):
                result.add_error(
                    f"Tag {tag!r} contains forbidden characters.",
                    "Tags",
                )
        return result


# ══════════════════════════════════════════════════════════════════
#  Compound validator: full password-entry record
# ══════════════════════════════════════════════════════════════════

class PasswordEntryValidator:
    """Validate a complete password-entry record before saving to DB.
    Проверяет полную запись пароля перед сохранением в БД.
    Перевіряє повний запис пароля перед збереженням до БД."""

    _label    = LabelValidator(required=True)
    _password = PasswordValidator(required=True, min_length=1)
    _url      = URLValidator(required=False)
    _email    = EmailValidator(required=False)
    _category = CategoryValidator(required=False)
    _tags     = TagValidator(required=False)
    _notes    = FieldValidator(required=False, max_len=MAX_NOTES_LEN, field_name="Notes")
    _username = FieldValidator(required=False, max_len=MAX_USERNAME_LEN, field_name="Username")

    def validate(
        self,
        *,
        label:    str,
        password: str,
        url:      str = "",
        email:    str = "",
        username: str = "",
        notes:    str = "",
        category: str = "",
        tags:     Optional[List[str]] = None,
    ) -> ValidationResult:
        """Validate all fields of a password entry.
        Проверяет все поля записи пароля.
        Перевіряє всі поля запису пароля."""
        combined = ValidationResult()
        for validator, value in [
            (self._label,    label),
            (self._password, password),
            (self._url,      url),
            (self._email,    email),
            (self._username, username),
            (self._notes,    notes),
            (self._category, category),
        ]:
            combined.merge(validator.validate(value))
        if tags:
            combined.merge(self._tags.validate_list(tags))
        return combined


# ══════════════════════════════════════════════════════════════════
#  Convenience function
# ══════════════════════════════════════════════════════════════════

def validate(*pairs: Any) -> List[str]:
    """Run validators in (value, validator) pairs; return all error messages.

    Запускает пары (значение, валидатор) и возвращает все сообщения об ошибках.
    Запускає пари (значення, валідатор) та повертає всі повідомлення про помилки.

    Args:
        *pairs: Alternating (value, validator) arguments.

    Returns:
        List[str]: All collected error messages (empty = valid).

    Example::

        errors = validate(
            label,    LabelValidator(),
            password, PasswordValidator(min_length=8),
            url,      URLValidator(required=False),
        )
        if errors:
            show_errors(errors)
            return
    """
    if len(pairs) % 2 != 0:
        raise ValueError("validate() requires an even number of arguments: (value, validator) pairs")
    errors: List[str] = []
    for i in range(0, len(pairs), 2):
        value, validator = pairs[i], pairs[i + 1]
        result = validator.validate(value)
        errors.extend(result.errors)
    return errors


__all__: List[str] = [
    # Main function
    "validate",
    # Sanitisation
    "sanitize_text", "sanitize_label", "sanitize_url", "sanitize_notes",
    # Validators
    "ValidationResult",
    "BaseValidator",
    "FieldValidator",
    "LabelValidator",
    "PasswordValidator",
    "MasterPasswordValidator",
    "URLValidator",
    "EmailValidator",
    "FilePathValidator",
    "CategoryValidator",
    "TagValidator",
    "PasswordEntryValidator",
    # Constants
    "MAX_LABEL_LEN", "MAX_PASSWORD_LEN", "MAX_URL_LEN",
    "MAX_EMAIL_LEN", "MAX_NOTES_LEN", "MAX_CATEGORY_LEN",
    "MIN_MASTER_LEN", "MAX_MASTER_LEN",
]


# ══════════════════════════════════════════════════════════════════
#  Extended validation  — added in v4.0 refactor
# ══════════════════════════════════════════════════════════════════

import hashlib
import json
import math
import struct
import base64 as _base64


# ── Warning / non-blocking result ────────────────────────────────

@dataclass
class ValidationWarning:
    """Non-blocking advisory produced by extended validators.
    Неблокирующее предупреждение расширенных валидаторов.
    Незаблокуюче попередження розширених валідаторів."""
    field:   str
    message: str
    code:    str = ""

    def __str__(self) -> str:
        return f"[{self.field}] {self.message}"


@dataclass
class ExtendedValidationResult(ValidationResult):
    """ValidationResult extended with a list of non-blocking warnings.
    ValidationResult с добавленным списком предупреждений.
    ValidationResult з доданим списком попереджень."""
    warnings: List[ValidationWarning] = field(default_factory=list)

    def add_warning(self, field: str, message: str, code: str = "") -> None:
        """Add a non-blocking warning — does not set valid=False.
        Добавляет предупреждение, не блокирующее сохранение.
        Додає попередження, що не блокує збереження."""
        self.warnings.append(ValidationWarning(field=field, message=message, code=code))

    def has_warnings(self) -> bool:
        """Return True if any warnings were generated.
        True, если есть предупреждения.
        True, якщо є попередження."""
        return bool(self.warnings)


# ── Password entropy & strength ───────────────────────────────────

def _pool_size(password: str) -> int:
    """Estimate the character-pool size for *password*.
    Оценивает размер пула символов для пароля.
    Оцінює розмір пулу символів для пароля."""
    pool = 0
    if re.search(r'[a-z]', password):         pool += 26
    if re.search(r'[A-Z]', password):         pool += 26
    if re.search(r'\d', password):            pool += 10
    if re.search(r'[^a-zA-Z0-9]', password):  pool += 33
    return max(pool, 1)


def estimate_entropy(password: str) -> float:
    """Estimate Shannon entropy of *password* in bits.

    H = L × log2(N)  where L = length, N = character-pool size.

    Оценивает энтропию Шеннона пароля в битах.
    Оцінює ентропію Шеннона пароля в бітах.

    Args:
        password (str): Plaintext password to evaluate.

    Returns:
        float: Estimated entropy in bits (higher → stronger).
    """
    if not password:
        return 0.0
    pool = _pool_size(password)
    return len(password) * math.log2(pool)


def score_password(password: str) -> Dict[str, Any]:
    """Score *password* strength on a 0-100 scale.

    Оценивает надёжность пароля по шкале 0-100.
    Оцінює надійність пароля за шкалою 0-100.

    Args:
        password (str): Plaintext password.

    Returns:
        Dict with keys:
          ``score``   (int 0-100),
          ``label``   (str: "Very Weak" / "Weak" / "Fair" / "Strong" / "Very Strong"),
          ``entropy`` (float, bits),
          ``warnings`` (List[str], human-readable advisories).
    """
    if not password:
        return {"score": 0, "label": "Very Weak", "entropy": 0.0, "warnings": []}

    entropy  = estimate_entropy(password)
    warnings: List[str] = []

    # Base score from entropy
    # < 28 bits → Very Weak, 28-36 → Weak, 36-60 → Fair, 60-80 → Strong, 80+ → Very Strong
    if   entropy < 28:  score, label = 10,  "Very Weak"
    elif entropy < 36:  score, label = 30,  "Weak"
    elif entropy < 60:  score, label = 55,  "Fair"
    elif entropy < 80:  score, label = 75,  "Strong"
    else:               score, label = 95,  "Very Strong"

    # Deductions for patterns
    if re.search(r'(.)\1{3,}', password):          # 4+ repeated chars
        score -= 15;  warnings.append("Repeated characters weaken the password.")
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|qwerty|asdf)', password.lower()):
        score -= 10;  warnings.append("Sequential characters detected.")
    if len(set(password)) < len(password) * 0.4:   # low unique-char ratio
        score -= 10;  warnings.append("Too many repeated characters.")

    # Bonuses
    if re.search(r'[^a-zA-Z0-9]', password):        score += 5   # symbols
    if len(password) >= 20:                          score += 5   # long
    if re.search(r'[a-z].*[A-Z]|[A-Z].*[a-z]', password):  score += 3

    score = max(0, min(100, score))

    # Recalculate label from final score
    if   score < 20:  label = "Very Weak"
    elif score < 40:  label = "Weak"
    elif score < 60:  label = "Fair"
    elif score < 80:  label = "Strong"
    else:             label = "Very Strong"

    return {"score": score, "label": label, "entropy": round(entropy, 1), "warnings": warnings}


# ── Duplicate-label detector ─────────────────────────────────────

def check_duplicate_label(label: str, exclude_id: Optional[int] = None) -> bool:
    """Return True if *label* already exists in the password database.

    Возвращает True, если метка уже существует в базе паролей.
    Повертає True, якщо мітка вже існує в базі паролів.

    Args:
        label (str): The label to check.
        exclude_id (int | None): Record ID to exclude (use when editing).

    Returns:
        bool: True if a duplicate exists.
    """
    try:
        from storage.database import PasswordDB
        all_records = PasswordDB.get_all() or []
        label_lower = label.strip().lower()
        for rec in all_records:
            if rec.get("label", "").lower() == label_lower:
                if exclude_id is not None and rec.get("id") == exclude_id:
                    continue
                return True
    except Exception:  # noqa: BLE001 — DB might not be initialised yet
        pass
    return False


# ── Custom-fields JSON validator ─────────────────────────────────

def validate_custom_fields(json_str: str) -> Tuple[bool, str]:
    """Validate the JSON structure used for custom_fields.

    Expected format: ``[{"name": "...", "value": "..."}, ...]``

    Проверяет структуру JSON для пользовательских полей.
    Перевіряє структуру JSON для користувацьких полів.

    Args:
        json_str (str): JSON-encoded list of ``{name, value}`` dicts.

    Returns:
        Tuple[bool, str]: ``(True, "")`` on success or
            ``(False, error_message)`` on failure.
    """
    if not json_str or json_str.strip() in ("", "[]", "null"):
        return True, ""
    try:
        data = json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as exc:
        return False, f"custom_fields is not valid JSON: {exc}"
    if not isinstance(data, list):
        return False, "custom_fields must be a JSON array."
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f"custom_fields[{i}] must be a JSON object."
        if "name" not in item:
            return False, f"custom_fields[{i}] is missing key 'name'."
        if len(str(item.get("name", ""))) > 100:
            return False, f"custom_fields[{i}].name exceeds 100 characters."
        if len(str(item.get("value", ""))) > 4096:
            return False, f"custom_fields[{i}].value exceeds 4096 characters."
    if len(data) > 50:
        return False, f"Too many custom fields (max 50, got {len(data)})."
    return True, ""


# ── TOTP secret validator ─────────────────────────────────────────

def validate_totp_secret(secret: str) -> Tuple[bool, str]:
    """Validate a TOTP/HOTP Base32-encoded secret key.

    Проверяет секретный ключ TOTP/HOTP в кодировке Base32.
    Перевіряє секретний ключ TOTP/HOTP у кодуванні Base32.

    Args:
        secret (str): Raw or padded Base32 string.

    Returns:
        Tuple[bool, str]: ``(True, "")`` or ``(False, error_message)``.
    """
    if not secret:
        return False, "TOTP secret is empty."
    clean = secret.strip().upper().replace(" ", "").replace("-", "")
    if not re.match(r'^[A-Z2-7]+=*$', clean):
        return False, "TOTP secret contains invalid characters (must be Base32: A-Z, 2-7)."
    # Pad to multiple of 8
    pad = len(clean) % 8
    if pad:
        clean += "=" * (8 - pad)
    try:
        decoded = _base64.b32decode(clean)
        if len(decoded) < 10:
            return False, "TOTP secret is too short (minimum 10 bytes / 16 Base32 chars)."
        if len(decoded) > 256:
            return False, "TOTP secret is too long."
    except Exception as exc:
        return False, f"TOTP secret is not valid Base32: {exc}"
    return True, ""


# ── URL homograph / IDN attack detector ──────────────────────────

def check_url_homograph(url: str) -> Optional[str]:
    """Detect potential IDN homograph attacks in *url*.

    Returns a warning message if suspicious Unicode is detected,
    otherwise returns None.

    Обнаруживает потенциальные атаки через омографы IDN.
    Виявляє потенційні атаки через омографи IDN.

    Args:
        url (str): URL to check.

    Returns:
        str | None: Warning message or None if safe.
    """
    if not url:
        return None
    try:
        # Extract hostname
        m = re.search(r'://([^/:?#]+)', url)
        if not m:
            return None
        host = m.group(1)
        # Flag hostnames with mixed scripts (Latin + Cyrillic etc.)
        has_latin   = bool(re.search(r'[a-zA-Z]', host))
        has_cyrillic = bool(re.search(r'[\u0400-\u04FF]', host))
        has_greek    = bool(re.search(r'[\u0370-\u03FF]', host))
        script_count = sum([has_latin, has_cyrillic, has_greek])
        if script_count > 1:
            return (f"URL hostname '{host}' mixes character scripts "
                    f"(possible homograph/phishing attack). / "
                    f"Имя хоста смешивает алфавиты (возможная атака омографом).")
        # Punycode indicator
        if 'xn--' in host.lower():
            return (f"URL uses Punycode (IDN) encoding: '{host}'. "
                    f"Verify it is the intended domain. / "
                    f"URL использует Punycode — проверьте домен.")
    except (AttributeError, re.error):
        pass
    return None


# ── Compound extended validator ───────────────────────────────────

class ExtendedPasswordEntryValidator:
    """Full extended validation for a password entry before DB write.

    Covers basic field rules AND:
    • Password entropy / strength scoring
    • Duplicate-label detection
    • Custom-fields JSON structure
    • URL homograph detection
    • Non-blocking strength warnings

    Расширенная валидация записи пароля перед записью в БД.
    Розширена валідація запису пароля перед записом до БД.
    """

    _base = PasswordEntryValidator()

    def validate(
        self,
        *,
        label:         str,
        password:      str,
        url:           str              = "",
        email:         str              = "",
        username:      str              = "",
        notes:         str              = "",
        category:      str              = "",
        tags:          Optional[List[str]] = None,
        custom_fields: str              = "[]",
        exclude_id:    Optional[int]    = None,
        warn_duplicate: bool            = True,
        warn_weak:      bool            = True,
    ) -> ExtendedValidationResult:
        """Validate all fields and return an ExtendedValidationResult.

        Validates all fields and returns an ExtendedValidationResult
        with errors (blocking) and warnings (non-blocking).

        Проверяет все поля и возвращает ExtendedValidationResult
        с ошибками (блокирующими) и предупреждениями (нет).
        Перевіряє всі поля та повертає ExtendedValidationResult.

        Args:
            label (str): Entry display name.
            password (str): Plaintext password.
            url (str): Associated URL.
            email (str): Associated e-mail.
            username (str): Associated username.
            notes (str): Free-text notes.
            category (str): Category name.
            tags (List[str] | None): Tag list.
            custom_fields (str): JSON-encoded custom field list.
            exclude_id (int | None): Exclude this DB id from duplicate check.
            warn_duplicate (bool): Warn (not error) when label exists.
            warn_weak (bool): Warn when password entropy < 36 bits.

        Returns:
            ExtendedValidationResult: Contains .valid, .errors, .warnings.
        """
        result = ExtendedValidationResult()

        # ── Run base field validation (blocking) ──────────────────
        base = self._base.validate(
            label=label, password=password, url=url,
            email=email, username=username, notes=notes,
            category=category, tags=tags,
        )
        result.merge(base)

        # ── URL homograph check (non-blocking warning) ────────────
        if url:
            homograph_warning = check_url_homograph(url)
            if homograph_warning:
                result.add_warning("url", homograph_warning, code="HOMOGRAPH")

        # ── Custom-fields JSON structure (blocking) ───────────────
        if custom_fields:
            cf_ok, cf_err = validate_custom_fields(custom_fields)
            if not cf_ok:
                result.add_error(cf_err, "custom_fields")

        # ── Password strength (non-blocking warnings) ─────────────
        if warn_weak and password:
            strength = score_password(password)
            if strength["score"] < 30:
                result.add_warning(
                    "password",
                    f"Password is {strength['label']} "
                    f"(entropy ≈ {strength['entropy']} bits). "
                    f"Consider using the password generator. / "
                    f"Пароль слабый ({strength['entropy']} бит). / "
                    f"Пароль слабкий ({strength['entropy']} біт).",
                    code="WEAK_PASSWORD",
                )
            for w in strength.get("warnings", []):
                result.add_warning("password", w, code="PASSWORD_PATTERN")

        # ── Duplicate label detection (non-blocking warning) ──────
        if warn_duplicate and label and result.valid:
            if check_duplicate_label(label, exclude_id=exclude_id):
                result.add_warning(
                    "label",
                    f"An entry named '{label}' already exists. "
                    f"Consider using a more specific label. / "
                    f"Запись с именем '{label}' уже существует. / "
                    f"Запис з назвою '{label}' вже існує.",
                    code="DUPLICATE_LABEL",
                )

        return result


# ── Module-level singleton ────────────────────────────────────────
extended_validator = ExtendedPasswordEntryValidator()
"""Module-level singleton — ``from core.validators import extended_validator``."""

# ── Update __all__ ────────────────────────────────────────────────
__all__ += [
    "ExtendedValidationResult",
    "ValidationWarning",
    "ExtendedPasswordEntryValidator",
    "extended_validator",
    "estimate_entropy",
    "score_password",
    "check_duplicate_label",
    "validate_custom_fields",
    "validate_totp_secret",
    "check_url_homograph",
]
