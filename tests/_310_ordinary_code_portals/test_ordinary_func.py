from pythagoras import OrdinaryFn, _PortalTester, OrdinaryCodePortal


def simple_function(a:int,b:int) -> int:
    return a+b

def test_ordinary_function(tmpdir):
    """Test basic OrdinaryFn functionality and wrapping."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(simple_function)
        f = OrdinaryFn(f)

        assert f(a=1, b=2) == 3
        assert f(a=3, b=4) == 7



def fibonacci(n:int) -> int:
    if n < 2:
        return n
    return fibonacci(n=n-1) + fibonacci(n=n-2)

def test_ordinary_function_with_recursion(tmpdir):
    """Test OrdinaryFn with recursive function."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir):
        f = OrdinaryFn(fibonacci)
        f = OrdinaryFn(f)

        assert f(n=6) == 8
        assert f(n=10) == 55


def test_ordinary_fn_properties(tmpdir):
    """Test OrdinaryFn properties: name, source_code, hash_signature."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)
        
        # Test name property
        assert f.name == "simple_function"
        
        # Test source_code property returns normalized source
        source = f.source_code
        assert "def simple_function" in source
        assert "return a+b" in source or "return a + b" in source
        
        # Test hash_signature property
        hash_sig = f.hash_signature
        assert isinstance(hash_sig, str)
        assert len(hash_sig) > 0
        
        # Same function should have same hash
        f2 = OrdinaryFn(simple_function, portal=t.portal)
        assert f.hash_signature == f2.hash_signature


def test_ordinary_fn_execute_method(tmpdir):
    """Test OrdinaryFn execute() method with kwargs."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        # execute() should work like __call__() but only accepts kwargs
        result = f.execute(a=5, b=10)
        assert result == 15

        result = f.execute(a=100, b=200)
        assert result == 300


def test_ordinary_fn_pickling(tmpdir):
    """Test OrdinaryFn can be pickled and unpickled."""
    import pickle

    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        # Pickle the function
        pickled = pickle.dumps(f)

        # Unpickle it
        f_restored = pickle.loads(pickled)

        # Verify it works correctly
        assert f_restored(a=10, b=20) == 30
        assert f_restored.name == "simple_function"
        assert f_restored.source_code == f.source_code


def test_ordinary_fn_identity_key(tmpdir):
    """Test OrdinaryFn identity key uniqueness and consistency."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f1 = OrdinaryFn(simple_function, portal=t.portal)
        f2 = OrdinaryFn(simple_function, portal=t.portal)

        # Same function should have same identity key
        assert f1.get_identity_key() == f2.get_identity_key()

        # Identity key should be a non-empty string
        assert isinstance(f1.get_identity_key(), str)
        assert len(f1.get_identity_key()) > 0

        # Different functions should have different identity keys
        f3 = OrdinaryFn(fibonacci, portal=t.portal)
        assert f1.get_identity_key() != f3.get_identity_key()


def test_ordinary_fn_positional_args_error(tmpdir):
    """Test OrdinaryFn raises error when called with positional args."""
    import pytest
    from pythagoras import FunctionError

    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        # Should raise FunctionError when called with positional args
        with pytest.raises(FunctionError, match="can't be called.*with positional arguments"):
            f(1, 2)

        with pytest.raises(FunctionError, match="can't be called.*with positional arguments"):
            f(10, b=20)


def test_ordinary_fn_available_names(tmpdir):
    """Test OrdinaryFn._available_names() returns correct namespace."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        names = f._available_names()

        # Should contain builtins
        assert "__builtins__" in names

        # Should contain the function itself by name
        assert f.name in names
        assert names[f.name] is f

        # Should contain "self" pointing to the function
        assert "self" in names
        assert names["self"] is f

        # Should contain "pth" module
        assert "pth" in names
        import pythagoras as pth
        assert names["pth"] is pth


def test_ordinary_fn_from_string(tmpdir):
    """Test OrdinaryFn can be created from source code string."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        source_code = """
def multiply(x, y):
    return x * y
"""
        f = OrdinaryFn(source_code, portal=t.portal)

        assert f.name == "multiply"
        assert f(x=3, y=4) == 12
        assert f(x=5, y=6) == 30


def test_ordinary_fn_internal_names(tmpdir):
    """Test internal variable and filename generation."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        # Virtual filename should contain function name and hash
        virtual_file = f._virtual_file_name
        assert "simple_function" in virtual_file
        assert f.hash_signature in virtual_file
        assert virtual_file.endswith(".py")

        # Internal variable names should be unique and contain hash
        kwargs_var = f._kwargs_var_name
        result_var = f._result_var_name
        tmp_fn = f._tmp_fn_name

        assert "kwargs" in kwargs_var
        assert "simple_function" in kwargs_var
        assert f.hash_signature in kwargs_var

        assert "result" in result_var
        assert "simple_function" in result_var
        assert f.hash_signature in result_var

        assert "func" in tmp_fn
        assert "simple_function" in tmp_fn
        assert f.hash_signature in tmp_fn


def test_ordinary_fn_hash_addr_descriptor(tmpdir):
    """Test __hash_addr_descriptor__ method."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
        f = OrdinaryFn(simple_function, portal=t.portal)

        descriptor = f.__hash_addr_descriptor__()

        # Should be lowercase
        assert descriptor == descriptor.lower()

        # Should contain function name
        assert "simple_function" in descriptor

        # Should contain class name
        assert "ordinaryfn" in descriptor


