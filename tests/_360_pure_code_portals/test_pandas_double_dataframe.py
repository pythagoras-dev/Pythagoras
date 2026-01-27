import numpy as np
import pandas as pd

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._360_pure_code_portals.pure_core_classes import (
    PureCodePortal)
from pythagoras._360_pure_code_portals.pure_decorator import pure

def double(x):
  print("I am about to double something \n")
  # sleep(1)
  return x*2

def test_pure_double_pandas_dataframe(tmpdir):
    # tmpdir = 2*"PURE_DOUBLE_PANDAS_DATAFRAME_" + str(int(time.time()))
    with _PortalTester(PureCodePortal
            , tmpdir
            ):
        global double
        double_pure = pure()(double)
        df = pd.DataFrame(np.random.randn(10, 20))
        df_zero = double_pure(x=df) - double_pure(x=df)
        total_sum = df_zero.sum().sum()
        assert int(total_sum) == 0
        
        