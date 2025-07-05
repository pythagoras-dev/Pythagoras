import ast
from typing import Callable, Union

from .._020_ordinary_code_portals import get_normalized_function_source

class NamesUsedInFunction:
    def __init__(self):
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
        self.names = NamesUsedInFunction()
        self.imported_packages_deep = set()
        self.func_nesting_level = 0
        self.n_yelds = 0

    def visit_FunctionDef(self, node):
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
        self.generic_visit(node)

    def visit_Yield(self, node):
        self.n_yelds += 1
        self.generic_visit(node)

    def visit_YieldFrom(self, node):
        self.n_yelds += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        for handler in node.handlers:
            self.names.local |= {handler.name}
            self.names.accessible |= {handler.name}
        self.generic_visit(node)

    def visit_comprehension(self, node):
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
        self.visit_comprehension(node)

    def visit_ListComp(self, node):
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        for gen in node.generators:
            self.visit_comprehension(gen)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.names.imported |= {name}
            self.imported_packages_deep |= {alias.name.split('.')[0]}
        self.names.accessible |= self.names.imported
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imported_packages_deep |= {node.module.split('.')[-1]}
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.names.imported |= {name}
        self.names.accessible |= self.names.imported
        self.generic_visit(node)

    def visit_Nonlocal(self, node):
        nonlocals =  set(node.names)
        self.names.explicitly_nonlocal_unbound_deep |= nonlocals
        self.names.accessible |= nonlocals
        self.generic_visit(node)

    def visit_Global(self, node):
        globals = set(node.names)
        self.names.explicitly_global_unbound_deep |= globals
        self.names.accessible |= globals
        self.generic_visit(node)

def analyze_names_in_function(
        a_func: Union[Callable,str]
        ):
    """Analyze names used in a function.

    It returns an instance of NamesUsageAnalyzer class,
    which contains all the data needed to analyze
    names, used by the function.
    """

    normalized_source = get_normalized_function_source(a_func)

    lines, line_num = normalized_source.splitlines(), 0
    while lines[line_num].startswith("@"):
        line_num+=1

    assert lines[line_num].startswith("def "),("This action can only"
            + " be applied to conventional functions,"
            + " not to instances of callable classes, "
            + " not to lambda functions, "
            + " not to async functions.")
    tree = ast.parse(normalized_source)
    assert isinstance(tree, ast.Module), (f"Only one high lever"
            + f" function definition is allowed to be processed."
            + f" The following code is not allowed: {normalized_source}")
    assert isinstance(tree.body[0], ast.FunctionDef), (f"Only one high lever"
            + f" function definition is allowed to be processed."
            + f" The following code is not allowed: {normalized_source}")
    assert len(tree.body)==1, (f"Only one high lever"
            + f" function definition is allowed to be processed."
            + f" The following code is not allowed: {normalized_source}")
    analyzer = NamesUsageAnalyzer()
    analyzer.visit(tree)
    result = dict(tree=tree, analyzer=analyzer
        , normalized_source=normalized_source)
    return result