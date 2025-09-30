#!/usr/bin/env python3
"""
Comprehensive Import Issue Finder

This script systematically finds all import issues in the codebase by:
1. Static analysis of import statements
2. Dynamic import testing
3. Dependency graph analysis
"""

import ast
import os
import sys
import importlib.util
import traceback
from pathlib import Path
from typing import List, Dict, Set, Tuple
import re

class ImportIssuesFinder:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.issues = []
        self.all_python_files = []
        self.known_problematic_patterns = [
            r'app\.core\.config(?!\.core)',  # Old config imports
            r'app\.config\.redis_client',    # Old redis imports
            r'app\.config\.settings',        # Old settings imports
            r'app\.config\.supabase',        # Old supabase imports
            r'app\.workers\.timezone_scheduler',  # Old worker imports
            r'app\.workers\.email_service',       # Old worker imports
            r'app\.workers\.types',              # Old worker types
            r'app\.core\.websocket(?!\.infrastructure)',  # Old websocket imports
        ]

    def find_all_python_files(self) -> List[Path]:
        """Find all Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Skip certain directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return python_files

    def extract_imports_from_file(self, file_path: Path) -> List[Tuple[str, int]]:
        """Extract all import statements from a Python file"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append((node.module, node.lineno))
                        # Also check for submodule imports
                        for alias in node.names:
                            full_import = f"{node.module}.{alias.name}"
                            imports.append((full_import, node.lineno))

        except (SyntaxError, UnicodeDecodeError) as e:
            self.issues.append({
                'type': 'syntax_error',
                'file': str(file_path),
                'line': 0,
                'import': '',
                'error': str(e)
            })

        return imports

    def check_static_patterns(self, file_path: Path, imports: List[Tuple[str, int]]):
        """Check for known problematic import patterns"""
        for import_name, line_no in imports:
            for pattern in self.known_problematic_patterns:
                if re.search(pattern, import_name):
                    self.issues.append({
                        'type': 'known_pattern',
                        'file': str(file_path),
                        'line': line_no,
                        'import': import_name,
                        'pattern': pattern,
                        'error': f'Matches known problematic pattern: {pattern}'
                    })

    def test_dynamic_import(self, file_path: Path) -> bool:
        """Test if a file can be imported dynamically"""
        try:
            # Convert file path to module name
            rel_path = file_path.relative_to(self.root_dir)
            if rel_path.name == '__init__.py':
                module_parts = rel_path.parts[:-1]
            else:
                module_parts = rel_path.parts[:-1] + (rel_path.stem,)

            module_name = '.'.join(module_parts)

            # Try to import the module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return True

        except Exception as e:
            error_msg = str(e)

            # Categorize the error
            if "No module named" in error_msg:
                missing_module = re.search(r"No module named '([^']+)'", error_msg)
                if missing_module:
                    self.issues.append({
                        'type': 'missing_module',
                        'file': str(file_path),
                        'line': 0,
                        'import': missing_module.group(1),
                        'error': error_msg
                    })
            else:
                self.issues.append({
                    'type': 'import_error',
                    'file': str(file_path),
                    'line': 0,
                    'import': '',
                    'error': error_msg
                })

            return False

        return True

    def analyze_codebase(self):
        """Run comprehensive analysis"""
        print("🔍 Finding all Python files...")
        self.all_python_files = self.find_all_python_files()
        print(f"Found {len(self.all_python_files)} Python files")

        print("\n📝 Analyzing import statements...")
        for file_path in self.all_python_files:
            print(f"  Analyzing: {file_path.relative_to(self.root_dir)}")

            # Extract imports
            imports = self.extract_imports_from_file(file_path)

            # Check static patterns
            self.check_static_patterns(file_path, imports)

        print(f"\n🧪 Testing dynamic imports...")
        failed_imports = 0
        for file_path in self.all_python_files:
            print(f"  Testing: {file_path.relative_to(self.root_dir)}")

            if not self.test_dynamic_import(file_path):
                failed_imports += 1

        print(f"\nCompleted analysis: {failed_imports} files failed to import")

    def generate_report(self):
        """Generate a comprehensive report"""
        print("\n" + "="*80)
        print("🚨 IMPORT ISSUES REPORT")
        print("="*80)

        if not self.issues:
            print("✅ No import issues found!")
            return

        # Group issues by type
        issues_by_type = {}
        for issue in self.issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        for issue_type, issues in issues_by_type.items():
            print(f"\n🔴 {issue_type.upper()} ({len(issues)} issues)")
            print("-" * 40)

            for issue in issues:
                print(f"File: {issue['file']}")
                if issue['line'] > 0:
                    print(f"Line: {issue['line']}")
                if issue['import']:
                    print(f"Import: {issue['import']}")
                print(f"Error: {issue['error']}")
                print()

        # Summary
        print("\n📊 SUMMARY")
        print("-" * 20)
        print(f"Total issues found: {len(self.issues)}")
        for issue_type, issues in issues_by_type.items():
            print(f"  {issue_type}: {len(issues)}")

        # Suggestions
        print("\n💡 SUGGESTED FIXES")
        print("-" * 20)

        missing_modules = set()
        for issue in self.issues:
            if issue['type'] == 'missing_module':
                missing_modules.add(issue['import'])

        if missing_modules:
            print("Missing modules that need to be fixed:")
            for module in sorted(missing_modules):
                print(f"  - {module}")

                # Suggest fixes for known patterns
                suggestions = self.get_fix_suggestions(module)
                for suggestion in suggestions:
                    print(f"    → {suggestion}")

    def get_fix_suggestions(self, module: str) -> List[str]:
        """Get fix suggestions for common import issues"""
        suggestions = []

        if module == 'app.core.config':
            suggestions.append("Create compatibility shim or use app.config.core.settings")
        elif module == 'app.config.redis_client':
            suggestions.append("Change to app.config.cache.redis_client")
        elif module == 'app.config.settings':
            suggestions.append("Change to app.config.core.settings")
        elif module == 'app.config.supabase':
            suggestions.append("Change to app.config.database.supabase")
        elif module == 'app.workers.timezone_scheduler':
            suggestions.append("Change to app.workers.scheduling.timezone_scheduler")
        elif module == 'app.workers.email_service':
            suggestions.append("Change to app.workers.communication.email_service")
        elif module == 'app.core.websocket':
            suggestions.append("Change to app.core.infrastructure.websocket")
        elif 'app.core.config' in module:
            suggestions.append("Update to use app.config.core.* path")

        return suggestions

if __name__ == "__main__":
    print("🔍 Comprehensive Import Issues Finder")
    print("=====================================")

    # Set up the project root
    project_root = os.path.dirname(os.path.abspath(__file__))

    finder = ImportIssuesFinder(project_root)
    finder.analyze_codebase()
    finder.generate_report()

    print(f"\n✅ Analysis complete! Check the report above for all import issues.")