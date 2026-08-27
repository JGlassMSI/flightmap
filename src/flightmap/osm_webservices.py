import json
import requests
from pathlib import Path
 
def get_tile(zoom: int, x: int, y: int, tile_dir: str = "tiles", obey_cache=True) -> str | None:
    """Download an OSM tile and cache it locally. Returns path to cached tile."""
    # For wide zooms, don't" download impossible tiles
    if x < 0 or y < 0: return None 

    # Create tile directory if it doesn't exist
    tile_path = Path(tile_dir) / str(zoom) / str(x) / f"{y}.png"
    tile_path.parent.mkdir(parents=True, exist_ok=True)
 
    # Return cached tile if it exists
    if obey_cache and tile_path.exists():
        return str(tile_path)
 
    if True:
        # Download tile from OSM server
        url = f"https://a.tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    else:
        # download from cartodb with api key
        with open("creds.json", "r") as f:
            creds = json.load(f)
        key = creds['cartodb']
        url = f"https://basemaps.cartocdn.com/rastertiles/voyager/{zoom}/{x}/{y}.png?key={key}"

    headers = {
        "User-Agent": "Griffin MSI OSM Cache"
    }
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

def get_tiles_from_tilelist(tilelist: Path | str, sleep):
    data = load_tilelist(tilelist)
    for tiledata in data:
        z, x, y = tiledata['tile_z'], tiledata['tile_x'], tiledata['tile_y']
        get_tile(z, x, y)
        print(f"Got tile at {z=}, {x=}, {y=}")
        #sleep(random() * 2 + .5)

def make_tilelist(lat_deg: float, lon_deg: float, radius_km: int, zoom: int) -> list[dict[str, tuple[int,int, int]]]:
    from osmtilecalc.calculators import get_bounding_box, get_tile_coords

    bounding_box = get_bounding_box((lat_deg,lon_deg), radius_km)
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
    return data['tile_coords']


    