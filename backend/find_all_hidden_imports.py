#!/usr/bin/env python3
"""
Find ALL Hidden Import Issues

This tool specifically finds relative imports that are incorrect due to refactoring.
It catches issues like:
- from .module_name import ... (when module_name is in a different directory)
- from ..wrong_path import ...
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Set

def find_all_relative_imports():
    """Find all relative imports in the codebase"""
    issues = []

    print("Scanning for problematic relative imports...")

    for py_file in Path('.').rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # Check for relative imports
                    if node.module.startswith('.'):
                        # This is a relative import - validate it
                        if not validate_relative_import(node.module, py_file):
                            issues.append({
                                'file': str(py_file),
                                'line': node.lineno,
                                'import': node.module,
                                'names': [alias.name for alias in node.names]
                            })

        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    return issues

def validate_relative_import(import_path: str, file_path: Path) -> bool:
    """Check if a relative import is valid"""
    try:
        # Get the current file's directory structure
        rel_path = file_path.relative_to(Path('.'))
        if rel_path.name == '__init__.py':
            current_dir_parts = rel_path.parts[:-1]
        else:
            current_dir_parts = rel_path.parts[:-1]

        # Parse the relative import
        if import_path == '.':
            # Same directory import
            target_parts = current_dir_parts
        elif import_path.startswith('..'):
            # Parent directory imports
            dots = 0
            remaining = import_path
            while remaining.startswith('.'):
                dots += 1
                remaining = remaining[1:]

            # Go up 'dots-1' levels from current directory
            if dots - 1 > len(current_dir_parts):
                return False

            parent_parts = current_dir_parts[:-dots+1] if dots > 1 else current_dir_parts[:-1] if dots == 2 else current_dir_parts

            if remaining:
                target_parts = parent_parts + tuple(remaining.split('.'))
            else:
                target_parts = parent_parts
        else:
            # Single dot import like ".module_name"
            module_name = import_path[1:]
            target_parts = current_dir_parts + (module_name,)

        # Check if the target exists
        target_path = Path(*target_parts) if target_parts else Path('.')

        # Check for __init__.py (package) or .py file
        if (target_path / '__init__.py').exists():
            return True
        elif (target_path.parent / f"{target_path.name}.py").exists():
            return True
        else:
            return False

    except Exception:
        return False

def suggest_fix(import_path: str, file_path: Path) -> str:
    """Suggest the correct import path"""
    # Common patterns we've seen
    fixes = {
        '.conversation_state_manager': '..conversation.conversation_state_manager',
        '.llm_service': '..services.llm_service',
        '.websocket': '..infrastructure.websocket',
        '.config': '..config.core.settings',
    }

    if import_path in fixes:
        return fixes[import_path]

    # Try to guess based on known module locations
    if import_path.startswith('.'):
        module_name = import_path[1:]

        # Look for the module in the codebase
        for py_file in Path('.').rglob(f'{module_name}.py'):
            rel_path = py_file.relative_to(Path('.'))
            suggested_path = '.'.join([''] + ['.' for _ in range(len(file_path.parts) - len(rel_path.parts) + 1)] + list(rel_path.parts[:-1]) + [rel_path.stem])
            return suggested_path

    return "Unknown - check module location manually"

def main():
    print("🔍 Finding ALL Hidden Import Issues")
    print("="*50)

    issues = find_all_relative_imports()

    if not issues:
        print("✅ No problematic relative imports found!")
        return

    print(f"❌ Found {len(issues)} problematic relative imports:")
    print("="*50)

    for issue in issues:
        print(f"📁 File: {issue['file']}")
        print(f"📍 Line: {issue['line']}")
        print(f"📦 Import: {issue['import']}")
        print(f"🎯 Names: {', '.join(issue['names'])}")

        # Suggest fix
        fix = suggest_fix(issue['import'], Path(issue['file']))
        print(f"💡 Suggested fix: {fix}")
        print("-" * 40)

    # Show summary
    print(f"\\n📊 Summary: {len(issues)} imports need fixing")

    # Group by import pattern
    patterns = {}
    for issue in issues:
        pattern = issue['import']
        if pattern not in patterns:
            patterns[pattern] = []
        patterns[pattern].append(issue['file'])

    print("\\n🔄 Import patterns found:")
    for pattern, files in patterns.items():
        print(f"  {pattern}: {len(files)} files")

if __name__ == "__main__":
    main()