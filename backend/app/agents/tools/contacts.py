"""
Google Contacts integration tool for PulsePlan agents.
Provides access to user's Google Contacts for academic and professional networking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import asyncio

from .base import BaseTool, ToolResult, ToolError

logger = logging.getLogger(__name__)

class GoogleContactsTool(BaseTool):
    """
    Google Contacts integration tool for agent access to user's contact network.
    
    Use cases for agents:
    1. Find professor/TA contact info for office hours scheduling
    2. Locate classmates for study groups
    3. Search for professional contacts (internship coordinators, mentors)
    4. Get contact details when scheduling meetings
    5. Identify emergency contacts for important deadlines
    """
    
    def __init__(self):
        super().__init__(
            name="google_contacts",
            description="Access Google Contacts to find professors, classmates, and professional contacts for academic planning"
        )
        
        self.access_token = None  # Set per request from OAuth tokens
    
    def get_required_tokens(self) -> List[str]:
        """Google Contacts requires OAuth access token"""
        return ["google_oauth"]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for contacts operations"""
        operation = input_data.get("operation")
        
        if not operation:
            return False
        
        valid_operations = {
            "search_contacts", "get_contact_details", "list_contacts", 
            "find_contacts_by_organization", "search_by_email_domain",
            "get_contact_groups", "find_academic_contacts", "get_recent_contacts"
        }
        
        return operation in valid_operations
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute Google Contacts operation based on input"""
        start_time = datetime.utcnow()
        
        try:
            operation = input_data.get("operation")
            user_id = context.get("user_id")
            oauth_tokens = context.get("oauth_tokens", {})
            
            if not user_id:
                raise ToolError("User ID required in context", self.name)
            
            # Get Google OAuth token
            self.access_token = oauth_tokens.get("google_access_token")
            if not self.access_token:
                raise ToolError("Google OAuth access token required", self.name)
            
            # Route to appropriate operation
            if operation == "search_contacts":
                result = await self._search_contacts(input_data, user_id)
            elif operation == "get_contact_details":
                result = await self._get_contact_details(input_data, user_id)
            elif operation == "list_contacts":
                result = await self._list_contacts(input_data, user_id)
            elif operation == "find_contacts_by_organization":
                result = await self._find_contacts_by_organization(input_data, user_id)
            elif operation == "search_by_email_domain":
                result = await self._search_by_email_domain(input_data, user_id)
            elif operation == "get_contact_groups":
                result = await self._get_contact_groups(input_data, user_id)
            elif operation == "find_academic_contacts":
                result = await self._find_academic_contacts(input_data, user_id)
            elif operation == "get_recent_contacts":
                result = await self._get_recent_contacts(input_data, user_id)
            else:
                raise ToolError(f"Unknown operation: {operation}", self.name)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            tool_result = ToolResult(
                success=True,
                data=result,
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": user_id
                }
            )
            
            self.log_execution(input_data, tool_result, context)
            return tool_result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.error(f"Google Contacts tool execution failed: {e}")
            
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                execution_time=execution_time,
                metadata={
                    "operation": operation,
                    "user_id": context.get("user_id")
                }
            )
    
    async def _make_contacts_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Google People API"""
        base_url = "https://people.googleapis.com/v1"
        url = f"{base_url}/{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise ToolError("Google Contacts API authentication failed - token may be expired", self.name)
                elif response.status == 403:
                    raise ToolError("Google Contacts API access forbidden - check permissions", self.name)
                else:
                    error_text = await response.text()
                    raise ToolError(f"Google Contacts API error {response.status}: {error_text}", self.name)
    
    async def _search_contacts(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Search contacts by name, email, or other criteria"""
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", 25)
        
        if not query:
            raise ToolError("Search query is required", self.name)
        
        try:
            # Use searchContacts endpoint for query-based search
            response = await self._make_contacts_request("people:searchContacts", {
                "query": query,
                "pageSize": min(max_results, 30)  # API limit
            })
            
            contacts = []
            results = response.get("results", [])
            
            for result in results:
                person = result.get("person", {})
                contact_info = self._parse_contact_person(person)
                if contact_info:
                    contacts.append(contact_info)
            
            return {
                "operation": "search_contacts",
                "query": query,
                "contacts_found": len(contacts),
                "contacts": contacts,
                "searched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Contact search failed: {e}")
            raise ToolError(f"Failed to search contacts: {e}", self.name)
    
    async def _list_contacts(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """List user's contacts with optional filtering"""
        max_results = input_data.get("max_results", 50)
        sort_field = input_data.get("sort_field", "names")  # names, lastModifiedTime
        
        try:
            # Get connections (user's contacts)
            response = await self._make_contacts_request("people/me/connections", {
                "personFields": "names,emailAddresses,phoneNumbers,organizations,photos,biographies",
                "pageSize": min(max_results, 100),  # API limit
                "sortOrder": "LAST_MODIFIED_DESCENDING" if sort_field == "lastModifiedTime" else "FIRST_NAME_ASCENDING"
            })
            
            contacts = []
            connections = response.get("connections", [])
            
            for person in connections:
                contact_info = self._parse_contact_person(person)
                if contact_info:
                    contacts.append(contact_info)
            
            return {
                "operation": "list_contacts",
                "contacts_returned": len(contacts),
                "total_available": len(connections),
                "contacts": contacts,
                "sort_field": sort_field,
                "listed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Contact listing failed: {e}")
            raise ToolError(f"Failed to list contacts: {e}", self.name)
    
    async def _get_contact_details(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific contact"""
        contact_id = input_data.get("contact_id")
        resource_name = input_data.get("resource_name")  # Alternative identifier
        
        if not contact_id and not resource_name:
            raise ToolError("Either contact_id or resource_name is required", self.name)
        
        try:
            # Use resource_name if provided, otherwise construct from contact_id
            person_resource = resource_name or f"people/{contact_id}"
            
            response = await self._make_contacts_request(person_resource, {
                "personFields": "names,emailAddresses,phoneNumbers,organizations,addresses,birthdays,biographies,photos,urls,relations"
            })
            
            contact_details = self._parse_contact_person(response, detailed=True)
            
            return {
                "operation": "get_contact_details",
                "contact_id": contact_id,
                "contact_details": contact_details,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get contact details: {e}")
            raise ToolError(f"Failed to get contact details: {e}", self.name)
    
    async def _find_contacts_by_organization(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Find contacts by organization/company/school"""
        organization = input_data.get("organization", "")
        max_results = input_data.get("max_results", 25)
        
        if not organization:
            raise ToolError("Organization name is required", self.name)
        
        try:
            # Get all contacts and filter by organization
            response = await self._make_contacts_request("people/me/connections", {
                "personFields": "names,emailAddresses,organizations",
                "pageSize": 100  # Get more to filter locally
            })
            
            matching_contacts = []
            connections = response.get("connections", [])
            
            for person in connections:
                organizations = person.get("organizations", [])
                
                # Check if any organization matches
                for org in organizations:
                    org_name = org.get("name", "").lower()
                    if organization.lower() in org_name:
                        contact_info = self._parse_contact_person(person)
                        if contact_info:
                            contact_info["matched_organization"] = org.get("name")
                            contact_info["title"] = org.get("title", "")
                            matching_contacts.append(contact_info)
                        break
                
                if len(matching_contacts) >= max_results:
                    break
            
            return {
                "operation": "find_contacts_by_organization",
                "organization": organization,
                "contacts_found": len(matching_contacts),
                "contacts": matching_contacts,
                "searched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Organization search failed: {e}")
            raise ToolError(f"Failed to search by organization: {e}", self.name)
    
    async def _search_by_email_domain(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Find contacts by email domain (e.g., university domain)"""
        domain = input_data.get("domain", "")
        max_results = input_data.get("max_results", 25)
        
        if not domain:
            raise ToolError("Email domain is required", self.name)
        
        # Normalize domain (remove @ if present)
        domain = domain.lstrip("@").lower()
        
        try:
            response = await self._make_contacts_request("people/me/connections", {
                "personFields": "names,emailAddresses,organizations",
                "pageSize": 100
            })
            
            matching_contacts = []
            connections = response.get("connections", [])
            
            for person in connections:
                emails = person.get("emailAddresses", [])
                
                # Check if any email matches domain
                for email_info in emails:
                    email = email_info.get("value", "").lower()
                    if email.endswith(f"@{domain}"):
                        contact_info = self._parse_contact_person(person)
                        if contact_info:
                            contact_info["matched_email"] = email
                            matching_contacts.append(contact_info)
                        break
                
                if len(matching_contacts) >= max_results:
                    break
            
            return {
                "operation": "search_by_email_domain",
                "domain": domain,
                "contacts_found": len(matching_contacts),
                "contacts": matching_contacts,
                "searched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Email domain search failed: {e}")
            raise ToolError(f"Failed to search by email domain: {e}", self.name)
    
    async def _find_academic_contacts(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Find academic contacts (professors, TAs, academic staff)"""
        max_results = input_data.get("max_results", 30)
        
        # Keywords that indicate academic contacts
        academic_keywords = [
            "professor", "prof", "dr.", "phd", "instructor", "teacher", "ta", "teaching assistant",
            "academic", "faculty", "department", "university", "college", "research", "advisor"
        ]
        
        try:
            response = await self._make_contacts_request("people/me/connections", {
                "personFields": "names,emailAddresses,organizations,biographies",
                "pageSize": 100
            })
            
            academic_contacts = []
            connections = response.get("connections", [])
            
            for person in connections:
                is_academic = False
                matched_keywords = []
                
                # Check names for titles
                names = person.get("names", [])
                for name in names:
                    display_name = name.get("displayName", "").lower()
                    for keyword in academic_keywords:
                        if keyword in display_name:
                            is_academic = True
                            matched_keywords.append(keyword)
                
                # Check organizations
                organizations = person.get("organizations", [])
                for org in organizations:
                    org_name = org.get("name", "").lower()
                    org_title = org.get("title", "").lower()
                    
                    for keyword in academic_keywords:
                        if keyword in org_name or keyword in org_title:
                            is_academic = True
                            matched_keywords.append(keyword)
                
                # Check biography
                biographies = person.get("biographies", [])
                for bio in biographies:
                    bio_text = bio.get("value", "").lower()
                    for keyword in academic_keywords:
                        if keyword in bio_text:
                            is_academic = True
                            matched_keywords.append(keyword)
                
                if is_academic:
                    contact_info = self._parse_contact_person(person)
                    if contact_info:
                        contact_info["academic_keywords"] = list(set(matched_keywords))
                        contact_info["likely_academic"] = True
                        academic_contacts.append(contact_info)
                
                if len(academic_contacts) >= max_results:
                    break
            
            return {
                "operation": "find_academic_contacts",
                "academic_contacts_found": len(academic_contacts),
                "contacts": academic_contacts,
                "searched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Academic contacts search failed: {e}")
            raise ToolError(f"Failed to find academic contacts: {e}", self.name)
    
    async def _get_contact_groups(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get contact groups/labels"""
        try:
            response = await self._make_contacts_request("contactGroups", {
                "pageSize": 50
            })
            
            groups = []
            contact_groups = response.get("contactGroups", [])
            
            for group in contact_groups:
                group_info = {
                    "resource_name": group.get("resourceName"),
                    "name": group.get("name"),
                    "formatted_name": group.get("formattedName"),
                    "group_type": group.get("groupType"),
                    "member_count": group.get("memberCount", 0)
                }
                groups.append(group_info)
            
            return {
                "operation": "get_contact_groups",
                "groups_found": len(groups),
                "groups": groups,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get contact groups: {e}")
            raise ToolError(f"Failed to get contact groups: {e}", self.name)
    
    async def _get_recent_contacts(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Get recently contacted people"""
        max_results = input_data.get("max_results", 20)
        
        try:
            response = await self._make_contacts_request("people/me/connections", {
                "personFields": "names,emailAddresses,phoneNumbers,organizations",
                "pageSize": min(max_results, 50),
                "sortOrder": "LAST_MODIFIED_DESCENDING"
            })
            
            contacts = []
            connections = response.get("connections", [])
            
            for person in connections:
                contact_info = self._parse_contact_person(person)
                if contact_info:
                    contacts.append(contact_info)
            
            return {
                "operation": "get_recent_contacts",
                "recent_contacts_found": len(contacts),
                "contacts": contacts,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get recent contacts: {e}")
            raise ToolError(f"Failed to get recent contacts: {e}", self.name)
    
    def _parse_contact_person(self, person: Dict[str, Any], detailed: bool = False) -> Optional[Dict[str, Any]]:
        """Parse Google People API person object into contact info"""
        try:
            contact = {}
            
            # Names
            names = person.get("names", [])
            if names:
                primary_name = names[0]
                contact["name"] = primary_name.get("displayName", "")
                contact["given_name"] = primary_name.get("givenName", "")
                contact["family_name"] = primary_name.get("familyName", "")
            else:
                contact["name"] = "Unknown"
            
            # Email addresses
            emails = person.get("emailAddresses", [])
            contact["emails"] = []
            for email in emails:
                contact["emails"].append({
                    "address": email.get("value", ""),
                    "type": email.get("type", ""),
                    "primary": email.get("metadata", {}).get("primary", False)
                })
            
            # Phone numbers
            phones = person.get("phoneNumbers", [])
            contact["phones"] = []
            for phone in phones:
                contact["phones"].append({
                    "number": phone.get("value", ""),
                    "type": phone.get("type", "")
                })
            
            # Organizations
            organizations = person.get("organizations", [])
            contact["organizations"] = []
            for org in organizations:
                contact["organizations"].append({
                    "name": org.get("name", ""),
                    "title": org.get("title", ""),
                    "department": org.get("department", "")
                })
            
            # Resource name for API calls
            contact["resource_name"] = person.get("resourceName", "")
            
            if detailed:
                # Additional details for full contact view
                
                # Photos
                photos = person.get("photos", [])
                if photos:
                    contact["photo_url"] = photos[0].get("url", "")
                
                # Biography
                biographies = person.get("biographies", [])
                if biographies:
                    contact["biography"] = biographies[0].get("value", "")
                
                # Addresses
                addresses = person.get("addresses", [])
                contact["addresses"] = []
                for address in addresses:
                    contact["addresses"].append({
                        "formatted_value": address.get("formattedValue", ""),
                        "type": address.get("type", "")
                    })
                
                # URLs
                urls = person.get("urls", [])
                contact["urls"] = []
                for url in urls:
                    contact["urls"].append({
                        "value": url.get("value", ""),
                        "type": url.get("type", "")
                    })
            
            return contact if contact.get("name") != "Unknown" or contact.get("emails") else None
            
        except Exception as e:
            logger.warning(f"Failed to parse contact person: {e}")
            return None

# Create global instance
google_contacts_tool = GoogleContactsTool()