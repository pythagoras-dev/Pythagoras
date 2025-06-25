from .data_portal_core_classes import HashAddr

def ready(obj, seen=None):
    if seen is None:
        seen = set()

    if id(obj) in seen:
        return True

    seen.add(id(obj))

    if isinstance(obj, HashAddr):
        return obj.ready
    elif isinstance(obj, (list,tuple)):
        return all(ready(item, seen) for item in obj)
    elif isinstance(obj, dict):
        return all(ready(value, seen) for key, value in obj.items())
    else:
        return True


def get(obj, seen=None):
    if seen is None:
        seen = dict()

    if id(obj) in seen:
        return seen[id(obj)]

    # For mutable objects that could contain circular references,
    # add a placeholder to break recursion
    if isinstance(obj, (list, dict)):
        # Create an empty container of the same type as a placeholder
        placeholder = type(obj)()
        seen[id(obj)] = placeholder

        if isinstance(obj, list):
            result = [get(item, seen) for item in obj]
            # Update the placeholder with the actual values
            placeholder.extend(result)
            return placeholder
        elif isinstance(obj, dict):
            result = {key: get(value, seen) for key, value in obj.items()}
            # Update the placeholder with the actual values
            placeholder.update(result)
            return placeholder

    if isinstance(obj, HashAddr):
        result = obj.get()
    elif isinstance(obj, tuple):
        result = tuple(get(item, seen) for item in obj)
    else:
        result = obj

    seen[id(obj)] = result
    return result
