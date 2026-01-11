"""Version information for the pythagoras package."""

from importlib import metadata as _md

try:
    __version__ = _md.version("pythagoras")
except _md.PackageNotFoundError:
    __version__ = "unknown"
