"""Content-addressable storage and immutable value management.

This subpackage provides the foundation for persistent, content-addressed data
storage in Pythagoras. It enables distributed applications to share immutable
values across processes and machines through DataPortals.

Core Concepts
-------------
**DataPortal**: A persistent storage container that manages immutable values
using content-addressable storage. Multiple processes or application sessions
can access the same DataPortal to share data. Typically backed by a shared
filesystem (e.g., Dropbox or Amazon EFS) or cloud storage (e.g., Amazon S3).

**ValueAddr**: A globally unique identifier for an immutable value, derived
from the value's content. Two objects with identical type and content always
produce identical ValueAddr instances, enabling reliable deduplication and
content-based retrieval.

**StorableFn**: Functions that can be persistently stored in DataPortals using
content-addressable storage, enabling function sharing across distributed processes.

Address Structure
-----------------
A ValueAddr conceptually consists of:
- descriptor: Human-readable type/shape information
- hash_signature: SHA-256 hash encoded in base-32

The hash is split into three parts (shard, subshard, hash_tail) to:
- Address filesystem limitations (max files per directory)
- Optimize cloud storage access patterns (S3 prefix distribution)

In filesystem implementations, the address structure naturally maps to directory
hierarchies: `<base>/<shard>/<subshard>/<descriptor>/<hash_tail>`.

Exports
-------
Core classes:
- DataPortal: Portal for storing and retrieving immutable values
- HashAddr: Base class for hash-based addresses (abstract)
- ValueAddr: Content-derived address for immutable values
- StorableFn: Ordinary function with content-addressable storage

Decorators:
- storable: Convert functions to StorableFn instances

Utilities:
- ready: Check if addresses in a nested structure are ready for retrieval
- get: Recursively resolve all addresses in a nested structure
"""


from .data_portal_core_classes import (
    DataPortal, HashAddr, ValueAddr, StorableFn)
from .storable_decorator import storable
from .ready_and_get import ready, get

