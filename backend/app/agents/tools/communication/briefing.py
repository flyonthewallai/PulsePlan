"""
Briefing and data aggregation tools for PulsePlan agents.
Handles data collection and content synthesis for daily briefings.
"""
from typing import Dict, Any, List
import asyncio
import logging
from datetime import datetime, timedelta
from ..core.base import BriefingTool, ToolResult, ToolError
from app.services.briefing_service import BriefingService, get_briefing_service

logger = logging.getLogger(__name__)


class DataAggregatorTool(BriefingTool):
    """Tool for aggregating data from multiple sources"""
    
    def __init__(self, briefing_service: BriefingService = None):
        super().__init__(
            name="data_aggregator",
            description="Aggregates data from emails, calendar, and tasks for briefings"
        )
        self.briefing_service = briefing_service or get_briefing_service()
    
    def get_required_tokens(self) -> list[str]:
        return []  # Uses other tools that handle tokens
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate data aggregation input"""
        # Accept either sources list OR briefing_date format (used by workflow)
        if "sources" in input_data:
            sources = input_data.get("sources", [])
            if not sources or not isinstance(sources, list):
                return False
            valid_sources = ["email", "calendar", "tasks", "weather", "news"]
            return all(source in valid_sources for source in sources)

        # Also accept briefing_date format (workflow uses this)
        return "briefing_date" in input_data or "user_id" in input_data
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute data aggregation"""
        start_time = datetime.utcnow()

        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - sources list or briefing_date required", self.name)

            # Handle both input formats: sources list (old) or workflow format (new)
            if "sources" in input_data:
                sources = input_data["sources"]
            else:
                # Default sources for briefing workflow
                sources = ["email", "calendar", "tasks"]

            # Update context with connected accounts if provided
            if "connected_accounts" in input_data:
                context["connected_accounts"] = input_data["connected_accounts"]

            result = await self.aggregate_data(sources, context)

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time

            self.log_execution(input_data, result, context)
            return result

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )

            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def aggregate_data(self, sources: list[str], context: Dict[str, Any]) -> ToolResult:
        """Aggregate data from multiple sources with caching"""
        try:
            from app.services.infrastructure.cache_service import get_cache_service
            import hashlib
            
            user_id = context["user_id"]
            connected_accounts = context.get("connected_accounts", {})
            
            # Create cache key for user data
            cache_key_data = f"{user_id}_{sources}_{datetime.utcnow().date().isoformat()}"
            cache_key = f"briefing_data:{hashlib.md5(cache_key_data.encode()).hexdigest()}"
            
            # Check cache first (cache for 30 minutes)
            try:
                cache_service = get_cache_service()
                cached_data = await cache_service.get(cache_key)
                if cached_data:
                    return ToolResult(
                        success=True,
                        data={"aggregated_data": cached_data},
                        metadata={"operation": "aggregate", "sources": sources, "cached": True}
                    )
            except Exception as cache_error:
                logger.warning(f"Cache get failed, continuing without cache: {cache_error}")
            
            aggregated_data = {}
            
            # Aggregate email data
            if "email" in sources:
                email_data = await self._aggregate_email_data(connected_accounts, user_id)
                aggregated_data["email"] = email_data
            
            # Aggregate calendar data  
            if "calendar" in sources:
                calendar_data = await self._aggregate_calendar_data(connected_accounts, user_id)
                aggregated_data["calendar"] = calendar_data
            
            # Aggregate task data
            if "tasks" in sources:
                task_data = await self._aggregate_task_data(user_id)
                aggregated_data["tasks"] = task_data
            
            # Add metadata
            aggregated_data["metadata"] = {
                "aggregation_timestamp": datetime.utcnow().isoformat(),
                "sources_requested": sources,
                "sources_available": list(aggregated_data.keys()),
                "user_id": user_id
            }

            # Cache the aggregated data for 30 minutes
            try:
                await cache_service.set(cache_key, aggregated_data, ttl_seconds=1800)
            except Exception as cache_error:
                logger.warning(f"Cache set failed, continuing without cache: {cache_error}")
            
            return ToolResult(
                success=True,
                data={"aggregated_data": aggregated_data},
                metadata={"operation": "aggregate", "sources": sources, "cached": False}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to aggregate data: {e}", self.name, recoverable=True)
    
    async def _aggregate_email_data(self, connected_accounts: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Aggregate email data from connected accounts using BriefingService"""
        try:
            return await self.briefing_service.aggregate_email_data(user_id, connected_accounts)
        except Exception as e:
            logger.error(f"Error aggregating email data: {e}")
            return {
                "total_emails": 0,
                "unread_emails": 0,
                "important_emails": [],
                "accounts": [],
                "summary": "Unable to fetch email data at this time."
            }
    
    async def _aggregate_calendar_data(self, connected_accounts: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Aggregate calendar data using BriefingService"""
        try:
            return await self.briefing_service.aggregate_calendar_data(user_id, connected_accounts)
        except Exception as e:
            logger.error(f"Error aggregating calendar data: {e}")
            return {
                "total_events_today": 0,
                "total_events_week": 0,
                "upcoming_events": [],
                "providers": [],
                "summary": "Unable to fetch calendar data at this time."
            }
    
    async def _aggregate_task_data(self, user_id: str) -> Dict[str, Any]:
        """Aggregate task data using BriefingService"""
        try:
            return await self.briefing_service.aggregate_task_data(user_id)
        except Exception as e:
            logger.error(f"Error aggregating task data: {e}")
            return {
                "total_tasks": 0,
                "overdue_tasks": 0,
                "due_today": 0,
                "due_this_week": 0,
                "completed_yesterday": 0,
                "high_priority_tasks": [],
                "summary": "Unable to fetch task data at this time."
            }
    
    async def synthesize_content(self, data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for aggregator tool"""
        raise ToolError("Content synthesis not supported by aggregator tool", self.name)


class ContentSynthesizerTool(BriefingTool):
    """Tool for synthesizing content into briefings"""
    
    def __init__(self):
        super().__init__(
            name="content_synthesizer",
            description="Synthesizes aggregated data into coherent briefings using LLM"
        )
    
    def get_required_tokens(self) -> list[str]:
        return []  # Uses LLM API, not OAuth tokens
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate content synthesis input"""
        if not input_data.get("aggregated_data"):
            return False
        
        synthesis_type = input_data.get("synthesis_type", "daily_briefing")
        valid_types = ["daily_briefing", "weekly_summary", "custom"]
        
        return synthesis_type in valid_types
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute content synthesis"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - aggregated_data required", self.name)
            
            aggregated_data = input_data["aggregated_data"]
            synthesis_type = input_data.get("synthesis_type", "daily_briefing")
            
            result = await self.synthesize_content(aggregated_data, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result.execution_time = execution_time
            
            self.log_execution(input_data, result, context)
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_result = ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time
            )
            
            self.log_execution(input_data, error_result, context)
            return error_result
    
    async def synthesize_content(self, data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Synthesize aggregated data into briefing content using LLM"""
        try:
            # Use LLM to synthesize content intelligently
            synthesized_content = await self._llm_synthesize(data, context)
            
            return ToolResult(
                success=True,
                data={
                    "synthesized_content": synthesized_content,
                    "synthesis_metadata": {
                        "synthesis_method": "llm",
                        "data_sources": list(data.keys()),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                },
                metadata={"operation": "synthesize", "method": "llm"}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to synthesize content: {e}", self.name, recoverable=True)
    
    async def _llm_synthesize(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to synthesize briefing content with cost optimization"""
        from langchain_openai import ChatOpenAI
        from app.services.infrastructure.cache_service import get_cache_service
        import json
        import hashlib
        
        # Create cache key based on data content
        data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        cache_key = f"briefing_synthesis:{data_hash}"
        
        # Check cache first
        try:
            cache_service = get_cache_service()
            cached_result = await cache_service.get(cache_key)
            if cached_result:
                return cached_result
        except Exception as cache_error:
            logger.warning(f"Cache get failed for synthesis, continuing: {cache_error}")
        
        # Use gpt-4o-mini for cost efficiency, optimized settings
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.1,  # Lower temperature for consistency
            max_tokens=500,   # Limit tokens for cost control
            timeout=15        # Quick timeout
        )
        
        # Prepare data for LLM
        data_summary = self._prepare_data_for_llm(data)
        
        # Optimized, concise prompt to reduce token usage
        prompt = f"""Create a brief daily summary from: {data_summary}

IMPORTANT: Use the exact times provided in the data (e.g., "4:00 PM", "5:00 PM") - do not convert or modify them.

Return JSON with:
{{
    "greeting": "Brief morning greeting",
    "email_summary": "Key email highlights (1-2 sentences)",
    "calendar_overview": "Today's schedule summary (1-2 sentences) - use the exact times from the data", 
    "task_status": "Task priorities (1-2 sentences)",
    "priority_items": ["Top 3 priorities"],
    "recommendations": ["2-3 quick tips"],
    "closing": "Short motivational note"
}}

Keep all fields concise and actionable."""
        
        try:
            response = llm.invoke(prompt)
            
            # Parse LLM response - ensure we handle the response properly
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            try:
                # Clean the response content to handle markdown code blocks
                response_content = response_content.strip()
                
                # Remove markdown code block markers if present
                if response_content.startswith("```json"):
                    response_content = response_content[7:]  # Remove ```json
                elif response_content.startswith("```"):
                    response_content = response_content[3:]   # Remove ```
                
                if response_content.endswith("```"):
                    response_content = response_content[:-3]  # Remove trailing ```
                
                response_content = response_content.strip()
                
                synthesized_content = json.loads(response_content)
                
                # Add generated timestamp
                synthesized_content["generated_at"] = datetime.utcnow().isoformat()

                # Cache the result for 2 hours to reduce API calls
                try:
                    await cache_service.set(cache_key, synthesized_content, ttl_seconds=7200)
                except Exception as cache_error:
                    logger.warning(f"Cache set failed for synthesis, continuing: {cache_error}")
                
                return synthesized_content
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing failed: {json_error}")
                logger.error(f"Raw response: {response_content}")
                # Fallback to structured response if JSON parsing fails
                return self._fallback_synthesis(data, f"JSON parsing failed: {json_error}")
                
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Fallback to template-based synthesis if LLM fails
            return self._fallback_synthesis(data, str(e))
    
    def _prepare_data_for_llm(self, data: Dict[str, Any]) -> str:
        """Prepare aggregated data for LLM processing"""
        sections = []
        
        # Handle the nested structure from DataAggregatorTool
        aggregated_data = data.get("aggregated_data", data)
        
        if "email" in aggregated_data:
            email_data = aggregated_data["email"]
            total_emails = email_data.get('total_emails', 0) if isinstance(email_data, dict) else 0
            unread_emails = email_data.get('unread_emails', 0) if isinstance(email_data, dict) else 0
            sections.append(f"EMAILS: {total_emails} total, {unread_emails} unread")
            
            if email_data.get("important_emails"):
                sections.append("Important emails:")
                for email in email_data["important_emails"][:3]:  # Top 3
                    sections.append(f"  - {email.get('subject', 'No subject')} from {email.get('from', 'Unknown')}")
        
        if "calendar" in aggregated_data:
            calendar_data = aggregated_data["calendar"]
            sections.append(f"CALENDAR: {calendar_data.get('total_events_today', 0)} events today")
            
            if calendar_data.get("upcoming_events"):
                sections.append("Today's events:")
                for event in calendar_data["upcoming_events"][:3]:  # Top 3
                    time_display = event.get('time_display', 'All day')
                    sections.append(f"  - {event.get('title', 'No title')} at {time_display}")
        
        if "tasks" in aggregated_data:
            task_data = aggregated_data["tasks"]
            sections.append(f"TASKS: {task_data.get('total_tasks', 0)} total, {task_data.get('due_today', 0)} due today, {task_data.get('overdue_tasks', 0)} overdue")
            
            if task_data.get("high_priority_tasks"):
                sections.append("High priority tasks:")
                for task in task_data["high_priority_tasks"][:3]:  # Top 3
                    sections.append(f"  - {task.get('title', 'No title')} (due: {task.get('due', 'No due date')})")
        
        result = "\n".join(sections)
        return result
    
    def _fallback_synthesis(self, data: Dict[str, Any], error: str = None) -> Dict[str, Any]:
        """Fallback content synthesis when LLM fails"""
        # Extract priority items from actual data
        priority_items = []
        if "tasks" in data and data["tasks"].get("high_priority_tasks"):
            for task in data["tasks"]["high_priority_tasks"][:3]:
                priority_items.append(f"{task.get('title', 'Untitled task')} (due: {task.get('due', 'No date')})")
        
        # Extract recommendations based on actual data
        recommendations = []
        if "tasks" in data:
            task_data = data["tasks"]
            if task_data.get("overdue_tasks", 0) > 0:
                recommendations.append(f"Address {task_data['overdue_tasks']} overdue tasks first")
            if task_data.get("due_today", 0) > 0:
                recommendations.append(f"Focus on {task_data['due_today']} tasks due today")
        
        if "calendar" in data:
            calendar_data = data["calendar"]
            if calendar_data.get("total_events_today", 0) > 0:
                recommendations.append("Prepare for today's meetings")
            else:
                recommendations.append("Block time for focused work")
        
        # Default recommendations if none generated
        if not recommendations:
            recommendations = [
                "Block time for focused work",
                "Review your calendar for the week",
                "Address overdue tasks first"
            ]
        
        return {
            "greeting": "Good morning! Here's your daily briefing.",
            "email_summary": self._extract_email_summary(data),
            "calendar_overview": self._extract_calendar_summary(data),
            "task_status": self._extract_task_summary(data),
            "priority_items": priority_items if priority_items else [
                "Review important emails",
                "Prepare for today's meetings", 
                "Focus on high-priority tasks"
            ],
            "recommendations": recommendations,
            "closing": "Have a productive day!",
            "generated_at": datetime.utcnow().isoformat(),
            "fallback_reason": f"LLM synthesis failed: {error}" if error else "Using fallback synthesis"
        }
    
    def _extract_email_summary(self, data: Dict[str, Any]) -> str:
        """Extract email summary from aggregated data"""
        if "email" not in data:
            return "No email data available."
        
        email_data = data["email"]
        total = email_data.get("total_emails", 0)
        unread = email_data.get("unread_emails", 0)
        
        return f"You have {total} emails today with {unread} unread. Check for important messages from your manager or clients."
    
    def _extract_calendar_summary(self, data: Dict[str, Any]) -> str:
        """Extract calendar summary from aggregated data"""
        if "calendar" not in data:
            return "No calendar data available."
        
        calendar_data = data["calendar"]
        today_events = calendar_data.get("total_events_today", 0)
        upcoming_events = calendar_data.get("upcoming_events", [])
        
        if today_events == 0:
            return "You have a free day with no scheduled meetings."
        elif today_events == 1 and upcoming_events:
            event = upcoming_events[0]
            event_title = event.get("title", "meeting")
            event_time = event.get("time_display", "")
            if event_time:
                return f"You have 1 meeting today: {event_title} at {event_time}."
            else:
                return f"You have 1 meeting today: {event_title}."
        else:
            return f"You have {today_events} meetings scheduled today. Make sure to prepare in advance."
    
    def _extract_task_summary(self, data: Dict[str, Any]) -> str:
        """Extract task summary from aggregated data"""
        if "tasks" not in data:
            return "No task data available."
        
        task_data = data["tasks"]
        total = task_data.get("total_tasks", 0)
        due_today = task_data.get("due_today", 0)
        overdue = task_data.get("overdue_tasks", 0)
        due_this_week = task_data.get("due_this_week", 0)
        
        if total == 0:
            return "You have no active tasks - perfect for planning ahead!"
        
        summary_parts = [f"You have {total} active tasks"]
        
        if due_today > 0:
            summary_parts.append(f"{due_today} due today")
        
        if overdue > 0:
            summary_parts.append(f"{overdue} overdue")
        
        if due_this_week > 0 and due_this_week > due_today:
            summary_parts.append(f"{due_this_week} due this week")
        
        return ", ".join(summary_parts) + "."
    
    async def aggregate_data(self, sources: list[str], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for synthesizer tool"""
        raise ToolError("Data aggregation not supported by synthesizer tool", self.name)
