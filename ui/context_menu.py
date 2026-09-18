"""
Right-click "Copy" context menu shared by every read-only Text widget in
the app (manifest viewer, list fields, etc.).
"""
import tkinter as tk

from config import MARKED_LINE_TAG


class TextContextMenu:
    """
    Attach to any Text widget with `attach(widget)`. Right-click will offer
    to copy the current selection, or the currently marked line if nothing
    is selected.
    """

    def __init__(self, root: tk.Misc):
        self._menu = tk.Menu(root, tearoff=0)
        self._menu.add_command(label="Copy Text", command=self._copy)
        self._active_widget = None

    def attach(self, widget: tk.Text):
        widget.bind("<Button-3>", self._show)

    def _show(self, event):
        self._active_widget = event.widget
        self._menu.tk_popup(event.x_root, event.y_root)

    def _copy(self):
        widget = self._active_widget
        if widget is None:
            return
        try:
            if widget.tag_ranges(tk.SEL):
                text_to_copy = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            else:
                marked = widget.tag_ranges(MARKED_LINE_TAG)
                text_to_copy = widget.get(marked[0], marked[1]) if marked else ""

            if text_to_copy:
                widget.clipboard_clear()
                widget.clipboard_append(text_to_copy)
        except Exception:
            pass
