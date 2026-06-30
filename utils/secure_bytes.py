"""
Secure memory management - SecureBytes class
Безопасная работа с чувствительными данными - Класс SecureBytes
Безпечна робота з чутливими даними - Клас SecureBytes

FIXED #51: Added copy/pickle protection for SecureBytes
FIXED #M5: Added __getitem__ method for SecureBytes

Исправлено #51: Добавлена защита от копирования/pickle для SecureBytes
Исправлено #M5: Добавлен метод __getitem__ для SecureBytes

Виправлено #51: Додано захист від копіювання/pickle для SecureBytes
Виправлено #M5: Додано метод __getitem__ для SecureBytes
"""
from __future__ import annotations

import time
import gc
from typing import Optional, Union
from utils.logger import get_logger
from utils.secure_memory_core import secure_zero_memory

logger = get_logger("secure_memory")

class SecureBytes:
    """
    Secure byte storage with automatic clearing and protection against copying/pickling.

    Безопасное хранилище байтов с автоматической очисткой и защитой от копирования/pickle.
    Безпечне сховище байтів з автоматичним очищенням та захистом від копіювання/pickle.

    FIXED #51: Added __reduce__ and __reduce_ex__ to prevent pickling
    FIXED #51: Added __copy__ and __deepcopy__ to prevent copying
    FIXED #M5: Added __getitem__ for subscript access

    Исправлено #51: Добавлены __reduce__ и __reduce_ex__ для предотвращения pickling
    Исправлено #51: Добавлены __copy__ и __deepcopy__ для предотвращения копирования
    Исправлено #M5: Добавлен __getitem__ для доступа по индексу

    Виправлено #51: Додано __reduce__ та __reduce_ex__ для запобігання pickling
    Виправлено #51: Додано __copy__ та __deepcopy__ для запобігання копіюванню
    Виправлено #M5: Додано __getitem__ для доступу за індексом
    """

    __slots__ = ('_data', '_cleared', '_creation_time')

    def __init__(self, data: Optional[Union[str, bytes, bytearray]] = None) -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self._data: Optional[bytearray] = None
        self._cleared = False
        self._creation_time = time.time()
        if data is not None:
            self.set(data)

    def set(self, data: Union[str, bytes, bytearray]) -> None:
        """Set data with clearing of previous data
        Установить данные с очисткой предыдущих данных
        Встановити дані з очищенням попередніх даних"""
        self.clear()
        try:
            if isinstance(data, str):
                self._data = bytearray(data.encode('utf-8'))
            elif isinstance(data, bytes):
                self._data = bytearray(data)
            elif isinstance(data, bytearray):
                self._data = bytearray(data)
            else:
                raise TypeError(f"Unsupported data type: {type(data).__name__} / Неподдерживаемый тип данных: {type(data).__name__} / Непідтримуваний тип даних: {type(data).__name__}")
            self._cleared = False
        except (UnicodeEncodeError, TypeError, MemoryError, ValueError) as e:
            logger.error(f"Failed to set secure data / Ошибка установки безопасных данных / Помилка встановлення безпечних даних: {e}")
            self._data = None
            self._cleared = True

    def get(self) -> Optional[bytes]:
        """Return a copy of the data (without clearing)
        Вернуть копию данных (без очистки)
        Повернути копію даних (без очищення)"""
        if self._data is None or self._cleared:
            return None
        try:
            return bytes(self._data)
        except (TypeError, MemoryError, ValueError) as e:
            logger.debug(f"Failed to get secure data / Ошибка получения безопасных данных / Помилка отримання безпечних даних: {e}")
            return None

    def get_string(self) -> Optional[str]:
        """Return a string (without clearing)
        Вернуть строку (без очистки)
        Повернути рядок (без очищення)"""
        data = self.get()
        if data is None:
            return None
        try:
            return data.decode('utf-8')
        except (UnicodeDecodeError, ValueError) as e:
            logger.debug(f"Failed to decode secure data / Ошибка декодирования безопасных данных / Помилка декодування безпечних даних: {e}")
            return None

    def clear(self) -> None:
        """Clear data from memory / Очистить данные из памяти / Очистити дані з пам'яті"""
        if self._data:
            try:
                secure_zero_memory(self._data)
                secure_zero_memory(self._data)
                self._data = None
            except (TypeError, ValueError, AttributeError, OSError) as e:
                logger.debug(f"SecureBytes clear error / Ошибка очистки SecureBytes / Помилка очищення SecureBytes: {e}")
                self._data = None
        self._cleared = True
        try:
            gc.collect()
        except (RuntimeError, ImportError) as e:
            logger.debug(f"GC collect error / Ошибка сборщика мусора / Помилка збирача сміття: {e}")

    def is_cleared(self) -> bool:
        """Check if data has been cleared / Проверить, очищены ли данные / Перевірити, чи очищено дані"""
        return self._cleared

    def get_age(self) -> float:
        """Get age of object in seconds / Получить возраст объекта в секундах / Отримати вік об'єкта в секундах"""
        return time.time() - self._creation_time

    # FIXED #51: Prevent pickling (security measure)
    # SECURITY: pickle serialization is explicitly blocked.
    # Sensitive data must never be serialized to untrusted storage.
    def __reduce__(self) -> None:
        """Prevent pickling - raises exception
        Предотвращает pickling - вызывает исключение
        Запобігає pickling - викликає виняток"""
        raise TypeError("SecureBytes cannot be pickled for security reasons / SecureBytes не может быть сериализован по соображениям безопасности / SecureBytes не може бути серіалізований з міркувань безпеки")

    def __reduce_ex__(self, protocol) -> None:
        """Prevent pickling - raises exception
        Предотвращает pickling - вызывает исключение
        Запобігає pickling - викликає виняток"""
        raise TypeError("SecureBytes cannot be pickled for security reasons / SecureBytes не может быть сериализован по соображениям безопасности / SecureBytes не може бути серіалізований з міркувань безпеки")

    # FIXED #51: Prevent copying (security measure)
    def __copy__(self) -> None:
        """Prevent shallow copy - raises exception
        Предотвращает поверхностное копирование - вызывает исключение
        Запобігає поверхневому копіюванню - викликає виняток"""
        raise TypeError("SecureBytes cannot be copied for security reasons / SecureBytes не может быть скопирован по соображениям безопасности / SecureBytes не може бути скопійований з міркувань безпеки")

    def __deepcopy__(self, memo) -> None:
        """Prevent deep copy - raises exception
        Предотвращает глубокое копирование - вызывает исключение
        Запобігає глибокому копіюванню - викликає виняток"""
        raise TypeError("SecureBytes cannot be copied for security reasons / SecureBytes не может быть скопирован по соображениям безопасности / SecureBytes не може бути скопійований з міркувань безпеки")

    # FIXED #M5: Add __getitem__ for subscript access
    def __getitem__(self, index: Union[int, slice]) -> Union[int, bytes]:
        """
        Get item at index or slice.
        Returns a single byte as int for integer index, or bytes for slice.

        Получить элемент по индексу или срез.
        Возвращает отдельный байт как int для целочисленного индекса, или bytes для среза.

        Отримати елемент за індексом або зрізом.
        Повертає окремий байт як int для цілочисельного індексу, або bytes для зрізу.
        """
        if self._data is None or self._cleared:
            raise ValueError("SecureBytes data has been cleared / Данные SecureBytes были очищены / Дані SecureBytes було очищено")

        if isinstance(index, int):
            if index < 0:
                index = len(self._data) + index
            if index < 0 or index >= len(self._data):
                raise IndexError("SecureBytes index out of range / Индекс SecureBytes вне диапазона / Індекс SecureBytes поза діапазоном")
            return self._data[index]
        elif isinstance(index, slice):
            return bytes(self._data[index])
        else:
            raise TypeError(f"SecureBytes indices must be integers or slices, not {type(index).__name__} / Индексы SecureBytes должны быть целыми числами или срезами, а не {type(index).__name__} / Індекси SecureBytes повинні бути цілими числами або зрізами, а не {type(index).__name__}")

    def __len__(self) -> int:
        """Return length of data (if not cleared)
        Вернуть длину данных (если не очищены)
        Повернути довжину даних (якщо не очищено)"""
        if self._data and not self._cleared:
            return len(self._data)
        return 0

    def __enter__(self) -> Any:
        """
        Enter the context manager.
        Войти в контекстный менеджер.
        Увійти в контекстний менеджер.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager and clean up.
        Выйти из контекстного менеджера и освободить ресурсы.
        Вийти з контекстного менеджера та звільнити ресурси.
        """
        self.clear()

    def __del__(self) -> None:
        """
        Handle del.
        Обработать del.
        Обробити del.
        """
        self.clear()
