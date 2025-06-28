from pythagoras import logging
from pythagoras._010_basic_portals.portal_tester import _PortalTester
from pythagoras._040_logging_code_portals import (
    LoggingCodePortal,LoggingFnCallSignature)
import pytest

def test_basics(tmpdir):
    # tmpdir = 3*"BASICS_EXECUTION_RECORDS_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as t:

        @logging(excessive_logging=True)
        def f():
            return 1

        assert f() == 1
        a = LoggingFnCallSignature(fn=f, arguments={})
        assert a.execute() == 1
        assert len(a.execution_attempts) == 2
        assert len(a.execution_results) == 2
        assert len(a.execution_records) == 2
        all_records = a.execution_records
        first_record = all_records[0]
        assert first_record.result == 1
        assert isinstance(a.execution_records[0].attempt_context, dict)
        assert a.execution_records[0].events == []
        assert a.execution_records[0].crashes == []
        assert a.execution_records[0].output == ""


def test_basics_no_logging_recalc(tmpdir):
    # tmpdir = 3*"BASICS_EXECUTION_RECORDS_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , p_consistency_checks = 1) as t:

        @logging(excessive_logging=False)
        def f():
            return 1

        assert f() == 1
        a = LoggingFnCallSignature(fn=f, arguments={})
        assert a.execute() == 1
        assert len(a.execution_attempts) == 0
        assert len(a.execution_results) == 0
        assert len(a.execution_records) == 0
        assert len(a.execution_outputs) == 0
        assert len(a.crashes) == 0


def test_basics_with_logging_recalc(tmpdir):
    # tmpdir = 3*"BASICS_EXECUTION_RECORDS_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir
            , p_consistency_checks = 1) as t:

        @logging(excessive_logging=True)
        def f():
            return 1

        assert f() == 1
        a = LoggingFnCallSignature(fn=f, arguments={})
        assert a.execute() == 1
        assert len(a.execution_attempts) == 2
        assert len(a.execution_results) == 2
        assert len(a.execution_records) == 2
        assert len(a.execution_outputs) == 2
        assert len(a.crashes) == 0



def test_basics_many_kwargs(tmpdir):
    # tmpdir = 3*"BASICS_MANY_KWARGS_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as t:

        @logging(excessive_logging=True)
        def f(**kwargs):
            print(f"{kwargs=}")
            result = sum(kwargs.values())
            print(f"{result=}")
            return result

        total = 0
        all_args = dict()
        for i in range(1,11):
            total += i
            all_args["a"+str(i)] = i
            assert f(**all_args) == total
            a = LoggingFnCallSignature(fn=f, arguments = all_args)

            for j in range(1,5):
                assert a.execute() == total
            assert len(a.execution_attempts) == 5
            assert len(a.execution_outputs) == 5
            assert len(a.execution_results) == 5
            assert len(a.execution_records) == 5
            all_records = a.execution_records
            last_record = all_records[-1]
            assert last_record.result == total
            assert isinstance(last_record.attempt_context, dict)
            assert last_record.events == []
            assert last_record.crashes == []
            assert isinstance(last_record.output, str)
            assert "kwargs" in last_record.output
            assert "result" in last_record.output

            assert len(t.portal._crash_history) == 0



def test_total_recalc(tmpdir):
    # tmpdir = 5*"TOTAL_RECALC_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal
            , tmpdir
            , p_consistency_checks = 1) as t:

        @logging(excessive_logging=True)
        def f():
            return 1

        NUM_ITERS = 5

        for i in range(NUM_ITERS):
            assert f() == 1

        a = LoggingFnCallSignature(fn=f, arguments={})
        assert a.execute() == 1

        assert len(a.execution_attempts) == NUM_ITERS + 1
        assert len(a.execution_results) == NUM_ITERS + 1
        assert len(a.execution_records) == NUM_ITERS + 1
        all_records = a.execution_records

        for i in range(NUM_ITERS):
            a_record = all_records[i]
            assert a_record.result == 1
            assert isinstance(a.execution_records[i].attempt_context, dict)
            assert a.execution_records[i].events == []
            assert a.execution_records[i].crashes == []
            assert a.execution_records[i].output == ""


def test_exception(tmpdir):
    # tmpdir = 3*"EXCEPTIONS_" +str(int(time.time()))
    with _PortalTester(LoggingCodePortal, tmpdir) as t:

        @logging(excessive_logging=True)
        def fff():
            return 1/0

        with pytest.raises(ZeroDivisionError):
            fff()
        a = LoggingFnCallSignature(fn=fff, arguments={})

        assert len(a.execution_attempts) == 1
        assert len(a.execution_results) == 0
        assert len(a.execution_outputs) == 1
        assert len(a.execution_records) == 1
        assert len(a.crashes) == 1
        assert isinstance(a.execution_records[0].attempt_context, dict)
        assert a.execution_records[0].events == []
        assert len(a.execution_records[0].crashes) == 1
        with pytest.raises(Exception):
            x = a.execution_records[0].result
        assert "ZeroDivisionError" in a.execution_records[0].output
