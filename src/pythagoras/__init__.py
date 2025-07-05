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


