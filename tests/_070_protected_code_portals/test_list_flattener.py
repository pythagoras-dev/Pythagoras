from pythagoras._070_protected_code_portals import flatten_list

def test_fltattener_int():
    model_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    list_1 = [1, [2, 3, [4, 5, 6], 7, 8], 9]
    list_2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    list_3 = [1, [2, 3, [4, 5, 6], 7, 8], 9]
    list_4 = [1, [2, [3, [4, [5,[6,[7]]]]]],8, 9]
    assert flatten_list(list_1) == model_list
    assert flatten_list(list_2) == model_list
    assert flatten_list(list_3) == model_list
    assert flatten_list(list_4) == model_list


def test_flattener_empty():
    assert flatten_list([]) == []
    assert flatten_list([[[[[[]]]]]]) == []
    assert flatten_list([[],[],[],[],[],[],[],[],[],[]]) == []


def test_flattener_str():
    model_list = ["aaa", "bbb", "ccc", "ddd"]
    list_1 = [[[["aaa"], "bbb"], "ccc"], "ddd"]
    assert flatten_list(list_1) == model_list



