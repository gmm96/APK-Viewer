"""
Popup dialog showing the parsed details of a single intent-filter action.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from config import FONT_MONO


class IntentActionParser:
    """Turns a formatted "action ( key='value', ... )" line back into a dict."""

    def parse(self, line_text: str) -> dict:
        action = line_text
        extras_str = ""

        if " ( " in action and action.endswith(" )"):
            action, extras_str = action.split(" ( ", 1)
            extras_str = extras_str[:-2]

        fields = {"Action": action}

        if extras_str:
            for extra in extras_str.split(", "):
                if "=" not in extra:
                    continue
                key, value = extra.split("=", 1)
                key = key.strip().capitalize()
                value = value.strip().strip("'").strip('"')

                if key in fields:
                    fields[key] += f", {value}"
                else:
                    fields[key] = value

        return fields


class IntentDetailsDialog:
    """Builds and shows the modal 'Intent Details' popup on demand."""

    def __init__(self, parent: tk.Misc, parser: IntentActionParser = None):
        self._parent = parent
        self._parser = parser or IntentActionParser()

    def open(self, line_text: str) -> None:
        try:
            fields = self._parser.parse(line_text)
            dialog = self._build_dialog(fields)
            self._center_on_parent(dialog)
            self._show(dialog)
        except Exception as exc:
            messagebox.showerror("Parse Error", f"Could not load intent details:\n{exc}")

    def _build_dialog(self, fields: dict) -> tk.Toplevel:
        dialog = tk.Toplevel(self._parent)
        dialog.title("Intent Details")
        dialog.minsize(550, 150)
        dialog.transient(self._parent)

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        row_idx = 0
        for label_text, value_text in fields.items():
            ttk.Label(main_frame, text=label_text, width=15).grid(row=row_idx, column=0, sticky="w", pady=5)

            entry = ttk.Entry(main_frame, font=FONT_MONO)
            entry.insert(0, str(value_text))
            entry.configure(state="readonly")
            entry.grid(row=row_idx, column=1, sticky="ew", pady=5, padx=(10, 0))

            main_frame.columnconfigure(1, weight=1)
            row_idx += 1

        ttk.Button(main_frame, text="Close", command=dialog.destroy).grid(
            row=row_idx, column=0, columnspan=2, pady=(20, 0)
        )
        return dialog

    def _center_on_parent(self, dialog: tk.Toplevel) -> None:
        dialog.update_idletasks()
        x = self._parent.winfo_x() + (self._parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self._parent.winfo_y() + (self._parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    @staticmethod
    def _show(dialog: tk.Toplevel) -> None:
        dialog.deiconify()
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after(150, lambda: dialog.attributes("-topmost", False))
        dialog.focus_force()
        dialog.grab_set()
