# Maps plane categories from API to icons
from PIL import Image, ImageFile
from pathlib import Path

from opensky_api import StateVector

plane_icons_base = {
    2: Image.open(Path(r"icons\png\cessna.png")), # Light (< 15500 lbs),
    3: Image.open(Path(r"icons\png\glf5.png")), # Small (15500 to 75000 lbs),
    4: Image.open(Path(r"icons\png\a330.png")), # Large (75000 to 300000 lbs),
    5: Image.open(Path(r"icons\png\b767.png")), # High Vortex Large (aircraft such as B-757),
    6: Image.open(Path(r"icons\png\b787.png")), # Heavy (> 300000 lbs),
    7: Image.open(Path(r"icons\png\a6.png")), # High Performance (> 5g acceleration and 400 kts),
    8: Image.open(Path(r"icons\png\a7.png")), # Rotorcraft,
    9: Image.open(Path(r"icons\png\b1.png")), # Glider / sailplane,
    10: Image.open(Path(r"icons\png\f11.png")), # Lighter-than-air,
    # 11: ..., # Parachutist / Skydiver,
    12: Image.open(Path(r"icons\png\b4.png")), # Ultralight / hang-glider / paraglider,
    # 13: ..., # Reserved,
    14: Image.open(Path(r"icons\png\b0.png")), # Unmanned Aerial Vehicle,
    # 15: ..., # Space / Trans-atmospheric vehicle,
    # 16: ..., # Surface Vehicle – Emergency Vehicle,
    # 17: ..., # Surface Vehicle – Service Vehicle,
    # 18: ..., # Point Obstacle (includes tethered balloons),
    # 19: ..., # Cluster Obstacle,
    # 20: ..., # Line Obstacle.
}

filler_plane_icons_base = (
    Image.open(Path(r"icons\png\a0.png")),
    Image.open(Path(r"icons\png\b737.png")),
    Image.open(Path(r"icons\png\b747.png")),
    Image.open(Path(r"icons\png\b777.png")),
    Image.open(Path(r"icons\png\md11.png")),
    Image.open(Path(r"icons\png\a330.png")),
    Image.open(Path(r"icons\png\a340.png")),
    Image.open(Path(r"icons\png\a380.png")),
)

def make_rotations(base_img: ImageFile.ImageFile) -> dict[int, ImageFile.ImageFile]:
    def _rotate_and_thumb(img: ImageFile.ImageFile, r, size):
        img = img.rotate(r)
        img.thumbnail((size, size))
        return img
    return {r: _rotate_and_thumb(base_img, r, 25) for r in range(0, 361, 10)}

    
print("Pre-generating rotations of included plane icons")
plane_icons_rotated = {
    index: make_rotations(base_image) for index, base_image in plane_icons_base.items()
}
print("Finished generating standard plane icon rotations")

print("Pre-generating rotations of additional plane icons")
filler_icons_rotated = [make_rotations(base_image) for base_image in filler_plane_icons_base]
print("Finished generating additions plane rotations")


def get_plane_icon(plane: StateVector) -> ImageFile.ImageFile:
    rot = 360 - (round(plane.true_track / 10) * 10)

    if plane.category is not None:
        if plane.category in plane_icons_rotated:
            img = plane_icons_rotated[plane.category][rot]
            print(f"Using plane category {plane.category}")
        elif plane.category in (0, 1):
            if plane.icao24 is not None:
                img = filler_icons_rotated[int(plane.icao24, 16) % len(filler_icons_rotated)][rot]
                print(f"{plane.category=}, using 'random' filler icon from icao id")
            else:
                img = filler_icons_rotated[0][rot]
                print(f"{plane.category=}, but no icao id")
        else:
            img = filler_icons_rotated[0][rot]
            print(f"No icon for {plane.category=}")
    else:
        img = filler_icons_rotated[0][rot]
        print(f"{plane.category=}")

    return img