"""
Semantic verification system for scheduler API responses.

Ensures API responses are semantically correct, user-friendly,
and consistent with frontend expectations.
"""

import logging
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import json

from ..io.dto import ScheduleResponse, ScheduleBlock
from ..core.domain import Task, Todo
from ...core.utils.timezone_utils import get_timezone_manager

logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """Levels of semantic verification."""
    BASIC = "basic"           # Basic structure and type checking
    STANDARD = "standard"     # Standard semantic checks
    STRICT = "strict"         # Strict validation with UX requirements
    PARANOID = "paranoid"     # Comprehensive validation for production


class VerificationSeverity(Enum):
    """Severity levels for verification issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class VerificationIssue:
    """Represents a semantic verification issue."""
    severity: VerificationSeverity
    category: str
    field: str
    message: str
    suggestion: Optional[str] = None

    # Context information
    actual_value: Any = None
    expected_value: Any = None
    user_impact: str = ""


@dataclass
class VerificationResult:
    """Result of semantic verification."""
    is_valid: bool
    issues: List[VerificationIssue] = field(default_factory=list)
    corrected_response: Optional[Dict[str, Any]] = None

    # Metrics
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def __post_init__(self):
        # Count issues by severity
        for issue in self.issues:
            if issue.severity == VerificationSeverity.ERROR or issue.severity == VerificationSeverity.CRITICAL:
                self.error_count += 1
            elif issue.severity == VerificationSeverity.WARNING:
                self.warning_count += 1
            elif issue.severity == VerificationSeverity.INFO:
                self.info_count += 1


class SemanticVerifier:
    """Semantic verification system for scheduler API responses."""

    def __init__(self, verification_level: VerificationLevel = VerificationLevel.STANDARD):
        self.verification_level = verification_level
        self.timezone_manager = get_timezone_manager()

        # Frontend expectations and patterns
        self.expected_patterns = {
            "task_id": r"^[a-zA-Z0-9\-_]{8,}$",
            "user_id": r"^[a-fA-F0-9\-]{36}$",  # UUID format
            "job_id": r"^[a-zA-Z0-9\-_]{8,}$",
            "iso_datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        }

        # UX requirements
        self.ux_requirements = {
            "max_explanation_length": 500,
            "min_explanation_length": 10,
            "max_block_title_length": 100,
            "required_metadata_fields": ["duration_minutes", "provider"],
            "valid_block_types": ["work", "break", "meeting", "personal"],
            "min_block_duration": 5,  # minutes
            "max_block_duration": 480,  # 8 hours
        }

    def verify_schedule_response(self, response: ScheduleResponse, context: Dict[str, Any] = None) -> VerificationResult:
        """Verify a schedule response for semantic correctness."""

        issues = []
        corrected_response = None
        context = context or {}

        try:
            # Convert response to dict for easier manipulation
            response_dict = self._response_to_dict(response)

            # Basic structure verification
            issues.extend(self._verify_response_structure(response_dict))

            # Schedule block verification
            if "blocks" in response_dict:
                issues.extend(self._verify_schedule_blocks(response_dict["blocks"]))

            # Metrics verification
            if "metrics" in response_dict:
                issues.extend(self._verify_metrics(response_dict["metrics"]))

            # Explanations verification
            if "explanations" in response_dict:
                issues.extend(self._verify_explanations(response_dict["explanations"]))

            # Frontend compatibility verification
            issues.extend(self._verify_frontend_compatibility(response_dict, context))

            # UX semantic verification
            if self.verification_level in [VerificationLevel.STRICT, VerificationLevel.PARANOID]:
                issues.extend(self._verify_ux_semantics(response_dict, context))

            # Attempt to correct issues if needed
            if issues and any(issue.severity in [VerificationSeverity.ERROR, VerificationSeverity.CRITICAL] for issue in issues):
                corrected_response = self._attempt_corrections(response_dict, issues)

            # Determine overall validity
            critical_errors = [i for i in issues if i.severity == VerificationSeverity.CRITICAL]
            errors = [i for i in issues if i.severity == VerificationSeverity.ERROR]

            is_valid = len(critical_errors) == 0 and (
                self.verification_level == VerificationLevel.BASIC or len(errors) == 0
            )

            return VerificationResult(
                is_valid=is_valid,
                issues=issues,
                corrected_response=corrected_response
            )

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            issues.append(VerificationIssue(
                severity=VerificationSeverity.CRITICAL,
                category="verification_error",
                field="response",
                message=f"Verification process failed: {str(e)}",
                user_impact="API response may be malformed"
            ))

            return VerificationResult(is_valid=False, issues=issues)

    def _response_to_dict(self, response: Union[ScheduleResponse, Dict[str, Any]]) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        if isinstance(response, dict):
            return response
        elif hasattr(response, 'dict'):
            return response.dict()
        elif hasattr(response, '__dict__'):
            return response.__dict__
        else:
            # Try JSON serialization
            try:
                import json
                return json.loads(json.dumps(response, default=str))
            except:
                raise ValueError(f"Cannot convert response to dict: {type(response)}")

    def _verify_response_structure(self, response: Dict[str, Any]) -> List[VerificationIssue]:
        """Verify basic response structure."""
        issues = []

        # Required fields
        required_fields = ["job_id", "feasible", "blocks", "metrics"]
        for field in required_fields:
            if field not in response:
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.ERROR,
                    category="structure",
                    field=field,
                    message=f"Missing required field: {field}",
                    user_impact="Frontend may not display results correctly"
                ))
            elif response[field] is None:
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.WARNING,
                    category="structure",
                    field=field,
                    message=f"Field {field} is null",
                    suggestion=f"Provide default value for {field}"
                ))

        # Type checking
        if "feasible" in response and not isinstance(response["feasible"], bool):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.ERROR,
                category="type",
                field="feasible",
                message="Field 'feasible' must be boolean",
                actual_value=response["feasible"],
                expected_value="true/false"
            ))

        if "blocks" in response and not isinstance(response["blocks"], list):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.ERROR,
                category="type",
                field="blocks",
                message="Field 'blocks' must be a list",
                actual_value=type(response["blocks"]).__name__,
                expected_value="list"
            ))

        # Job ID format validation
        if "job_id" in response and response["job_id"]:
            if not re.match(self.expected_patterns["job_id"], str(response["job_id"])):
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.WARNING,
                    category="format",
                    field="job_id",
                    message="Job ID format may not be compatible with frontend tracking",
                    actual_value=response["job_id"],
                    suggestion="Use alphanumeric IDs with hyphens/underscores"
                ))

        return issues

    def _verify_schedule_blocks(self, blocks: List[Dict[str, Any]]) -> List[VerificationIssue]:
        """Verify schedule blocks for semantic correctness."""
        issues = []

        if not isinstance(blocks, list):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.ERROR,
                category="type",
                field="blocks",
                message="Blocks must be a list",
                user_impact="Schedule will not render in frontend"
            ))
            return issues

        # Check each block
        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.ERROR,
                    category="type",
                    field=f"blocks[{i}]",
                    message="Each block must be an object",
                    user_impact="Block will not render correctly"
                ))
                continue

            # Required block fields
            required_block_fields = ["task_id", "start", "end", "duration_minutes"]
            for field in required_block_fields:
                if field not in block:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.ERROR,
                        category="structure",
                        field=f"blocks[{i}].{field}",
                        message=f"Missing required block field: {field}",
                        user_impact="Block may not display correctly in calendar"
                    ))

            # Validate datetime formats
            for time_field in ["start", "end"]:
                if time_field in block and block[time_field]:
                    time_value = block[time_field]
                    if isinstance(time_value, str):
                        if not re.match(self.expected_patterns["iso_datetime"], time_value):
                            issues.append(VerificationIssue(
                                severity=VerificationSeverity.ERROR,
                                category="format",
                                field=f"blocks[{i}].{time_field}",
                                message=f"Invalid datetime format: {time_value}",
                                suggestion="Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                                user_impact="Calendar display will be incorrect"
                            ))
                    elif not isinstance(time_value, datetime):
                        issues.append(VerificationIssue(
                            severity=VerificationSeverity.WARNING,
                            category="type",
                            field=f"blocks[{i}].{time_field}",
                            message=f"Time field should be datetime or ISO string, got {type(time_value).__name__}",
                            suggestion="Convert to ISO string for frontend"
                        ))

            # Validate duration
            if "duration_minutes" in block:
                duration = block["duration_minutes"]
                if not isinstance(duration, (int, float)) or duration <= 0:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.ERROR,
                        category="value",
                        field=f"blocks[{i}].duration_minutes",
                        message=f"Invalid duration: {duration}",
                        expected_value="positive number",
                        user_impact="Block duration will display incorrectly"
                    ))
                elif duration < self.ux_requirements["min_block_duration"]:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.WARNING,
                        category="ux",
                        field=f"blocks[{i}].duration_minutes",
                        message=f"Block duration {duration} is very short",
                        suggestion=f"Consider minimum {self.ux_requirements['min_block_duration']} minutes",
                        user_impact="May be hard to see/click in calendar"
                    ))
                elif duration > self.ux_requirements["max_block_duration"]:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.WARNING,
                        category="ux",
                        field=f"blocks[{i}].duration_minutes",
                        message=f"Block duration {duration} is very long",
                        suggestion="Consider breaking into smaller blocks",
                        user_impact="May overwhelm calendar view"
                    ))

            # Validate title/description length
            if "title" in block and block["title"]:
                title_len = len(str(block["title"]))
                if title_len > self.ux_requirements["max_block_title_length"]:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.WARNING,
                        category="ux",
                        field=f"blocks[{i}].title",
                        message=f"Title too long ({title_len} chars)",
                        suggestion=f"Keep under {self.ux_requirements['max_block_title_length']} characters",
                        user_impact="Title may be truncated in UI"
                    ))

            # Check for required metadata
            if "metadata" in block and isinstance(block["metadata"], dict):
                for req_field in self.ux_requirements["required_metadata_fields"]:
                    if req_field not in block["metadata"]:
                        issues.append(VerificationIssue(
                            severity=VerificationSeverity.INFO,
                            category="metadata",
                            field=f"blocks[{i}].metadata.{req_field}",
                            message=f"Missing recommended metadata field: {req_field}",
                            suggestion="Add for better UX"
                        ))

        # Check for overlapping blocks
        if len(blocks) > 1:
            overlaps = self._check_block_overlaps(blocks)
            for overlap in overlaps:
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.ERROR,
                    category="logic",
                    field="blocks",
                    message=f"Overlapping blocks detected: {overlap}",
                    user_impact="Calendar display will be confusing"
                ))

        return issues

    def _verify_metrics(self, metrics: Dict[str, Any]) -> List[VerificationIssue]:
        """Verify metrics for completeness and accuracy."""
        issues = []

        if not isinstance(metrics, dict):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.ERROR,
                category="type",
                field="metrics",
                message="Metrics must be an object",
                user_impact="Status information unavailable to user"
            ))
            return issues

        # Check for important metrics
        important_metrics = [
            "total_blocks", "total_scheduled_minutes",
            "feasible", "solve_time_ms"
        ]

        for metric in important_metrics:
            if metric not in metrics:
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.INFO,
                    category="completeness",
                    field=f"metrics.{metric}",
                    message=f"Missing useful metric: {metric}",
                    suggestion="Include for better user feedback"
                ))

        # Validate numeric metrics
        numeric_metrics = ["total_blocks", "total_scheduled_minutes", "solve_time_ms"]
        for metric in numeric_metrics:
            if metric in metrics:
                value = metrics[metric]
                if not isinstance(value, (int, float)) or value < 0:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.WARNING,
                        category="value",
                        field=f"metrics.{metric}",
                        message=f"Invalid metric value: {value}",
                        expected_value="non-negative number"
                    ))

        return issues

    def _verify_explanations(self, explanations: Dict[str, Any]) -> List[VerificationIssue]:
        """Verify explanations for user-friendliness."""
        issues = []

        if not isinstance(explanations, dict):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.WARNING,
                category="type",
                field="explanations",
                message="Explanations should be an object",
                user_impact="User feedback will be unavailable"
            ))
            return issues

        # Check explanation content
        for key, explanation in explanations.items():
            if isinstance(explanation, str):
                exp_len = len(explanation)

                # Check length
                if exp_len > self.ux_requirements["max_explanation_length"]:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.WARNING,
                        category="ux",
                        field=f"explanations.{key}",
                        message=f"Explanation too long ({exp_len} chars)",
                        suggestion=f"Keep under {self.ux_requirements['max_explanation_length']} characters",
                        user_impact="May overwhelm user with information"
                    ))
                elif exp_len < self.ux_requirements["min_explanation_length"]:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.INFO,
                        category="ux",
                        field=f"explanations.{key}",
                        message=f"Explanation very short ({exp_len} chars)",
                        suggestion="Provide more helpful detail"
                    ))

                # Check for technical jargon
                technical_terms = [
                    "solver", "constraint", "optimization", "objective",
                    "feasible", "infeasible", "algorithm"
                ]
                jargon_count = sum(1 for term in technical_terms if term.lower() in explanation.lower())
                if jargon_count > 2:
                    issues.append(VerificationIssue(
                        severity=VerificationSeverity.INFO,
                        category="ux",
                        field=f"explanations.{key}",
                        message="Explanation contains technical jargon",
                        suggestion="Use more user-friendly language",
                        user_impact="May confuse non-technical users"
                    ))

        return issues

    def _verify_frontend_compatibility(self, response: Dict[str, Any], context: Dict[str, Any]) -> List[VerificationIssue]:
        """Verify compatibility with frontend expectations."""
        issues = []

        # Check WebSocket event structure compatibility
        if "blocks" in response:
            for i, block in enumerate(response["blocks"]):
                if isinstance(block, dict):
                    # Check for frontend-expected fields
                    frontend_expected_fields = ["task_id", "start", "end", "title"]
                    for field in frontend_expected_fields:
                        if field not in block:
                            issues.append(VerificationIssue(
                                severity=VerificationSeverity.INFO,
                                category="frontend",
                                field=f"blocks[{i}].{field}",
                                message=f"Frontend expects field: {field}",
                                suggestion="Add for better frontend integration"
                            ))

                    # Check datetime string format for frontend
                    for time_field in ["start", "end"]:
                        if time_field in block and isinstance(block[time_field], str):
                            # Ensure timezone info is included
                            time_str = block[time_field]
                            if "T" in time_str and not any(tz in time_str for tz in ["Z", "+", "-"]):
                                issues.append(VerificationIssue(
                                    severity=VerificationSeverity.WARNING,
                                    category="frontend",
                                    field=f"blocks[{i}].{time_field}",
                                    message="Datetime missing timezone information",
                                    suggestion="Include timezone (Z or +/-HH:MM)",
                                    user_impact="May display in wrong timezone"
                                ))

        # Check cache invalidation compatibility
        if context.get("cache_keys"):
            expected_cache_keys = context["cache_keys"]
            # This would check if response structure matches what cache expects
            # Implementation depends on specific cache structure

        return issues

    def _verify_ux_semantics(self, response: Dict[str, Any], context: Dict[str, Any]) -> List[VerificationIssue]:
        """Verify UX-specific semantic requirements."""
        issues = []

        # Check for empty results with helpful messaging
        if response.get("feasible") is False:
            if "explanations" not in response or not response["explanations"]:
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.ERROR,
                    category="ux",
                    field="explanations",
                    message="No explanation provided for infeasible schedule",
                    suggestion="Always explain why scheduling failed",
                    user_impact="User won't understand why scheduling failed"
                ))

        # Check for successful results without blocks
        if response.get("feasible") is True and not response.get("blocks"):
            issues.append(VerificationIssue(
                severity=VerificationSeverity.WARNING,
                category="logic",
                field="blocks",
                message="Schedule marked feasible but no blocks provided",
                user_impact="User sees success but no actual schedule"
            ))

        # Check for reasonable scheduling outcomes
        if response.get("blocks"):
            blocks = response["blocks"]
            total_duration = sum(block.get("duration_minutes", 0) for block in blocks if isinstance(block, dict))

            # Warn if scheduled time is unreasonably high
            if total_duration > 16 * 60:  # More than 16 hours
                issues.append(VerificationIssue(
                    severity=VerificationSeverity.WARNING,
                    category="ux",
                    field="blocks",
                    message=f"Total scheduled time ({total_duration/60:.1f} hours) seems excessive",
                    suggestion="Consider breaking across multiple days",
                    user_impact="User may find schedule overwhelming"
                ))

            # Check for reasonable time gaps
            sorted_blocks = sorted(
                [b for b in blocks if isinstance(b, dict) and "start" in b],
                key=lambda x: x["start"]
            )

            for i in range(len(sorted_blocks) - 1):
                # This would check gaps between blocks
                # Implementation depends on datetime parsing
                pass

        return issues

    def _check_block_overlaps(self, blocks: List[Dict[str, Any]]) -> List[str]:
        """Check for overlapping schedule blocks."""
        overlaps = []

        # Parse and sort blocks by start time
        parsed_blocks = []
        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue

            start_str = block.get("start")
            end_str = block.get("end")

            if start_str and end_str:
                try:
                    # Simple string comparison for now
                    # In practice, would parse to datetime objects
                    parsed_blocks.append((i, start_str, end_str, block.get("task_id", f"block_{i}")))
                except:
                    continue

        # Check for overlaps (simplified)
        for i in range(len(parsed_blocks)):
            for j in range(i + 1, len(parsed_blocks)):
                block1 = parsed_blocks[i]
                block2 = parsed_blocks[j]

                # Simple string comparison (would use datetime in practice)
                if (block1[1] < block2[2] and block2[1] < block1[2]):
                    overlaps.append(f"Block {block1[3]} overlaps with {block2[3]}")

        return overlaps

    def _attempt_corrections(self, response: Dict[str, Any], issues: List[VerificationIssue]) -> Dict[str, Any]:
        """Attempt to automatically correct response issues."""
        corrected = response.copy()

        for issue in issues:
            if issue.severity in [VerificationSeverity.ERROR, VerificationSeverity.CRITICAL]:
                # Attempt basic corrections
                if issue.category == "structure" and "Missing required field" in issue.message:
                    field = issue.field
                    if field == "explanations" and field not in corrected:
                        corrected[field] = {"summary": "Schedule completed"}
                    elif field == "metrics" and field not in corrected:
                        corrected[field] = {"status": "completed"}

                # Fix datetime formats
                elif issue.category == "format" and "datetime format" in issue.message:
                    # Would implement datetime format correction
                    pass

                # Fix type issues
                elif issue.category == "type":
                    if "must be boolean" in issue.message and issue.field == "feasible":
                        corrected["feasible"] = bool(corrected.get("feasible", True))

        return corrected


# Factory function
def create_verifier(level: VerificationLevel = VerificationLevel.STANDARD) -> SemanticVerifier:
    """Create a semantic verifier with specified level."""
    return SemanticVerifier(verification_level=level)


