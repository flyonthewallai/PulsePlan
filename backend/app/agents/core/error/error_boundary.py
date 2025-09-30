"""
Error Boundary System for Workflow Isolation
Provides comprehensive error handling, recovery, and circuit breaking for workflows
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, Type
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import traceback

from ...graphs.base import WorkflowError, WorkflowState

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    ESCALATE = "escalate"
    FAIL_FAST = "fail_fast"


@dataclass
class ErrorBoundaryConfig:
    """Configuration for error boundary behavior"""
    max_retry_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    error_tracking_window: float = 300.0  # 5 minutes
    enable_fallback: bool = True
    escalation_threshold: int = 10


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    timestamp: datetime
    error_type: str
    severity: ErrorSeverity
    workflow_id: str
    workflow_type: str
    user_id: str
    error_message: str
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False


class CircuitBreaker:
    """Circuit breaker for workflow error protection"""
    
    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def can_execute(self) -> bool:
        """Check if execution should be allowed"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time and (
                datetime.utcnow() - self.last_failure_time
            ).total_seconds() >= self.timeout:
                self.state = "half_open"
                return True
            return False
        
        # half_open state
        return True
    
    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = "closed"
        logger.info("Circuit breaker reset after successful execution")
    
    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures",
                extra={
                    "threshold": self.threshold,
                    "timeout": self.timeout
                }
            )
        elif self.state == "half_open":
            # Failed while half-open, go back to open
            self.state = "open"


class WorkflowErrorBoundary:
    """
    Error boundary for workflow execution with:
    - Error classification and severity assessment
    - Retry logic with exponential backoff
    - Circuit breaker protection
    - Fallback mechanism execution
    - Error tracking and metrics
    """
    
    def __init__(self, config: Optional[ErrorBoundaryConfig] = None):
        self.config = config or ErrorBoundaryConfig()
        self.error_history: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
    
    async def execute_with_boundary(
        self,
        workflow_func: Callable,
        state: WorkflowState,
        workflow_type: str,
        fallback_handler: Optional[Callable] = None
    ) -> WorkflowState:
        """
        Execute workflow function with comprehensive error boundary protection
        """
        workflow_key = f"{workflow_type}_{state.get('user_id', 'unknown')}"
        
        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(workflow_key)
        if not circuit_breaker.can_execute():
            logger.warning(
                f"Circuit breaker is open for {workflow_key}",
                extra={"workflow_type": workflow_type}
            )
            return await self._handle_circuit_breaker_open(state, workflow_type)
        
        # Execute with retry logic
        last_error = None
        for attempt in range(self.config.max_retry_attempts + 1):
            try:
                # Execute the workflow
                result = await workflow_func(state)
                
                # Record success
                circuit_breaker.record_success()
                
                # Clean up old error records
                self._cleanup_error_history()
                
                return result
                
            except Exception as e:
                last_error = e
                
                # Classify error
                error_classification = self._classify_error(e, state, workflow_type)
                
                # Record error
                error_record = self._create_error_record(
                    e, state, workflow_type, error_classification.severity
                )
                self.error_history.append(error_record)
                
                # Determine recovery strategy
                recovery_strategy = self._determine_recovery_strategy(
                    error_classification, attempt, workflow_type
                )
                
                logger.warning(
                    f"Workflow error on attempt {attempt + 1}: {str(e)}",
                    extra={
                        "workflow_type": workflow_type,
                        "error_type": type(e).__name__,
                        "severity": error_classification.severity.value,
                        "recovery_strategy": recovery_strategy.value,
                        "attempt": attempt + 1,
                        "max_attempts": self.config.max_retry_attempts + 1
                    }
                )
                
                # Handle based on recovery strategy
                if recovery_strategy == RecoveryStrategy.FAIL_FAST:
                    circuit_breaker.record_failure()
                    return await self._create_error_response(e, state, workflow_type)
                
                elif recovery_strategy == RecoveryStrategy.CIRCUIT_BREAK:
                    circuit_breaker.record_failure()
                    return await self._handle_circuit_break(state, workflow_type, e)
                
                elif recovery_strategy == RecoveryStrategy.FALLBACK:
                    if fallback_handler or self.fallback_handlers.get(workflow_type):
                        handler = fallback_handler or self.fallback_handlers[workflow_type]
                        try:
                            return await handler(state, e)
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback handler failed: {str(fallback_error)}",
                                extra={"workflow_type": workflow_type}
                            )
                            # Continue to retry logic
                
                elif recovery_strategy == RecoveryStrategy.ESCALATE:
                    await self._escalate_error(error_record, workflow_type)
                    # Continue to retry logic
                
                # Retry logic (for RETRY strategy or when other strategies don't terminate)
                if attempt < self.config.max_retry_attempts:
                    # Calculate backoff delay
                    delay = self._calculate_backoff_delay(attempt, error_classification.severity)
                    
                    logger.info(
                        f"Retrying workflow in {delay:.2f}s (attempt {attempt + 2})",
                        extra={"workflow_type": workflow_type}
                    )
                    
                    await asyncio.sleep(delay)
                    
                    # Update state for retry
                    state = self._prepare_retry_state(state, attempt + 1, str(e))
        
        # All retries exhausted
        circuit_breaker.record_failure()
        
        logger.error(
            f"Workflow failed after {self.config.max_retry_attempts + 1} attempts",
            extra={
                "workflow_type": workflow_type,
                "final_error": str(last_error)
            }
        )
        
        return await self._create_error_response(last_error, state, workflow_type)
    
    def _classify_error(self, error: Exception, state: WorkflowState, workflow_type: str) -> 'ErrorClassification':
        """Classify error by type and severity"""
        error_type = type(error).__name__
        
        # Determine severity based on error type and context
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, (ConnectionError, OSError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, WorkflowError):
            # Use workflow error's recoverable flag to determine severity
            severity = ErrorSeverity.MEDIUM if error.recoverable else ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            severity = ErrorSeverity.LOW
        elif isinstance(error, (MemoryError, SystemError)):
            severity = ErrorSeverity.CRITICAL
        else:
            severity = ErrorSeverity.MEDIUM
        
        # Adjust severity based on workflow type
        critical_workflows = ["briefing", "scheduling", "calendar"]
        if workflow_type in critical_workflows and severity == ErrorSeverity.LOW:
            severity = ErrorSeverity.MEDIUM
        
        return ErrorClassification(
            error_type=error_type,
            severity=severity,
            is_retryable=self._is_retryable_error(error),
            is_circuit_breaking=severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        )
    
    def _determine_recovery_strategy(
        self,
        classification: 'ErrorClassification',
        attempt: int,
        workflow_type: str
    ) -> RecoveryStrategy:
        """Determine appropriate recovery strategy"""
        
        # Critical errors should fail fast
        if classification.severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.FAIL_FAST
        
        # High severity errors should circuit break after threshold
        if classification.is_circuit_breaking and attempt >= 2:
            return RecoveryStrategy.CIRCUIT_BREAK
        
        # Check if we should escalate based on error frequency
        recent_errors = self._get_recent_errors(workflow_type, window_minutes=5)
        if len(recent_errors) >= self.config.escalation_threshold:
            return RecoveryStrategy.ESCALATE
        
        # Use fallback if available and error is not retryable
        if not classification.is_retryable and (
            workflow_type in self.fallback_handlers or self.config.enable_fallback
        ):
            return RecoveryStrategy.FALLBACK
        
        # Default to retry for retryable errors
        if classification.is_retryable:
            return RecoveryStrategy.RETRY
        
        # Fail fast for non-retryable errors without fallback
        return RecoveryStrategy.FAIL_FAST
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Determine if error is retryable"""
        retryable_errors = (
            asyncio.TimeoutError,
            ConnectionError,
            OSError,
            # Add more retryable error types as needed
        )
        
        if isinstance(error, retryable_errors):
            return True
        
        if isinstance(error, WorkflowError):
            return error.recoverable
        
        # Consider certain generic errors as retryable
        error_msg = str(error).lower()
        if any(keyword in error_msg for keyword in ["timeout", "connection", "temporary", "rate limit"]):
            return True
        
        return False
    
    def _calculate_backoff_delay(self, attempt: int, severity: ErrorSeverity) -> float:
        """Calculate backoff delay for retry"""
        base_delay = 1.0
        
        # Adjust base delay by severity
        severity_multipliers = {
            ErrorSeverity.LOW: 0.5,
            ErrorSeverity.MEDIUM: 1.0,
            ErrorSeverity.HIGH: 2.0,
            ErrorSeverity.CRITICAL: 5.0
        }
        
        base_delay *= severity_multipliers.get(severity, 1.0)
        
        # Exponential backoff
        delay = base_delay * (self.config.retry_backoff_multiplier ** attempt)
        
        # Cap maximum delay
        return min(delay, 30.0)
    
    def _get_circuit_breaker(self, workflow_key: str) -> CircuitBreaker:
        """Get or create circuit breaker for workflow"""
        if workflow_key not in self.circuit_breakers:
            self.circuit_breakers[workflow_key] = CircuitBreaker(
                threshold=self.config.circuit_breaker_threshold,
                timeout=self.config.circuit_breaker_timeout
            )
        return self.circuit_breakers[workflow_key]
    
    def _create_error_record(
        self,
        error: Exception,
        state: WorkflowState,
        workflow_type: str,
        severity: ErrorSeverity
    ) -> ErrorRecord:
        """Create error record for tracking"""
        return ErrorRecord(
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            severity=severity,
            workflow_id=state.get("trace_id", "unknown"),
            workflow_type=workflow_type,
            user_id=state.get("user_id", "unknown"),
            error_message=str(error),
            context=getattr(error, "context", {})
        )
    
    def _get_recent_errors(self, workflow_type: str, window_minutes: int = 5) -> List[ErrorRecord]:
        """Get recent errors for workflow type within time window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        return [
            error for error in self.error_history
            if error.workflow_type == workflow_type and error.timestamp >= cutoff_time
        ]
    
    def _cleanup_error_history(self):
        """Remove old error records to prevent memory buildup"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.config.error_tracking_window)
        self.error_history = [
            error for error in self.error_history
            if error.timestamp >= cutoff_time
        ]
    
    def _prepare_retry_state(self, state: WorkflowState, attempt: int, error_msg: str) -> WorkflowState:
        """Prepare state for retry attempt"""
        retry_state = state.copy()
        retry_state.update({
            "retry_count": attempt,
            "last_error": error_msg,
            "retry_timestamp": datetime.utcnow().isoformat()
        })
        return retry_state
    
    async def _handle_circuit_breaker_open(self, state: WorkflowState, workflow_type: str) -> WorkflowState:
        """Handle circuit breaker open state"""
        error_msg = f"Circuit breaker is open for {workflow_type}"
        
        return await self._create_error_response(
            WorkflowError(error_msg, {"circuit_breaker": "open"}, recoverable=True),
            state,
            workflow_type
        )
    
    async def _handle_circuit_break(
        self,
        state: WorkflowState,
        workflow_type: str,
        error: Exception
    ) -> WorkflowState:
        """Handle circuit breaking scenario"""
        error_msg = f"Circuit breaker activated due to repeated failures in {workflow_type}"
        
        return await self._create_error_response(
            WorkflowError(error_msg, {"original_error": str(error)}, recoverable=True),
            state,
            workflow_type
        )
    
    async def _escalate_error(self, error_record: ErrorRecord, workflow_type: str):
        """Escalate error to monitoring/alerting system"""
        logger.critical(
            f"Escalating error for workflow {workflow_type}",
            extra={
                "error_record": {
                    "error_type": error_record.error_type,
                    "severity": error_record.severity.value,
                    "workflow_id": error_record.workflow_id,
                    "user_id": error_record.user_id,
                    "message": error_record.error_message
                },
                "recent_error_count": len(self._get_recent_errors(workflow_type))
            }
        )
        
        # TODO: Integrate with alerting system (PagerDuty, Slack, etc.)
    
    async def _create_error_response(
        self,
        error: Exception,
        state: WorkflowState,
        workflow_type: str
    ) -> WorkflowState:
        """Create standardized error response"""
        error_state = state.copy()
        error_state.update({
            "error": {
                "message": str(error),
                "type": type(error).__name__,
                "recoverable": getattr(error, "recoverable", False),
                "timestamp": datetime.utcnow().isoformat(),
                "context": getattr(error, "context", {})
            },
            "output_data": {
                "success": False,
                "error": str(error),
                "workflow_type": workflow_type,
                "recoverable": getattr(error, "recoverable", False),
                "suggested_actions": self._get_error_suggestions(error, workflow_type)
            },
            "current_node": "error_boundary",
            "visited_nodes": state.get("visited_nodes", []) + ["error_boundary"]
        })
        
        return error_state
    
    def _get_error_suggestions(self, error: Exception, workflow_type: str) -> List[str]:
        """Get user-friendly suggestions for error resolution"""
        suggestions = []
        
        if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
            suggestions.extend([
                "Try again in a few moments",
                "Check your internet connection",
                "Simplify your request if it's complex"
            ])
        elif isinstance(error, ConnectionError):
            suggestions.extend([
                "Check your internet connection",
                "Try again later",
                "Contact support if the problem persists"
            ])
        elif isinstance(error, WorkflowError) and error.recoverable:
            suggestions.extend([
                "Try again",
                "Provide more specific information",
                "Check your account permissions"
            ])
        else:
            suggestions.extend([
                "Try again later",
                "Contact support if the problem persists"
            ])
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def register_fallback_handler(self, workflow_type: str, handler: Callable):
        """Register fallback handler for workflow type"""
        self.fallback_handlers[workflow_type] = handler
        logger.info(f"Registered fallback handler for {workflow_type}")
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error boundary metrics"""
        now = datetime.utcnow()
        recent_errors = [
            error for error in self.error_history
            if (now - error.timestamp).total_seconds() <= 300  # Last 5 minutes
        ]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "circuit_breakers": {
                key: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
                for key, breaker in self.circuit_breakers.items()
            },
            "error_breakdown": self._get_error_breakdown(recent_errors)
        }
    
    def _get_error_breakdown(self, errors: List[ErrorRecord]) -> Dict[str, Any]:
        """Get breakdown of errors by type and severity"""
        breakdown = {
            "by_type": {},
            "by_severity": {},
            "by_workflow": {}
        }
        
        for error in errors:
            # By type
            breakdown["by_type"][error.error_type] = breakdown["by_type"].get(error.error_type, 0) + 1
            
            # By severity
            breakdown["by_severity"][error.severity.value] = breakdown["by_severity"].get(error.severity.value, 0) + 1
            
            # By workflow
            breakdown["by_workflow"][error.workflow_type] = breakdown["by_workflow"].get(error.workflow_type, 0) + 1
        
        return breakdown


@dataclass
class ErrorClassification:
    """Classification result for an error"""
    error_type: str
    severity: ErrorSeverity
    is_retryable: bool
    is_circuit_breaking: bool


# Global error boundary instance
workflow_error_boundary = WorkflowErrorBoundary()