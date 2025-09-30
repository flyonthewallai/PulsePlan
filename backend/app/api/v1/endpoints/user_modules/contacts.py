"""
Google Contacts API Endpoints
Handles contacts operations with proper OAuth integration
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.core.auth import get_current_user, CurrentUser
from app.agents.tools.data.contacts import GoogleContactsTool
from app.services.auth.token_service import get_token_service

logger = logging.getLogger(__name__)
router = APIRouter()


class ContactSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for contacts")
    max_results: int = Field(default=25, ge=1, le=100, description="Maximum results to return")


class ContactSearchResponse(BaseModel):
    success: bool
    contacts_found: int
    contacts: List[Dict[str, Any]]
    message: Optional[str] = None


class ContactListRequest(BaseModel):
    max_results: int = Field(default=50, ge=1, le=100, description="Maximum results to return")
    sort_field: str = Field(default="names", description="Sort field (names or lastModifiedTime)")


class ContactOperationResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    message: Optional[str] = None


@router.get("/search", response_model=ContactSearchResponse)
async def search_contacts(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(default=25, ge=1, le=100, description="Maximum results"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Search Google Contacts
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "search_contacts",
            "query": query,
            "max_results": max_results
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute search
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactSearchResponse(
                success=True,
                contacts_found=result.data.get("contacts_found", 0),
                contacts=result.data.get("contacts", []),
                message="Contacts retrieved successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to search contacts"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search contacts: {str(e)}"
        )


@router.get("/list", response_model=ContactOperationResponse)
async def list_contacts(
    max_results: int = Query(default=50, ge=1, le=100),
    sort_field: str = Query(default="names", regex="^(names|lastModifiedTime)$"),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List user's Google Contacts
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "list_contacts",
            "max_results": max_results,
            "sort_field": sort_field
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute list
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactOperationResponse(
                success=True,
                data=result.data,
                message="Contacts listed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to list contacts"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contacts: {str(e)}"
        )


@router.get("/details/{contact_id}", response_model=ContactOperationResponse)
async def get_contact_details(
    contact_id: str,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get detailed information for a specific contact
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "get_contact_details",
            "contact_id": contact_id
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute get details
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactOperationResponse(
                success=True,
                data=result.data,
                message="Contact details retrieved successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to get contact details"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contact details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact details: {str(e)}"
        )


@router.get("/organization/{organization}", response_model=ContactOperationResponse)
async def find_contacts_by_organization(
    organization: str,
    max_results: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Find contacts by organization/company/school
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "find_contacts_by_organization",
            "organization": organization,
            "max_results": max_results
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute search
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactOperationResponse(
                success=True,
                data=result.data,
                message="Organization contacts found successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to find contacts by organization"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding contacts by organization: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find contacts by organization: {str(e)}"
        )


@router.get("/academic", response_model=ContactOperationResponse)
async def find_academic_contacts(
    max_results: int = Query(default=30, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Find academic contacts (professors, TAs, academic staff)
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "find_academic_contacts",
            "max_results": max_results
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute search
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactOperationResponse(
                success=True,
                data=result.data,
                message="Academic contacts found successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to find academic contacts"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding academic contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find academic contacts: {str(e)}"
        )


@router.get("/domain/{domain}", response_model=ContactOperationResponse)
async def search_by_email_domain(
    domain: str,
    max_results: int = Query(default=25, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Find contacts by email domain (e.g., university domain)
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account not connected. Please connect your Google account first."
            )
        
        # Initialize contacts tool
        contacts_tool = GoogleContactsTool()
        
        # Prepare input data
        input_data = {
            "operation": "search_by_email_domain",
            "domain": domain,
            "max_results": max_results
        }
        
        # Prepare context
        context = {
            "user_id": current_user.user_id,
            "oauth_tokens": {
                "google_access_token": user_tokens.google.access_token
            }
        }
        
        # Execute search
        result = await contacts_tool.execute(input_data, context)
        
        if result.success:
            return ContactOperationResponse(
                success=True,
                data=result.data,
                message="Domain contacts found successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error or "Failed to search by email domain"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching by email domain: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search by email domain: {str(e)}"
        )


@router.get("/status")
async def get_contacts_connection_status(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get Google Contacts connection status
    """
    try:
        # Get user tokens
        token_service = get_token_service()
        user_tokens = await token_service.get_user_tokens_for_agent(current_user.user_id)
        
        if not user_tokens or not user_tokens.google:
            return {
                "connected": False,
                "message": "Google account not connected"
            }
        
        # Check if contacts scope is available
        scopes = user_tokens.google.scope.split() if user_tokens.google.scope else []
        has_contacts_scope = any("contacts" in scope for scope in scopes)
        
        return {
            "connected": True,
            "has_contacts_access": has_contacts_scope,
            "scopes": scopes,
            "message": "Google Contacts integration active" if has_contacts_scope else "Google connected but contacts access not granted"
        }
    
    except Exception as e:
        logger.error(f"Error checking contacts status: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "message": "Failed to check contacts connection status"
        }