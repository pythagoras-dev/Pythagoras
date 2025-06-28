import sys, logging
from pythagoras._040_logging_code_portals.output_capturer import OutputCapturer

def test_capture_stdout():
    with OutputCapturer() as capturer:
        print("Hello, stdout!")

    output = capturer.get_output()
    assert "Hello, stdout!" in output

def test_capture_stderr():
    with OutputCapturer() as capturer:
        print("Hello, stderr!", file=sys.stderr)

    output = capturer.get_output()
    assert "Hello, stderr!" in output

def test_capture_combined_output():
    with OutputCapturer() as capturer:
        print("First, stdout")
        print("Then, stderr", file=sys.stderr)

    output = capturer.get_output()
    assert "First, stdout" in output
    assert "Then, stderr" in output


def test_logging_debug_capture():
    logging.getLogger().setLevel(logging.DEBUG)
    with OutputCapturer() as capturer:
        logging.debug("Test DEBUG message")

    output = capturer.get_output()
    assert "Test DEBUG message" in output

def test_logging_info_capture():
    logging.getLogger().setLevel(logging.INFO)
    with OutputCapturer() as capturer:
        logging.info("Test INFO message")

    output = capturer.get_output()
    assert "Test INFO message" in output

def test_logging_warning_capture():
    logging.getLogger().setLevel(logging.WARNING)
    with OutputCapturer() as capturer:
        logging.warning("Test WARNING message")

    output = capturer.get_output()
    assert "Test WARNING message" in output

def test_logging_error_capture():
    logging.getLogger().setLevel(logging.ERROR)

    with OutputCapturer() as capturer:
        logging.error("Test ERROR message")

    output = capturer.get_output()
    assert "Test ERROR message" in output

def test_logging_critical_capture():
    logging.getLogger().setLevel(logging.CRITICAL)

    with OutputCapturer() as capturer:
        logging.critical("Test CRITICAL message")

    output = capturer.get_output()
    assert "Test CRITICAL message" in output
