import json
from pathlib import Path
from time import sleep
from random import random

from .osm_webservices import get_tile
from .osmviewer import OSMViewer

import tkinter as tk
import logging

# Inspired by https://www.pythontutorials.net/blog/how-can-i-display-osm-tiles-using-python/

def main() -> None:
    #make_tilelist(41.571, -87.492, 200, 9)
    #get_tiles_from_tilelist(r"C:\Users\trex\Documents\code\flightmap\tiles-41_571--87_492-200-9")
    logging.basicConfig(level=logging.INFO)


    root = tk.Tk()
    root.attributes("-fullscreen", True)
    app = OSMViewer(root)
    root.mainloop()