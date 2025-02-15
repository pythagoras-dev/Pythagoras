"""Pythagoras aims to democratize access to distributed serverless compute.

We make it simple and inexpensive to create, deploy and run
massively parallel algorithms from within local Python scripts and notebooks.
Pythagoras makes data scientists' lives easier, while allowing them to
solve more complex problems in a shorter time with smaller budgets.
"""
from typing import Optional, Dict
from random import Random
from persidict import PersiDict

from pythagoras._800_persidict_extensions import *
from pythagoras._810_output_manipulators import *
from pythagoras._820_strings_signatures_converters import *

from pythagoras._010_basic_portals import *
from pythagoras._010_basic_portals import _PortalTester
from pythagoras._020_ordinary_code_portals import *
from pythagoras._030_data_portals import *
from pythagoras._040_logging_code_portals import *
from pythagoras._050_safe_code_portals import *
from pythagoras._060_autonomous_code_portals import *
from pythagoras._070_protected_code_portals import *
from pythagoras._080_pure_code_portals import *
from pythagoras._090_swarming_portals import *
from pythagoras._100_default_local_portals import *
from pythagoras._110_top_level_API import *


primary_decorators = {d.__name__:d for d in [
    autonomous
    , pure
    ]}

all_decorators = {d.__name__:d for d in [
    ordinary
    , logging
    , safe
    , autonomous
    , protected
    , pure
]}


