"""
Enhanced Pydantic Schemas with Versioning and Validation
Production-ready schemas with trace IDs, migration support, and comprehensive validation
"""
import uuid
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import json
import logging

logger = logging.getLogger(__name__)


class SchemaVersion(str, Enum):
    """Schema version enumeration"""
    V1_0 = "1.0"
    V1_1 = "1.1" 
    V2_0 = "2.0"


class WorkflowOperation(str, Enum):
    """Valid workflow operations"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    GET = "get"
    LIST = "list"
    BULK_TOGGLE = "bulk_toggle"
    CONVERT_TO_TASK = "convert_to_task"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    """Task/Todo status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ConfidenceLevel(str, Enum):
    """Confidence level categories"""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


class BaseVersionedModel(BaseModel):
    """Base model with versioning and trace ID support"""
    
    version: SchemaVersion = Field(default=SchemaVersion.V2_0, description="Schema version")
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Workflow trace ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ValidationError(BaseModel):
    """Structured validation error"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    value: Any = Field(..., description="Invalid value")
    constraint: Optional[str] = Field(None, description="Validation constraint that failed")


class SupervisionResult(BaseVersionedModel):
    """Enhanced supervision result with comprehensive validation"""
    
    operation_type: WorkflowOperation = Field(..., description="Type of operation to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    ready_to_execute: bool = Field(..., description="Whether workflow can proceed")
    
    # Confidence and quality metrics
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence score")
    confidence_level: ConfidenceLevel = Field(..., description="Categorized confidence level")
    
    # Contextual information
    clarification_message: Optional[str] = Field(None, description="Message requesting more information")
    missing_context: List[str] = Field(default_factory=list, description="Missing required context")
    policy_violations: List[str] = Field(default_factory=list, description="Policy violations found")
    
    # Conversation management
    conversation_id: Optional[str] = Field(None, description="Multi-turn conversation ID")
    turn_number: int = Field(default=1, ge=1, description="Turn number in conversation")
    
    # Execution metadata
    execution_time_ms: Optional[float] = Field(None, ge=0, description="Processing time in milliseconds")
    llm_tokens_used: Optional[int] = Field(None, ge=0, description="LLM tokens consumed")
    cache_hit: bool = Field(default=False, description="Whether result was cached")
    
    # Error handling
    validation_errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    
    @validator('confidence_level', pre=True, always=True)
    def set_confidence_level(cls, v, values):
        """Automatically set confidence level based on confidence score"""
        if 'confidence' in values:
            confidence = values['confidence']
            if confidence <= 0.2:
                return ConfidenceLevel.VERY_LOW
            elif confidence <= 0.4:
                return ConfidenceLevel.LOW
            elif confidence <= 0.6:
                return ConfidenceLevel.MEDIUM
            elif confidence <= 0.8:
                return ConfidenceLevel.HIGH
            else:
                return ConfidenceLevel.VERY_HIGH
        return v
    
    @validator('parameters')
    def validate_operation_parameters(cls, v, values):
        """Validate parameters based on operation type"""
        if 'operation_type' not in values:
            return v
            
        operation = values['operation_type']
        errors = []
        
        # Operation-specific validation
        if operation == WorkflowOperation.CREATE:
            if not v.get('title'):
                errors.append(ValidationError(
                    field="title",
                    message="Title is required for create operations",
                    value=v.get('title'),
                    constraint="required"
                ))
        
        elif operation in [WorkflowOperation.UPDATE, WorkflowOperation.DELETE, WorkflowOperation.GET]:
            if not v.get('todo_id') and not v.get('task_id') and not v.get('id'):
                errors.append(ValidationError(
                    field="id",
                    message=f"ID is required for {operation} operations",
                    value=None,
                    constraint="required"
                ))
        
        elif operation == WorkflowOperation.BULK_TOGGLE:
            if not v.get('todo_ids') and not v.get('task_ids'):
                errors.append(ValidationError(
                    field="ids",
                    message="IDs list is required for bulk operations",
                    value=None,
                    constraint="required"
                ))
        
        # Store validation errors
        if errors and 'validation_errors' in values:
            values['validation_errors'].extend(errors)
        
        return v
    
    @root_validator
    def validate_consistency(cls, values):
        """Validate overall consistency of the result"""
        ready = values.get('ready_to_execute', False)
        missing_context = values.get('missing_context', [])
        clarification = values.get('clarification_message')
        policy_violations = values.get('policy_violations', [])
        
        # If not ready to execute, should have clarification or missing context
        if not ready and not clarification and not missing_context and not policy_violations:
            values['warnings'] = values.get('warnings', []) + [
                "Not ready to execute but no clarification provided"
            ]
        
        # If ready to execute, shouldn't have missing context
        if ready and missing_context:
            values['warnings'] = values.get('warnings', []) + [
                "Ready to execute but missing context specified"
            ]
        
        return values
    
    def is_high_confidence(self) -> bool:
        """Check if result has high confidence"""
        return self.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
    
    def has_errors(self) -> bool:
        """Check if result has validation errors"""
        return len(self.validation_errors) > 0 or len(self.policy_violations) > 0
    
    def to_execution_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for workflow execution"""
        return {
            "operation_type": self.operation_type,
            "parameters": self.parameters,
            "trace_id": self.trace_id,
            "conversation_id": self.conversation_id,
            "metadata": {
                "confidence": self.confidence,
                "execution_time_ms": self.execution_time_ms,
                "cache_hit": self.cache_hit,
                "version": self.version
            }
        }


class LLMProposal(BaseVersionedModel):
    """LLM's proposed interpretation with enhanced metadata"""
    
    operation_type: WorkflowOperation = Field(..., description="Proposed operation")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Extracted parameters")
    confidence: float = Field(..., ge=0.0, le=1.0, description="LLM confidence score")
    reasoning: str = Field(..., min_length=1, description="Brief LLM reasoning for the proposal (max 10 words)")
    
    # Context analysis
    missing_context: List[str] = Field(default_factory=list, description="Missing required context")
    clarification_suggestion: Optional[str] = Field(None, description="Suggested clarification question")
    
    # LLM metadata
    model_used: Optional[str] = Field(None, description="LLM model that generated this proposal")
    tokens_used: Optional[int] = Field(None, ge=0, description="Tokens consumed")
    response_time_ms: Optional[float] = Field(None, ge=0, description="LLM response time")
    prompt_version: str = Field(default="1.0", description="Prompt template version used")
    
    # Quality indicators
    ambiguity_detected: bool = Field(default=False, description="Whether ambiguity was detected")
    alternative_interpretations: List[str] = Field(default_factory=list, description="Alternative interpretations considered")
    
    @validator('reasoning')
    def validate_reasoning_quality(cls, v):
        """Ensure reasoning meets quality standards"""
        if len(v.strip()) < 10:
            raise ValueError("Reasoning must be at least 10 characters")
        
        # Check for generic responses
        generic_phrases = ["i think", "maybe", "probably", "not sure"]
        if any(phrase in v.lower() for phrase in generic_phrases):
            logger.warning(f"Generic reasoning detected: {v[:50]}...")
        
        return v.strip()


class PolicyEnforcement(BaseVersionedModel):
    """Enhanced policy enforcement result"""
    
    valid: bool = Field(..., description="Whether proposal passes policy checks")
    violations: List[str] = Field(default_factory=list, description="Policy violations found")
    warnings: List[str] = Field(default_factory=list, description="Policy warnings")
    
    # Required field analysis
    required_fields: List[str] = Field(default_factory=list, description="Required fields for operation")
    missing_required: List[str] = Field(default_factory=list, description="Missing required fields")
    
    # Value validation
    allowed_values: Dict[str, List[Any]] = Field(default_factory=dict, description="Allowed values per field")
    invalid_values: Dict[str, Any] = Field(default_factory=dict, description="Invalid values found")
    
    # Permission checks
    permission_errors: List[str] = Field(default_factory=list, description="Permission violations")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context used for validation")
    
    # Policy metadata
    policies_checked: List[str] = Field(default_factory=list, description="Policies that were evaluated")
    policy_version: str = Field(default="1.0", description="Policy rule version")
    
    def is_critical_violation(self) -> bool:
        """Check if violations are critical (block execution)"""
        critical_keywords = ["security", "permission", "required", "forbidden"]
        return any(
            any(keyword in violation.lower() for keyword in critical_keywords)
            for violation in self.violations
        )
    
    def get_actionable_feedback(self) -> List[str]:
        """Get user-actionable feedback messages"""
        feedback = []
        
        if self.missing_required:
            feedback.append(f"Please provide: {', '.join(self.missing_required)}")
        
        if self.invalid_values:
            for field, value in self.invalid_values.items():
                allowed = self.allowed_values.get(field, [])
                if allowed:
                    feedback.append(f"'{field}' must be one of: {', '.join(map(str, allowed))}")
                else:
                    feedback.append(f"'{field}' has an invalid value: {value}")
        
        if self.permission_errors:
            feedback.extend(self.permission_errors)
        
        return feedback


class WorkflowTrace(BaseVersionedModel):
    """Complete workflow execution trace"""
    
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique workflow ID")
    user_id: str = Field(..., description="User who initiated workflow")
    workflow_type: str = Field(..., description="Type of workflow executed")
    
    # Execution flow
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Workflow start time")
    end_time: Optional[datetime] = Field(None, description="Workflow completion time")
    status: Literal["running", "completed", "failed", "cancelled"] = Field(default="running")
    
    # Processing steps
    supervision_result: Optional[SupervisionResult] = Field(None, description="Supervision analysis")
    llm_proposal: Optional[LLMProposal] = Field(None, description="LLM proposal")
    policy_enforcement: Optional[PolicyEnforcement] = Field(None, description="Policy validation")
    
    # Results
    final_result: Optional[Dict[str, Any]] = Field(None, description="Final workflow result")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Performance metrics
    total_duration_ms: Optional[float] = Field(None, ge=0, description="Total execution time")
    llm_calls_made: int = Field(default=0, ge=0, description="Number of LLM calls")
    cache_hits: int = Field(default=0, ge=0, description="Number of cache hits")
    database_queries: int = Field(default=0, ge=0, description="Number of database queries")
    
    def mark_completed(self, result: Dict[str, Any] = None):
        """Mark workflow as completed"""
        self.end_time = datetime.utcnow()
        self.status = "completed"
        if result:
            self.final_result = result
        
        if self.start_time:
            self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
    
    def mark_failed(self, error: str):
        """Mark workflow as failed"""
        self.end_time = datetime.utcnow()
        self.status = "failed"
        self.error_message = error
        
        if self.start_time:
            self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000


class SchemaMigrator:
    """Handle schema migrations between versions"""
    
    @staticmethod
    def migrate_supervision_result(data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate SupervisionResult between schema versions"""
        
        if from_version == "1.0" and to_version >= "1.1":
            # Add new fields introduced in v1.1
            data.setdefault("confidence_level", "medium")
            data.setdefault("turn_number", 1)
            data.setdefault("validation_errors", [])
            data.setdefault("warnings", [])
        
        if from_version <= "1.1" and to_version >= "2.0":
            # Add new fields introduced in v2.0
            data.setdefault("execution_time_ms", None)
            data.setdefault("llm_tokens_used", None)
            data.setdefault("cache_hit", False)
        
        # Update version
        data["version"] = to_version
        return data
    
    @staticmethod
    def migrate_llm_proposal(data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
        """Migrate LLMProposal between schema versions"""
        
        if from_version == "1.0" and to_version >= "2.0":
            # Add new metadata fields
            data.setdefault("model_used", "unknown")
            data.setdefault("prompt_version", "1.0")
            data.setdefault("ambiguity_detected", False)
            data.setdefault("alternative_interpretations", [])
        
        data["version"] = to_version
        return data
    
    @staticmethod
    def auto_migrate(model_class: BaseModel, data: Dict[str, Any]) -> BaseModel:
        """Automatically migrate data to latest schema version"""
        current_version = data.get("version", "1.0")
        target_version = SchemaVersion.V2_0.value  # Always migrate to latest
        
        if current_version != target_version:
            if model_class == SupervisionResult:
                data = SchemaMigrator.migrate_supervision_result(data, current_version, target_version)
            elif model_class == LLMProposal:
                data = SchemaMigrator.migrate_llm_proposal(data, current_version, target_version)
            
            logger.info(f"Migrated {model_class.__name__} from v{current_version} to v{target_version}")
        
        return model_class(**data)