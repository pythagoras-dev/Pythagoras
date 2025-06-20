from typing import Callable

from .ordinary_portal_core_classes_NEW import OrdinaryFn, OrdinaryCodePortal


class ordinary:
    """A decorator that converts a Python function into an OrdinaryFn object.

    As a part of the conversion process, the source code of the function
    is checked. If it does not meet the requirements of an ordinary function,
    an exception is raised.
    """

    _portal: OrdinaryCodePortal | None

    def __init__(self, portal: OrdinaryCodePortal | None = None):
       assert portal is None or isinstance(portal, OrdinaryCodePortal)
       self._portal=portal


    def __call__(self,fn:Callable)->OrdinaryFn:
        wrapper = OrdinaryFn(fn, portal=self._portal)
        return wrapper


    def __getstate__(self):
        raise TypeError("Decorators cannot be pickled.")


    def __setstate__(self, state):
        raise TypeError("Decorators cannot be pickled.")