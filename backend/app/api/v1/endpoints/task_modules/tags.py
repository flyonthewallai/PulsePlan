"""
Tags Management API Endpoints

Handles predefined tags and user custom tags.
Implements RULES.md Section 6.1 - No DB access in routers, use service layer.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel, Field
import logging

from app.core.auth import get_current_user
from app.services.tag_service import TagService, get_tag_service
from app.core.utils.error_handlers import handle_endpoint_error, ServiceError

logger = logging.getLogger(__name__)
router = APIRouter()


class UserTagCreateRequest(BaseModel):
    """Request model for creating user tags"""
    name: str = Field(..., description="Tag name", min_length=1, max_length=50)


@router.get("/predefined", response_model=Dict[str, Any])
async def get_predefined_tags(
    service: TagService = Depends(get_tag_service)
):
    """
    Get all predefined system tags

    Returns:
        Dictionary with success status and tag data
    """
    try:
        tags = await service.get_predefined_tags()

        return {
            "success": True,
            "data": {
                "tags": tags,
                "total": len(tags)
            }
        }

    except Exception as e:
        return handle_endpoint_error(e, logger, "get_predefined_tags")


@router.get("/user", response_model=Dict[str, Any])
async def get_user_tags(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Get all user custom tags

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary with success status and user tag data
    """
    try:
        tags = await service.get_user_tags(current_user.user_id)

        return {
            "success": True,
            "data": {
                "tags": tags,
                "total": len(tags)
            }
        }

    except Exception as e:
        return handle_endpoint_error(e, logger, "get_user_tags")


@router.get("/all", response_model=Dict[str, Any])
async def get_all_available_tags(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Get all available tags (predefined + user custom)

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary with all available tags categorized by type
    """
    try:
        result = await service.get_all_available_tags(current_user.user_id)

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        return handle_endpoint_error(e, logger, "get_all_available_tags")


@router.post("/user", response_model=Dict[str, Any])
async def create_user_tag(
    request: UserTagCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Create a new user custom tag

    Args:
        request: Tag creation request
        current_user: Current authenticated user

    Returns:
        Dictionary with created tag data

    Raises:
        HTTPException: If tag already exists or creation fails
    """
    try:
        tag = await service.create_user_tag(current_user.user_id, request.name)

        return {
            "success": True,
            "data": {"tag": tag}
        }

    except ServiceError as e:
        # Handle specific service errors
        if "already exists" in e.message.lower():
            raise HTTPException(status_code=400, detail="Tag already exists")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        return handle_endpoint_error(e, logger, "create_user_tag")


@router.delete("/user/{tag_id}", response_model=Dict[str, Any])
async def delete_user_tag(
    tag_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Delete a user custom tag

    Args:
        tag_id: Tag ID to delete
        current_user: Current authenticated user

    Returns:
        Dictionary with deletion confirmation

    Raises:
        HTTPException: If tag not found or deletion fails
    """
    try:
        deleted = await service.delete_user_tag(current_user.user_id, tag_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Tag not found")

        return {
            "success": True,
            "data": {"deleted_tag_id": tag_id}
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        return handle_endpoint_error(e, logger, "delete_user_tag")


@router.get("/suggestions/{text}", response_model=Dict[str, Any])
async def get_tag_suggestions(
    text: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Get tag suggestions based on text analysis

    Args:
        text: Text to analyze for tag suggestions
        current_user: Current authenticated user

    Returns:
        Dictionary with suggested tags
    """
    try:
        suggestions = await service.get_tag_suggestions(current_user.user_id, text)

        return {
            "success": True,
            "data": {
                "suggestions": suggestions,
                "text_analyzed": text
            }
        }

    except Exception as e:
        return handle_endpoint_error(e, logger, "get_tag_suggestions")


@router.get("/analytics", response_model=Dict[str, Any])
async def get_tag_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: TagService = Depends(get_tag_service)
):
    """
    Get tag usage analytics for the user

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary with tag analytics data
    """
    try:
        analytics = await service.get_tag_analytics(current_user.user_id)

        return {
            "success": True,
            "data": analytics
        }

    except Exception as e:
        return handle_endpoint_error(e, logger, "get_tag_analytics")
