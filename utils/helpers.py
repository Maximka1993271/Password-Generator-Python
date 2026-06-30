"""
Compatibility shim — re-exports everything from the focused submodules.

Thin wrapper kept so that existing ``from utils.helpers import X`` imports
continue to work without modification.

Совместимый шим — реэкспортирует всё из специализированных модулей.
Шим сумісності — реекспортує все зі спеціалізованих модулів.
"""
from __future__ import annotations

from utils.platform_utils import (
    is_windows, is_macos, is_linux,
    get_platform, is_admin,
    get_screen_size, get_system_scaling,
    get_linux_desktop_environment, is_wayland,
    get_platform_info,
)

from utils.window_utils import (
    get_global_radius, set_global_radius,
    center_screen, center_window_relative,
    apply_window_rounding, set_window_icon,
    apply_linux_theme, apply_macos_theme,
)

from utils.resources import (
    get_resource_path, clear_resource_cache,
)

from utils.sound_utils import (
    play_sound,
    _get_sound_path,
    _validate_sound_path,
    _play_sound_windows,
    _play_sound_macos,
    _play_sound_linux,
)

from utils.file_utils import (
    format_time, truncate_string,
    is_valid_filename, ensure_dir,
    get_file_size_mb, safe_remove_file,
)

__all__ = [
    # platform
    "is_windows", "is_macos", "is_linux", "get_platform", "is_admin",
    "get_screen_size", "get_system_scaling",
    "get_linux_desktop_environment", "is_wayland", "get_platform_info",
    # window
    "get_global_radius", "set_global_radius",
    "center_screen", "center_window_relative",
    "apply_window_rounding", "set_window_icon",
    "apply_linux_theme", "apply_macos_theme",
    # resources
    "get_resource_path", "clear_resource_cache",
    # sound
    "play_sound",
    # file / string
    "format_time", "truncate_string", "is_valid_filename",
    "ensure_dir", "get_file_size_mb", "safe_remove_file",
]
