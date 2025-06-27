import { Router } from 'express';
import { authenticate } from '../middleware/authenticate';
import {
  updateAgentStatus,
  getAgentStatus,
  getAgentStatusForUser,
  getAgentStatusStats,
  clearAgentStatus,
} from '../controllers/agentStatusController';

const router = Router();

/**
 * POST /api/agent-status
 * Receive status updates from n8n workflows
 * No authentication required (n8n will send directly)
 */
router.post('/', updateAgentStatus);

/**
 * GET /api/agent-status
 * Get current agent status for authenticated user
 */
router.get('/', authenticate, getAgentStatus);

/**
 * GET /api/agent-status/stats
 * Get queue statistics (admin/monitoring)
 */
router.get('/stats', authenticate, getAgentStatusStats);

/**
 * GET /api/agent-status/:userId
 * Get agent status for specific user
 */
router.get('/:userId', authenticate, getAgentStatusForUser);

/**
 * DELETE /api/agent-status
 * Clear agent status for authenticated user
 */
router.delete('/', authenticate, clearAgentStatus);

export default router; 