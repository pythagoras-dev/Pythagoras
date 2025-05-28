from copy import deepcopy

import pandas as pd

from src.pythagoras._010_basic_portals.portal_aware_classes import _most_recently_entered_portal
from src.pythagoras._010_basic_portals.portal_tester import _PortalTester
from src.pythagoras._030_data_portals import *



def test_value_address_basic(tmpdir):
        """Test ValueAddr constructor and basis functions."""
        with _PortalTester(DataPortal,tmpdir):
            samples_to_test = ["something", 10, 10.0, 10j, True, None
                , (1,2,3), [1,2,3], {1,2,3}, {1:2, 3:4}
                , pd.DataFrame([[1,2.005],[-3,"QQQ"]])]
            for sample in samples_to_test:
                addr = ValueAddr(sample, portal=None)
                assert ValueAddr(sample, portal=None) == addr
                assert ValueAddr(sample, portal=None) != ValueAddr(
                    "something else", portal=None)
                assert ValueAddr(sample, portal=None).ready
                restored_sample = deepcopy(ValueAddr(sample, portal=None).get())
                if type(sample) == pd.DataFrame:
                    assert sample.equals(restored_sample)
                else:
                    assert ValueAddr(sample, portal=None).get() == sample

                assert ValueAddr(sample, portal=None
                                 ).portal == _most_recently_entered_portal()
