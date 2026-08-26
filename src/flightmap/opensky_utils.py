from pathlib import Path
import pickle

from opensky_api import OpenSkyApi, OpenSkyStates

def get_states(use_cache=False):
    if use_cache and Path(".statescache").exists():
        print("Using cached states for testing")
        with open(".statescache", "rb") as f:
            return pickle.load(f)
    return get_states_unauthorized()

def get_states_unauthorized() -> OpenSkyStates:
    api = OpenSkyApi()
    states = api.get_states()
    with open(".statescache", "wb+") as f:
        pickle.dump(states,f)
        print("Dumped copy of states to cache")
    return states

