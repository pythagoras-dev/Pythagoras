"""Classes to work with persistent storage and immutable values.

The most important classes in this sub-package are
DataPortal and ValueAddr.

A DataPortal is a container for storing and retrieving values.
In distributed applications, multiple application sessions / processes
can access the same DataPortal, which enables them to interact
via passing values through the portal.

A ValueAddr is a unique identifier for an immutable value.
Two objects with exactly the same type and value will always have
exactly the same ValueAddr-es.

Conceptually, ValueAddr consists of 2 strings: a descriptor, and a hash signature.
A descriptor contains human-readable information about an object's type.
A hash string contains the object's hash signature.

Under the hood, the hash signature is further split into 3 strings:
a shard, a subshard and a hash tail.
This is done to address limitations of some file systems
and to optimize work sith cloud storage (e.g. S3).

Typically, a DataPortal is implemented as
a shared directory on a file system (e.g., Amazon EFS),
or as a shared bucket in a cloud storage (e.g., Amazon S3).
In this case, a ValueAddr becomes a part of a file path
or a URL (e.g., a hash serves as a filename,
and a prefix is a folder name).
"""


from .data_portal_core_classes import (
    DataPortal, HashAddr, ValueAddr, StorableFn)
from .storable_decorator import storable
from .ready_and_get import ready, get

