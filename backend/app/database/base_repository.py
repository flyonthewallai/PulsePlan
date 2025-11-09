"""
Base Repository
Standardized database access layer with CRUD operations
"""
import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from app.config.database.supabase import get_supabase
from app.core.utils.error_handlers import RepositoryError

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Base repository class providing standard CRUD operations

    All repositories should extend this class and implement the table_name property.
    This ensures consistent database access patterns across the application.
    """

    def __init__(self):
        """Initialize repository with Supabase client"""
        self._supabase = None

    @property
    def supabase(self):
        """Lazy-loaded Supabase client"""
        if self._supabase is None:
            self._supabase = get_supabase()
        return self._supabase

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Table name for this repository - must be implemented by subclasses"""
        pass

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single record by ID

        Args:
            id: Record ID

        Returns:
            Record dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error fetching {self.table_name} by id {id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_by_id",
                details={"id": id}
            )

    async def get_all(self, filters: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all records with optional filters

        Args:
            filters: Optional dictionary of field:value filters
            limit: Optional limit on number of results

        Returns:
            List of record dictionaries

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name).select("*")

            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # Apply limit if provided
            if limit:
                query = query.limit(limit)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching all from {self.table_name}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="get_all",
                details={"filters": filters, "limit": limit}
            )

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record

        Args:
            data: Record data dictionary

        Returns:
            Created record dictionary

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name).insert(data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            raise RepositoryError(
                message="No data returned after insert",
                table=self.table_name,
                operation="create"
            )

        except Exception as e:
            logger.error(f"Error creating {self.table_name}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="create",
                details={"data": data}
            )

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record by ID

        Args:
            id: Record ID
            data: Update data dictionary

        Returns:
            Updated record dictionary or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name).update(data).eq("id", id).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating {self.table_name} id {id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="update",
                details={"id": id, "data": data}
            )

    async def delete(self, id: str) -> bool:
        """
        Delete a record by ID

        Args:
            id: Record ID

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", id).execute()

            return response.data is not None and len(response.data) > 0

        except Exception as e:
            logger.error(f"Error deleting {self.table_name} id {id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="delete",
                details={"id": id}
            )

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters

        Args:
            filters: Optional dictionary of field:value filters

        Returns:
            Count of matching records

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            query = self.supabase.table(self.table_name).select("id", count="exact")

            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            response = query.execute()
            return response.count or 0

        except Exception as e:
            logger.error(f"Error counting {self.table_name}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="count",
                details={"filters": filters}
            )

    async def exists(self, id: str) -> bool:
        """
        Check if a record exists by ID

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise

        Raises:
            RepositoryError: If database operation fails
        """
        try:
            record = await self.get_by_id(id)
            return record is not None

        except Exception as e:
            logger.error(f"Error checking existence in {self.table_name} for id {id}: {e}", exc_info=True)
            raise RepositoryError(
                message=str(e),
                table=self.table_name,
                operation="exists",
                details={"id": id}
            )

    async def health_check(self) -> bool:
        """
        Simple health check - performs a minimal query to verify database connectivity
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            # Perform a minimal query (select id limit 1) to test connectivity
            response = self.supabase.table(self.table_name)\
                .select("id")\
                .limit(1)\
                .execute()
            return True
        except Exception as e:
            logger.debug(f"Health check failed for {self.table_name}: {e}")
            return False
