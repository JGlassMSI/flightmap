import json
from pathlib import Path
import pickle

from opensky_api import OpenSkyApi, OpenSkyStates, FlightTrack


def get_states(use_cache=False):
    if use_cache and Path(".statescache").exists():
        print("Using cached states for testing")
        with open(".statescache", "rb") as f:
            return pickle.load(f)
    return get_states_unauthorized()

def get_track(icao24: str, use_cache=False):
    track_cache_path = Path(".trackscache")
    cache_data = None
    if track_cache_path.exists():
        try:
            with open(track_cache_path, "rb") as f:
                cache_data: dict = pickle.load(f)
            if use_cache and icao24 in cache_data:
                return cache_data[icao24]
        except EOFError:
            cache_data = None

    track = get_track_unauthorized(icao24)

    if cache_data: cache_data[icao24] = track
    else: cache_data = {icao24: track}

    with open(track_cache_path, "wb") as f:
        pickle.dump(cache_data, f)



def get_states_unauthorized() -> OpenSkyStates:
    api = OpenSkyApi()
    states = api.get_states()
    with open(".statescache", "wb+") as f:
        pickle.dump(states, f)
        print("Dumped copy of states to cache")
    return states

def get_track_unauthorized(icao24: str) -> FlightTrack:
    api = OpenSkyApi()
    track = api.get_track_by_aircraft(icao24)
    return track
