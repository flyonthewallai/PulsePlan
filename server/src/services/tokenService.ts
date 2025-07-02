import crypto from 'crypto';
import supabase from '../config/supabase';
import { getOAuth2Client } from '../config/google';
import { getAccessTokenWithRefreshToken } from '../config/microsoft';
import { ConnectedAccount, TokenPair, UserTokens, TokenRefreshResult, TokenValidationResult } from '../types/tokens';
import { logger } from '../../jobs/utils/logger';

class TokenService {
  private readonly encryptionKey: string;

  constructor() {
    // Use environment variable for encryption key, fallback to a default for development
    this.encryptionKey = process.env.TOKEN_ENCRYPTION_KEY || 'fallback-key-for-development-only';
    
    if (this.encryptionKey === 'fallback-key-for-development-only') {
      logger.warn('Using fallback encryption key. Set TOKEN_ENCRYPTION_KEY in production!');
    }
  }

  /**
   * Encrypt sensitive token data
   */
  private encrypt(text: string): string {
    if (!text) return text;
    
    try {
      const algorithm = 'aes-256-gcm';
      const key = crypto.scryptSync(this.encryptionKey, 'salt', 32);
      const iv = crypto.randomBytes(16);
      const cipher = crypto.createCipheriv(algorithm, key, iv);
      
      let encrypted = cipher.update(text, 'utf8', 'hex');
      encrypted += cipher.final('hex');
      
      const authTag = cipher.getAuthTag();
      return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
    } catch (error) {
      logger.error('Error encrypting token', error);
      return text; // Return unencrypted in case of error
    }
  }

  /**
   * Decrypt sensitive token data
   */
  private decrypt(encryptedText: string): string {
    if (!encryptedText || !encryptedText.includes(':')) return encryptedText;
    
    try {
      const algorithm = 'aes-256-gcm';
      const key = crypto.scryptSync(this.encryptionKey, 'salt', 32);
      const parts = encryptedText.split(':');
      
      if (parts.length !== 3) return encryptedText; // Invalid format
      
      const [ivHex, authTagHex, encrypted] = parts;
      const iv = Buffer.from(ivHex, 'hex');
      const authTag = Buffer.from(authTagHex, 'hex');
      const decipher = crypto.createDecipheriv(algorithm, key, iv);
      decipher.setAuthTag(authTag);
      
      let decrypted = decipher.update(encrypted, 'hex', 'utf8');
      decrypted += decipher.final('utf8');
      
      return decrypted;
    } catch (error) {
      logger.error('Error decrypting token', error);
      return encryptedText; // Return as-is in case of error
    }
  }

  /**
   * Get all connected accounts for a user
   */
  async getUserConnectedAccounts(userId: string): Promise<ConnectedAccount[]> {
    if (!supabase) {
      throw new Error('Supabase client not available');
    }

    try {
      const { data, error } = await supabase
        .from('calendar_connections')
        .select('*')
        .eq('user_id', userId);

      if (error) {
        logger.error('Error fetching connected accounts', error);
        throw error;
      }

      // Decrypt tokens for internal use
      return (data || []).map(account => ({
        ...account,
        access_token: this.decrypt(account.access_token),
        refresh_token: account.refresh_token ? this.decrypt(account.refresh_token) : undefined
      }));
    } catch (error) {
      logger.error(`Error in getUserConnectedAccounts for user ${userId}`, error);
      throw error;
    }
  }

  /**
   * Get tokens formatted for agent API calls
   */
  async getUserTokensForAgent(userId: string): Promise<UserTokens> {
    try {
      const accounts = await this.getUserConnectedAccounts(userId);
      const userTokens: UserTokens = { userId };

      for (const account of accounts) {
        // Validate and refresh tokens if needed
        const validation = await this.validateToken(account);
        
        let tokenPair: TokenPair = {
          access_token: account.access_token,
          refresh_token: account.refresh_token,
          expires_at: account.expires_at,
          scopes: account.scopes
        };

        // Refresh token if needed
        if (validation.needsRefresh && account.refresh_token) {
          const refreshResult = await this.refreshUserToken(userId, account.provider, account.refresh_token);
          if (refreshResult.success && refreshResult.tokens) {
            tokenPair = refreshResult.tokens;
          }
        }

        // Add to user tokens based on provider
        switch (account.provider) {
          case 'google':
            userTokens.google = tokenPair;
            break;
          case 'microsoft':
            userTokens.microsoft = tokenPair;
            break;
          case 'canvas':
            userTokens.canvas = tokenPair;
            break;
          case 'notion':
            userTokens.notion = tokenPair;
            break;
        }
      }

      return userTokens;
    } catch (error) {
      logger.error(`Error in getUserTokensForAgent for user ${userId}`, error);
      return { userId }; // Return empty tokens object if error
    }
  }

  /**
   * Validate if a token is still valid
   */
  private async validateToken(account: ConnectedAccount): Promise<TokenValidationResult> {
    try {
      // Check if token is expired based on expires_at
      const isExpired = account.expires_at ? new Date(account.expires_at) <= new Date() : false;
      
      if (isExpired) {
        return {
          isValid: false,
          needsRefresh: true
        };
      }

      // For additional validation, you could make a test API call here
      // For now, we'll trust the expires_at timestamp

      return {
        isValid: true,
        needsRefresh: false
      };
    } catch (error) {
      logger.error('Error validating token', error);
      return {
        isValid: false,
        needsRefresh: true,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Refresh a user's token for a specific provider
   */
  private async refreshUserToken(userId: string, provider: string, refreshToken: string): Promise<TokenRefreshResult> {
    try {
      let newTokens: any = null;

      switch (provider) {
        case 'google':
          newTokens = await this.refreshGoogleToken(refreshToken);
          break;
        case 'microsoft':
          newTokens = await this.refreshMicrosoftToken(refreshToken);
          break;
        default:
          return { success: false, error: `Unsupported provider: ${provider}` };
      }

      if (!newTokens) {
        return { success: false, error: 'Failed to refresh token' };
      }

      // Update tokens in database
      const updateData: any = {
        access_token: this.encrypt(newTokens.access_token),
        updated_at: new Date().toISOString()
      };

      if (newTokens.refresh_token) {
        updateData.refresh_token = this.encrypt(newTokens.refresh_token);
      }

      if (newTokens.expires_at) {
        updateData.expires_at = newTokens.expires_at;
      }

      const { error } = await supabase!
        .from('calendar_connections')
        .update(updateData)
        .eq('user_id', userId)
        .eq('provider', provider);

      if (error) {
        logger.error('Error updating refreshed tokens', error);
        return { success: false, error: 'Failed to update tokens in database' };
      }

      logger.info(`Successfully refreshed ${provider} token for user ${userId}`);

      return {
        success: true,
        tokens: {
          access_token: newTokens.access_token,
          refresh_token: newTokens.refresh_token,
          expires_at: newTokens.expires_at,
          scopes: newTokens.scopes || []
        }
      };
    } catch (error) {
      logger.error(`Error refreshing ${provider} token for user ${userId}`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Refresh Google OAuth token
   */
  private async refreshGoogleToken(refreshToken: string): Promise<any> {
    try {
      const oauth2Client = getOAuth2Client();
      oauth2Client.setCredentials({
        refresh_token: refreshToken
      });

      const refreshResponse = await oauth2Client.refreshAccessToken();
      const tokens = refreshResponse.credentials;

      return {
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token || refreshToken,
        expires_at: tokens.expiry_date ? new Date(tokens.expiry_date).toISOString() : null
      };
    } catch (error) {
      logger.error('Error refreshing Google token', error);
      throw error;
    }
  }

  /**
   * Refresh Microsoft OAuth token
   */
  private async refreshMicrosoftToken(refreshToken: string): Promise<any> {
    try {
      const tokenResponse = await getAccessTokenWithRefreshToken(refreshToken);

      if (!tokenResponse) {
        throw new Error('Failed to refresh Microsoft token');
      }

      return {
        access_token: tokenResponse.accessToken,
        refresh_token: (tokenResponse as any).refreshToken || refreshToken,
        expires_at: tokenResponse.expiresOn ? new Date(tokenResponse.expiresOn).toISOString() : null
      };
    } catch (error) {
      logger.error('Error refreshing Microsoft token', error);
      throw error;
    }
  }

  /**
   * Store new tokens for a user (used during OAuth flow)
   */
  async storeUserTokens(
    userId: string,
    provider: string,
    tokens: {
      access_token: string;
      refresh_token?: string;
      expires_at?: string;
      scopes: string[];
      email?: string;
    }
  ): Promise<void> {
    if (!supabase) {
      throw new Error('Supabase client not available');
    }

    try {
      const { error } = await supabase
        .from('calendar_connections')
        .upsert({
          user_id: userId,
          provider,
          access_token: this.encrypt(tokens.access_token),
          refresh_token: tokens.refresh_token ? this.encrypt(tokens.refresh_token) : null,
          expires_at: tokens.expires_at,
          scopes: tokens.scopes,
          email: tokens.email
        }, {
          onConflict: 'user_id,provider'
        });

      if (error) {
        logger.error('Error storing tokens', error);
        throw error;
      }

      logger.info(`Successfully stored ${provider} tokens for user ${userId}`);
    } catch (error) {
      logger.error(`Error in storeUserTokens for user ${userId}`, error);
      throw error;
    }
  }

  /**
   * Remove tokens for a user and provider
   */
  async removeUserTokens(userId: string, provider: string): Promise<void> {
    if (!supabase) {
      throw new Error('Supabase client not available');
    }

    try {
      const { error } = await supabase
        .from('calendar_connections')
        .delete()
        .eq('user_id', userId)
        .eq('provider', provider);

      if (error) {
        logger.error('Error removing tokens', error);
        throw error;
      }

      logger.info(`Successfully removed ${provider} tokens for user ${userId}`);
    } catch (error) {
      logger.error(`Error in removeUserTokens for user ${userId}`, error);
      throw error;
    }
  }

  /**
   * Check if user has connected a specific provider
   */
  async hasProviderConnected(userId: string, provider: string): Promise<boolean> {
    try {
      if (!supabase) return false;

      const { data, error } = await supabase
        .from('calendar_connections')
        .select('id')
        .eq('user_id', userId)
        .eq('provider', provider)
        .single();

      return !error && !!data;
    } catch (error) {
      logger.error(`Error checking provider connection for user ${userId}`, error);
      return false;
    }
  }

  /**
   * Get connection status for all providers for a user
   */
  async getUserConnectionStatus(userId: string): Promise<{
    google: boolean;
    microsoft: boolean;
    canvas: boolean;
    notion: boolean;
  }> {
    try {
      const accounts = await this.getUserConnectedAccounts(userId);
      const providers = accounts.map(account => account.provider);

      return {
        google: providers.includes('google'),
        microsoft: providers.includes('microsoft'),
        canvas: providers.includes('canvas'),
        notion: providers.includes('notion')
      };
    } catch (error) {
      logger.error(`Error getting connection status for user ${userId}`, error);
      return {
        google: false,
        microsoft: false,
        canvas: false,
        notion: false
      };
    }
  }
}

export const tokenService = new TokenService(); 