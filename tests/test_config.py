#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for storage/config.py - FULLY FIXED v4.0.1

Модульные тесты для storage/config.py - ПОЛНОСТЬЮ ИСПРАВЛЕНО v4.0.1
Модульні тести для storage/config.py - ПОВНІСТЮ ВИПРАВЛЕНО v4.0.1

ALL EXCEPTION HANDLING FIXED - No 'except Exception' remains
ВСЕ ОБРАБОТКИ ИСКЛЮЧЕНИЙ ИСПРАВЛЕНЫ - Не осталось 'except Exception'
ВСІ ОБРОБКИ ВИНЯТКІВ ВИПРАВЛЕНІ - Не залишилось 'except Exception'
"""
from __future__ import annotations

import pytest
import json
import os
import tempfile
import shutil
import time
import threading
from unittest.mock import patch

from utils.logger import get_logger
logger = get_logger("test_config")

from storage.config import Config

SCHEMA_VERSION = 5


class TestConfig:
    """Test configuration module - Fixed with proper mocking of config_paths"""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup config for tests with proper temp directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, '.securepass')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        
        with patch('storage.config_paths.get_config_file', return_value=self.config_path):
            with patch('storage.config_paths.get_config_dir', return_value=self.config_dir):
                Config._instance = None
                self.config = Config()
                self.config.set("THEME", "Dark")
                self.config.set("LANG", "RU")
                yield
                Config._instance = None
        
        time.sleep(0.1)
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"Cleanup error: {e}")

    # ==================== THREAD SAFETY TESTS ====================

    def test_concurrent_config_access(self):
        """Test concurrent access to config
        
        Тест параллельного доступа к конфигурации
        Тест паралельного доступу до конфігурації
        """
        results = []
        errors = []

        def worker(worker_id: int):
            try:
                self.config.set(f"worker_{worker_id}", worker_id)
                value = self.config.get(f"worker_{worker_id}")
                results.append((worker_id, value))
            except (KeyError, ValueError, TypeError, AttributeError, RuntimeError) as e:
                errors.append(e)
            except OSError as e:
                logger.debug(f"OS error in concurrent access: {e}")
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10


# ==================== INTEGRATION TESTS ====================

class TestConfigIntegration:
    """Integration tests for Config module"""

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.temp_dir, '.securepass')
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "config.json")
        
        with patch('storage.config_paths.get_config_file', return_value=self.config_path):
            with patch('storage.config_paths.get_config_dir', return_value=self.config_dir):
                Config._instance = None
                self.config = Config()
                yield
                Config._instance = None
        
        time.sleep(0.1)
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except (OSError, IOError, PermissionError) as e:
            logger.debug(f"Integration test cleanup error: {e}")

    def test_config_persistence(self):
        """Test that config persists across instances"""
        self.config.set("THEME", "Light")
        if hasattr(self.config, 'force_save'):
            self.config.force_save()
        else:
            self.config.save()
        
        Config._instance = None
        
        with patch('storage.config_paths.get_config_file', return_value=self.config_path):
            with patch('storage.config_paths.get_config_dir', return_value=self.config_dir):
                Config._instance = None
                new_config = Config()
                assert new_config.get("THEME") == "Light"
                Config._instance = None

    def test_config_corruption_recovery(self):
        """Test recovery from corrupted config file"""
        try:
            self.config.set("THEME", "Dark")
            if hasattr(self.config, 'force_save'):
                self.config.force_save()
            else:
                self.config.save()
            
            Config._instance = None
            time.sleep(0.1)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write("{corrupted json content")
            
            with patch('storage.config_paths.get_config_file', return_value=self.config_path):
                with patch('storage.config_paths.get_config_dir', return_value=self.config_dir):
                    Config._instance = None
                    new_config = Config()
                    assert new_config.get("THEME") is not None
                    Config._instance = None
        except PermissionError as e:
            logger.debug(f"Permission denied - skipping corruption test: {e}")
            pytest.skip("Permission denied on Windows - skipping corruption test")
        except (OSError, IOError) as e:
            logger.debug(f"OS error - skipping corruption test: {e}")
            pytest.skip(f"OS error: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])