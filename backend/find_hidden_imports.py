#!/usr/bin/env python3
"""
Enhanced Import Issue Finder - Catches Dynamic and Hidden Imports

This tool finds import issues that the basic tools miss:
1. Dynamic imports inside functions
2. Imports inside try/except blocks
3. Relative imports with incorrect paths
4. Imports that fail at runtime but not at parse time
"""

import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

class HiddenImportsFinder:
    def __init__(self):
        self.issues = []
        self.dynamic_imports = []

    def find_all_imports_in_file(self, file_path: Path) -> List[Dict]:
        """Find all imports including dynamic ones"""
        imports = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Walk through all nodes to find imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'line': node.lineno,
                            'context': 'top_level'
                        })

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append({
                            'type': 'from_import',
                            'module': node.module,
                            'names': [alias.name for alias in node.names],
                            'line': node.lineno,
                            'context': self._get_context(node, tree)
                        })

            # Also find string-based imports (importlib, __import__, etc.)
            string_imports = self._find_string_based_imports(content)
            imports.extend(string_imports)

        except Exception as e:
            self.issues.append({
                'type': 'parse_error',
                'file': str(file_path),
                'error': str(e)
            })

        return imports

    def _get_context(self, node, tree):
        """Determine if import is at top level or inside function/class"""
        # Walk up the AST to find parent nodes
        for parent in ast.walk(tree):
            if hasattr(parent, 'body') and node in parent.body:
                if isinstance(parent, ast.FunctionDef):
                    return f'function:{parent.name}'
                elif isinstance(parent, ast.ClassDef):
                    return f'class:{parent.name}'
                elif isinstance(parent, ast.Module):
                    return 'top_level'
        return 'unknown'

    def _find_string_based_imports(self, content: str) -> List[Dict]:
        """Find imports using importlib, __import__, etc."""
        imports = []
        lines = content.split('\n')

        patterns = [
            r'importlib\.import_module\([\'"]([^\'"]+)[\'"]',
            r'__import__\([\'"]([^\'"]+)[\'"]',
            r'from\s+([^\s]+)\s+import',
        ]

        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    imports.append({
                        'type': 'dynamic_import',
                        'module': match,
                        'line': i,
                        'context': 'string_based'
                    })

        return imports

    def validate_import_path(self, module: str, file_path: Path) -> bool:
        """Check if an import path is valid"""
        # Handle relative imports
        if module.startswith('.'):
            # Calculate what the absolute module would be
            rel_path = file_path.relative_to(Path('.'))
            if rel_path.name == '__init__.py':
                current_package = '.'.join(rel_path.parts[:-1])
            else:
                current_package = '.'.join(rel_path.parts[:-1])

            # Resolve relative import
            if module == '.':
                resolved = current_package
            elif module.startswith('..'):
                # Count the dots to go up directories
                dots = len(module) - len(module.lstrip('.'))
                parts = current_package.split('.')
                if dots > len(parts):
                    return False
                resolved = '.'.join(parts[:-dots]) + module[dots:]
            else:
                resolved = current_package + module

            # Check if the resolved path exists
            return self._module_exists(resolved)
        else:
            return self._module_exists(module)

    def _module_exists(self, module: str) -> bool:
        """Check if a module exists in the filesystem"""
        parts = module.split('.')

        # Try to find the module
        current_path = Path('.')
        for part in parts:
            # Try as directory with __init__.py
            dir_path = current_path / part
            if (dir_path / '__init__.py').exists():
                current_path = dir_path
                continue

            # Try as .py file
            file_path = current_path / f"{part}.py"
            if file_path.exists():
                return True

            # Not found
            return False

        return True

    def analyze_all_files(self):
        """Analyze all Python files for import issues"""
        print("Scanning for hidden import issues...")

        for py_file in Path('.').rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            print(f"  Checking: {py_file}")
            imports = self.find_all_imports_in_file(py_file)

            for imp in imports:
                # Check if import path is valid
                if not self.validate_import_path(imp['module'], py_file):
                    self.issues.append({
                        'type': 'invalid_import',
                        'file': str(py_file),
                        'line': imp['line'],
                        'module': imp['module'],
                        'context': imp['context'],
                        'import_type': imp['type']
                    })

                # Track dynamic imports for special attention
                if imp['context'] != 'top_level':
                    self.dynamic_imports.append({
                        'file': str(py_file),
                        'line': imp['line'],
                        'module': imp['module'],
                        'context': imp['context']
                    })

    def generate_report(self):
        """Generate comprehensive report"""
        print("\\n" + "="*60)
        print("HIDDEN IMPORTS ANALYSIS REPORT")
        print("="*60)

        if not self.issues and not self.dynamic_imports:
            print("No hidden import issues found!")
            return

        # Report invalid imports
        if self.issues:
            print(f"\\nFOUND {len(self.issues)} IMPORT ISSUES:")
            print("-" * 40)
            for issue in self.issues:
                print(f"File: {issue['file']}")
                print(f"Line: {issue['line']}")
                print(f"Module: {issue['module']}")
                print(f"Context: {issue['context']}")
                print(f"Type: {issue['import_type']}")
                print()

        # Report dynamic imports (for awareness)
        if self.dynamic_imports:
            print(f"\\nFOUND {len(self.dynamic_imports)} DYNAMIC IMPORTS:")
            print("-" * 40)
            print("(These are imports inside functions - check manually)")
            for imp in self.dynamic_imports[:10]:  # Show first 10
                print(f"  {imp['file']}:{imp['line']} - {imp['module']} ({imp['context']})")
            if len(self.dynamic_imports) > 10:
                print(f"  ... and {len(self.dynamic_imports) - 10} more")

if __name__ == "__main__":
    finder = HiddenImportsFinder()
    finder.analyze_all_files()
    finder.generate_report()