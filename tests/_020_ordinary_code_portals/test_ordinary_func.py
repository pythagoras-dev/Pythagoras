from pythagoras import OrdinaryFn, _PortalTester, OrdinaryCodePortal


def simple_function(a:int,b:int) -> int:
    return a+b

def test_ordinary_function(tmpdir):
    """Test basic OrdinaryFn functionality and wrapping."""
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
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
    with _PortalTester(OrdinaryCodePortal, root_dict=tmpdir) as t:
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




