"""Tests for fix_kwargs with overlapping keyword arguments."""
import pytest

from pythagoras._210_basic_portals.portal_tester import _PortalTester
from pythagoras._340_autonomous_code_portals import *


def test_fix_kwargs_rejects_overlapping_keys():
    """Test that fix_kwargs raises ValueError when trying to fix already-fixed kwargs."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def add_three(a, b, c):
            return a + b + c

        # Fix 'a' to 1
        partially_fixed = add_three.fix_kwargs(a=1)

        # Trying to fix 'a' again should raise ValueError
        with pytest.raises(ValueError, match="Overlapping kwargs"):
            partially_fixed.fix_kwargs(a=999)


def test_execute_rejects_overlapping_with_fixed_kwargs():
    """Test that execute raises ValueError when call-time kwargs overlap with fixed kwargs."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def multiply(x, y):
            return x * y

        # Fix 'x' to 10
        fixed_x = multiply.fix_kwargs(x=10)

        # Trying to provide 'x' at call time should raise ValueError
        with pytest.raises(ValueError, match="Overlapping kwargs"):
            fixed_x.execute(x=5, y=3)

        # Providing only 'y' should work
        result = fixed_x.execute(y=3)
        assert result == 30


def test_fix_kwargs_chain_with_distinct_keys():
    """Test that fix_kwargs can be chained multiple times with distinct keys."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def compute(a, b, c, d):
            return a + b * c - d

        # Chain multiple fix_kwargs calls with distinct keys
        f1 = compute.fix_kwargs(a=100)
        f2 = f1.fix_kwargs(b=10)
        f3 = f2.fix_kwargs(c=5)

        # All three should be fixed now
        result = f3.execute(d=20)
        assert result == 100 + 10 * 5 - 20  # 130

        # Verify the fixed_kwargs are cumulative
        assert f3.fixed_kwargs == {'a': 100, 'b': 10, 'c': 5}


def test_fix_kwargs_partial_overlap_in_chain():
    """Test that partial overlap in fix_kwargs chain is detected at each step."""
    with _PortalTester(AutonomousCodePortal):
        @autonomous()
        def subtract(x, y):
            return x - y

        f1 = subtract.fix_kwargs(x=100)
        f2 = f1.fix_kwargs(y=30)

        # Trying to fix 'x' again on f2 should fail
        with pytest.raises(ValueError, match="Overlapping kwargs"):
            f2.fix_kwargs(x=999)

        # Trying to fix 'y' again on f2 should also fail
        with pytest.raises(ValueError, match="Overlapping kwargs"):
            f2.fix_kwargs(y=999)
