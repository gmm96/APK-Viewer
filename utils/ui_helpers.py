"""
Small reusable Tkinter UI helpers shared by several widgets.
"""
import tkinter as tk
from tkinter import ttk

from config import COLOR_PLACEHOLDER_BG, COLOR_PLACEHOLDER_BORDER, ICON_SIZE
from utils.optional_deps import HAS_PIL, Image, ImageDraw, ImageTk


def create_placeholder_icon():
    """Build a neutral placeholder image shown before an APK icon is loaded."""
    if HAS_PIL:
        img = Image.new("RGB", ICON_SIZE, color=COLOR_PLACEHOLDER_BG)
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [0, 0, ICON_SIZE[0] - 1, ICON_SIZE[1] - 1],
            outline=COLOR_PLACEHOLDER_BORDER,
            width=2,
        )
        return ImageTk.PhotoImage(img)
    return tk.PhotoImage(width=ICON_SIZE[0], height=ICON_SIZE[1])


def make_autohide_scroll_command(scrollbar: ttk.Scrollbar, grid_kwargs: dict):
    """
    Return a callback suitable for `xscrollcommand` (or `yscrollcommand`) that
    hides the given scrollbar whenever the whole content is already visible,
    and re-shows it (re-gridding with `grid_kwargs`) otherwise.
    """
    def _on_scroll(first, last):
        if float(first) <= 0.0 and float(last) >= 1.0:
            scrollbar.grid_remove()
        else:
            scrollbar.grid(**grid_kwargs)
        scrollbar.set(first, last)

    return _on_scroll
