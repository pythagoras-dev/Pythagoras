from .._060_autonomous_code_portals import AutonomousFn, autonomous
from .OK_const import OK
from .package_manager import install_package


def check_python_package_and_install_if_needed(packed_kwargs, package_name):
    assert isinstance(package_name, str)
    import importlib
    try:
        importlib.import_module(package_name)
        return OK
    except:
        install_package(package_name)
        return OK


def installed_packages(package_names:list[str]|str) -> list[AutonomousFn]:
    global check_python_package_and_install_if_needed
    if not isinstance(check_python_package_and_install_if_needed, AutonomousFn):
        check_python_package_and_install_if_needed = autonomous()(
            check_python_package_and_install_if_needed)

    result = []
    if isinstance(package_names, str):
        package_names = [package_names]
    for package_name in package_names:
        result.append(check_python_package_and_install_if_needed.fix_kwargs(
            package_name=package_name))
    return result
