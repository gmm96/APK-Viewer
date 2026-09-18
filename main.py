"""
Entry point for the APKViewer desktop application.

Usage:
    python main.py [path/to/app.apk]
"""
import sys
import tkinter as tk

from ui.app import ApkAnalyzerApp


def main():
    root = tk.Tk()
    app = ApkAnalyzerApp(root)

    if len(sys.argv) > 1:
        root.after(100, lambda: app.start_analysis(sys.argv[1]))

    root.mainloop()


if __name__ == "__main__":
    main()
