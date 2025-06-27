import { Request, Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import { agentStatusService } from '../services/agentStatusService';
import { AgentStatusUpdate } from '../types/agentStatus';

/**
 * Receive agent status updates from n8n workflows
 * POST /api/agent-status
 */
export const updateAgentStatus = async (req: Request, res: Response): Promise<void> => {
  try {
    const { tool, status, userId, message, metadata }: AgentStatusUpdate = req.body;

    // Validate required fields
    if (!tool || !status || !userId) {
      res.status(400).json({ 
        error: 'Missing required fields: tool, status, userId' 
      });
      return;
    }

    // Validate status values
    const validStatuses = ['active', 'completed', 'error', 'idle'];
    if (!validStatuses.includes(status)) {
      res.status(400).json({ 
        error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` 
      });
      return;
    }

    // Add to queue for processing
    await agentStatusService.addStatusUpdate({
      tool,
      status,
      userId,
      message,
      metadata,
      timestamp: new Date().toISOString(),
    });

    res.json({ 
      success: true, 
      message: 'Agent status update queued successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error updating agent status:', error);
    res.status(500).json({ 
      error: 'Failed to update agent status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Get current agent status for authenticated user
 * GET /api/agent-status
 */
export const getAgentStatus = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  try {
    const userId = req.user?.id;

    if (!userId) {
      res.status(401).json({ error: 'User not authenticated' });
      return;
    }

    const userStatus = agentStatusService.getUserStatus(userId);

    if (!userStatus) {
      res.json({
        userId,
        status: 'idle',
        currentTool: null,
        lastUpdate: new Date().toISOString(),
        toolHistory: [],
      });
      return;
    }

    res.json(userStatus);
  } catch (error) {
    console.error('Error getting agent status:', error);
    res.status(500).json({ 
      error: 'Failed to get agent status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Get agent status for specific user (admin only)
 * GET /api/agent-status/:userId
 */
export const getAgentStatusForUser = async (req: AuthenticatedRequest & { params: { userId: string } }, res: Response): Promise<void> => {
  try {
    const { userId } = req.params;
    const requestingUserId = req.user?.id;

    if (!requestingUserId) {
      res.status(401).json({ error: 'User not authenticated' });
      return;
    }

    // For now, only allow users to see their own status
    // Later you can add admin role checking here
    if (requestingUserId !== userId) {
      res.status(403).json({ error: 'Access denied' });
      return;
    }

    const userStatus = agentStatusService.getUserStatus(userId);

    if (!userStatus) {
      res.json({
        userId,
        status: 'idle',
        currentTool: null,
        lastUpdate: new Date().toISOString(),
        toolHistory: [],
      });
      return;
    }

    res.json(userStatus);
  } catch (error) {
    console.error('Error getting agent status for user:', error);
    res.status(500).json({ 
      error: 'Failed to get agent status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Get queue statistics (admin/monitoring)
 * GET /api/agent-status/stats
 */
export const getAgentStatusStats = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  try {
    const userId = req.user?.id;

    if (!userId) {
      res.status(401).json({ error: 'User not authenticated' });
      return;
    }

    // For now, allow any authenticated user to see stats
    // Later you can add admin role checking here
    const stats = agentStatusService.getQueueStats();

    res.json({
      ...stats,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error getting agent status stats:', error);
    res.status(500).json({ 
      error: 'Failed to get agent status stats',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Clear agent status for authenticated user
 * DELETE /api/agent-status
 */
export const clearAgentStatus = async (req: AuthenticatedRequest, res: Response): Promise<void> => {
  try {
    const userId = req.user?.id;

    if (!userId) {
      res.status(401).json({ error: 'User not authenticated' });
      return;
    }

    agentStatusService.clearUserStatus(userId);

    res.json({ 
      success: true, 
      message: 'Agent status cleared successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error clearing agent status:', error);
    res.status(500).json({ 
      error: 'Failed to clear agent status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}; 