class NotPicklable:
    def __getstate__(self):
        raise TypeError(f"{type(self).__name__} cannot be pickled")

    def __setstate__(self, state):
        raise TypeError(f"{type(self).__name__} cannot be unpickled")
