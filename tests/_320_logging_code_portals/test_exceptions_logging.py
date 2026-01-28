import pythagoras as pth
from pythagoras import _PortalTester
from pythagoras import LoggingCodePortal
from pythagoras._320_logging_code_portals.logging_portal_core_classes import LoggingFnCallSignature


def test_exception_inside_with(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir + "__12345") as p:
        assert len(p.portal._crash_history) == 0
        try:
            with p.portal:
                _ = 1/0
        except Exception:
            pass
        assert len(p.portal._crash_history) == 1


def test_sequential_exceptions_inside_with(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir + "__QETUO") as p:
        assert len(p.portal._crash_history) == 0

        try:
            with p.portal:
                _ = 1/0
        except Exception:
            pass

        try:
            with p.portal:
                _ = 1 / 0
        except Exception:
            pass

        assert len(p.portal._crash_history) == 2

def test_exceptions_2_exceptions(tmpdir):
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert len(p.portal._crash_history) == 0
        try:
            with p.portal:
                _ = 1/0
        except Exception:
            pass

    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        assert len(p.portal._crash_history) == 1

        try:
            with p.portal:
                _ = 2/0
        except Exception:
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
                                    _ = 1/0
        except Exception:
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
        except Exception:
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
            except Exception:
                pass
            assert len(p.portal._crash_history) == 1
            assert len(portal2._crash_history) == 0
            assert len(portal3._crash_history) == 0
        assert len(p.portal._crash_history) == 1
        assert len(portal2._crash_history) == 0
        assert len(portal3._crash_history) == 0


def test_same_exception_not_logged_twice(tmpdir):
    """Test that the same exception instance is not logged multiple times."""
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        initial_count = len(p.portal._crash_history)

        try:
            with p.portal:
                raise ValueError("This exception should only be logged once")
        except ValueError:
            pass

        # Exception should be logged once
        assert len(p.portal._crash_history) == initial_count + 1


def test_exception_deduplication_across_nested_contexts(tmpdir):
    """Test that exception deduplication works across nested portal contexts."""
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        initial_count = len(p.portal._crash_history)

        try:
            with p.portal:
                with p.portal:
                    with p.portal:
                        raise RuntimeError("Nested exception")
        except RuntimeError:
            pass

        # Despite multiple nested contexts, exception should be logged once
        assert len(p.portal._crash_history) == initial_count + 1


def test_different_exception_instances_logged_separately(tmpdir):
    """Test that different exception instances are logged separately."""
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        initial_count = len(p.portal._crash_history)

        # First exception
        try:
            with p.portal:
                raise ValueError("First exception")
        except ValueError:
            pass

        # Second exception (different instance)
        try:
            with p.portal:
                raise ValueError("Second exception")
        except ValueError:
            pass

        # Both should be logged
        assert len(p.portal._crash_history) == initial_count + 2


def test_exception_types_mixed(tmpdir):
    """Test that different exception types are all logged correctly."""
    with _PortalTester(LoggingCodePortal, tmpdir) as p:
        initial_count = len(p.portal._crash_history)

        exception_types = [ValueError, TypeError, RuntimeError, KeyError, AttributeError]

        for exc_type in exception_types:
            try:
                with p.portal:
                    raise exc_type(f"Exception of type {exc_type.__name__}")
            except Exception:
                pass

        # All should be logged
        assert len(p.portal._crash_history) == initial_count + len(exception_types)