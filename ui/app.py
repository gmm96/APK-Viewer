"""
Main application window: wires together the header, status bar, tabs and
the background analysis pipeline.
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import apk_service, file_tree_service, manifest_service
from ui.context_menu import TextContextMenu
from ui.header import AppHeader
from ui.status_bar import StatusBar
from ui.widgets.files_panel import FilesPanel
from ui.widgets.info_panel import InfoPanel
from ui.widgets.intent_dialog import open_intent_dialog
from ui.widgets.manifest_panel import ManifestPanel


class ApkAnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("APKViewer")
        self.root.geometry("1000x750")

        self._configure_style()
        self.context_menu = TextContextMenu(root)
        self._build_layout()

    def _configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=(20, 2))
        style.map("TNotebook.Tab", padding=[("selected", (20, 3))])

    def _build_layout(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=15)
        self.header = AppHeader(top_frame, on_load_click=self.load_apk)
        self.header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))

        self.info_panel = InfoPanel(notebook, self.context_menu, on_intent_double_click=self._show_intent_dialog)
        notebook.add(self.info_panel, text="Information")

        self.manifest_panel = ManifestPanel(notebook, self.context_menu)
        notebook.add(self.manifest_panel, text="Manifest.xml")

        self.files_panel = FilesPanel(notebook)
        notebook.add(self.files_panel, text="Files")

    # --- Public actions ----------------------------------------------------

    def load_apk(self):
        apk_path = filedialog.askopenfilename(
            title="Select APK file",
            filetypes=[("APK files", "*.apk"), ("All files", "*.*")],
        )
        if apk_path:
            self.start_analysis(apk_path)

    def start_analysis(self, apk_path: str):
        if not os.path.exists(apk_path):
            messagebox.showerror("Error", f"File not found:\n{apk_path}")
            return

        self._set_status(f"Analyzing: {os.path.basename(apk_path)}... (Please wait)", "blue")
        self.header.set_loading_enabled(False)
        self.header.reset_to_placeholder(os.path.basename(apk_path))

        self.info_panel.clear()
        self.manifest_panel.clear()
        self.files_panel.clear()

        threading.Thread(target=self._analyze_in_background, args=(apk_path,), daemon=True).start()

    # --- Background worker (runs off the Tk main thread) --------------------

    def _analyze_in_background(self, apk_path: str):
        try:
            result = apk_service.analyze(apk_path)
            manifest_xml = manifest_service.format_manifest(result["apk"])
            file_tree = file_tree_service.build_file_tree(apk_path)

            self.root.after(0, lambda: self._render_result(result, manifest_xml, file_tree))
            self._set_status("Analysis completed successfully.", "green")
        except Exception as exc:
            self.root.after(
                0, lambda: messagebox.showerror("Error", f"An error occurred while analyzing the APK:\n{exc}")
            )
            self.root.after(0, self.header.show_error)
            self._set_status("Analysis failed.", "red")
        finally:
            self.root.after(0, lambda: self.header.set_loading_enabled(True))

    # --- UI updates (must run on the Tk main thread) ------------------------

    def _set_status(self, message: str, color: str = "gray"):
        self.root.after(0, lambda: self.status_bar.set_status(message, color))

    def _render_result(self, result: dict, manifest_xml: str, file_tree: dict):
        app_info = result["sections"].get("App Information", {})
        self.header.show_result(
            app_name=app_info.get("App name"),
            package_name=app_info.get("Package name"),
            icon_image=result["icon"],
        )
        self.info_panel.render(result["sections"])
        self.manifest_panel.render(manifest_xml)
        self.files_panel.set_tree(file_tree)

    def _show_intent_dialog(self, line_text: str):
        open_intent_dialog(self.root, line_text)
