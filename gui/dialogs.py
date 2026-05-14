"""
Custom dialog windows (MessageBox, InputDialog)
"""
import tkinter as tk
import customtkinter as ctk
from localization.lang import LANGUAGES
from utils.helpers import get_global_radius, set_global_radius, center_screen


class CTkMessageBox:
    """Custom message box with theming"""
    
    _current_theme = "dark"
    _current_lang = "RU"
    
    @classmethod
    def set_theme(cls, theme: str) -> None:
        cls._current_theme = theme
    
    @classmethod
    def set_lang(cls, lang: str) -> None:
        cls._current_lang = lang
    
    @staticmethod
    def _get_colors(theme: str) -> dict:
        if theme == "light":
            return {
                "bg": "#F3F3F3", "fg": "#000000", "button_fg": "#1f538d",
                "button_text": "#FFFFFF", "label_text": "#000000", "entry_bg": "#FFFFFF"
            }
        return {
            "bg": "#1d1e1e", "fg": "#FFFFFF", "button_fg": "#1f538d",
            "button_text": "#FFFFFF", "label_text": "#FFFFFF", "entry_bg": "#2b2b2b"
        }
    
    @staticmethod
    def _show(parent, title: str, message: str, button_text: str = "OK", 
              icon: str = "ℹ️", icon_color: str = "#4EC9B0", 
              button_color: str = "#1f538d", is_question: bool = False):
        
        win = ctk.CTkToplevel(parent)
        win.title(title)
        win.resizable(False, False)
        win.grab_set()
        win.attributes("-topmost", True)
        
        colors = CTkMessageBox._get_colors(CTkMessageBox._current_theme)
        L = LANGUAGES.get(CTkMessageBox._current_lang, LANGUAGES["RU"])
        radius = get_global_radius()
        
        w, h = (420, 220) if is_question else (420, 200)
        center_screen(win, w, h)
        win.configure(fg_color=colors["bg"])
        
        ctk.CTkLabel(win, text=icon, font=("Segoe UI", 40), 
                    text_color=icon_color).pack(pady=(20, 5))
        ctk.CTkLabel(win, text=message, font=("Segoe UI", 13), 
                    wraplength=360, justify="center", 
                    text_color=colors["label_text"]).pack(pady=(0, 15))
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack()
        
        result = [None]
        
        if is_question:
            def on_yes(): result[0] = "yes"; win.destroy()
            def on_no(): result[0] = "no"; win.destroy()
            ctk.CTkButton(btn_frame, text=L.get("yes", "Да"), width=100, height=35, 
                         command=on_yes, fg_color="#2d6a4f", corner_radius=radius).pack(side="left", padx=8)
            ctk.CTkButton(btn_frame, text=L.get("no", "Нет"), width=100, height=35, 
                         command=on_no, fg_color="#8b0000", corner_radius=radius).pack(side="left", padx=8)
        else:
            def on_ok(): result[0] = "ok"; win.destroy()
            btn_text = button_text if button_text != "OK" else L.get("ok", "OK")
            ctk.CTkButton(btn_frame, text=btn_text, width=120, height=35, 
                         command=on_ok, fg_color=colors["button_fg"], 
                         corner_radius=radius).pack()
        
        win.after(100, lambda: win.attributes("-topmost", False))
        parent.wait_window(win)
        return result[0]
    
    @staticmethod
    def info(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="✅", icon_color="#2ECC71")
    
    @staticmethod
    def warning(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="⚠️", icon_color="#FFA500")
    
    @staticmethod
    def error(parent, title: str, message: str) -> None:
        CTkMessageBox._show(parent, title, message, icon="❌", icon_color="#FF4444")
    
    @staticmethod
    def question(parent, title: str, message: str) -> bool:
        result = CTkMessageBox._show(parent, title, message, is_question=True)
        return result == "yes"


class CTkInputDialog:
    """Custom input dialog"""
    
    def __init__(self, parent, title: str, prompt: str, show: str = "", 
                 theme: str = "dark", lang: str = "RU"):
        self.result = None
        self.win = ctk.CTkToplevel(parent)
        self.win.title(title)
        self.win.resizable(False, False)
        self.win.grab_set()
        self.win.attributes("-topmost", True)
        
        L = LANGUAGES.get(lang, LANGUAGES["RU"])
        radius = get_global_radius()
        
        if theme == "light":
            bg_color, fg_color, entry_bg, btn_fg = "#F3F3F3", "#000000", "#FFFFFF", "#1f538d"
        else:
            bg_color, fg_color, entry_bg, btn_fg = "#1d1e1e", "#FFFFFF", "#2b2b2b", "#1f538d"
        
        center_screen(self.win, 420, 220)
        self.win.configure(fg_color=bg_color)
        
        ctk.CTkLabel(self.win, text=prompt, font=("Segoe UI", 13), 
                    wraplength=360, text_color=fg_color).pack(padx=20, pady=(20, 8))
        
        self.entry = ctk.CTkEntry(self.win, width=360, height=40, font=("Segoe UI", 14), 
                                  show=show, fg_color=entry_bg, text_color=fg_color, 
                                  corner_radius=radius)
        self.entry.pack(padx=20, pady=(0, 12))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._ok())
        self.entry.bind("<Escape>", lambda e: self._cancel())
        
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack()
        ctk.CTkButton(btn_frame, text=L["ok"], width=110, height=36, 
                     command=self._ok, fg_color=btn_fg, corner_radius=radius).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text=L["cancel"], width=110, height=36, 
                     command=self._cancel, fg_color="#ca5010", corner_radius=radius).pack(side="left", padx=8)
        
        self.win.protocol("WM_DELETE_WINDOW", self._cancel)
        parent.wait_window(self.win)
    
    def _ok(self) -> None:
        self.result = self.entry.get()
        self.win.destroy()
    
    def _cancel(self) -> None:
        self.result = None
        self.win.destroy()
    
    @staticmethod
    def ask(parent, title: str, prompt: str, show: str = "", 
            theme: str = "dark", lang: str = "RU"):
        return CTkInputDialog(parent, title, prompt, show, theme, lang).result