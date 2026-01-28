from pythagoras._340_autonomous_code_portals.names_usage_analyzer import _analyze_names_in_function


def nested_class_no_pollution():
    """Test that class-level assignments don't pollute function scope."""
    class MyClass:
        x = 1  # This should NOT be added to function's local set
        y = 2

        def method(self):
            return self.x + self.y

    # If 'x' were incorrectly added to locals, this would not be detected
    # as an unclassified name
    import math
    return math.sqrt(x)  # noqa: F821 - x is a global, should be detected as unclassified


def test_nested_class_no_pollution():
    """Verify that class attributes don't leak into function's local namespace."""
    analyzer = _analyze_names_in_function(nested_class_no_pollution)["analyzer"]

    # The class name should be local
    assert "MyClass" in analyzer.names.local
    assert "MyClass" in analyzer.names.accessible

    # Class attributes (x, y) should NOT be in function's local set
    assert "x" not in analyzer.names.local
    assert "y" not in analyzer.names.local

    # 'x' should be detected as unclassified (it's referenced but not defined)
    assert "x" in analyzer.names.unclassified_deep

    # math should be imported
    assert "math" in analyzer.names.imported
    assert "math" in analyzer.imported_packages_deep


def nested_class_with_base():
    """Test class with base class reference."""
    class BaseClass:
        pass

    class DerivedClass(BaseClass):  # BaseClass is referenced in parent scope
        value = 42

    return DerivedClass


def test_nested_class_with_base():
    """Verify that base class references are handled correctly."""
    analyzer = _analyze_names_in_function(nested_class_with_base)["analyzer"]

    # Both class names should be local
    assert "BaseClass" in analyzer.names.local
    assert "DerivedClass" in analyzer.names.local

    # 'value' should NOT leak into function scope
    assert "value" not in analyzer.names.local

    # No unclassified names (BaseClass is defined before use)
    assert analyzer.names.unclassified_deep == set()


def nested_class_external_reference():
    """Test class that references external names."""
    import json

    class MyClass:
        def serialize(self, data):
            return json.dumps(data)  # json is from parent scope

    return MyClass


def test_nested_class_external_reference():
    """Verify that external references from class body are captured."""
    analyzer = _analyze_names_in_function(nested_class_external_reference)["analyzer"]

    # Class name should be local
    assert "MyClass" in analyzer.names.local

    # json is imported in function scope
    assert "json" in analyzer.names.imported
    assert "json" in analyzer.imported_packages_deep

    # Method names should NOT leak
    assert "serialize" not in analyzer.names.local
    assert "data" not in analyzer.names.local


def nested_class_with_decorator():
    """Test class with decorators."""
    def my_decorator(cls):
        return cls

    @my_decorator
    class DecoratedClass:
        x = 1

    return DecoratedClass


def test_nested_class_with_decorator():
    """Verify that class decorators are handled in parent scope."""
    analyzer = _analyze_names_in_function(nested_class_with_decorator)["analyzer"]

    # Both decorator and class should be local
    assert "my_decorator" in analyzer.names.local
    assert "DecoratedClass" in analyzer.names.local

    # Class attribute should NOT leak
    assert "x" not in analyzer.names.local


def false_negative_example():
    """
    This is the false negative scenario from the issue description.
    Before the fix, 'x' from the class would pollute the function's locals,
    causing the analyzer to miss that 'x' is used as a global without import.
    """
    class MyClass:
        x = 1  # Without fix, this would leak into function locals

    # Now use 'x' as if it were a global variable
    return x * 2  # noqa: F821 - This should be detected as unclassified!


def test_false_negative_example():
    """
    Verify the fix prevents the false negative described in the issue.

    Before fix: 'x' from class leaks to function locals, so 'x' usage
                appears valid even though it's not actually accessible.
    After fix: 'x' is correctly identified as unclassified/missing.
    """
    analyzer = _analyze_names_in_function(false_negative_example)["analyzer"]

    # Class name should be local
    assert "MyClass" in analyzer.names.local

    # CRITICAL: 'x' from class should NOT be in function locals
    assert "x" not in analyzer.names.local

    # 'x' should be detected as unclassified (it's used but not defined in function scope)
    assert "x" in analyzer.names.unclassified_deep

    # This proves the false negative is fixed: before the fix, 'x' would
    # incorrectly appear in locals, hiding the fact that it's not accessible
