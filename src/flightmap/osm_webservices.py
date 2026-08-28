from abc import ABC, abstractmethod
from enum import Enum, auto
import json
import requests
from pathlib import Path
from typing import Self


class TileGetter(ABC):
    @abstractmethod
    def create_download_url(zoom: int, x: int, y: int) -> str:
        ...

    @abstractmethod
    def get_tile_path(zoom: int, x:int, y:int) -> str:
        ...

    def get_tile(
        self: TileGetter,
        zoom: int,
        x: int,
        y: int,
        tile_dir: str = "tiles",
        obey_cache=True,
    ) -> str | None:
        """Download an OSM tile and cache it locally. Returns path to cached tile."""
        # For wide zooms, don't" download impossible tiles
        if x < 0 or y < 0:
            return None

        # Create tile directory if it doesn't exist
        tile_path = self.get_tile_path(zoom,x, y)
        tile_path.parent.mkdir(parents=True, exist_ok=True)

        # Return cached tile if it exists
        if obey_cache and tile_path.exists():
            return str(tile_path)

        url = self.create_download_url(zoom, x, y)

        headers = {"User-Agent": "Griffin MSI OSM Cache"}
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()  # Raise error for 4xx/5xx statuses
            with open(tile_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded tile: {zoom}/{x}/{y}.png")
            return str(tile_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download {url}: {e}")
            return None

    def get_tiles_from_tilelist(self: TileGetter, tilelist: Path | str, sleep):
        data = load_tilelist(tilelist)
        for tiledata in data:
            z, x, y = tiledata["tile_z"], tiledata["tile_x"], tiledata["tile_y"]
            self.get_tile(z, x, y)
            print(f"Got tile at {z=}, {x=}, {y=}")
            # sleep(random() * 2 + .5)

class OSM_TileGetter(TileGetter):
    def create_download_url(self: Self, zoom: int, x: int, y: int) -> str:
        return f"https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png"

    def get_tile_path(self: Self, zoom: int, x:int, y:int) -> str:
        return Path("tiles") / "osm" / str(zoom) / str(x) / f"{y}.png"


# CartoDB Styles
# "light_all"
# "dark_all"
# "light_nolabels"
# "light_only_labels"
# "dark_nolabels"
# "dark_only_labels"
# "rastertiles/voyager"
# "rastertiles/voyager_nolabels"
# "rastertiles/voyager_only_labels"
# "rastertiles/voyager_labels_under"

class CartoDB_TileGetter(TileGetter):
    def __init__(self, style: CartDBStyle | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = style if style else "rastertiles/voyager"

    def create_download_url(self: Self, zoom: int, x: int, y: int) -> str:
        with open("creds.json", "r") as f:
            creds = json.load(f)
        key = creds["cartodb"]
        return f"https://basemaps.cartocdn.com/{self.style}/{zoom}/{x}/{y}.png?key={key}"

    def get_tile_path(self: Self, zoom: int, x:int, y:int) -> str:
        return Path("tiles") / "cartodb" / f"{self.style.replace("/", "_")}" / str(zoom) / str(x) / f"{y}.png"

def make_tilelist(
    lat_deg: float, lon_deg: float, radius_km: int, zoom: int
) -> list[dict[str, tuple[int, int, int]]]:
    from osmtilecalc.calculators import get_bounding_box, get_tile_coords

    bounding_box = get_bounding_box((lat_deg, lon_deg), radius_km)
    tile_coords = get_tile_coords(bounding_box, zoom)

    def f(val: float) -> str:
        # flatten and remove decimals
        return str(val).replace(".", "_").strip()

    filename = f"./tiles-{f(lat_deg)}-{f(lon_deg)}-{f(radius_km)}-{f(zoom)}"
    with open(filename, "w+") as f:
        json.dump({"tile_coords": tile_coords}, f)
        print(f"Wrote data to {filename}")

    return tile_coords


def load_tilelist(tilelist_file: Path | str) -> dict:
    with open(tilelist_file, "r") as f:
        data = json.load(f)
    return data["tile_coords"]
