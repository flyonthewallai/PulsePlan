"""
Entity Matching API Endpoints
Preview and test entity matching for focus sessions
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel, Field
import logging

from app.core.auth import get_current_user, CurrentUser
from app.services.focus.entity_matcher import get_entity_matcher

logger = logging.getLogger(__name__)

router = APIRouter()


class EntityMatchRequest(BaseModel):
    """Request to match an entity"""
    input_text: str = Field(..., description="Natural language input to match")
    duration_minutes: Optional[int] = Field(None, description="Optional duration hint")
    
    class Config:
        schema_extra = {
            "example": {
                "input_text": "Study for my biology exam for 45 minutes",
                "duration_minutes": 45
            }
        }


@router.post("/match", response_model=dict)
async def match_entity(
    request: EntityMatchRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Preview entity matching without creating a session
    
    **Use this to:**
    - Test matching before starting session
    - Show user what entity will be linked
    - Provide autocomplete suggestions
    
    **Returns:**
    - `entity_type`: task, todo, exam, timeblock, or null
    - `entity_id`: UUID of matched entity
    - `entity`: Full entity data
    - `confidence`: Match confidence (0.0-1.0)
    - `auto_created`: Whether entity was auto-created
    - `match_reason`: Why this match was selected
    """
    try:
        logger.info(f"Matching entity for user {current_user.user_id}: '{request.input_text}'")
        
        entity_matcher = get_entity_matcher()
        result = await entity_matcher.match_entity(
            user_id=current_user.user_id,
            input_text=request.input_text,
            duration_minutes=request.duration_minutes
        )
        
        return {
            "success": True,
            "match": result
        }
        
    except Exception as e:
        logger.error(f"Error matching entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to match entity: {str(e)}")


@router.get("/suggestions", response_model=dict)
async def get_entity_suggestions(
    query: Optional[str] = None,
    limit: int = 10,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get entity suggestions for autocomplete
    
    **Returns top entities matching query:**
    - Recent tasks
    - Upcoming exams/assignments
    - Active todos
    - Recent timeblocks
    """
    try:
        entity_matcher = get_entity_matcher()
        supabase = entity_matcher.supabase
        
        suggestions = []
        
        # Get recent/upcoming tasks
        tasks_query = supabase.table("tasks")\
            .select("id, title, task_type, course, due_date")\
            .eq("user_id", current_user.user_id)\
            .neq("status", "completed")\
            .order("updated_at", desc=True)\
            .limit(limit)
        
        if query:
            tasks_query = tasks_query.ilike("title", f"%{query}%")
        
        tasks_response = tasks_query.execute()
        
        for task in (tasks_response.data or []):
            suggestions.append({
                "type": "task",
                "id": task['id'],
                "title": task['title'],
                "subtitle": task.get('course') or task.get('task_type'),
                "due_date": task.get('due_date')
            })
        
        # Get active todos
        if len(suggestions) < limit:
            todos_query = supabase.table("todos")\
                .select("id, title")\
                .eq("user_id", current_user.user_id)\
                .eq("completed", False)\
                .order("created_at", desc=True)\
                .limit(limit - len(suggestions))
            
            if query:
                todos_query = todos_query.ilike("title", f"%{query}%")
            
            todos_response = todos_query.execute()
            
            for todo in (todos_response.data or []):
                suggestions.append({
                    "type": "todo",
                    "id": todo['id'],
                    "title": todo['title'],
                    "subtitle": "To-do"
                })
        
        return {
            "success": True,
            "suggestions": suggestions[:limit]
        }
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")

