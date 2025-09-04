"""
Base Workflow Supervisor Agent
Provides intelligent workflow supervision with LLM proposal + Policy enforcement
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
import json
import logging

from app.agents.services.context_builder import get_context_builder

logger = logging.getLogger(__name__)


@dataclass
class SupervisionResult:
    """Consistent response schema for all supervisors"""
    operation_type: str  # e.g., "create", "update", "delete", "list"
    parameters: Dict[str, Any]  # Extracted/proposed parameters
    ready_to_execute: bool  # Whether we have enough to proceed
    clarification_message: Optional[str] = None  # Message to ask user
    missing_context: List[str] = None  # What specific info is missing
    confidence: float = 0.0  # LLM confidence in the analysis
    policy_violations: List[str] = None  # Any policy issues found
    conversation_id: Optional[str] = None  # For multi-turn tracking


@dataclass
class LLMProposal:
    """LLM's proposed interpretation of user request"""
    operation_type: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str
    missing_context: List[str]
    clarification_suggestion: Optional[str]


@dataclass
class PolicyEnforcement:
    """Deterministic policy validation result"""
    valid: bool
    violations: List[str]
    required_fields: List[str]
    allowed_values: Dict[str, List[Any]]
    permission_errors: List[str]


class WorkflowPolicyValidator(ABC):
    """Base class for deterministic policy validation"""
    
    @abstractmethod
    def get_required_fields(self, operation_type: str) -> List[str]:
        """Return required fields for this operation"""
        pass
    
    @abstractmethod
    def get_allowed_values(self, field_name: str) -> List[Any]:
        """Return allowed values for a field"""
        pass
    
    @abstractmethod
    def validate_permissions(self, operation_type: str, context: Dict[str, Any]) -> List[str]:
        """Check user permissions for this operation"""
        pass
    
    def enforce_policy(self, proposal: LLMProposal, context: Dict[str, Any]) -> PolicyEnforcement:
        """Deterministic policy enforcement"""
        violations = []
        permission_errors = []
        
        # Check required fields
        required_fields = self.get_required_fields(proposal.operation_type)
        missing_required = [
            field for field in required_fields 
            if field not in proposal.parameters or proposal.parameters[field] is None
        ]
        
        if missing_required:
            violations.extend([f"Missing required field: {field}" for field in missing_required])
        
        # Check allowed values
        allowed_values = {}
        for field, value in proposal.parameters.items():
            allowed = self.get_allowed_values(field)
            if allowed and value not in allowed:
                violations.append(f"Invalid value '{value}' for field '{field}'. Allowed: {allowed}")
            allowed_values[field] = allowed or []
        
        # Check permissions
        permission_errors = self.validate_permissions(proposal.operation_type, context)
        
        return PolicyEnforcement(
            valid=len(violations) == 0 and len(permission_errors) == 0,
            violations=violations,
            required_fields=required_fields,
            allowed_values=allowed_values,
            permission_errors=permission_errors
        )


class BaseWorkflowSupervisor(ABC):
    """Base supervisor agent with LLM proposal + Policy enforcement"""
    
    def __init__(self, workflow_type: str, policy_validator: WorkflowPolicyValidator):
        self.workflow_type = workflow_type
        self.policy_validator = policy_validator
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.conversation_history: Dict[str, List[Dict]] = {}  # conversation_id -> messages
        self.context_builder = None
    
    async def supervise(
        self, 
        query: str, 
        context: Dict[str, Any], 
        conversation_id: Optional[str] = None
    ) -> SupervisionResult:
        """Main supervision flow with comprehensive context integration"""
        
        # Ensure context builder is initialized
        if not self.context_builder:
            self.context_builder = await get_context_builder()
        
        # Build comprehensive agent context
        user_id = context.get("user_id")
        session_id = context.get("session_id", conversation_id)
        
        if user_id and session_id:
            try:
                agent_context = await self.context_builder.build_context_for_agent(
                    user_id=user_id,
                    session_id=session_id,
                    workflow_type=self.workflow_type,
                    current_message=query,
                    context_options={
                        "include_memories": True,
                        "memory_limit": 8,
                        "conversation_limit": 15
                    }
                )
                # Merge agent context into existing context
                context = {**context, **agent_context}
                logger.info(f"Enhanced context with {agent_context.get('metadata', {}).get('context_token_count', 0)} tokens")
            except Exception as e:
                logger.error(f"Failed to build comprehensive context: {e}")
                # Continue with basic context
        
        # Step 1: LLM Analysis & Proposal
        llm_proposal = await self.get_llm_proposal(query, context, conversation_id)
        
        # Step 2: Deterministic Policy Enforcement  
        policy_result = self.policy_validator.enforce_policy(llm_proposal, context)
        
        # Step 3: Generate consistent response
        return self._generate_supervision_result(
            llm_proposal, policy_result, conversation_id
        )
    
    async def get_llm_proposal(
        self, 
        query: str, 
        context: Dict[str, Any], 
        conversation_id: Optional[str] = None
    ) -> LLMProposal:
        """LLM proposes operation and parameters using comprehensive context"""
        
        # Use comprehensive context if available, fallback to local conversation history
        conversation_context = ""
        if "conversation_context" in context:
            conversation_context = context["conversation_context"]
        elif conversation_id and conversation_id in self.conversation_history:
            history = self.conversation_history[conversation_id]
            conversation_context = f"Conversation History: {json.dumps(history, indent=2)}"
        
        prompt = await self._build_llm_prompt(query, context, conversation_context)
        
        try:
            response = await self.llm.ainvoke(prompt)
            return await self._parse_llm_response(response.content)
        except Exception as e:
            logger.error(f"LLM proposal generation failed: {e}")
            # Fallback proposal
            return LLMProposal(
                operation_type="unknown",
                parameters={},
                confidence=0.0,
                reasoning=f"LLM parsing failed: {e}",
                missing_context=["operation_type"],
                clarification_suggestion="I couldn't understand your request. Could you please rephrase it?"
            )
    
    def _generate_supervision_result(
        self, 
        llm_proposal: LLMProposal, 
        policy_result: PolicyEnforcement,
        conversation_id: Optional[str]
    ) -> SupervisionResult:
        """Generate consistent SupervisionResult"""
        
        # Determine readiness
        ready_to_execute = (
            policy_result.valid and 
            len(llm_proposal.missing_context) == 0 and
            llm_proposal.confidence > 0.3  # Minimum confidence threshold
        )
        
        # Generate clarification if needed
        clarification_message = None
        missing_context = []
        
        if not ready_to_execute:
            if policy_result.violations:
                # Policy violations take priority
                clarification_message = self._format_policy_violations(policy_result.violations)
                missing_context = policy_result.required_fields
            elif llm_proposal.missing_context:
                # Use LLM's suggested clarification
                clarification_message = llm_proposal.clarification_suggestion or \
                                      self._format_missing_context(llm_proposal.missing_context)
                missing_context = llm_proposal.missing_context
            elif llm_proposal.confidence <= 0.3:
                clarification_message = "I'm not confident I understood your request correctly. Could you please provide more details?"
                missing_context = ["clarification"]
        
        return SupervisionResult(
            operation_type=llm_proposal.operation_type,
            parameters=llm_proposal.parameters,
            ready_to_execute=ready_to_execute,
            clarification_message=clarification_message,
            missing_context=missing_context,
            confidence=llm_proposal.confidence,
            policy_violations=policy_result.violations + policy_result.permission_errors,
            conversation_id=conversation_id
        )
    
    def update_conversation(self, conversation_id: str, user_message: str, assistant_response: str):
        """Update conversation history for multi-turn support"""
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = []
        
        self.conversation_history[conversation_id].extend([
            {"role": "user", "content": user_message, "timestamp": datetime.utcnow().isoformat()},
            {"role": "assistant", "content": assistant_response, "timestamp": datetime.utcnow().isoformat()}
        ])
        
        # Limit conversation history to last 10 exchanges
        if len(self.conversation_history[conversation_id]) > 20:
            self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
    
    def _format_policy_violations(self, violations: List[str]) -> str:
        """Format policy violations into user-friendly message"""
        if len(violations) == 1:
            return f"I need more information: {violations[0]}"
        else:
            return f"I need more information:\n" + "\n".join(f"- {v}" for v in violations)
    
    def _format_missing_context(self, missing_context: List[str]) -> str:
        """Format missing context into user-friendly message"""
        if len(missing_context) == 1:
            field = missing_context[0].replace("_", " ")
            return f"What {field} would you like me to use?"
        else:
            fields = [field.replace("_", " ") for field in missing_context]
            return f"I need to know: {', '.join(fields)}"
    
    @abstractmethod
    async def _build_llm_prompt(
        self, 
        query: str, 
        context: Dict[str, Any], 
        conversation_context: str
    ) -> str:
        """Build workflow-specific LLM prompt"""
        pass
    
    @abstractmethod
    async def _parse_llm_response(self, response_content: str) -> LLMProposal:
        """Parse LLM response into LLMProposal"""
        pass