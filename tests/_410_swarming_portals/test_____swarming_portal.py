from pythagoras import SwarmingPortal
from pythagoras import _PortalTester
import time


def test_descendant_process_registration_swarming_portal(tmpdir):
    """Verify descendant process can be registered without errors."""
    # tmpdir = "TEST_PROCESS_REGISTRATION"+str(time.time())
    with _PortalTester():
        portal = SwarmingPortal(
            root_dict=tmpdir,
            max_n_workers=0)  # Don't auto-start workers

        # Verify we can register a fake descendant process without errors
        # Using a non-existent PID to avoid interfering with actual process tracking
        portal.register_descendant_process("test_worker", 999_999_999, int(time.time()))

        # Verify process type filtering works
        assert portal.get_active_descendant_process_counter("test_worker") == 0  # Process is not alive
        assert portal.get_active_descendant_process_counter("nonexistent_type") == 0









