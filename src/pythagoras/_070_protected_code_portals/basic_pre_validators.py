from .._070_protected_code_portals import SimplePreValidatorFn
from .validation_succesful_const import ValidationStatusClass


def _at_least_X_CPU_cores_free_check(n:int)-> ValidationStatusClass | None:
    cores = pth.get_unused_cpu_cores()
    if cores >= n-0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_cpu(cores:int) -> SimplePreValidatorFn:
    assert isinstance(cores, int)
    assert cores > 0
    return SimplePreValidatorFn(_at_least_X_CPU_cores_free_check).fix_kwargs(n=cores)


def _at_least_X_G_RAM_free_check(x:int)-> ValidationStatusClass | None:
    ram = pth.get_unused_ram_mb() / 1024
    if ram >= x-0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_ram(Gb:int) -> SimplePreValidatorFn:
    assert isinstance(Gb, int)
    assert Gb > 0
    return SimplePreValidatorFn(_at_least_X_G_RAM_free_check).fix_kwargs(x=Gb)


def _check_python_package_and_install_if_needed(package_name)-> ValidationStatusClass | None:
    assert isinstance(package_name, str)
    import importlib
    try:
        importlib.import_module(package_name)
        return pth.VALIDATION_SUCCESSFUL
    except:
        pth.install_package(package_name)
        return pth.VALIDATION_SUCCESSFUL


def installed_packages(*args)  -> list[SimplePreValidatorFn]:
    validators = []
    for package_name in args:
        assert isinstance(package_name, str)
        new_validator = SimplePreValidatorFn(_check_python_package_and_install_if_needed)
        new_validator = new_validator.fix_kwargs(package_name=package_name)
        validators.append(new_validator)
    return validators