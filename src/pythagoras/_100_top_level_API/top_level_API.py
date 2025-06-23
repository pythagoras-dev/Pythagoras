# import pandas as pd
# from pandas import describe_option
#
# from pythagoras import SwarmingPortal, BasicPortal
# from pythagoras._090_swarming_portals.default_portal import default_portal
#
#
# def initialize(root_dict) -> pd.DataFrame: #TODO: refactor
#     BasicPortal._clear_all()
#     portal = SwarmingPortal(root_dict=root_dict, max_n_workers=3)
#     portal.__enter__()
#     return portal.describe()
#
# def connect_to_local_portal(root_dict=None, max_n_workers=3) -> pd.DataFrame:
#     portal = SwarmingPortal(
#         root_dict=root_dict
#         , max_n_workers=max_n_workers)
#     return portal.describe()
#
# def connect_to_default_portal() -> pd.DataFrame:
#     portal = default_portal()
#     return portal.describe()
#
# def describe() -> pd.DataFrame:
#     if len(BasicPortal._all_known_portals) == 1:
#         return list(BasicPortal._all_known_portals.values())[0].describe()
#
#     all_descriptions = []
#     for i,portal in enumerate(BasicPortal._all_known_portals.values()):
#         description = portal.describe()
#         description.insert(0, "portal", i)
#         all_descriptions.append(description)
#     return pd.concat(all_descriptions, ignore_index=True)
#
