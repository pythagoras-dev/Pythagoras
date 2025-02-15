from pythagoras.___OLD_autonomous.call_graph_explorer import *

def a():
    return {"a"}

def b():
    return a() | {"b"}

def c():
    return b() | {"c"}

def d():
    return c() | {"d"}

def e():
    return d() | {"e"}

def f():
    return a() | {"f"}

def g():
    return f() | {"g"}

def h():
    return g() | {"h"}

def i():
    return h() | d() | {"i"}

def test_diamond():
    assert get_referenced_names(a) == {
        "a":{"a"}}
    assert get_referenced_names(b) == {
        "b":{"b","a"}}
    assert get_referenced_names(c) == {
        "c":{"c","b"}}
    assert get_referenced_names(d) == {
        "d":{"d","c"}}
    assert get_referenced_names(e) == {
        "e":{"e","d"}}
    assert get_referenced_names(f) == {
        "f":{"f","a"}}
    assert get_referenced_names(g) == {
        "g":{"g","f"}}
    assert get_referenced_names(h) == {
        "h":{"h","g"}}
    assert get_referenced_names(i) == {
        "i":{"i","h","d"}}
    assert explore_call_graph_shallow([a, b, c, d, e, f, g, h, i]) == {
        "a":{"a"},"b":{"b","a"},"c":{"c","b"},"d":{"d","c"}
        ,"e":{"e","d"},"f":{"f","a"},"g":{"g","f"},"h":{"h","g"}
        ,"i":{"i","h","d"}}
    all_funcs = [a, b, c, d, e, f, g, h, i]
    all_names = {"a", "b", "c", "d", "e", "f", "g", "h", "i"}
    deep_graph = explore_call_graph_deep([a, b, c, d, e, f, g, h, i])
    for fnk in all_funcs:
        assert deep_graph[fnk.__name__] == fnk()