from __future__ import annotations
# gui/mixins/hibp_mixin.py
"""
Hibp mixin module for Secure Pass Pro.
Модуль Hibp mixin для Secure Pass Pro.
Модуль Hibp mixin для Secure Pass Pro.
"""
"""
Hibp mixin module for Secure Pass Pro.
Модуль Hibp mixin для Secure Pass Pro.
Модуль Hibp mixin для Secure Pass Pro.
"""
"""
HIBP (Have I Been Pwned) mixin for SecurePassPro
with rate limiting and improved error handling

Миксин HIBP (Have I Been Pwned) для SecurePassPro
с ограничением частоты и улучшенной обработкой ошибок

Міксин HIBP (Have I Been Pwned) для SecurePassPro
з обмеженням частоти та покращеною обробкою помилок

FIXED: Full 3-language support (RU, EN, UA) with localization keys
FIXED: Fixed "bad window path name" with withdraw() and delayed destroy()
FIXED: Theme now properly applied from main window
FIXED: HIBP windows now correctly use light/dark theme colors
FIXED: Warning and result dialogs now follow theme colors
FIXED: Result window layout - text centered, button at bottom
FIXED: Added emoji icons back to result window
FIXED: Button icon no longer disappears after click

FIXED: Added comment explaining why SHA-1 is REQUIRED by HIBP API
"""

import threading
import hashlib
import socket
import urllib.request
import urllib.error
import time
import tkinter as tk
import customtkinter as ctk
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from typing import Optional

logger = get_logger("hibp")

# Rate limiting
_last_hibp_check = 0
HIBP_COOLDOWN = 10
_MAX_RETRIES = 3
_RETRY_DELAY = 1


class HIBPMixin:
    """Mixin class for checking passwords against Have I Been Pwned database"""

    def _get_theme_colors(self) -> Any:
        """Get colors based on current theme from main window"""
        # Check current_theme from main window
        if hasattr(self, 'current_theme') and self.current_theme == "Light":
            return {
                "bg": "#F3F3F3",        # Light window background
                "fg": "#000000",        # Black text
                "entry_bg": "#FFFFFF",  # White entry background
                "label_text": "#000000", # Black label text
                "button_fg": "#1f538d",  # Blue button
                "button_text": "#FFFFFF", # White button text
                "frame_bg": "#F3F3F3",   # Frame background
                "success": "#00C853",    # Green for success
                "error": "#FF0000",      # Red for error
                "warning": "#FF9800",    # Orange for warning
                "progress_bg": "#E0E0E0", # Light gray progress bg
                "progress_color": "#1f538d" # Blue progress
            }
        else:
            return {
                "bg": "#1d1e1e",        # Dark window background
                "fg": "#FFFFFF",        # White text
                "entry_bg": "#2b2b2b",  # Dark entry background
                "label_text": "#FFFFFF", # White label text
                "button_fg": "#1f538d",  # Blue button
                "button_text": "#FFFFFF", # White button text
                "frame_bg": "#1d1e1e",   # Frame background
                "success": "#2ECC71",    # Green for success
                "error": "#FF4444",      # Red for error
                "warning": "#FFA500",    # Orange for warning
                "progress_bg": "#2b2b2b", # Dark gray progress bg
                "progress_color": "#1f538d" # Blue progress
            }

    def _update_ctkmessagebox_theme(self) -> None:
        """Update CTkMessageBox theme to match current theme"""
        try:
            from gui.dialogs import CTkMessageBox
            actual_theme = "light" if hasattr(self, 'current_theme') and self.current_theme == "Light" else "dark"
            CTkMessageBox.set_theme(actual_theme)
            if hasattr(self, 'current_lang'):
                CTkMessageBox.set_lang(self.current_lang)
            logger.debug(f"CTkMessageBox theme updated to: {actual_theme}")
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug(f"Failed to update CTkMessageBox theme: {e}")

    def _restore_hibp_button(self, original_text: str) -> None:
        """Restore HIBP button original text with icon"""
        try:
            if hasattr(self, 'btn_hibp') and self.btn_hibp and self.btn_hibp.winfo_exists():
                self.btn_hibp.configure(state="normal", text=original_text)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Failed to restore HIBP button: {e}")

    def _check_hibp(self) -> None:
        """
        Check current password against Have I Been Pwned (k-anonymity) with rate limiting.
        
        IMPORTANT: This uses SHA-1 as REQUIRED by the HIBP API specification.
        The Have I Been Pwned API uses the k-anonymity model which requires SHA-1
        hashes of passwords. This is an API requirement, not a security choice.
        The password itself is never sent to the API - only the first 5 characters
        of the SHA-1 hash are sent.
        
        ВАЖНО: Здесь используется SHA-1, так как это ТРЕБУЕТСЯ спецификацией HIBP API.
        API Have I Been Pwned использует модель k-анонимности, которая требует
        SHA-1 хеши паролей. Это требование API, а не выбор безопасности.
        Сам пароль никогда не отправляется в API - только первые 5 символов
        SHA-1 хеша отправляются.
        
        ВАЖЛИВО: Тут використовується SHA-1, оскільки це ВИМАГАЄТЬСЯ специфікацією HIBP API.
        API Have I Been Pwned використовує модель k-анонімності, яка вимагає
        SHA-1 хеші паролів. Це вимога API, а не вибір безпеки.
        Сам пароль ніколи не відправляється в API - тільки перші 5 символів
        SHA-1 хеша відправляються.
        """
        global _last_hibp_check

        # Update MessageBox theme before showing any dialog
        self._update_ctkmessagebox_theme()

        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        password = self.entry_res.get()

        if not password:
            CTkMessageBox.warning(
                self,
                L.get("hibp_check_button", "Check leaks / Проверить утечки / Перевірити витоки"),
                L.get("hibp_no_password", "Generate a password first. / Сначала сгенерируйте пароль. / Спочатку згенеруйте пароль.")
            )
            return

        now = time.time()
        time_since_last = now - _last_hibp_check

        if time_since_last < HIBP_COOLDOWN:
            wait_seconds = int(HIBP_COOLDOWN - time_since_last) + 1
            CTkMessageBox.warning(
                self,
                L.get("hibp_check_button", "Check leaks"),
                L.get("hibp_rate_limit", "Please wait {0} seconds before next check.\nThis protects the server from overload.").format(wait_seconds)
            )
            return

        _last_hibp_check = now

        # Show progress window
        self._show_checking_window()

        # Save original button text with icon
        original_text = ""
        try:
            # Get the original text to restore later
            if hasattr(self.btn_hibp, '_original_text'):
                original_text = self.btn_hibp._original_text
            else:
                original_text = self.btn_hibp.cget("text")
                self.btn_hibp._original_text = original_text
        except (tk.TclError, AttributeError, RuntimeError):
            pass

        # Disable button and show checking text (without icon)
        try:
            checking_text = L.get("hibp_checking_status", "Checking... / Проверка... / Перевірка...")
            self.btn_hibp.configure(state="disabled", text=checking_text)
        except (tk.TclError, AttributeError, KeyError):
            pass

        def _worker() -> None:
            """
            Handle worker.
            Обработать worker.
            Обробити worker.
            """
            try:
                result = self._check_hibp_with_retry(password)
                self.after(0, lambda: self._show_hibp_result(result))
            except (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError, ValueError, TypeError, AttributeError) as e:
                logger.error(f"HIBP error: {e}")
                self.after(0, lambda: self._show_hibp_result(None))
            finally:
                self.after(0, self._close_checking_window)
                # Restore button with original text (with icon)
                self.after(0, lambda: self._restore_hibp_button(original_text))

        threading.Thread(target=_worker, daemon=True).start()

    def _check_hibp_with_retry(self, password: str) -> Optional[int]:
        """
        Check password with retry attempts on errors.
        
        IMPORTANT: SHA-1 is REQUIRED by the HIBP API specification.
        The Have I Been Pwned API uses the k-anonymity model which requires
        SHA-1 hashes. This is an API requirement, not a security choice.
        Only the first 5 characters of the hash are sent to the API.
        
        ВАЖНО: SHA-1 ТРЕБУЕТСЯ спецификацией HIBP API.
        API Have I Been Pwned использует модель k-анонимности, которая требует
        SHA-1 хеши. Это требование API, а не выбор безопасности.
        Только первые 5 символов хеша отправляются в API.
        
        ВАЖЛИВО: SHA-1 ВИМАГАЄТЬСЯ специфікацією HIBP API.
        API Have I Been Pwned використовує модель k-анонімності, яка вимагає
        SHA-1 хеші. Це вимога API, а не вибір безпеки.
        Тільки перші 5 символів хеша відправляються в API.
        """
        for attempt in range(_MAX_RETRIES):
            try:
                # SHA-1 is REQUIRED by the HIBP API specification (k-anonymity model).
                # The API only accepts SHA1 prefixes of the password hash.
                # This is an API requirement, not a security choice.
                # The password itself is never sent - only the first 5 chars of the hash.
                sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
                prefix, suffix = sha1[:5], sha1[5:]
                url = f"https://api.pwnedpasswords.com/range/{prefix}"

                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "SecurePassPro/4.0",
                        "Add-Padding": "true"
                    }
                )

                with urllib.request.urlopen(req, timeout=10) as resp:
                    body = resp.read().decode("utf-8")

                for line in body.splitlines():
                    try:
                        h, c = line.split(":")
                        if h.strip() == suffix:
                            return int(c.strip())
                    except (ValueError, UnicodeDecodeError):
                        continue
                return 0

            except (urllib.error.URLError, socket.timeout, ConnectionError, TimeoutError) as e:
                logger.warning(f"HIBP error (attempt {attempt + 1}): {e}")
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(_RETRY_DELAY * (attempt + 1))
                else:
                    return None

        return None

    def _show_checking_window(self) -> None:
        """Show progress window for checking with theme support."""
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        colors = self._get_theme_colors()
        radius = self.current_radius

        # Close existing window
        self._close_checking_window()

        # Create new window
        checking_window = ctk.CTkToplevel(self)
        self._checking_window = checking_window

        try:
            checking_window.title(L.get("hibp_checking_title", "Checking password... / Проверка пароля... / Перевірка пароля..."))
            checking_window.geometry("350x200")
            checking_window.resizable(False, False)
            checking_window.transient(self)
            checking_window.grab_set()
            checking_window.lift()
            checking_window.focus_force()
            checking_window.after(100, lambda: checking_window.attributes("-topmost", False) if checking_window and checking_window.winfo_exists() else None)
            checking_window.attributes("-topmost", True)
            
            # Apply theme colors
            checking_window.configure(fg_color=colors["bg"])

            # Center window
            self._center_window(checking_window, 350, 200)

            main_frame = ctk.CTkFrame(checking_window, fg_color=colors["frame_bg"])
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Text label with theme color
            text_label = ctk.CTkLabel(
                main_frame,
                text=L.get("hibp_checking_status", "Checking... / Проверка... / Перевірка..."),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=colors["label_text"]
            )
            text_label.pack(pady=(30, 15))

            # Progress bar with theme colors
            progress_bar = ctk.CTkProgressBar(
                main_frame, 
                width=280,
                progress_color=colors["progress_color"],
                fg_color=colors["progress_bg"]
            )
            progress_bar.pack(pady=10)
            progress_bar.set(0)

            def animate(i=0) -> None:
                """
                Handle animate.
                Обработать animate.
                Обробити animate.
                """
                try:
                    if not checking_window or not checking_window.winfo_exists():
                        return
                    if i <= 100:
                        try:
                            progress_bar.set(i / 100)
                        except (tk.TclError, AttributeError, RuntimeError):
                            pass
                        try:
                            if checking_window and checking_window.winfo_exists():
                                checking_window.after(20, lambda: animate(i + 2))
                        except (tk.TclError, AttributeError, RuntimeError):
                            pass
                except (tk.TclError, AttributeError, RuntimeError):
                    pass

            animate()

            def remove_topmost() -> None:
                """
                Handle remove topmost.
                Обработать remove topmost.
                Обробити remove topmost.
                """
                if checking_window and checking_window.winfo_exists():
                    checking_window.attributes("-topmost", False)
            checking_window.after(100, remove_topmost)

        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Checking window error: {e}")
            self._close_checking_window()

    def _close_checking_window(self) -> None:
        """Close progress window safely using withdraw() and delayed destroy()."""
        if hasattr(self, '_checking_window') and self._checking_window:
            try:
                window = self._checking_window

                # Check if window exists
                if window.winfo_exists():
                    # Immediately hide the window (visually disappears)
                    window.withdraw()

                    # Release grab
                    try:
                        window.grab_release()
                    except (tk.TclError, AttributeError, RuntimeError):
                        pass

                    # Delay physical destruction to let CustomTkinter callbacks finish
                    def safe_delayed_destroy(w=window) -> None:
                        """
                        Handle safe delayed destroy.
                        Обработать safe delayed destroy.
                        Обробити safe delayed destroy.
                        """
                        try:
                            if w and w.winfo_exists():
                                w.destroy()
                        except (tk.TclError, AttributeError, RuntimeError):
                            pass

                    self.after(200, safe_delayed_destroy)

            except (tk.TclError, AttributeError, RuntimeError) as e:
                logger.debug(f"Error hiding checking window: {e}")

            # Clear reference immediately
            self._checking_window = None

    def _show_hibp_result(self, count: Optional[int]) -> None:
        """Show check result in a separate window with theme support."""
        # Update MessageBox theme before showing result
        self._update_ctkmessagebox_theme()

        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        colors = self._get_theme_colors()
        radius = self.current_radius

        # Create result window
        result_window = ctk.CTkToplevel(self)
        self._result_window = result_window
        
        result_window.title(L.get("hibp_result_title", "Breach check result / Результат проверки утечек / Результат перевірки витоків"))
        result_window.geometry("450x420")
        result_window.resizable(False, False)
        result_window.transient(self)
        result_window.grab_set()
        result_window.attributes("-topmost", True)
        
        # Apply theme colors to window
        result_window.configure(fg_color=colors["bg"])

        self._center_window(result_window, 450, 420)

        # Main container - using grid for better control
        main_frame = ctk.CTkFrame(result_window, fg_color=colors["frame_bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Configure grid rows - center row expands, button row fixed at bottom
        main_frame.grid_rowconfigure(0, weight=1)  # Top spacer
        main_frame.grid_rowconfigure(1, weight=0)  # Content
        main_frame.grid_rowconfigure(2, weight=1)  # Bottom spacer (pushes button down)
        main_frame.grid_rowconfigure(3, weight=0)  # Button
        main_frame.grid_columnconfigure(0, weight=1)

        # Top spacer
        top_spacer = ctk.CTkFrame(main_frame, fg_color="transparent", height=20)
        top_spacer.grid(row=0, column=0, sticky="nsew")

        # Content frame (centered)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.grid(row=1, column=0, sticky="n")

        if count is None:
            # Error
            icon_label = ctk.CTkLabel(
                content_frame,
                text=L.get("icon_warn", "(!)"),
                font=ctk.CTkFont(size=48),
                text_color=colors["warning"]
            )
            icon_label.pack(pady=(0, 10))
            
            title_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_error_title", "Check error / Ошибка проверки / Помилка перевірки"),
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=colors["warning"]
            )
            title_label.pack(pady=5)
            
            msg_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_check_error", "Could not connect to server.\nPlease check your internet connection. / Не удалось подключиться к серверу.\nПожалуйста, проверьте интернет-соединение. / Не вдалося підключитися до сервера.\nБудь ласка, перевірте інтернет-з'єднання."),
                font=ctk.CTkFont(size=13),
                justify="center",
                text_color=colors["label_text"]
            )
            msg_label.pack(pady=10)

        elif count == 0:
            # Safe - Password not found
            icon_label = ctk.CTkLabel(
                content_frame,
                text=L.get("icon_ok",   "(v)"),
                font=ctk.CTkFont(size=48),
                text_color=colors["success"]
            )
            icon_label.pack(pady=(0, 10))
            
            title_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_safe_title", "Password is safe / Пароль безопасен / Пароль безпечний"),
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=colors["success"]
            )
            title_label.pack(pady=5)
            
            msg_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_safe_message", "Password not found in breach databases.\n\nSafe to use. / Пароль не найден в базах утечек.\n\nБезопасно использовать. / Пароль не знайдено в базах витоків.\n\nБезпечно використовувати."),
                font=ctk.CTkFont(size=13),
                justify="center",
                text_color=colors["label_text"]
            )
            msg_label.pack(pady=10)

        else:
            # Found - Password compromised
            icon_label = ctk.CTkLabel(
                content_frame,
                text=L.get("icon_warn", "(!)"),
                font=ctk.CTkFont(size=48),
                text_color=colors["error"]
            )
            icon_label.pack(pady=(0, 10))
            
            title_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_found_title", "WARNING! Password compromised / ВНИМАНИЕ! Пароль скомпрометирован / УВАГА! Пароль скомпрометовано"),
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=colors["error"]
            )
            title_label.pack(pady=5)

            count_str = f"{count:,}".replace(",", " ")

            msg_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_found_message", "Password found {0} time(s) in breaches!\n\nGenerate a new password. / Пароль найден {0} раз(а) в утечках!\n\nСгенерируйте новый пароль. / Пароль знайдено {0} раз(и) у витоках!\n\nЗгенеруйте новий пароль.").format(count_str),
                font=ctk.CTkFont(size=13),
                justify="center",
                text_color=colors["label_text"]
            )
            msg_label.pack(pady=10)

            warning_label = ctk.CTkLabel(
                content_frame,
                text=L.get("hibp_change_password", "It is recommended to change your password immediately! / Рекомендуется немедленно сменить пароль! / Рекомендується негайно змінити пароль!"),
                font=ctk.CTkFont(size=12),
                text_color=colors["warning"]
            )
            warning_label.pack(pady=5)

            def generate_new() -> None:
                """
                Handle generate new.
                Обработать generate new.
                Обробити generate new.
                """
                try:
                    result_window.destroy()
                    self._result_window = None
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                self._generate()

            gen_btn = ctk.CTkButton(
                content_frame,
                text=L.get("hibp_generate_new", "Generate new password / Сгенерировать новый пароль / Згенерувати новий пароль"),
                command=generate_new,
                height=35,
                width=220,
                corner_radius=radius,
                fg_color=colors["button_fg"],
                text_color=colors["button_text"]
            )
            gen_btn.pack(pady=(10, 5))

        # Bottom spacer (pushes button down)
        bottom_spacer = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_spacer.grid(row=2, column=0, sticky="nsew")

        # Close button at the bottom
        def close_window() -> None:
            """
            Close window.
            Закрыть window.
            Закрити window.
            """
            try:
                result_window.destroy()
                self._result_window = None
            except (tk.TclError, AttributeError, RuntimeError):
                pass

        close_btn = ctk.CTkButton(
            main_frame,
            text=L.get("hibp_close", "Close / Закрыть / Закрити"),
            command=close_window,
            height=35,
            width=140,
            corner_radius=radius,
            fg_color="#8b0000",
            text_color="white"
        )
        close_btn.grid(row=3, column=0, pady=(10, 0))

        # Remove topmost after window is shown
        def remove_topmost() -> None:
            """
            Handle remove topmost.
            Обработать remove topmost.
            Обробити remove topmost.
            """
            if result_window and result_window.winfo_exists():
                result_window.attributes("-topmost", False)
        result_window.after(100, remove_topmost)

        # Store window reference for potential theme updates
        self._result_window = result_window

    def _center_window(self, window, width: int, height: int) -> None:
        """Center window relative to parent."""
        try:
            if not window or not window.winfo_exists():
                return
            if not self or not self.winfo_exists():
                from utils.helpers import center_screen
                center_screen(window, width, height)
                return

            window.update_idletasks()
            parent_x = self.winfo_x()
            parent_y = self.winfo_y()
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()
            x = parent_x + (parent_width // 2) - (width // 2)
            y = parent_y + (parent_height // 2) - (height // 2)

            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            if x < 0:
                x = 10
            if y < 30:
                y = 30
            if x + width > screen_width:
                x = screen_width - width - 10
            if y + height > screen_height:
                y = screen_height - height - 10

            window.geometry(f"{width}x{height}+{x}+{y}")
        except (tk.TclError, AttributeError, RuntimeError, ValueError):
            try:
                from utils.helpers import center_screen
                center_screen(window, width, height)
            except (tk.TclError, AttributeError, RuntimeError):
                pass


def reset_hibp_rate_limit() -> None:
    """Reset HIBP rate limit."""
    global _last_hibp_check
    _last_hibp_check = 0
