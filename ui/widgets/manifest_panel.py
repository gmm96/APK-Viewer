"""
"Manifest.xml" tab: read-only text view with XML syntax highlighting.
"""
import tkinter as tk
from tkinter import ttk

from config import COLOR_TEXT_BG, FONT_MONO
from ui.context_menu import TextContextMenu
from ui.widgets.xml_highlighter import XmlSyntaxHighlighter


class ManifestPanel(ttk.Frame):
    def __init__(self, parent, context_menu: TextContextMenu, highlighter: XmlSyntaxHighlighter = None):
        super().__init__(parent)
        self._highlighter = highlighter or XmlSyntaxHighlighter()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.text = tk.Text(self, wrap=tk.NONE, font=FONT_MONO, borderwidth=0, bg=COLOR_TEXT_BG)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)

        self.text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        self._highlighter.configure_tags(self.text)
        context_menu.attach(self.text)

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete(1.0, tk.END)

    def render(self, manifest_xml: str):
        self.clear()
        self.text.insert(tk.END, manifest_xml)
        self._highlighter.highlight(self.text, manifest_xml)
        self.text.configure(state="disabled")
