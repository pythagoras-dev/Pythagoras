class NotPicklable:
    def __getstate__(self):
        """This method is called when the object is pickled."""
        raise TypeError(f"{type(self).__name__} cannot be pickled")

    def __setstate__(self, state):
        """This method is called when the object is unpickled."""
        raise TypeError(f"{type(self).__name__} cannot be unpickled")
