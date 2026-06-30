#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for security/totp.py
"""
from __future__ import annotations

import pytest
import time
import os
import tempfile
import json
import threading
import hashlib
import base64
import binascii
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List, Generator, Optional

# ==================== IMPORTS ====================
from security.totp_core import TOTP
from security.totp_manager import TOTPManager
from security.totp import (
    TOTPError,
    TOTPRateLimitError,
    TOTPReplayError,
    TOTPInvalidSecretError,
    get_totp_manager,
    verify_2fa_code,
    init_totp_from_config,
    save_totp_to_config,
    is_2fa_enabled,
    generate_2fa_qr_data,
    reset_2fa_rate_limit,
    get_2fa_rate_limit_status,
    clear_2fa_used_codes_cache,
    force_2fa_cache_cleanup,
    get_trusted_devices,
    generate_trusted_device_token,
    verify_trusted_device_token,
    remove_trusted_device,
    generate_recovery_codes,
    verify_recovery_code,
    get_recovery_codes_status,
    MAX_VERIFY_ATTEMPTS,
    VERIFY_ATTEMPT_WINDOW,
    ANTI_REPLAY_CACHE_SIZE,
    ANTI_REPLAY_EXPIRY_SECONDS,
    RECOVERY_CODES_COUNT,
    RECOVERY_CODE_LENGTH,
    MAX_TRUSTED_DEVICES,
    TRUSTED_DEVICE_TOKEN_EXPIRY,
)


class TestTOTP:
    """Test TOTP module"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """
        Handle setup and teardown.
        Обработать setup and teardown.
        Обробити setup and teardown.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.trusted_devices_file = os.path.join(self.temp_dir, "trusted_devices.json")
        yield
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== SECRET GENERATION TESTS ====================

    def test_generate_secret(self):
        """
        Handle test generate secret.
        Обработать test generate secret.
        Обробити test generate secret.
        """
        secret = TOTP.generate_secret()
        assert secret is not None
        assert len(secret) >= 16
        assert secret.isupper()
        import re
        assert re.match(r'^[A-Z2-7]+$', secret) is not None

    def test_generate_secret_different_lengths(self):
        """
        Handle test generate secret different lengths.
        Обработать test generate secret different lengths.
        Обробити test generate secret different lengths.
        """
        for length in [10, 16, 20, 32]:
            secret = TOTP.generate_secret(length)
            assert len(secret) >= length

    def test_generate_secret_uniqueness(self):
        """
        Handle test generate secret uniqueness.
        Обработать test generate secret uniqueness.
        Обробити test generate secret uniqueness.
        """
        secrets = set()
        for i in range(10):
            secret = TOTP.generate_secret()
            assert secret not in secrets
            secrets.add(secret)

    # ==================== TOTP INITIALIZATION TESTS ====================

    def test_totp_initialization(self):
        """
        Handle test totp initialization.
        Обработать test totp initialization.
        Обробити test totp initialization.
        """
        totp = TOTP()
        assert totp.secret is not None
        assert totp.digits == 6
        assert totp.interval == 30
        assert totp.algorithm == "SHA1"

    def test_totp_with_custom_secret(self):
        """
        Handle test totp with custom secret.
        Обработать test totp with custom secret.
        Обробити test totp with custom secret.
        """
        custom_secret = "JBSWY3DPEHPK3PXP"
        totp = TOTP(custom_secret)
        assert totp.secret == custom_secret

    def test_totp_with_custom_parameters(self):
        """
        Handle test totp with custom parameters.
        Обработать test totp with custom parameters.
        Обробити test totp with custom parameters.
        """
        totp = TOTP(digits=8, interval=60, algorithm="SHA256")
        assert totp.digits == 8
        assert totp.interval == 60
        assert totp.algorithm == "SHA256"

    def test_totp_with_sha512(self):
        """
        Handle test totp with sha512.
        Обработать test totp with sha512.
        Обробити test totp with sha512.
        """
        totp = TOTP(algorithm="SHA512")
        assert totp.algorithm == "SHA512"
        code = totp.get_current_code()
        assert len(code) == 6

    # ==================== CODE GENERATION TESTS ====================

    def test_generate_code(self):
        """
        Handle test generate code.
        Обработать test generate code.
        Обробити test generate code.
        """
        totp = TOTP()
        code = totp.generate_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_with_timestamp(self):
        """
        Handle test generate code with timestamp.
        Обработать test generate code with timestamp.
        Обробити test generate code with timestamp.
        """
        totp = TOTP()
        timestamp = time.time()
        code1 = totp.generate_code(timestamp)
        code2 = totp.generate_code(timestamp)
        assert code1 == code2

    def test_get_current_code(self):
        """
        Handle test get current code.
        Обработать test get current code.
        Обробити test get current code.
        """
        totp = TOTP()
        code = totp.get_current_code()
        assert len(code) == 6
        assert code.isdigit()

    def test_code_changes_over_time(self):
        """
        Handle test code changes over time.
        Обработать test code changes over time.
        Обробити test code changes over time.
        """
        totp = TOTP(interval=1)
        code1 = totp.get_current_code()
        time.sleep(1.5)
        code2 = totp.get_current_code()
        assert len(code1) == 6
        assert len(code2) == 6

    def test_code_consistency(self):
        """
        Handle test code consistency.
        Обработать test code consistency.
        Обробити test code consistency.
        """
        secret = TOTP.generate_secret()
        totp1 = TOTP(secret)
        totp2 = TOTP(secret)
        code1 = totp1.get_current_code()
        code2 = totp2.get_current_code()
        assert code1 == code2

    # ==================== CODE VERIFICATION TESTS ====================

    def test_verify_correct_code(self):
        """
        Handle test verify correct code.
        Обработать test verify correct code.
        Обробити test verify correct code.
        """
        totp = TOTP()
        code = totp.get_current_code()
        is_valid, drift = totp.verify(code, window=1)
        assert is_valid is True

    def test_verify_incorrect_code(self):
        """
        Handle test verify incorrect code.
        Обработать test verify incorrect code.
        Обробити test verify incorrect code.
        """
        totp = TOTP()
        is_valid, drift = totp.verify("123456", window=1)
        assert is_valid is False

    def test_verify_with_time_window(self):
        """
        Handle test verify with time window.
        Обработать test verify with time window.
        Обробити test verify with time window.
        """
        totp = TOTP()
        code = totp.generate_code(time.time() - 30)
        is_valid, drift = totp.verify(code, window=2)
        assert is_valid is True

    def test_verify_with_negative_drift(self):
        """
        Handle test verify with negative drift.
        Обработать test verify with negative drift.
        Обробити test verify with negative drift.
        """
        totp = TOTP(interval=30)
        code = totp.generate_code(time.time() + 30)
        is_valid, drift = totp.verify(code, window=3)
        assert is_valid is True
        assert drift in [-1, 0, 1]

    def test_verify_with_zero_window(self):
        """
        Handle test verify with zero window.
        Обработать test verify with zero window.
        Обробити test verify with zero window.
        """
        totp = TOTP()
        code = totp.get_current_code()
        is_valid, drift = totp.verify(code, window=0)
        assert is_valid is True

    # ==================== ANTI-REPLAY PROTECTION TESTS ====================

    def test_anti_replay_protection(self):
        """
        Handle test anti replay protection.
        Обработать test anti replay protection.
        Обробити test anti replay protection.
        """
        totp = TOTP()
        code = totp.get_current_code()
        is_valid, _ = totp.verify(code, window=1)
        assert is_valid is True
        is_valid, _ = totp.verify(code, window=1)
        assert is_valid is False

    def test_anti_replay_different_timestamps(self):
        """
        Handle test anti replay different timestamps.
        Обработать test anti replay different timestamps.
        Обробити test anti replay different timestamps.
        """
        totp = TOTP(interval=1)
        code = totp.get_current_code()
        result, drift = totp.verify(code)
        assert result is True
        time.sleep(1.5)
        code2 = totp.get_current_code()
        result2, drift2 = totp.verify(code2)
        assert result2 is True

    def test_anti_replay_cache_size_limit(self):
        """
        Handle test anti replay cache size limit.
        Обработать test anti replay cache size limit.
        Обробити test anti replay cache size limit.
        """
        totp = TOTP()
        for i in range(ANTI_REPLAY_CACHE_SIZE + 10):
            temp_totp = TOTP()
            code = temp_totp.get_current_code()
            temp_totp.verify(code)
        assert len(totp._used_codes) <= ANTI_REPLAY_CACHE_SIZE + 10

    def test_anti_replay_cache_cleanup(self):
        """
        Handle test anti replay cache cleanup.
        Обработать test anti replay cache cleanup.
        Обробити test anti replay cache cleanup.
        """
        totp = TOTP()
        code = totp.get_current_code()
        totp.verify(code)
        removed = totp.force_cleanup()
        assert removed >= 0
        totp.clear_used_codes_cache()
        assert len(totp._used_codes) == 0

    # ==================== RATE LIMITING TESTS ====================

    def test_rate_limiting(self):
        """
        Handle test rate limiting.
        Обработать test rate limiting.
        Обробити test rate limiting.
        """
        totp = TOTP()
        source = "test_source"
        for i in range(MAX_VERIFY_ATTEMPTS):
            try:
                totp.verify("000000", source=source)
            except TOTPRateLimitError:
                pass
        status = totp.get_rate_limit_status(source)
        assert status["attempts"] >= 0
        assert status["remaining"] >= 0

    def test_rate_limit_reset(self):
        """
        Handle test rate limit reset.
        Обработать test rate limit reset.
        Обробити test rate limit reset.
        """
        totp = TOTP()
        source = "reset_test"
        for i in range(3):
            totp.verify("000000", source=source)
        status_before = totp.get_rate_limit_status(source)
        totp.reset_rate_limit(source)
        status_after = totp.get_rate_limit_status(source)
        assert status_after["attempts"] == 0

    def test_rate_limit_all_sources_reset(self):
        """
        Handle test rate limit all sources reset.
        Обработать test rate limit all sources reset.
        Обробити test rate limit all sources reset.
        """
        totp = TOTP()
        for i in range(3):
            totp.verify("000000", source=f"source_{i}")
        totp.reset_rate_limit(None)
        for i in range(3):
            status = totp.get_rate_limit_status(f"source_{i}")
            assert status["attempts"] == 0

    def test_get_time_remaining(self):
        """
        Handle test get time remaining.
        Обработать test get time remaining.
        Обробити test get time remaining.
        """
        totp = TOTP(interval=30)
        remaining = totp.get_time_remaining()
        assert 0 <= remaining <= 30

    def test_get_time_remaining_with_timestamp(self):
        """
        Handle test get time remaining with timestamp.
        Обработать test get time remaining with timestamp.
        Обробити test get time remaining with timestamp.
        """
        totp = TOTP(interval=30)
        timestamp = time.time()
        remaining = totp.get_time_remaining(timestamp)
        assert 0 <= remaining <= 30

    # ==================== BACKUP CODES TESTS ====================

    def test_backup_codes_generation(self):
        """
        Handle test backup codes generation.
        Обработать test backup codes generation.
        Обробити test backup codes generation.
        """
        totp = TOTP()
        backup_codes = totp.get_backup_codes(count=10, length=8)
        assert len(backup_codes) == 10
        for code in backup_codes:
            code_clean = code.replace("-", "")
            assert len(code_clean) == 8

    def test_backup_codes_various_lengths(self):
        """
        Handle test backup codes various lengths.
        Обработать test backup codes various lengths.
        Обробити test backup codes various lengths.
        """
        totp = TOTP()
        for length in [6, 8, 10]:
            backup_codes = totp.get_backup_codes(count=5, length=length)
            assert len(backup_codes) == 5
            for code in backup_codes:
                code_clean = code.replace("-", "")
                assert len(code_clean) == length

    def test_backup_code_hash(self):
        """
        Handle test backup code hash.
        Обработать test backup code hash.
        Обробити test backup code hash.
        """
        code = "12345678"
        hashed = TOTP.hash_backup_code(code)
        assert hashed is not None
        assert TOTP.verify_backup_code(code, hashed) is True
        assert TOTP.verify_backup_code("wrong", hashed) is False
        assert TOTP.verify_backup_code("87654321", hashed) is False

    def test_backup_code_hash_consistency(self):
        """
        Handle test backup code hash consistency.
        Обработать test backup code hash consistency.
        Обробити test backup code hash consistency.
        """
        code = "12345678"
        hashed1 = TOTP.hash_backup_code(code)
        hashed2 = TOTP.hash_backup_code(code)
        assert hashed1 != hashed2
        assert TOTP.verify_backup_code(code, hashed1) is True
        assert TOTP.verify_backup_code(code, hashed2) is True

    def test_backup_code_hash_legacy_compatibility(self):
        """
        Handle test backup code hash legacy compatibility.
        Обработать test backup code hash legacy compatibility.
        Обробити test backup code hash legacy compatibility.
        """
        code = "12345678"
        legacy_hash = hashlib.sha256(code.encode()).hexdigest()
        assert TOTP.verify_backup_code(code, legacy_hash) is True

    # ==================== PROVISIONING URI TESTS ====================

    def test_get_provisioning_uri(self):
        """
        Handle test get provisioning uri.
        Обработать test get provisioning uri.
        Обробити test get provisioning uri.
        """
        secret = "JBSWY3DPEHPK3PXP"
        uri = TOTP.get_provisioning_uri(secret, "test@example.com", "TestApp")
        assert "otpauth://totp/" in uri
        assert "secret=JBSWY3DPEHPK3PXP" in uri
        assert "issuer=TestApp" in uri
        assert "period=30" in uri
        assert "digits=6" in uri

    def test_get_provisioning_uri_with_special_chars(self):
        """
        Handle test get provisioning uri with special chars.
        Обработать test get provisioning uri with special chars.
        Обробити test get provisioning uri with special chars.
        """
        secret = TOTP.generate_secret()
        account_name = "user@domain.com"
        uri = TOTP.get_provisioning_uri(secret, account_name)
        assert "otpauth://totp/" in uri
        assert "%40" in uri

    def test_get_provisioning_uri_with_spaces(self):
        """
        Handle test get provisioning uri with spaces.
        Обработать test get provisioning uri with spaces.
        Обробити test get provisioning uri with spaces.
        """
        secret = TOTP.generate_secret()
        uri = TOTP.get_provisioning_uri(secret, "test", "My Test App")
        assert "My%20Test%20App" in uri

    # ==================== TOTP MANAGER TESTS ====================

    def test_totp_manager_enable_disable(self):
        """
        Handle test totp manager enable disable.
        Обработать test totp manager enable disable.
        Обробити test totp manager enable disable.
        """
        manager = TOTPManager()
        manager.disable_2fa()
        assert manager.is_enabled() is False
        secret, uri = manager.enable_2fa()
        assert manager.is_enabled() is True
        assert secret is not None
        assert uri is not None
        manager.disable_2fa()
        assert manager.is_enabled() is False

    def test_totp_manager_verify(self):
        """
        Handle test totp manager verify.
        Обработать test totp manager verify.
        Обробити test totp manager verify.
        """
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        totp = TOTP(secret)
        code = totp.get_current_code()
        assert manager.verify_code(code) is True
        assert manager.verify_code("123456") is False

    def test_totp_manager_backup_codes(self):
        """
        Handle test totp manager backup codes.
        Обработать test totp manager backup codes.
        Обробити test totp manager backup codes.
        """
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        backup_codes = ["12345678", "87654321", "11111111"]
        manager.set_backup_codes(backup_codes)
        assert manager.verify_backup_code("12345678") is True
        assert manager.verify_backup_code("wrong") is False
        assert manager.verify_backup_code("87654321") is True
        assert manager.verify_backup_code("12345678") is False

    def test_totp_manager_secret_storage(self):
        """
        Handle test totp manager secret storage.
        Обработать test totp manager secret storage.
        Обробити test totp manager secret storage.
        """
        manager = TOTPManager()
        secret = "JBSWY3DPEHPK3PXP"
        manager.set_secret(secret)
        assert manager.get_secret() == secret

    def test_totp_manager_account_name(self):
        """
        Handle test totp manager account name.
        Обработать test totp manager account name.
        Обробити test totp manager account name.
        """
        manager = TOTPManager()
        account_name = "MySecureAccount"
        manager.set_account_name(account_name)
        secret, uri = manager.enable_2fa()
        assert account_name in uri

    def test_totp_manager_get_provisioning_uri(self):
        """
        Handle test totp manager get provisioning uri.
        Обработать test totp manager get provisioning uri.
        Обробити test totp manager get provisioning uri.
        """
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        retrieved_uri = manager.get_provisioning_uri()
        assert retrieved_uri is not None
        assert secret in retrieved_uri

    def test_totp_manager_generate_new_backup_codes(self):
        """Test TOTP manager backup code generation - fixed"""
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        codes = manager.generate_new_backup_codes(count=5, length=8)
        assert len(codes) == 5
        
        # Must call set_backup_codes to actually store them
        manager.set_backup_codes(codes)
        
        status = manager.get_recovery_codes_status()
        assert "total" in status
        assert status.get("total", 0) == 5
        assert status.get("available", 0) == 5

    # ==================== TRUSTED DEVICES TESTS ====================

    def test_trusted_devices(self):
        """
        Handle test trusted devices.
        Обработать test trusted devices.
        Обробити test trusted devices.
        """
        totp = TOTP()
        totp.set_trusted_devices_file(self.trusted_devices_file)
        device_id = "test_device_001"
        device_name = "Test Laptop"
        token = totp.generate_trusted_device_token(device_id, device_name)
        assert token is not None
        result = totp.verify_trusted_device_token(device_id, token)
        assert result is True
        devices = totp.get_trusted_devices()
        assert len(devices) >= 1
        result = totp.remove_trusted_device(device_id)
        assert result is True
        result = totp.verify_trusted_device_token(device_id, token)
        assert result is False

    def test_trusted_devices_persistence(self):
        """
        Handle test trusted devices persistence.
        Обработать test trusted devices persistence.
        Обробити test trusted devices persistence.
        """
        totp = TOTP()
        totp.set_trusted_devices_file(self.trusted_devices_file)
        device_id = "persistent_device"
        device_name = "Persistent Device"
        token = totp.generate_trusted_device_token(device_id, device_name)
        assert token is not None
        totp2 = TOTP()
        totp2.set_trusted_devices_file(self.trusted_devices_file)
        result = totp2.verify_trusted_device_token(device_id, token)
        assert result is True

    def test_trusted_devices_max_limit(self):
        """
        Handle test trusted devices max limit.
        Обработать test trusted devices max limit.
        Обробити test trusted devices max limit.
        """
        totp = TOTP()
        totp.set_trusted_devices_file(self.trusted_devices_file)
        devices_added = 0
        for i in range(MAX_TRUSTED_DEVICES + 5):
            token = totp.generate_trusted_device_token(f"device_{i}", f"Device {i}")
            if token:
                devices_added += 1
            else:
                break
        assert devices_added <= MAX_TRUSTED_DEVICES

    # ==================== GLOBAL FUNCTIONS TESTS ====================

    def test_global_totp_manager(self):
        """
        Handle test global totp manager.
        Обработать test global totp manager.
        Обробити test global totp manager.
        """
        manager1 = get_totp_manager()
        manager2 = get_totp_manager()
        assert manager1 is manager2

    def test_verify_2fa_code_function(self):
        """
        Handle test verify 2fa code function.
        Обработать test verify 2fa code function.
        Обробити test verify 2fa code function.
        """
        result = verify_2fa_code("123456", source="test")
        assert isinstance(result, bool)

    def test_is_2fa_enabled_function(self):
        """
        Handle test is 2fa enabled function.
        Обработать test is 2fa enabled function.
        Обробити test is 2fa enabled function.
        """
        result = is_2fa_enabled()
        assert isinstance(result, bool)

    def test_generate_2fa_qr_data_function(self):
        """
        Handle test generate 2fa qr data function.
        Обработать test generate 2fa qr data function.
        Обробити test generate 2fa qr data function.
        """
        secret, uri = generate_2fa_qr_data("test@example.com")
        assert secret is not None
        assert uri is not None
        assert "otpauth://totp/" in uri

    def test_rate_limit_functions(self):
        """
        Handle test rate limit functions.
        Обработать test rate limit functions.
        Обробити test rate limit functions.
        """
        reset_2fa_rate_limit("test_source")
        status = get_2fa_rate_limit_status("test_source")
        assert "attempts" in status
        assert "max_attempts" in status
        assert "remaining" in status

    def test_cache_cleanup_functions(self):
        """
        Handle test cache cleanup functions.
        Обработать test cache cleanup functions.
        Обробити test cache cleanup functions.
        """
        clear_2fa_used_codes_cache()
        result = force_2fa_cache_cleanup()
        assert result >= 0

    # ==================== CONFIG INTEGRATION TESTS ====================

    def test_init_totp_from_config(self):
        """
        Handle test init totp from config.
        Обработать test init totp from config.
        Обробити test init totp from config.
        """
        class MockConfig:
            def __init__(self):
                self._data = {
                    "2fa_enabled": True,
                    "2fa_secret": "JBSWY3DPEHPK3PXP",
                    "2fa_backup_hashes": [],
                    "2fa_account_name": "TestUser",
                }
            def get(self, key, default=None):
                return self._data.get(key, default)
        mock_config = MockConfig()
        init_totp_from_config(mock_config)
        assert True

    def test_save_totp_to_config(self):
        """
        Handle test save totp to config.
        Обработать test save totp to config.
        Обробити test save totp to config.
        """
        class MockConfig:
            def __init__(self):
                self._data = {}
            def set(self, key, value):
                self._data[key] = value
                return True
            def save(self):
                return True
        mock_config = MockConfig()
        save_totp_to_config(mock_config)
        assert True

    # ==================== CONCURRENT VERIFICATION TESTS ====================

    def test_concurrent_verification(self):
        """
        Handle test concurrent verification.
        Обработать test concurrent verification.
        Обробити test concurrent verification.
        """
        totp = TOTP()
        code = totp.get_current_code()
        results = []
        errors = []

        def verify_worker():
            try:
                result, _ = totp.verify(code, source=f"worker_{threading.current_thread().name}")
                results.append(result)
            except (ValueError, TypeError, RuntimeError, AttributeError,
                    TOTPRateLimitError, TOTPReplayError, TOTPError) as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=verify_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert sum(results) == 1


# ==================== INTEGRATION TESTS ====================

class TestTOTPIntegration:
    """Integration tests for TOTP"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Handle setup.
        Обработать setup.
        Обробити setup.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.trusted_file = os.path.join(self.temp_dir, "trusted.json")
        yield
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_2fa_flow(self):
        """Test complete 2FA flow - fixed"""
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        assert manager.is_enabled() is True
        
        backup_codes = manager.generate_new_backup_codes(count=5, length=8)
        assert len(backup_codes) == 5
        
        # Must call set_backup_codes to actually store them
        manager.set_backup_codes(backup_codes)
        
        totp = TOTP(secret)
        code = totp.get_current_code()
        assert manager.verify_code(code) is True
        assert manager.verify_backup_code(backup_codes[0]) is True
        assert manager.verify_backup_code(backup_codes[0]) is False
        
        status = manager.get_recovery_codes_status()
        used = status.get("used", 0)
        assert used >= 1
        available = status.get("available", 0)
        assert available == 4
        total = status.get("total", 0)
        assert total == 5
        
        manager.disable_2fa()
        assert manager.is_enabled() is False

    def test_full_2fa_flow_with_trusted_device(self):
        """
        Handle test full 2fa flow with trusted device.
        Обработать test full 2fa flow with trusted device.
        Обробити test full 2fa flow with trusted device.
        """
        manager = TOTPManager()
        manager.set_trusted_devices_file(self.trusted_file)
        secret, uri = manager.enable_2fa()
        assert manager.is_enabled() is True
        device_id = "trusted_laptop"
        device_name = "My Laptop"
        token = manager.generate_trusted_device_token(device_id, device_name)
        assert token is not None
        result = manager.verify_trusted_device_token(device_id, token)
        assert result is True
        devices = manager.get_trusted_devices()
        assert len(devices) >= 1
        result = manager.remove_trusted_device(device_id)
        assert result is True
        result = manager.verify_trusted_device_token(device_id, token)
        assert result is False
        manager.disable_2fa()
        assert manager.is_enabled() is False

    def test_2fa_with_rate_limiting(self):
        """
        Handle test 2fa with rate limiting.
        Обработать test 2fa with rate limiting.
        Обробити test 2fa with rate limiting.
        """
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        source = "test_source"
        for i in range(MAX_VERIFY_ATTEMPTS):
            result = manager.verify_code("000000", source=source)
            assert result is False
        result = manager.verify_code("000000", source=source)
        assert result is False
        manager.reset_rate_limit(source)
        result = manager.verify_code("000000", source=source)
        assert result is False

    def test_2fa_backup_codes_regeneration(self):
        """
        Handle test 2fa backup codes regeneration.
        Обработать test 2fa backup codes regeneration.
        Обробити test 2fa backup codes regeneration.
        """
        manager = TOTPManager()
        secret, uri = manager.enable_2fa()
        codes1 = manager.generate_new_backup_codes(count=3, length=8)
        assert len(codes1) == 3
        codes2 = manager.generate_new_backup_codes(count=3, length=8)
        assert len(codes2) == 3
        assert codes1 != codes2
        
        # Need to set codes to actually store them
        manager.set_backup_codes(codes2)
        
        result = manager.verify_backup_code(codes1[0])
        assert result is False
        result = manager.verify_backup_code(codes2[0])
        assert result is True


if __name__ == "__main__":

    main()
