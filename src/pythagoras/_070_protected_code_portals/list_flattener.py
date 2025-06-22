

def flatten_list(nested_list):
    """Flatten a list with unlimited nesting levels."""
    assert isinstance(nested_list, list)
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened