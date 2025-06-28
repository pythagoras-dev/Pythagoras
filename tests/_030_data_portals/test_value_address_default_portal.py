import random
import sys
from copy import copy
from typing import Any

import pytest

from pythagoras._010_basic_portals import (
    get_active_portal, _PortalTester)
from pythagoras._030_data_portals import *

#
# def test_value_address_basic():
#     with _PortalTester() :
#
#         modules = sys.modules
#         for i in range(100):
#             # random int from 0 to 1_000_000_000_000_000
#             random_number = random.randint(1, 1_000_000_000_000_000)
#             assert ValueAddr(random_number).get() == random_number
#             assert ValueAddr(random_number).get() == random_number
#             assert ValueAddr(random_number) in active_portal()._value_store
