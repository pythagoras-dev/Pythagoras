import pythagoras as pth
from pythagoras import _PortalTester
from pythagoras import LoggingCodePortal
from pythagoras._040_logging_code_portals.logging_portal_core_classes import LoggingFnCallSignature


def test_exception_inside_with(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir + "__12345") as p:
        assert len(p.portal._crash_history) == 0
        try:
            with p.portal:
                x = 1/0
        except:
            pass
        assert len(p.portal._crash_history) == 1


def test_sequential_exceptions_inside_with(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir + "__QETUO") as p:
        assert len(p.portal._crash_history) == 0

        try:
            with p.portal:
                x = 1/0
        except:
            pass

        try:
            with p.portal:
                x = 1 / 0
        except:
            pass

        assert len(p.portal._crash_history) == 2

def test_exceptions_2_exceptions(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert len(p.portal._crash_history) == 0
        try:
            with p.portal:
                x = 1/0
        except:
            pass

    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert len(p.portal._crash_history) == 1

        try:
            with p.portal:
                x = 2/0
        except:
            pass

        assert len(p.portal._crash_history) == 2

def test_exception_inside_nested_with_same_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir + "__12Q3Q45") as p:
        assert len(p.portal._crash_history) == 0
        try:
            with p.portal:
                with p.portal:
                    with p.portal:
                        with p.portal:
                            with p.portal:
                                with p.portal:
                                    x = 1/0
        except:
            pass
        assert len(p.portal._crash_history) == 1


def test_fn_exception_inside_nested_with_same_portal(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        @pth.logging()
        def yyy():
            raise Exception("This is a demo exception")
        sifnature = LoggingFnCallSignature(yyy, {})
        assert len(p.portal._crash_history) == 0
        assert len(sifnature.crashes) == 0
        try:
            with p.portal:
                with p.portal:
                    with p.portal:
                        with p.portal:
                            with p.portal:
                                with p.portal:
                                    yyy()
        except:
            pass

        assert len(p.portal._crash_history) == 1
        assert len(sifnature.crashes) == 0


def test_exception_inside_nested_with(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        portal2=LoggingCodePortal(tmpdir + "_22")
        portal3=LoggingCodePortal(tmpdir + "_333")
        assert len(p.portal._crash_history) == 0
        assert len(portal2._crash_history) == 0
        assert len(portal3._crash_history) == 0
        with portal2:
            try:
                with p.portal:
                    raise Exception("This is a test exception")
            except:
                pass
            assert len(p.portal._crash_history) == 1
            assert len(portal2._crash_history) == 0
            assert len(portal3._crash_history) == 0
        assert len(p.portal._crash_history) == 1
        assert len(portal2._crash_history) == 0
        assert len(portal3._crash_history) == 0