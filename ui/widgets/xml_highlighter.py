"""
Minimal XML syntax highlighter applied to the Manifest.xml text view.
"""
import re
import tkinter as tk

from config import COLOR_XML_ATTR, COLOR_XML_COMMENT, COLOR_XML_TAG, COLOR_XML_VALUE, FONT_MONO_SMALL_ITALIC


class XmlSyntaxHighlighter:
    _TAG_RE = re.compile(r"<[^>]+>")
    _ATTR_RE = re.compile(r"([a-zA-Z0-9_:-]+)\s*=\s*(\"[^\"]*\"|'[^']*')")
    _COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

    def configure_tags(self, text_widget: tk.Text) -> None:
        text_widget.tag_configure("xml_tag", foreground=COLOR_XML_TAG)
        text_widget.tag_configure("xml_attr", foreground=COLOR_XML_ATTR)
        text_widget.tag_configure("xml_value", foreground=COLOR_XML_VALUE)
        text_widget.tag_configure("xml_comment", foreground=COLOR_XML_COMMENT, font=FONT_MONO_SMALL_ITALIC)

    def highlight(self, text_widget: tk.Text, content: str) -> None:
        for match in self._TAG_RE.finditer(content):
            self._tag_range(text_widget, "xml_tag", match.start(), match.end())
            self._highlight_attributes(text_widget, match)

        for match in self._COMMENT_RE.finditer(content):
            self._tag_range(text_widget, "xml_comment", match.start(), match.end())
            text_widget.tag_raise("xml_comment")

    def _highlight_attributes(self, text_widget: tk.Text, tag_match: "re.Match") -> None:
        tag_str = tag_match.group()
        base = tag_match.start()
        for attr_match in self._ATTR_RE.finditer(tag_str):
            self._tag_range(text_widget, "xml_attr", base + attr_match.start(1), base + attr_match.end(1))
            self._tag_range(text_widget, "xml_value", base + attr_match.start(2), base + attr_match.end(2))

    @staticmethod
    def _tag_range(text_widget: tk.Text, tag_name: str, start: int, end: int) -> None:
        text_widget.tag_add(tag_name, f"1.0 + {start} chars", f"1.0 + {end} chars")
