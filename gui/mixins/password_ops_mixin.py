"""
Password operations mixin for SecurePassPro - WORKING VERSION (UTF-8 + PDF CYRILLIC SUPPORT)
Миксин операций с паролями для SecurePassPro - РАБОЧАЯ ВЕРСИЯ (UTF-8 + ПОДДЕРЖКА КИРИЛЛИЦЫ В PDF)
Міксин операцій з паролями для SecurePassPro - РОБОЧА ВЕРСІЯ (UTF-8 + ПІДТРИМКА КИРИЛИЦІ В PDF)
"""
from __future__ import annotations

import os
import sys
import re
import datetime
import sqlite3
import time
import secrets
import tkinter as tk
from tkinter import filedialog
from typing import Tuple

import customtkinter as ctk

from storage.database import PasswordDB
from gui.dialogs import CTkMessageBox
from Langs.lang import LANGUAGES
from utils.logger import get_logger
from cryptography.exceptions import InvalidTag
from core.generator import SecurePasswordContext, _clear_string

logger = get_logger("password_ops")

MAX_PASSWORD_LENGTH = 1000
MAX_LABEL_LENGTH = 200


def sanitize_label(label: str, max_length: int = MAX_LABEL_LENGTH) -> str:
    """
    Handle sanitize label.
    Обработать sanitize label.
    Обробити sanitize label.
    """
    if not label:
        return "Без метки / No label / Без мітки"
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(label))
    sanitized = sanitized.strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized if sanitized else "Без метки / No label / Без мітки"


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    Проверить корректность password strength.
    Перевірити коректність password strength.
    """
    if not password:
        return False, "Password is empty"
    if len(password) < 4:
        return False, "Password too short (minimum 4 characters)"
    return True, ""


class PasswordOpsMixin:
    """
    Passwordopsmixin class.
    Класс PasswordOpsMixin.
    Клас PasswordOpsMixin.
    """
    SHIELD_ICON_SIZE = 96

    def _update_len_label(self, val: float) -> None:
        """
        Handle update len label.
        Обработать update len label.
        Обробити update len label.
        """
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            self.lbl_len.configure(text=f"{L.get('len', 'Length')}: {int(val)}")
        except (KeyError, AttributeError, tk.TclError, RuntimeError) as e:
            logger.debug(f"Update length label error: {e}")

    def _load_shield_icons(self) -> None:
        """
        Handle load shield icons.
        Обработать load shield icons.
        Обробити load shield icons.
        """
        try:
            from PIL import Image
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            resources_dir = os.path.join(base_dir, "Icons")
            if not os.path.exists(resources_dir):
                resources_dir = os.path.join(os.getcwd(), "Icons")
            if not os.path.exists(resources_dir):
                resources_dir = os.path.join(os.getcwd())
            
            self._shield_icons = {}
            icon_names = {
                "weak": "Shield_red.png",
                "medium": "Shield_orange.png", 
                "medium_plus": "Shield_yellow.png",
                "strong": "Shield_green.png"
            }
            for strength, filename in icon_names.items():
                icon_path = os.path.join(resources_dir, filename)
                if os.path.exists(icon_path):
                    img = Image.open(icon_path).convert("RGBA")
                    size = self.SHIELD_ICON_SIZE
                    try:
                        img = img.resize((size, size), Image.Resampling.LANCZOS)
                    except AttributeError:
                        img = img.resize((size, size), Image.ANTIALIAS)
                    self._shield_icons[strength] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            if self._shield_icons:
                self.after(10, lambda: self._update_shield_icon("strong"))
        except (ImportError, OSError, IOError, PermissionError, AttributeError, ValueError) as e:
            logger.warning(f"Shield icons not loaded: {e}")

    def _create_shield_label(self) -> None:
        """
        Handle create shield label.
        Обработать create shield label.
        Обробити create shield label.
        """
        try:
            if hasattr(self, '_shield_label') and self._shield_label and self._shield_label.winfo_exists():
                return
            icon = self._shield_icons.get("strong")
            if not icon:
                return
            self._shield_label = ctk.CTkLabel(self.left_panel, image=icon, text="")
            self._shield_label.image = icon
            self._shield_label.pack(pady=(5, 0))
        except (KeyError, AttributeError, tk.TclError, RuntimeError) as e:
            logger.debug(f"Shield label creation error: {e}")

    def _update_shield_icon(self, strength_type: str, entropy_bits: float = 0) -> None:
        """
        Handle update shield icon.
        Обработать update shield icon.
        Обробити update shield icon.
        """
        if not hasattr(self, '_shield_icons') or not self._shield_icons:
            self._load_shield_icons()
            if not hasattr(self, '_shield_icons') or not self._shield_icons:
                return
        icon_key = "weak" if strength_type == "weak" else ("medium_plus" if strength_type == "medium" and entropy_bits >= 60 else "strong" if strength_type == "strong" else "medium")
        icon = self._shield_icons.get(icon_key, self._shield_icons.get("strong"))
        if not icon:
            return
        if hasattr(self, '_shield_label') and self._shield_label and self._shield_label.winfo_exists():
            try:
                self._shield_label.configure(image=icon)
                self._shield_label.image = icon
            except (AttributeError, tk.TclError, RuntimeError) as e:
                logger.debug(f"Shield label update ignored: {e}")
        else:
            self._create_shield_label()

    def _update_strength_meter(self, password: str) -> None:
        """
        Handle update strength meter.
        Обработать update strength meter.
        Обробити update strength meter.
        """
        if not password:
            try:
                self.lbl_strength_text.configure(text="")
                self.lbl_strength.configure(text="")
                self.lbl_crack.configure(text="")
            except (AttributeError, tk.TclError, RuntimeError) as e:
                logger.debug(f"Strength meter clear ignored: {e}")
            return
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        try:
            stats = self.strength_calc.calculate(password)
        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            logger.error(f"Strength calculation error: {e}")
            return
        try:
            self.lbl_strength.configure(text=L.get("strength", "Strength: ~{0} combos").format(stats.get('combinations', '0')))
        except (KeyError, AttributeError, tk.TclError, RuntimeError) as e:
            logger.debug(f"Strength label format ignored: {e}")
            
        strength_type = stats.get('strength_level', 'medium')
        entropy_bits = stats.get('entropy_bits', 0)
        self._update_shield_icon(strength_type, entropy_bits)
        if strength_type == 'weak':
            stars_color = "#FF4C4C"
            st_text = L.get("st_low", "Weak password")
        elif strength_type == 'medium':
            stars_color = "#FFD700" if entropy_bits >= 60 else "#FFA500"
            st_text = L.get("st_mid", "Medium password")
        else:
            stars_color = "#2ECC71"
            st_text = L.get("st_high", "Strong password")
        try:
            self.lbl_strength_text.configure(text=st_text, text_color=stars_color)
            self.lbl_crack.configure(text=L.get("crack_time", "{0}").format(L.get(stats.get('crack_time_label', 'time_cent'), "centuries to crack")), text_color=stars_color)
        except (KeyError, AttributeError, tk.TclError, RuntimeError) as e:
            logger.debug(f"Crack time label format ignored: {e}")
        self._animate_password_field(strength_type)

    def _animate_password_field(self, strength_type: str = "medium") -> None:
        """
        Handle animate password field.
        Обработать animate password field.
        Обробити animate password field.
        """
        try:
            original_border = self.entry_res.cget("border_color")
        except (tk.TclError, AttributeError, RuntimeError) as e:
            original_border = "#2b2b2b"
            logger.debug(f"Original border fetch failed: {e}")
            
        if strength_type == "weak":
            neon_colors = ["#FF4444", "#FF6666", "#FF8888", "#FF6666", "#FF4444"]
        elif strength_type == "strong":
            neon_colors = ["#2ECC71", "#55DD88", "#88EEAA", "#55DD88", "#2ECC71"]
        else:
            neon_colors = ["#FFA500", "#FFBB33", "#FFCC66", "#FFBB33", "#FFA500"]
        
        def pulse_step(step: int = 0):
            if step < len(neon_colors):
                try:
                    self.entry_res.configure(border_color=neon_colors[step], border_width=3)
                    self._pulse_animation_id = self.after(60, lambda: pulse_step(step + 1))
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Pulse step update failed: {e}")
            else:
                try:
                    self.entry_res.configure(border_color=original_border if original_border else "#2b2b2b", border_width=2)
                except (tk.TclError, AttributeError, RuntimeError) as e:
                    logger.debug(f"Pulse border restore failed: {e}")
                self._pulse_animation_id = None
        
        if self._pulse_animation_id:
            try:
                self.after_cancel(self._pulse_animation_id)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Pulse animation cancel failed: {e}")
        pulse_step()

    def _check_duplicate_password(self, password: str) -> bool:
        """
        Handle check duplicate password.
        Обработать check duplicate password.
        Обробити check duplicate password.
        """
        try:
            all_passwords = PasswordDB.get_all()
            for record in all_passwords:
                if record.get("password") == password:
                    return True
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError) as e:
            logger.error(f"Duplicate check error: {e}")
        return False

    def _sanitize_import_content(self, content: str) -> str:
        """
        Handle sanitize import content.
        Обработать sanitize import content.
        Обробити sanitize import content.
        """
        if not content:
            return ""
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', content)
        sanitized = re.sub(r'[\u200B-\u200D\uFEFF]', '', sanitized)
        if len(sanitized) > MAX_PASSWORD_LENGTH:
            sanitized = sanitized[:MAX_PASSWORD_LENGTH]
        return sanitized

    def _generate(self) -> None:
        """
        Handle generate.
        Обработать generate.
        Обробити generate.
        """
        if hasattr(self, 'btn_gen') and self.btn_gen:
            self._animate_button(self.btn_gen)
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        self.generator.use_upper = self.upper_var.get()
        self.generator.use_lower = self.lower_var.get()
        self.generator.use_digits = self.digits_var.get()
        self.generator.use_special = self.symb_var.get()
        self.generator.exclude_ambiguous = self.ambig_var.get()
        self.generator.exclude_unambiguous = self.unambig_var.get()
        self.generator.min_each = self.at_least_var.get()
        self.generator.no_repeat = self.no_repeat_var.get()
        self.generator.length = int(self.slider_len.get())
        
        if not (self.generator.use_upper or self.generator.use_lower or
                self.generator.use_digits or self.generator.use_special):
            CTkMessageBox.warning(self, L.get("err_title", "Error"), L.get("err_cat", "Select at least one category!"))
            return
        
        try:
            with SecurePasswordContext() as ctx:
                secure_pwd = self.generator.generate_secure()
                if secure_pwd is None:
                    CTkMessageBox.warning(self, L.get("err_title", "Error"), L.get("err_pool_small", "Too few available characters!"))
                    return
                password = secure_pwd.get_string()
                ctx.set_password(secure_pwd)
                if password:
                    self.entry_res.delete(0, "end")
                    self.entry_res.insert(0, password)
                    self.history.append(password)
                    self._update_strength_meter(password)
                    self._play_sound()
                _clear_string(password)
        except (InvalidTag, ValueError, TypeError, RuntimeError, OSError, AttributeError) as e:
            logger.error(f"Generation error: {e}")
            CTkMessageBox.error(self, L.get("err_title", "Error"), f"Generation error: {e}")

    def _clear_clipboard(self) -> None:
        """
        Handle clear clipboard.
        Обработать clear clipboard.
        Обробити clear clipboard.
        """
        try:
            if not self.winfo_exists():
                return
            for i in range(5):
                try:
                    junk = secrets.token_hex(512)
                    self.clipboard_clear()
                    self.clipboard_append(junk)
                    self.update()
                    time.sleep(0.01)
                except (tk.TclError, OSError, PermissionError, RuntimeError):
                    continue
            self.clipboard_clear()
            self.update()
        except (tk.TclError, OSError, PermissionError, RuntimeError) as e:
            logger.debug(f"Clipboard clear error: {e}")
        finally:
            self._clipboard_timer = None

    def _copy(self) -> None:
        """
        Handle copy.
        Обработать copy.
        Обробити copy.
        """
        if hasattr(self, 'btn_copy') and self.btn_copy:
            self._animate_button(self.btn_copy)
        pwd = self.entry_res.get().strip()
        if not pwd:
            CTkMessageBox.warning(self, "Warning", "No password to copy!")
            return
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        if hasattr(self, '_clipboard_timer') and self._clipboard_timer:
            try:
                self.after_cancel(self._clipboard_timer)
            except (tk.TclError, ValueError, RuntimeError) as e:
                logger.debug(f"Clipboard timer cancel failed: {e}")
                
        try:
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.update()
            self._play_sound()
        except (tk.TclError, OSError, PermissionError, RuntimeError) as e:
            logger.error(f"Clipboard copy error: {e}")
            CTkMessageBox.error(self, L.get("err_title", "Error"), f"Could not copy: {e}")
            return
        
        timeout_ms = self.clipboard_timeout * 1000
        self._clipboard_timer = self.after(timeout_ms, self._clear_clipboard)
        
        try:
            old_text = self.btn_copy.cget("text")
            self.btn_copy.configure(text=L.get("copied", "Copied! ({0}s)").format(self.clipboard_timeout))
            self.after(2000, lambda: self.btn_copy.configure(text=old_text))
        except (tk.TclError, AttributeError, KeyError, RuntimeError) as e:
            logger.debug(f"Copy button text restore failed: {e}")
        
        CTkMessageBox.info(self, L.get("dlg_title_copied", "Clipboard"), L.get("pwd_done", "Password copied!"))

    def _safe_button_restore(self, old_text: str) -> None:
        """
        Handle safe button restore.
        Обработать safe button restore.
        Обробити safe button restore.
        """
        try:
            if hasattr(self, 'btn_copy') and self.btn_copy and self.btn_copy.winfo_exists():
                self.btn_copy.configure(text=old_text)
        except (tk.TclError, AttributeError, RuntimeError) as e:
            logger.debug(f"Safe button restore failed: {e}")

    def _play_sound(self, sound_type: str = "click") -> None:
        """
        Handle play sound.
        Обработать play sound.
        Обробити play sound.
        """
        if not hasattr(self, 'sound_enabled') or not self.sound_enabled.get():
            return
        try:
            import platform
            import subprocess
            import shutil
            import ctypes
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            file_path = os.path.join(base_path, "Computer Mouse Click.mp3")
            if not os.path.exists(file_path):
                alt_paths = [
                    os.path.join(os.getcwd(), "Computer Mouse Click.mp3"),
                    os.path.join(os.getcwd(), "Icons", "Computer Mouse Click.mp3"),
                ]
                for alt in alt_paths:
                    if os.path.exists(alt):
                        file_path = alt
                        break
                else:
                    return
            if platform.system() == "Windows":
                winmm = ctypes.windll.winmm
                alias = "app_click"
                winmm.mciSendStringW(f'close {alias}', None, 0, 0)
                winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {alias}', None, 0, 0)
                winmm.mciSendStringW(f'play {alias} from 0', None, 0, 0)
                self.after(1000, lambda: winmm.mciSendStringW(f'close {alias}', None, 0, 0))
            elif platform.system() == "Darwin":
                if shutil.which("afplay"):
                    subprocess.Popen(["afplay", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                if shutil.which("mpg123"):
                    subprocess.Popen(["mpg123", "-q", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, IOError, PermissionError, subprocess.SubprocessError, AttributeError, TypeError) as e:
            logger.debug(f"Sound playback failed: {e}")

    def _save(self) -> None:
        """
        Handle save.
        Обработать save.
        Обробити save.
        """
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        pwd = self.entry_res.get().strip()
        
        if not pwd:
            CTkMessageBox.warning(self, L.get("warn", "Warning"), L.get("no_pwd", "No password to save!"))
            return

        self.attributes("-topmost", False)
        self.update_idletasks()
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".txt",
            filetypes=[
                (L.get("export_text", "Text Files"), "*.txt"),
                (L.get("export_password", "Password Files"), "*.key"),
                (L.get("export_log", "Log Files"), "*.log"),
                (L.get("export_pdf", "PDF Files"), "*.pdf"),
                (L.get("export_all", "All Files"), "*.*")
            ]
        )

        if not path:
            return

        try:
            target_dir = os.path.dirname(path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            ext = os.path.splitext(path)[1].lower()
            
            if ext == ".pdf":
                try:
                    from fpdf import FPDF
                    
                    pdf_theme = "light"
                    if hasattr(self, 'config') and self.config:
                        try:
                            pdf_theme = self.config.get("PDF_THEME", "light")
                        except (KeyError, AttributeError, RuntimeError):
                            pdf_theme = "light"
                    
                    font_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Resources", "DejaVuSansCondensed.ttf")
                    if not os.path.exists(font_path):
                        font_path = os.path.join(os.getcwd(), "Resources", "DejaVuSansCondensed.ttf")
                    if not os.path.exists(font_path):
                        font_path = os.path.join(os.getcwd(), "DejaVuSansCondensed.ttf")
                    
                    pdf = FPDF()
                    pdf.set_author("Maxim Melnikov")
                    pdf.set_creator("Secure Pass Pro v4.0")
                    pdf.set_title("Secure Pass Pro Password")
                    
                    if os.path.exists(font_path):
                        pdf.add_font('DejaVu', '', font_path, uni=True)
                        font_name = 'DejaVu'
                    else:
                        font_name = 'Helvetica'
                    
                    pdf.add_page()
                    
                    date_label = L.get("pdf_date", "Date")
                    password_label = L.get("pdf_pass", "Password")
                    date_label = date_label.strip()
                    password_label = password_label.strip()
                    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    if pdf_theme == "dark":
                        pdf.set_fill_color(30, 30, 46)
                        pdf.set_text_color(200, 200, 200)
                        pdf.set_draw_color(45, 106, 79)
                        pdf.rect(0, 0, 210, 297, 'F')
                        pdf.set_text_color(78, 201, 176)
                        pdf.set_font(font_name, '', 14)
                        pdf.cell(0, 10, "Secure Pass Pro v4.0", 0, 1, 'C')
                        pdf.ln(5)
                        pdf.set_font(font_name, '', 11)
                        pdf.cell(0, 10, f"{date_label}: {current_date}", 0, 1)
                        pdf.cell(0, 10, f"{password_label}: {pwd}", 0, 1)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                        pdf.set_text_color(0, 0, 0)
                        pdf.set_font(font_name, '', 14)
                        pdf.cell(0, 10, "Secure Pass Pro v4.0", 0, 1, 'C')
                        pdf.ln(5)
                        pdf.set_font(font_name, '', 11)
                        pdf.cell(0, 10, f"{date_label}: {current_date}", 0, 1)
                        pdf.cell(0, 10, f"{password_label}: {pwd}", 0, 1)
                    
                    pdf.output(path)
                except ImportError:
                    CTkMessageBox.error(self, L.get("err_title", "Error"), L.get("err_pdf_module", "PDF export requires fpdf module: pip install fpdf2"))
                    return
            else:
                current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                date_label = L.get("export_date", "Date")
                password_label = L.get("export_password_label", "Password")
                file_content = f"{date_label}: {current_date}\n{password_label}: {pwd}"
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                    f.flush()
                    os.fsync(f.fileno())

            if os.path.exists(path) and os.path.getsize(path) > 0:
                self._play_sound("success")
                fname = os.path.basename(path)
                self.title(fname)
                self.after(3000, lambda: self.title(L.get("win_title", "Secure Pass Pro v4.0")))
                CTkMessageBox.info(self, L.get("export_title", "Save"), L.get("file_saved", "File saved: {0}").format(fname))
            else:
                raise IOError(L.get("err_file_not_created", "File was not created properly"))

        except PermissionError as e:
            CTkMessageBox.error(self, L.get("err_title", "Error"), L.get("err_permission", "No write permission: {0}").format(e))
        except (OSError, IOError, PermissionError, ValueError, TypeError, RuntimeError) as e:
            logger.error(f"Save error: {e}")
            CTkMessageBox.error(self, L.get("err_title", "Error"), L.get("err_save", "Save failed: {0}").format(e))

    def _open(self) -> None:
        """
        Handle open.
        Обработать open.
        Обробити open.
        """
        L = LANGUAGES.get(self.current_lang, LANGUAGES["RU"])
        self.attributes("-topmost", False)
        self.update_idletasks()
        path = filedialog.askopenfilename(
            parent=self,
            title=L.get("open_title", "Select password file"),
            filetypes=[
                (L.get("export_all", "All Files"), "*.*"),
                (L.get("export_text", "Text Files"), "*.txt"),
                (L.get("export_password", "Password Files"), "*.key"),
                (L.get("export_log", "Log Files"), "*.log"),
                (L.get("export_pdf", "PDF Files"), "*.pdf")
            ]
        )
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == ".pdf":
                import subprocess
                import platform
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":
                    subprocess.run(["open", path], check=False)
                else:
                    subprocess.run(["xdg-open", path], check=False)
                self._play_sound()
                return
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            lines = content.split('\n')
            password = None
            for line in lines:
                line_lower = line.lower()
                if 'password:' in line_lower or 'пароль:' in line_lower:
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        password = parts[1].strip()
                        break
            
            if password is None:
                password = content
            
            if not password:
                raise ValueError(L.get("err_file_empty", "File is empty"))
            if len(password) > MAX_PASSWORD_LENGTH:
                password = password[:MAX_PASSWORD_LENGTH]
            sanitized_content = self._sanitize_import_content(password)
            self.entry_res.delete(0, "end")
            self.entry_res.insert(0, sanitized_content)
            self._update_strength_meter(sanitized_content)
            self._play_sound()
        except (OSError, IOError, PermissionError, UnicodeDecodeError, ValueError, TypeError, RuntimeError) as e:
            CTkMessageBox.error(self, L.get("err_title", "Error"), L.get("err_open", "Could not read file: {0}").format(e))