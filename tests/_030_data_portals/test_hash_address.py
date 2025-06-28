from copy import deepcopy

import pandas as pd

from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._030_data_portals import *



def test_value_address_basic(tmpdir):
        """Test ValueAddr constructor and basis functions."""
        with _PortalTester(DataPortal,tmpdir):
            samples_to_test = ["something", 10, 10.0, 10j, True, None
                , (1,2,3), [1,2,3], {1,2,3}, {1:2, 3:4}
                , pd.DataFrame([[1,2.005],[-3,"QQQ"]])]
            for sample in samples_to_test:
                addr = ValueAddr(sample)
                assert ValueAddr(sample) == addr
                assert ValueAddr(sample) != ValueAddr(
                    "something else")
                assert ValueAddr(sample).ready
                restored_sample = deepcopy(ValueAddr(sample).get())
                if type(sample) == pd.DataFrame:
                    assert sample.equals(restored_sample)
                else:
                    assert ValueAddr(sample).get() == sample

