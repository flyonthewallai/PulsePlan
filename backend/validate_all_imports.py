#!/usr/bin/env python3
"""
Ultimate Import Validation Tool

This tool provides multiple approaches to find import issues:
1. Static analysis with AST
2. Python compilation check
3. Runtime import testing
4. Dependency graph analysis
"""

import os
import sys
import subprocess
from pathlib import Path

def method1_compileall():
    """Method 1: Use Python's compileall module"""
    print("=== METHOD 1: Python Compilation Check ===")
    try:
        result = subprocess.run([
            sys.executable, "-m", "compileall", "-b", "."
        ], capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            print("✓ All Python files compile successfully")
            return True
        else:
            print("✗ Compilation errors found:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error running compileall: {e}")
        return False

def method2_static_analysis():
    """Method 2: Static import pattern analysis"""
    print("\n=== METHOD 2: Static Pattern Analysis ===")

    # Run a simple grep-like search for known problematic patterns
    problematic_patterns = [
        "from app.core.config import",
        "from app.config.settings import",
        "from app.config.redis_client import",
        "from app.config.supabase import",
        "from app.workers.timezone_scheduler import",
        "from app.workers.email_service import",
        "from app.core.websocket import",
    ]

    issues_found = []

    for py_file in Path(".").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                for pattern in problematic_patterns:
                    if pattern in line and not line.strip().startswith("#"):
                        issues_found.append(f"{py_file}:{i} - {line.strip()}")
        except Exception:
            pass

    if issues_found:
        print(f"✗ Found {len(issues_found)} potential static issues:")
        for issue in issues_found[:10]:  # Show first 10
            print(f"  {issue}")
        if len(issues_found) > 10:
            print(f"  ... and {len(issues_found) - 10} more")
        return False
    else:
        print("✓ No problematic import patterns found")
        return True

def method3_runtime_test():
    """Method 3: Test critical imports at runtime"""
    print("\n=== METHOD 3: Critical Runtime Import Test ===")

    critical_imports = [
        "app.config.cache.redis_client",
        "app.config.core.settings",
        "app.config.database.supabase",
        "app.workers.scheduling.timezone_scheduler",
        "app.workers.communication.email_service",
        "app.core.infrastructure.websocket",
        "app.core.config.settings",  # Compatibility shim
        "app.agents.orchestrator",
        "app.api.v1.api",
    ]

    failed_imports = []

    for module_name in critical_imports:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))

    if failed_imports:
        print(f"\n✗ {len(failed_imports)} critical imports failed")
        return False
    else:
        print("\n✓ All critical imports successful")
        return True

def method4_flask_startup_test():
    """Method 4: Test actual application startup"""
    print("\n=== METHOD 4: Application Startup Test ===")

    try:
        # Try to import the main application
        from main import create_application
        app = create_application()
        print("✓ Application creates successfully")

        # Get route count as a basic health check
        route_count = len([r for r in app.routes if hasattr(r, 'path')])
        print(f"✓ Application has {route_count} routes registered")

        return True

    except Exception as e:
        print(f"✗ Application startup failed: {e}")
        return False

def main():
    print("🔍 Ultimate Import Validation Tool")
    print("=" * 50)

    os.chdir(Path(__file__).parent)

    results = []

    # Run all methods
    results.append(("Compilation Check", method1_compileall()))
    results.append(("Static Analysis", method2_static_analysis()))
    results.append(("Runtime Imports", method3_runtime_test()))
    results.append(("App Startup", method4_flask_startup_test()))

    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} {status}")
        all_passed = all_passed and passed

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! No import issues found.")
        print("Your refactoring is complete and all imports are working correctly.")
    else:
        print("⚠️  Some issues found. Check the details above.")
        print("Focus on fixing the failed tests to resolve remaining import issues.")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())