"""This module is only needed for development. No runtime usage."""
import ast
import pandas as pd
from pathlib import Path


def analyze_file(file_path):
    """Analyzes a single Python file and returns the number of lines, classes, and functions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (FileNotFoundError, IOError) as e:
        print(f"Error reading file {file_path}: {e}")
        return 0, 0, 0

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in file {file_path}: {e}")
        return 0, 0, 0

    def count_functions_and_classes(node):
        functions = 0
        classes = 0
        if isinstance(node, ast.FunctionDef):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        for child in ast.iter_child_nodes(node):
            f, c = count_functions_and_classes(child)
            functions += f
            classes += c
        return functions, classes

    total_functions = 0
    total_classes = 0
    for node in tree.body:
        f, c = count_functions_and_classes(node)
        total_functions += f
        total_classes += c

    lines = len(content.splitlines())

    return {"lines": lines, "classes": total_classes, "functions": total_functions}

def analyze_project(path_to_root):
    """
    Analyzes a Python project directory and returns a summary DataFrame.

    Args:
        path_to_root (str): Path to the root directory of the project.

    Returns:
        pd.DataFrame: DataFrame containing the summary statistics.
    """
    path_to_root = Path(path_to_root)
    if not path_to_root.is_dir():
        print(f"Provided path {path_to_root} is not a directory.")
        return pd.DataFrame()

    main_code = {'lines': 0, 'classes': 0, 'functions': 0, 'files': 0}
    unit_tests = {'lines': 0, 'classes': 0, 'functions': 0, 'files': 0}

    for file_path in path_to_root.rglob('*.py'):
        if '___OLD_' in str(file_path) :
            continue
        if 'python' in str(file_path) :
            continue
        if '/.' in str(file_path) :
            continue
        print(f"Analyzing file {file_path}")
        stats = analyze_file(file_path)
        rel_path = file_path.relative_to(path_to_root).parts

        if 'tests' in rel_path or file_path.name.startswith('test_'):
            unit_tests['lines'] += stats['lines']
            unit_tests['classes'] += stats['classes']
            unit_tests['functions'] += stats['functions']
            unit_tests['files'] += 1
        else:
            main_code['lines'] += stats['lines']
            main_code['classes'] += stats['classes']
            main_code['functions'] += stats['functions']
            main_code['files'] += 1

    total = {
        'lines': main_code['lines'] + unit_tests['lines'],
        'classes': main_code['classes'] + unit_tests['classes'],
        'functions': main_code['functions'] + unit_tests['functions'],
        'files': main_code['files'] + unit_tests['files']
    }

    data = {
        'Main code': [main_code['lines'], main_code['classes'], main_code['functions'], main_code['files']],
        'Unit Tests': [unit_tests['lines'], unit_tests['classes'], unit_tests['functions'], unit_tests['files']],
        'Total': [total['lines'], total['classes'], total['functions'], total['files']]
    }

    df = pd.DataFrame(data, index=['Lines Of Code', 'Classes', 'Functions / Methods', 'Files'])
    print("Analysis complete. Returning DataFrame.")
    return df



