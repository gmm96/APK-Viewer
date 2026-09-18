"""
Bottom status bar showing the current operation state.
"""
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, relief="sunken", borderwidth=1)
        self.label = ttk.Label(self, text="Ready.", foreground="gray")
        self.label.pack(side="left", padx=10, pady=2)

    def set_status(self, message: str, color: str = "gray"):
        self.label.config(text=message, foreground=color)
