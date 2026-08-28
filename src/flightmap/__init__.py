from .osmviewer import OSMViewer

import tkinter as tk
import logging

# Inspired by https://www.pythontutorials.net/blog/how-can-i-display-osm-tiles-using-python/


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    root = tk.Tk()
    root.attributes("-fullscreen", True)
    app = OSMViewer(root, use_state_cache=True)
    root.mainloop()
