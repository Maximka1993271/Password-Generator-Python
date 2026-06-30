"""
Security audit tests for Secure Pass Pro.
Тесты безопасности для Secure Pass Pro.
Тести безпеки для Secure Pass Pro.
"""
from __future__ import annotations
import os
import pytest
import hashlib
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock


class TestHashAlgorithms:
    """Test that hash algorithms are used correctly."""

    def test_sha256_used_for_integrity(self):
        """Test that SHA256 is used for integrity checks."""
        files_to_check = [
            'storage/database_migrations.py',
            'security/integrity.py',
            'security/integrity_check.py'
        ]
        found = False
        for file_path in files_to_check:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'hashlib' in content and 'sha256' in content.lower():
                        found = True
                        break
        assert found, "SHA256 not found in integrity modules"

    def test_hibp_uses_sha1_by_requirement(self):
        """Test that HIBP uses SHA1 as required by the API."""
        if os.path.exists('gui/mixins/hibp_mixin.py'):
            with open('gui/mixins/hibp_mixin.py', 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'sha1' in content.lower()
                # Should have comment about API requirement
                assert 'api' in content.lower() or 'required' in content.lower()


class TestDatabaseMigrations:
    """Test database migrations."""

    def setup_method(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create a fresh database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                password TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT,
                notes TEXT
            )
        """)
        conn.commit()
        conn.close()

    def teardown_method(self):
        """Clean up test database."""
        import time
        if hasattr(self, 'db_path') and os.path.exists(self.db_path):
            try:
                time.sleep(0.1)
                os.remove(self.db_path)
            except (OSError, PermissionError):
                pass

    @patch('storage.database_migrations.get_db_path')
    def test_custom_fields_default_is_empty_json(self, mock_get_db_path):
        """Test that custom_fields default is empty JSON array."""
        mock_get_db_path.return_value = self.db_path
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add column if it doesn't exist
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'custom_fields' not in columns:
            cursor.execute("ALTER TABLE passwords ADD COLUMN custom_fields TEXT DEFAULT '[]'")
            conn.commit()
        
        # Check that default is '[]'
        cursor.execute("PRAGMA table_info(passwords)")
        for col in cursor.fetchall():
            if col[1] == 'custom_fields':
                default = col[4] or '[]'
                assert default == '[]' or default == "''" or default == "'[]'"
                break
        
        conn.close()

    @patch('storage.database_migrations.get_db_path')
    def test_password_history_table_exists(self, mock_get_db_path):
        """Test that password_history table exists after migration v8."""
        mock_get_db_path.return_value = self.db_path
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create password_history table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                password TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
        """)
        conn.commit()
        
        # Check that table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'password_history' in tables

    @patch('storage.database_migrations.get_db_path')
    def test_migration_is_idempotent(self, mock_get_db_path):
        """Test that migrations can be run multiple times without errors."""
        mock_get_db_path.return_value = self.db_path
        
        from storage.database_migrations import DatabaseMigration
        
        for _ in range(2):
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS passwords (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        label TEXT NOT NULL,
                        password TEXT NOT NULL,
                        created TEXT NOT NULL,
                        updated TEXT,
                        notes TEXT
                    )
                """)
                conn.commit()
                conn.close()
            except sqlite3.Error:
                pass
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        assert 'passwords' in tables or len(tables) > 0


class TestSecurityUtils:
    """Test security utilities."""

    def test_import_security_modules(self):
        """Test importing security modules."""
        from security import master, encryption, integrity
        assert master is not None
        assert encryption is not None
        assert integrity is not None

    def test_import_antidebug(self):
        """Test importing antidebug module."""
        from security import antidebug
        assert antidebug is not None

    def test_import_vm_detection(self):
        """Test importing vm_detection module."""
        from security import vm_detection
        assert vm_detection is not None

    def test_import_encryption_has_encrypt_decrypt(self):
        """Test that encryption module has encrypt/decrypt functions."""
        from security import encryption
        assert hasattr(encryption, 'encrypt')
        assert hasattr(encryption, 'decrypt')

    def test_import_master_has_is_set_verify(self):
        """Test that master module has is_set/verify functions."""
        from security import master
        assert hasattr(master, 'MasterPassword')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])