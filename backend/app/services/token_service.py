from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from app.config.supabase import get_supabase
from app.config.redis import redis_client
from app.security.encryption import encryption_service
from app.models.oauth_tokens import (
    OAuthToken, OAuthTokenCreate, OAuthTokenUpdate,
    TokenPair, UserTokens, TokenRefreshResult, TokenValidationResult,
    ConnectionStatus, Provider
)

logger = logging.getLogger(__name__)

class TokenService:
    """
    Token service for managing OAuth tokens (matching Node.js tokenService)
    Handles encryption, storage, and refresh of OAuth tokens
    """
    
    def __init__(self):
        self.supabase = None
        
    def _get_supabase(self):
        """Get Supabase client"""
        if not self.supabase:
            self.supabase = get_supabase()
        return self.supabase
    
    async def get_user_connected_accounts(self, user_id: str) -> List[OAuthToken]:
        """Get all connected accounts for a user (matching Node.js method)"""
        try:
            supabase = self._get_supabase()
            
            result = supabase.table('oauth_tokens').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                connections = []
                for row in result.data:
                    # Decrypt tokens for internal use
                    decrypted_access = encryption_service.decrypt_token(
                        row['access_token'], user_id
                    )
                    decrypted_refresh = None
                    if row.get('refresh_token'):
                        decrypted_refresh = encryption_service.decrypt_token(
                            row['refresh_token'], user_id
                        )
                    
                    # Convert to model
                    connection = OAuthToken(
                        id=row['id'],
                        user_id=row['user_id'],
                        provider=Provider(row['provider']),
                        access_token=decrypted_access,
                        refresh_token=decrypted_refresh,
                        expires_at=datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00')) if row.get('expires_at') else None,
                        scopes=row.get('scopes', []),
                        email=row.get('email'),
                        created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
                    )
                    connections.append(connection)
                
                return connections
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching connected accounts for user {user_id}: {e}")
            raise
    
    async def get_user_tokens_for_agent(self, user_id: str) -> UserTokens:
        """Get tokens formatted for agent API calls (matching Node.js method)"""
        try:
            # Check cache first
            cached_tokens = await redis_client.get_cached_user_tokens(user_id)
            if cached_tokens:
                return self._deserialize_user_tokens_from_cache(cached_tokens)
            
            accounts = await self.get_user_connected_accounts(user_id)
            user_tokens = UserTokens(user_id=user_id)
            
            for account in accounts:
                # Validate and refresh tokens if needed
                validation = await self._validate_token(account)
                
                token_pair = TokenPair(
                    access_token=account.access_token,
                    refresh_token=account.refresh_token,
                    expires_at=account.expires_at,
                    scopes=account.scopes
                )
                
                # Refresh token if needed
                if validation.needs_refresh and account.refresh_token:
                    refresh_result = await self._refresh_user_token(
                        user_id, account.provider.value, account.refresh_token
                    )
                    if refresh_result.success and refresh_result.tokens:
                        token_pair = refresh_result.tokens
                
                # Add to user tokens based on provider
                if account.provider == Provider.GOOGLE:
                    user_tokens.google = token_pair
                elif account.provider == Provider.MICROSOFT:
                    user_tokens.microsoft = token_pair
                elif account.provider == Provider.CANVAS:
                    user_tokens.canvas = token_pair
                elif account.provider == Provider.NOTION:
                    user_tokens.notion = token_pair
            
            # Cache the result with proper datetime serialization
            cache_data = self._serialize_user_tokens_for_cache(user_tokens)
            await redis_client.cache_user_tokens(user_id, cache_data, ttl=300)  # 5 minutes
            
            return user_tokens
            
        except Exception as e:
            logger.error(f"Error getting tokens for agent for user {user_id}: {e}")
            return UserTokens(user_id=user_id)  # Return empty tokens on error
    
    def _serialize_user_tokens_for_cache(self, user_tokens: UserTokens) -> dict:
        """Serialize UserTokens for caching with proper datetime handling"""
        cache_data = {
            "user_id": user_tokens.user_id,
            "google": None,
            "microsoft": None,
            "canvas": None,
            "notion": None
        }
        
        # Serialize each provider's tokens
        for provider in ["google", "microsoft", "canvas", "notion"]:
            token_pair = getattr(user_tokens, provider)
            if token_pair:
                cache_data[provider] = {
                    "access_token": token_pair.access_token,
                    "refresh_token": token_pair.refresh_token,
                    "expires_at": token_pair.expires_at.isoformat() if token_pair.expires_at else None,
                    "scopes": token_pair.scopes
                }
        
        return cache_data

    def _deserialize_user_tokens_from_cache(self, cached_data: dict) -> UserTokens:
        """Deserialize cached UserTokens with proper datetime handling"""
        user_tokens = UserTokens(user_id=cached_data["user_id"])
        
        # Deserialize each provider's tokens
        for provider in ["google", "microsoft", "canvas", "notion"]:
            token_data = cached_data.get(provider)
            if token_data:
                token_pair = TokenPair(
                    access_token=token_data["access_token"],
                    refresh_token=token_data.get("refresh_token"),
                    expires_at=datetime.fromisoformat(token_data["expires_at"].replace('Z', '+00:00')) if token_data.get("expires_at") else None,
                    scopes=token_data.get("scopes", [])
                )
                setattr(user_tokens, provider, token_pair)
        
        return user_tokens

    async def _validate_token(self, account: OAuthToken) -> TokenValidationResult:
        """Validate if a token is still valid (matching Node.js method)"""
        try:
            # Check if token is expired based on expires_at
            is_expired = False
            if account.expires_at:
                is_expired = account.expires_at <= datetime.now(timezone.utc)
            
            if is_expired:
                return TokenValidationResult(
                    is_valid=False,
                    needs_refresh=True
                )
            
            # For additional validation, you could make a test API call here
            # For now, we'll trust the expires_at timestamp
            return TokenValidationResult(
                is_valid=True,
                needs_refresh=False
            )
            
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return TokenValidationResult(
                is_valid=False,
                needs_refresh=True,
                error=str(e)
            )
    
    async def _refresh_user_token(self, user_id: str, provider: str, refresh_token: str) -> TokenRefreshResult:
        """Refresh a user's token for a specific provider (matching Node.js method)"""
        try:
            new_tokens = None
            
            if provider == "google":
                new_tokens = await self._refresh_google_token(refresh_token)
            elif provider == "microsoft":
                new_tokens = await self._refresh_microsoft_token(refresh_token)
            else:
                return TokenRefreshResult(success=False, error=f"Unsupported provider: {provider}")
            
            if not new_tokens:
                return TokenRefreshResult(success=False, error="Failed to refresh token")
            
            # Update tokens in database
            supabase = self._get_supabase()
            
            update_data = {
                'access_token': encryption_service.encrypt_token(new_tokens['access_token'], user_id),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if new_tokens.get('refresh_token'):
                update_data['refresh_token'] = encryption_service.encrypt_token(
                    new_tokens['refresh_token'], user_id
                )
            
            if new_tokens.get('expires_at'):
                update_data['expires_at'] = new_tokens['expires_at']
            
            result = supabase.table('oauth_tokens').update(update_data).eq(
                'user_id', user_id
            ).eq('provider', provider).execute()
            
            if result.data:
                logger.info(f"Successfully refreshed {provider} token for user {user_id}")
                
                # Invalidate user cache
                await redis_client.invalidate_user_cache(user_id)
                
                return TokenRefreshResult(
                    success=True,
                    tokens=TokenPair(
                        access_token=new_tokens['access_token'],
                        refresh_token=new_tokens.get('refresh_token'),
                        expires_at=datetime.fromisoformat(new_tokens['expires_at'].replace('Z', '+00:00')) if new_tokens.get('expires_at') else None,
                        scopes=new_tokens.get('scopes', [])
                    )
                )
            else:
                return TokenRefreshResult(success=False, error="Failed to update tokens in database")
                
        except Exception as e:
            logger.error(f"Error refreshing {provider} token for user {user_id}: {e}")
            return TokenRefreshResult(success=False, error=str(e))
    
    async def _refresh_google_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Google OAuth token"""
        from app.services.oauth_providers import OAuthProviderFactory
        provider = OAuthProviderFactory.get_provider("google")
        return await provider.refresh_token(refresh_token)
    
    async def _refresh_microsoft_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh Microsoft OAuth token"""
        from app.services.oauth_providers import OAuthProviderFactory
        provider = OAuthProviderFactory.get_provider("microsoft")
        return await provider.refresh_token(refresh_token)
    
    async def store_user_tokens(
        self, 
        user_id: str, 
        provider: str, 
        tokens: OAuthTokenCreate
    ) -> str:
        """Store new tokens for a user (matching Node.js method)"""
        try:
            supabase = self._get_supabase()
            
            # Encrypt tokens before storage
            encrypted_access = encryption_service.encrypt_token(tokens.access_token, user_id)
            encrypted_refresh = None
            if tokens.refresh_token:
                encrypted_refresh = encryption_service.encrypt_token(tokens.refresh_token, user_id)
            
            data = {
                'user_id': user_id,
                'provider': provider,
                'access_token': encrypted_access,
                'refresh_token': encrypted_refresh,
                'expires_at': tokens.expires_at.isoformat() if tokens.expires_at else None,
                'scopes': tokens.scopes,
                'email': tokens.email
            }
            
            # Check if connection already exists
            existing = supabase.table('oauth_tokens').select('*').eq(
                'user_id', user_id
            ).eq('provider', provider).execute()
            
            if existing.data:
                # Update existing connection
                result = supabase.table('oauth_tokens').update(data).eq(
                    'id', existing.data[0]['id']
                ).execute()
            else:
                # Insert new connection
                result = supabase.table('oauth_tokens').insert(data).execute()
            
            if result.data:
                logger.info(f"Successfully stored {provider} tokens for user {user_id}")
                
                # Invalidate user cache
                await redis_client.invalidate_user_cache(user_id)
                
                return result.data[0]['id']
            else:
                raise Exception("Failed to store tokens")
                
        except Exception as e:
            logger.error(f"Error storing tokens for user {user_id}: {e}")
            raise
    
    async def remove_user_tokens(self, user_id: str, provider: str) -> bool:
        """Remove tokens for a user and provider (matching Node.js method)"""
        try:
            supabase = self._get_supabase()
            
            result = supabase.table('oauth_tokens').delete().eq(
                'user_id', user_id
            ).eq('provider', provider).execute()
            
            if result.data is not None:  # Successful deletion
                logger.info(f"Successfully removed {provider} tokens for user {user_id}")
                
                # Invalidate user cache
                await redis_client.invalidate_user_cache(user_id)
                
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error removing tokens for user {user_id}: {e}")
            return False
    
    async def has_provider_connected(self, user_id: str, provider: str) -> bool:
        """Check if user has connected a specific provider (matching Node.js method)"""
        try:
            supabase = self._get_supabase()
            
            result = supabase.table('oauth_tokens').select('id').eq(
                'user_id', user_id
            ).eq('provider', provider).limit(1).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking provider connection for user {user_id}: {e}")
            return False
    
    async def get_user_connection_status(self, user_id: str) -> ConnectionStatus:
        """Get connection status for all providers (matching Node.js method)"""
        try:
            accounts = await self.get_user_connected_accounts(user_id)
            providers = [account.provider.value for account in accounts]
            
            return ConnectionStatus(
                google=Provider.GOOGLE.value in providers,
                microsoft=Provider.MICROSOFT.value in providers,
                canvas=Provider.CANVAS.value in providers,
                notion=Provider.NOTION.value in providers
            )
            
        except Exception as e:
            logger.error(f"Error getting connection status for user {user_id}: {e}")
            return ConnectionStatus()
    
    async def has_calendar_access(self, user_id: str, provider: str = "google") -> bool:
        """Check if user has calendar access for specific provider"""
        try:
            user_tokens = await self.get_user_tokens_for_agent(user_id)
            
            if provider == "google" and user_tokens.google:
                calendar_scopes = [
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.readonly',
                    'calendar'
                ]
                return any(scope in user_tokens.google.scopes for scope in calendar_scopes)
            
            elif provider == "microsoft" and user_tokens.microsoft:
                calendar_scopes = [
                    'https://graph.microsoft.com/calendars.readwrite',
                    'https://graph.microsoft.com/calendars.read',
                    'calendars.readwrite'
                ]
                return any(scope in user_tokens.microsoft.scopes for scope in calendar_scopes)
            
            return False
        except Exception as e:
            logger.error(f"Error checking calendar access for user {user_id}: {e}")
            return False
    
    async def has_email_access(self, user_id: str, provider: str = "google") -> bool:
        """Check if user has email access for specific provider"""
        try:
            user_tokens = await self.get_user_tokens_for_agent(user_id)
            
            if provider == "google" and user_tokens.google:
                email_scopes = [
                    'https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'gmail.send', 'gmail.readonly'
                ]
                return any(scope in user_tokens.google.scopes for scope in email_scopes)
            
            elif provider == "microsoft" and user_tokens.microsoft:
                email_scopes = [
                    'https://graph.microsoft.com/mail.send',
                    'https://graph.microsoft.com/mail.read',
                    'mail.send', 'mail.read'
                ]
                return any(scope in user_tokens.microsoft.scopes for scope in email_scopes)
            
            return False
        except Exception as e:
            logger.error(f"Error checking email access for user {user_id}: {e}")
            return False
    
    async def has_contacts_access(self, user_id: str, provider: str = "google") -> bool:
        """Check if user has contacts access for specific provider"""
        try:
            user_tokens = await self.get_user_tokens_for_agent(user_id)
            
            if provider == "google" and user_tokens.google:
                contacts_scopes = [
                    'https://www.googleapis.com/auth/contacts.readonly',
                    'https://www.googleapis.com/auth/contacts',
                    'contacts.readonly', 'contacts'
                ]
                return any(scope in user_tokens.google.scopes for scope in contacts_scopes)
            
            elif provider == "microsoft" and user_tokens.microsoft:
                # Microsoft uses People API for contacts
                contacts_scopes = [
                    'https://graph.microsoft.com/people.read',
                    'https://graph.microsoft.com/contacts.read',
                    'people.read', 'contacts.read'
                ]
                return any(scope in user_tokens.microsoft.scopes for scope in contacts_scopes)
            
            return False
        except Exception as e:
            logger.error(f"Error checking contacts access for user {user_id}: {e}")
            return False

# Global token service instance
token_service = TokenService()

def get_token_service() -> TokenService:
    """Get the global token service instance"""
    return token_service