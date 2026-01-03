"""Distributed serverless compute at a global scale.

Pythagoras is a framework for distributed computations in Python.

It offers 3 main advantages:

- Global scale: parallelize your algorithms to scale to millions of nodes.
- Low maintenance: no need to manage servers and infrastructure,
Pythagoras replaces expensive compute with cheap storage.
- High performance: 'compute once, reuse forever' strategy
significanty accelerates long-running workflows.

Pythagoras is able to offer these benefits as it's the first framework
to fully implement the Functional Programming 2.0 paradigm.

Pythagoras excels at optimizing complex, long-running,
resource-demanding computations. It’s not the best choice for real-time,
latency-sensitive workflows.
"""


from ._210_basic_portals import *
from ._210_basic_portals import _PortalTester
from ._320_ordinary_code_portals import *
from ._330_data_portals import *
from ._340_logging_code_portals import *
from ._350_safe_code_portals import *
from ._360_autonomous_code_portals import *
from ._370_protected_code_portals import *
from ._380_pure_code_portals import *
from ._390_swarming_portals import *
from ._800_top_level_API import *
from ._110_supporting_utilities import *

from importlib import metadata as _md
try:
    __version__ = _md.version("pythagoras")
except _md.PackageNotFoundError:
    __version__ = "unknown"


