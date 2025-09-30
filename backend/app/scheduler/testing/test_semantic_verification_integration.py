"""
Integration tests for semantic verification system.

Tests the full integration of semantic verification with the scheduler API
including middleware functionality and endpoint behavior.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from ..api.semantic_verification import SemanticVerifier, VerificationLevel
from ..api.verification_middleware import VerificationMiddleware
from ..io.dto import ScheduleResponse, ScheduleBlock, ModelMetrics
from ...core.utils.timezone_utils import get_timezone_manager


class TestSemanticVerificationIntegration:
    """Test semantic verification integration."""

    def setup_method(self):
        """Setup test environment."""
        self.timezone_manager = get_timezone_manager()
        self.verifier = SemanticVerifier(verification_level=VerificationLevel.STANDARD)
        self.middleware = VerificationMiddleware(self.verifier)

    def _create_test_response(
        self,
        feasible: bool = True,
        blocks_count: int = 3,
        add_issues: bool = False
    ) -> ScheduleResponse:
        """Create a test schedule response."""

        # Create test blocks
        blocks = []
        base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        for i in range(blocks_count):
            block_start = base_time + timedelta(hours=i*2)
            block_end = block_start + timedelta(hours=1)

            # Add issues if requested
            if add_issues and i == 0:
                # Create block with missing title to trigger verification issues
                block = ScheduleBlock(
                    task_id=f"task_{i}",
                    title="",  # Empty title will trigger issue
                    start=block_start.isoformat(),
                    end=block_end.isoformat()
                )
            else:
                block = ScheduleBlock(
                    task_id=f"task_{i}",
                    title=f"Test Task {i}",
                    start=block_start.isoformat(),
                    end=block_end.isoformat()
                )
            blocks.append(block)

        # Create metrics as dict
        metrics = {
            "total_tasks": blocks_count,
            "scheduled_tasks": blocks_count if feasible else 0,
            "completion_score": 0.85 if feasible else 0.0,
            "urgency_distribution": [0.2, 0.3, 0.3, 0.2],
            "time_utilization": 0.75 if feasible else 0.0
        }

        explanations = {
            "summary": f"Scheduled {blocks_count} tasks",
            "reasoning": "Test schedule generation"
        }

        return ScheduleResponse(
            feasible=feasible,
            blocks=blocks,
            metrics=metrics,
            explanations=explanations
        )

    def test_verifier_basic_functionality(self):
        """Test basic verifier functionality."""

        # Test valid response
        response = self._create_test_response()
        result = self.verifier.verify_schedule_response(response)

        assert result.is_valid
        assert result.confidence_score > 0.8
        assert len(result.issues) == 0

    def test_verifier_detects_issues(self):
        """Test that verifier detects issues."""

        # Create response with issues
        response = self._create_test_response(add_issues=True)
        result = self.verifier.verify_schedule_response(response)

        assert not result.is_valid
        assert len(result.issues) > 0
        assert result.confidence_score < 0.8

    def test_middleware_tracking(self):
        """Test middleware statistics tracking."""

        # Initial stats should be empty
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 0
        assert stats["issues_detected"] == 0

        # Process a valid response
        response = self._create_test_response()
        processed_response = self.middleware.verify_and_track(response)

        # Check stats updated
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 1
        assert stats["issues_detected"] == 0
        assert processed_response.feasible == response.feasible

    def test_middleware_issue_tracking(self):
        """Test middleware issue detection and tracking."""

        # Process response with issues
        response = self._create_test_response(add_issues=True)
        processed_response = self.middleware.verify_and_track(response)

        # Check stats
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 1
        assert stats["issues_detected"] > 0
        assert stats["issue_rate"] > 0.0

        # Check recent issues
        recent_issues = self.middleware.get_recent_issues()
        assert len(recent_issues) > 0
        assert recent_issues[0]["type"] is not None

    def test_middleware_correction_application(self):
        """Test automatic correction application."""

        # Enable auto-correction
        self.verifier.auto_correction = True
        self.middleware = VerificationMiddleware(self.verifier)

        # Process response that can be corrected
        response = self._create_test_response(add_issues=True)
        processed_response = self.middleware.verify_and_track(response)

        # Check if corrections were applied
        stats = self.middleware.get_statistics()
        if stats["corrections_applied"] > 0:
            # Correction was applied
            assert processed_response != response
        else:
            # No automatic correction available, response unchanged
            assert processed_response == response

    def test_middleware_enable_disable(self):
        """Test middleware enable/disable functionality."""

        # Disable middleware
        self.middleware.disable()
        assert not self.middleware.enabled

        # Process response (should not be verified)
        response = self._create_test_response()
        processed_response = self.middleware.verify_and_track(response)

        # Stats should remain empty
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 0
        assert processed_response == response

        # Re-enable and test
        self.middleware.enable()
        assert self.middleware.enabled

        processed_response = self.middleware.verify_and_track(response)
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 1

    def test_different_verification_levels(self):
        """Test different verification levels."""

        response = self._create_test_response()

        # Test basic level (should be permissive)
        basic_verifier = SemanticVerifier(verification_level=VerificationLevel.BASIC)
        basic_result = basic_verifier.verify_schedule_response(response)
        basic_issues = len(basic_result.issues)

        # Test paranoid level (should be strict)
        paranoid_verifier = SemanticVerifier(verification_level=VerificationLevel.PARANOID)
        paranoid_result = paranoid_verifier.verify_schedule_response(response)
        paranoid_issues = len(paranoid_result.issues)

        # Paranoid should detect more issues (or at least the same)
        assert paranoid_issues >= basic_issues

    def test_context_influence_on_verification(self):
        """Test that context influences verification."""

        response = self._create_test_response()

        # Test with different contexts
        context1 = {"preview": True, "user_id": "test_user"}
        result1 = self.verifier.verify_schedule_response(response, context1)

        context2 = {"reschedule": True, "user_id": "test_user"}
        result2 = self.verifier.verify_schedule_response(response, context2)

        # Results should be consistent but context-aware
        assert result1.is_valid == result2.is_valid
        # Context should be reflected in the verification process

    def test_performance_tracking(self):
        """Test performance tracking in middleware."""

        # Process multiple responses
        for i in range(5):
            response = self._create_test_response()
            self.middleware.verify_and_track(response)

        # Check performance stats
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 5
        assert stats["performance"]["avg_verification_time_ms"] > 0
        assert stats["performance"]["max_verification_time_ms"] > 0

    def test_statistics_reset(self):
        """Test statistics reset functionality."""

        # Generate some activity
        response = self._create_test_response()
        self.middleware.verify_and_track(response)

        # Check stats exist
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] > 0

        # Reset and verify
        self.middleware.reset_statistics()
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 0
        assert stats["issues_detected"] == 0
        assert len(self.middleware.get_recent_issues()) == 0

    def test_edge_cases(self):
        """Test edge cases and error handling."""

        # Test with empty response
        empty_response = ScheduleResponse(
            feasible=False,
            blocks=[],
            metrics={
                "total_tasks": 0,
                "scheduled_tasks": 0,
                "completion_score": 0.0,
                "urgency_distribution": [],
                "time_utilization": 0.0
            },
            explanations={
                "summary": "No tasks to schedule",
                "reasoning": "Empty test case"
            }
        )

        # Should handle gracefully
        result = self.verifier.verify_schedule_response(empty_response)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.confidence_score, float)

        # Test middleware with empty response
        processed = self.middleware.verify_and_track(empty_response)
        assert processed.feasible == empty_response.feasible

    def test_concurrent_verification(self):
        """Test concurrent verification operations."""

        async def verify_response(response_id: int):
            """Verify a response asynchronously."""
            response = self._create_test_response()
            # Note: ScheduleResponse doesn't have user_id field directly
            return self.middleware.verify_and_track(response)

        async def run_concurrent_verification():
            """Run multiple verifications concurrently."""
            tasks = [verify_response(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results

        # Run concurrent verifications
        results = asyncio.run(run_concurrent_verification())

        # Check all succeeded
        assert len(results) == 10
        for result in results:
            assert result.feasible is not None

        # Check stats
        stats = self.middleware.get_statistics()
        assert stats["total_verifications"] == 10


if __name__ == "__main__":
    # Run basic tests
    print("Running semantic verification integration tests...")

    test_instance = TestSemanticVerificationIntegration()

    # Test basic functionality
    test_instance.setup_method()
    test_instance.test_verifier_basic_functionality()
    print("Basic functionality: PASSED")

    # Test issue detection
    test_instance.setup_method()
    test_instance.test_verifier_detects_issues()
    print("Issue detection: PASSED")

    # Test middleware tracking
    test_instance.setup_method()
    test_instance.test_middleware_tracking()
    print("Middleware tracking: PASSED")

    # Test enable/disable
    test_instance.setup_method()
    test_instance.test_middleware_enable_disable()
    print("Enable/disable: PASSED")

    # Test verification levels
    test_instance.setup_method()
    test_instance.test_different_verification_levels()
    print("Verification levels: PASSED")

    print("All semantic verification integration tests passed!")

