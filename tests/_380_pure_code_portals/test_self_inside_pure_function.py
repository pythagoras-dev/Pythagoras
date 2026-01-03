from pythagoras import autonomous, _PortalTester, AutonomousCodePortal


def simple_p_function(a:int,b:int)->int:
    # assert isinstance(self,pth.AutonomousFn)
    print(f"{type(self)=}")
    return a+b

def another_p_function()->str:
    return self.name

def test_simple(tmpdir):
    global simple_p_function, another_p_function
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:
        simple_a_function = autonomous()(simple_p_function)
        assert simple_a_function(a=111,b=111000)==111111

        another_p_function = autonomous()(another_p_function)
        assert another_p_function()=="another_p_function"

