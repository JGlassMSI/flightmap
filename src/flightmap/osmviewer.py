import tkinter as tk
from PIL import Image, ImageTk
import logging

from .webservices import get_tile
from .conversion import deg2tile
 
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
        self.images = []

        def on_escape(event=None):
            """Close the window when Escape is pressed."""
            self.root.destroy()

        # Bind escape key to quit
        self.root.bind("<Escape>", on_escape)
    
        # Initial map render
        self.render_map()

    def render_map(self):
        """Render tiles centered on self.center_lat/center_lon."""
        self.canvas.delete("all")  # Clear previous tiles
        self.images = []  # Reset image references
        
        # Get center tile (x, y)
        center_x, center_y = deg2tile(self.center_lat, self.center_lon, self.zoom)
        # GMSI should be (131, 190) @ Zoom 9
        
        # Calculate how many tiles fit in the window (with padding)
        tiles_per_side = (
            int(self.canvas_width / 256) + 2,  # +2 to avoid edge gaps
            int(self.canvas_height / 256) + 2
        )
        # At 1920x1080, should be (9,6)
        
        # Top-left tile to start drawing from
        start_x = center_x - (tiles_per_side[0] // 2)
        start_y = center_y - (tiles_per_side[1] // 2)
        #(127, 187)

        
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
                self.images.append(photo)  # Keep reference
                
                # Calculate position on canvas
                canvas_x = (x - start_x) * 256 - 128 
                canvas_y = (y - start_y) * 256 - (self.canvas_height // 2 - 128)

                logging.debug(f"Drawing tile ({x}, {y}) at canvas position ({canvas_x}, {canvas_y})")
                
                # Draw tile
                self.canvas.create_image(canvas_x, canvas_y, anchor=tk.NW, image=photo)