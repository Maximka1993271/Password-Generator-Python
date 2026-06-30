"""
Tests for database diagnostics module.
Тесты для модуля диагностики базы данных.
Тести для модуля діагностики бази даних.
"""
from __future__ import annotations
import os
import pytest
import tempfile
import sqlite3
import time
from unittest.mock import patch, MagicMock

from storage.db_diagnostics import (
    DatabaseDiagnostics,
    run_database_diagnostics,
    quick_database_check,
    DIAGNOSTIC_OK,
    DIAGNOSTIC_WARNING,
    DIAGNOSTIC_ERROR,
    DIAGNOSTIC_CRITICAL
)


class TestDatabaseDiagnostics:
    """Test database diagnostics functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.db_diag = DatabaseDiagnostics()
        self.db_diag.clear_diagnostic_log()
        
        # Create test database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.test_db_path = self.temp_db.name
        
        # Create a simple test table
        conn = sqlite3.connect(self.test_db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test (name) VALUES ('test1'), ('test2')")
        conn.commit()
        conn.close()

    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            try:
                # Close any connections
                try:
                    conn = sqlite3.connect(self.test_db_path)
                    conn.close()
                except sqlite3.Error:
                    pass
                time.sleep(0.1)
                os.remove(self.test_db_path)
            except (OSError, PermissionError) as e:
                print(f"Cleanup warning: {e}")
                try:
                    time.sleep(0.5)
                    os.remove(self.test_db_path)
                except (OSError, sqlite3.Error):
                    pass

    @patch('storage.db_diagnostics.get_db_path')
    def test_diagnostics_ok(self, mock_get_db_path):
        """Test diagnostics on healthy database."""
        mock_get_db_path.return_value = self.test_db_path
        
        result = self.db_diag.run_diagnostics(auto_repair=False)
        
        assert result is not None
        assert 'status' in result
        assert result['db_exists'] is True
        assert 'checks' in result
        assert len(result['checks']) > 0

    @patch('storage.db_diagnostics.get_db_path')
    def test_diagnostics_db_not_exists(self, mock_get_db_path):
        """Test diagnostics when database doesn't exist."""
        mock_get_db_path.return_value = "/non/existent/path.db"
        
        result = self.db_diag.run_diagnostics(auto_repair=False)
        
        assert result is not None
        assert result['status'] == DIAGNOSTIC_CRITICAL
        assert result['db_exists'] is False
        assert 'errors' in result
        assert len(result['errors']) > 0

    @patch('storage.db_diagnostics.get_db_path')
    def test_quick_check(self, mock_get_db_path):
        """Test quick health check."""
        mock_get_db_path.return_value = self.test_db_path
        
        is_healthy, message = self.db_diag.quick_check()
        
        assert is_healthy is True
        assert "healthy" in message.lower()

    def test_diagnostic_log(self):
        """Test diagnostic logging."""
        self.db_diag._log_diagnostic("TEST_CODE", "info", "Test message")
        
        log = self.db_diag.get_diagnostic_log()
        assert len(log) == 1
        assert log[0]['code'] == "TEST_CODE"
        assert log[0]['level'] == "info"
        assert log[0]['message'] == "Test message"

    def test_clear_diagnostic_log(self):
        """Test clearing diagnostic log."""
        self.db_diag._log_diagnostic("TEST_CODE", "info", "Test message")
        assert len(self.db_diag.get_diagnostic_log()) == 1
        
        self.db_diag.clear_diagnostic_log()
        assert len(self.db_diag.get_diagnostic_log()) == 0

    @patch('storage.db_diagnostics.get_db_path')
    def test_run_database_diagnostics_function(self, mock_get_db_path):
        """Test convenience function."""
        mock_get_db_path.return_value = self.test_db_path
        
        result = run_database_diagnostics(auto_repair=False)
        
        assert result is not None
        assert 'status' in result

    @patch('storage.db_diagnostics.get_db_path')
    def test_quick_database_check_function(self, mock_get_db_path):
        """Test quick check convenience function."""
        mock_get_db_path.return_value = self.test_db_path
        
        is_healthy, message = quick_database_check()
        
        assert is_healthy is True

    @patch('storage.db_diagnostics.get_db_path')
    def test_get_diagnostic_log(self, mock_get_db_path):
        """Test getting diagnostic log."""
        mock_get_db_path.return_value = self.test_db_path
        
        self.db_diag._log_diagnostic("TEST1", "info", "Message 1")
        self.db_diag._log_diagnostic("TEST2", "warning", "Message 2")
        
        log = self.db_diag.get_diagnostic_log()
        assert len(log) == 2
        assert log[0]['code'] == "TEST1"
        assert log[1]['code'] == "TEST2"


class TestDatabaseDiagnosticsCorruption:
    """Test database diagnostics with corrupted database."""

    def setup_method(self):
        """Set up test environment with corrupted database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.test_db_path = self.temp_db.name
        
        # Create a corrupted database (write invalid data)
        with open(self.test_db_path, 'wb') as f:
            f.write(b'corrupted database data' * 100)

    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            try:
                time.sleep(0.1)
                os.remove(self.test_db_path)
            except (OSError, PermissionError) as e:
                print(f"Cleanup warning: {e}")
                try:
                    time.sleep(0.5)
                    os.remove(self.test_db_path)
                except (OSError, sqlite3.Error):
                    pass

    @patch('storage.db_diagnostics.get_db_path')
    def test_diagnostics_corrupted_db(self, mock_get_db_path):
        """Test diagnostics on corrupted database."""
        mock_get_db_path.return_value = self.test_db_path
        
        db_diag = DatabaseDiagnostics()
        result = db_diag.run_diagnostics(auto_repair=False)
        
        assert result is not None
        assert result['db_exists'] is True
        # Should have errors or status not OK
        assert result['status'] != DIAGNOSTIC_OK or len(result.get('errors', [])) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])