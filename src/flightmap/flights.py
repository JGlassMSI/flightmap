import math
from fractions import Fraction

from opensky_api import OpenSkyApi, OpenSkyStates, StateVector
from geopy.distance import geodesic


def filter_states(states: list[StateVector], lat_deg: float, lon_deg: float, radius_km: float, max_states=4000) -> list[StateVector]:
    def dist(state: StateVector, lat_deg: float, lon_deg: float):
        return geodesic(
            (state.latitude, state.longitude),
            ((lat_deg), (lon_deg))
        )
    base = [s for s in states if dist(s, lat_deg, lon_deg) < radius_km]
    if len(base) < max_states: return base
    else: 
        trim_ratio = Fraction(max_states / len(base)).limit_denominator(25)
        print("TODO NEXT - filter available flights in a smarter way")
        breakpoint()
        return base[:max_states]

def lat_long_zoom_to_tile(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
    x = (lon_deg + 180) / 360 * math.pow(2, zoom)

    y = (
        (
            1
            - math.log(
                math.tan(lat_deg * math.pi / 180) + 1 / math.cos(lat_deg * math.pi / 180)
            )
            / math.pi
        )
        / 2
        * math.pow(2, zoom)
    )

    return x, y