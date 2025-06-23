"""Pythagoras aims to democratize access to distributed serverless compute.

We make it simple and inexpensive to create, deploy and run
massively parallel algorithms from within local Python scripts and notebooks.
Pythagoras makes data scientists' lives easier, while allowing them to
solve more complex problems in a shorter time with smaller budgets.
"""


from ._010_basic_portals import *
from ._010_basic_portals import _PortalTester
from ._020_ordinary_code_portals import *
from ._030_data_portals import *
from ._040_logging_code_portals import *
from ._050_safe_code_portals import *
from ._060_autonomous_code_portals import *
from ._070_protected_code_portals import *
from ._080_pure_code_portals import *
from ._090_swarming_portals import *
from ._100_top_level_API import *
from ._800_signatures_and_converters import *


primary_decorators = {d.__name__:d for d in [
    autonomous
    , pure
    ]}

all_decorators = {d.__name__:d for d in [
    ordinary
    , storable
    , logging
    , safe
    , autonomous
    , protected
    , pure
]}


