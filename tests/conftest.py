"""
Pytest fixtures for Secure Pass Pro tests.
Фикстуры Pytest для тестов Secure Pass Pro.
Фікстури Pytest для тестів Secure Pass Pro.

FIXED: Corrected project root path detection
FIXED: Added proper sys.path handling
"""
from __future__ import annotations

import os
import sys
import tempfile
import pytest
import sqlite3
import time
from unittest.mock import MagicMock

# ==================== PATH SETUP ====================

# Get the project root directory
# Получаем корневую директорию проекта
# Отримуємо кореневу директорію проекту
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project root to path if not already there
# Добавляем корень проекта в путь, если его там нет
# Додаємо корінь проекту до шляху, якщо його там немає
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ==================== ENVIRONMENT FIXTURES ====================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    os.environ['SECUREPASS_TEST_MODE'] = '1'
    os.environ['SECUREPASS_SKIP_DB_INIT'] = '1'
    # Sync env changes into ConfigManager
    try:
        from core.config_manager import ConfigManager
        ConfigManager.instance().reload_env()
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError):
        pass
    yield
    os.environ.pop('SECUREPASS_TEST_MODE', None)
    os.environ.pop('SECUREPASS_SKIP_DB_INIT', None)


# ==================== DATABASE FIXTURES ====================

@pytest.fixture
def temp_db():
    """Create temporary database file."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except (OSError, PermissionError):
            pass


@pytest.fixture
def mock_db_path(tmp_path):
    """Create a mock database path for testing."""
    db_path = tmp_path / "test_passwords.db"
    return str(db_path)


@pytest.fixture
def clean_db(mock_db_path):
    """Create a clean database for testing with all tables."""
    import storage.database_queries
    from storage.database_migrations import init_database_schema
    
    # Patch get_db_path to use mock path
    original_get_db_path = storage.database_queries.get_db_path
    
    def mock_get_db_path():
        return mock_db_path
    
    storage.database_queries.get_db_path = mock_get_db_path
    
    # Create database with all tables
    try:
        # Create tables directly
        conn = sqlite3.connect(mock_db_path)
        cursor = conn.cursor()
        
        # Create passwords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
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
                sort_order INTEGER DEFAULT 0,
                custom_fields TEXT DEFAULT '[]',
                password_changed_at TEXT,
                deleted_at TEXT,
                tags TEXT DEFAULT '[]'
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_label ON passwords(label)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON passwords(created)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON passwords(favorite)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON passwords(category)")
        
        # Create password_history table for migration v8
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                password TEXT NOT NULL,
                changed_at TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hist_record ON password_history(record_id)")
        
        # Create schema_version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                applied_at TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # Set schema version to 8
        import datetime
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT OR REPLACE INTO schema_version (id, version, applied_at, description) VALUES (1, 8, ?, 'Initialized for tests')",
            (now,)
        )
        
        conn.commit()
        conn.close()
        
        # Also run init_database_schema for any additional setup
        try:
            init_database_schema()
        except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as e:
            print(f"Database init warning: {e}")
        
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as e:
        print(f"Database creation error: {e}")
    
    yield mock_db_path
    
    # Cleanup
    storage.database_queries.get_db_path = original_get_db_path
    if os.path.exists(mock_db_path):
        try:
            time.sleep(0.1)
            os.remove(mock_db_path)
        except (OSError, PermissionError):
            pass


# ==================== MOCK FIXTURES ====================

@pytest.fixture
def mock_config():
    """Mock Config object."""
    config = MagicMock()
    config.get.return_value = None
    config.set.return_value = True
    config.is_2fa_enabled.return_value = False
    return config


@pytest.fixture
def mock_logger():
    """Mock logger."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a mock config file."""
    config_path = tmp_path / 'config.json'
    config_path.write_text('{"THEME": "Dark", "LANG": "RU"}')
    return str(config_path)


@pytest.fixture
def patch_security_paths(monkeypatch, tmp_path):
    """Patch security module paths for testing."""
    # Mock paths
    monkeypatch.setattr('security.master_auth_constants.CONFIG_DIR', str(tmp_path))
    monkeypatch.setattr('security.master_auth_constants.MASTER_FILE', str(tmp_path / 'master.key'))
    monkeypatch.setattr('security.master_auth_constants.LOCKOUT_FILE', str(tmp_path / 'lockout.json'))
    monkeypatch.setattr('security.master_auth_constants.AUDIT_LOG_FILE', str(tmp_path / 'auth_audit.json'))
    monkeypatch.setattr('security.master_auth_constants.PASSWORD_HISTORY_FILE', str(tmp_path / 'password_history.json'))
    monkeypatch.setattr('security.master_auth_constants.TRUSTED_DEVICES_FILE', str(tmp_path / 'trusted_devices.json'))
    monkeypatch.setattr('security.master_auth_constants.RECOVERY_CODES_FILE', str(tmp_path / 'recovery_codes.json'))
    monkeypatch.setattr('security.master_auth_constants.SESSIONS_FILE', str(tmp_path / 'sessions.json'))
    
    return tmp_path


@pytest.fixture
def mock_master_password(monkeypatch):
    """Mock MasterPassword class for testing."""
    mock = MagicMock()
    mock.is_set.return_value = True
    mock.verify.return_value = True
    mock.get_lockout_info.return_value = {
        'attempts': 0,
        'max_attempts': 5,
        'remaining_attempts': 5,
        'lockout_seconds': 0,
        'is_locked': False,
        'is_permanently_locked': False
    }
    monkeypatch.setattr('security.master.MasterPassword', mock)
    return mock


# ==================== SAMPLE DATA FIXTURES ====================

@pytest.fixture
def sample_password_data():
    """Sample password data for tests."""
    return {
        "label": "Test Password",
        "password": "TestP@ssw0rd123!",
        "notes": "Test notes",
        "url": "https://example.com",
        "username": "testuser",
        "email": "test@example.com",
        "category": "Tests",
        "favorite": 0
    }


@pytest.fixture
def sample_passwords_list():
    """List of sample passwords."""
    return [
        {"label": "Google", "password": "G00gleP@ss!", "notes": "Google account"},
        {"label": "GitHub", "password": "GhP@ss123!", "notes": "GitHub account"},
        {"label": "Email", "password": "Em@ilP@ss!", "notes": "Email account"},
    ]


# ==================== EXPORTS ====================

__all__ = [
    # Environment
    'setup_test_environment',
    
    # Database
    'temp_db',
    'mock_db_path',
    'clean_db',
    
    # Mocks
    'mock_config',
    'mock_logger',
    'mock_config_file',
    'patch_security_paths',
    'mock_master_password',
    
    # Sample data
    'sample_password_data',
    'sample_passwords_list',

]
