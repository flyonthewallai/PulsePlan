"""
Tags management API endpoints.
Handles predefined tags and user custom tags.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.config.database.supabase import get_supabase

router = APIRouter()


class UserTagCreateRequest(BaseModel):
    """Request model for creating user tags"""
    name: str = Field(..., description="Tag name")


@router.get("/predefined", response_model=Dict[str, Any])
async def get_predefined_tags():
    """Get all predefined system tags"""
    try:
        supabase = get_supabase()
        result = supabase.table("predefined_tags").select("*").execute()

        return {
            "success": True,
            "data": {
                "tags": result.data,
                "total": len(result.data)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user", response_model=Dict[str, Any])
async def get_user_tags(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all user custom tags"""
    try:
        supabase = get_supabase()
        result = supabase.table("user_tags").select("*").eq("user_id", current_user["id"]).execute()

        return {
            "success": True,
            "data": {
                "tags": result.data,
                "total": len(result.data)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all", response_model=Dict[str, Any])
async def get_all_available_tags(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all available tags (predefined + user custom)"""
    try:
        supabase = get_supabase()

        # Get predefined tags
        predefined_result = supabase.table("predefined_tags").select("name, category").execute()
        predefined_tags = [{"name": tag["name"], "category": tag["category"], "type": "predefined"} for tag in predefined_result.data]

        # Get user tags
        user_result = supabase.table("user_tags").select("name").eq("user_id", current_user["id"]).execute()
        user_tags = [{"name": tag["name"], "category": "custom", "type": "user"} for tag in user_result.data]

        all_tags = predefined_tags + user_tags

        return {
            "success": True,
            "data": {
                "tags": all_tags,
                "predefined_count": len(predefined_tags),
                "user_count": len(user_tags),
                "total": len(all_tags)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user", response_model=Dict[str, Any])
async def create_user_tag(
    request: UserTagCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new user custom tag"""
    try:
        supabase = get_supabase()

        # Check if tag already exists for this user
        existing = supabase.table("user_tags").select("id").eq("user_id", current_user["id"]).eq("name", request.name.lower()).execute()

        if existing.data:
            raise HTTPException(status_code=400, detail="Tag already exists")

        # Create the tag
        tag_data = {
            "user_id": current_user["id"],
            "name": request.name.lower()
        }

        result = supabase.table("user_tags").insert(tag_data).execute()

        if result.data:
            return {
                "success": True,
                "data": {"tag": result.data[0]}
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create tag")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user/{tag_id}", response_model=Dict[str, Any])
async def delete_user_tag(
    tag_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a user custom tag"""
    try:
        supabase = get_supabase()

        # Delete the tag (RLS policy ensures only owner can delete)
        result = supabase.table("user_tags").delete().eq("id", tag_id).eq("user_id", current_user["id"]).execute()

        if result.data:
            return {
                "success": True,
                "data": {"deleted_tag_id": tag_id}
            }
        else:
            raise HTTPException(status_code=404, detail="Tag not found")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{text}", response_model=Dict[str, Any])
async def get_tag_suggestions(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get tag suggestions based on text analysis"""
    try:
        supabase = get_supabase()

        # Get all available tags
        predefined_result = supabase.table("predefined_tags").select("name").execute()
        predefined_tags = {tag["name"].lower() for tag in predefined_result.data}

        user_result = supabase.table("user_tags").select("name").eq("user_id", current_user["id"]).execute()
        user_tags = {tag["name"].lower() for tag in user_result.data}

        all_tags = predefined_tags | user_tags

        # Simple keyword-based suggestions
        text_lower = text.lower()
        suggestions = []

        tag_patterns = {
            "fitness": ["gym", "workout", "exercise", "fitness", "run", "walk", "jog", "bike"],
            "errand": ["store", "shop", "buy", "pick up", "get", "purchase", "grocery", "mall"],
            "work": ["work", "job", "office", "project", "deadline", "meeting", "client"],
            "personal": ["personal", "self", "me", "my"],
            "health": ["doctor", "dentist", "checkup", "appointment", "health", "medicine"],
            "family": ["family", "mom", "dad", "parent", "sibling", "kids", "children"],
            "club": ["club", "organization", "society", "group", "team"]
        }

        for tag, keywords in tag_patterns.items():
            if tag in all_tags and any(keyword in text_lower for keyword in keywords):
                suggestions.append(tag)

        return {
            "success": True,
            "data": {
                "suggestions": suggestions[:3],  # Limit to 3 suggestions
                "text_analyzed": text
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics", response_model=Dict[str, Any])
async def get_tag_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get tag usage analytics for the user"""
    try:
        supabase = get_supabase()

        # Get tag usage counts using junction table
        # First get user's todo IDs
        user_todos = supabase.table("todos").select("id").eq("user_id", current_user["id"]).execute()
        todo_ids = [todo["id"] for todo in user_todos.data]

        if todo_ids:
            # Query junction table for tag counts
            tag_usage = supabase.table("todo_tags").select("tag_name").in_("todo_id", todo_ids).execute()

            tag_counts = {}
            for tag_record in tag_usage.data:
                tag_name = tag_record["tag_name"]
                tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
        else:
            tag_counts = {}

        analytics_data = [{"tag_name": tag, "usage_count": count} for tag, count in tag_counts.items()]

        # Sort by usage count
        analytics_data.sort(key=lambda x: x.get("usage_count", 0), reverse=True)

        return {
            "success": True,
            "data": {
                "tag_analytics": analytics_data,
                "total_unique_tags": len(analytics_data),
                "most_used_tag": analytics_data[0] if analytics_data else None
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
