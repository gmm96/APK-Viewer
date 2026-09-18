"""
Highlights the line under the cursor when the user single-clicks inside a
read-only Text widget (without dragging a selection). Used by the list
fields in the Information tab so users can mark + copy one line at a time.
"""
import tkinter as tk

from config import COLOR_MARK_BG, MARKED_LINE_TAG


class TextLineMarker:
    def __init__(self, tag_name: str = MARKED_LINE_TAG, mark_color: str = COLOR_MARK_BG):
        self._tag_name = tag_name
        self._mark_color = mark_color

    def bind(self, text_widget: tk.Text) -> None:
        text_widget.tag_configure(self._tag_name, background=self._mark_color)
        text_widget.bind("<Button-1>", lambda e: e.widget.tag_remove(self._tag_name, "1.0", tk.END))
        text_widget.bind("<ButtonRelease-1>", self._on_release)

    def _on_release(self, event):
        widget = event.widget
        if widget.tag_ranges(tk.SEL):
            return  # a drag-selection is in progress; don't override it

        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split(".")[0]
        widget.tag_remove(self._tag_name, "1.0", tk.END)
        widget.tag_add(self._tag_name, f"{line_num}.0", f"{line_num}.end")
