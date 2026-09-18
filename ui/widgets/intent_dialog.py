"""
Popup dialog showing the parsed details of a single intent-filter action.
"""
import tkinter as tk
from tkinter import messagebox, ttk

from config import FONT_MONO


def open_intent_dialog(parent: tk.Misc, line_text: str):
    """Parse a formatted intent-action line and show it in a small dialog."""
    try:
        dialog = tk.Toplevel(parent)
        dialog.title("Intent Details")
        dialog.minsize(550, 150)
        dialog.transient(parent)

        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        fields = _parse_intent_line(line_text)

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

        _center_on_parent(dialog, parent)

        dialog.deiconify()
        dialog.lift()
        dialog.attributes("-topmost", True)
        dialog.after(150, lambda: dialog.attributes("-topmost", False))
        dialog.focus_force()
        dialog.grab_set()

    except Exception as exc:
        messagebox.showerror("Parse Error", f"Could not load intent details:\n{exc}")


def _parse_intent_line(line_text: str) -> dict:
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


def _center_on_parent(dialog: tk.Toplevel, parent: tk.Misc):
    dialog.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")
