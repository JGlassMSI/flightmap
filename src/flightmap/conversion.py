import math


def deg2tile(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    """Convert latitude/longitude to OSM tile (x, y) at a given zoom level."""
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    x = int((lon_deg + 180.0) / 360.0 * n)  # Simplified from radians formula
    y = int(
        (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
        / 2.0
        * n
    )
    return x, y
