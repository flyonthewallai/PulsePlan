"""
Weekly profile snapshot system for capturing behavioral patterns and preferences.
Analyzes user behavior to create insights for scheduling and task planning.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .vector_memory import get_vector_memory_service, VectorMemoryService
from .ingestion import get_ingestion_service, IngestionService
from .types import WeeklyProfileSnapshot, VecMemoryCreate

logger = logging.getLogger(__name__)

@dataclass
class BehaviorMetrics:
    """Metrics extracted from user behavior analysis"""
    on_time_completion_rate: float
    average_study_block_minutes: int
    preferred_start_time: str
    preferred_days: List[str]
    total_study_minutes: int
    tasks_completed: int
    tasks_planned: int
    productivity_score: float
    consistency_score: float
    procrastination_tendency: float

class WeeklyProfileService:
    """Service for creating and managing weekly behavioral profile snapshots"""
    
    def __init__(
        self,
        vector_service: Optional[VectorMemoryService] = None,
        ingestion_service: Optional[IngestionService] = None
    ):
        self.vector_service = vector_service or get_vector_memory_service()
        self.ingestion_service = ingestion_service or get_ingestion_service()
    
    async def generate_weekly_snapshot(
        self,
        user_id: str,
        week_start_date: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a weekly profile snapshot from user telemetry data.
        
        Args:
            user_id: User identifier
            week_start_date: ISO date string for week start (defaults to last Monday)
            
        Returns:
            Memory ID of created snapshot, or None if failed
        """
        try:
            # Calculate week boundaries
            if not week_start_date:
                week_start = self._get_last_monday()
            else:
                week_start = datetime.fromisoformat(week_start_date).date()
            
            week_end = week_start + timedelta(days=6)
            
            logger.info(f"Generating weekly snapshot for user {user_id}, week {week_start}")
            
            # Analyze user behavior for the week
            metrics = await self._analyze_weekly_behavior(user_id, week_start, week_end)
            
            if not metrics:
                logger.warning(f"No behavior data found for user {user_id} in week {week_start}")
                return None
            
            # Create snapshot object
            snapshot = WeeklyProfileSnapshot(
                user_id=user_id,
                week_start=week_start.isoformat(),
                on_time_rate=metrics.on_time_completion_rate,
                avg_study_block_min=metrics.average_study_block_minutes,
                preferred_start_local=metrics.preferred_start_time,
                preferred_days=metrics.preferred_days,
                total_study_minutes=metrics.total_study_minutes,
                tasks_completed=metrics.tasks_completed,
                tasks_planned=metrics.tasks_planned
            )
            
            # Ingest into vector memory
            memory_id = await self.ingestion_service.ingest_weekly_snapshot(snapshot)
            
            if memory_id:
                logger.info(f"Created weekly snapshot {memory_id} for user {user_id}")
                return memory_id
            else:
                logger.error(f"Failed to store weekly snapshot for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate weekly snapshot: {e}")
            return None
    
    async def _analyze_weekly_behavior(
        self,
        user_id: str,
        week_start: datetime.date,
        week_end: datetime.date
    ) -> Optional[BehaviorMetrics]:
        """
        Analyze user behavior from database tables to extract behavioral metrics.
        
        Note: This implementation uses placeholder queries. In production,
        integrate with your actual telemetry/analytics tables.
        """
        try:
            # This is a placeholder implementation
            # In production, query actual user behavior data from tables like:
            # - time_sessions
            # - tasks (with completed_at timestamps)
            # - schedule_blocks
            # - daily_analytics
            
            # Placeholder metrics - replace with actual database queries
            metrics = await self._get_placeholder_metrics(user_id, week_start, week_end)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze weekly behavior: {e}")
            return None
    
    async def _get_placeholder_metrics(
        self,
        user_id: str,
        week_start: datetime.date,
        week_end: datetime.date
    ) -> BehaviorMetrics:
        """
        Generate placeholder metrics for demonstration.
        Replace with actual database queries in production.
        """
        # Simulate analysis of user data
        import random
        
        # Generate realistic but placeholder metrics
        on_time_rate = random.uniform(0.6, 0.9)
        avg_block_minutes = random.choice([25, 30, 45, 50, 90])
        
        # Preferred start times based on common patterns
        start_times = ["08:00", "09:00", "09:30", "10:00", "14:00", "19:00"]
        preferred_start = random.choice(start_times)
        
        # Preferred days (weekdays more likely)
        all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekdays = all_days[:5]
        preferred_days = random.sample(weekdays, random.randint(3, 5))
        
        # Study metrics
        total_minutes = random.randint(300, 1200)  # 5-20 hours per week
        tasks_planned = random.randint(8, 20)
        tasks_completed = int(tasks_planned * on_time_rate)
        
        # Derived metrics
        productivity_score = on_time_rate * 0.7 + random.uniform(0.1, 0.3)
        consistency_score = random.uniform(0.5, 0.9)
        procrastination_tendency = 1.0 - on_time_rate
        
        return BehaviorMetrics(
            on_time_completion_rate=on_time_rate,
            average_study_block_minutes=avg_block_minutes,
            preferred_start_time=preferred_start,
            preferred_days=preferred_days,
            total_study_minutes=total_minutes,
            tasks_completed=tasks_completed,
            tasks_planned=tasks_planned,
            productivity_score=productivity_score,
            consistency_score=consistency_score,
            procrastination_tendency=procrastination_tendency
        )
    
    def _get_last_monday(self) -> datetime.date:
        """Get the date of the most recent Monday"""
        today = datetime.utcnow().date()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday)
        return last_monday
    
    async def get_recent_snapshots(
        self,
        user_id: str,
        weeks_back: int = 4
    ) -> List[Dict[str, Any]]:
        """Get recent weekly snapshots for a user"""
        try:
            from .types import SearchOptions
            
            # Search for profile snapshots
            search_options = SearchOptions(
                user_id=user_id,
                namespaces=["profile_snapshot"],
                query="weekly study profile behavior",
                limit=weeks_back * 2  # Buffer for multiple snapshots
            )
            
            results = await self.vector_service.search_memory(search_options)
            
            # Filter and sort by date
            snapshots = []
            cutoff_date = datetime.utcnow() - timedelta(weeks=weeks_back)
            
            for result in results:
                if result.created_at >= cutoff_date:
                    snapshots.append({
                        "id": result.id,
                        "doc_id": result.doc_id,
                        "week_start": result.metadata.get("week_start"),
                        "summary": result.summary,
                        "metadata": result.metadata,
                        "created_at": result.created_at.isoformat()
                    })
            
            # Sort by week_start (most recent first)
            snapshots.sort(key=lambda x: x.get("week_start", ""), reverse=True)
            
            return snapshots[:weeks_back]
            
        except Exception as e:
            logger.error(f"Failed to get recent snapshots: {e}")
            return []
    
    async def compare_snapshots(
        self,
        user_id: str,
        snapshot1_id: str,
        snapshot2_id: str
    ) -> Optional[Dict[str, Any]]:
        """Compare two weekly snapshots to show behavior changes"""
        try:
            # Get both snapshots
            snapshot1 = await self.vector_service.get_memory_by_id(snapshot1_id, user_id)
            snapshot2 = await self.vector_service.get_memory_by_id(snapshot2_id, user_id)
            
            if not snapshot1 or not snapshot2:
                logger.error("Could not retrieve one or both snapshots for comparison")
                return None
            
            # Extract metrics from metadata
            metrics1 = snapshot1.metadata
            metrics2 = snapshot2.metadata
            
            # Calculate changes
            comparison = {
                "snapshot1": {
                    "id": snapshot1_id,
                    "week_start": metrics1.get("week_start"),
                    "metrics": metrics1
                },
                "snapshot2": {
                    "id": snapshot2_id,
                    "week_start": metrics2.get("week_start"),
                    "metrics": metrics2
                },
                "changes": {}
            }
            
            # Compare key metrics
            numeric_fields = [
                "on_time_rate", "avg_study_block_min", "total_study_minutes",
                "tasks_completed", "tasks_planned"
            ]
            
            for field in numeric_fields:
                val1 = metrics1.get(field, 0)
                val2 = metrics2.get(field, 0)
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    change = val2 - val1
                    change_percent = (change / val1 * 100) if val1 != 0 else 0
                    
                    comparison["changes"][field] = {
                        "absolute_change": change,
                        "percent_change": round(change_percent, 1),
                        "trend": "improving" if change > 0 else "declining" if change < 0 else "stable"
                    }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare snapshots: {e}")
            return None
    
    async def generate_behavior_insights(
        self,
        user_id: str,
        weeks_back: int = 4
    ) -> Dict[str, Any]:
        """Generate insights about user behavior patterns"""
        try:
            snapshots = await self.get_recent_snapshots(user_id, weeks_back)
            
            if len(snapshots) < 2:
                return {
                    "insights": ["Not enough data to generate behavioral insights"],
                    "recommendations": ["Continue using the system to build behavioral data"]
                }
            
            insights = []
            recommendations = []
            
            # Analyze trends
            on_time_rates = []
            study_minutes = []
            
            for snapshot in snapshots:
                metadata = snapshot.get("metadata", {})
                if "on_time_rate" in metadata:
                    on_time_rates.append(metadata["on_time_rate"])
                if "total_study_minutes" in metadata:
                    study_minutes.append(metadata["total_study_minutes"])
            
            # On-time completion trend
            if len(on_time_rates) >= 2:
                recent_avg = sum(on_time_rates[:2]) / 2
                older_avg = sum(on_time_rates[2:]) / len(on_time_rates[2:]) if len(on_time_rates) > 2 else recent_avg
                
                if recent_avg > older_avg + 0.1:
                    insights.append("Your on-time completion rate is improving")
                elif recent_avg < older_avg - 0.1:
                    insights.append("Your on-time completion rate has declined recently")
                    recommendations.append("Consider breaking tasks into smaller chunks or adjusting deadlines")
            
            # Study volume trend
            if len(study_minutes) >= 2:
                recent_avg = sum(study_minutes[:2]) / 2
                older_avg = sum(study_minutes[2:]) / len(study_minutes[2:]) if len(study_minutes) > 2 else recent_avg
                
                if recent_avg > older_avg * 1.1:
                    insights.append("Your study volume has increased recently")
                elif recent_avg < older_avg * 0.9:
                    insights.append("Your study volume has decreased recently")
                    recommendations.append("Consider scheduling more focused study blocks")
            
            # Extract common patterns
            preferred_days_counts = {}
            preferred_times = []
            
            for snapshot in snapshots:
                metadata = snapshot.get("metadata", {})
                
                # Count preferred days
                if "preferred_days" in metadata:
                    for day in metadata["preferred_days"]:
                        preferred_days_counts[day] = preferred_days_counts.get(day, 0) + 1
                
                # Collect preferred times
                if "preferred_start_local" in metadata:
                    preferred_times.append(metadata["preferred_start_local"])
            
            # Most common preferred days
            if preferred_days_counts:
                most_common_day = max(preferred_days_counts, key=preferred_days_counts.get)
                insights.append(f"You consistently prefer studying on {most_common_day}")
            
            # Most common preferred times
            if preferred_times:
                most_common_time = max(set(preferred_times), key=preferred_times.count)
                insights.append(f"You typically prefer starting study sessions around {most_common_time}")
            
            return {
                "insights": insights,
                "recommendations": recommendations,
                "data_points": len(snapshots),
                "analysis_period_weeks": weeks_back
            }
            
        except Exception as e:
            logger.error(f"Failed to generate behavior insights: {e}")
            return {
                "insights": ["Error analyzing behavioral patterns"],
                "recommendations": [],
                "error": str(e)
            }
    
    async def schedule_weekly_snapshot_generation(self, user_id: str) -> bool:
        """
        Schedule automatic generation of weekly snapshots.
        This would typically be called by a background job scheduler.
        """
        try:
            # Generate snapshot for the completed week
            memory_id = await self.generate_weekly_snapshot(user_id)
            
            if memory_id:
                logger.info(f"Scheduled weekly snapshot generated for user {user_id}: {memory_id}")
                return True
            else:
                logger.warning(f"Failed to generate scheduled snapshot for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to schedule weekly snapshot generation: {e}")
            return False

# Global profile service instance
weekly_profile_service = WeeklyProfileService()

def get_weekly_profile_service() -> WeeklyProfileService:
    """Get the global weekly profile service instance"""
    return weekly_profile_service