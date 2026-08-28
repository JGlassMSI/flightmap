import tkinter as tk
from PIL import Image, ImageTk
import logging
import json
import math
from typing import Iterable

from opensky_api import StateVector

from .osm_webservices import OSM_TileGetter, CartoDB_TileGetter
from .conversion import deg2tile
from .opensky_utils import get_states
from .flights import filter_states, lat_long_zoom_to_tile
from .plane_icons import ImageManager


class OSMViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Local OSM Tile Viewer")

        with open("location.json", "r") as f:
            config = json.load(f)

        self.zoom = config["zoom"]
        self.center_lat = config["lat"]
        self.center_lon = config["lon"]
        self.filter_radius = config["filter_radius"]
        self.update_time = config.get("refresh_seconds", 60)  # seconds
        self.include_onground = config.get("include_onground", True)
        self.plane_size = config.get("plane_size", 25)

        # Default settings
        self.canvas_width = 1920  # Window width
        self.canvas_height = 1080  # Window height

        # Create canvas for drawing tiles
        self.canvas = tk.Canvas(
            root, width=self.canvas_width, height=self.canvas_height, bg="lightgray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_manager = ImageManager(self.plane_size)
        self.tile_getter = CartoDB_TileGetter(style="light_all")

        # Store references to images (prevents Tkinter garbage collection)
        self.tile_images = []
        self.plane_photoimages = []

        def on_escape(event=None):
            """Close the window when Escape is pressed."""
            self.root.destroy()

        # Bind escape key to quit
        self.root.bind("<Escape>", on_escape)

        # Initial map render
        self.render_map()
        self.update_loop()

    def update_loop(self):
        logging.debug("update_loop() is rendering planes")
        self.render_planes()
        self.root.after(self.update_time * 1000, self.update_loop)
        logging.debug(f"Planes will update in {self.update_time} seconds")

    def render_map(self):
        """Render tiles centered on self.center_lat/center_lon."""
        self.canvas.delete("tile")  # Clear previous tiles
        self.tile_images = []  # Reset image references

        # Get center tile (x, y)
        center_x, center_y = deg2tile(self.center_lat, self.center_lon, self.zoom)

        # Calculate how many tiles fit in the window (with padding)
        tiles_per_side = (
            int(self.canvas_width / 256) + 2,  # +2 to avoid edge gaps
            int(self.canvas_height / 256) + 2,
        )

        # Top-left tile to start drawing from
        start_x = center_x - (tiles_per_side[0] // 2)
        start_y = center_y - (tiles_per_side[1] // 2)

        # Draw tiles
        for x in range(start_x, start_x + tiles_per_side[0]):
            for y in range(start_y, start_y + tiles_per_side[1]):
                # Download/cache tile
                tile_path = self.tile_getter.get_tile(self.zoom, x, y)
                if not tile_path:
                    continue  # Skip if download failed
                # Load tile image
                img = Image.open(tile_path)
                photo = ImageTk.PhotoImage(img)
                self.tile_images.append(photo)  # Keep reference

                # Calculate position on canvas
                canvas_x = (x - start_x) * 256 - 128
                canvas_y = (y - start_y) * 256 - (self.canvas_height // 2 - 128)

                logging.debug(
                    f"Drawing tile ({x}, {y}) at canvas position ({canvas_x}, {canvas_y})"
                )

                # Draw tile
                self.canvas.create_image(
                    canvas_x, canvas_y, anchor=tk.NW, image=photo, tags=["tile"]
                )

    def tile_loc_to_screen(self, x: float, y: float) -> tuple[int, int]:
        # Get center tile (x, y)
        center_x, center_y = deg2tile(self.center_lat, self.center_lon, self.zoom)

        # Calculate how many tiles fit in the window (with padding)
        tiles_per_side = (
            int(self.canvas_width / 256) + 2,  # +2 to avoid edge gaps
            int(self.canvas_height / 256) + 2,
        )

        # Top-left tile to start drawing from
        start_x = center_x - (tiles_per_side[0] // 2)
        start_y = center_y - (tiles_per_side[1] // 2)

        canvas_x = (x - start_x) * 256 - 128
        canvas_y = (y - start_y) * 256 - (self.canvas_height // 2 - 128)

        return canvas_x, canvas_y

    def render_planes(self):
        self.canvas.delete("plane_layer")  # Clear previous tiles
        self.plane_photoimages = []

        home = (self.center_lat, self.center_lon)
        state_data = get_states(use_cache=True)
        states = state_data.states
        filtered = filter_states(states, *home, self.filter_radius, include_onground=self.include_onground)

        plane_layer = ImageTk.PhotoImage(self.make_plane_layer(filtered))
        self.plane_photoimages.append(plane_layer)
        self.canvas.create_image(
            0, 0, anchor=tk.NW, image=plane_layer, tags=["plane_layer"]
        )

    def make_plane_layer(self, planes: Iterable[StateVector]) -> Image:
        frame = Image.new(
            "RGBA", (self.canvas_width, self.canvas_height), color=(0, 0, 0, 0)
        )
        for plane in planes:
            if not plane.latitude or not plane.longitude:
                continue
            tile_x, tile_y = lat_long_zoom_to_tile(
                plane.latitude, plane.longitude, self.zoom
            )
            canvas_x, canvas_y = self.tile_loc_to_screen(tile_x, tile_y)
            # print(f"Plane {i} of {len(filtered)} - ", end = "")
            img = self.image_manager.get_plane_icon(plane)
            frame.paste(
                img,
                (int(canvas_x - img.width / 2), int(canvas_y - img.height / 2)),
                mask=img,
            )
        return frame
