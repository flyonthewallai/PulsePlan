"""
Weekly pulse generation and analysis tools for PulsePlan agents.
Handles weekly productivity analytics and insights generation.
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base import BriefingTool, ToolResult, ToolError


class WeeklyPulseTool(BriefingTool):
    """Tool for generating weekly productivity pulse"""
    
    def __init__(self):
        super().__init__(
            name="weekly_pulse_generator",
            description="Generates weekly productivity pulse with analytics and insights"
        )
    
    def get_required_tokens(self) -> List[str]:
        return ["google", "microsoft"]  # For calendar and email data
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate weekly pulse input"""
        user_id = input_data.get("user_id")
        return bool(user_id)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute weekly pulse generation"""
        start_time = datetime.utcnow()
        
        try:
            if not self.validate_input(input_data):
                raise ToolError("Invalid input data - user_id required", self.name)
            
            user_id = input_data["user_id"]
            week_offset = input_data.get("week_offset", 0)  # 0 = current week, -1 = last week
            
            # Generate weekly pulse data
            pulse_data = await self._generate_weekly_pulse(user_id, week_offset, context)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result = ToolResult(
                success=True,
                data=pulse_data,
                execution_time=execution_time,
                metadata={"operation": "weekly_pulse", "week_offset": week_offset}
            )
            
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
    
    async def _generate_weekly_pulse(
        self, 
        user_id: str, 
        week_offset: int, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive weekly pulse data"""
        
        # Calculate week boundaries
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
        week_end = week_start + timedelta(days=6)
        
        # Gather data from multiple sources
        task_analytics = await self._analyze_task_completion(user_id, week_start, week_end)
        calendar_analytics = await self._analyze_calendar_productivity(user_id, week_start, week_end, context)
        productivity_score = await self._calculate_productivity_score(task_analytics, calendar_analytics)
        achievements = await self._identify_achievements(user_id, task_analytics, calendar_analytics)
        recommendations = await self._generate_recommendations(user_id, task_analytics, calendar_analytics)
        
        return {
            "completed_tasks": task_analytics["completed_count"],
            "total_tasks": task_analytics["total_count"],
            "productivity_score": productivity_score,
            "weekly_goals": task_analytics.get("goals_progress", []),
            "achievements": achievements,
            "next_week_recommendations": recommendations,
            "weekly_stats": {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "task_analytics": task_analytics,
                "calendar_analytics": calendar_analytics,
                "trends": await self._analyze_trends(user_id, week_offset)
            },
            "generated_at": datetime.utcnow()
        }
    
    async def _analyze_task_completion(
        self, 
        user_id: str, 
        week_start: datetime.date, 
        week_end: datetime.date
    ) -> Dict[str, Any]:
        """Analyze task completion for the week"""
        # In a real implementation, this would query the database
        # For now, returning mock analytics
        
        return {
            "completed_count": 12,
            "total_count": 15,
            "completion_rate": 0.8,
            "overdue_count": 1,
            "subjects": {
                "work": {"completed": 8, "total": 10},
                "personal": {"completed": 4, "total": 5}
            },
            "daily_breakdown": [
                {"day": "Monday", "completed": 3, "total": 4},
                {"day": "Tuesday", "completed": 2, "total": 2},
                {"day": "Wednesday", "completed": 2, "total": 3},
                {"day": "Thursday", "completed": 3, "total": 3},
                {"day": "Friday", "completed": 2, "total": 3}
            ],
            "goals_progress": [
                {"goal": "Complete project milestone", "progress": 85},
                {"goal": "Read 2 chapters", "progress": 100}
            ]
        }
    
    async def _analyze_calendar_productivity(
        self, 
        user_id: str, 
        week_start: datetime.date, 
        week_end: datetime.date,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze calendar and meeting productivity"""
        connected_accounts = context.get("connected_accounts", {})
        
        # Mock calendar analytics - in real implementation would use calendar APIs
        return {
            "total_meetings": 8,
            "meeting_hours": 6.5,
            "focus_time_hours": 25.5,
            "meeting_efficiency_score": 7.2,
            "calendar_providers": list(connected_accounts.keys()),
            "time_distribution": {
                "meetings": 6.5,
                "focused_work": 25.5,
                "admin_tasks": 3.0,
                "breaks": 5.0
            },
            "most_productive_day": "Wednesday",
            "meeting_feedback": "Good balance of meetings vs. focus time"
        }
    
    async def _calculate_productivity_score(
        self, 
        task_analytics: Dict[str, Any], 
        calendar_analytics: Dict[str, Any]
    ) -> float:
        """Calculate overall productivity score for the week"""
        
        # Weight different factors
        task_completion_weight = 0.4
        calendar_efficiency_weight = 0.3
        consistency_weight = 0.2
        goal_progress_weight = 0.1
        
        # Task completion score (0-10)
        task_score = (task_analytics["completion_rate"] * 10)
        
        # Calendar efficiency score
        calendar_score = calendar_analytics.get("meeting_efficiency_score", 7.0)
        
        # Consistency score (based on daily breakdown variance)
        daily_rates = []
        for day in task_analytics.get("daily_breakdown", []):
            if day["total"] > 0:
                daily_rates.append(day["completed"] / day["total"])
        
        consistency_score = 8.0  # Mock score
        if daily_rates:
            variance = sum((rate - sum(daily_rates)/len(daily_rates))**2 for rate in daily_rates) / len(daily_rates)
            consistency_score = max(0, 10 - (variance * 20))  # Lower variance = higher score
        
        # Goal progress score
        goal_scores = [goal["progress"]/10 for goal in task_analytics.get("goals_progress", [])]
        goal_score = sum(goal_scores) / len(goal_scores) if goal_scores else 7.0
        
        # Calculate weighted average
        productivity_score = (
            task_score * task_completion_weight +
            calendar_score * calendar_efficiency_weight +
            consistency_score * consistency_weight +
            goal_score * goal_progress_weight
        )
        
        return round(min(10.0, max(0.0, productivity_score)), 1)
    
    async def _identify_achievements(
        self, 
        user_id: str, 
        task_analytics: Dict[str, Any], 
        calendar_analytics: Dict[str, Any]
    ) -> List[str]:
        """Identify notable achievements for the week"""
        achievements = []
        
        # Task completion achievements
        completion_rate = task_analytics.get("completion_rate", 0)
        if completion_rate >= 0.9:
            achievements.append("Achieved 90%+ task completion rate!")
        elif completion_rate >= 0.8:
            achievements.append("Strong task completion with 80%+ rate")
        
        # Consistency achievements
        daily_breakdown = task_analytics.get("daily_breakdown", [])
        if len([day for day in daily_breakdown if day["completed"] == day["total"]]) >= 3:
            achievements.append("Perfect completion on 3+ days")
        
        # Focus time achievements  
        focus_hours = calendar_analytics.get("focus_time_hours", 0)
        if focus_hours >= 25:
            achievements.append("Maintained excellent focus time (25+ hours)")
        
        # Goal achievements
        completed_goals = [g for g in task_analytics.get("goals_progress", []) if g["progress"] >= 100]
        if completed_goals:
            achievements.append(f"Completed {len(completed_goals)} weekly goal(s)")
        
        # Meeting efficiency
        efficiency_score = calendar_analytics.get("meeting_efficiency_score", 0)
        if efficiency_score >= 8.0:
            achievements.append("Maintained highly efficient meetings")
        
        # Fallback if no specific achievements
        if not achievements:
            achievements.append("Stayed consistent with your productivity habits")
        
        return achievements
    
    async def _generate_recommendations(
        self, 
        user_id: str, 
        task_analytics: Dict[str, Any], 
        calendar_analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate personalized recommendations for next week"""
        recommendations = []
        
        # Task-based recommendations
        completion_rate = task_analytics.get("completion_rate", 0)
        if completion_rate < 0.7:
            recommendations.append("Consider breaking large tasks into smaller, manageable chunks")
            recommendations.append("Review task priorities and focus on high-impact items first")
        
        overdue_count = task_analytics.get("overdue_count", 0)
        if overdue_count > 0:
            recommendations.append("Address overdue tasks early in the week to prevent backlog")
        
        # Calendar-based recommendations
        meeting_hours = calendar_analytics.get("meeting_hours", 0)
        focus_hours = calendar_analytics.get("focus_time_hours", 0)
        
        if meeting_hours > focus_hours:
            recommendations.append("Try to block more time for focused deep work")
            recommendations.append("Consider consolidating meetings to create larger focus blocks")
        
        # Subject balance recommendations
        subjects = task_analytics.get("subjects", {})
        if len(subjects) > 1:
            subject_rates = {name: data["completed"]/data["total"] if data["total"] > 0 else 0 
                           for name, data in subjects.items()}
            worst_subject = min(subject_rates.keys(), key=lambda k: subject_rates[k])
            if subject_rates[worst_subject] < 0.7:
                recommendations.append(f"Focus extra attention on {worst_subject} tasks")
        
        # Consistency recommendations
        daily_breakdown = task_analytics.get("daily_breakdown", [])
        if daily_breakdown:
            worst_days = [day for day in daily_breakdown 
                         if day["total"] > 0 and day["completed"]/day["total"] < 0.6]
            if worst_days:
                recommendations.append("Plan lighter workloads on typically challenging days")
        
        # General recommendations
        recommendations.append("Set 2-3 key priorities for the week ahead")
        recommendations.append("Review and update your weekly goals")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def _analyze_trends(self, user_id: str, week_offset: int) -> Dict[str, Any]:
        """Analyze productivity trends over time"""
        # Mock trend analysis - would compare with previous weeks in real implementation
        return {
            "completion_rate_trend": "+5%",
            "productivity_score_trend": "+0.3",
            "focus_time_trend": "+2.5 hours",
            "streak_days": 12,
            "improvement_areas": ["Meeting efficiency", "Task estimation"]
        }
    
    async def aggregate_data(self, sources: List[str], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for weekly pulse tool"""
        raise ToolError("Data aggregation not supported by weekly pulse tool", self.name)
    
    async def synthesize_content(self, data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Not implemented for weekly pulse tool"""
        raise ToolError("Content synthesis not supported by weekly pulse tool", self.name)