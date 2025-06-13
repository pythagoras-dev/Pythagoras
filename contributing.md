We follow the same title-prefix conventions used in pandas. 
Below are common prefixes and guidance on when to apply each:

```
ENH: Enhancement, new functionality
BUG: Bug fix
DOC: Additions/updates to documentation
TST: Additions/updates to tests
BLD: Updates to the build process/scripts
PERF: Performance improvement
TYP: Type annotations
CLN: Code cleanup
```

While creating or calling functions, we prefer to 
use named (keyword) arguments / parameters over positional ones. 
This improves code readability and reduces the risk of errors. 
This also unifies function usage across the code, because 
for some specific types of functions (e.g. autonomous and pure functions) 
positional arguments are not allowed.