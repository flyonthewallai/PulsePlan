import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import { tokenService } from '../services/tokenService';
import { enhancedAgentService } from '../services/enhancedAgentService';
import { logger } from '../../jobs/utils/logger';

/**
 * GET /connections/status/:userId
 * Get connection status for all providers for a user
 */
export const getConnectionStatus = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = (req as any).params;

  if (!userId) {
    res.status(400).json({ error: 'User ID is required' });
    return;
  }

  try {
    const connectionStatus = await enhancedAgentService.getUserConnectionStatus(userId);
    
    res.json({
      success: true,
      data: {
        userId,
        connections: connectionStatus,
        hasAnyConnections: Object.values(connectionStatus).some(status => status)
      }
    });
  } catch (error) {
    logger.error(`Error getting connection status for user ${userId}`, error);
    res.status(500).json({
      error: 'Failed to get connection status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * GET /connections/accounts/:userId
 * Get detailed connected accounts for a user (sanitized)
 */
export const getConnectedAccounts = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = (req as any).params;

  if (!userId) {
    res.status(400).json({ error: 'User ID is required' });
    return;
  }

  try {
    const accounts = await tokenService.getUserConnectedAccounts(userId);
    
    // Sanitize sensitive data before sending to client
    const sanitizedAccounts = accounts.map(account => ({
      provider: account.provider,
      email: account.email,
      scopes: account.scopes,
      connected_at: account.created_at,
      last_updated: account.updated_at,
      // Don't include actual tokens for security
      has_access_token: !!account.access_token,
      has_refresh_token: !!account.refresh_token,
      expires_at: account.expires_at
    }));

    res.json({
      success: true,
      data: {
        userId,
        accounts: sanitizedAccounts
      }
    });
  } catch (error) {
    logger.error(`Error getting connected accounts for user ${userId}`, error);
    res.status(500).json({
      error: 'Failed to get connected accounts',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * DELETE /connections/:provider/:userId
 * Disconnect a specific provider for a user
 */
export const disconnectProvider = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { provider, userId } = (req as any).params;

  if (!provider || !userId) {
    res.status(400).json({ error: 'Provider and user ID are required' });
    return;
  }

  if (!['google', 'microsoft', 'canvas', 'notion'].includes(provider)) {
    res.status(400).json({ error: 'Invalid provider' });
    return;
  }

  try {
    await tokenService.removeUserTokens(userId, provider);
    
    res.json({
      success: true,
      message: `Successfully disconnected ${provider} for user ${userId}`
    });
  } catch (error) {
    logger.error(`Error disconnecting ${provider} for user ${userId}`, error);
    res.status(500).json({
      error: 'Failed to disconnect provider',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * POST /connections/test-agent/:userId
 * Test agent service with user's tokens
 */
export const testAgentConnection = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = (req as any).params;

  if (!userId) {
    res.status(400).json({ error: 'User ID is required' });
    return;
  }

  try {
    // Check if user has any connected accounts
    const hasConnections = await enhancedAgentService.hasConnectedAccounts(userId);
    
    if (!hasConnections) {
      res.json({
        success: true,
        data: {
          userId,
          hasConnections: false,
          message: 'No connected accounts found'
        }
      });
      return;
    }

    // Test agent health
    const agentHealthy = await enhancedAgentService.healthCheck();
    
    // Get connection status
    const connectionStatus = await enhancedAgentService.getUserConnectionStatus(userId);

    res.json({
      success: true,
      data: {
        userId,
        hasConnections: true,
        agentHealthy,
        connectionStatus,
        message: agentHealthy ? 
          'Agent service is healthy and tokens are available' : 
          'Agent service is not responding'
      }
    });
  } catch (error) {
    logger.error(`Error testing agent connection for user ${userId}`, error);
    res.status(500).json({
      error: 'Failed to test agent connection',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * POST /connections/refresh-tokens/:userId
 * Manually refresh tokens for a user
 */
export const refreshUserTokens = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  const { userId } = (req as any).params;
  const { provider } = req.body;

  if (!userId) {
    res.status(400).json({ error: 'User ID is required' });
    return;
  }

  try {
    if (provider) {
      // Refresh specific provider
      if (!['google', 'microsoft', 'canvas', 'notion'].includes(provider)) {
        res.status(400).json({ error: 'Invalid provider' });
        return;
      }

      const hasProvider = await tokenService.hasProviderConnected(userId, provider);
      if (!hasProvider) {
        res.status(404).json({ error: `${provider} not connected for this user` });
        return;
      }

      // Force refresh by getting tokens (this will refresh if needed)
      await tokenService.getUserTokensForAgent(userId);
      
      res.json({
        success: true,
        message: `Successfully refreshed ${provider} tokens for user ${userId}`
      });
    } else {
      // Refresh all providers
      await tokenService.getUserTokensForAgent(userId);
      
      res.json({
        success: true,
        message: `Successfully refreshed all tokens for user ${userId}`
      });
    }
  } catch (error) {
    logger.error(`Error refreshing tokens for user ${userId}`, error);
    res.status(500).json({
      error: 'Failed to refresh tokens',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}; 