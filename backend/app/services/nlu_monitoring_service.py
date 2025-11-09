"""
NLU Monitoring Service
Business logic for NLU model performance monitoring and corrections
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from app.database.repositories.integration_repositories import NLURepository, create_nlu_repository
from app.database.repositories.user_repositories import UserRepository, get_user_repository
from app.core.utils.error_handlers import ServiceError

logger = logging.getLogger(__name__)


class NLUMonitoringService:
    """
    Service layer for NLU monitoring operations
    
    Handles business logic for:
    - Performance statistics
    - Low confidence prompt analysis
    - Failed workflow analysis
    - Manual corrections
    - Training data export
    """

    def __init__(
        self,
        nlu_repo: NLURepository = None,
        user_repo: UserRepository = None
    ):
        """
        Initialize NLUMonitoringService
        
        Args:
            nlu_repo: Optional NLURepository instance (for dependency injection/testing)
            user_repo: Optional UserRepository instance (for dependency injection/testing)
        """
        self.nlu_repo = nlu_repo or create_nlu_repository()
        self.user_repo = user_repo or UserRepository()

    async def verify_admin(self, user_id: str) -> bool:
        """
        Verify user has admin role
        
        Args:
            user_id: User ID to check
        
        Returns:
            True if user is admin, False otherwise
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return False
            return user.get("role") == "admin"
        
        except Exception as e:
            logger.error(f"Failed to verify admin status for user {user_id}: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to verify admin status: {str(e)}",
                service="NLUMonitoringService",
                operation="verify_admin",
                details={"user_id": user_id}
            )

    async def get_nlu_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get NLU performance statistics
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with statistics including:
            - Total prompts (all time, today, last N days)
            - Average confidence scores
            - Low confidence count
            - Failed workflow count
            - Intent distribution
            - Confidence distribution
            - Workflow success rates
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            now = datetime.utcnow()
            days_ago = now - timedelta(days=days)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Total prompts using repository
            total_prompts = await self.nlu_repo.count_all_prompts()
            
            # Prompts today using repository
            total_prompts_today = await self.nlu_repo.count_prompts_since(today_start)
            
            # Prompts last N days using repository
            total_prompts_week = await self.nlu_repo.count_prompts_since(days_ago)
            
            # Get all prompts for calculations (last N days) using repository
            prompts = await self.nlu_repo.get_prompts_since(days_ago)
            
            # Calculate average confidence
            if prompts:
                avg_confidence = sum(p.get("confidence", 0) for p in prompts) / len(prompts)
            else:
                avg_confidence = 0.0
            
            # Prompts today for avg confidence
            prompts_today = [p for p in prompts if p.get("created_at", "") >= today_start.isoformat()]
            if prompts_today:
                avg_confidence_today = sum(p.get("confidence", 0) for p in prompts_today) / len(prompts_today)
            else:
                avg_confidence_today = 0.0
            
            # Low confidence count (< 0.7)
            low_confidence_count = len([p for p in prompts if p.get("confidence", 1.0) < 0.7])
            
            # Failed workflows
            failed_workflows = len([p for p in prompts if p.get("was_successful") is False])
            
            # Corrections count
            correction_count = len([p for p in prompts if p.get("corrected_intent")])
            
            # Intent distribution
            intent_counts: Dict[str, int] = {}
            for p in prompts:
                intent = p.get("predicted_intent", "unknown")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            intent_distribution = [
                {"intent": intent, "count": count}
                for intent, count in sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
            ]
            
            # Confidence distribution (buckets)
            confidence_buckets = {
                "0.0-0.5": 0,
                "0.5-0.7": 0,
                "0.7-0.85": 0,
                "0.85-1.0": 0
            }
            for p in prompts:
                conf = p.get("confidence", 0)
                if conf < 0.5:
                    confidence_buckets["0.0-0.5"] += 1
                elif conf < 0.7:
                    confidence_buckets["0.5-0.7"] += 1
                elif conf < 0.85:
                    confidence_buckets["0.7-0.85"] += 1
                else:
                    confidence_buckets["0.85-1.0"] += 1
            
            confidence_distribution = [
                {"bucket": bucket, "count": count}
                for bucket, count in confidence_buckets.items()
            ]
            
            # Workflow success rate by intent
            intent_success: Dict[str, Dict[str, int]] = {}
            for p in prompts:
                if p.get("was_successful") is not None:
                    intent = p.get("predicted_intent", "unknown")
                    if intent not in intent_success:
                        intent_success[intent] = {"total": 0, "success": 0}
                    intent_success[intent]["total"] += 1
                    if p.get("was_successful"):
                        intent_success[intent]["success"] += 1
            
            workflow_success_rate = {
                intent: {
                    "total": stats["total"],
                    "success": stats["success"],
                    "rate": round(100 * stats["success"] / stats["total"], 1) if stats["total"] > 0 else 0
                }
                for intent, stats in intent_success.items()
            }
            
            return {
                "total_prompts": total_prompts,
                "total_prompts_today": total_prompts_today,
                "total_prompts_week": total_prompts_week,
                "avg_confidence": round(avg_confidence, 3),
                "avg_confidence_today": round(avg_confidence_today, 3),
                "low_confidence_count": low_confidence_count,
                "failed_workflows": failed_workflows,
                "correction_count": correction_count,
                "intent_distribution": intent_distribution,
                "confidence_distribution": confidence_distribution,
                "workflow_success_rate": workflow_success_rate
            }
        
        except Exception as e:
            logger.error(f"Failed to get NLU stats: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get NLU stats: {str(e)}",
                service="NLUMonitoringService",
                operation="get_nlu_stats",
                details={"days": days}
            )

    async def get_low_confidence_prompts(
        self,
        threshold: float = 0.7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get prompts with low confidence for manual review
        
        Args:
            threshold: Confidence threshold (default: 0.7)
            limit: Maximum number of results (default: 100)
        
        Returns:
            List of low confidence prompt dictionaries
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            prompts = await self.nlu_repo.get_low_confidence_prompts(
                threshold=threshold,
                limit=limit
            )
            return prompts
        
        except Exception as e:
            logger.error(f"Failed to get low confidence prompts: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get low confidence prompts: {str(e)}",
                service="NLUMonitoringService",
                operation="get_low_confidence_prompts",
                details={"threshold": threshold, "limit": limit}
            )

    async def get_failed_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get prompts that led to failed workflows
        
        Args:
            limit: Maximum number of results (default: 100)
        
        Returns:
            List of failed workflow prompt dictionaries
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            prompts = await self.nlu_repo.get_failed_workflow_prompts(limit=limit)
            return prompts
        
        except Exception as e:
            logger.error(f"Failed to get failed workflows: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to get failed workflows: {str(e)}",
                service="NLUMonitoringService",
                operation="get_failed_workflows",
                details={"limit": limit}
            )

    async def add_correction(
        self,
        log_id: UUID,
        corrected_intent: str,
        correction_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add manual correction to a prompt log
        
        Args:
            log_id: Prompt log ID
            corrected_intent: Corrected intent
            correction_notes: Optional correction notes
        
        Returns:
            Success message dictionary
            
        Raises:
            ServiceError: If operation fails
        """
        try:
            await self.nlu_repo.add_prompt_correction(
                log_id=log_id,
                corrected_intent=corrected_intent,
                correction_notes=correction_notes
            )
            return {"success": True, "message": "Correction added"}
        
        except Exception as e:
            logger.error(f"Failed to add correction: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to add correction: {str(e)}",
                service="NLUMonitoringService",
                operation="add_correction",
                details={"log_id": str(log_id), "corrected_intent": corrected_intent}
            )

    async def export_training_data(
        self,
        mode: str = "retraining",
        days: Optional[int] = 30
    ) -> Dict[str, Any]:
        """
        Export training data for model retraining or review
        
        Args:
            mode: Export mode ("retraining" or "review")
            days: Number of days to include (None for all)
        
        Returns:
            Dict with mode, count, and data
            
        Raises:
            ServiceError: If operation fails
            ValueError: If invalid mode
        """
        try:
            # Calculate min_date
            min_date = None
            if days:
                min_date = datetime.utcnow() - timedelta(days=days)
            
            if mode == "retraining":
                # Get prompts for retraining (corrected + high confidence)
                prompts = await self.nlu_repo.get_prompts_for_retraining(
                    min_date=min_date,
                    limit=10000
                )
                
                # Convert to training format
                training_data = []
                for log in prompts:
                    label = log.get("corrected_intent") or log.get("predicted_intent")
                    prompt_text = log.get("prompt")
                    
                    if prompt_text and label:
                        training_data.append({
                            "text": prompt_text,
                            "label": label,
                            "confidence": log.get("confidence"),
                            "source": "production",
                            "corrected": bool(log.get("corrected_intent"))
                        })
                
                return {
                    "mode": "retraining",
                    "count": len(training_data),
                    "data": training_data
                }
            
            elif mode == "review":
                # Get low confidence prompts for review
                prompts = await self.nlu_repo.get_low_confidence_prompts(
                    threshold=0.7,
                    limit=100
                )
                
                review_data = [
                    {
                        "id": log.get("id"),
                        "prompt": log.get("prompt"),
                        "predicted_intent": log.get("predicted_intent"),
                        "confidence": log.get("confidence"),
                        "created_at": log.get("created_at")
                    }
                    for log in prompts
                ]
                
                return {
                    "mode": "review",
                    "count": len(review_data),
                    "data": review_data
                }
            
            else:
                raise ValueError(f"Invalid export mode: {mode}")
        
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to export training data: {e}", exc_info=True)
            raise ServiceError(
                message=f"Failed to export training data: {str(e)}",
                service="NLUMonitoringService",
                operation="export_training_data",
                details={"mode": mode, "days": days}
            )


def get_nlu_monitoring_service() -> NLUMonitoringService:
    """
    Dependency injection function for NLUMonitoringService
    
    Returns:
        NLUMonitoringService instance with default dependencies
    """
    return NLUMonitoringService(
        nlu_repo=create_nlu_repository(),
        user_repo=get_user_repository()
    )

