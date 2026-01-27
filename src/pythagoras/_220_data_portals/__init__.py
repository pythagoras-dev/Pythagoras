"""Persistent data storage with content-addressable addressing.

This subpackage extends BasicPortal with persistent storage capabilities
using persidict. It enables distributed applications to share immutable values
across processes and machines through DataPortals.

Core Concepts
-------------
**DataPortal**: Extends BasicPortal with persistent storage for inputs,
outputs, and metadata using persidict. Multiple processes can access the same
DataPortal to share data, typically backed by a shared filesystem (e.g., Dropbox
or Amazon EFS) or cloud storage (e.g., Amazon S3).

**HashAddr**: Base address type representing a hash-keyed location in persistent
storage. Provides the foundation for content-addressable retrieval.

**ValueAddr**: Address type for values stored in persistent storage. Derived
from the value's content, ensuring identical objects produce identical addresses.

**StorableObject**: Minimal portal-aware base class for objects that work with
DataPortal. Provides the .addr property for content-addressable storage.

Address Structure
-----------------
A HashAddr consists of:
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
- DataPortal: Portal with persistent storage via persidict
- HashAddr: Base class for hash-based addresses
- ValueAddr: Content-derived address for immutable values
- StorableObject: Minimal base class for storable portal-aware objects

Utilities:
- ready: Check if all addresses in a structure are available
- get: Resolve all addresses in a structure to their values
"""


from .data_portal_core_classes import *
from .kw_args import *
from .ready_and_get import *

