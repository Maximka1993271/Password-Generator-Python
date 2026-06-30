"""
TOTP (Time-based One-Time Password) for two-factor authentication

TOTP (Time-based One-Time Password) для двухфакторной аутентификации
TOTP (Time-based One-Time Password) для двофакторної аутентифікації

FIXED #SPLIT: Code split into totp_core.py and totp_manager.py
This file is a wrapper for backward compatibility.

FIXED #SPLIT: Код разделён на totp_core.py и totp_manager.py
Этот файл является обёрткой для обратной совместимости.

FIXED #SPLIT: Код розділено на totp_core.py та totp_manager.py
Цей файл є обгорткою для зворотної сумісності.
"""
from __future__ import annotations

from security.totp_core import (
    TOTP,
    TOTPError,
    TOTPInvalidSecretError,
    TOTPRateLimitError,
    TOTPReplayError,
    TrustedDeviceToken,
    RecoveryCode,
    DEFAULT_INTERVAL,
    DEFAULT_DIGITS,
    DEFAULT_ALGORITHM,
    MAX_VERIFY_ATTEMPTS,
    VERIFY_ATTEMPT_WINDOW,
    ANTI_REPLAY_CACHE_SIZE,
    ANTI_REPLAY_EXPIRY_SECONDS,
    CACHE_CLEANUP_INTERVAL,
    RECOVERY_CODES_COUNT,
    RECOVERY_CODE_LENGTH,
    RECOVERY_CODE_HASH_PREFIX,
    RECOVERY_CODE_HASH_ITERATIONS,
    RECOVERY_CODE_SALT_BYTES,
    TRUSTED_DEVICE_TOKEN_EXPIRY,
    MAX_TRUSTED_DEVICES,
    TRUSTED_DEVICES_FILE,
)

from security.totp_manager import (
    TOTPManager,
    get_totp_manager,
    init_totp_from_config,
    save_totp_to_config,
    is_2fa_enabled,
    generate_2fa_qr_data,
    verify_2fa_code,
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
)

__all__ = [
    'TOTP',
    'TOTPManager',
    'TOTPError',
    'TOTPInvalidSecretError',
    'TOTPRateLimitError',
    'TOTPReplayError',
    'TrustedDeviceToken',
    'RecoveryCode',
    'get_totp_manager',
    'init_totp_from_config',
    'save_totp_to_config',
    'is_2fa_enabled',
    'generate_2fa_qr_data',
    'verify_2fa_code',
    'reset_2fa_rate_limit',
    'get_2fa_rate_limit_status',
    'clear_2fa_used_codes_cache',
    'force_2fa_cache_cleanup',
    'get_trusted_devices',
    'generate_trusted_device_token',
    'verify_trusted_device_token',
    'remove_trusted_device',
    'generate_recovery_codes',
    'verify_recovery_code',
    'get_recovery_codes_status',
    'DEFAULT_INTERVAL',
    'DEFAULT_DIGITS',
    'DEFAULT_ALGORITHM',
    'MAX_VERIFY_ATTEMPTS',
    'VERIFY_ATTEMPT_WINDOW',
    'ANTI_REPLAY_CACHE_SIZE',
    'ANTI_REPLAY_EXPIRY_SECONDS',
    'CACHE_CLEANUP_INTERVAL',
    'RECOVERY_CODES_COUNT',
    'RECOVERY_CODE_LENGTH',
    'RECOVERY_CODE_HASH_PREFIX',
    'RECOVERY_CODE_HASH_ITERATIONS',
    'RECOVERY_CODE_SALT_BYTES',
    'TRUSTED_DEVICE_TOKEN_EXPIRY',
    'MAX_TRUSTED_DEVICES',
    'TRUSTED_DEVICES_FILE',

]
