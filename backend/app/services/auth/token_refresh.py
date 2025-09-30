"""
Token Refresh Service
Handles automatic refresh of OAuth tokens for various providers
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.config.database.supabase import get_supabase
from app.services.auth.oauth import GoogleOAuthService, MicrosoftOAuthService


logger = logging.getLogger(__name__)


class TokenProvider(str, Enum):
    """Supported OAuth providers"""
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GMAIL = "gmail"
    OUTLOOK = "outlook"


class RefreshResult(str, Enum):
    """Token refresh operation results"""
    SUCCESS = "success"
    FAILED = "failed"
    NO_REFRESH_TOKEN = "no_refresh_token"
    PROVIDER_ERROR = "provider_error"
    TOKEN_REVOKED = "token_revoked"


@dataclass
class RefreshAttempt:
    """Token refresh attempt result"""
    user_id: str
    provider: TokenProvider
    result: RefreshResult
    timestamp: datetime
    error: Optional[str] = None
    new_expires_at: Optional[datetime] = None

@dataclass
class OAuthToken:
    """OAuth token data structure for Supabase"""
    id: str
    user_id: str
    provider: str
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    scope: Optional[str]
    expires_at: datetime
    created_at: datetime
    last_refreshed: Optional[datetime]
    is_active: bool
    encryption_key_version: int


class TokenRefreshService:
    """
    Service for automatically refreshing OAuth tokens
    Runs background tasks to refresh tokens before they expire
    """
    
    def __init__(self):
        self.refresh_margin_minutes = 30  # Refresh 30 minutes before expiry
        self.max_retry_attempts = 3
        self.retry_delay_seconds = 300  # 5 minutes between retries
        self.batch_size = 50  # Process tokens in batches
        
        # OAuth service instances
        self.oauth_services = {
            TokenProvider.GOOGLE: GoogleOAuthService(),
            TokenProvider.MICROSOFT: MicrosoftOAuthService(),
            TokenProvider.GMAIL: GoogleOAuthService(),  # Gmail uses Google OAuth
            TokenProvider.OUTLOOK: MicrosoftOAuthService()  # Outlook uses Microsoft OAuth
        }
        
        # Track refresh attempts
        self.recent_attempts: List[RefreshAttempt] = []
        self.max_attempt_history = 1000
        
        # Background task control
        self._refresh_task: Optional[asyncio.Task] = None
        self._stop_refresh = False
    
    async def start_background_refresh(self):
        """Start the background token refresh task"""
        if self._refresh_task and not self._refresh_task.done():
            logger.warning("Background refresh task is already running")
            return
        
        self._stop_refresh = False
        self._refresh_task = asyncio.create_task(self._background_refresh_loop())
        logger.info("Started background token refresh service")
    
    async def stop_background_refresh(self):
        """Stop the background token refresh task"""
        self._stop_refresh = True
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped background token refresh service")
    
    async def _background_refresh_loop(self):
        """Main background loop for token refresh"""
        while not self._stop_refresh:
            try:
                # Check for tokens that need refresh
                tokens_to_refresh = await self._get_tokens_needing_refresh()
                
                if tokens_to_refresh:
                    logger.info(f"Found {len(tokens_to_refresh)} tokens needing refresh")
                    await self._refresh_token_batch(tokens_to_refresh)
                else:
                    logger.debug("No tokens require refresh at this time")
                
                # Wait before next check (every 5 minutes)
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in background refresh loop: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _get_tokens_needing_refresh(self) -> List[OAuthToken]:
        """Get tokens that need to be refreshed"""
        refresh_threshold = datetime.utcnow() + timedelta(minutes=self.refresh_margin_minutes)
        
        try:
            supabase = get_supabase()
            
            # Query oauth_tokens table for tokens needing refresh
            response = supabase.table("oauth_tokens").select("*").filter(
                "expires_at", "lte", refresh_threshold.isoformat()
            ).filter(
                "refresh_token", "not.is", "null"
            ).filter(
                "is_active", "eq", True
            ).limit(self.batch_size).execute()
            
            # Convert to OAuthToken objects
            tokens = []
            for data in response.data or []:
                token = OAuthToken(
                    id=data["id"],
                    user_id=data["user_id"],
                    provider=data["provider"],
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    token_type=data.get("token_type", "Bearer"),
                    scope=data.get("scope"),
                    expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    last_refreshed=datetime.fromisoformat(data["last_refreshed"].replace("Z", "+00:00")) if data.get("last_refreshed") else None,
                    is_active=data.get("is_active", True),
                    encryption_key_version=data.get("encryption_key_version", 1)
                )
                tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Error getting tokens needing refresh: {e}")
            return []
    
    async def _refresh_token_batch(self, tokens: List[OAuthToken]):
        """Refresh a batch of tokens"""
        refresh_tasks = []
        
        for token in tokens:
            task = asyncio.create_task(self._refresh_single_token(token))
            refresh_tasks.append(task)
        
        # Execute all refresh operations concurrently
        results = await asyncio.gather(*refresh_tasks, return_exceptions=True)
        
        # Log results
        success_count = sum(1 for r in results if isinstance(r, RefreshAttempt) and r.result == RefreshResult.SUCCESS)
        logger.info(f"Token refresh batch complete: {success_count}/{len(tokens)} successful")
    
    async def _refresh_single_token(self, token: OAuthToken) -> RefreshAttempt:
        """Refresh a single OAuth token"""
        provider = TokenProvider(token.provider)
        
        attempt = RefreshAttempt(
            user_id=token.user_id,
            provider=provider,
            result=RefreshResult.FAILED,
            timestamp=datetime.utcnow()
        )
        
        try:
            if not token.refresh_token:
                attempt.result = RefreshResult.NO_REFRESH_TOKEN
                attempt.error = "No refresh token available"
                await self._mark_token_expired(token)
                return attempt
            
            oauth_service = self.oauth_services.get(provider)
            if not oauth_service:
                attempt.error = f"No OAuth service available for provider {provider}"
                return attempt
            
            # Attempt token refresh
            refresh_data = await oauth_service.refresh_token(token.refresh_token)
            
            if not refresh_data or not refresh_data.get("access_token"):
                attempt.result = RefreshResult.PROVIDER_ERROR
                attempt.error = "Provider returned invalid refresh response"
                return attempt
            
            # Update token in database
            await self._update_token(token, refresh_data)
            
            attempt.result = RefreshResult.SUCCESS
            attempt.new_expires_at = datetime.utcnow() + timedelta(seconds=refresh_data.get("expires_in", 3600))
            
            logger.info(f"Successfully refreshed token for user {token.user_id} provider {provider}")
            
        except Exception as e:
            attempt.error = str(e)
            logger.error(f"Failed to refresh token for user {token.user_id} provider {provider}: {str(e)}")
            
            # Check if token was revoked
            if "revoked" in str(e).lower() or "invalid_grant" in str(e).lower():
                attempt.result = RefreshResult.TOKEN_REVOKED
                await self._mark_token_expired(token)
        
        # Store attempt in history
        self._add_refresh_attempt(attempt)
        return attempt
    
    async def _update_token(self, token: OAuthToken, refresh_data: Dict[str, Any]):
        """Update token with new refresh data"""
        try:
            supabase = get_supabase()
            
            # Prepare update data
            update_data = {
                "access_token": refresh_data["access_token"],
                "last_refreshed": datetime.utcnow().isoformat()
            }
            
            if "refresh_token" in refresh_data:
                update_data["refresh_token"] = refresh_data["refresh_token"]
            
            expires_in = refresh_data.get("expires_in", 3600)
            new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            update_data["expires_at"] = new_expires_at.isoformat()
            
            if "scope" in refresh_data:
                update_data["scope"] = refresh_data["scope"]
            
            # Update token in Supabase
            response = supabase.table("oauth_tokens").update(update_data).eq("id", token.id).execute()
            
            if not response.data:
                raise Exception("Failed to update token in database")
            
        except Exception as e:
            logger.error(f"Failed to update token {token.id}: {e}")
            raise e
    
    async def _mark_token_expired(self, token: OAuthToken):
        """Mark token as expired/inactive"""
        try:
            supabase = get_supabase()
            
            update_data = {
                "is_active": False,
                "last_refreshed": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("oauth_tokens").update(update_data).eq("id", token.id).execute()
            
            if not response.data:
                raise Exception("Failed to mark token as expired in database")
                
        except Exception as e:
            logger.error(f"Failed to mark token as expired: {str(e)}")
    
    def _add_refresh_attempt(self, attempt: RefreshAttempt):
        """Add refresh attempt to history"""
        self.recent_attempts.append(attempt)
        
        # Keep history limited
        if len(self.recent_attempts) > self.max_attempt_history:
            self.recent_attempts = self.recent_attempts[-self.max_attempt_history:]
    
    async def force_refresh_user_tokens(self, user_id: str, provider: Optional[TokenProvider] = None) -> List[RefreshAttempt]:
        """Force refresh all tokens for a specific user"""
        try:
            supabase = get_supabase()
            
            # Build query
            query = supabase.table("oauth_tokens").select("*").filter(
                "user_id", "eq", user_id
            ).filter(
                "is_active", "eq", True
            ).filter(
                "refresh_token", "not.is", "null"
            )
            
            if provider:
                query = query.filter("provider", "eq", provider.value)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            # Convert to OAuthToken objects
            tokens = []
            for data in response.data:
                token = OAuthToken(
                    id=data["id"],
                    user_id=data["user_id"],
                    provider=data["provider"],
                    access_token=data["access_token"],
                    refresh_token=data.get("refresh_token"),
                    token_type=data.get("token_type", "Bearer"),
                    scope=data.get("scope"),
                    expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
                    created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                    last_refreshed=datetime.fromisoformat(data["last_refreshed"].replace("Z", "+00:00")) if data.get("last_refreshed") else None,
                    is_active=data.get("is_active", True),
                    encryption_key_version=data.get("encryption_key_version", 1)
                )
                tokens.append(token)
            
            # Refresh all tokens
            refresh_tasks = [self._refresh_single_token(token) for token in tokens]
            results = await asyncio.gather(*refresh_tasks, return_exceptions=True)
            
            # Filter out exceptions and return only RefreshAttempt objects
            attempts = [r for r in results if isinstance(r, RefreshAttempt)]
            return attempts
            
        except Exception as e:
            logger.error(f"Error force refreshing tokens for user {user_id}: {e}")
            return []
    
    async def get_token_health(self, user_id: str) -> Dict[str, Any]:
        """Get health status of user's tokens"""
        try:
            supabase = get_supabase()
            
            response = supabase.table("oauth_tokens").select("*").filter(
                "user_id", "eq", user_id
            ).filter(
                "is_active", "eq", True
            ).execute()
            
            tokens_data = response.data or []
            
            health_status = {
                "user_id": user_id,
                "total_tokens": len(tokens_data),
                "tokens_by_provider": {},
                "expiring_soon": [],
                "expired": [],
                "missing_refresh_token": []
            }
            
            now = datetime.utcnow()
            expiry_threshold = now + timedelta(hours=1)
            
            for token_data in tokens_data:
                provider = token_data["provider"]
                expires_at = datetime.fromisoformat(token_data["expires_at"].replace("Z", "+00:00"))
                
                # Count by provider
                if provider not in health_status["tokens_by_provider"]:
                    health_status["tokens_by_provider"][provider] = 0
                health_status["tokens_by_provider"][provider] += 1
                
                # Check token status
                if expires_at <= now:
                    health_status["expired"].append({
                        "provider": provider,
                        "expired_at": expires_at.isoformat()
                    })
                elif expires_at <= expiry_threshold:
                    health_status["expiring_soon"].append({
                        "provider": provider,
                        "expires_at": expires_at.isoformat()
                    })
                
                if not token_data.get("refresh_token"):
                    health_status["missing_refresh_token"].append(provider)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting token health for user {user_id}: {e}")
            return {
                "user_id": user_id,
                "total_tokens": 0,
                "tokens_by_provider": {},
                "expiring_soon": [],
                "expired": [],
                "missing_refresh_token": [],
                "error": str(e)
            }
    
    def get_refresh_metrics(self) -> Dict[str, Any]:
        """Get token refresh service metrics"""
        if not self.recent_attempts:
            return {
                "total_attempts": 0,
                "success_rate": 0,
                "attempts_by_provider": {},
                "attempts_by_result": {}
            }
        
        total_attempts = len(self.recent_attempts)
        successful_attempts = sum(1 for a in self.recent_attempts if a.result == RefreshResult.SUCCESS)
        
        # Count by provider
        by_provider = {}
        for attempt in self.recent_attempts:
            provider = attempt.provider.value
            if provider not in by_provider:
                by_provider[provider] = {"total": 0, "successful": 0}
            by_provider[provider]["total"] += 1
            if attempt.result == RefreshResult.SUCCESS:
                by_provider[provider]["successful"] += 1
        
        # Count by result
        by_result = {}
        for attempt in self.recent_attempts:
            result = attempt.result.value
            by_result[result] = by_result.get(result, 0) + 1
        
        return {
            "total_attempts": total_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "attempts_by_provider": by_provider,
            "attempts_by_result": by_result,
            "background_task_running": self._refresh_task is not None and not self._refresh_task.done()
        }


# Global service instance
token_refresh_service = TokenRefreshService()
