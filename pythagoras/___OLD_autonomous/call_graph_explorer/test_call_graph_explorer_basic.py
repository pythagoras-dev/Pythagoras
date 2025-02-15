from pythagoras.___OLD_autonomous.call_graph_explorer import *


def f_inner():
    import sys
    a = 10
    x = set(a, sys.api_version)
    return x


def f_outer():
    a = 10
    print(f_inner())
    return a

def test_2_nested_funcs():
    assert get_referenced_names(f_inner) == {
        "f_inner":{"f_inner","set"}}
    assert get_referenced_names(f_outer) == {
        "f_outer":{"f_outer","f_inner","print"}}
    assert explore_call_graph_shallow([f_inner, f_outer]) == {
        "f_inner":{"f_inner"},"f_outer":{"f_outer","f_inner"}}
    assert explore_call_graph_deep([f_inner, f_outer]) == {
        "f_inner": {"f_inner"}, "f_outer": {"f_outer", "f_inner"}}

def a_i():
    import sys
    return sys.api_version
    return 10

def b_i():
    return 100

def test_2_independent_funcs():
    assert get_referenced_names(a_i) == {
        "a_i":{"a_i"}}
    assert get_referenced_names(b_i) == {
        "b_i":{"b_i"}}
    assert explore_call_graph_shallow([a_i, b_i]) == {
        "a_i":{"a_i"},"b_i":{"b_i"}}
    assert explore_call_graph_deep([a_i, b_i]) == {
        "a_i":{"a_i"},"b_i":{"b_i"}}


def x():
    pass

def y():
    return x()

def z():
    return y()

def test_3_funcs_chain():
    assert get_referenced_names(x) == {
        "x":{"x"}}
    assert get_referenced_names(y) == {
        "y":{"y","x"}}
    assert get_referenced_names(z) == {
        "z":{"z","y"}}
    assert explore_call_graph_shallow([x, y, z]) == {
        "x":{"x"},"y":{"y","x"},"z":{"z","y"}}
    assert explore_call_graph_deep([x, y, z]) == {
        "x":{"x"},"y":{"y","x"},"z":{"z","y","x"}}


def a():
    pass

def b():
    while True:
        a()

def c():
    for i in range(10):
        a()
    a()

def d():
    b()
    c()

def test_4_funcs_diamond_graph():
    assert get_referenced_names(a) == {
        "a":{"a"}}
    assert get_referenced_names(b) == {
        "b":{"b","a"}}
    assert get_referenced_names(c) == {
        "c":{"c","a","range"}}
    assert get_referenced_names(d) == {
        "d":{"d","b","c"}}
    assert explore_call_graph_shallow([a, b, c, d]) == {
        "a":{"a"},"b":{"b","a"},"c":{"c","a"},"d":{"d","b","c"}}
    assert explore_call_graph_deep([a, b, c, d]) == {
        "a":{"a"},"b":{"b","a"},"c":{"c","a"},"d":{"d","b","c","a"}}

def aa():
    try:
        dd()
    except:
        pass

def bb():
    while True:
        aa()

def cc():
    for i in range(10):
        aa()
    aa()

def dd():
    bb()
    cc()


def test_diamond_loop():
    assert get_referenced_names(aa) == {
        "aa":{"aa","dd"}}
    assert explore_call_graph_shallow([aa,bb,cc,dd]) == {
        "aa":{"aa","dd"},"bb":{"bb","aa"}
        ,"cc":{"cc","aa"},"dd":{"dd","bb","cc"}}
    assert explore_call_graph_deep([aa,bb,cc,dd]) == {
        "aa":{"aa","dd","bb","cc"},"bb":{"aa","dd","bb","cc"}
        ,"cc":{"aa","dd","bb","cc"},"dd":{"dd","bb","cc","aa"}}

