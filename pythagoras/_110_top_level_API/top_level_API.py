import pandas as pd
from pandas import describe_option

from pythagoras import SwarmingPortal, BasicPortal, DefaultLocalPortal


def initialize(root_dict) -> pd.DataFrame: #TODO: refactor
    BasicPortal._clear_all()
    portal = SwarmingPortal(root_dict=root_dict, n_background_workers=3)
    portal.__enter__()
    return portal.describe()

def connect_to_local_portal(root_dict=None, n_background_workers=3) -> pd.DataFrame:
    portal = SwarmingPortal(
        root_dict=root_dict
        , n_background_workers=n_background_workers)
    return portal.describe()

def connect_to_default_portal() -> pd.DataFrame:
    portal = DefaultLocalPortal()
    return portal.describe()

def describe() -> pd.DataFrame:
    if len(BasicPortal.all_portals) == 1:
        return list(BasicPortal.all_portals.values())[0].describe()

    all_descriptions = []
    for i,portal in enumerate(BasicPortal.all_portals.values()):
        description = portal.describe()
        description.insert(0, "portal", i)
        all_descriptions.append(description)
    return pd.concat(all_descriptions, ignore_index=True)

