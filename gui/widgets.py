"""
Custom GUI widgets
"""
import tkinter as tk


class ToolTip:
    """Tooltip for widgets"""
    
    def __init__(self, widget):
        self.widget = widget
        self.text = ""
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    
    def set_text(self, text: str) -> None:
        self.text = text
    
    def show_tip(self, event=None) -> None:
        if self.tip_window or not self.text:
            return
        try:
            if not self.widget.winfo_exists():
                return
        except Exception:
            return
        
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        tk.Label(tw, text=self.text, justify='left', background="#ffffe0", 
                relief='solid', borderwidth=1, font=("Segoe UI", 9, "normal")).pack(ipadx=1)
    
    def hide_tip(self, event=None) -> None:
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None
