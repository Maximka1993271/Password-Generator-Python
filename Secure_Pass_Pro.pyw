#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure Pass Pro v4.0 — Cryptographically secure password generator
Author: Maxim Melnikov
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        from gui.main_window import SecurePassPro
        import customtkinter as ctk
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        app = SecurePassPro()
        app.mainloop()
    except ImportError as e:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Required modules missing!\n\n{str(e)}\n\nMake sure all modules are in place.")
        sys.exit(1)