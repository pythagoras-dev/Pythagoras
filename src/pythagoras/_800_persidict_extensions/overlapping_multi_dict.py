from persidict import PersiDict
from src.pythagoras._010_basic_portals.exceptions import NotPicklableObject, NotSupportedOperation


# TODO: move this class to persidict package?

class OverlappingMultiDict:
    """A class that holds several PersiDict objects with different fyle_type-s.

    The class is designed to be used as a container for several PersiDict objects
    that have different file_type-s. All inner PersiDict objects
    have the same dir_name attribute. Each inner PersiDict object is accessible
    as an attribute of the OverlappingMultiDict object.
    The attribute name is the same as the file_type
    of the inner PersiDict object.

    OverlappingMultiDict allows to store several PersiDict objects
    in a single object, which can be useful for managing multiple types of data
    in a single file directory or in an s3 bucket.

    """
    def __init__(self
                 , dict_type:type
                 , shared_subdicts_params:dict
                 , **individual_subdicts_params):
        assert issubclass(dict_type, PersiDict)
        assert isinstance(shared_subdicts_params, dict)
        self.dict_type = dict_type
        self.shared_subdicts_params = shared_subdicts_params
        self.individual_subdicts_params = individual_subdicts_params
        self.subdicts_names = list(individual_subdicts_params.keys())
        for subdict_name in individual_subdicts_params:
            assert isinstance(individual_subdicts_params[subdict_name], dict)
            self.__dict__[subdict_name] = dict_type(
                **{**shared_subdicts_params
                ,**individual_subdicts_params[subdict_name]
                ,"file_type":subdict_name})

        def __getstate__(self):
            raise NotPicklableObject("This object should never be pickled")

        def __setstate__(self, state):
            raise NotPicklableObject("This object should never be pickled")

        def __getitem__(self, key):
            raise NotSupportedOperation(
                "Individual items should be accessed through nested dicts, "
                + f"which are available via attributes {self.subdicts_names}")

        def __setitem__(self, key, value):
            raise NotSupportedOperation(
                "Individual items should be accessed through nested dicts, "
                + f"which are available via attributes {self.subdicts_names}")

        def __delitem__(self, key):
            raise NotSupportedOperation(
                "Individual items should be accessed through nested dicts, "
                + f"which are available via attributes {self.subdicts_names}")