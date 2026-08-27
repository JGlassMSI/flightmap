# Maps plane categories from API to icons
from PIL import Image, ImageFile
from pathlib import Path
from typing import Iterable

from opensky_api import StateVector

class ImageSpinner:
    def __init__(self, img_path: Path | str, size=25):
        self.img_path = Path(img_path)
        self._base_img = Image.open(self.img_path)
        self.size = size


    def rotated(self, deg: int, obey_cache:bool = True) -> ImageFile.ImageFile:
        cache_path = self.img_path.parent / self.img_path.stem / f"{self.img_path.stem}_{deg}.png"
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if obey_cache and cache_path.exists():
            return Image.open(cache_path)

        resized_and_rotated = _rotate_and_thumb(self._base_img, deg, self.size)
        resized_and_rotated.save(cache_path)
        return resized_and_rotated

    def precache_rotations(self, deg_list: Iterable[int]) -> None:
        for deg in deg_list:
            _ = self.rotated(deg, obey_cache=True)
        
    

plane_icons_base = {
    2: ImageSpinner(Path(r"icons\png\cessna.png")), # Light (< 15500 lbs),
    3: ImageSpinner(Path(r"icons\png\glf5.png")), # Small (15500 to 75000 lbs),
    4: ImageSpinner(Path(r"icons\png\a330.png")), # Large (75000 to 300000 lbs),
    5: ImageSpinner(Path(r"icons\png\b767.png")), # High Vortex Large (aircraft such as B-757),
    6: ImageSpinner(Path(r"icons\png\b787.png")), # Heavy (> 300000 lbs),
    7: ImageSpinner(Path(r"icons\png\a6.png")), # High Performance (> 5g acceleration and 400 kts),
    8: ImageSpinner(Path(r"icons\png\a7.png")), # Rotorcraft,
    9: ImageSpinner(Path(r"icons\png\b1.png")), # Glider / sailplane,
    10: ImageSpinner(Path(r"icons\png\f11.png")), # Lighter-than-air,
    # 11: ..., # Parachutist / Skydiver,
    12: ImageSpinner(Path(r"icons\png\b4.png")), # Ultralight / hang-glider / paraglider,
    # 13: ..., # Reserved,
    14: ImageSpinner(Path(r"icons\png\b0.png")), # Unmanned Aerial Vehicle,
    # 15: ..., # Space / Trans-atmospheric vehicle,
    # 16: ..., # Surface Vehicle – Emergency Vehicle,
    # 17: ..., # Surface Vehicle – Service Vehicle,
    # 18: ..., # Point Obstacle (includes tethered balloons),
    # 19: ..., # Cluster Obstacle,
    # 20: ..., # Line Obstacle.
}

filler_plane_icons_base = (
    ImageSpinner(Path(r"icons\png\a0.png")),
    ImageSpinner(Path(r"icons\png\b737.png")),
    ImageSpinner(Path(r"icons\png\b747.png")),
    ImageSpinner(Path(r"icons\png\b777.png")),
    ImageSpinner(Path(r"icons\png\md11.png")),
    ImageSpinner(Path(r"icons\png\a330.png")),
    ImageSpinner(Path(r"icons\png\a340.png")),
    ImageSpinner(Path(r"icons\png\a380.png")),
)

def retieve_rotation(base_img: ImageFile.ImageFile, rot_list: list[int]) -> ImageFile.ImageFile:
    ...

def _rotate_and_thumb(img: ImageFile.ImageFile, r, size):
    img = img.rotate(r)
    img.thumbnail((size, size))
    return img

def make_rotations(base_img: ImageFile.ImageFile) -> dict[int, ImageFile.ImageFile]:

    return {r: _rotate_and_thumb(base_img, r, 25) for r in range(0, 361, 10)}

    
print("Pre-generating rotations of included plane icons")
for spinner in plane_icons_base.values():
    spinner.precache_rotations(range(0, 361, 10))
print("Finished generating standard plane icon rotations")

print("Pre-generating rotations of additional plane icons")
for spinner in filler_plane_icons_base:
    spinner.precache_rotations(range(0, 361, 10))
print("Finished generating additions plane rotations")


def get_plane_icon(plane: StateVector) -> ImageFile.ImageFile:
    rot = 360 - (round(plane.true_track / 10) * 10)

    if plane.category is not None:
        if plane.category in plane_icons_base:
            img = plane_icons_base[plane.category].rotated(rot)
            #print(f"Using plane category {plane.category}")
        elif plane.category in (0, 1):
            if plane.icao24 is not None:
                img = filler_plane_icons_base[int(plane.icao24, 16) % len(filler_plane_icons_base)].rotated(rot)
                #print(f"{plane.category=}, using 'random' filler icon from icao id")
            else:
                img = filler_plane_icons_base[0].rotated(rot)
                #print(f"{plane.category=}, but no icao id")
        else:
            img = filler_plane_icons_base[0].rotated(rot)
            #print(f"No icon for {plane.category=}")
    else:
        img = filler_plane_icons_base[0].rotated(rot)
        #print(f"{plane.category=}")

    return img