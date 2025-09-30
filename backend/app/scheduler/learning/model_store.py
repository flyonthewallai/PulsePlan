"""
Model persistence for learning components.

Handles storage and retrieval of model parameters and bandit state.
"""

import json
import pickle
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ModelStore:
    """
    Persistent storage for machine learning model parameters.
    
    Supports both JSON (for simple parameters) and pickle (for complex objects)
    with database and file system backends.
    """
    
    def __init__(self, backend: str = "db", base_path: Optional[str] = None):
        """
        Initialize model store.
        
        Args:
            backend: Storage backend ('db', 'file', 'memory')
            base_path: Base path for file storage
        """
        self.backend = backend
        self.base_path = Path(base_path) if base_path else Path("./model_store")
        self.memory_store = {}  # For memory backend
        
        if self.backend == "file":
            self.base_path.mkdir(parents=True, exist_ok=True)
            
    async def save_model_params(
        self, 
        user_id: str, 
        model_type: str, 
        params: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save model parameters for a user.
        
        Args:
            user_id: User identifier
            model_type: Type of model ('completion', 'bandit', etc.)
            params: Model parameters to save
            metadata: Optional metadata (version, timestamp, etc.)
            
        Returns:
            Success status
        """
        try:
            store_data = {
                'params': params,
                'metadata': metadata or {},
                'updated_at': datetime.now().isoformat(),
                'model_type': model_type
            }
            
            key = f"{user_id}:{model_type}"
            
            if self.backend == "db":
                return await self._save_to_db(key, store_data)
            elif self.backend == "file":
                return await self._save_to_file(key, store_data)
            elif self.backend == "memory":
                self.memory_store[key] = store_data
                return True
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
                
        except Exception as e:
            logger.error(f"Failed to save model params for {user_id}:{model_type}: {e}")
            return False
    
    async def load_model_params(
        self, 
        user_id: str, 
        model_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load model parameters for a user.
        
        Args:
            user_id: User identifier
            model_type: Type of model to load
            
        Returns:
            Model parameters or None if not found
        """
        try:
            key = f"{user_id}:{model_type}"
            
            if self.backend == "db":
                store_data = await self._load_from_db(key)
            elif self.backend == "file":
                store_data = await self._load_from_file(key)
            elif self.backend == "memory":
                store_data = self.memory_store.get(key)
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
                
            return store_data.get('params') if store_data else None
            
        except Exception as e:
            logger.error(f"Failed to load model params for {user_id}:{model_type}: {e}")
            return None
    
    async def save_model_object(
        self, 
        user_id: str, 
        model_type: str, 
        model_obj: Any,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save a complete model object using pickle.
        
        Args:
            user_id: User identifier
            model_type: Type of model
            model_obj: Model object to serialize
            metadata: Optional metadata
            
        Returns:
            Success status
        """
        try:
            # Serialize object
            serialized = pickle.dumps(model_obj)
            
            store_data = {
                'model_blob': serialized,
                'metadata': metadata or {},
                'updated_at': datetime.now().isoformat(),
                'model_type': model_type
            }
            
            key = f"{user_id}:{model_type}:blob"
            
            if self.backend == "db":
                return await self._save_blob_to_db(key, store_data)
            elif self.backend == "file":
                return await self._save_blob_to_file(key, store_data)
            elif self.backend == "memory":
                self.memory_store[key] = store_data
                return True
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
                
        except Exception as e:
            logger.error(f"Failed to save model object for {user_id}:{model_type}: {e}")
            return False
    
    async def load_model_object(
        self, 
        user_id: str, 
        model_type: str
    ) -> Optional[Any]:
        """
        Load a complete model object using pickle.
        
        Args:
            user_id: User identifier
            model_type: Type of model to load
            
        Returns:
            Deserialized model object or None if not found
        """
        try:
            key = f"{user_id}:{model_type}:blob"
            
            if self.backend == "db":
                store_data = await self._load_blob_from_db(key)
            elif self.backend == "file":
                store_data = await self._load_blob_from_file(key)
            elif self.backend == "memory":
                store_data = self.memory_store.get(key)
            else:
                raise ValueError(f"Unknown backend: {self.backend}")
                
            if store_data and 'model_blob' in store_data:
                return pickle.loads(store_data['model_blob'])
                
            return None
            
        except Exception as e:
            logger.error(f"Failed to load model object for {user_id}:{model_type}: {e}")
            return None
    
    async def list_models(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all stored models for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of model metadata
        """
        try:
            if self.backend == "memory":
                models = []
                for key, data in self.memory_store.items():
                    if key.startswith(f"{user_id}:"):
                        models.append({
                            'key': key,
                            'model_type': data.get('model_type'),
                            'updated_at': data.get('updated_at'),
                            'metadata': data.get('metadata', {})
                        })
                return models
            else:
                # Database/file listing would require more implementation
                return []
                
        except Exception as e:
            logger.error(f"Failed to list models for {user_id}: {e}")
            return []
    
    async def delete_model(
        self, 
        user_id: str, 
        model_type: str, 
        include_blob: bool = True
    ) -> bool:
        """
        Delete stored model data.
        
        Args:
            user_id: User identifier
            model_type: Type of model to delete
            include_blob: Whether to also delete blob data
            
        Returns:
            Success status
        """
        try:
            keys_to_delete = [f"{user_id}:{model_type}"]
            if include_blob:
                keys_to_delete.append(f"{user_id}:{model_type}:blob")
            
            if self.backend == "memory":
                for key in keys_to_delete:
                    self.memory_store.pop(key, None)
                return True
            else:
                # Database/file deletion would require more implementation
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete model for {user_id}:{model_type}: {e}")
            return False
    
    # File system backend methods
    async def _save_to_file(self, key: str, data: Dict) -> bool:
        """Save data to file system."""
        file_path = self.base_path / f"{key}.json"
        
        def _write():
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        
        await asyncio.get_event_loop().run_in_executor(None, _write)
        return True
    
    async def _load_from_file(self, key: str) -> Optional[Dict]:
        """Load data from file system."""
        file_path = self.base_path / f"{key}.json"
        
        if not file_path.exists():
            return None
        
        def _read():
            with open(file_path, 'r') as f:
                return json.load(f)
        
        return await asyncio.get_event_loop().run_in_executor(None, _read)
    
    async def _save_blob_to_file(self, key: str, data: Dict) -> bool:
        """Save blob data to file system."""
        file_path = self.base_path / f"{key}.pkl"
        
        def _write():
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
        
        await asyncio.get_event_loop().run_in_executor(None, _write)
        return True
    
    async def _load_blob_from_file(self, key: str) -> Optional[Dict]:
        """Load blob data from file system."""
        file_path = self.base_path / f"{key}.pkl"
        
        if not file_path.exists():
            return None
        
        def _read():
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        
        return await asyncio.get_event_loop().run_in_executor(None, _read)
    
    # Database backend methods (stubbed for now)
    async def _save_to_db(self, key: str, data: Dict) -> bool:
        """Save data to database."""
        try:
            from app.config.database.supabase import get_supabase
            import json
            
            supabase = get_supabase()
            
            # Prepare data for storage
            storage_data = {
                "key": key,
                "data": json.dumps(data, default=str),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data_type": "learning_params",
                "size_bytes": len(json.dumps(data, default=str).encode())
            }
            
            # Try to update first, then insert if not exists
            try:
                response = supabase.table("learning_data").update({
                    "data": storage_data["data"],
                    "updated_at": storage_data["updated_at"],
                    "size_bytes": storage_data["size_bytes"]
                }).eq("key", key).execute()
                
                if not response.data:
                    # Record doesn't exist, insert new one
                    response = supabase.table("learning_data").insert(storage_data).execute()
                
            except Exception:
                # Fallback to insert (might be first time)
                response = supabase.table("learning_data").insert(storage_data).execute()
            
            if response.data:
                logger.info(f"Saved learning data to database: {key}")
                return True
            else:
                logger.error(f"Failed to save learning data: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Database save failed for {key}: {e}, falling back to memory")
            self.memory_store[key] = data
            return True
    
    async def _load_from_db(self, key: str) -> Optional[Dict]:
        """Load data from database."""
        try:
            from app.config.database.supabase import get_supabase
            import json
            
            supabase = get_supabase()
            
            # Load from database
            response = supabase.table("learning_data").select("data").eq("key", key).single().execute()
            
            if response.data:
                data = json.loads(response.data["data"])
                logger.info(f"Loaded learning data from database: {key}")
                return data
            else:
                logger.info(f"No learning data found in database for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Database load failed for {key}: {e}, falling back to memory")
            return self.memory_store.get(key)
    
    async def _save_blob_to_db(self, key: str, data: Dict) -> bool:
        """Save blob data to database."""
        try:
            from app.config.database.supabase import get_supabase
            import json
            import base64
            
            supabase = get_supabase()
            
            # For large blob data, we might want to compress or use external storage
            # For now, we'll store as base64 encoded JSON
            blob_data = json.dumps(data, default=str)
            encoded_data = base64.b64encode(blob_data.encode()).decode()
            
            # Prepare storage data
            storage_data = {
                "key": key,
                "data": encoded_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data_type": "learning_blob",
                "size_bytes": len(blob_data.encode()),
                "encoding": "base64"
            }
            
            # Try to update first, then insert if not exists
            try:
                response = supabase.table("learning_data").update({
                    "data": storage_data["data"],
                    "updated_at": storage_data["updated_at"],
                    "size_bytes": storage_data["size_bytes"]
                }).eq("key", key).execute()
                
                if not response.data:
                    # Record doesn't exist, insert new one
                    response = supabase.table("learning_data").insert(storage_data).execute()
                
            except Exception:
                # Fallback to insert (might be first time)
                response = supabase.table("learning_data").insert(storage_data).execute()
            
            if response.data:
                logger.info(f"Saved learning blob to database: {key} ({storage_data['size_bytes']} bytes)")
                return True
            else:
                logger.error(f"Failed to save learning blob: {key}")
                return False
                
        except Exception as e:
            logger.error(f"Database blob save failed for {key}: {e}, falling back to memory")
            self.memory_store[key] = data
            return True
    
    async def _load_blob_from_db(self, key: str) -> Optional[Dict]:
        """Load blob data from database."""
        try:
            from app.config.database.supabase import get_supabase
            import json
            import base64
            
            supabase = get_supabase()
            
            # Load from database
            response = supabase.table("learning_data").select("data, encoding").eq("key", key).single().execute()
            
            if response.data:
                encoded_data = response.data["data"]
                encoding = response.data.get("encoding", "json")
                
                if encoding == "base64":
                    # Decode base64 then JSON
                    decoded_data = base64.b64decode(encoded_data.encode()).decode()
                    data = json.loads(decoded_data)
                else:
                    # Assume JSON
                    data = json.loads(encoded_data)
                
                logger.info(f"Loaded learning blob from database: {key}")
                return data
            else:
                logger.info(f"No learning blob found in database for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Database blob load failed for {key}: {e}, falling back to memory")
            return self.memory_store.get(key)


# Global model store instance
_model_store = None

def get_model_store(backend: str = "memory") -> ModelStore:
    """Get global model store instance."""
    global _model_store
    if _model_store is None:
        _model_store = ModelStore(backend=backend)
    return _model_store
