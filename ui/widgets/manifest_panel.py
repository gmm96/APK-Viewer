"""
"Manifest.xml" tab: read-only text view with a minimal XML syntax highlighter.
"""
import re
import tkinter as tk
from tkinter import ttk

from config import (
    COLOR_TEXT_BG,
    COLOR_XML_ATTR,
    COLOR_XML_COMMENT,
    COLOR_XML_TAG,
    COLOR_XML_VALUE,
    FONT_MONO,
    FONT_MONO_SMALL_ITALIC,
)
from ui.context_menu import TextContextMenu

_TAG_RE = re.compile(r"<[^>]+>")
_ATTR_RE = re.compile(r"([a-zA-Z0-9_:-]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


class ManifestPanel(ttk.Frame):
    def __init__(self, parent, context_menu: TextContextMenu):
        super().__init__(parent)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.text = tk.Text(self, wrap=tk.NONE, font=FONT_MONO, borderwidth=0, bg=COLOR_TEXT_BG)
        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)

        self.text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        self._configure_tags()
        context_menu.attach(self.text)

    def _configure_tags(self):
        self.text.tag_configure("xml_tag", foreground=COLOR_XML_TAG)
        self.text.tag_configure("xml_attr", foreground=COLOR_XML_ATTR)
        self.text.tag_configure("xml_value", foreground=COLOR_XML_VALUE)
        self.text.tag_configure("xml_comment", foreground=COLOR_XML_COMMENT, font=FONT_MONO_SMALL_ITALIC)

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete(1.0, tk.END)

    def render(self, manifest_xml: str):
        self.clear()
        self.text.insert(tk.END, manifest_xml)
        self._highlight(manifest_xml)
        self.text.configure(state="disabled")

    # --- Syntax highlighting -----------------------------------------------

    def _highlight(self, content: str):
        for match in _TAG_RE.finditer(content):
            self._tag_range("xml_tag", match.start(), match.end())
            self._highlight_attributes(match)

        for match in _COMMENT_RE.finditer(content):
            self._tag_range("xml_comment", match.start(), match.end())
            self.text.tag_raise("xml_comment")

    def _highlight_attributes(self, tag_match: "re.Match"):
        tag_str = tag_match.group()
        base = tag_match.start()
        for attr_match in _ATTR_RE.finditer(tag_str):
            self._tag_range("xml_attr", base + attr_match.start(1), base + attr_match.end(1))
            self._tag_range("xml_value", base + attr_match.start(2), base + attr_match.end(2))

    def _tag_range(self, tag_name: str, start: int, end: int):
        self.text.tag_add(tag_name, f"1.0 + {start} chars", f"1.0 + {end} chars")
