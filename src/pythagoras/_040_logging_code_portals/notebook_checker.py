
_is_in_notebook: bool|None = None

def is_executed_in_notebook() -> bool:
    """Return whether code is running inside a Jupyter/IPython notebook.

    Uses a lightweight heuristic: checks if IPython is present and whether the
    current shell exposes the set_custom_exc attribute, which is specific to
    IPython interactive environments (including Jupyter).

    Returns:
        bool: True if running inside a Jupyter/IPython notebook, False otherwise.
    """
    global _is_in_notebook
    if _is_in_notebook is not None:
        return _is_in_notebook
    _is_in_notebook = False
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is not None and hasattr(ipython, "set_custom_exc"):
            _is_in_notebook = True
            return True
        else:
            return False
    except:
        return False