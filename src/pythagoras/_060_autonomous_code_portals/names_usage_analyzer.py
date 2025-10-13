import ast
from typing import Callable, Union

from .._020_ordinary_code_portals import get_normalized_function_source

class NamesUsedInFunction:
    """Container for name usage sets discovered in a function.

    Attributes:
        function: Name of the top-level function being analyzed.
        explicitly_global_unbound_deep: Names explicitly marked as global in the
            function or its nested functions, which are not locally bound.
        explicitly_nonlocal_unbound_deep: Names explicitly marked as nonlocal in
            the function or its nested functions, which are not locally bound.
        local: Names bound locally in the top-level function (including args).
        imported: Names explicitly imported within the function body.
        unclassified_deep: Names used in the function and/or nested functions
            that are neither imported nor explicitly marked global/nonlocal.
        accessible: All names currently considered accessible within function
            scope during analysis; a union built as nodes are visited.
    """
    def __init__(self):
        """Initialize all name sets to empty defaults."""
        self.function = None # name of the function
        self.explicitly_global_unbound_deep = set() # names, explicitly marked as global inside the function and/or called subfunctions, yet not bound to any object
        self.explicitly_nonlocal_unbound_deep = set() # names, explicitly marked as nonlocal inside the function and/or called subfunctions, yet not bound to any object
        self.local = set() # local variables in a function
        self.imported = set() # all names, which are explixitly imported inside the function
        self.unclassified_deep = set() # names, used inside the function and/or called subfunctions, while not explicitly imported, amd not explicitly marked as nonlocal / global
        self.accessible = set() # all names, currently accessable within the function

class NamesUsageAnalyzer(ast.NodeVisitor):
    """Collect data needed to analyze function autonomicity.

    This class is a visitor of an AST (Abstract Syntax Tree) that collects data
    needed to analyze function autonomy.
    """
    # TODO: add support for structural pattern matching
    def __init__(self):
        """Initialize the analyzer state and counters."""
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
            for arg in node.args.args:
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
            # self.names.imported is not changing
            # self.n_yelds is not changing

    def visit_Name(self, node):
        """Track variable usage and binding for a Name node.

        - On load: if the name is not accessible, mark it unclassified and
          accessible.
        - On store: register it as a local and accessible.

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

        Exception handler names become local and accessible.

        Args:
            node: The ast.Try node.
        """
        for handler in node.handlers:
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

        Args:
            node: The ast.ListComp node.
        """
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        """Handle bindings within a set comprehension.

        Args:
            node: The ast.SetComp node.
        """
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        """Handle bindings within a dict comprehension.

        Args:
            node: The ast.DictComp node.
        """
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        """Handle bindings within a generator expression.

        Args:
            node: The ast.GeneratorExp node.
        """
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

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

        Args:
            node: The ast.ImportFrom node.
        """
        self.imported_packages_deep |= {node.module.split('.')[-1]}
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

def analyze_names_in_function(
        a_func: Union[Callable,str]
        ):
    """Analyze names used in a single conventional function.

    The function source is normalized, decorators are skipped, and an AST is
    parsed. Assertions ensure that exactly one top-level regular function
    definition is present. The tree is visited with NamesUsageAnalyzer.

    Args:
        a_func: A function object or its source string to analyze.

    Returns:
        dict: A mapping with keys:
            - tree (ast.Module): The parsed AST module with a single function.
            - analyzer (NamesUsageAnalyzer): The populated analyzer instance.
            - normalized_source (str): The normalized source code.

    Raises:
        ValueError: If the input is not a single regular function (e.g., a
            lambda, async function, callable class, or multiple definitions).
    """

    normalized_source = get_normalized_function_source(a_func)

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
    result = dict(tree=tree, analyzer=analyzer
        , normalized_source=normalized_source)
    return result