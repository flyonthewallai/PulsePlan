"""
Conversation Repository
Handles database operations for conversations and chat turns
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.database.base_repository import BaseRepository
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository):
    """Repository for conversation operations"""

    @property
    def table_name(self) -> str:
        """Return the table name"""
        return "conversations"

    async def get_active_by_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent active conversation for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Conversation dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .order("last_message_at", desc=True)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching active conversation for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_active_by_user",
                details={"user_id": user_id}
            )

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        include_inactive: bool = False,
        order_by: str = "last_message_at",
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List conversations for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to return
            include_inactive: Whether to include inactive conversations
            order_by: Field to order by
            order_desc: Whether to order descending
        
        Returns:
            List of conversation dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)
            
            if not include_inactive:
                query = query.eq("is_active", True)
            
            if order_desc:
                query = query.order(order_by, desc=True)
            else:
                query = query.order(order_by, desc=False)
            
            response = query.limit(limit).execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error listing conversations for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="list_by_user",
                details={"user_id": user_id, "limit": limit}
            )

    async def count_active_by_user(self, user_id: str) -> int:
        """
        Count active conversations for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Number of active conversations
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .execute()
            
            return response.count if hasattr(response, 'count') else len(response.data or [])
        
        except Exception as e:
            logger.error(f"Error counting active conversations for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="count_active_by_user",
                details={"user_id": user_id}
            )

    async def get_by_id_and_user(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation by ID and user ID
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            
        Returns:
            Conversation dictionary or None if not found
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching conversation {conversation_id} for user {user_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id_and_user",
                details={"conversation_id": conversation_id, "user_id": user_id}
            )

    async def create(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new conversation
        
        Args:
            conversation_data: Conversation data dictionary
            
        Returns:
            Created conversation dictionary
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .insert(conversation_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise RepositoryError(
                message="Failed to create conversation",
                table=self.table_name,
                operation="create"
            )
        
        except Exception as e:
            logger.error(f"Error creating conversation: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create",
                details=conversation_data
            )

    async def update(
        self,
        conversation_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update conversation
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated conversation dictionary
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name)\
                .update(updates)\
                .eq("id", conversation_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise RepositoryError(
                message="Failed to update conversation",
                table=self.table_name,
                operation="update"
            )
        
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update",
                details={"conversation_id": conversation_id, "user_id": user_id, "updates": updates}
            )

    async def delete(
        self,
        conversation_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete conversation (soft or hard delete)
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID
            soft_delete: If True, mark as inactive; if False, hard delete
            
        Returns:
            True if successful
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            if soft_delete:
                response = self.supabase.table(self.table_name)\
                    .update({
                        "is_active": False,
                        "updated_at": datetime.utcnow().isoformat()
                    })\
                    .eq("id", conversation_id)\
                    .eq("user_id", user_id)\
                    .execute()
            else:
                response = self.supabase.table(self.table_name)\
                    .delete()\
                    .eq("id", conversation_id)\
                    .eq("user_id", user_id)\
                    .execute()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete",
                details={"conversation_id": conversation_id, "user_id": user_id, "soft_delete": soft_delete}
            )

    # Chat Turns methods
    async def create_chat_turn(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new chat turn
        
        Args:
            turn_data: Chat turn data dictionary
            
        Returns:
            Created chat turn dictionary
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table("chat_turns")\
                .insert(turn_data)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise RepositoryError(
                message="Failed to create chat turn",
                table="chat_turns",
                operation="create_chat_turn"
            )
        
        except Exception as e:
            logger.error(f"Error creating chat turn: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table="chat_turns",
                operation="create_chat_turn",
                details=turn_data
            )

    async def get_chat_turns(
        self,
        conversation_id: str,
        limit: int = 50,
        order_desc: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get chat turns for a conversation
        
        Args:
            conversation_id: Conversation ID
            limit: Maximum number of turns to return
            order_desc: Whether to order by timestamp descending
            
        Returns:
            List of chat turn dictionaries
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table("chat_turns")\
                .select("*")\
                .eq("conversation_id", conversation_id)
            
            if order_desc:
                query = query.order("timestamp", desc=True)
            else:
                query = query.order("timestamp", desc=False)
            
            response = query.limit(limit).execute()
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching chat turns for conversation {conversation_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table="chat_turns",
                operation="get_chat_turns",
                details={"conversation_id": conversation_id, "limit": limit}
            )

    async def count_chat_turns(self, conversation_id: str) -> int:
        """
        Count chat turns for a conversation
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Number of chat turns
            
        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table("chat_turns")\
                .select("id", count="exact")\
                .eq("conversation_id", conversation_id)\
                .execute()
            
            return response.count if hasattr(response, 'count') else len(response.data or [])
        
        except Exception as e:
            logger.error(f"Error counting chat turns for conversation {conversation_id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table="chat_turns",
                operation="count_chat_turns",
                details={"conversation_id": conversation_id}
            )


def get_conversation_repository() -> ConversationRepository:
    """Dependency injection function"""
    return ConversationRepository()

