"""
Verification middleware for automatic semantic checking.

Provides middleware functions for automatic verification of API responses
and statistical tracking of verification results.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from ..api.semantic_verification import SemanticVerifier, VerificationResult
from ..io.dto import ScheduleResponse

logger = logging.getLogger(__name__)


@dataclass
class VerificationStats:
    """Statistics tracking for verification middleware."""

    total_verifications: int = 0
    issues_detected: int = 0
    corrections_applied: int = 0
    verification_failures: int = 0

    # Issue type breakdown
    issue_types: Dict[str, int] = field(default_factory=dict)

    # Performance tracking
    total_verification_time_ms: float = 0.0
    max_verification_time_ms: float = 0.0

    # Recent activity
    last_verification_time: Optional[datetime] = None
    recent_issues: list = field(default_factory=list)


class VerificationMiddleware:
    """Middleware for automatic semantic verification."""

    def __init__(self, verifier: SemanticVerifier):
        self.verifier = verifier
        self.stats = VerificationStats()
        self.enabled = True

    def verify_and_track(
        self,
        response: ScheduleResponse,
        context: Dict[str, Any] = None
    ) -> ScheduleResponse:
        """
        Verify response and track statistics.

        Returns either the original response or a corrected version.
        """
        if not self.enabled:
            return response

        start_time = datetime.now()

        try:
            # Perform verification
            result = self.verifier.verify_schedule_response(response, context or {})

            # Update statistics
            self._update_stats(result, start_time)

            # Return corrected response if available
            if result.corrected_response and self.verifier.auto_correction:
                logger.info(f"Applied automatic corrections: {len(result.issues)} issues fixed")
                return result.corrected_response

            # Log issues if any
            if result.issues:
                self._log_issues(result.issues, context)

            return response

        except Exception as e:
            logger.error(f"Verification middleware failed: {e}")
            self.stats.verification_failures += 1
            return response  # Return original on verification failure

    def _update_stats(self, result: VerificationResult, start_time: datetime):
        """Update verification statistics."""

        # Basic counts
        self.stats.total_verifications += 1
        if result.issues:
            self.stats.issues_detected += len(result.issues)

        if result.corrected_response:
            self.stats.corrections_applied += 1

        # Issue type breakdown
        for issue in result.issues:
            issue_type = issue.issue_type
            self.stats.issue_types[issue_type] = self.stats.issue_types.get(issue_type, 0) + 1

        # Performance tracking
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        self.stats.total_verification_time_ms += duration_ms
        self.stats.max_verification_time_ms = max(
            self.stats.max_verification_time_ms,
            duration_ms
        )

        # Recent activity
        self.stats.last_verification_time = datetime.now()

        # Keep recent issues (last 100)
        if result.issues:
            self.stats.recent_issues.extend([
                {
                    "timestamp": datetime.now(),
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description
                }
                for issue in result.issues
            ])

            # Trim to last 100 issues
            self.stats.recent_issues = self.stats.recent_issues[-100:]

    def _log_issues(self, issues: list, context: Dict[str, Any]):
        """Log verification issues with appropriate severity."""

        high_severity_issues = [issue for issue in issues if issue.severity >= 0.7]
        medium_severity_issues = [issue for issue in issues if 0.3 <= issue.severity < 0.7]
        low_severity_issues = [issue for issue in issues if issue.severity < 0.3]

        user_id = context.get("user_id", "unknown")

        # Log high severity issues as warnings
        if high_severity_issues:
            logger.warning(
                f"High severity verification issues for user {user_id}: "
                f"{[issue.description for issue in high_severity_issues]}"
            )

        # Log medium severity as info
        if medium_severity_issues:
            logger.info(
                f"Medium severity verification issues for user {user_id}: "
                f"{len(medium_severity_issues)} issues detected"
            )

        # Log low severity as debug
        if low_severity_issues:
            logger.debug(
                f"Low severity verification issues for user {user_id}: "
                f"{len(low_severity_issues)} minor issues"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """Get verification statistics."""

        avg_verification_time = 0.0
        if self.stats.total_verifications > 0:
            avg_verification_time = (
                self.stats.total_verification_time_ms /
                self.stats.total_verifications
            )

        return {
            "enabled": self.enabled,
            "total_verifications": self.stats.total_verifications,
            "issues_detected": self.stats.issues_detected,
            "corrections_applied": self.stats.corrections_applied,
            "verification_failures": self.stats.verification_failures,
            "issue_rate": (
                self.stats.issues_detected / max(1, self.stats.total_verifications)
            ),
            "correction_rate": (
                self.stats.corrections_applied / max(1, self.stats.total_verifications)
            ),
            "performance": {
                "avg_verification_time_ms": round(avg_verification_time, 2),
                "max_verification_time_ms": round(self.stats.max_verification_time_ms, 2),
                "total_time_ms": round(self.stats.total_verification_time_ms, 2)
            },
            "issue_types": dict(self.stats.issue_types),
            "last_verification": (
                self.stats.last_verification_time.isoformat()
                if self.stats.last_verification_time else None
            ),
            "recent_issues_count": len(self.stats.recent_issues)
        }

    def reset_statistics(self):
        """Reset verification statistics."""
        self.stats = VerificationStats()
        logger.info("Verification statistics reset")

    def enable(self):
        """Enable verification middleware."""
        self.enabled = True
        logger.info("Verification middleware enabled")

    def disable(self):
        """Disable verification middleware."""
        self.enabled = False
        logger.info("Verification middleware disabled")

    def get_recent_issues(self, limit: int = 50) -> list:
        """Get recent verification issues."""
        return self.stats.recent_issues[-limit:]


# Global middleware instance
_verification_middleware = None


def get_verification_middleware() -> VerificationMiddleware:
    """Get global verification middleware instance."""
    global _verification_middleware
    if _verification_middleware is None:
        from ..api.semantic_verification import SemanticVerifier
        verifier = SemanticVerifier()
        _verification_middleware = VerificationMiddleware(verifier)
    return _verification_middleware


def setup_verification_middleware(verifier: SemanticVerifier) -> VerificationMiddleware:
    """Setup verification middleware with custom verifier."""
    global _verification_middleware
    _verification_middleware = VerificationMiddleware(verifier)
    return _verification_middleware