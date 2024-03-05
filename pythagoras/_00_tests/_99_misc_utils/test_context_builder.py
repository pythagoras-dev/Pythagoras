from pythagoras._05_events_and_exceptions.context_utils import build_context

def test_build_context():
    context = build_context()
    assert isinstance(context, dict)
    assert "hostname" in context
    assert "user" in context
    assert "pid" in context
    assert "platform" in context
    assert "python_implementation" in context
    assert "python_version" in context
    assert "processor" in context
    assert "cpu_count" in context
    assert "cpu_load_avg" in context
    assert "disk_usage" in context
    assert "virtual_memory" in context
    assert "working_directory" in context
    assert "local_timezone" in context
    