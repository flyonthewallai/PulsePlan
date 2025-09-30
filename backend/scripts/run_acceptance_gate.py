#!/usr/bin/env python3
"""
CI Acceptance Gate Runner Script.

Simple script for running the scheduler acceptance gate in CI/CD pipelines.
Can be called from GitHub Actions, Jenkins, or other CI systems.
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.scheduler.testing.ci_acceptance_gate import run_ci_acceptance_gate


async def main():
    """Run acceptance gate and output results."""

    print("=" * 60)
    print("🚀 PulsePlan Scheduler Acceptance Gate")
    print("=" * 60)

    try:
        # Run the acceptance gate
        passed, report = await run_ci_acceptance_gate()

        # Print report
        print(report)

        # Save results for CI artifacts
        result_data = {
            "passed": passed,
            "timestamp": str(datetime.now()),
            "report": report
        }

        # Save to CI artifacts directory if available
        artifacts_dir = os.environ.get("CI_ARTIFACTS_DIR", ".")
        results_file = Path(artifacts_dir) / "acceptance_gate_results.json"

        with open(results_file, "w") as f:
            json.dump(result_data, f, indent=2)

        print(f"\n📄 Results saved to: {results_file}")

        # Exit with appropriate code
        if passed:
            print("\n🎉 ACCEPTANCE GATE PASSED ✅")
            print("✅ Ready for deployment!")
            sys.exit(0)
        else:
            print("\n❌ ACCEPTANCE GATE FAILED ❌")
            print("🚫 Deployment blocked!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Acceptance gate execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Import datetime here since it's only needed in main
    from datetime import datetime

    asyncio.run(main())