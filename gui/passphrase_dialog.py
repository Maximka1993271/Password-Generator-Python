"""
Passphrase Generator Dialog for SecurePassPro
Диалог генератора парольных фраз для SecurePassPro
Діалог генератора парольних фраз для SecurePassPro

This dialog provides Diceware-style passphrase generation without modifying existing UI.

FIXED: Added full type hints for all methods
"""
from __future__ import annotations

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple, Union, Callable, cast

import customtkinter as ctk

from utils.passphrase_generator import (
    PassphraseGenerator,
    DEFAULT_WORD_COUNT,
    DEFAULT_SEPARATOR,
    DEFAULT_CAPITALIZE,
    DEFAULT_ADD_NUMBER,
    MIN_WORD_COUNT,
    MAX_WORD_COUNT,
)
from utils.logger import get_logger
from Langs.lang import LANGUAGES
from gui.dialogs import CTkMessageBox
from utils.helpers import get_global_radius, play_sound

logger = get_logger("passphrase_dialog")


class PassphraseDialog:
    """
    Dialog for generating Diceware-style passphrases.
    Диалог для генерации парольных фраз в стиле Diceware.
    Діалог для генерації парольних фраз у стилі Diceware.
    """
    
    def __init__(self, parent: ctk.CTkToplevel, lang: str = "RU", theme: str = "dark") -> None:
        """
        Initialise the instance.
        Инициализировать экземпляр.
        Ініціалізувати екземпляр.
        """
        self.parent: ctk.CTkToplevel = parent
        self.lang: str = lang
        self.theme: str = theme
        self.window: Optional[ctk.CTkToplevel] = None
        self.result_text: Optional[ctk.CTkTextbox] = None
        self.result_list: List[str] = []
        
        # Settings variables
        self.word_count_var: tk.IntVar = tk.IntVar(value=DEFAULT_WORD_COUNT)
        self.separator_var: tk.StringVar = tk.StringVar(value=DEFAULT_SEPARATOR)
        self.capitalize_var: tk.BooleanVar = tk.BooleanVar(value=DEFAULT_CAPITALIZE)
        self.add_number_var: tk.BooleanVar = tk.BooleanVar(value=DEFAULT_ADD_NUMBER)
        self.number_position_var: tk.StringVar = tk.StringVar(value="end")
        self.count_var: tk.IntVar = tk.IntVar(value=5)
        
        # Internal state
        self._neon_frames: List[ctk.CTkFrame] = []
        self._neon_active: bool = True
        self._generation_in_progress: bool = False
        self._cancel_requested: bool = False
        self._generation_thread: Optional[threading.Thread] = None
        self._generated_names: set = set()  # For duplicate tracking if needed
        
        self._create_window()
    
    def _get_text(self, key: str, default: str = "") -> str:
        """Get localized text."""
        L: Dict[str, str] = LANGUAGES.get(self.lang, LANGUAGES["RU"])
        return L.get(key, default)
    
    def _create_window(self) -> None:
        """Create the passphrase generator dialog window."""
        L: Dict[str, str] = LANGUAGES.get(self.lang, LANGUAGES["RU"])
        radius: int = get_global_radius()
        
        # Theme colors
        if self.theme == "light":
            bg_color: str = "#F3F3F3"
            fg_color: str = "#000000"
            entry_bg: str = "#FFFFFF"
            frame_bg: str = "#F3F3F3"
        else:
            bg_color = "#1d1e1e"
            fg_color = "#FFFFFF"
            entry_bg = "#2b2b2b"
            frame_bg = "#1d1e1e"
        
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title(L.get("passphrase_title", "Passphrase Generator / Генератор парольных фраз / Генератор парольних фраз"))
        self.window.geometry("650x750")
        self.window.minsize(600, 700)
        self.window.resizable(True, True)
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.lift()
        self.window.focus_force()
        self.window.after(100, lambda: self.window.attributes("-topmost", False) if self.window and self.window.winfo_exists() else None)
        self.window.attributes("-topmost", True)
        
        # Center window
        self.window.update_idletasks()
        x: int = self.parent.winfo_x() + (self.parent.winfo_width() - 650) // 2
        y: int = self.parent.winfo_y() + (self.parent.winfo_height() - 750) // 2
        if x < 0:
            x = 10
        if y < 30:
            y = 30
        self.window.geometry(f"650x750+{x}+{y}")
        
        self.window.configure(fg_color=bg_color)
        
        # Main frame
        main_frame: ctk.CTkFrame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label: ctk.CTkLabel = ctk.CTkLabel(
            main_frame,
            text=L.get("passphrase_title", "Passphrase Generator / Генератор парольных фраз / Генератор парольних фраз"),
            font=("Segoe UI", 20, "bold"),
            text_color=fg_color
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label: ctk.CTkLabel = ctk.CTkLabel(
            main_frame,
            text=L.get("passphrase_desc", 
                "Generate secure passphrases using the Diceware method.\n"
                "Each word adds ~13 bits of entropy.\n"
                "A 6-word passphrase provides ~78 bits of entropy.",
                "Генерируйте безопасные парольные фразы методом Diceware.\n"
                "Каждое слово добавляет ~13 бит энтропии.\n"
                "Фраза из 6 слов даёт ~78 бит энтропии.",
                "Генеруйте безпечні парольні фрази методом Diceware.\n"
                "Кожне слово додає ~13 біт ентропії.\n"
                "Фраза з 6 слів дає ~78 біт ентропії."),
            font=("Segoe UI", 12),
            text_color=fg_color,
            wraplength=550,
            justify="center"
        )
        desc_label.pack(pady=(0, 15))
        
        # Separator
        ctk.CTkFrame(main_frame, height=2, fg_color="#2d6a4f").pack(fill="x", pady=(0, 15))
        
        # Settings frame
        settings_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color=frame_bg, corner_radius=radius)
        settings_frame.pack(fill="x", pady=(0, 15), padx=10)
        
        ctk.CTkLabel(
            settings_frame,
            text=L.get("passphrase_settings", "Settings / Настройки / Налаштування"),
            font=("Segoe UI", 16, "bold"),
            text_color=fg_color
        ).pack(pady=(10, 10))
        
        # Settings grid
        grid_frame: ctk.CTkFrame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        grid_frame.pack(padx=15, pady=(0, 15))
        
        # Row 1: Word count
        row1: ctk.CTkFrame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        ctk.CTkLabel(
            row1,
            text=L.get("passphrase_word_count", "Word count / Количество слов / Кількість слів") + ":",
            font=("Segoe UI", 13),
            text_color=fg_color,
            width=180,
            anchor="w"
        ).pack(side="left")
        
        word_count_slider: ctk.CTkSlider = ctk.CTkSlider(
            row1,
            from_=MIN_WORD_COUNT,
            to=MAX_WORD_COUNT,
            number_of_steps=MAX_WORD_COUNT - MIN_WORD_COUNT,
            width=200,
            command=self._on_word_count_change
        )
        word_count_slider.set(self.word_count_var.get())
        word_count_slider.pack(side="left", padx=(10, 10))
        
        self.word_count_label: ctk.CTkLabel = ctk.CTkLabel(
            row1,
            text=str(self.word_count_var.get()),
            font=("Segoe UI", 13, "bold"),
            text_color="#4EC9B0",
            width=40
        )
        self.word_count_label.pack(side="left")
        
        # Row 2: Separator
        row2: ctk.CTkFrame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        ctk.CTkLabel(
            row2,
            text=L.get("passphrase_separator", "Separator / Разделитель / Розділювач") + ":",
            font=("Segoe UI", 13),
            text_color=fg_color,
            width=180,
            anchor="w"
        ).pack(side="left")
        
        sep_options: List[str] = [" ", "-", "_", ".", "|", "~", "+", "="]
        sep_menu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            row2,
            values=sep_options,
            variable=self.separator_var,
            width=120,
            corner_radius=radius
        )
        sep_menu.pack(side="left", padx=(10, 10))
        
        # Row 3: Capitalize
        row3: ctk.CTkFrame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        cap_check: ctk.CTkCheckBox = ctk.CTkCheckBox(
            row3,
            text=L.get("passphrase_capitalize", "Capitalize each word / Заглавные буквы / Великі літери"),
            variable=self.capitalize_var,
            font=("Segoe UI", 13)
        )
        cap_check.pack(anchor="w", padx=(180, 0))
        
        # Row 4: Add number
        row4: ctk.CTkFrame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        row4.pack(fill="x", pady=5)
        num_check: ctk.CTkCheckBox = ctk.CTkCheckBox(
            row4,
            text=L.get("passphrase_add_number", "Add a random number / Добавить число / Додати число"),
            variable=self.add_number_var,
            font=("Segoe UI", 13),
            command=self._on_add_number_change
        )
        num_check.pack(anchor="w", padx=(180, 0))
        
        # Row 5: Number position (visible only when add_number is True)
        self.row5: ctk.CTkFrame = ctk.CTkFrame(grid_frame, fg_color="transparent")
        self.row5.pack(fill="x", pady=5)
        ctk.CTkLabel(
            self.row5,
            text=L.get("passphrase_number_position", "Number position / Позиция числа / Позиція числа") + ":",
            font=("Segoe UI", 13),
            text_color=fg_color,
            width=180,
            anchor="w"
        ).pack(side="left")
        
        pos_options: List[Tuple[str, str]] = [
            (L.get("passphrase_position_start", "Start / Начало / Початок"), "start"),
            (L.get("passphrase_position_end", "End / Конец / Кінець"), "end"),
            (L.get("passphrase_position_random", "Random / Случайно / Випадково"), "random")
        ]
        
        pos_frame: ctk.CTkFrame = ctk.CTkFrame(self.row5, fg_color="transparent")
        pos_frame.pack(side="left", padx=(10, 0))
        for text, value in pos_options:
            rb: ctk.CTkRadioButton = ctk.CTkRadioButton(
                pos_frame,
                text=text,
                variable=self.number_position_var,
                value=value,
                font=("Segoe UI", 12)
            )
            rb.pack(side="left", padx=5)
        
        # Initially hide number position row
        if not self.add_number_var.get():
            self.row5.pack_forget()
        
        # Separator
        ctk.CTkFrame(main_frame, height=1, fg_color="#333333").pack(fill="x", pady=(5, 10))
        
        # Count frame
        count_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color="transparent")
        count_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            count_frame,
            text=L.get("passphrase_generate_count", "Number of phrases / Количество фраз / Кількість фраз") + ":",
            font=("Segoe UI", 13),
            text_color=fg_color
        ).pack(side="left", padx=(10, 10))
        
        count_options: List[str] = ["1", "2", "3", "4", "5", "10"]
        count_menu: ctk.CTkOptionMenu = ctk.CTkOptionMenu(
            count_frame,
            values=count_options,
            variable=self.count_var,
            width=100,
            corner_radius=radius
        )
        count_menu.pack(side="left")
        
        # Entropy info
        self.entropy_label: ctk.CTkLabel = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 12),
            text_color="#888888"
        )
        self.entropy_label.pack(pady=(0, 10))
        self._update_entropy_display()
        
        # Buttons
        button_frame: ctk.CTkFrame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        generate_btn: ctk.CTkButton = ctk.CTkButton(
            button_frame,
            text=L.get("passphrase_generate", "Generate / Сгенерировать / Згенерувати"),
            command=self._generate,
            fg_color="#00C853",
            hover_color="#00E676",
            height=40,
            corner_radius=radius,
            font=("Segoe UI", 14, "bold")
        )
        generate_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        copy_btn: ctk.CTkButton = ctk.CTkButton(
            button_frame,
            text=L.get("passphrase_copy_all", "Copy All / Копировать всё / Копіювати всі"),
            command=self._copy_all,
            fg_color="#2196F3",
            hover_color="#64B5F6",
            height=40,
            corner_radius=radius,
            font=("Segoe UI", 14, "bold")
        )
        copy_btn.pack(side="left", expand=True, fill="x")
        
        clear_btn: ctk.CTkButton = ctk.CTkButton(
            button_frame,
            text=L.get("passphrase_clear", "Clear / Очистить / Очистити"),
            command=self._clear,
            fg_color="#FF9800",
            hover_color="#FFB74D",
            height=40,
            corner_radius=radius,
            font=("Segoe UI", 14, "bold")
        )
        clear_btn.pack(side="left", padx=(10, 0), expand=True, fill="x")
        
        # Result text box
        self.result_text = ctk.CTkTextbox(
            main_frame,
            height=300,
            font=("Consolas", 14),
            corner_radius=radius,
            border_spacing=12,
            fg_color=entry_bg,
            text_color=fg_color
        )
        self.result_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Close button
        close_btn: ctk.CTkButton = ctk.CTkButton(
            main_frame,
            text=L.get("close", "Close / Закрыть / Закрити"),
            command=self._close,
            fg_color="#8b0000",
            hover_color="#cc0000",
            height=38,
            width=140,
            corner_radius=radius,
            font=("Segoe UI", 13, "bold")
        )
        close_btn.pack(pady=(0, 5))
        
        # Remove topmost after window is shown
        self.window.after(100, lambda: self.window.attributes("-topmost", False))
        
        # Generate initial passphrases
        self._generate()
    
    def _on_word_count_change(self, value: float) -> None:
        """Handle word count slider change."""
        count: int = int(value)
        self.word_count_var.set(count)
        self.word_count_label.configure(text=str(count))
        self._update_entropy_display()
    
    def _on_add_number_change(self) -> None:
        """Handle add number checkbox change."""
        if self.add_number_var.get():
            self.row5.pack(fill="x", pady=5)
        else:
            self.row5.pack_forget()
    
    def _update_entropy_display(self) -> None:
        """Update the entropy information display."""
        L: Dict[str, str] = LANGUAGES.get(self.lang, LANGUAGES["RU"])
        word_count: int = self.word_count_var.get()
        entropy: float = PassphraseGenerator.get_entropy_bits(word_count)
        
        # Determine strength level
        if entropy < 60:
            strength: str = L.get("strength_weak", "Weak / Слабый / Слабкий")
            color: str = "#FF4444"
        elif entropy < 80:
            strength = L.get("strength_medium", "Medium / Средний / Середній")
            color = "#FFA500"
        else:
            strength = L.get("strength_strong", "Strong / Надёжный / Надійний")
            color = "#2ECC71"
        
        self.entropy_label.configure(
            text=f"{L.get('passphrase_entropy', 'Entropy / Энтропия / Ентропія')}: {entropy:.1f} bits ({strength})",
            text_color=color
        )
    
    def _generate(self) -> None:
        """Generate passphrases and display them."""
        L: Dict[str, str] = LANGUAGES.get(self.lang, LANGUAGES["RU"])
        
        word_count: int = self.word_count_var.get()
        separator: str = self.separator_var.get()
        capitalize: bool = self.capitalize_var.get()
        add_number: bool = self.add_number_var.get()
        number_position: str = self.number_position_var.get()
        count: int = self.count_var.get()
        
        # Clear previous results
        self.result_list = []
        
        try:
            for _ in range(count):
                passphrase: str = PassphraseGenerator.generate(
                    word_count=word_count,
                    separator=separator,
                    capitalize=capitalize,
                    add_number=add_number,
                    number_position=number_position
                )
                self.result_list.append(passphrase)
            
            # Display results
            self.result_text.delete("1.0", tk.END)
            if count == 1:
                self.result_text.insert("1.0", self.result_list[0])
            else:
                self.result_text.insert("1.0", "\n".join(self.result_list))
            
            play_sound("generate", True)
            
        except (ValueError, TypeError, OSError, MemoryError, KeyError) as e:
            logger.error(f"Passphrase generation error: {e}")
            CTkMessageBox.error(
                self.window,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"{L.get('passphrase_error', 'Failed to generate passphrase')}:\n{str(e)}"
            )
    
    def _copy_all(self) -> None:
        """Copy all generated passphrases to clipboard."""
        L: Dict[str, str] = LANGUAGES.get(self.lang, LANGUAGES["RU"])
        
        if not self.result_list:
            CTkMessageBox.warning(
                self.window,
                L.get("warn", "Warning / Внимание / Увага"),
                L.get("passphrase_nothing_to_copy", "Nothing to copy. Generate passphrases first.")
            )
            return
        
        text: str = "\n".join(self.result_list)
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            play_sound("copy", True)
            CTkMessageBox.info(
                self.window,
                L.get("passphrase_copied_title", "Copied / Скопировано / Скопійовано"),
                L.get("passphrase_copied", "Passphrases copied to clipboard!")
            )
        except (RuntimeError, AttributeError, OSError, tk.TclError) as e:
            logger.error(f"Copy error: {e}")
            CTkMessageBox.error(
                self.window,
                L.get("err_title", "Error / Ошибка / Помилка"),
                f"{L.get('err_copy', 'Copy error')}: {str(e)}"
            )
    
    def _clear(self) -> None:
        """Clear the result text box."""
        self.result_text.delete("1.0", tk.END)
        self.result_list = []
    
    def _close(self) -> None:
        """Close the dialog window."""
        if self.window:
            self.window.destroy()
            self.window = None
    
    def show(self) -> None:
        """Show the dialog and wait for it to close."""
        if self.window:
            self.parent.wait_window(self.window)


def show_passphrase_dialog(
    parent: ctk.CTkToplevel,
    lang: str = "RU",
    theme: str = "dark"
) -> None:
    """
    Convenience function to show the passphrase generator dialog.
    
    Args:
        parent: Parent window
        lang: Language code (RU, EN, UA)
        theme: Theme (light/dark)
    """
    dialog: PassphraseDialog = PassphraseDialog(parent, lang, theme)
    dialog.show()


__all__: List[str] = [
    'PassphraseDialog',
    'show_passphrase_dialog',
]