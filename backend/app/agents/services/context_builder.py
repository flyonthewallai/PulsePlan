"""
Context Builder Service
Builds comprehensive context for AI agents by integrating user profile, memory, and conversation history
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.infrastructure.user_context import get_user_context_service, UserContextSnapshot

logger = logging.getLogger(__name__)


class AgentContextBuilder:
    """Service for building comprehensive AI agent context"""
    
    def __init__(self):
        self.user_context_service = None
    
    async def _ensure_services(self):
        """Lazy initialize services"""
        if not self.user_context_service:
            self.user_context_service = await get_user_context_service()
    
    async def build_context_for_agent(
        self,
        user_id: str,
        session_id: str,
        workflow_type: str,
        current_message: str = "",
        context_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for AI agent workflows
        
        Args:
            user_id: User identifier
            session_id: Conversation session ID
            workflow_type: Type of workflow (chat, task, scheduling, etc.)
            current_message: Current user message for context
            context_options: Additional options for context building
        
        Returns:
            Dictionary containing formatted context for the agent
        """
        await self._ensure_services()
        
        try:
            # Set default options
            options = context_options or {}
            include_memories = options.get("include_memories", True)
            memory_limit = options.get("memory_limit", 8)
            conversation_limit = options.get("conversation_limit", 15)
            cache_enabled = options.get("cache_enabled", True)
            
            # Try to get cached context first
            context_snapshot = None
            if cache_enabled:
                context_snapshot = await self.user_context_service.get_cached_context(user_id)
            
            # Build fresh context if cache miss or disabled
            if not context_snapshot:
                context_snapshot = await self.user_context_service.build_comprehensive_context(
                    user_id=user_id,
                    session_id=session_id,
                    current_message=current_message,
                    include_memories=include_memories,
                    memory_limit=memory_limit,
                    conversation_limit=conversation_limit
                )
            
            # Format context based on workflow type
            formatted_context = await self._format_context_for_workflow(
                context_snapshot, workflow_type, options
            )
            
            # Add workflow-specific metadata
            formatted_context["metadata"] = {
                "workflow_type": workflow_type,
                "user_id": user_id,
                "session_id": session_id,
                "context_generated_at": context_snapshot.generated_at.isoformat(),
                "context_token_count": context_snapshot.context_token_count,
                "cache_version": context_snapshot.cache_version
            }
            
            logger.info(f"Built context for {workflow_type} workflow: {context_snapshot.context_token_count} tokens")
            return formatted_context
            
        except Exception as e:
            logger.error(f"Error building agent context for {user_id}: {e}")
            # Return minimal context on error
            return {
                "user_context": f"User ID: {user_id}",
                "conversation_context": "",
                "memory_context": "",
                "metadata": {
                    "workflow_type": workflow_type,
                    "user_id": user_id,
                    "session_id": session_id,
                    "error": str(e),
                    "context_generated_at": datetime.utcnow().isoformat(),
                    "context_token_count": 0
                }
            }
    
    async def _format_context_for_workflow(
        self,
        context_snapshot: UserContextSnapshot,
        workflow_type: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format context based on specific workflow requirements"""
        
        base_context = {
            "user_context": self._format_user_profile(context_snapshot),
            "conversation_context": self._format_conversation_history(context_snapshot),
            "memory_context": self._format_memory_context(context_snapshot)
        }
        
        # Workflow-specific formatting
        if workflow_type == "chat":
            # Chat workflows need full context
            base_context["system_context"] = self.user_context_service.format_context_for_llm(
                context_snapshot, include_memories=True
            )
        
        elif workflow_type == "task":
            # Task workflows focus on task-related memories and preferences
            base_context["task_context"] = self._format_task_context(context_snapshot)
            base_context["system_context"] = self._format_task_system_context(context_snapshot)
        
        elif workflow_type == "scheduling":
            # Scheduling workflows need calendar preferences and constraints
            base_context["scheduling_context"] = self._format_scheduling_context(context_snapshot)
            base_context["system_context"] = self._format_scheduling_system_context(context_snapshot)
        
        elif workflow_type == "briefing":
            # Briefing workflows need aggregated data and insights
            base_context["briefing_context"] = self._format_briefing_context(context_snapshot)
            base_context["system_context"] = self._format_briefing_system_context(context_snapshot)
        
        else:
            # Default formatting
            base_context["system_context"] = self.user_context_service.format_context_for_llm(
                context_snapshot, include_memories=True
            )
        
        return base_context
    
    def _format_user_profile(self, context: UserContextSnapshot) -> str:
        """Format user profile for agent context"""
        profile = context.profile
        
        sections = []
        sections.append(f"Name: {profile.name or 'User'}")
        
        if profile.timezone:
            sections.append(f"Timezone: {profile.timezone}")
        
        if profile.agent_description:
            sections.append(f"Description: {profile.agent_description}")
            
        if profile.agent_instructions:
            sections.append(f"Instructions: {profile.agent_instructions}")
            
        if profile.working_hours:
            sections.append(f"Working Hours: {profile.working_hours}")
        
        return " | ".join(sections)
    
    def _format_conversation_history(self, context: UserContextSnapshot) -> str:
        """Format recent conversation for agent context"""
        if not context.recent_conversations or not context.recent_conversations[0].messages:
            return "No recent conversation history."
        
        conv = context.recent_conversations[0]
        recent_messages = conv.messages[-6:]  # Last 6 messages
        
        formatted = []
        for msg in recent_messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:150]  # Truncate
            formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _format_memory_context(self, context: UserContextSnapshot) -> str:
        """Format relevant memories for agent context"""
        if not context.relevant_memories:
            return "No relevant memories found."
        
        formatted = []
        for i, memory in enumerate(context.relevant_memories[:3], 1):
            namespace = memory.get("namespace", "").upper()
            summary = memory.get("summary", "")
            formatted.append(f"{i}. [{namespace}] {summary}")
        
        return "\n".join(formatted)
    
    def _format_task_context(self, context: UserContextSnapshot) -> str:
        """Format task-specific context"""
        task_memories = [
            m for m in context.relevant_memories 
            if m.get("namespace") in ["task", "assignment", "course"]
        ]
        
        if not task_memories:
            return "No task-related context available."
        
        formatted = []
        for memory in task_memories[:5]:
            summary = memory.get("summary", "")
            metadata = memory.get("metadata", {})
            due_date = metadata.get("due_date", "")
            priority = metadata.get("priority", "")
            
            entry = summary
            if due_date:
                entry += f" (due: {due_date})"
            if priority:
                entry += f" [priority: {priority}]"
                
            formatted.append(entry)
        
        return "\n".join(formatted)
    
    def _format_task_system_context(self, context: UserContextSnapshot) -> str:
        """Format system context for task workflows"""
        profile = context.profile
        
        sections = [
            f"USER: {profile.name or 'User'} ({profile.timezone})"
        ]
        
        if profile.agent_instructions:
            sections.append(f"INSTRUCTIONS: {profile.agent_instructions}")
        
        # Task-focused memory context
        task_memories = [m for m in context.relevant_memories if m.get("namespace") in ["task", "assignment"]]
        if task_memories:
            sections.append(f"RELEVANT TASKS ({len(task_memories)}):")
            for memory in task_memories[:3]:
                sections.append(f"- {memory.get('summary', '')}")
        
        return "\n".join(sections)
    
    def _format_scheduling_context(self, context: UserContextSnapshot) -> str:
        """Format scheduling-specific context"""
        profile = context.profile
        
        scheduling_info = []
        
        if profile.working_hours:
            scheduling_info.append(f"Working Hours: {profile.working_hours}")
        
        if profile.study_preferences:
            scheduling_info.append(f"Study Preferences: {profile.study_preferences}")
        
        # Calendar-related memories
        calendar_memories = [
            m for m in context.relevant_memories 
            if m.get("namespace") in ["calendar", "assignment"]
        ]
        
        if calendar_memories:
            scheduling_info.append("Recent Calendar Events:")
            for memory in calendar_memories[:3]:
                scheduling_info.append(f"- {memory.get('summary', '')}")
        
        return "\n".join(scheduling_info) if scheduling_info else "No scheduling context available."
    
    def _format_scheduling_system_context(self, context: UserContextSnapshot) -> str:
        """Format system context for scheduling workflows"""
        profile = context.profile
        
        sections = [
            f"USER: {profile.name or 'User'}"
        ]
        
        if profile.timezone:
            sections.append(f"TIMEZONE: {profile.timezone}")
        
        if profile.working_hours:
            sections.append(f"WORK HOURS: {profile.working_hours}")
        
        if profile.agent_instructions:
            sections.append(f"PREFERENCES: {profile.agent_instructions}")
        
        return "\n".join(sections)
    
    def _format_briefing_context(self, context: UserContextSnapshot) -> str:
        """Format briefing-specific context"""
        all_memories = context.relevant_memories
        
        if not all_memories:
            return "No data available for briefing."
        
        # Group memories by namespace
        memory_groups = {}
        for memory in all_memories:
            namespace = memory.get("namespace", "unknown")
            if namespace not in memory_groups:
                memory_groups[namespace] = []
            memory_groups[namespace].append(memory)
        
        formatted = []
        for namespace, memories in memory_groups.items():
            formatted.append(f"{namespace.upper()} ({len(memories)} items):")
            for memory in memories[:2]:  # Top 2 per category
                formatted.append(f"- {memory.get('summary', '')}")
        
        return "\n".join(formatted)
    
    def _format_briefing_system_context(self, context: UserContextSnapshot) -> str:
        """Format system context for briefing workflows"""
        profile = context.profile
        
        return f"""USER PROFILE: {profile.name or 'User'} ({profile.timezone})
AVAILABLE DATA: {len(context.relevant_memories)} memory items across {len(set(m.get('namespace', '') for m in context.relevant_memories))} categories
CONTEXT GENERATED: {context.generated_at.strftime('%Y-%m-%d %H:%M')}"""


# Global context builder instance
_context_builder: Optional[AgentContextBuilder] = None

async def get_context_builder() -> AgentContextBuilder:
    """Get global context builder instance"""
    global _context_builder
    
    if _context_builder is None:
        _context_builder = AgentContextBuilder()
    
    return _context_builder