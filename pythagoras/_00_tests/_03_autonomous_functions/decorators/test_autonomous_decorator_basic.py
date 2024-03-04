
from pythagoras._03_autonomous_functions import *
from pythagoras._06_mission_control.global_state_management import (
    _clean_global_state, initialize)

def test_strictly_autonomous(tmpdir):

    _clean_global_state()
    initialize(tmpdir)

    def f(a: int):
        b = 24
        return a + b

    f = strictly_autonomous()(f)

    assert is_strictly_autonomous(f)
    assert not is_loosely_autonomous(f)
    assert is_autonomous(f)

    assert f(a=10) == 34


def h(a:int):
    b=100
    return a+b

def test_not_autonomous(tmpdir):
    _clean_global_state()
    initialize(tmpdir)
    assert not is_autonomous(h)
    assert not is_loosely_autonomous(h)
    assert not is_strictly_autonomous(h)
    assert h(a=10) == 110



def test_autonomous(tmpdir):
    _clean_global_state()
    initialize(tmpdir)

    @autonomous(island_name="DEMO")
    def zyx(a: int):
        b = 10
        return a + b

    assert not is_strictly_autonomous(zyx)
    assert  is_loosely_autonomous(zyx)
    assert is_autonomous(zyx)
    assert zyx(a=10) == 20


def f_1():
    return 1000

def f_2():
    return f_1() + 10

def test_default_island_chained(tmpdir):
    _clean_global_state()
    initialize(tmpdir)

    global f_1, f_2
    f_1 = autonomous(island_name=DefaultIsland)(f_1)
    f_2 = autonomous(island_name=DefaultIsland)(f_2)

    assert f_1() == 1000
    assert f_2() == 1010



def g_2():
    return g_1() + 10


def g_1():
    return 1000

def test_chained_reversed_order(tmpdir):
    _clean_global_state()
    initialize(tmpdir)

    global g_1, g_2

    g_2 = autonomous(island_name="ABC")(g_2)
    g_1 = autonomous(island_name="ABC")(g_1)


    assert g_1() == 1000
    assert g_2() == 1010


