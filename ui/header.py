"""
Top header: app icon, name/package labels and the "Load APK" button.
"""
import tkinter as tk
from tkinter import ttk

from config import FONT_SUBTITLE, FONT_TITLE
from utils.optional_deps import HAS_PIL, ImageTk
from utils.ui_helpers import create_placeholder_icon


class AppHeader(ttk.Frame):
    def __init__(self, parent, on_load_click):
        super().__init__(parent)
        self._placeholder_icon = create_placeholder_icon()
        self._current_icon = None

        left = ttk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y)

        self.icon_label = ttk.Label(left, image=self._placeholder_icon)
        self.icon_label.pack(side=tk.LEFT, padx=(0, 15))

        text_frame = ttk.Frame(left)
        text_frame.pack(side=tk.LEFT, expand=True, fill=tk.Y)

        self.name_label = ttk.Label(text_frame, text="No APK Loaded", font=FONT_TITLE)
        self.name_label.pack(side=tk.TOP, anchor="sw", expand=True)

        self.package_label = ttk.Label(
            text_frame,
            text="Select an application file to begin analysis.",
            font=FONT_SUBTITLE,
            foreground="#666666",
        )
        self.package_label.pack(side=tk.TOP, anchor="nw", expand=True)

        self.load_button = ttk.Button(self, text="Load APK", command=on_load_click)
        self.load_button.pack(side=tk.RIGHT)

    def reset_to_placeholder(self, file_name: str):
        self._current_icon = None
        self.icon_label.config(image=self._placeholder_icon)
        self.name_label.config(text="Analyzing APK...")
        self.package_label.config(text=file_name)

    def show_error(self):
        self.name_label.config(text="Error loading APK")

    def set_loading_enabled(self, enabled: bool):
        self.load_button.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def show_result(self, app_name: str, package_name: str, icon_image=None):
        if icon_image is not None and HAS_PIL:
            self._current_icon = ImageTk.PhotoImage(icon_image)
            self.icon_label.config(image=self._current_icon)

        self.name_label.config(text=app_name or "Unknown App")
        self.package_label.config(text=package_name or "Unknown Package")
