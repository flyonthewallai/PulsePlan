import express from 'express';
import { 
  initiateGoogleAuth,
  handleGoogleCallback,
  disconnectGoogle
} from '../controllers/googleAuthController';

const router = express.Router();

/**
 * Gmail OAuth Routes
 * These use the same Google OAuth infrastructure but are specifically for Gmail access
 */

/**
 * @route   GET /gmail/auth
 * @desc    Initiate Google OAuth flow specifically for Gmail
 * @access  Public
 */
router.get('/auth', (req, res) => {
  // Add a source parameter to track that this is from Gmail settings
  req.query.source = 'gmail';
  initiateGoogleAuth(req, res);
});

/**
 * @route   GET /gmail/auth/callback
 * @desc    Handle Google OAuth callback for Gmail
 * @access  Public
 */
router.get('/auth/callback', handleGoogleCallback);

/**
 * @route   DELETE /gmail/disconnect/:userId
 * @desc    Disconnect Gmail integration
 * @access  Private
 */
router.delete('/disconnect/:userId', disconnectGoogle);

/**
 * @route   GET /gmail/status/:userId
 * @desc    Get Gmail connection status
 * @access  Private
 */
router.get('/status/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    
    // Use the same connection status logic as calendar
    const baseUrl = process.env.NODE_ENV === 'production' 
      ? 'https://api.pulseplan.app' 
      : `http://localhost:${process.env.PORT || 5000}`;
    const response = await fetch(`${baseUrl}/calendar/status/${userId}`);
    const status = await response.json();
    
    // Filter to only show Google connections and add Gmail-specific messaging
    const gmailStatus = {
      connected: status.providers?.some((p: any) => p.provider === 'google' && p.isActive) || false,
      providers: status.providers?.filter((p: any) => p.provider === 'google') || []
    };
    
    res.json(gmailStatus);
  } catch (error) {
    console.error('Error getting Gmail status:', error);
    res.status(500).json({ error: 'Failed to get Gmail connection status' });
  }
});

export default router; 