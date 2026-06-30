"""
Main application window - UI methods
Главное окно приложения - UI методы
Головне вікно програми - UI методи

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import os
import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, TypeVar, cast

import customtkinter as ctk

from gui.widgets import ToolTip
from utils.helpers import (
    get_global_radius, set_global_radius, center_screen,
    get_resource_path, play_sound, is_windows, is_macos, is_linux,
    apply_window_rounding, set_window_icon, apply_linux_theme, get_system_scaling,
    get_linux_desktop_environment, is_wayland
)
from utils.logger import get_logger
from Langs.lang import LANGUAGES

logger = get_logger("main_window_ui")


class UIMethods:
    """UI creation and setup methods for SecurePassPro."""

    # ==================== UI SETUP ====================

    def _setup_ui(self) -> None:
        """Create the complete user interface."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])

        try:
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self.grid_rowconfigure(0, weight=1)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Grid configuration error: {e}")

        # Create panels
        self._create_left_panel()
        self._create_2fa_indicator()
        self._create_checkboxes()
        self._create_length_slider()
        self._create_password_entry()
        self._create_strength_indicators()
        self._create_right_panel()
        self._create_bottom_frame()
        self._apply_linux_adaptation()

    # ==================== LEFT PANEL ====================

    def _create_left_panel(self) -> None:
        """Create the left panel with app info."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
            self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 0))

            self.lbl_title = ctk.CTkLabel(
                self.left_panel,
                text="Secure Pass Pro v4.0",
                font=("Segoe UI", 20, "bold")
            )
            self.lbl_title.pack(pady=(5, 0))

            self.lbl_author = ctk.CTkLabel(
                self.left_panel,
                text=L.get("author", "Author: Maxim Melnikov"),
                font=("Segoe UI", 14, "italic"),
                text_color="gray"
            )
            self.lbl_author.pack(pady=(0, 10))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Left panel setup error: {e}")

    def _create_2fa_indicator(self) -> None:
        """Create the 2FA status indicator."""
        try:
            self._2fa_indicator_label = ctk.CTkLabel(
                self.left_panel,
                text="",
                font=("Segoe UI", 11),
                text_color="#888888"
            )
            self._2fa_indicator_label.pack(pady=(0, 5))
            self.after(100, self._update_2fa_indicator)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"2FA indicator setup error: {e}")

    # ==================== CHECKBOXES ====================

    def _create_checkboxes(self) -> None:
        """Create the checkbox grid."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.cb_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
            self.cb_frame.pack(pady=10)

            # Row 0: Uppercase / Lowercase
            self.cb_upper = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("upper", "Uppercase"),
                variable=self.upper_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_upper.grid(row=0, column=1, padx=(70, 20), pady=6, sticky="w")

            self.cb_lower = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("lower", "Lowercase"),
                variable=self.lower_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_lower.grid(row=0, column=0, padx=(20, 70), pady=6, sticky="w")

            # Row 1: Digits / Special symbols
            self.cb_digits = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("digits", "Digits"),
                variable=self.digits_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_digits.grid(row=1, column=1, padx=(70, 20), pady=6, sticky="w")

            self.cb_symb = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("symb", "Special symbols"),
                variable=self.symb_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_symb.grid(row=1, column=0, padx=(20, 70), pady=6, sticky="w")

            # Row 2: Exclude ambiguous
            self.cb_ambig = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("ambig", "Exclude ambiguous"),
                variable=self.ambig_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_ambig.grid(row=2, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            # Row 4: Min 1 from each category
            self.cb_at_least = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("at_least", "Min 1 from each category"),
                variable=self.at_least_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_at_least.grid(row=4, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            # Row 5: Hide symbols
            self.cb_hide = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("hide", "Hide symbols"),
                variable=self.hide_var, command=self._toggle_hide,
                border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_hide.grid(row=5, column=0, columnspan=2, padx=20, pady=8, sticky="w")

            # Row 6: Avoid consecutive repeated characters
            self.cb_no_repeat = ctk.CTkCheckBox(
                self.cb_frame, text=L.get("no_repeat", "Avoid consecutive repeated characters"),
                variable=self.no_repeat_var, border_color="#4EC9B0", hover_color="#4EC9B0"
            )
            self.cb_no_repeat.grid(row=6, column=0, columnspan=2, padx=20, pady=8, sticky="w")

        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Checkbox setup error: {e}")

    # ==================== LENGTH SLIDER ====================

    def _create_length_slider(self) -> None:
        """Create the password length slider."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.lbl_len = ctk.CTkLabel(
                self.left_panel,
                text=f"{L.get('len', 'Length')}: 20",
                font=("Segoe UI", 16, "bold")
            )
            self.lbl_len.pack(pady=(10, 0))

            self.slider_len = ctk.CTkSlider(
                self.left_panel,
                from_=4, to=64, number_of_steps=60,
                width=400, command=self._update_len_label
            )
            self.slider_len.set(20)
            self.slider_len.pack(pady=(4, 0))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Slider setup error: {e}")

    # ==================== PASSWORD ENTRY ====================

    def _create_password_entry(self) -> None:
        """Create the password entry field with eye button."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.entry_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
            self.entry_frame.pack(pady=15, padx=40, fill="x")

            self.entry_res = ctk.CTkEntry(
                self.entry_frame,
                height=50,
                font=("Consolas", 22),
                justify="center",
                corner_radius=self.current_radius
            )
            self.entry_res.pack(side="left", fill="x", expand=True)

            # Eye button
            self.btn_eye = ctk.CTkButton(
                self.entry_frame,
                text=L.get("btn_eye", ""),
                width=50, height=50,
                font=("Segoe UI", 20),
                fg_color="#3a3a3a",
                hover_color="#555555",
                corner_radius=self.current_radius,
                command=self._toggle_eye
            )
            self.btn_eye.pack(side="left", padx=(6, 0))

            # Tooltip for eye button
            self._tooltips["btn_eye"] = ToolTip(self.btn_eye)
            self._tooltips["btn_eye"].set_text(
                L.get("tt_eye", "Show / hide password")
            )

        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Entry setup error: {e}")

    # ==================== STRENGTH INDICATORS ====================

    def _create_strength_indicators(self) -> None:
        """Create password strength indicator labels."""
        try:
            self.lbl_strength_text = ctk.CTkLabel(
                self.left_panel,
                text="",
                font=("Segoe UI", 14, "bold")
            )
            self.lbl_strength_text.pack()

            self.lbl_strength = ctk.CTkLabel(
                self.left_panel,
                text="",
                font=("Segoe UI", 13)
            )
            self.lbl_strength.pack()

            self.lbl_crack = ctk.CTkLabel(
                self.left_panel,
                text="",
                font=("Segoe UI", 13, "bold"),
                wraplength=500
            )
            self.lbl_crack.pack(pady=(0, 5))

            self._load_shield_icon()
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Strength indicators setup error: {e}")

    # ==================== RIGHT PANEL ====================

    def _create_right_panel(self) -> None:
        """Create the right panel with menu buttons."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.right_panel = ctk.CTkScrollableFrame(self, width=280)
            self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

            self.lbl_menu = ctk.CTkLabel(
                self.right_panel,
                text=L.get("menu_title", "Menu"),
                font=("Segoe UI", 18, "bold")
            )
            self.lbl_menu.pack(pady=15)

            # Create menu buttons
            self._create_menu_buttons()

        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Right panel setup error: {e}")

    def _create_menu_buttons(self) -> None:
        """Create all menu buttons."""
        buttons_config: List[Tuple[str, str, Callable, str, str]] = [
            ("btn_gen", "tt_gen", self._generate, "#00C853", ""),
            ("btn_name_gen", "tt_name_gen", self._open_name_generator, "#E91E63", ""),
            ("btn_passphrase", "tt_passphrase", self._open_passphrase_generator, "#00BCD4", ""),
            ("btn_copy", "tt_copy", self._copy, "#00B0F0", ""),
            ("btn_save", "tt_save", self._save, "#9C27B0", ""),
            ("btn_open", "tt_open", self._open, "#FF9800", ""),
            ("btn_qr", "tt_qr", self._show_qr, "#E91E63", ""),
            ("btn_hist", "tt_hist", self._show_history, "#FFC107", ""),
            ("btn_db", "tt_db", self._show_db_window, "#2196F3", ""),
            ("btn_hibp", "tt_hibp", self._check_hibp, "#FF5722", ""),
            ("btn_upd", "tt_upd", self._open_update_url, "#009688", ""),
            ("btn_settings", "tt_settings", self._show_settings, "#607D8B", ""),
            ("btn_about", "tt_about", self._show_about, "#455A64", ""),
        ]

        for lang_key, tt_key, cmd, color, icon in buttons_config:
            self._create_menu_btn(self.right_panel, lang_key, tt_key, cmd, color, icon)

    def _create_menu_btn(
        self,
        parent: ctk.CTkFrame,
        lang_key: str,
        tt_key: str,
        cmd: Callable,
        color: str,
        icon: str = ""
    ) -> ctk.CTkButton:
        """Create a single menu button."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])

        neon_colors: Dict[str, str] = {
            "#00C853": "#00E676", "#00B0F0": "#4FC3F7", "#9C27B0": "#CE93D8",
            "#FF9800": "#FFB74D", "#E91E63": "#F06292", "#FFC107": "#FFD54F",
            "#2196F3": "#64B5F6", "#009688": "#4DB6AC", "#607D8B": "#90A4AE",
            "#455A64": "#78909C", "#00BCD4": "#26C6DA",
        }
        hover: str = neon_colors.get(color, color)

        btn: ctk.CTkButton = ctk.CTkButton(
            parent,
            text="",
            fg_color=color,
            height=45,
            border_width=0,
            font=("Segoe UI", 13, "bold"),
            hover_color=hover,
            corner_radius=self.current_radius,
            anchor="w"
        )

        def animated_cmd() -> None:
            self._animate_button(btn)
            cmd()

        btn.configure(command=animated_cmd)
        btn.pack(pady=6, padx=20, fill="x")

        # Store metadata
        btn.lang_key = lang_key
        btn.tt_key = tt_key
        btn.icon = icon

        # Set text with icon
        btn_text: str = L.get(lang_key, lang_key)
        if icon:
            btn.configure(text=f" {icon}   {btn_text}")
        else:
            btn.configure(text=f"   {btn_text}")

        # Add tooltip
        tt_text: str = L.get(tt_key, tt_key)
        if tt_key == "tt_copy":
            tt_text = tt_text.format(self.clipboard_timeout)

        self._tooltips[lang_key] = ToolTip(btn)
        self._tooltips[lang_key].set_text(tt_text)

        return btn

    # ==================== BOTTOM FRAME ====================

    def _create_bottom_frame(self) -> None:
        """Create the bottom frame with rating stars."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
            self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 15))

            self.lbl_app_rating = ctk.CTkLabel(
                self.bottom_frame,
                text=L.get("rating_stars", "★★★★★"),
                font=("Segoe UI", 20),
                text_color="#FFD700"
            )
            self.lbl_app_rating.pack(pady=(5, 5))
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Bottom frame setup error: {e}")

    # ==================== LINUX ADAPTATION ====================

    def _apply_linux_adaptation(self) -> None:
        """Apply Linux-specific adaptations."""
        if not is_linux():
            return

        try:
            scaling: float = get_system_scaling()
            desktop_env: str = get_linux_desktop_environment()

            if scaling > 1.0:
                try:
                    self.lbl_title.configure(font=("Segoe UI", int(20 * min(scaling, 2.0))))
                    self.lbl_menu.configure(font=("Segoe UI", int(18 * min(scaling, 2.0))))
                    self.entry_res.configure(font=("Consolas", int(22 * min(scaling, 2.0))))
                    self.btn_eye.configure(font=("Segoe UI", int(20 * min(scaling, 2.0))))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Linux font scaling error: {e}")

            if 'gnome' in desktop_env or 'unity' in desktop_env:
                try:
                    self.right_panel.configure(scrollbar_button_color="#2d6a4f")
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
            elif 'kde' in desktop_env or 'plasma' in desktop_env:
                try:
                    ctk.set_widget_scaling(1.0)
                except (tk.TclError, AttributeError, RuntimeError):
                    pass

            if is_wayland():
                try:
                    self.attributes('-type', 'normal')
                except (tk.TclError, AttributeError, RuntimeError):
                    pass

        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Linux adaptation error: {e}")

    # ==================== UTILITY METHODS ====================

    def _open_passphrase_generator(self) -> None:
        """Open the passphrase generator dialog."""
        try:
            from gui.passphrase_dialog import show_passphrase_dialog
            actual_theme: str = "light" if self.current_theme == "Light" else "dark"
            show_passphrase_dialog(self, self.current_lang, actual_theme)
        except ImportError as e:
            logger.error(f"Failed to import passphrase generator: {e}")
            from gui.dialogs import CTkMessageBox
            L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error"),
                f"{L.get('passphrase_error', 'Failed to open passphrase generator')}:\n{str(e)}"
            )
        except (TypeError, ValueError, OSError, MemoryError) as e:
            logger.error(f"Failed to open passphrase generator: {e}")
            from gui.dialogs import CTkMessageBox
            L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
            CTkMessageBox.error(
                self,
                L.get("err_title", "Error"),
                f"{L.get('passphrase_error', 'Failed to open passphrase generator')}:\n{str(e)}"
            )

    def _load_shield_icon(self) -> None:
        """Load shield icon for password strength display."""
        try:
            from PIL import Image
            import os

            possible_paths: List[str] = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "Icons", "Shield.png"),
                os.path.join(os.getcwd(), "Icons", "Shield.png"),
                os.path.join(os.getcwd(), "Shield.png"),
                get_resource_path("Shield.png"),
            ]

            icon_path: Optional[str] = None
            for path in possible_paths:
                if os.path.exists(path):
                    icon_path = path
                    break

            if not icon_path:
                logger.warning(
                    "Shield icon not found / Иконка щита не найдена / Іконку щита не знайдено"
                )
                return

            img = Image.open(icon_path).convert("RGBA")
            try:
                img = img.resize((48, 48), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize((48, 48), Image.ANTIALIAS)

            self._base_shield_image = img
            self._update_shield_icon("medium")
            logger.info(
                "Shield icon loaded successfully / Иконка щита загружена / Іконку щита завантажено"
            )

        except ImportError as e:
            logger.warning(
                f"PIL not available for shield icon / PIL не доступен для иконки щита: {e}"
            )
        except (OSError, IOError, PermissionError, AttributeError) as e:
            logger.debug(f"Shield icon load error: {e}")

    def _update_shield_icon(self, strength_type: str = "medium") -> None:
        """Update shield icon color based on password strength."""
        if not hasattr(self, '_base_shield_image') or self._base_shield_image is None:
            return

        try:
            from PIL import Image

            colors: Dict[str, Tuple[int, int, int]] = {
                "weak": (255, 68, 68),
                "medium": (255, 165, 0),
                "medium_plus": (255, 215, 0),
                "strong": (46, 204, 113)
            }

            if strength_type == "weak":
                color: Tuple[int, int, int] = colors["weak"]
            elif strength_type == "medium":
                if hasattr(self, '_last_entropy') and self._last_entropy < 60:
                    color = colors["medium"]
                else:
                    color = colors["medium_plus"]
            else:
                color = colors["strong"]

            img = self._base_shield_image.copy()
            overlay = Image.new("RGBA", img.size, (*color, 0))
            result = Image.alpha_composite(img, overlay)

            ctk_img = ctk.CTkImage(light_image=result, dark_image=result, size=(48, 48))

            if hasattr(self, '_shield_label') and self._shield_label:
                try:
                    self._shield_label.configure(image=ctk_img)
                    self._shield_label.image = ctk_img
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Shield label update error: {e}")
            else:
                try:
                    self._shield_label = ctk.CTkLabel(self.left_panel, image=ctk_img, text="")
                    self._shield_label.image = ctk_img
                    self._shield_label.pack(pady=(5, 0))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Shield label creation error: {e}")

        except (ImportError, AttributeError, RuntimeError, OSError) as e:
            logger.debug(f"Shield icon update error: {e}")

    def _update_2fa_indicator(self) -> None:
        """Update 2FA indicator in main window."""
        if not hasattr(self, '_2fa_indicator_label') or not self._2fa_indicator_label:
            return

        try:
            L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
            if self.config.is_2fa_enabled():
                self._2fa_indicator_label.configure(
                    text=L.get("2fa_status_enabled", "2FA Enabled"),
                    text_color="#2ECC71"
                )
            else:
                self._2fa_indicator_label.configure(
                    text=L.get("2fa_status_disabled", "2FA Disabled"),
                    text_color="#888888"
                )
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Update 2FA indicator error: {e}")

    # ==================== THEME AND UI HELPERS ====================

    def _apply_theme_colors(self, actual_theme: str) -> None:
        """Apply theme colors to all widgets."""
        if actual_theme == "light":
            bg_main: str = "#F3F3F3"
            fg_main: str = "#000000"
            entry_bg: str = "#FFFFFF"
            panel_bg: str = "#F3F3F3"
            checkmark_color: str = "#1f538d"
        else:
            bg_main = "#1d1e1e"
            fg_main = "#FFFFFF"
            entry_bg = "#2b2b2b"
            panel_bg = "#1d1e1e"
            checkmark_color = "#4EC9B0"

        try:
            self.configure(fg_color=bg_main)
            self.left_panel.configure(fg_color=panel_bg)
            self.right_panel.configure(fg_color=panel_bg)
            self.entry_res.configure(fg_color=entry_bg, text_color=fg_main)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Theme color application error: {e}")

        checkboxes: List[ctk.CTkCheckBox] = [
            self.cb_upper, self.cb_lower, self.cb_digits, self.cb_symb,
            self.cb_ambig, self.cb_at_least, self.cb_hide, self.cb_no_repeat
        ]
        for cb in checkboxes:
            if cb and cb.winfo_exists():
                try:
                    cb.configure(fg_color=panel_bg, text_color=fg_main, checkmark_color=checkmark_color)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Checkbox color error: {e}")

        labels: List[ctk.CTkLabel] = [
            self.lbl_title, self.lbl_author, self.lbl_len,
            self.lbl_strength, self.lbl_strength_text, self.lbl_crack, self.lbl_menu
        ]
        for label in labels:
            if label and label.winfo_exists():
                try:
                    label.configure(text_color=fg_main)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Label color error: {e}")

        canvases: List[Optional[tk.Canvas]] = [
            self._rgb_c_top, self._rgb_c_bottom,
            self._rgb_c_left, self._rgb_c_right
        ]
        for canvas in canvases:
            if canvas:
                try:
                    canvas.configure(bg=bg_main)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Canvas color error: {e}")

        self._update_rgb_speed_buttons()
        self._update_rgb_width_buttons()

    def _center_main_window(self) -> None:
        """Center main window on screen."""
        try:
            self.update_idletasks()
            x: int = (self.winfo_screenwidth() // 2) - (950 // 2)
            y: int = (self.winfo_screenheight() // 2) - (800 // 2)
            self.geometry(f"950x800+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.error(f"Main window centering error: {e}")
            self.geometry("950x800")

    def _center_window_relative_to_parent(self, window: ctk.CTkToplevel, width: int, height: int) -> None:
        """Center window relative to parent."""
        try:
            window.update_idletasks()
            parent_x: int = self.winfo_x()
            parent_y: int = self.winfo_y()
            parent_width: int = self.winfo_width()
            parent_height: int = self.winfo_height()

            x: int = parent_x + (parent_width // 2) - (width // 2)
            y: int = parent_y + (parent_height // 2) - (height // 2)

            screen_width: int = self.winfo_screenwidth()
            screen_height: int = self.winfo_screenheight()

            if x < 0:
                x = 10
            if y < 30:
                y = 30
            if x + width > screen_width:
                x = screen_width - width - 10
            if y + height > screen_height:
                y = screen_height - height - 10

            window.geometry(f"{width}x{height}+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Window centering error: {e}")

    # ==================== RGB METHODS ====================

    def _update_rgb_speed_buttons(self) -> None:
        """Update RGB speed button states."""
        # Implementation in RGB mixin
        pass

    def _update_rgb_width_buttons(self) -> None:
        """Update RGB width button states."""
        # Implementation in RGB mixin
        pass

    def _animate_button(self, btn: ctk.CTkButton) -> None:
        """Animate button click with sound."""
        play_sound("click", self.sound_enabled.get())

    # ==================== EYE BUTTON HELPERS ====================

    def _toggle_hide(self) -> None:
        """Toggle hide mode."""
        self._sync_eye_to_hide_var()

    def _toggle_eye(self) -> None:
        """Toggle eye button."""
        self.hide_var.set(not self.hide_var.get())
        self._sync_eye_to_hide_var()

    def _sync_eye_to_hide_var(self) -> None:
        """Sync eye button with hide variable."""
        hidden: bool = self.hide_var.get()
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.entry_res.configure(show="*" if hidden else "")
            if hidden:
                self.btn_eye.configure(text=L.get("btn_eye_closed", ""))
            else:
                self.btn_eye.configure(text=L.get("btn_eye", ""))
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Eye button sync error: {e}")

    def _open_update_url(self) -> None:
        """Open GitHub releases page."""
        import webbrowser
        try:
            webbrowser.open(UPD_URL)
        except webbrowser.Error as e:
            logger.error(f"Failed to open URL: {e}")

    def _update_len_label(self, val: float) -> None:
        """Update length label."""
        L: Dict[str, str] = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.lbl_len.configure(text=f"{L.get('len', 'Length')}: {int(val)}")
        except (tk.TclError, KeyError, AttributeError) as e:
            logger.debug(f"Update length label error: {e}")


# ==================== CONSTANTS ====================

UPD_URL: str = "https://github.com/Maximka1993271/Password-Generator-Python/releases"
