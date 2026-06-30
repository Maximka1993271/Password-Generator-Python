"""
Tests for GUI module.
Тесты для GUI модуля.
Тести для GUI модуля.
"""
from __future__ import annotations
import os
import pytest
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock

from storage.database_migrations import SCHEMA_VERSION


class TestDBSchemaV3:
    """Test database schema v3 migration."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def teardown_method(self):
        """Clean up test environment."""
        import time
        if hasattr(self, 'db_path') and os.path.exists(self.db_path):
            try:
                time.sleep(0.1)
                os.remove(self.db_path)
            except (OSError, PermissionError):
                pass

    @patch('storage.database_migrations.get_db_path')
    def test_v3_migration(self, mock_get_db_path):
        """Test that v3 migration adds new columns."""
        mock_get_db_path.return_value = self.db_path
        
        # Create a fresh database with v2 schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create v2 schema (without new columns)
        cursor.execute("""
            CREATE TABLE passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                password TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT,
                notes TEXT
            )
        """)
        
        # Create schema_version table with version 2
        cursor.execute("""
            CREATE TABLE schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                applied_at TEXT NOT NULL,
                description TEXT
            )
        """)
        import datetime
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO schema_version (version, applied_at, description) VALUES (2, ?, 'Initial schema v2')",
            (now,)
        )
        conn.commit()
        conn.close()
        
        # Run migrations
        from storage.database_migrations import DatabaseMigration
        DatabaseMigration.migrate(self.db_path, SCHEMA_VERSION)
        
        # Check that new columns exist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        # v3 should add: url, username, email, favorite, category, sort_order
        assert "url" in columns
        assert "username" in columns
        assert "email" in columns
        assert "favorite" in columns
        assert "category" in columns
        assert "sort_order" in columns
        
        # Check schema version
        from storage.database_migrations import DatabaseMigration
        version = DatabaseMigration.get_current_schema_version(self.db_path)
        # Current version is 8 (not 3) because we have more migrations
        assert version == SCHEMA_VERSION

    @patch('storage.database_migrations.get_db_path')
    def test_v4_migration(self, mock_get_db_path):
        """Test that v4 migration adds custom_fields."""
        mock_get_db_path.return_value = self.db_path
        
        # Create a fresh database with v3 schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE passwords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                password TEXT NOT NULL,
                created TEXT NOT NULL,
                updated TEXT,
                notes TEXT,
                url TEXT,
                username TEXT,
                email TEXT,
                favorite INTEGER DEFAULT 0,
                category TEXT DEFAULT "",
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Run migrations
        from storage.database_migrations import DatabaseMigration
        DatabaseMigration.migrate(self.db_path, SCHEMA_VERSION)
        
        # Check that custom_fields column exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(passwords)")
        columns = [col[1] for col in cursor.fetchall()]
        conn.close()
        
        assert "custom_fields" in columns


class TestGUIWidgets:
    """Test GUI widgets."""

    def test_import_main_window(self):
        """Test that main window can be imported."""
        from gui.main_window import SecurePassPro
        assert SecurePassPro is not None

    def test_import_dialogs(self):
        """Test that dialogs can be imported."""
        from gui.dialogs import CTkMessageBox, CTkInputDialog
        assert CTkMessageBox is not None
        assert CTkInputDialog is not None

    def test_import_widgets(self):
        """Test that widgets can be imported."""
        from gui.widgets import CustomButton, CustomCheckBox, CustomEntry
        assert CustomButton is not None
        assert CustomCheckBox is not None
        assert CustomEntry is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
