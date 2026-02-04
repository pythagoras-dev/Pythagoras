"""Tests for OrdinaryCodePortal function tracking and linking."""

import pytest

from pythagoras import (
    OrdinaryFn, OrdinaryCodePortal, _PortalTester, ordinary
)


def sample_func_1(x):
    """First sample function."""
    return x * 2


def sample_func_2(x, y):
    """Second sample function."""
    return x + y


def sample_func_3(a, b, c):
    """Third sample function."""
    return a * b + c


def test_portal_tracks_linked_functions(tmpdir):
    """Test that portal correctly tracks linked functions."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        # Linked functions are registered lazily on first portal access.
        assert portal.get_number_of_linked_functions() == 0
        assert len(portal.get_linked_functions()) == 0

        f1 = OrdinaryFn(sample_func_1, portal=portal)
        assert portal.get_number_of_linked_functions() == 0
        _ = f1.portal
        assert portal.get_number_of_linked_functions() == 1
        linked = portal.get_linked_functions()
        assert len(linked) == 1
        assert f1 in linked

        f2 = OrdinaryFn(sample_func_2, portal=portal)
        assert portal.get_number_of_linked_functions() == 1
        _ = f2.portal
        assert portal.get_number_of_linked_functions() == 2
        linked = portal.get_linked_functions()
        assert len(linked) == 2
        assert f1 in linked
        assert f2 in linked

        f3 = OrdinaryFn(sample_func_3, portal=portal)
        assert portal.get_number_of_linked_functions() == 2
        _ = f3.portal
        assert portal.get_number_of_linked_functions() == 3
        linked = portal.get_linked_functions()
        assert len(linked) == 3
        assert f1 in linked
        assert f2 in linked
        assert f3 in linked


def test_portal_get_linked_functions_returns_set(tmpdir):
    """Test portal.get_linked_functions() returns a set."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        f1 = OrdinaryFn(sample_func_1, portal=portal)
        f2 = OrdinaryFn(sample_func_2, portal=portal)

        funcs = portal.get_linked_functions()
        assert isinstance(funcs, set)
        assert len(funcs) == 0

        _ = f1.portal
        _ = f2.portal

        funcs = portal.get_linked_functions()
        assert isinstance(funcs, set)
        assert len(funcs) == 2
        assert f1 in funcs
        assert f2 in funcs


def test_unlinked_function_not_tracked(tmpdir):
    """Test that functions without explicit portal link are not in linked list."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        f1 = OrdinaryFn(sample_func_1)

        assert portal.get_number_of_linked_functions() == 0

        result = f1(x=5)
        assert result == 10


def test_decorator_with_portal_creates_link(tmpdir):
    """Test that @ordinary decorator with portal creates proper link."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        @ordinary(portal=portal)
        def decorated_func(n):
            return n ** 2

        assert portal.get_number_of_linked_functions() == 0

        _ = decorated_func.portal

        assert portal.get_number_of_linked_functions() == 1
        linked = portal.get_linked_functions()
        assert decorated_func in linked


def test_portal_describe_shows_function_count(tmpdir):
    """Test that portal.describe() shows correct function count."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        desc = portal.describe()
        from pythagoras._210_basic_portals.portal_description_helpers import (
            _get_description_value_by_key
        )
        from pythagoras._310_ordinary_code_portals.ordinary_portal_core_classes import (
            _REGISTERED_FUNCTIONS_TXT
        )

        assert _get_description_value_by_key(desc, _REGISTERED_FUNCTIONS_TXT) == 0

        f1 = OrdinaryFn(sample_func_1, portal=portal)
        desc = portal.describe()
        assert _get_description_value_by_key(desc, _REGISTERED_FUNCTIONS_TXT) == 0
        _ = f1.portal
        desc = portal.describe()
        assert _get_description_value_by_key(desc, _REGISTERED_FUNCTIONS_TXT) == 1

        f2 = OrdinaryFn(sample_func_2, portal=portal)
        desc = portal.describe()
        assert _get_description_value_by_key(desc, _REGISTERED_FUNCTIONS_TXT) == 1
        _ = f2.portal
        desc = portal.describe()
        assert _get_description_value_by_key(desc, _REGISTERED_FUNCTIONS_TXT) == 2


def test_multiple_portals_separate_tracking(tmpdir):
    """Test that different portals track their own functions separately."""
    with _PortalTester():
        portal1 = OrdinaryCodePortal(tmpdir.mkdir("portal1"))
        portal2 = OrdinaryCodePortal(tmpdir.mkdir("portal2"))

        f1 = OrdinaryFn(sample_func_1, portal=portal1)
        f2 = OrdinaryFn(sample_func_2, portal=portal2)

        assert portal1.get_number_of_linked_functions() == 0
        assert portal2.get_number_of_linked_functions() == 0

        _ = f1.portal
        _ = f2.portal

        assert portal1.get_number_of_linked_functions() == 1
        assert portal2.get_number_of_linked_functions() == 1

        assert f1 in portal1.get_linked_functions()
        assert f1 not in portal2.get_linked_functions()

        assert f2 in portal2.get_linked_functions()
        assert f2 not in portal1.get_linked_functions()


def test_same_function_different_instances(tmpdir):
    """Test creating multiple OrdinaryFn instances from same function."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        f1 = OrdinaryFn(sample_func_1, portal=portal)
        f2 = OrdinaryFn(sample_func_1, portal=portal)

        assert f1.hash_signature == f2.hash_signature

        # Identity keys derive from normalized source, so wrappers should match.
        assert f1.get_identity_key() == f2.get_identity_key()

        _ = f1.portal
        _ = f2.portal

        assert portal.get_number_of_linked_functions() == 1


def test_get_linked_functions_with_type_filter(tmpdir):
    """Test get_linked_functions with target_class parameter."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        portal = t.portal

        f1 = OrdinaryFn(sample_func_1, portal=portal)

        linked = portal.get_linked_functions(target_class=OrdinaryFn)
        assert len(linked) == 0

        _ = f1.portal

        linked = portal.get_linked_functions(target_class=OrdinaryFn)
        assert len(linked) == 1
        assert f1 in linked

        linked_none = portal.get_linked_functions(target_class=None)
        assert len(linked_none) == 1
        assert f1 in linked_none


def test_get_linked_functions_invalid_type():
    """Test get_linked_functions with invalid target_class."""
    with _PortalTester():
        portal = OrdinaryCodePortal()

        with pytest.raises(TypeError, match="must be a subclass"):
            portal.get_linked_functions(target_class=str)

        with pytest.raises(TypeError, match="must be a subclass"):
            portal.get_linked_functions(target_class=int)
