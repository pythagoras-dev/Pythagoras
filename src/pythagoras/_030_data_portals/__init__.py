"""Classes to work with persistent storage and immutable values.

The most important classes in this sub-package are
DataPortal and ValueAddr.

A DataPortal is a container for storing and retrieving immutable values.
In distributed applications, multiple application sessions / processes
can access the same DataPortal, which enables them to interact
via passing values through the portal.

A ValueAddr is a unique identifier for an immutable value.
Two objects with exactly the same type and value will always have
exactly the same ValueAddr-es.

A ValueAddr consists of 2 strings: a descriptor, and a hash.
A descriptor contains human-readable information about an object's type.
A hash string contains the object's hash signature.

Typically, a DataPortal is implemented as
a shared directory on a file system (e.g. Amazon EFS),
or as a shared bucket in a cloud storage (e.g. Amazon S3).
In this case, a ValueAddr becomes a part of file path
or a URL (e.g. a hash serves as a filename,
and a prefix is a folder name).

DataPortal is a subclass of OrdinaryCodePortal.
"""


from .data_portal_core_classes import (
    DataPortal, HashAddr, ValueAddr, StorableFn)
from .storable_decorator import storable
from .ready_and_get import ready, get

