# Maps plane categories from API to icons
import colorsys
from PIL import Image, ImageFile, ImageChops
from pathlib import Path
from typing import Iterable, Self

from opensky_api import StateVector


class ImageSpinner:
    def __init__(self, img_path: Path | str, size=25):
        self.img_path = Path(img_path)
        self._base_img = Image.open(self.img_path)
        self.size = size

    def rotated(
        self, deg: int, size: int, obey_cache: bool = True
    ) -> ImageFile.ImageFile:
        cache_path = (
            self.img_path.parent
            / self.img_path.stem
            / f"{self.img_path.stem}_{deg}_{size}.png"
        )
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        if obey_cache and cache_path.exists():
            return Image.open(cache_path)

        resized_and_rotated = _rotate_and_thumb(self._base_img, deg, size)
        resized_and_rotated.save(cache_path)
        return resized_and_rotated

    def precache_rotations(self, deg_list: Iterable[int], size: int) -> None:
        for deg in deg_list:
            _ = self.rotated(deg, size, obey_cache=True)


plane_icons_base = {
    2: ImageSpinner(Path(r"icons\png\cessna.png")),  # Light (< 15500 lbs),
    3: ImageSpinner(Path(r"icons\png\glf5.png")),  # Small (15500 to 75000 lbs),
    4: ImageSpinner(Path(r"icons\png\a330.png")),  # Large (75000 to 300000 lbs),
    5: ImageSpinner(
        Path(r"icons\png\b767.png")
    ),  # High Vortex Large (aircraft such as B-757),
    6: ImageSpinner(Path(r"icons\png\b787.png")),  # Heavy (> 300000 lbs),
    7: ImageSpinner(
        Path(r"icons\png\a6.png")
    ),  # High Performance (> 5g acceleration and 400 kts),
    8: ImageSpinner(Path(r"icons\png\a7.png")),  # Rotorcraft,
    9: ImageSpinner(Path(r"icons\png\b1.png")),  # Glider / sailplane,
    10: ImageSpinner(Path(r"icons\png\f11.png")),  # Lighter-than-air,
    # 11: ..., # Parachutist / Skydiver,
    12: ImageSpinner(
        Path(r"icons\png\b4.png")
    ),  # Ultralight / hang-glider / paraglider,
    # 13: ..., # Reserved,
    14: ImageSpinner(Path(r"icons\png\b0.png")),  # Unmanned Aerial Vehicle,
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


def _rotate_and_thumb(img: ImageFile.ImageFile, r, size):
    img = img.rotate(r)
    img.thumbnail((size, size))
    return img


class ImageManager:
    MAX_HEIGHT = 14_000  # meters
    MAX_HUE = 0.8

    def __init__(self, plane_size: int = 25):
        self.plane_size = plane_size
        self.make_rotations()

    def make_rotations(self):
        print("Pre-generating rotations of included plane icons")
        for spinner in plane_icons_base.values():
            spinner.precache_rotations(range(0, 361, 10), size=self.plane_size)
        print("Finished generating standard plane icon rotations")

        print("Pre-generating rotations of additional plane icons")
        for spinner in filler_plane_icons_base:
            spinner.precache_rotations(range(0, 361, 10), size=self.plane_size)
        print("Finished generating additions plane rotations")

    def get_plane_icon(
        self, plane: StateVector, color: bool = True
    ) -> ImageFile.ImageFile:
        rot = 360 - (round(plane.true_track / 10) * 10)

        if plane.category is not None:
            if plane.category in plane_icons_base:
                img = plane_icons_base[plane.category].rotated(rot, self.plane_size)
                # print(f"Using plane category {plane.category}")
            elif plane.category in (0, 1):
                if plane.icao24 is not None:
                    img = filler_plane_icons_base[
                        int(plane.icao24, 16) % len(filler_plane_icons_base)
                    ].rotated(rot, self.plane_size)
                    # print(f"{plane.category=}, using 'random' filler icon from icao id")
                else:
                    img = filler_plane_icons_base[0].rotated(rot, self.plane_size)
                    # print(f"{plane.category=}, but no icao id")
            else:
                img = filler_plane_icons_base[0].rotated(rot, self.plane_size)
                # print(f"No icon for {plane.category=}")
        else:
            img = filler_plane_icons_base[0].rotated(rot, self.plane_size)
            # print(f"{plane.category=}")

        if color:
            if plane.baro_altitude:
                altitude = plane.baro_altitude
            elif plane.geo_altitude:
                altitude = plane.geo_altitude
            else:
                altitude = 0

            color = self.altitude_to_rgb(altitude)
            return self.recolor_img(img, color, alpha_tolerance=30)

        return img

    def recolor_img(
        self: Self,
        img: ImageFile.ImageFile,
        new_color: tuple[int, int, int],
        alpha_tolerance=0,
    ) -> ImageFile.ImageFile:
        src_color = (0, 0, 0)

        # Split into R, G, B channels
        r, g, b, a = img.split()

        # Create binary masks for each channel where the target color exists
        src_color = (0, 0, 0, 255)  # black
        _r = r.point(lambda x: 1 if x == src_color[0] else 0, mode="1")
        _g = g.point(lambda x: 1 if x == src_color[1] else 0, mode="1")
        _b = b.point(lambda x: 1 if x == src_color[2] else 0, mode="1")
        _a = a.point(
            lambda x: 1 if abs(x - src_color[3]) < alpha_tolerance else 0, mode="1"
        )

        # Combine masks with logical AND to get pixels that match all three channels
        mask = ImageChops.logical_and(_r, _g)
        mask = ImageChops.logical_and(mask, _b)
        mask = ImageChops.logical_and(mask, _a)

        # Create a new image with the replacement color
        new_img = Image.new("RGBA", img.size, new_color)

        # Paste the replacement color where the mask is True
        img.paste(new_img, mask=mask)

        return img

    def altitude_to_rgb(self: Self, altitude: float) -> tuple[int, int, int]:
        hue = min(
            (altitude * self.MAX_HUE) / (self.MAX_HEIGHT), self.MAX_HUE
        )  # clamp higher altitudes to max
        saturation = 1.0
        lightness = 0.5

        # Convert HLS (colorsys uses HLS, not HSL) to RGB (0–1 range)
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)

        # Convert to 0–255 integer RGB values
        return tuple(int(x * 255) for x in (r, g, b))

    def generate_altitude_key(self: Self, width: int, height: int):
        scale = Image.new("RGB", (width, height))
        for x in range(width):
            color = self.altitude_to_rgb((x / width) * self.MAX_HEIGHT)
            for y in range(height):
                scale.putpixel((x, y), color)
        return scale
