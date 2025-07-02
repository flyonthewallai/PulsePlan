import express from 'express';
import { authenticate } from '../middleware/authenticate';
import {
  getConnectionStatus,
  getConnectedAccounts,
  disconnectProvider,
  testAgentConnection,
  refreshUserTokens
} from '../controllers/connectionController';

const router = express.Router();

/**
 * @route   GET /connections/status/:userId
 * @desc    Get connection status for all providers for a user
 * @access  Private
 */
router.get('/status/:userId', authenticate, getConnectionStatus);

/**
 * @route   GET /connections/accounts/:userId
 * @desc    Get detailed connected accounts for a user
 * @access  Private
 */
router.get('/accounts/:userId', authenticate, getConnectedAccounts);

/**
 * @route   DELETE /connections/:provider/:userId
 * @desc    Disconnect a specific provider for a user
 * @access  Private
 */
router.delete('/:provider/:userId', authenticate, disconnectProvider);

/**
 * @route   POST /connections/test-agent/:userId
 * @desc    Test agent service with user's tokens
 * @access  Private
 */
router.post('/test-agent/:userId', authenticate, testAgentConnection);

/**
 * @route   POST /connections/refresh-tokens/:userId
 * @desc    Manually refresh tokens for a user
 * @access  Private
 */
router.post('/refresh-tokens/:userId', authenticate, refreshUserTokens);

export default router; 