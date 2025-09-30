"""
Simple verification test for the semantic verification system.

Basic tests to verify the system is working correctly.
"""

from datetime import datetime
from ..api.semantic_verification import SemanticVerifier, VerificationLevel
from ..api.verification_middleware import VerificationMiddleware
from ..io.dto import ScheduleResponse, ScheduleBlock


def test_basic_verification():
    """Test basic semantic verification functionality."""

    # Create a simple, valid response
    block = ScheduleBlock(
        task_id="test_1",
        title="Test Task",
        start="2024-01-01T09:00:00Z",
        end="2024-01-01T10:00:00Z"
    )

    response = ScheduleResponse(
        feasible=True,
        blocks=[block],
        metrics={"test": "value"},
        explanations={"summary": "Test response"}
    )

    # Create verifier
    verifier = SemanticVerifier(verification_level=VerificationLevel.BASIC)

    # Verify response
    result = verifier.verify_schedule_response(response)

    print(f"Verification result: valid={result.is_valid}")
    print(f"Issues: {len(result.issues)} (errors: {result.error_count}, warnings: {result.warning_count})")

    if result.issues:
        for issue in result.issues:
            print(f"  - {issue.message} (severity: {issue.severity})")

    return result.is_valid, len(result.issues)


def test_middleware_functionality():
    """Test middleware functionality."""

    verifier = SemanticVerifier(verification_level=VerificationLevel.BASIC)
    middleware = VerificationMiddleware(verifier)

    # Create response
    block = ScheduleBlock(
        task_id="test_1",
        title="Test Task",
        start="2024-01-01T09:00:00Z",
        end="2024-01-01T10:00:00Z"
    )

    response = ScheduleResponse(
        feasible=True,
        blocks=[block],
        metrics={"test": "value"},
        explanations={"summary": "Test response"}
    )

    # Process with middleware
    processed = middleware.verify_and_track(response)

    # Get stats
    stats = middleware.get_statistics()

    print(f"Middleware stats: verifications={stats['total_verifications']}, issues={stats['issues_detected']}")

    return stats['total_verifications'] > 0


if __name__ == "__main__":
    print("Testing semantic verification system...")

    # Test basic verification
    print("\n1. Testing basic verification:")
    is_valid, issue_count = test_basic_verification()
    print(f"Result: valid={is_valid}, issues={issue_count}")

    # Test middleware
    print("\n2. Testing middleware:")
    middleware_works = test_middleware_functionality()
    print(f"Middleware working: {middleware_works}")

    print("\nBasic semantic verification tests completed!")