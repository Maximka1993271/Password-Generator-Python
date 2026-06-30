#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for import module (JSON, CSV, KeePass XML, Bitwarden, 1Password)
Тесты для модуля импорта (JSON, CSV, KeePass XML, Bitwarden, 1Password)
Тести для модуля імпорту (JSON, CSV, KeePass XML, Bitwarden, 1Password)

FIXED: Updated imports to use utils.importer
"""
from __future__ import annotations

import os
import json
import csv
import tempfile
import pytest
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

from utils.importer import (
    PasswordImporter,
    import_from_json,
    import_from_csv,
    import_from_keepass_xml,
    import_from_bitwarden_json,
    import_from_1password_csv,
    import_from_1pux,
    PasswordImportError,
    InvalidFileFormatError,
    MalformedFileError,
    FileTooLargeError,
    UnsupportedEncodingError,
    sanitize_password,
    sanitize_label,
    detect_encoding,
    detect_csv_delimiter,
    find_password_column,
    find_label_column,
    is_duplicate_password,
    safe_xml_parse,
)


class TestImportBase:
    """Test import base functions / Тест базовых функций импорта / Тест базових функцій імпорту"""

    def test_sanitize_password(self):
        """Test password sanitization / Тест санитизации пароля / Тест санітизації пароля"""
        # Normal password
        assert sanitize_password("P@ssw0rd!") == "P@ssw0rd!"
        
        # Password with control characters
        assert sanitize_password("P@ss\x00w0rd!") == "P@ssw0rd!"
        
        # Empty password
        assert sanitize_password("") == ""
        
        # Too long password
        long_pwd = "a" * 1500
        assert len(sanitize_password(long_pwd)) <= 1000
    
    def test_sanitize_label(self):
        """Test label sanitization / Тест санитизации метки / Тест санітизації мітки"""
        # Normal label
        assert sanitize_label("My Password") == "My Password"
        
        # Label with control characters
        assert sanitize_label("My\x00Password") == "MyPassword"
        
        # Empty label
        assert sanitize_label("") == "Imported"
        
        # Too long label
        long_label = "a" * 300
        assert len(sanitize_label(long_label)) <= 200
    
    def test_detect_encoding(self):
        """Test encoding detection / Тест определения кодировки / Тест визначення кодування"""
        # Create a UTF-8 file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write("Тестовые данные".encode('utf-8'))
            temp_path = f.name
        
        try:
            encoding, content = detect_encoding(temp_path)
            assert encoding in ['utf-8', 'utf-8-sig']
            assert "Тестовые данные" in content
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_detect_csv_delimiter(self):
        """Test CSV delimiter detection / Тест определения разделителя CSV / Тест визначення роздільника CSV"""
        content_comma = "col1,col2,col3\n1,2,3"
        assert detect_csv_delimiter(content_comma) == ","
        
        content_semicolon = "col1;col2;col3\n1;2;3"
        assert detect_csv_delimiter(content_semicolon) == ";"
        
        content_tab = "col1\tcol2\tcol3\n1\t2\t3"
        assert detect_csv_delimiter(content_tab) == "\t"
    
    def test_find_password_column(self):
        """Test password column detection / Тест определения колонки пароля / Тест визначення колонки пароля"""
        fieldnames = ["id", "label", "password", "notes"]
        assert find_password_column(fieldnames) == "password"
        
        fieldnames = ["id", "label", "pwd", "notes"]
        assert find_password_column(fieldnames) == "pwd"
        
        fieldnames = ["id", "label", "пароль", "notes"]
        assert find_password_column(fieldnames) == "пароль"
        
        fieldnames = ["id", "label", "notes"]
        assert find_password_column(fieldnames) is None
    
    def test_find_label_column(self):
        """Test label column detection / Тест определения колонки метки / Тест визначення колонки мітки"""
        fieldnames = ["id", "label", "password", "notes"]
        assert find_label_column(fieldnames) == "label"
        
        fieldnames = ["id", "name", "password", "notes"]
        assert find_label_column(fieldnames) == "name"
        
        fieldnames = ["id", "title", "password", "notes"]
        assert find_label_column(fieldnames) == "title"
        
        fieldnames = ["id", "password", "notes"]
        assert find_label_column(fieldnames) == "id"  # First column as fallback
    
    def test_is_duplicate_password(self):
        """Test duplicate detection / Тест обнаружения дубликатов / Тест виявлення дублікатів"""
        existing = {"password1", "password2", "password3"}
        
        assert is_duplicate_password("password1", existing) is True
        assert is_duplicate_password("password4", existing) is False
    
    def test_safe_xml_parse(self):
        """Test safe XML parsing / Тест безопасного парсинга XML / Тест безпечного парсингу XML"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <Entry>
                <Title>Test Entry</Title>
                <Password>TestP@ss</Password>
            </Entry>
        </root>"""
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as f:
            f.write(xml_content.encode('utf-8'))
            temp_path = f.name
        
        try:
            root = safe_xml_parse(temp_path)
            assert root is not None
            assert root.tag == "root"
            entries = root.findall('.//Entry')
            assert len(entries) == 1
            assert entries[0].find('.//Title').text == "Test Entry"
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


# ... остальные тесты те же самые, только импорты изменены с utils.import_passwords на utils.importer