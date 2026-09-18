"""
"Information" tab: renders the analysis sections (app info, security,
components, trackers) as read-only entry fields and scrollable list boxes.
"""
import tkinter as tk
from tkinter import ttk

from config import COLOR_MARK_BG, COLOR_TEXT_BG, FONT_MONO_SMALL, LABEL_WIDTH, MIN_LIST_LINES
from ui.context_menu import TextContextMenu
from ui.scrollable_frame import ScrollableFrame
from utils.ui_helpers import make_autohide_scroll_command


class InfoPanel(ttk.Frame):
    def __init__(self, parent, context_menu: TextContextMenu, on_intent_double_click):
        super().__init__(parent)
        self._context_menu = context_menu
        self._on_intent_double_click = on_intent_double_click

        self.scroll_frame = ScrollableFrame(self)
        self.scroll_frame.pack(expand=True, fill=tk.BOTH)

    def clear(self):
        for widget in self.scroll_frame.inner_frame.winfo_children():
            widget.destroy()

    def render(self, sections: dict):
        self.clear()
        container = self.scroll_frame.inner_frame
        container.columnconfigure(0, weight=1)

        for row_idx, (section_title, fields) in enumerate(sections.items()):
            frame = ttk.LabelFrame(container, text=section_title)
            frame.grid(row=row_idx, column=0, sticky="ew", padx=15, pady=10)

            for inner_row, (label, value) in enumerate(fields.items()):
                if isinstance(value, list):
                    self._add_list_field(frame, inner_row, label, value)
                else:
                    self._add_entry_field(frame, inner_row, label, value)

    # --- Field builders ---------------------------------------------------

    def _add_entry_field(self, parent, row, label_text, value):
        ttk.Label(parent, text=label_text, width=LABEL_WIDTH).grid(row=row, column=0, sticky="w", padx=10, pady=5)

        entry = ttk.Entry(parent)
        entry.insert(0, str(value) if value is not None else "")
        entry.configure(state="readonly")
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        parent.columnconfigure(1, weight=1)

    def _add_list_field(self, parent, row, label_text, items):
        ttk.Label(parent, text=f"{label_text} ({len(items)})", width=LABEL_WIDTH).grid(
            row=row, column=0, sticky="nw", padx=10, pady=5
        )

        separator = "\n\n" if "Certificates" in label_text else "\n"
        display_text = separator.join(items) if items else "None found"

        line_count = max(display_text.count("\n") + 1, MIN_LIST_LINES)
        display_text += "\n" * (line_count - (display_text.count("\n") + 1))

        container = ttk.Frame(parent)
        container.grid(row=row, column=1, sticky="ew", padx=10, pady=5)
        parent.columnconfigure(1, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        text_widget = tk.Text(
            container, height=line_count, wrap=tk.NONE, borderwidth=1,
            relief="solid", bg=COLOR_TEXT_BG, font=FONT_MONO_SMALL,
        )
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=text_widget.xview)
        text_widget.configure(
            xscrollcommand=make_autohide_scroll_command(h_scroll, {"row": 1, "column": 0, "sticky": "ew"})
        )
        text_widget.grid(row=0, column=0, sticky="ew")

        text_widget.insert(tk.END, display_text)
        text_widget.configure(state="disabled")
        text_widget.tag_configure("marked_line", background=COLOR_MARK_BG)

        text_widget.bind("<Button-1>", lambda e: e.widget.tag_remove("marked_line", "1.0", tk.END))
        text_widget.bind("<ButtonRelease-1>", self._mark_clicked_line)
        self._context_menu.attach(text_widget)

        if label_text == "Intent Actions":
            text_widget.bind("<Double-Button-1>", self._handle_intent_double_click)

    # --- Interaction handlers ----------------------------------------------

    @staticmethod
    def _mark_clicked_line(event):
        widget = event.widget
        if widget.tag_ranges(tk.SEL):
            return  # a drag-selection is in progress; don't override it

        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split(".")[0]
        widget.tag_remove("marked_line", "1.0", tk.END)
        widget.tag_add("marked_line", f"{line_num}.0", f"{line_num}.end")

    def _handle_intent_double_click(self, event):
        widget = event.widget
        index = widget.index(f"@{event.x},{event.y}")
        line_num = index.split(".")[0]
        line_text = widget.get(f"{line_num}.0", f"{line_num}.end").strip()

        if line_text and line_text != "None found":
            self._on_intent_double_click(line_text)
