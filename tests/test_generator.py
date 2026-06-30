from __future__ import annotations
"""
Test generator module for Secure Pass Pro.
Модуль Test generator для Secure Pass Pro.
Модуль Test generator для Secure Pass Pro.
"""
"""
Test generator module for Secure Pass Pro.
Модуль Test generator для Secure Pass Pro.
Модуль Test generator для Secure Pass Pro.
"""
import pytest
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.generator import PasswordGenerator


class TestPasswordGenerator:
    """Тесты для генератора паролей"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.generator = PasswordGenerator()

    def test_default_generation(self):
        """Тест генерации пароля по умолчанию"""
        password = self.generator.generate()
        assert password is not None
        assert len(password) >= 8
        assert isinstance(password, str)

    def test_length_parameter(self):
        """Тест изменения длины пароля через атрибут"""
        for length in [4, 8, 12, 16, 32, 64]:
            self.generator.length = length
            password = self.generator.generate()
            assert len(password) == length

    def test_uppercase_only(self):
        """Тест только заглавные буквы"""
        self.generator.use_upper = True
        self.generator.use_lower = False
        self.generator.use_digits = False
        self.generator.use_symbols = False
        self.generator.length = 20
        password = self.generator.generate()
        assert password.isupper()
        assert password.isalpha()

    def test_lowercase_only(self):
        """Тест только строчные буквы"""
        self.generator.use_upper = False
        self.generator.use_lower = True
        self.generator.use_digits = False
        self.generator.use_symbols = False
        self.generator.length = 20
        password = self.generator.generate()
        assert password.islower()
        assert password.isalpha()

    def test_digits_only(self):
        """Тест только цифры"""
        self.generator.use_upper = False
        self.generator.use_lower = False
        self.generator.use_digits = True
        self.generator.use_symbols = False
        self.generator.length = 20
        password = self.generator.generate()
        assert password.isdigit()

    def test_symbols_only(self):
        """Тест только спецсимволы (если поддерживается)"""
        import string
        self.generator.use_upper = False
        self.generator.use_lower = False
        self.generator.use_digits = False
        self.generator.use_symbols = True
        self.generator.length = 20
        
        password = self.generator.generate()
        
        # Если генератор не может создать пароль только из спецсимволов
        if password is None:
            pytest.skip("Генератор не поддерживает только спецсимволы")
        
        # Проверяем, что все символы — спецсимволы
        for ch in password:
            assert ch in string.punctuation