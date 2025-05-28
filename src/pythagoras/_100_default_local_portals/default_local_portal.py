# from __future__ import annotations
#
# from parameterizable import parameterizable
# from persidict import FileDirDict
# from sympy import false
#
# from pythagoras._010_basic_portals import BasicPortal
# from pythagoras._090_swarming_portals.swarming_portals import SwarmingPortal
#
# class DefaultLocalPortal(SwarmingPortal):
#     """A default local portal stored in ~/.pythagoras/.default_portal
#
#     This portal is automatically is used by a Pythagoras-enabled program
#     if/when no other portal is specified.
#     """
#
#     _default_local_portal_instance: DefaultLocalPortal | None = None
#     _default_instance_created:bool = False
#
#     def __new__(cls):
#         """ Singleton pattern implementation for DefaultLocalPortal class.
#
#         Returns the same instance of DefaultLocalPortal class if it has been
#         created before, otherwise creates a new instance and returns it.
#         """
#         assert cls == DefaultLocalPortal
#         if cls._default_local_portal_instance is None:
#             cls._default_local_portal_instance = super(
#                 DefaultLocalPortal, cls).__new__(cls)
#         return cls._default_local_portal_instance
#
#     def __init__(self):
#         if DefaultLocalPortal._default_instance_created:
#             return
#         DefaultLocalPortal._default_instance_created = True
#         SwarmingPortal.__init__(self
#             , root_dict = FileDirDict(BasicPortal.default_base_dir())
#             , excessive_logging = None
#             , p_consistency_checks = 0
#             , n_background_workers = 3
#             , runtime_id = None
#             )
#
#
#     @classmethod
#     def _clear_all(cls):
#         """Clear all data stored in the portal"""
#         cls._default_local_portal_instance = None
#         cls._calls_counter = 0
#         super()._clear_all()
#
# parameterizable.register_parameterizable_class(DefaultLocalPortal)