"""
Small reusable Tkinter UI helper classes shared by several widgets.
"""
import tkinter as tk
from tkinter import ttk

from config import COLOR_PLACEHOLDER_BG, COLOR_PLACEHOLDER_BORDER, ICON_SIZE
from utils.optional_deps import HAS_PIL, Image, ImageDraw, ImageTk


class PlaceholderIconFactory:
    """Builds the neutral placeholder image shown before an APK icon is loaded."""

    def __init__(self, size=ICON_SIZE, bg_color=COLOR_PLACEHOLDER_BG, border_color=COLOR_PLACEHOLDER_BORDER):
        self._size = size
        self._bg_color = bg_color
        self._border_color = border_color

    def create(self):
        if HAS_PIL:
            img = Image.new("RGB", self._size, color=self._bg_color)
            draw = ImageDraw.Draw(img)
            draw.rectangle(
                [0, 0, self._size[0] - 1, self._size[1] - 1],
                outline=self._border_color,
                width=2,
            )
            return ImageTk.PhotoImage(img)
        return tk.PhotoImage(width=self._size[0], height=self._size[1])


class AutoHideScrollbar:
    """
    Wraps a ttk.Scrollbar so it hides itself (via grid_remove) whenever the
    whole content is already visible, and re-grids it otherwise. Bind its
    `scroll_command` method to a widget's xscrollcommand/yscrollcommand.
    """

    def __init__(self, scrollbar: ttk.Scrollbar, grid_kwargs: dict):
        self._scrollbar = scrollbar
        self._grid_kwargs = grid_kwargs

    def scroll_command(self, first, last):
        if float(first) <= 0.0 and float(last) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid(**self._grid_kwargs)
        self._scrollbar.set(first, last)
