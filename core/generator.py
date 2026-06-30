"""
PasswordGenerator — cryptographically-secure password/passphrase generation.
PasswordGenerator — криптографически безопасная генерация паролей/парольных фраз.
PasswordGenerator — криптографічно безпечна генерація паролів/парольних фраз.

Note: SecureString and SecurePasswordContext have been moved to
      core.secure_context to keep this file focused on generation logic.
"""
from __future__ import annotations
import json
import math
import os
import secrets
import string
from typing import Any, Dict, List, Optional, Union

from core.secure_context import (        # noqa: F401
    SecureString, SecurePasswordContext,
    _secure_zero_bytearray, _clear_string, secure_compare,
)
# Also re-import SecurePassword from the same place it originates
from utils.secure_memory import SecurePassword  # noqa: F401
class PasswordGenerator:
    """Cryptographically secure password generator with Diceware support

    Криптографически безопасный генератор паролей с поддержкой Diceware
    Криптографічно безпечний генератор паролів з підтримкою Diceware
    """

    DEFAULT_SPECIAL: str = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
    AMBIGUOUS_CHARS: str = "il1Lo0O"
    UNAMBIGUOUS_CHARS: str = "{}[]()/\\'\"`~,;:.<>"

    # FIXED #M1: Full EFF Diceware word list - now loaded from file
    # Полный список слов Diceware EFF - теперь загружается из файла
    # Повний список слів Diceware EFF - тепер завантажується з файлу
    @classmethod
    def _get_diceware_file_paths(cls) -> List[str]:
        """Get possible paths for diceware wordlist file

        Получить возможные пути к файлу со словами Diceware
        Отримати можливі шляхи до файлу зі словами Diceware
        """
        base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return [
            os.path.join(base_dir, "resources", "diceware_words.json"),
            os.path.join(base_dir, "data", "diceware_words.json"),
            os.path.join(base_dir, "diceware_words.json"),
            os.path.join(os.path.dirname(__file__), "diceware_words.json"),
            os.path.join(os.getcwd(), "resources", "diceware_words.json"),
            os.path.join(os.getcwd(), "diceware_words.json"),
        ]

    @classmethod
    def _create_default_wordlist(cls) -> List[str]:
        """Create a basic default wordlist when no file is found.

        Создает базовый стандартный список слов, когда файл не найден.
        Створює базовий стандартний список слів, коли файл не знайдено.
        """
        return [
            "abacus", "abdicate", "abduct", "abhor", "abide", "abject", "abjure", "ablate", "ablaze",
            "abnegate", "abode", "abort", "abound", "abrade", "abridge", "abrupt", "absent", "absorb",
            "absurd", "abut", "abysmal", "accent", "accept", "access", "accord", "accost", "accrete",
            "accrue", "accuse", "acerbic", "acetate", "achieve", "acidic", "acme", "acorn", "acquire",
            "acrid", "acumen", "acute", "adage", "adapt", "addict", "addle", "address", "adhere",
            "adieu", "adjacent", "adjure", "adjust", "adman", "admire", "admit", "adobe", "adopt",
            "adore", "adorn", "adrift", "adroit", "adult", "advent", "adverb", "adverse", "advise",
            "advocate", "aegis", "aerate", "aerial", "aerobic", "affable", "affect", "affine", "affirm",
            "affix", "afflict", "affluent", "afford", "affront", "afield", "afire", "afloat", "afoot",
            "afraid", "afresh", "after", "agape", "agate", "agave", "agency", "agenda", "agent",
        ]

    @classmethod
    def _load_diceware_wordlist(cls) -> List[str]:
        """Load full Diceware wordlist from JSON file.

        Загружает полный список слов Diceware из JSON файла.
        Завантажує повний список слів Diceware з JSON файлу.
        """
        possible_paths: List[str] = cls._get_diceware_file_paths()

        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data: Union[List[str], Dict[str, Any]] = json.load(f)

                        if isinstance(data, list):
                            wordlist: List[str] = data
                        elif isinstance(data, dict) and 'words' in data:
                            wordlist = cast(List[str], data['words'])
                        elif isinstance(data, dict) and 'diceware' in data:
                            wordlist = cast(List[str], data['diceware'])
                        else:
                            continue

                        if len(wordlist) >= 7776:
                            logger.info(f"Loaded {len(wordlist)} Diceware words from {path} / Загружено {len(wordlist)} слов Diceware из {path} / Завантажено {len(wordlist)} слів Diceware з {path}")
                            return wordlist
                        elif len(wordlist) >= 1000:
                            logger.info(f"Using partial wordlist from {path} ({len(wordlist)} words) / Используется частичный список из {path} ({len(wordlist)} слов) / Використовується частковий список з {path} ({len(wordlist)} слів)")
                            return wordlist
            except (OSError, IOError, json.JSONDecodeError) as e:
                logger.debug(f"Failed to load diceware words from {path}: {e}")
                continue

        logger.warning("Full Diceware wordlist not found! Using fallback wordlist. / Полный список Diceware не найден! Используется резервный список. / Повний список Diceware не знайдено! Використовується резервний список.")
        return cls._create_default_wordlist()

    def __init__(self) -> None:
        # Main settings / Основные настройки / Основні налаштування
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.use_upper: bool = True
        self.use_lower: bool = True
        self.use_digits: bool = True
        self.use_special: bool = False
        self.exclude_ambiguous: bool = False
        self.exclude_unambiguous: bool = False
        self.min_each: bool = False
        self.no_repeat: bool = False
        self.length: int = 20

        # Diceware settings / Настройки Diceware / Налаштування Diceware
        self.use_diceware: bool = False
        self.diceware_word_count: int = 4
        self.diceware_separator: str = "-"
        self.diceware_capitalize: bool = False
        self.diceware_add_number: bool = False

        self._diceware_words: Optional[List[str]] = None
        self._wordlist_size: int = 0
        self._secure_buffer: Optional[SecurePassword] = None

    @property
    def DICEWARE_WORDS(self) -> List[str]:
        """Lazy-load the Diceware wordlist.

        Ленивая загрузка списка слов Diceware.
        Ліниве завантаження списку слів Diceware.
        """
        if self._diceware_words is None:
            self._diceware_words = self._load_diceware_wordlist()
            self._wordlist_size = len(self._diceware_words)
        return self._diceware_words

    # ── Character pool construction ───────────────────────────
    # The pool is the universe of characters the generator may use.
    # Combining multiple character classes multiplies the search space:
#   lower(26) + upper(26) + digit(10) + symbol(32) = 94 chars
#   → 94^16  ≈ 2^105 possible 16-char passwords (well above 80-bit target)
    def _get_pool(self) -> str:
        """Get character pool based on current settings

        Получить пул символов на основе текущих настроек
        Отримати пул символів на основі поточних налаштувань
        """
        pool: str = ""
        if self.use_lower:
            pool += string.ascii_lowercase
        if self.use_upper:
            pool += string.ascii_uppercase
        if self.use_digits:
            pool += string.digits
        if self.use_special:
            pool += self.DEFAULT_SPECIAL

        if self.exclude_ambiguous:
            for ch in self.AMBIGUOUS_CHARS:
                pool = pool.replace(ch, '')

        if self.exclude_unambiguous:
            for ch in self.UNAMBIGUOUS_CHARS:
                pool = pool.replace(ch, '')

        return pool

    def _get_categories(self) -> List[str]:
        """Get list of character categories for 'min each' mode

        Получить список категорий символов для режима 'минимум из каждой категории'
        Отримати список категорій символів для режиму 'мінімум з кожної категорії'
        """
        categories: List[str] = []
        if self.use_lower:
            categories.append(string.ascii_lowercase)
        if self.use_upper:
            categories.append(string.ascii_uppercase)
        if self.use_digits:
            categories.append(string.digits)
        if self.use_special:
            categories.append(self.DEFAULT_SPECIAL)

        if self.exclude_ambiguous:
            categories = [''.join(c for c in cat if c not in self.AMBIGUOUS_CHARS) for cat in categories]
        if self.exclude_unambiguous:
            categories = [''.join(c for c in cat if c not in self.UNAMBIGUOUS_CHARS) for cat in categories]

        return [cat for cat in categories if cat]

    def _fix_no_repeats(self, chars: List[str], pool: str) -> Optional[bytearray]:
        """Ensure no consecutive repeated characters, returns bytearray

        Гарантирует отсутствие повторяющихся символов подряд, возвращает bytearray
        Гарантує відсутність повторюваних символів підряд, повертає bytearray
        """
        result: List[str] = list(chars)
        unique_pool: List[str] = list(set(pool))
        max_attempts: int = 300

        if len(pool) < 2 and len(chars) > 1:
            logger.debug("Pool too small for no_repeat mode - disabling / Пул слишком мал для режима no_repeat - отключение / Пул занадто малий для режиму no_repeat - вимкнення")
            return None

        def _secure_shuffle(lst: List[str]) -> None:
            for i in range(len(lst) - 1, 0, -1):
                j: int = secrets.randbelow(i + 1)
                lst[i], lst[j] = lst[j], lst[i]

        for _ in range(max_attempts):
            _secure_shuffle(result)
            has_repeat: bool = any(result[i] == result[i + 1] for i in range(len(result) - 1))
            if not has_repeat:
                return bytearray("".join(result), 'utf-8')

        result = list(chars)
        _secure_shuffle(result)
        for attempt in range(max_attempts):
            fixed: bool = False
            for i in range(len(result) - 1):
                if result[i] == result[i + 1]:
                    candidates: List[str] = [c for c in unique_pool if c != result[i] and (i == 0 or c != result[i - 1])]
                    if candidates:
                        result[i + 1] = secrets.choice(candidates)
                        fixed = True
            if not fixed:
                break
            if not any(result[i] == result[i + 1] for i in range(len(result) - 1)):
                return bytearray("".join(result), 'utf-8')
        return None

    def _generate_diceware_secure(self) -> SecurePassword:
        """Generate Diceware passphrase as SecurePassword

        Генерирует Diceware парольную фразу как SecurePassword
        Генерує Diceware парольну фразу як SecurePassword
        """
        words: List[str] = []
        for _ in range(self.diceware_word_count):
            word: str = secrets.choice(self.DICEWARE_WORDS)
            if self.diceware_capitalize:
                word = word.capitalize()
            words.append(word)

        passphrase: str = self.diceware_separator.join(words)

        if self.diceware_add_number:
            number: str = str(secrets.randbelow(100))
            passphrase += self.diceware_separator + number
            _clear_string(number)

        result: SecurePassword = SecurePassword(passphrase)
        _clear_string(passphrase)
        for word in words:
            _clear_string(word)

        return result

    def _get_min_required_length(self) -> int:
        """Calculate minimum required length based on active categories

        Вычисляет минимальную длину на основе активных категорий
        Обчислює мінімальну довжину на основі активних категорій
        """
        count: int = 0
        if self.use_upper:
            count += 1
        if self.use_lower:
            count += 1
        if self.use_digits:
            count += 1
        if self.use_special:
            count += 1

        if self.min_each and count > 0:
            return max(1, count)
        return 1

    def _generate_secure(self) -> Optional[SecurePassword]:
        """Generate a password as SecurePassword based on current settings.

        Генерирует пароль как SecurePassword на основе текущих настроек.
        Генерує пароль як SecurePassword на основі поточних налаштувань.
        """
        if self.use_diceware:
            return self._generate_diceware_secure()

        try:
            length: int = int(self.length)
        except (TypeError, ValueError) as e:
            logger.debug(f"Length conversion error: {e}")
            return None
        if length <= 0:
            return None

        pool: str = self._get_pool()
        if not pool:
            return None

        min_length: int = self._get_min_required_length()
        if length < min_length:
            return None

        if self.min_each:
            categories: List[str] = self._get_categories()
            if not categories or len(categories) < 1:
                categories = [pool]
            if length < len(categories):
                return None

            password_chars: List[str] = []
            for cat in categories:
                if cat:
                    password_chars.append(secrets.choice(cat))

            remaining: int = length - len(password_chars)
            if remaining > 0 and pool:
                for _ in range(remaining):
                    password_chars.append(secrets.choice(pool))

            for i in range(len(password_chars) - 1, 0, -1):
                j: int = secrets.randbelow(i + 1)
                password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

            result_str: str = "".join(password_chars)
            result: SecurePassword = SecurePassword(result_str)
            _clear_string(result_str)
        else:
            if not pool:
                return None
            result_str = ''.join(secrets.choice(pool) for _ in range(length))
            result = SecurePassword(result_str)
            _clear_string(result_str)

        if self.no_repeat:
            fixed: Optional[bytearray] = self._fix_no_repeats(list(result.get_string()), pool)
            if not fixed:
                return None
            result.clear()
            result = SecurePassword(fixed.decode('utf-8'))
            _secure_zero_bytearray(fixed)

        return result

    def generate(self) -> Optional[str]:
        """
        Generate a password based on current settings.
        CAUTION: Returns a regular Python string.

        Генерирует пароль на основе текущих настроек.
        ВНИМАНИЕ: Возвращает обычную строку Python.

        Генерує пароль на основі поточних налаштувань.
        УВАГА: Повертає звичайний рядок Python.
        """
        secure_pwd: Optional[SecurePassword] = self._generate_secure()
        if secure_pwd is None:
            return None

        result: str = secure_pwd.get_string()
        secure_pwd.clear()
        return result

    def generate_secure(self) -> Optional[SecurePassword]:
        """Generate a password as SecurePassword.

        Генерирует пароль как SecurePassword.
        Генерує пароль як SecurePassword.
        """
        return self._generate_secure()

    def filter_ambiguous_chars(self, password: str) -> str:
        """Filter out ambiguous characters (0, O, 1, l, I)

        Фильтрует неоднозначные символы (0, O, 1, l, I)
        Фільтрує неоднозначні символи (0, O, 1, l, I)
        """
        if not hasattr(self, '_ambig_trans_table'):
            ambig_map: Dict[str, str] = {
                '0': 'O',
                'O': 'Q',
                '1': '!',
                'l': 'L',
                'I': '!',
            }
            self._ambig_trans_table = str.maketrans(ambig_map)

        return password.translate(self._ambig_trans_table)

    def get_entropy_bits(self, password: str) -> float:
        """Calculate entropy bits of a password

        Вычисляет энтропию пароля в битах
        Обчислює ентропію пароля в бітах
        """
        if not password:
            return 0.0

        pool_size: int = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in string.punctuation for c in password):
            pool_size += 32

        if pool_size == 0:
            return 0.0

        return len(password) * math.log2(pool_size)

    def clear_sensitive_data(self) -> None:
        """Clear all sensitive data from buffers

        Очищает все чувствительные данные из буферов
        Очищує всі чутливі дані з буферів
        """
        if self._secure_buffer:
            self._secure_buffer.clear()
            self._secure_buffer = None


class StrengthCalculator:
    """
    Calculate password strength metrics

    Вычисляет метрики стойкости пароля
    Обчислює метрики стійкості пароля
    """

    @staticmethod
    def calculate(password: str) -> Dict[str, Any]:
        """
        Calculate password strength
        Returns dict with: pool_size, combinations, entropy_bits, strength_level, crack_time_label

        Вычисляет стойкость пароля
        Возвращает словарь с: pool_size, combinations, entropy_bits, strength_level, crack_time_label

        Обчислює стійкість пароля
        Повертає словник з: pool_size, combinations, entropy_bits, strength_level, crack_time_label
        """
        if not password:
            return {
                'pool_size': 0,
                'combinations': 0,
                'entropy_bits': 0.0,
                'strength_level': 'empty',
                'crack_time_label': ''
            }

        pool_size: int = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in string.punctuation for c in password):
            pool_size += 32

        if pool_size == 0:
            pool_size = 1

        entropy_bits: float = len(password) * math.log2(pool_size) if pool_size > 0 else 0.0
        combinations: float = pool_size ** len(password) if pool_size > 0 else 0

        if entropy_bits < 40:
            strength_level: str = 'weak'
            crack_time_label: str = 'time_sec'
        elif entropy_bits < 60:
            strength_level = 'medium'
            crack_time_label = 'time_day'
        elif entropy_bits < 80:
            strength_level = 'medium'
            crack_time_label = 'time_year'
        else:
            strength_level = 'strong'
            crack_time_label = 'time_cent'

        return {
            'pool_size': pool_size,
            'combinations': f"{combinations:.1e}" if combinations > 0 else "0",
            'entropy_bits': entropy_bits,
            'strength_level': strength_level,
            'crack_time_label': crack_time_label
        }

    @staticmethod
    def calculate_entropy_bits(password: str) -> float:
        """Calculate entropy bits only

        Вычисляет только энтропию в битах
        Обчислює лише ентропію в бітах
        """
        if not password:
            return 0.0

        pool_size: int = 0
        if any(c.islower() for c in password):
            pool_size += 26
        if any(c.isupper() for c in password):
            pool_size += 26
        if any(c.isdigit() for c in password):
            pool_size += 10
        if any(c in string.punctuation for c in password):
            pool_size += 32

        if pool_size == 0:
            return 0.0

        return len(password) * math.log2(pool_size)


# ==================== ARGON2 HASHING METHODS / МЕТОДЫ ХЕШИРОВАНИЯ ARGON2 / МЕТОДИ ХЕШУВАННЯ ARGON2 ====================

def _hash_argon2(password: str) -> str:
    """Hash password using Argon2id

    Хеширует пароль с использованием Argon2id
    Хешує пароль з використанням Argon2id
    """
    if not _ARGON2_OK:
        raise RuntimeError("Argon2 is not available / Argon2 недоступен / Argon2 недоступний")
    try:
        _ph = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN
        )
        return _ph.hash(password)
    except (ValueError, TypeError, RuntimeError) as e:
        logger.error(f"Argon2 hash error / Ошибка хеширования Argon2 / Помилка хешування Argon2: {e}")
        raise RuntimeError(f"Failed to hash password / Ошибка хеширования пароля / Помилка хешування пароля: {e}")


def _verify_argon2(password: str, stored_hash: str) -> bool:
    """Verify password against Argon2id hash

    Проверяет пароль по хешу Argon2id
    Перевіряє пароль за хешем Argon2id
    """
    try:
        if not _ARGON2_OK:
            return False
        _ph = PasswordHasher(
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN
        )
        _ph.verify(stored_hash, password)
        if _ph.check_needs_rehash(stored_hash):
            logger.debug("Password hash needs rehash / Хеш пароля требует перехеширования / Хеш пароля потребує перехешування")
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError, TypeError, ValueError) as e:
        logger.debug(f"Argon2 verification failed / Ошибка верификации Argon2 / Помилка верифікації Argon2: {type(e).__name__}")
        return False


# ==================== EXPORTS (FIXED) / ЭКСПОРТЫ (ИСПРАВЛЕНО) / ЕКСПОРТИ (ВИПРАВЛЕНО) ====================
# FIXED: Added StrengthCalculator to __all__ for proper import
# Исправлено: Добавлен StrengthCalculator в __all__ для правильного импорта
# Виправлено: Додано StrengthCalculator в __all__ для правильного імпорту

__all__: List[str] = [
    'SecureString',
    'SecurePasswordContext',
    'PasswordGenerator',
    'StrengthCalculator',
    '_clear_string',
    'secure_compare',
]