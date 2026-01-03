from pythagoras import autonomous, _PortalTester, AutonomousCodePortal


def simple_a_function(a:int,b:int)->int:
    # assert isinstance(self,pth.AutonomousFn)
    print(f"{type(self)=}")
    return a+b

def another_a_function()->str:
    return self.name

def test_self_inside_autnms_fnc(tmpdir):
    global simple_a_function, another_a_function
    with _PortalTester(AutonomousCodePortal, root_dict=tmpdir) as t:
        simple_a_function = autonomous()(simple_a_function)
        assert simple_a_function(a=111,b=111000)==111111

        another_a_function = autonomous()(another_a_function)
        assert another_a_function()=="another_a_function"

