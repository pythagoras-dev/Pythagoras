# Pythagoras

[![PyPI version](https://img.shields.io/pypi/v/Pythagoras.svg)](https://pypi.org/project/Pythagoras/)
[![Python versions](https://img.shields.io/pypi/pyversions/Pythagoras.svg)](https://github.com/pythagoras-dev/Pythagoras)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/Pythagoras?color=blue)](https://pypistats.org/packages/pythagoras)
[![Code style: pep8](https://img.shields.io/badge/code_style-pep8-blue.svg)](https://peps.python.org/pep-0008/)
[![Docstring Style: Google](https://img.shields.io/badge/docstrings_style-Google-blue)](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
[![Ruff](https://github.com/pythagoras-dev/Pythagoras/actions/workflows/ruff.yml/badge.svg?branch=master)](https://github.com/pythagoras-dev/Pythagoras/actions/workflows/ruff.yml)


Planet-scale distributed computing in Python.

**!!! RESEARCH PREVIEW !!!**

## What is it?

Pythagoras is a super-scalable, easy-to-use, and
low-maintenance framework for (1) massive algorithm parallelization and 
(2) hardware usage optimization in Python. It simplifies and speeds up 
data science, machine learning, and AI workflows.

Pythagoras excels at complex, long-running, resource-demanding computations. 
It’s not recommended for real-time, latency-sensitive workflows.

For a comprehensive list of terms and definitions, see the [Glossary](https://github.com/pythagoras-dev/pythagoras/blob/master/GLOSSARY.md).

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

* **Portal**: A persistent gateway that connects your application to the world beyond 
  the current execution session. Portals link runtime state to persistent storage that 
  survives across multiple runs and machines. They provide a unified interface for data 
  persistence, caching, and state management, abstracting away storage backend complexities 
  (local filesystem, cloud storage, etc.) and handling serialization transparently. 
  A program can use multiple portals, each with its own storage backend, and each portal 
  can serve multiple applications. Portals define the execution context for pure functions, 
  enabling result caching and retrieval.

* **Autonomous Function**: A self-contained function with no external dependencies. 
  All imports must be done inside the function body. These functions cannot use global 
  objects (except built-ins), yield statements, or nonlocal variables, and must be called 
  with keyword arguments only. This design ensures complete isolation and portability, 
  making autonomous functions ideal building blocks for distributed computing—they carry 
  all dependencies with them and maintain clear interfaces.

* **Pure Function**: An autonomous function that has no side effects and always returns 
  the same result for the same arguments. Pythagoras caches pure function results using 
  content-based addressing: if a function is called multiple times with identical arguments, 
  it executes only once, and cached results are returned for subsequent calls. This 
  memoization works seamlessly across machines in a distributed system, enabling significant 
  performance improvements for computationally intensive workflows.

* **Validator**: An autonomous function that checks conditions before or after executing 
  a pure function. Pre-validators run before execution, post-validators run after. 
  Validators can be passive (e.g., check available RAM) or active (e.g., install a missing 
  library). They help ensure reliable distributed execution by validating requirements 
  and system state. Multiple validators can be combined using standard decorator syntax.

* **Value Address**: A globally unique, content-derived address for an **immutable value**. 
  It consists of a human-readable descriptor (based on type and shape/length) and a hash 
  signature (SHA-256) split into parts for storage efficiency. Creating a `ValueAddr(data)` 
  computes the content hash and stores the value in the active portal's storage, allowing 
  later retrieval via the address. Value addresses identify stored results and reference 
  inputs/outputs across distributed systems.

* **Execution Result Address**: A Value Address representing the result of a pure function 
  execution. It combines the function's signature with input parameters to create a unique 
  identifier. In swarm mode, functions immediately return an Execution Result Address that 
  acts as a "future" reference for checking execution status and retrieving results. 
  These addresses remain valid across application restarts and can be shared between machines.

* **Swarming**: An asynchronous execution model where you don't know when, where, or how 
  many times your function will execute. Pythagoras guarantees eventual execution at least 
  once but offers no further guarantees. This model maximizes flexibility by decoupling 
  function calls from execution—functions can be queued, load-balanced, retried on failure, 
  and parallelized automatically. The trade-off is reduced control over timing and location 
  in exchange for improved scalability, fault tolerance, and resource utilization.

For a complete list of terms and detailed definitions, see the [Glossary](https://github.com/pythagoras-dev/pythagoras/blob/master/GLOSSARY.md).

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
* [mixinforge](https://pypi.org/project/mixinforge/)
* [jsonpickle](https://jsonpickle.github.io)
* [joblib](https://joblib.readthedocs.io)
* [lz4](https://python-lz4.readthedocs.io)
* [pandas](https://pandas.pydata.org)
* [numpy](https://numpy.org)
* [psutil](https://psutil.readthedocs.io)
* [boto3](https://boto3.readthedocs.io)
* [pytest](https://pytest.org)
* [moto](http://getmoto.org)
* [scipy](https://www.scipy.org)
* [scikit-learn](https://scikit-learn.org)
* [autopep8](https://pypi.org/project/autopep8)
* [deepdiff](https://zepworks.com/deepdiff/current/)
* [nvidia-ml-py](https://pypi.org/project/nvidia-ml-py/)
* [uv](https://docs.astral.sh/uv/)


## Project Statistics

<!-- MIXINFORGE_STATS_START -->
| Metric | Main code | Unit Tests | Total |
|--------|-----------|------------|-------|
| Lines Of Code (LOC) | 11135 | 16045 | 27180 |
| Source Lines Of Code (SLOC) | 4308 | 9747 | 14055 |
| Classes | 53 | 46 | 99 |
| Functions / Methods | 465 | 1284 | 1749 |
| Files | 62 | 223 | 285 |
<!-- MIXINFORGE_STATS_END -->

## Contributing

Interested in contributing to Pythagoras? Please see our [Contributing Guidelines](https://github.com/pythagoras-dev/pythagoras/blob/master/CONTRIBUTING.md).

For project documentation standards, see:
* [Glossary](https://github.com/pythagoras-dev/pythagoras/blob/master/GLOSSARY.md)
* [Unit Tests Guidelines](https://github.com/pythagoras-dev/pythagoras/blob/master/unit_tests.md)
* [Docstrings and Comments Guidelines](https://github.com/pythagoras-dev/pythagoras/blob/master/docstrings_comments.md)
* [Type Hints Guidelines](https://github.com/pythagoras-dev/pythagoras/blob/master/type_hints.md)

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