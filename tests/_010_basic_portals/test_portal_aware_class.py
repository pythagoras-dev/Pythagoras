from pythagoras import BasicPortal, PortalAwareClass, _PortalTester

class SampleClass(PortalAwareClass):

    def __init__(self, n, portal:BasicPortal=None):
        super().__init__(portal)
        self.n = n

    def __getstate__(self):
        return {"n": self.n}

    def __setstate__(self, state):
        self.n = state["n"]

    def _register_in_portal(self):
        pass


def test_portal_awareness(tmpdir):

    with _PortalTester():

        portal = BasicPortal(tmpdir)
        portal2 = BasicPortal(tmpdir)

        # with portal:
        #     sample = SampleClass(10)
        #     assert sample.portal == portal
        #
        # with portal2:
        #     sample2 = copy(sample)
        #     assert sample2.portal == portal2
        #
        # assert sample.portal == portal
        # assert sample2.portal == portal2
        # assert sample.n == sample2.n
