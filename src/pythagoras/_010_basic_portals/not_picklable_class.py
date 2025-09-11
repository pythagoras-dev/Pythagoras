class NotPicklable:
    """A mixin class that prevents objects from being pickled or unpickled.

    This class provides a mechanism to explicitly prevent instances from being
    serialized using Python's pickle module. Classes that inherit from this
    mixin will raise TypeError exceptions when pickle attempts to serialize
    or deserialize them.

    This is useful for objects that contain non-serializable resources or
    should not be persisted for security or architectural reasons.
    """

    def __getstate__(self):
        """Prevent object serialization by raising TypeError.

        This method is called by pickle when attempting to serialize the object.
        It unconditionally raises a TypeError to prevent pickling.

        Raises:
            TypeError: Always raised to prevent the object from being pickled.
        """
        raise TypeError(f"{type(self).__name__} cannot be pickled")

    def __setstate__(self, state):
        """Prevent object deserialization by raising TypeError.

        This method is called by pickle when attempting to deserialize the object.
        It unconditionally raises a TypeError to prevent unpickling.

        Args:
            state: The state dictionary that would be used for unpickling.

        Raises:
            TypeError: Always raised to prevent the object from being unpickled.
        """
        raise TypeError(f"{type(self).__name__} cannot be unpickled")
