import tkinter as tk
from PIL import Image, ImageTk
from pathlib import Path
import logging
import math

from osmtilecalc.calculators import _lon_to_x, _lat_to_y
from opensky_api import StateVector

from .osm_webservices import get_tile
from .conversion import deg2tile
from .opensky_utils import get_states
from .flights import filter_states, lat_long_zoom_to_tile


 
class OSMViewer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Local OSM Tile Viewer")
        
        # Default settings
        self.zoom = 9  # Initial zoom level
        self.center_lat = 41.785  # GMSI
        self.center_lon = -87.580   # GMSI
        self.canvas_width = 1920    # Window width
        self.canvas_height = 1080   # Window height
        
        # Create canvas for drawing tiles
        self.canvas = tk.Canvas(
            root, 
            width=self.canvas_width, 
            height=self.canvas_height,
            bg="lightgray"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Store references to images (prevents Tkinter garbage collection)
        self.tile_images = []
        self.plane_photoimages = []

        def on_escape(event=None):
            """Close the window when Escape is pressed."""
            self.root.destroy()

        # Bind escape key to quit
        self.root.bind("<Escape>", on_escape)

        img = Image.open(Path(r"icons\png\a0.png"))
        self.plane_icons = {
           1: img
        }
    
        # Initial map render
        self.render_map()
        self.render_planes()

    def render_map(self):
        """Render tiles centered on self.center_lat/center_lon."""
        self.canvas.delete("tile")  # Clear previous tiles
        self.tile_images = []  # Reset image references
        
        # Get center tile (x, y)
        center_x, center_y = deg2tile(self.center_lat, self.center_lon, self.zoom)
        
        # Calculate how many tiles fit in the window (with padding)
        tiles_per_side = (
            int(self.canvas_width / 256) + 2,  # +2 to avoid edge gaps
            int(self.canvas_height / 256) + 2
        )
        
        # Top-left tile to start drawing from
        start_x = center_x - (tiles_per_side[0] // 2)
        start_y = center_y - (tiles_per_side[1] // 2)
        
        # Draw tiles
        for x in range(start_x, start_x + tiles_per_side[0]):
            for y in range(start_y, start_y + tiles_per_side[1]):
                # Download/cache tile
                tile_path = get_tile(self.zoom, x, y)
                if not tile_path:
                    continue  # Skip if download failed
                
                # Load tile image
                img = Image.open(tile_path)
                photo = ImageTk.PhotoImage(img)
                self.tile_images.append(photo)  # Keep reference
                
                # Calculate position on canvas
                canvas_x = (x - start_x) * 256 - 128 
                canvas_y = (y - start_y) * 256 - (self.canvas_height // 2 - 128)

                logging.debug(f"Drawing tile ({x}, {y}) at canvas position ({canvas_x}, {canvas_y})")
                
                # Draw tile
                self.canvas.create_image(canvas_x, canvas_y, anchor=tk.NW, image=photo, tags=['tile'])

    def tile_loc_to_screen(self,x: float, y:float) -> tuple[int, int]:
         # Get center tile (x, y)
        center_x, center_y = deg2tile(self.center_lat, self.center_lon, self.zoom)
        
        # Calculate how many tiles fit in the window (with padding)
        tiles_per_side = (
            int(self.canvas_width / 256) + 2,  # +2 to avoid edge gaps
            int(self.canvas_height / 256) + 2
        )
        
        # Top-left tile to start drawing from
        start_x = center_x - (tiles_per_side[0] // 2)
        start_y = center_y - (tiles_per_side[1] // 2)

        canvas_x = (x - start_x) * 256 - 128 
        canvas_y = (y - start_y) * 256 - (self.canvas_height // 2 - 128)

        return canvas_x, canvas_y


    def render_planes(self):
        self.canvas.delete("plane")  # Clear previous tiles

        home = (self.center_lat, self.center_lon)
        state_data = get_states(use_cache=True)
        states = state_data.states
        filtered = filter_states(states, *home, 220)


        for plane in filtered:
            tile_x, tile_y = lat_long_zoom_to_tile(
                plane.latitude,
                plane.longitude,
                9
            )
            canvas_x, canvas_y = self.tile_loc_to_screen(tile_x, tile_y)
            self.draw_plane(canvas_x, canvas_y, plane)

    def draw_plane(self, x: float, y: float, plane: StateVector | None = None) -> None:
        # self._draw_plane_as_circle(x, y)
        #self._draw_plane_as_arrow(x, y, plane)
        self._draw_plane_as_image(x, y, plane)

    def _draw_plane_as_image(self, x: float, y: float, plane: StateVector | None = None) -> None:
        if plane is None:
            self._draw_plane_as_circle(x, y)
            return

        img = self.plane_icons[1]
        if plane.true_track: img = img.rotate(-plane.true_track)
        img.thumbnail((30,30))
        photo = ImageTk.PhotoImage(img)
        self.plane_photoimages.append(photo)

        self.canvas.create_image(x, y, anchor=tk.CENTER, image=photo, tags=['plane'])

    def _draw_plane_as_arrow(self, x: float, y: float, plane: StateVector | None) -> None:
        if plane is None or plane.true_track is None:
            self._draw_plane_as_circle(x, y)
            return
        arrow_length = 8

        tt_radians = math.radians(plane.true_track)

        delta = (
                math.sin(tt_radians) * arrow_length,
                -math.cos(tt_radians) * arrow_length
            )
        start = (x - delta[0], y - delta[1])
        end = (x + delta[0], y + delta[1])

        self.canvas.create_line(start[0], start[1], end[0], end[1], width=3, arrow=tk.LAST, arrowshape=(8,8,8), fill="yellow")


    def _draw_plane_as_circle(self, x: float, y: float) -> None:
        plane_radius = 8
        self.canvas.create_oval(x-plane_radius, y-plane_radius,x+plane_radius, y+plane_radius,fill="green", outline="black",width=1)