"""
"Files" tab: hierarchical view of the APK's internal zip entries, with a
live text filter.
"""
import os
import tkinter as tk
from tkinter import ttk

from config import COLOR_FOLDER_BG, FONT_MONO_SMALL
from core.file_tree_service import filter_file_tree
from utils.formatting import human_size
from utils.ui_helpers import make_autohide_scroll_command


class FilesPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._tree_data = {}

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        self._build_treeview()
        self._build_filter_bar()

    def _build_treeview(self):
        columns = ("type", "size", "compressed", "modified")
        self.tree = ttk.Treeview(self, columns=columns, show="tree headings")

        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.column("#0", width=380, minwidth=200, stretch=True, anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.column("type", width=120, minwidth=80, stretch=False, anchor="w")
        self.tree.heading("size", text="Size", anchor="w")
        self.tree.column("size", width=100, minwidth=70, stretch=False, anchor="w")
        self.tree.heading("compressed", text="Compressed", anchor="w")
        self.tree.column("compressed", width=100, minwidth=70, stretch=False, anchor="w")
        self.tree.heading("modified", text="Modified", anchor="w")
        self.tree.column("modified", width=150, minwidth=130, stretch=False, anchor="w")

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=v_scroll.set,
            xscrollcommand=make_autohide_scroll_command(h_scroll, {"row": 1, "column": 0, "sticky": "ew"}),
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.tag_configure("folder", background=COLOR_FOLDER_BG, font=FONT_MONO_SMALL)
        self.tree.tag_configure("file", font=FONT_MONO_SMALL)

    def _build_filter_bar(self):
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)

        self.filter_entry = ttk.Entry(filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

    # --- Public API ----------------------------------------------------------

    def set_tree(self, tree_data: dict):
        self._tree_data = tree_data
        self.filter_entry.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
        self._populate(self._tree_data)

    def clear(self):
        self.tree.delete(*self.tree.get_children())
        self._tree_data = {}

    # --- Filtering / rendering -------------------------------------------

    def _apply_filter(self):
        query = self.filter_entry.get().strip().lower()
        self.tree.delete(*self.tree.get_children())

        if not query:
            self._populate(self._tree_data)
        else:
            self._populate(filter_file_tree(self._tree_data, query))

    def _populate(self, node_dict: dict, parent_iid: str = ""):
        entries = sorted(node_dict.items(), key=lambda kv: (kv[1].get("__is_file__", False), kv[0].lower()))

        for name, meta in entries:
            size_str = human_size(meta.get("__size__", 0))
            compressed_str = human_size(meta.get("__compressed__", 0))
            modified_str = meta.get("__modified__", "")

            if meta.get("__is_file__", False):
                ext = os.path.splitext(name)[1].lstrip(".").upper()
                type_label = f"{ext} File" if ext else "File"
                self.tree.insert(
                    parent_iid, tk.END, text=f" 📄 {name}",
                    values=(type_label, size_str, compressed_str, modified_str),
                    tags=("file",),
                )
            else:
                child_count = len(meta.get("__children__", {}))
                iid = self.tree.insert(
                    parent_iid, tk.END, text=f" 📁 {name}",
                    values=(f"Directory ({child_count})", size_str, compressed_str, modified_str),
                    open=True, tags=("folder",),
                )
                self._populate(meta.get("__children__", {}), iid)
