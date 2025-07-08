from .._070_protected_code_portals import SimplePreValidatorFn
from .validation_succesful_const import ValidationSuccessClass


def _at_least_X_CPU_cores_free_check(n:int)-> ValidationSuccessClass | None:
    cores = pth.get_unused_cpu_cores()
    if cores >= n-0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_cpu(cores:int) -> SimplePreValidatorFn:
    assert isinstance(cores, int)
    assert cores > 0
    return SimplePreValidatorFn(_at_least_X_CPU_cores_free_check).fix_kwargs(n=cores)


def _at_least_X_G_RAM_free_check(x:int)-> ValidationSuccessClass | None:
    ram = pth.get_unused_ram_mb() / 1024
    if ram >= x-0.1:
        return pth.VALIDATION_SUCCESSFUL


def unused_ram(Gb:int) -> SimplePreValidatorFn:
    assert isinstance(Gb, int)
    assert Gb > 0
    return SimplePreValidatorFn(_at_least_X_G_RAM_free_check).fix_kwargs(x=Gb)


def _check_python_package_and_install_if_needed(
        package_name)-> ValidationSuccessClass | None:
    assert isinstance(package_name, str)
    import importlib, time
    try:
        importlib.import_module(package_name)
        return pth.VALIDATION_SUCCESSFUL
    except:
        portal = self.portal
        address = (pth.get_node_signature()
                    , package_name
                    , "installation_attempt")
        # allow installation retries every 10 minutes
        if (not address in portal._config_settings
                or portal._config_settings[address] < time.time() - 600):
            portal._config_settings[address] = time.time()
            pth.install_package(package_name)
            return pth.VALIDATION_SUCCESSFUL


def installed_packages(*args)  -> list[SimplePreValidatorFn]:
    validators = []
    for package_name in args:
        assert isinstance(package_name, str)
        #TODO: check if the package is available on pypi.org
        new_validator = SimplePreValidatorFn(_check_python_package_and_install_if_needed)
        new_validator = new_validator.fix_kwargs(package_name=package_name)
        validators.append(new_validator)
    return validators