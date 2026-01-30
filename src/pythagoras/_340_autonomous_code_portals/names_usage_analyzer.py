import ast
from functools import cache
from typing import Callable

from .._310_ordinary_code_portals import get_normalized_fn_source_code_str

class NamesUsedInFunction:
    """Classification of all names referenced within a function and its nested scopes.

    This container organizes names into mutually exclusive sets based on their scope
    and origin. It is used to determine whether a function is autonomous by identifying
    external dependencies that would violate self-containment.

    The classification tracks names across the entire function tree (including nested
    functions, classes, lambdas, and comprehensions), distinguishing between:
    - Names defined locally within the function
    - Names explicitly imported inside the function body
    - Names marked as global or nonlocal
    - Names with unresolved origin (potential external dependencies)

    Design Rationale:
        Autonomous functions must be self-sufficient. This requires identifying all
        name references and ensuring they originate from:
        1. Built-in Python objects (checked separately against builtins)
        2. Function parameters or local assignments
        3. Imports within the function body
        4. Other autonomous functions passed as arguments

        Any name not falling into these categories indicates an external dependency
        that would prevent safe serialization and isolated execution.

    Attributes:
        function: Name of the top-level function being analyzed.

        explicitly_global_unbound_deep: Names declared with 'global' keyword in the
            function or nested functions but not subsequently bound locally. These
            reference module-level state and violate autonomy.

        explicitly_nonlocal_unbound_deep: Names declared with 'nonlocal' keyword in
            nested functions but not bound in any enclosing scope within the analyzed
            function. These reference closures and violate autonomy.

        local: Names bound in the top-level function scope through assignment,
            parameter declaration, or local import. These are safe for autonomy.

        imported: Names explicitly imported via import statements within the function
            body. These are safe for autonomy as long as imports are absolute.

        unclassified_deep: Names referenced but not locally bound, not imported, and
            not explicitly marked global/nonlocal. These are potential external
            dependencies or built-ins that need further validation.

        accessible: Working set of all names currently in scope during AST traversal.
            Used to distinguish between external references and names defined in
            enclosing scopes within the analyzed function.

        has_relative_imports: Flag indicating whether the function uses relative
            imports (from . or from ..), which violate autonomy by depending on
            package structure.
    """
    def __init__(self):
        """Initialize all name sets to empty defaults."""
        self.function = None
        self.explicitly_global_unbound_deep = set()
        self.explicitly_nonlocal_unbound_deep = set()
        self.local = set()
        self.imported = set()
        self.unclassified_deep = set()
        self.accessible = set()
        self.has_relative_imports = False

class NamesUsageAnalyzer(ast.NodeVisitor):
    """AST visitor that performs static analysis of name usage for autonomy validation.

    This analyzer traverses the Abstract Syntax Tree of a function to collect
    comprehensive data about all name references, their scopes, and their origins.
    The collected information is used to determine whether a function satisfies
    the autonomy requirements.

    Analysis Strategy:
        The visitor implements a depth-first traversal of the function's AST,
        maintaining scope-aware state as it descends into nested structures:

        1. Top-level function: Records parameters and body-level assignments as local names.

        2. Nested functions/classes/lambdas: Analyzed with fresh sub-analyzers to
           maintain separate scope tracking, then merged back with accessibility
           adjustments.

        3. Comprehensions: Treated as implicit scopes (Python 3 behavior) to prevent
           iterator variable leakage into parent scope.

        4. Name references: Classified as Load (usage), Store (definition), or
           Del (deletion), each handled differently for scope tracking.

        5. Import statements: Recorded as explicitly imported names, safe for autonomy.

        6. Global/nonlocal declarations: Tracked separately as potential autonomy violations.

    Scope Merging:
        When a nested scope completes analysis, its results are merged into the parent:
        - External references (unclassified names) are filtered against the parent's
          accessible set to determine if they're truly external or just parent-scoped.
        - Global/nonlocal declarations bubble up unchanged.
        - The nested scope's own name becomes accessible in the parent.

    Attributes:
        names: NamesUsedInFunction container holding all classification sets.
        imported_packages_deep: Top-level packages imported anywhere in the function tree.
        func_nesting_level: Current depth in the function nesting hierarchy (0 = top-level).
        n_yelds: Count of yield/yield from statements (disqualifies autonomy).
    """
    # TODO: add support for structural pattern matching
    def __init__(self):
        """Initialize the analyzer state and counters."""
        super().__init__()
        self.names = NamesUsedInFunction()
        self.imported_packages_deep = set()
        self.func_nesting_level = 0
        self.n_yelds = 0

    def visit_FunctionDef(self, node):
        """Handle a function definition.

        - For the top-level function: record its name, parameters as locals,
          and traverse its body.
        - For nested functions: analyze them with a fresh analyzer and merge
          relevant sets into the current analyzer, adjusting for accessibility.

        Args:
            node: The ast.FunctionDef node.
        """
        if self.func_nesting_level == 0:
            self.names.function = node.name
            self.func_nesting_level += 1
            for arg in node.args.posonlyargs:
                self.names.local |= {arg.arg}
            for arg in node.args.args:
                self.names.local |= {arg.arg}
            for arg in node.args.kwonlyargs:
                self.names.local |= {arg.arg}
            if node.args.vararg:
                self.names.local |= {node.args.vararg.arg}
            if node.args.kwarg:
                self.names.local |= {node.args.kwarg.arg}
            self.names.accessible |= self.names.local
            self.generic_visit(node)
            self.func_nesting_level -= 1
        else:
            nested = NamesUsageAnalyzer()
            nested.visit(node)
            self.imported_packages_deep |= nested.imported_packages_deep
            nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
            self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
            self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
            nested.names.unclassified_deep -= self.names.accessible
            self.names.unclassified_deep |= nested.names.unclassified_deep
            self.names.local |= {node.name}
            self.names.accessible |= {node.name}

    def visit_Lambda(self, node):
        """Handle a lambda expression.

        Lambdas create a nested scope similar to nested functions. Their
        parameters are local to the lambda and should not leak into the
        parent scope as unclassified names.

        Args:
            node: The ast.Lambda node.
        """
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = "<lambda>"
        nested.func_nesting_level += 1
        for arg in node.args.posonlyargs:
            nested.names.local |= {arg.arg}
        for arg in node.args.args:
            nested.names.local |= {arg.arg}
        for arg in node.args.kwonlyargs:
            nested.names.local |= {arg.arg}
        if node.args.vararg:
            nested.names.local |= {node.args.vararg.arg}
        if node.args.kwarg:
            nested.names.local |= {node.args.kwarg.arg}
        nested.names.accessible |= nested.names.local
        nested.generic_visit(node)
        nested.func_nesting_level -= 1

        # Merge nested lambda's analysis into parent scope
        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

    def visit_AsyncFunctionDef(self, node):
        """Handle an async function definition.

        Async functions are treated similarly to regular nested functions
        when they appear as nested definitions.

        Args:
            node: The ast.AsyncFunctionDef node.
        """
        if self.func_nesting_level == 0:
            self.names.function = node.name
            self.func_nesting_level += 1
            for arg in node.args.posonlyargs:
                self.names.local |= {arg.arg}
            for arg in node.args.args:
                self.names.local |= {arg.arg}
            for arg in node.args.kwonlyargs:
                self.names.local |= {arg.arg}
            if node.args.vararg:
                self.names.local |= {node.args.vararg.arg}
            if node.args.kwarg:
                self.names.local |= {node.args.kwarg.arg}
            self.names.accessible |= self.names.local
            self.generic_visit(node)
            self.func_nesting_level -= 1
        else:
            nested = NamesUsageAnalyzer()
            nested.visit(node)
            self.imported_packages_deep |= nested.imported_packages_deep
            nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
            self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
            self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
            nested.names.unclassified_deep -= self.names.accessible
            self.names.unclassified_deep |= nested.names.unclassified_deep
            self.names.local |= {node.name}
            self.names.accessible |= {node.name}

    def visit_ClassDef(self, node):
        """Handle a nested class definition.

        Classes create their own scope in Python. Assignments and method
        definitions within the class body should not leak into the parent
        function's local namespace. The class name itself becomes a local
        variable in the parent function.

        Args:
            node: The ast.ClassDef node.
        """
        # Analyze the class body in a nested analyzer to capture any
        # external references (e.g., base classes, decorators) without
        # polluting the parent function's locals with class attributes
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = f"<class {node.name}>"
        nested.func_nesting_level += 1

        # Visit base classes and decorators in the parent scope context
        # since these are evaluated in the enclosing scope
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)
        for decorator in node.decorator_list:
            self.visit(decorator)

        # Visit the class body in the nested scope
        for item in node.body:
            nested.visit(item)

        nested.func_nesting_level -= 1

        # Merge the nested analysis: only external references from the
        # class body should bubble up, not the class's own attributes
        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

        self.names.local |= {node.name}
        self.names.accessible |= {node.name}

    def visit_Name(self, node):
        """Track variable usage and binding for a Name node.

        - On load: if the name is not accessible, mark it unclassified and
          accessible.
        - On store: register it as a local and accessible.
        - On del: register it as a local and accessible (del establishes
          local scope in Python, similar to assignment).

        Args:
            node: The ast.Name node.
        """
        if isinstance(node.ctx, ast.Load):
            if node.id not in self.names.accessible:
                self.names.unclassified_deep |= {node.id}
                self.names.accessible |= {node.id}
        if isinstance(node.ctx, ast.Store):
            if node.id not in self.names.accessible:
                self.names.local |= {node.id}
                self.names.accessible |= {node.id}
        if isinstance(node.ctx, ast.Del):
            if node.id not in self.names.accessible:
                self.names.local |= {node.id}
                self.names.accessible |= {node.id}
        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Visit an attribute access expression.

        Currently no special handling is required; traversal continues.

        Args:
            node: The ast.Attribute node.
        """
        self.generic_visit(node)

    def visit_Yield(self, node):
        """Record usage of a yield expression.

        Increments the number of yields found, which disqualifies autonomy.

        Args:
            node: The ast.Yield node.
        """
        self.n_yelds += 1
        self.generic_visit(node)

    def visit_YieldFrom(self, node):
        """Record usage of a 'yield from' expression.

        Increments the number of yields found, which disqualifies autonomy.

        Args:
            node: The ast.YieldFrom node.
        """
        self.n_yelds += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        """Track names bound in exception handlers within try/except.

        Exception handler names become local and accessible when explicitly
        bound with 'as' syntax. Unbound handlers (e.g., 'except ValueError:')
        have handler.name = None and should not be added to name sets.

        Args:
            node: The ast.Try node.
        """
        for handler in node.handlers:
            if handler.name is not None:
                self.names.local |= {handler.name}
                self.names.accessible |= {handler.name}
        self.generic_visit(node)

    def visit_comprehension(self, node):
        """Handle variable binding within a comprehension clause.

        Targets in comprehension generators become local and accessible.

        Args:
            node: The ast.comprehension node or a loop node with a similar API.
        """
        if isinstance(node.target, (ast.Tuple, ast.List)):
            all_targets =node.target.elts
        else:
            all_targets = [node.target]
        for target in all_targets:
            if isinstance(target, ast.Name):
                if target.id not in self.names.accessible:
                    self.names.local |= {target.id}
        self.names.accessible |= self.names.local
        self.generic_visit(node)

    def visit_For(self, node):
        """Handle a for-loop comprehension-like binding.

        Args:
            node: The ast.For node.
        """
        self.visit_comprehension(node)

    def visit_ListComp(self, node):
        """Handle bindings within a list comprehension.

        List comprehensions in Python 3 create an implicit function scope,
        similar to generator expressions. Iterator variables should not
        leak to the parent function scope.

        Args:
            node: The ast.ListComp node.
        """
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = "<listcomp>"
        nested.func_nesting_level += 1

        for gen in node.generators:
            nested.visit_comprehension(gen)

        nested.visit(node.elt)

        nested.func_nesting_level -= 1

        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

    def visit_SetComp(self, node):
        """Handle bindings within a set comprehension.

        Set comprehensions in Python 3 create an implicit function scope,
        similar to list comprehensions. Iterator variables should not
        leak to the parent function scope.

        Args:
            node: The ast.SetComp node.
        """
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = "<setcomp>"
        nested.func_nesting_level += 1

        for gen in node.generators:
            nested.visit_comprehension(gen)

        nested.visit(node.elt)

        nested.func_nesting_level -= 1

        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

    def visit_DictComp(self, node):
        """Handle bindings within a dict comprehension.

        Dict comprehensions in Python 3 create an implicit function scope,
        similar to list comprehensions. Iterator variables should not
        leak to the parent function scope.

        Args:
            node: The ast.DictComp node.
        """
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = "<dictcomp>"
        nested.func_nesting_level += 1

        for gen in node.generators:
            nested.visit_comprehension(gen)

        nested.visit(node.key)
        nested.visit(node.value)

        nested.func_nesting_level -= 1

        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

    def visit_GeneratorExp(self, node):
        """Handle bindings within a generator expression.

        Generator expressions in Python 3 create an implicit function scope.
        Iterator variables should not leak to the parent function scope.

        Args:
            node: The ast.GeneratorExp node.
        """
        nested = NamesUsageAnalyzer()
        nested.func_nesting_level = 0
        nested.names.function = "<genexpr>"
        nested.func_nesting_level += 1

        for gen in node.generators:
            nested.visit_comprehension(gen)

        nested.visit(node.elt)

        nested.func_nesting_level -= 1

        self.imported_packages_deep |= nested.imported_packages_deep
        nested.names.explicitly_nonlocal_unbound_deep -= self.names.accessible
        self.names.explicitly_nonlocal_unbound_deep |= nested.names.explicitly_nonlocal_unbound_deep
        self.names.explicitly_global_unbound_deep |= nested.names.explicitly_global_unbound_deep
        nested.names.unclassified_deep -= self.names.accessible
        self.names.unclassified_deep |= nested.names.unclassified_deep

    def visit_Import(self, node):
        """Register imported names and top-level package usage.

        Args:
            node: The ast.Import node.
        """
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.names.imported |= {name}
            self.imported_packages_deep |= {alias.name.split('.')[0]}
        self.names.accessible |= self.names.imported
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Register names imported from a module and the module itself.

        Handles both absolute and relative imports. Relative imports
        (indicated by node.level > 0) are flagged for rejection in
        autonomous functions.

        Args:
            node: The ast.ImportFrom node.
        """
        # Detect relative imports (from . import x, from .. import y, etc.)
        if node.level > 0:
            self.names.has_relative_imports = True

        # Track the top-level package name, if available
        # For relative imports, node.module can be None (e.g., "from . import x")
        if node.module is not None:
            # Use [0] for consistency with visit_Import: track top-level package
            self.imported_packages_deep |= {node.module.split('.')[0]}

        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.names.imported |= {name}

        self.names.accessible |= self.names.imported
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        """Record names declared as nonlocal within the function.

        Args:
            node: The ast.Nonlocal node.
        """
        nonlocals =  set(node.names)
        self.names.explicitly_nonlocal_unbound_deep |= nonlocals
        self.names.accessible |= nonlocals
        self.generic_visit(node)

    def visit_Global(self, node):
        """Record names declared as global within the function.

        Args:
            node: The ast.Global node.
        """
        globals = set(node.names)
        self.names.explicitly_global_unbound_deep |= globals
        self.names.accessible |= globals
        self.generic_visit(node)

@cache
def _validate_and_parse_function_source(
        normalized_source: str
        ) -> dict[str, NamesUsageAnalyzer | str]:
    """Validate that normalized source is a single function definition and parse it.

    Args:
        normalized_source: Normalized function source code to validate and parse.

    Returns:
        The parsed AST Module containing the function definition.

    Raises:
        ValueError: If the source is not a single conventional function definition.
    """
    lines, line_num = normalized_source.splitlines(), 0
    while lines[line_num].startswith("@"):
        line_num+=1

    if not lines[line_num].startswith("def "):
        raise ValueError(
            "This action can only be applied to conventional functions, "
            "not to instances of callable classes, not to lambda functions, "
            "not to async functions.")
    tree = ast.parse(normalized_source)
    if not isinstance(tree, ast.Module):
        raise ValueError(
            f"Only one high level function definition is allowed to be processed. "
            f"The following code is not allowed: {normalized_source}")
    if not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError(
            f"Only one high level function definition is allowed to be processed. "
            f"The following code is not allowed: {normalized_source}")
    if len(tree.body) != 1:
        raise ValueError(
            f"Only one high level function definition is allowed to be processed. "
            f"The following code is not allowed: {normalized_source}")

    analyzer = NamesUsageAnalyzer()
    analyzer.visit(tree)
    result = dict(analyzer=analyzer, normalized_source=normalized_source)
    return result


def _analyze_names_in_function(
        a_func: Callable | str
        ) -> dict[str, NamesUsageAnalyzer | str]:
    """Perform comprehensive static analysis of name usage within a function.

    This function is the primary entry point for autonomy validation. It normalizes
    the function source code, parses it into an AST, and performs a complete
    traversal to identify all name references and their classifications.

    The analysis process:
        1. Normalizes source code using Pythagoras' code normalizer
        2. Validates the source is a single regular function definition
        3. Parses the normalized source into an AST
        4. Traverses the AST using NamesUsageAnalyzer to collect name usage data
        5. Returns the complete analysis result for autonomy validation

    This analysis is required before an AutonomousFn can be constructed, ensuring
    that the function satisfies all autonomy constraints at decoration time rather
    than discovering violations during execution.

    Args:
        a_func: Function object or source code string to analyze. If a function
            object is provided, its source will be extracted and normalized.

    Returns:
        Dictionary with two keys:
            - analyzer: The NamesUsageAnalyzer instance with complete name
              classification data.
            - normalized_source: The normalized source code string that was analyzed.

    Raises:
        ValueError: If the input is not a single conventional function definition.
            This includes lambda functions, async functions, callable class instances,
            or source code with multiple top-level definitions.

    Example:
        >>> def my_func(x: int) -> int:
        ...     import math
        ...     return math.sqrt(x)
        >>> result = _analyze_names_in_function(my_func)
        >>> result['analyzer'].names.imported
        {'math'}
    """

    normalized_source = get_normalized_fn_source_code_str(
        a_func, skip_ordinarity_check=True)
    return _validate_and_parse_function_source(normalized_source)