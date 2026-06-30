"""
Secure memory management - SecurePassword class
Безопасная работа с чувствительными данными - Класс SecurePassword
Безпечна робота з чутливими даними - Клас SecurePassword

FIXED #51: Added copy/pickle protection for SecurePassword
FIXED #M5: Added __getitem__ method (inherited from SecureBytes)

Исправлено #51: Добавлена защита от копирования/pickle для SecurePassword
Исправлено #M5: Добавлен метод __getitem__ (унаследован от SecureBytes)

Виправлено #51: Додано захист від копіювання/pickle для SecurePassword
Виправлено #M5: Додано метод __getitem__ (успадковано від SecureBytes)
"""
from __future__ import annotations

import time
import secrets
from typing import Optional, Union, Any
from utils.logger import get_logger
from utils.secure_bytes import SecureBytes

logger = get_logger("secure_memory")


class SecurePassword(SecureBytes):
    """
    Specialized class for secure password storage with copy/pickle protection.

    Специализированный класс для безопасного хранения паролей с защитой от копирования/pickle.
    Спеціалізований клас для безпечного зберігання паролів із захистом від копіювання/pickle.

    FIXED #M5: Added __getitem__ method (inherited from SecureBytes)
    Исправлено #M5: Добавлен метод __getitem__ (унаследован от SecureBytes)
    Виправлено #M5: Додано метод __getitem__ (успадковано від SecureBytes)
    """

    __slots__ = ('_copy_count', '_max_access_warning', '_access_times')

    def __init__(self, password: Optional[Union[str, bytes, bytearray]] = None) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        super().__init__(password)
        self._copy_count = 0
        self._max_access_warning = 100
        self._access_times: list = []

    def get_string(self) -> Optional[str]:
        """Return password string (with access tracking)
        Вернуть строку пароля (с отслеживанием доступа)
        Повернути рядок пароля (з відстеженням доступу)"""
        self._copy_count += 1
        self._access_times.append(time.time())

        # Clean old access times
        try:
            current_time = time.time()
            self._access_times = [t for t in self._access_times if current_time - t < 60]
        except (ValueError, TypeError, RuntimeError) as e:
            logger.debug(f"Access times cleanup error / Ошибка очистки времени доступа / Помилка очищення часу доступу: {e}")

        # Warning on frequent access
        if self._copy_count > self._max_access_warning:
            logger.warning(f"SecurePassword accessed {self._copy_count} times / SecurePassword был accessed {self._copy_count} раз / SecurePassword було accessed {self._copy_count} разів")

        return super().get_string()

    def verify(self, other: Union[str, bytes, 'SecurePassword']) -> bool:
        """Secure password comparison (resistant to timing attacks)
        Безопасное сравнение паролей (устойчивое к атакам по времени)
        Безпечне порівняння паролів (стійке до атак за часом)"""
        if self._data is None or self._cleared:
            return False

        other_data = None
        try:
            if isinstance(other, SecurePassword):
                other_data = other._data
            elif isinstance(other, str):
                other_data = bytearray(other.encode('utf-8'))
            elif isinstance(other, bytes):
                other_data = bytearray(other)
            else:
                raise TypeError(f"Unsupported comparison type: {type(other).__name__} / Неподдерживаемый тип сравнения: {type(other).__name__} / Непідтримуваний тип порівняння: {type(other).__name__}")
        except (TypeError, ValueError, UnicodeEncodeError) as e:
            logger.debug(f"Comparison type error / Ошибка типа сравнения / Помилка типу порівняння: {e}")
            return False

        if other_data is None:
            return False

        if len(self._data) != len(other_data):
            if other_data is not other._data:
                try:
                    from utils.secure_memory_core import secure_zero_memory
                    secure_zero_memory(other_data)
                except (TypeError, ValueError, AttributeError):
                    pass
            return False

        try:
            result = secrets.compare_digest(self._data, other_data)
        except (TypeError, ValueError) as e:
            logger.debug(f"Compare digest error / Ошибка сравнения дайджестов / Помилка порівняння дайджестів: {e}")
            result = False
        finally:
            if other_data is not getattr(other, '_data', None):
                try:
                    from utils.secure_memory_core import secure_zero_memory
                    secure_zero_memory(other_data)
                except (TypeError, ValueError, AttributeError):
                    pass

        return result

    def get_access_count(self) -> int:
        """Return number of accesses to the password
        Вернуть количество обращений к паролю
        Повернути кількість звернень до пароля"""
        return self._copy_count

    def get_access_frequency(self) -> float:
        """Get access frequency (accesses per minute)
        Получить частоту доступа (обращений в минуту)
        Отримати частоту доступу (звернень за хвилину)"""
        if not self._access_times:
            return 0.0
        try:
            oldest = min(self._access_times)
            newest = max(self._access_times)
            duration = newest - oldest
            if duration <= 0:
                return float(self._copy_count)
            return self._copy_count / (duration / 60.0)
        except (ValueError, TypeError, RuntimeError) as e:
            logger.debug(f"Frequency calculation error / Ошибка расчёта частоты / Помилка розрахунку частоти: {e}")
            return float(self._copy_count)

    def clear(self) -> None:
        """Clear password from memory / Очистить пароль из памяти / Очистити пароль з пам'яті"""
        super().clear()
        self._copy_count = 0
        self._access_times = []

    # FIXED #51: Override copy/pickle protection with same security measures
    # SECURITY: pickle serialization is explicitly blocked.
    # Sensitive data must never be serialized to untrusted storage.
    def __reduce__(self) -> None:
        """
        Handle reduce.
        Обработать reduce.
        Обробити reduce.
        """
        raise TypeError("SecurePassword cannot be pickled for security reasons / SecurePassword не может быть сериализован по соображениям безопасности / SecurePassword не може бути серіалізований з міркувань безпеки")

    def __reduce_ex__(self, protocol) -> None:
        """
        Handle reduce ex.
        Обработать reduce ex.
        Обробити reduce ex.
        """
        raise TypeError("SecurePassword cannot be pickled for security reasons / SecurePassword не может быть сериализован по соображениям безопасности / SecurePassword не може бути серіалізований з міркувань безпеки")

    def __copy__(self) -> None:
        """
        Handle copy.
        Обработать copy.
        Обробити copy.
        """
        raise TypeError("SecurePassword cannot be copied for security reasons / SecurePassword не может быть скопирован по соображениям безопасности / SecurePassword не може бути скопійований з міркувань безпеки")

    def __deepcopy__(self, memo) -> None:
        """
        Handle deepcopy.
        Обработать deepcopy.
        Обробити deepcopy.
        """
        raise TypeError("SecurePassword cannot be copied for security reasons / SecurePassword не может быть скопирован по соображениям безопасности / SecurePassword не може бути скопійований з міркувань безпеки")

    # FIXED #M5: __getitem__ is inherited from SecureBytes, but we add a string representation
    def __str__(self) -> str:
        """
        Return a human-readable string representation.
        Возвращает строковое представление для пользователей.
        Повертає рядкове представлення для користувачів.
        """
        return "<SecurePassword>"

    def __repr__(self) -> str:
        """
        Return a developer-friendly string representation.
        Возвращает строковое представление для разработчиков.
        Повертає рядкове представлення для розробників.
        """
        return f"<SecurePassword length={len(self._data) if self._data else 0}>"
