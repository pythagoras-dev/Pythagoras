# Pythagoras

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