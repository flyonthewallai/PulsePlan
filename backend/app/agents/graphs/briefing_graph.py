"""
Daily Briefing Workflow
Implements data aggregation and content synthesis for daily briefings
Based on LANGGRAPH_AGENT_WORKFLOWS.md
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from langgraph.graph import END

from .base import BaseWorkflow, WorkflowType, WorkflowState, WorkflowError


class BriefingWorkflow(BaseWorkflow):
    """
    Daily Briefing Workflow that:
    1. Aggregates user data from multiple sources
    2. Analyzes emails, calendar, and tasks
    3. Synthesizes content into coherent briefing
    4. Generates and delivers formatted briefing
    """
    
    def __init__(self):
        super().__init__(WorkflowType.BRIEFING)
        
    def define_nodes(self) -> Dict[str, callable]:
        """Define all nodes for briefing workflow"""
        return {
            "input_validator": self.input_validator_node,
            "data_aggregator": self.data_aggregator_node,
            "policy_gate": self.policy_gate_node,
            "rate_limiter": self.rate_limiter_node,
            "email_analyzer": self.email_analyzer_node,
            "calendar_analyzer": self.calendar_analyzer_node,
            "task_analyzer": self.task_analyzer_node,
            "content_synthesizer": self.content_synthesizer_node,
            "template_generator": self.template_generator_node,
            "delivery_service": self.delivery_service_node,
            "result_processor": self.result_processor_node,
            "trace_updater": self.trace_updater_node,
            "error_handler": self.error_handler_node
        }
    
    def define_edges(self) -> List[tuple]:
        """Define edges between nodes"""
        return [
            # Initial processing
            ("input_validator", "data_aggregator"),
            ("data_aggregator", "policy_gate"),
            ("policy_gate", "rate_limiter"),
            
            # Parallel analysis (simulate with sequential for now)
            ("rate_limiter", "email_analyzer"),
            ("email_analyzer", "calendar_analyzer"),
            ("calendar_analyzer", "task_analyzer"),
            
            # Content generation
            ("task_analyzer", "content_synthesizer"),
            ("content_synthesizer", "template_generator"),
            ("template_generator", "delivery_service"),
            
            # Final processing
            ("delivery_service", "result_processor"),
            ("result_processor", "trace_updater"),
            ("trace_updater", END),
            
            # Error handling
            ("error_handler", END)
        ]
    
    async def data_aggregator_node(self, state: WorkflowState) -> WorkflowState:
        """Collect user data from multiple sources"""
        state["current_node"] = "data_aggregator"
        state["visited_nodes"].append("data_aggregator")
        
        user_id = state["user_id"]
        briefing_date = state["input_data"].get("date", datetime.utcnow().date().isoformat())
        
        # Implement actual data collection from various sources
        try:
            # Get user's connected accounts from token service
            from app.services.token_service import get_token_service
            token_service = get_token_service()
            connection_status = await token_service.get_user_connection_status(user_id)
            
            # Get user tasks from database
            from app.config.database.supabase import get_supabase
            supabase = get_supabase()
            
            # Calculate date range for the briefing
            briefing_dt = datetime.fromisoformat(briefing_date)
            start_date = briefing_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            # Collect tasks data
            tasks_response = supabase.table("tasks").select("*").eq("user_id", user_id).gte("created_at", start_date.isoformat()).lt("created_at", end_date.isoformat()).execute()
            
            # Collect calendar events data
            events_response = supabase.table("calendar_events").select("*").eq("user_id", user_id).gte("start_time", start_date.isoformat()).lt("end_time", end_date.isoformat()).execute()
            
            aggregated_data = {
                "briefing_date": briefing_date,
                "user_id": user_id,
                "data_sources": {
                    "email": {
                        "status": "connected" if (connection_status.google or connection_status.microsoft) else "disconnected",
                        "accounts": []
                    },
                    "calendar": {
                        "status": "connected" if (connection_status.google or connection_status.microsoft) else "disconnected", 
                        "providers": [],
                        "events_count": len(events_response.data)
                    },
                    "tasks": {
                        "status": "available",
                        "count": len(tasks_response.data),
                        "completed_today": len([t for t in tasks_response.data if t.get("status") == "completed"]),
                        "pending": len([t for t in tasks_response.data if t.get("status") == "pending"])
                    }
                },
                "time_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "collected_at": datetime.utcnow().isoformat()
            }
            
            # Add connected account details
            if connection_status.google:
                aggregated_data["data_sources"]["email"]["accounts"].append("gmail")
                aggregated_data["data_sources"]["calendar"]["providers"].append("google")
            if connection_status.microsoft:
                aggregated_data["data_sources"]["email"]["accounts"].append("outlook")
                aggregated_data["data_sources"]["calendar"]["providers"].append("microsoft")
                
        except Exception as e:
            logger.error(f"Error collecting briefing data: {e}")
            # Fallback to basic structure on error
            aggregated_data = {
                "briefing_date": briefing_date,
                "user_id": user_id,
                "data_sources": {
                    "email": {"status": "error", "accounts": []},
                    "calendar": {"status": "error", "providers": []},
                    "tasks": {"status": "error", "count": 0}
                },
                "time_range": {
                    "start": briefing_date,
                    "end": (datetime.fromisoformat(briefing_date) + timedelta(days=1)).date().isoformat()
                },
                "error": str(e)
            }
        
        state["input_data"]["aggregated_data"] = aggregated_data
        
        return state
    
    async def email_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze email data from connected accounts"""
        state["current_node"] = "email_analyzer"
        state["visited_nodes"].append("email_analyzer")
        
        aggregated_data = state["input_data"]["aggregated_data"]
        email_accounts = aggregated_data["data_sources"]["email"]["accounts"]
        
        # Implement actual email analysis
        email_analysis = {
            "total_emails": 0,
            "unread_emails": 0,
            "important_emails": [],
            "summary": "No email analysis available - no connected accounts.",
            "analysis_time": datetime.utcnow().isoformat()
        }
        
        try:
            if email_accounts:
                # Use the EmailManagerTool to get email data
                from app.agents.tools.email import EmailManagerTool
                email_tool = EmailManagerTool()
                
                user_id = aggregated_data["user_id"]
                time_range = aggregated_data["time_range"]
                
                # Create context for email tool
                context = {
                    "user_id": user_id,
                    "user_context": {"email": "user@example.com"}  # Would get from user profile
                }
                
                total_emails = 0
                unread_count = 0
                important_emails = []
                
                for account in email_accounts:
                    try:
                        # Get emails from each connected account
                        result = await email_tool.execute({
                            "operation": "list",
                            "query": "",
                            "limit": 50,
                            "preferred_provider": account,
                            "since": time_range["start"]
                        }, context)
                        
                        if result.success:
                            messages = result.data.get("messages", [])
                            total_emails += len(messages)
                            
                            for msg in messages:
                                if msg.get("unread", False):
                                    unread_count += 1
                                
                                # Identify important emails (could use ML in future)
                                if self._is_important_email(msg):
                                    important_emails.append({
                                        "from": msg.get("from", "Unknown"),
                                        "subject": msg.get("subject", "No Subject"),
                                        "priority": self._classify_email_priority(msg),
                                        "received": msg.get("received", ""),
                                        "provider": account
                                    })
                    
                    except Exception as e:
                        logger.warning(f"Failed to analyze emails from {account}: {e}")
                        continue
                
                # Limit important emails to top 5
                important_emails = sorted(important_emails, 
                                        key=lambda x: self._priority_score(x["priority"]), 
                                        reverse=True)[:5]
                
                # Generate summary
                summary_parts = [f"You received {total_emails} emails"]
                if unread_count > 0:
                    summary_parts.append(f"with {unread_count} unread")
                if important_emails:
                    summary_parts.append(f". {len(important_emails)} important items require attention")
                else:
                    summary_parts.append(". No urgent items identified")
                
                email_analysis = {
                    "total_emails": total_emails,
                    "unread_emails": unread_count,
                    "important_emails": important_emails,
                    "summary": "".join(summary_parts) + ".",
                    "analysis_time": datetime.utcnow().isoformat(),
                    "accounts_analyzed": email_accounts
                }
                
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            email_analysis["error"] = str(e)
            email_analysis["summary"] = f"Email analysis failed: {str(e)}"
        
        state["input_data"]["email_analysis"] = email_analysis
        aggregated_data["data_sources"]["email"]["status"] = "completed"
        
        return state
    
    async def calendar_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze calendar events for the briefing period"""
        state["current_node"] = "calendar_analyzer"
        state["visited_nodes"].append("calendar_analyzer")
        
        aggregated_data = state["input_data"]["aggregated_data"]
        calendar_providers = aggregated_data["data_sources"]["calendar"]["providers"]
        
        # Implement actual calendar analysis
        calendar_analysis = {
            "total_events": 0,
            "today_events": [],
            "upcoming_events": [],
            "free_time_blocks": [],
            "summary": "No calendar analysis available - no connected accounts.",
            "analysis_time": datetime.utcnow().isoformat()
        }
        
        try:
            if calendar_providers:
                # Use the CalendarTool to get calendar data
                from app.agents.tools.calendar import CalendarTool
                calendar_tool = CalendarTool()
                
                user_id = aggregated_data["user_id"]
                time_range = aggregated_data["time_range"]
                
                # Create context for calendar tool
                context = {
                    "user_id": user_id,
                    "user_context": {"email": "user@example.com"}
                }
                
                all_events = []
                
                for provider in calendar_providers:
                    try:
                        # Get events from each connected provider
                        result = await calendar_tool.execute({
                            "operation": "list_events",
                            "start_date": time_range["start"],
                            "end_date": time_range["end"],
                            "preferred_provider": provider
                        }, context)
                        
                        if result.success:
                            events = result.data.get("events", [])
                            all_events.extend(events)
                            
                    except Exception as e:
                        logger.warning(f"Failed to get calendar events from {provider}: {e}")
                        continue
                
                # Process events
                today_events = []
                upcoming_events = []
                briefing_dt = datetime.fromisoformat(aggregated_data["briefing_date"])
                today_start = briefing_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                for event in all_events:
                    event_start = datetime.fromisoformat(event["start"].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event["end"].replace('Z', '+00:00'))
                    
                    if today_start <= event_start < today_end:
                        today_events.append({
                            "title": event["title"],
                            "time": f"{event_start.strftime('%H:%M')}-{event_end.strftime('%H:%M')}",
                            "type": self._classify_event_type(event),
                            "location": event.get("location", ""),
                            "provider": event.get("provider", "unknown")
                        })
                    elif event_start >= today_end and event_start < today_end + timedelta(days=7):
                        upcoming_events.append({
                            "title": event["title"],
                            "time": f"{event_start.strftime('%a %H:%M')}-{event_end.strftime('%H:%M')}",
                            "type": self._classify_event_type(event),
                            "date": event_start.date().isoformat()
                        })
                
                # Calculate free time blocks (simplified)
                free_time_blocks = self._calculate_free_time(today_events, today_start, today_end)
                
                # Generate summary
                summary_parts = []
                if today_events:
                    summary_parts.append(f"You have {len(today_events)} events today")
                    important_events = [e for e in today_events if e["type"] in ["meeting", "presentation"]]
                    if important_events:
                        summary_parts.append(f" including {len(important_events)} meetings")
                else:
                    summary_parts.append("You have no scheduled events today")
                    
                if upcoming_events:
                    next_event = upcoming_events[0]
                    summary_parts.append(f". Next event: {next_event['title']} on {next_event['time']}")
                
                if free_time_blocks:
                    summary_parts.append(f". {len(free_time_blocks)} free time blocks available")
                
                calendar_analysis = {
                    "total_events": len(all_events),
                    "today_events": sorted(today_events, key=lambda x: x["time"]),
                    "upcoming_events": upcoming_events[:5],  # Limit to next 5
                    "free_time_blocks": free_time_blocks,
                    "summary": "".join(summary_parts) + ".",
                    "analysis_time": datetime.utcnow().isoformat(),
                    "providers_analyzed": calendar_providers
                }
                
        except Exception as e:
            logger.error(f"Calendar analysis failed: {e}")
            calendar_analysis["error"] = str(e)
            calendar_analysis["summary"] = f"Calendar analysis failed: {str(e)}"
        
        state["input_data"]["calendar_analysis"] = calendar_analysis
        aggregated_data["data_sources"]["calendar"]["status"] = "completed"
        
        return state
    
    def task_analyzer_node(self, state: WorkflowState) -> WorkflowState:
        """Analyze pending tasks and priorities"""
        state["current_node"] = "task_analyzer"
        state["visited_nodes"].append("task_analyzer")
        
        # TODO: Implement actual task analysis
        # For now, mock task analysis
        task_analysis = {
            "total_tasks": 8,
            "overdue_tasks": 1,
            "due_today": 2,
            "due_this_week": 3,
            "high_priority_tasks": [
                {
                    "title": "Complete project proposal",
                    "due": "Today",
                    "priority": "high"
                },
                {
                    "title": "Review client feedback",
                    "due": "Tomorrow",
                    "priority": "high"
                }
            ],
            "completed_yesterday": 3,
            "summary": "You have 8 active tasks with 2 due today. Great job completing 3 tasks yesterday!"
        }
        
        state["input_data"]["task_analysis"] = task_analysis
        
        aggregated_data = state["input_data"]["aggregated_data"]
        aggregated_data["data_sources"]["tasks"]["status"] = "completed"
        aggregated_data["data_sources"]["tasks"]["count"] = task_analysis["total_tasks"]
        
        return state
    
    def content_synthesizer_node(self, state: WorkflowState) -> WorkflowState:
        """Synthesize all analysis into coherent briefing content"""
        state["current_node"] = "content_synthesizer"
        state["visited_nodes"].append("content_synthesizer")
        
        email_analysis = state["input_data"]["email_analysis"]
        calendar_analysis = state["input_data"]["calendar_analysis"]
        task_analysis = state["input_data"]["task_analysis"]
        
        # TODO: Use LLM to synthesize content intelligently
        # For now, create structured briefing content
        briefing_content = {
            "greeting": f"Good morning! Here's your briefing for {state['input_data']['aggregated_data']['briefing_date']}",
            "email_summary": email_analysis["summary"],
            "calendar_overview": calendar_analysis["summary"],
            "task_status": task_analysis["summary"],
            "priority_items": [
                "Complete project proposal (due today)",
                "Prepare for client presentation at 2 PM",
                "Review 5 unread emails"
            ],
            "recommendations": [
                "Block time between 10-12 PM for focused work on the project proposal",
                "Prep 30 minutes before client presentation",
                "Consider rescheduling tomorrow's project review if proposal runs late"
            ]
        }
        
        state["input_data"]["briefing_content"] = briefing_content
        
        return state
    
    def template_generator_node(self, state: WorkflowState) -> WorkflowState:
        """Generate formatted briefing using templates"""
        state["current_node"] = "template_generator"
        state["visited_nodes"].append("template_generator")
        
        briefing_content = state["input_data"]["briefing_content"]
        
        # TODO: Implement templating system (Jinja2, etc.)
        # For now, create simple formatted text
        formatted_briefing = self._format_briefing_text(briefing_content)
        
        state["output_data"] = {
            "briefing": {
                "formatted_text": formatted_briefing,
                "content_sections": briefing_content,
                "format": "text",  # TODO: Support HTML, markdown
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        return state
    
    def delivery_service_node(self, state: WorkflowState) -> WorkflowState:
        """Deliver briefing via configured channels"""
        state["current_node"] = "delivery_service"
        state["visited_nodes"].append("delivery_service")
        
        delivery_method = state["input_data"].get("delivery_method", "api")
        
        # TODO: Implement actual delivery (email, push notification, etc.)
        # For now, just track delivery
        delivery_info = {
            "method": delivery_method,
            "delivered_at": datetime.utcnow().isoformat(),
            "user_id": state["user_id"],
            "status": "delivered"
        }
        
        if delivery_method == "email":
            delivery_info["email_sent"] = True
        elif delivery_method == "notification":
            delivery_info["notification_sent"] = True
        
        state["metrics"]["delivery"] = delivery_info
        
        return state
    
    def _format_briefing_text(self, content: Dict[str, Any]) -> str:
        """Format briefing content as readable text"""
        lines = [
            content["greeting"],
            "",
            "EMAIL SUMMARY",
            content["email_summary"],
            "",
            "CALENDAR OVERVIEW", 
            content["calendar_overview"],
            "",
            "TASK STATUS",
            content["task_status"],
            "",
            "PRIORITY ITEMS",
        ]
        
        for item in content["priority_items"]:
            lines.append(f"• {item}")
        
        lines.extend([
            "",
            "RECOMMENDATIONS",
        ])
        
        for rec in content["recommendations"]:
            lines.append(f"• {rec}")
        
        lines.extend([
            "",
            "Have a productive day!"
        ])
        
        return "\n".join(lines)
    
    def _is_important_email(self, msg: Dict[str, Any]) -> bool:
        """Determine if an email is important based on various factors"""
        # Simple heuristics - could be enhanced with ML
        subject = msg.get("subject", "").lower()
        sender = msg.get("from", "").lower()
        
        # Important keywords in subject
        important_keywords = ["urgent", "asap", "deadline", "important", "action required", 
                            "meeting", "reschedule", "cancelled", "approval", "review"]
        
        # Check for important keywords
        if any(keyword in subject for keyword in important_keywords):
            return True
            
        # Check if from important senders (manager, clients, etc.)
        # This could be personalized based on user's contacts/preferences
        important_senders = ["manager", "boss", "ceo", "client", "customer"]
        if any(sender_type in sender for sender_type in important_senders):
            return True
            
        # Check if unread and recent
        if msg.get("unread", False):
            return True
            
        return False
    
    def _classify_email_priority(self, msg: Dict[str, Any]) -> str:
        """Classify email priority level"""
        subject = msg.get("subject", "").lower()
        
        if any(word in subject for word in ["urgent", "asap", "emergency"]):
            return "high"
        elif any(word in subject for word in ["important", "deadline", "action required"]):
            return "medium"
        else:
            return "low"
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting"""
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 0)
    
    def _classify_event_type(self, event: Dict[str, Any]) -> str:
        """Classify calendar event type"""
        title = event.get("title", "").lower()
        
        if any(word in title for word in ["meeting", "call", "standup", "sync"]):
            return "meeting"
        elif any(word in title for word in ["presentation", "demo", "review"]):
            return "presentation"  
        elif any(word in title for word in ["lunch", "dinner", "coffee"]):
            return "meal"
        elif any(word in title for word in ["travel", "flight", "commute"]):
            return "travel"
        else:
            return "event"
    
    def _calculate_free_time(self, today_events: list, today_start: datetime, today_end: datetime) -> list:
        """Calculate free time blocks between events"""
        if not today_events:
            return ["09:00-17:00"]  # Default working hours if no events
        
        # Sort events by start time
        sorted_events = sorted(today_events, key=lambda x: x["time"].split("-")[0])
        
        free_blocks = []
        current_time = today_start.replace(hour=9, minute=0)  # Start at 9 AM
        end_of_day = today_start.replace(hour=17, minute=0)   # End at 5 PM
        
        for event in sorted_events:
            event_start_str = event["time"].split("-")[0]
            event_end_str = event["time"].split("-")[1]
            
            try:
                event_start_time = datetime.strptime(event_start_str, "%H:%M").time()
                event_end_time = datetime.strptime(event_end_str, "%H:%M").time()
                
                event_start = today_start.replace(hour=event_start_time.hour, minute=event_start_time.minute)
                event_end = today_start.replace(hour=event_end_time.hour, minute=event_end_time.minute)
                
                # If there's a gap before this event
                if current_time < event_start:
                    gap_duration = event_start - current_time
                    if gap_duration.total_seconds() >= 30 * 60:  # At least 30 minutes
                        free_blocks.append(f"{current_time.strftime('%H:%M')}-{event_start.strftime('%H:%M')}")
                
                current_time = max(current_time, event_end)
                
            except ValueError:
                continue
        
        # Check for time after last event
        if current_time < end_of_day:
            gap_duration = end_of_day - current_time
            if gap_duration.total_seconds() >= 30 * 60:  # At least 30 minutes
                free_blocks.append(f"{current_time.strftime('%H:%M')}-{end_of_day.strftime('%H:%M')}")
        
        return free_blocks
