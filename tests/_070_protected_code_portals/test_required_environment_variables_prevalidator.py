import os

import pytest

from pythagoras import pure, required_environment_variables, _PortalTester, PureCodePortal


@pure(pre_validators=required_environment_variables("PYTHAGORAS_TEST_ENV_1", "PYTHAGORAS_TEST_ENV_2"))
def function_requiring_two_env_vars():
    return "ok"


def test_required_environment_variables_all_set(tmpdir, monkeypatch):
    """Function executes successfully when all required env vars are set."""

    env1 = "PYTHAGORAS_TEST_ENV_1"
    env2 = "PYTHAGORAS_TEST_ENV_2"

    monkeypatch.setenv(env1, "foo")
    monkeypatch.setenv(env2, "bar")

    with _PortalTester(PureCodePortal, tmpdir):
        assert function_requiring_two_env_vars() == "ok"


def test_required_environment_variables_missing(tmpdir, monkeypatch):
    """Pre-validator should prevent execution if a required env var is missing."""

    env1 = "PYTHAGORAS_TEST_ENV_1"
    env2 = "PYTHAGORAS_TEST_ENV_2"

    # Ensure both variables are absent
    monkeypatch.delenv(env1, raising=False)
    monkeypatch.delenv(env2, raising=False)

    with _PortalTester(PureCodePortal, tmpdir):
        with pytest.raises(Exception):
            function_requiring_two_env_vars()


def test_required_environment_variables_type_error():
    """Non-string names should raise TypeError."""

    with pytest.raises(TypeError):
        required_environment_variables("VALID_NAME", 123)


def test_required_environment_variables_empty_name():
    """Empty environment variable names should raise ValueError."""

    with pytest.raises(ValueError):
        required_environment_variables("")


@pytest.mark.parametrize("bad_name", [
    "INVALID-NAME",
    "SPACE NAME",
    "DOT.NAME",
    "NAME-WITH-DASH",
])
def test_required_environment_variables_invalid_characters(bad_name):
    """Names with characters other than letters, digits, and '_' should fail."""

    with pytest.raises(ValueError):
        required_environment_variables(bad_name)
