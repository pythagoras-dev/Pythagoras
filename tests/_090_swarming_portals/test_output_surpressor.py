import sys
from pythagoras._090_swarming_portals.output_suppressor import OutputSuppressor

def test_output_is_suppressed(capsys):
    """Verify that output to stdout and stderr is suppressed within the context."""
    with OutputSuppressor():
        print("This should not appear")
        print("This should also not appear", file=sys.stderr)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

def test_output_is_restored(capsys):
    """Verify that stdout and stderr are restored after exiting the context."""
    print("Before suppression")
    with OutputSuppressor():
        print("This is suppressed")
    print("After suppression")

    # This captures the output before and after the suppression context
    captured = capsys.readouterr()
    # As the prints inside the context are suppressed,
    # they should not appear in the captured output
    assert "Before suppression\n" in captured.out
    assert "After suppression\n" in captured.out
    assert "This is suppressed" not in captured.out

def test_no_output_with_suppressor(capsys):
    """Ensure no output is captured with the suppressor active."""
    with OutputSuppressor():
        print("This should not appear")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

