"""
WebSocket Manager for Real-time Agent Workflow Updates
Handles WebSocket connections, authentication, and message broadcasting
"""
import asyncio
import logging
from typing import Dict, Set, Any, Optional
from datetime import datetime
import socketio
from fastapi import HTTPException

from app.core.auth import verify_supabase_token

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time updates for agent workflows"""
    
    def __init__(self):
        # Create Socket.IO server with CORS support and timeout settings
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            ping_timeout=60,        # 60 seconds ping timeout
            ping_interval=25,       # 25 seconds ping interval
            max_http_buffer_size=1000000  # 1MB buffer size
        )
        
        # Store user connections: user_id -> set of session_ids
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Store workflow subscriptions: workflow_id -> set of session_ids
        self.workflow_subscriptions: Dict[str, Set[str]] = {}
        
        # Store session authentication: session_id -> user_id
        self.authenticated_sessions: Dict[str, str] = {}
        
        # Connection timeout tracking
        self.connection_timeouts: Dict[str, asyncio.Task] = {}
        self.connection_timeout_duration = 300  # 5 minutes timeout for unauthenticated connections
        
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            logger.info(f"WebSocket client connected: {sid}")
            
            # Start timeout task for unauthenticated connection
            timeout_task = asyncio.create_task(self._handle_connection_timeout(sid))
            self.connection_timeouts[sid] = timeout_task
            
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            logger.info(f"WebSocket client disconnected: {sid}")
            
            # Cancel timeout task
            if sid in self.connection_timeouts:
                self.connection_timeouts[sid].cancel()
                del self.connection_timeouts[sid]
            await self._cleanup_session(sid)
        
        @self.sio.event
        async def authenticate(sid, data):
            """Authenticate WebSocket connection"""
            try:
                token = data.get('token')
                user_id = data.get('userId')
                
                if not token:
                    await self.sio.emit('auth_error', {'error': 'No token provided'}, room=sid)
                    return
                
                # Verify token and get user
                try:
                    # Verify the token using Supabase
                    payload = verify_supabase_token(token)
                    verified_user_id = payload.get("sub")
                    
                    if verified_user_id and verified_user_id == user_id:
                        # Store authentication
                        self.authenticated_sessions[sid] = verified_user_id
                        
                        # Cancel timeout task since user is now authenticated
                        if sid in self.connection_timeouts:
                            self.connection_timeouts[sid].cancel()
                            del self.connection_timeouts[sid]
                        
                        # Add to user connections
                        if verified_user_id not in self.user_connections:
                            self.user_connections[verified_user_id] = set()
                        self.user_connections[verified_user_id].add(sid)
                        
                        logger.info(f"WebSocket authenticated: user {verified_user_id} via session {sid}")
                        await self.sio.emit('authenticated', {
                            'user_id': verified_user_id,
                            'timestamp': datetime.utcnow().isoformat()
                        }, room=sid)
                    else:
                        await self.sio.emit('auth_error', {'error': 'Invalid credentials'}, room=sid)
                        
                except Exception as e:
                    logger.error(f"Token verification failed: {e}")
                    await self.sio.emit('auth_error', {'error': 'Token verification failed'}, room=sid)
                    
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                await self.sio.emit('auth_error', {'error': 'Authentication failed'}, room=sid)
        
        @self.sio.event
        async def subscribe_workflow(sid, data):
            """Subscribe to workflow updates"""
            try:
                user_id = self.authenticated_sessions.get(sid)
                if not user_id:
                    await self.sio.emit('error', {'error': 'Not authenticated'}, room=sid)
                    return
                
                workflow_id = data.get('workflow_id')
                if not workflow_id:
                    await self.sio.emit('error', {'error': 'No workflow_id provided'}, room=sid)
                    return
                
                # Add to workflow subscriptions
                if workflow_id not in self.workflow_subscriptions:
                    self.workflow_subscriptions[workflow_id] = set()
                self.workflow_subscriptions[workflow_id].add(sid)
                
                logger.info(f"User {user_id} subscribed to workflow {workflow_id}")
                await self.sio.emit('workflow_subscribed', {
                    'workflow_id': workflow_id,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Workflow subscription error: {e}")
                await self.sio.emit('error', {'error': 'Subscription failed'}, room=sid)
        
        @self.sio.event
        async def unsubscribe_workflow(sid, data):
            """Unsubscribe from workflow updates"""
            try:
                workflow_id = data.get('workflow_id')
                if workflow_id and workflow_id in self.workflow_subscriptions:
                    self.workflow_subscriptions[workflow_id].discard(sid)
                    if not self.workflow_subscriptions[workflow_id]:
                        del self.workflow_subscriptions[workflow_id]
                
                logger.info(f"Session {sid} unsubscribed from workflow {workflow_id}")
                
            except Exception as e:
                logger.error(f"Workflow unsubscription error: {e}")
    
    async def _cleanup_session(self, sid: str):
        """Cleanup session data on disconnect"""
        try:
            # Remove from authenticated sessions
            user_id = self.authenticated_sessions.pop(sid, None)
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(sid)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from workflow subscriptions
            for workflow_id in list(self.workflow_subscriptions.keys()):
                self.workflow_subscriptions[workflow_id].discard(sid)
                if not self.workflow_subscriptions[workflow_id]:
                    del self.workflow_subscriptions[workflow_id]
                    
            logger.info(f"Cleaned up session {sid} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    async def emit_workflow_update(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """Emit workflow update to subscribed clients"""
        try:
            if workflow_id not in self.workflow_subscriptions:
                logger.debug(f"No subscribers for workflow {workflow_id}")
                return
            
            subscribers = self.workflow_subscriptions[workflow_id].copy()
            if not subscribers:
                return
            
            message = {
                'workflow_id': workflow_id,
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Broadcasting {event_type} for workflow {workflow_id} to {len(subscribers)} subscribers")
            logger.info(f"Message: {message}")
            
            # Emit to all subscribers
            for sid in subscribers:
                try:
                    await self.sio.emit('workflow_update', message, room=sid)
                except Exception as e:
                    logger.error(f"Failed to emit to session {sid}: {e}")
                    # Remove failed session
                    self.workflow_subscriptions[workflow_id].discard(sid)
            
        except Exception as e:
            logger.error(f"Error emitting workflow update: {e}")

    async def emit_to_user(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Emit event directly to all connections of a specific user with conversation context"""
        try:
            if user_id not in self.user_connections:
                logger.debug(f"No connections for user {user_id}")
                return

            user_sessions = self.user_connections[user_id].copy()
            if not user_sessions:
                return

            # Get conversation context if available
            conversation_context = None
            try:
                from app.agents.services.flexible_conversation_manager import get_flexible_conversation_manager
                conversation_manager = get_flexible_conversation_manager()
                conversation_context = conversation_manager.get_conversation_context(user_id)
            except Exception as e:
                logger.debug(f"Could not get conversation context for user {user_id}: {e}")

            message = {
                'user_id': user_id,
                'event_type': event_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'conversation_context': conversation_context
            }

            logger.info(f"Emitting {event_type} to user {user_id} ({len(user_sessions)} sessions)")

            # Emit to all user sessions
            for sid in user_sessions:
                try:
                    await self.sio.emit(event_type, message, room=sid)
                except Exception as e:
                    logger.error(f"Failed to emit to user session {sid}: {e}")
                    # Remove failed session
                    self.user_connections[user_id].discard(sid)

        except Exception as e:
            logger.error(f"Error emitting to user {user_id}: {e}")

    async def emit_node_update(self, workflow_id: str, node_name: str, status: str, data: Optional[Dict[str, Any]] = None):
        """Emit node status update"""
        await self.emit_workflow_update(workflow_id, 'node_update', {
            'node_name': node_name,
            'status': status,
            'data': data or {}
        })
    
    async def emit_tool_update(self, workflow_id: str, tool_name: str, status: str, result: Optional[str] = None, execution_time: Optional[float] = None):
        """Emit tool execution update"""
        await self.emit_workflow_update(workflow_id, 'tool_update', {
            'tool_name': tool_name,
            'status': status,
            'result': result,
            'execution_time': execution_time
        })
    
    async def emit_search_results(self, workflow_id: str, search_data: Dict[str, Any]):
        """Emit search results update"""
        logger.info(f"[WEBSOCKET MANAGER] Emitting search_results for workflow {workflow_id}")
        logger.info(f"[WEBSOCKET MANAGER] Data keys: {list(search_data.keys())}")
        await self.emit_workflow_update(workflow_id, 'search_results', search_data)
    
    async def emit_task_created(self, workflow_id: str, task_data: Dict[str, Any]):
        """Emit task/todo creation update"""
        logger.info(f"[WEBSOCKET MANAGER] Emitting task_created for workflow {workflow_id}")
        logger.info(f"[WEBSOCKET MANAGER] Task type: {task_data.get('type')}, Title: {task_data.get('title')}")

        # Emit to workflow subscribers
        await self.emit_workflow_update(workflow_id, 'task_created', task_data)

        # Also emit directly to the user who created the task (if we can determine user_id)
        # This ensures the task success card appears even without workflow subscription
        if 'user_id' in task_data:
            user_id = task_data['user_id']
            await self.emit_to_user(user_id, 'task_created', task_data)
    
    async def emit_task_updated(self, workflow_id: str, task_data: Dict[str, Any]):
        """Emit task/todo update update"""
        logger.info(f"[WEBSOCKET MANAGER] Emitting task_updated for workflow {workflow_id}")

        # Emit to workflow subscribers
        await self.emit_workflow_update(workflow_id, 'task_updated', task_data)

        # Also emit directly to the user who updated the task (if we can determine user_id)
        # This ensures the task update is reflected in real-time
        if 'user_id' in task_data:
            user_id = task_data['user_id']
            await self.emit_to_user(user_id, 'task_updated', task_data)
    
    async def emit_task_deleted(self, workflow_id: str, task_data: Dict[str, Any]):
        """Emit task/todo deletion update"""
        logger.info(f"[WEBSOCKET MANAGER] Emitting task_deleted for workflow {workflow_id}")
        logger.info(f"[WEBSOCKET MANAGER] Task type: {task_data.get('type')}, Title: {task_data.get('title')}")

        # Emit to workflow subscribers
        await self.emit_workflow_update(workflow_id, 'task_deleted', task_data)

        # Also emit directly to the user who deleted the task (if we can determine user_id)
        # This ensures the task delete card appears even without workflow subscription
        if 'user_id' in task_data:
            user_id = task_data['user_id']
            await self.emit_to_user(user_id, 'task_deleted', task_data)
    
    async def emit_email_results(self, workflow_id: str, email_data: Dict[str, Any]):
        """Emit email operation results"""
        logger.info(f"[WEBSOCKET MANAGER] Emitting email_results for workflow {workflow_id}")
        logger.info(f"[WEBSOCKET MANAGER] Email operation: {email_data.get('operation_type', 'unknown')}")
        if email_data.get('email_count'):
            logger.info(f"[WEBSOCKET MANAGER] Email count: {email_data['email_count']}")
        await self.emit_workflow_update(workflow_id, 'email_results', email_data)
    
    async def emit_workflow_status(self, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """Emit overall workflow status update"""
        await self.emit_workflow_update(workflow_id, 'workflow_status', {
            'status': status,
            'result': result
        })
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of active connections for a user"""
        return len(self.user_connections.get(user_id, set()))
    
    def get_workflow_subscriber_count(self, workflow_id: str) -> int:
        """Get number of subscribers for a workflow"""
        return len(self.workflow_subscriptions.get(workflow_id, set()))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics"""
        return {
            'total_connections': len(self.authenticated_sessions),
            'unique_users': len(self.user_connections),
            'active_workflows': len(self.workflow_subscriptions),
            'pending_timeouts': len(self.connection_timeouts),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _handle_connection_timeout(self, sid: str):
        """Handle connection timeout for unauthenticated sessions"""
        try:
            await asyncio.sleep(self.connection_timeout_duration)
            
            # Check if session is still unauthenticated
            if sid not in self.authenticated_sessions:
                logger.warning(f"⏰ Connection timeout for unauthenticated session: {sid}")
                await self.sio.emit('timeout_warning', {
                    'message': 'Connection will be closed due to inactivity',
                    'timeout': 30
                }, room=sid)
                
                # Give 30 seconds grace period
                await asyncio.sleep(30)
                
                # Force disconnect if still not authenticated
                if sid not in self.authenticated_sessions:
                    logger.info(f"Force disconnecting unauthenticated session: {sid}")
                    await self.sio.disconnect(sid)
                    
        except asyncio.CancelledError:
            # Timeout was cancelled (session authenticated or disconnected)
            pass
        except Exception as e:
            logger.error(f"Error in connection timeout handler for {sid}: {e}")
        finally:
            # Clean up timeout task reference
            if sid in self.connection_timeouts:
                del self.connection_timeouts[sid]

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
