"""Application-level logging infrastructure for Pythagoras.

This subpackage extends OrdinaryCodePortal with comprehensive logging capabilities,
capturing function executions, stdout/stderr, events, and exceptions to
persistent storage shared across the entire application.

Core Concepts
-------------
**LoggingCodePortal**: Extends OrdinaryCodePortal with application-level and
function-level logging. Maintains three persistent dictionaries:
- _run_history: Function execution artifacts (attempts, results, outputs)
- _crash_history: Exception logs organized by date
- _event_history: Custom event logs organized by date

**LoggingFn**: Function wrapper created by the @logging decorator. Extends
OrdinaryFn with automatic logging of execution attempts, results, exceptions,
and captured stdout/stderr.

**LoggingFnCallSignature**: Unique identifier combining a function and its
arguments, used to organize and retrieve execution artifacts in storage.

**LoggingFnExecutionRecord**: Read-only view of artifacts from a completed
execution session, providing access to results, outputs, crashes, and events.

**LoggingFnExecutionFrame**: Context manager that tracks a single execution
attempt, capturing stdout/stderr and recording execution metadata.

**KwArgs / PackedKwArgs / UnpackedKwArgs**: Dictionary subclasses for managing
function arguments. PackedKwArgs stores arguments as ValueAddr references;
UnpackedKwArgs stores resolved values.

Main Exports
------------
Portal and function classes:
- LoggingCodePortal: Portal with execution logging and output capture
- LoggingFn: Wrapper for functions with automatic execution logging
- LoggingFnCallSignature: Identifier for a specific function call
- LoggingFnExecutionRecord: Read-only access to execution artifacts
- LoggingFnExecutionFrame: Context manager for execution tracking

Argument handling:
- KwArgs, PackedKwArgs, UnpackedKwArgs: Argument dictionary classes

Decorator:
- logging: Convert functions to LoggingFn instances

Logging utilities:
- log_exception(): Log the current exception to the active portal
- log_event(): Log custom events with arbitrary keyword arguments
"""

from .logging_portal_core_classes import *
from .execution_environment_summary import *
from .logging_decorator import *

