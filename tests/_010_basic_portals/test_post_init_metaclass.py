import pytest
from pythagoras._010_basic_portals.post_init_metaclass import PostInitMeta

class TestPostInitMeta:

    def test_basic_execution_order(self):
        """
        Verify that __init__ is called before __post_init__.
        """
        call_order = []

        class MyClass(metaclass=PostInitMeta):
            def __init__(self):
                call_order.append("init")

            def __post_init__(self):
                call_order.append("post_init")

        _ = MyClass()
        assert call_order == ["init", "post_init"]

    def test_flags_setting_and_order(self):
        """
        Verify that _init_finished is set to True before __post_init__ runs,
        and _post_init_finished is set to True after __post_init__ runs.
        """
        class MyClassWithFlags(metaclass=PostInitMeta):
            _init_finished = False
            _post_init_finished = False
            
            def __init__(self):
                # Flags are initialized to False (via class attributes in this case, 
                # or could be instance attributes set here)
                pass

            def __post_init__(self):
                # Check _init_finished is already True
                if self._init_finished:
                    self.flag_status_in_post_init = "Correct"
                else:
                    self.flag_status_in_post_init = "Incorrect"
                
                # Check _post_init_finished is still False (it's set after this method returns)
                if not self._post_init_finished:
                    self.post_flag_status_in_post_init = "Correct"
                else:
                    self.post_flag_status_in_post_init = "Incorrect"

        obj = MyClassWithFlags()
        
        assert obj.flag_status_in_post_init == "Correct"
        assert obj.post_flag_status_in_post_init == "Correct"
        
        # Finally both should be True
        assert obj._init_finished is True
        assert obj._post_init_finished is True

    def test_no_post_init(self):
        """
        Verify that a class without __post_init__ works correctly.
        """
        class MyClassNoPostInit(metaclass=PostInitMeta):
            def __init__(self):
                self.initialized = True

        obj = MyClassNoPostInit()
        assert obj.initialized

    def test_non_callable_post_init(self):
        """
        Verify that TypeError is raised if __post_init__ is not callable.
        """
        class MyClassBadPostInit(metaclass=PostInitMeta):
            __post_init__ = "not a method"

        with pytest.raises(TypeError, match=r"__post_init__\(\) must be callable"):
            MyClassBadPostInit()

    def test_exception_in_post_init(self):
        """
        Verify that exceptions in __post_init__ are caught and re-raised correctly.
        """
        class MyClassErrorPostInit(metaclass=PostInitMeta):
            def __post_init__(self):
                raise ValueError("Something went wrong")

        # The metaclass re-raises type(e) with a new message
        with pytest.raises(ValueError, match="Error in __post_init__: Something went wrong"):
            MyClassErrorPostInit()

    def test_flags_not_created_if_missing(self):
        """
        Verify that flags are not created if they don't exist on the instance/class.
        """
        class MyClassNoFlags(metaclass=PostInitMeta):
            pass

        obj = MyClassNoFlags()
        assert not hasattr(obj, "_init_finished")
        assert not hasattr(obj, "_post_init_finished")

    def test_flags_as_instance_attributes(self):
        """
        Verify flags logic works when they are instance attributes set in __init__.
        """
        class MyClassInstanceFlags(metaclass=PostInitMeta):
            def __init__(self):
                self._init_finished = False
                self._post_init_finished = False

        obj = MyClassInstanceFlags()
        assert obj._init_finished is True
        assert obj._post_init_finished is True
