# Pythagoras

[![PyPI version](https://img.shields.io/pypi/v/Pythagoras.svg)](https://pypi.org/project/Pythagoras/)
[![Python versions](https://img.shields.io/pypi/pyversions/Pythagoras.svg)](https://github.com/pythagoras-dev/Pythagoras)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/Pythagoras?color=blue)](https://pypistats.org/packages/pythagoras)
[![Code style: pep8](https://img.shields.io/badge/code_style-pep8-blue.svg)](https://peps.python.org/pep-0008/)
[![Docstring Style: Google](https://img.shields.io/badge/docstrings_style-Google-blue)](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)



Planet-scale distributed computing in Python.

**!!! RESEARCH PREVIEW !!!**

## What is it?

Pythagoras is a super-scalable, easy-to-use, and
low-maintenance framework for (1) massive algorithm parallelization and 
(2) hardware usage optimization in Python. It simplifies and speeds up 
data science, machine learning, and AI workflows.

Pythagoras excels at complex, long-running, resource-demanding computations. 
It’s not recommended for real-time, latency-sensitive workflows.

## Tutorials

Pythagoras elevates two popular techniques — memoization and parallelization — 
to a global scale and then fuses them, unlocking performance and scalability 
that were previously out of reach.

* [Pythagoras 101: Introduction to Memoization](https://pythagoras.link/tutorial-101)

* [Pythagoras 102: Parallelization Basics](https://pythagoras.link/tutorial-102)

Drawing from many years of functional-programming practice, 
Pythagoras extends these proven ideas to the next level. 
In a Pythagoras environment, you can seamlessly employ your 
preferred functional patterns, augmented by new capabilities.

* [Pythagoras 203: Work with Functions](https://pythagoras.link/tutorial-203)

**!!! BOOKMARK THIS PAGE AND COME BACK LATER, WE WILL PUBLISH MORE TUTORIALS SOON !!!**

## Videos

* [15-minute Demo](https://pythagoras.link/15-min-demo)

* [Data Phoenix Webinar, August 27, 2025](https://youtu.be/eb6_atu1RQI) ([slides](https://docs.google.com/presentation/d/1fGBqnp0aqVHPJ-BYGYnUll1_TJI_WObAbEVX89Z3-yA))


## Usage Examples

Importing Pythagoras:
```python
from pythagoras.core import *
import pythagoras as pth
```

Creating a portal based on a (shared) folder:
```python
my_portal = get_portal("./my_local_folder")
```

Checking the state of a portal:
```python
my_portal.describe()
```

Decorating a function:
```python
@pure()
def my_long_running_function(a:float, b:float) -> float:
  from time import sleep # imports must be placed inside a pure function
  sleep(5)
  return a+10*b
```

Using a decorated function synchronously:
```python
result = my_long_running_function(a=1, b=2) # only named arguments are allowed
```

Using a decorated function asynchronously:
```python
future_result_address = my_long_running_function.swarm(a=10, b=20)
if ready(future_result_address):
    result = get(future_result_address)
```

Pre-conditions for executing a function:
```python
@pure(pre_validators=[
    unused_ram(Gb=5),
    installed_packages("scikit-learn","pandas"),
    unused_cpu(cores=10)])
def my_long_running_function(a:float, b:float) -> float:
  from time import sleep
  sleep(5)
  return a+10*b
```

Recursion:
```python
@pure(pre_validators=[recursive_parameters("n")])
def factorial(n:int)->int:
  if n == 1:
    return 1
  else:
    return n*factorial(n=n-1) # only named arguments are allowed
```

Partial function application:
```python
@pure()
def my_map(input_list:list, transformer: PureFn)->list:
  result = []
  for element in input_list:
    transformed_element = transformer(x=element)
    result.append(transformed_element)
  return result

@pure()
def my_square(x):
  return x*x

result = my_map(input_list=[1,2,3,4,5], transformer=my_square)

my_square_map = my_map.fix_kwargs(transformer = my_square)

result = my_square_map(input_list=[1,2,3,4,5])
```

Mutually recursive functions:
```python
@pure(pre_validators=recursive_parameters("n"))
def is_even(n:int, is_odd ,is_even)->bool:
  if n in {0,2}:
    return True
  else:
    return is_odd(n=n-1, is_even=is_even, is_odd=is_odd)

@pure(pre_validators=recursive_parameters("n"))
def is_odd(n:int, is_even, is_odd)->bool:
  if n in {0,2}:
    return False
  else:
    return is_even(n=n-1, is_odd=is_odd, is_even=is_even)

(is_even, is_odd) = (
  is_even.fix_kwargs(is_odd=is_odd, is_even=is_even)
  , is_odd.fix_kwargs(is_odd=is_odd, is_even=is_even) )

assert is_even(n=10)
assert is_odd(n=11)
```

## Core Concepts

 * **Portal**: An application's "window" into the non-ephemeral world outside the current application
  execution session. It's a connector that enables a link between a runtime-only ephemeral state and
  a persistent state that can be saved and loaded across multiple runs of the application and across
  multiple computers. Portals provide a unified interface for data persistence, caching, and state
  management across distributed systems. They abstract away the complexities of storage backends
  (local filesystem, cloud storage, etc.) and handle serialization/deserialization transparently.
  This allows applications to seamlessly work with persistent data while maintaining isolation between
  runtime and storage concerns. A program can use multiple portals, each with its own storage backend, and
  each portal can be used by multiple applications. A portal defines a context for the execution of
  pure functions, which is used to cache and retrieve results. 

* **Autonomous Function**: A self-contained function that does not depend on external
  imports or definitions. All necessary imports must be done inside the function body.
  These functions cannot use global objects (except built-ins), yield statements, or nonlocal variables.
  They must be called with keyword arguments only to ensure clear parameter passing.
  This design ensures complete isolation and portability, allowing the function to execute
  independently on any machine in a distributed system. The autonomous nature makes these
  functions ideal building blocks for parallel and distributed computing workflows, as they
  carry all their dependencies with them and maintain clear interfaces through strict
  parameter passing requirements.

* **Pure Function**: A special type of autonomous function that has no side effects and always
  returns the same result for the same arguments. This means the function's output depends solely
  on its input parameters, without relying on any external state or modifying anything outside its scope.
  Pythagoras caches the results of pure functions using content-based addressing, so if the function
  is called multiple times with the same arguments, the function is executed only once, and the cached
  result is returned for all subsequent executions. This caching mechanism (also known as memoization)
  works seamlessly across different machines in a distributed system, enabling significant performance
  improvements for computationally intensive workflows.

* **Validator**: An autonomous function that checks if certain conditions are met before or after 
  the execution of a pure function. Pre-validators run before the function, and post-validators run after.
  They can be passive (e.g., check for available RAM) or active (e.g., install a missing library).
  Validators help ensure reliable execution across distributed systems by validating requirements 
  and system state. Multiple validators can be combined using the standard decorator syntax 
  to create comprehensive validation chains.

* **Value Address**: A globally unique address of an ***immutable value***, derived from its content
  (type and value). It consists of a human-readable descriptor (often based on the object's type
  and shape/length) and a hash signature (SHA-256, encoded) split into parts for filesystem/storage
  efficiency. Creating a ValueAddr(data) computes the content hash of data and stores the value
  in the active portal's storage (if not already stored), allowing that value to be retrieved later
  via the address. These addresses are used extensively by the portal to identify stored results
  and to reference inputs/outputs across distributed systems.

* **Execution Result Address**: A special type of Value Address that represents the result of a pure
  function execution. It combines the function's signature with its input parameters to create a unique
  identifier. When a function is executed in swarm mode, it immediately returns an Execution Result Address. This address
  acts as a "future" reference that can be used to check execution status and retrieve results 
  once they become available. The address remains valid across application restarts and
  can be shared between different machines in the distributed system.

* **Swarming**: An asynchronous execution model where you do not know when your function will
  be executed, what machine will execute it, and how many times it will be executed.
  Pythagoras ensures that the function will be eventually executed at least once but does not
  offer any further guarantees. This model enables maximum flexibility in distributed execution
  by decoupling the function call from its actual execution. Functions can be queued, load-balanced,
  retried on failure, and executed in parallel across multiple machines automatically. The trade-off
  is reduced control over execution timing and location, in exchange for improved scalability,
  fault tolerance, and resource utilization across the distributed system.

## How to get it?

The source code is hosted on GitHub at: https://github.com/pythagoras-dev/pythagoras

Installers for the latest released version are available 
at the Python package index at: https://pypi.org/project/pythagoras

Using uv :
```
uv add pythagoras
```

Using pip (legacy alternative to uv):
```
pip install pythagoras
```

## Dependencies

* [persidict](https://pypi.org/project/persidict)
* [parameterizable](https://pypi.org/project/parameterizable/)
* [jsonpickle](https://jsonpickle.github.io)
* [joblib](https://joblib.readthedocs.io)
* [lz4](https://python-lz4.readthedocs.io)
* [pandas](https://pandas.pydata.org)
* [numpy](https://numpy.org)
* [psutil](https://psutil.readthedocs.io)
* [boto3](https://boto3.readthedocs.io)
* [pytest](https://pytest.org)
* [moto](http://getmoto.org)
* [boto3](https://boto3.readthedocs.io)
* [scipy](https://www.scipy.org)
* [jsonpickle](https://jsonpickle.github.io)
* [scikit-learn](https://scikit-learn.org)
* [autopep8](https://pypi.org/project/autopep8)
* [deepdiff](https://zepworks.com/deepdiff/current/)
* [nvidia-ml-p](https://pypi.org/project/nvidia-ml-py/)
* [uv](https://docs.astral.sh/uv/)

## Key Contacts

* [Vlad (Volodymyr) Pavlov](https://www.linkedin.com/in/vlpavlov/)

## About The Name

Pythagoras of Samos was a famous ancient Greek thinker and scientist 
who was the first man to call himself a philosopher ("lover of wisdom"). 
He is most recognised for his many mathematical findings, 
including the Pythagorean theorem. 

Not everyone knows that in antiquity, Pythagoras was also credited with 
major astronomical discoveries, such as sphericity of the Earth 
and the identity of the morning and evening stars as the planet Venus.