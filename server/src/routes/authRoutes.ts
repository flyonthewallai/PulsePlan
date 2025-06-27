import express from 'express';
import rateLimit from 'express-rate-limit';
import { 
  initiateGoogleAuth,
  handleGoogleCallback,
  disconnectGoogle
} from '../controllers/googleAuthController';
import {
  initiateMicrosoftAuth,
  handleMicrosoftCallback,
  disconnectMicrosoft
} from '../controllers/microsoftAuthController';
import { createUserRecord, updateUserProfile, getUserProfile } from '../controllers/authController';

const router = express.Router();

/**
 * Google OAuth Routes
 */

/**
 * @route   GET /auth/google
 * @desc    Initiate Google OAuth flow
 * @access  Public
 */
router.get('/google', initiateGoogleAuth);

/**
 * @route   GET /auth/google/callback
 * @desc    Handle Google OAuth callback
 * @access  Public
 */
router.get('/google/callback', handleGoogleCallback);

/**
 * @route   DELETE /auth/google/:userId
 * @desc    Disconnect Google Calendar integration
 * @access  Private
 */
router.delete('/google/:userId', disconnectGoogle);

/**
 * Microsoft OAuth Routes
 */

/**
 * @route   GET /auth/microsoft
 * @desc    Initiate Microsoft OAuth flow
 * @access  Public
 */
router.get('/microsoft', initiateMicrosoftAuth);

/**
 * @route   GET /auth/microsoft/callback
 * @desc    Handle Microsoft OAuth callback
 * @access  Public
 */
router.get('/microsoft/callback', handleMicrosoftCallback);

/**
 * @route   DELETE /auth/microsoft/:userId
 * @desc    Disconnect Microsoft Calendar integration
 * @access  Private
 */
router.delete('/microsoft/:userId', disconnectMicrosoft);

/**
 * User Management Routes
 */

/**
 * @route   POST /auth/create-user
 * @desc    Create new user record
 * @access  Public
 */
router.post('/create-user', createUserRecord);

/**
 * @route   GET /auth/user/:userId/profile
 * @desc    Get user profile with comprehensive data
 * @access  Private
 */
router.get('/user/:userId/profile', getUserProfile);

/**
 * @route   PUT /auth/user/:userId/profile
 * @desc    Update user profile (name, city, timezone, preferences, etc.)
 * @access  Private
 */
router.put('/user/:userId/profile', updateUserProfile);

/**
 * QR Code Authentication Routes for Canvas Extension
 */

// Rate limiting for QR auth endpoints
const qrAuthRateLimit = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 30, // limit each IP to 30 requests per windowMs
  message: 'Too many QR authentication attempts, please try again later.'
});

// In-memory store for QR sessions (in production, use Redis or database)
const qrSessions = new Map();

// Cleanup expired sessions every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [sessionId, session] of qrSessions.entries()) {
    if (now > session.expiresAt) {
      qrSessions.delete(sessionId);
    }
  }
}, 5 * 60 * 1000);

/**
 * @route   POST /auth/qr-init
 * @desc    Initialize QR login session for Canvas extension
 * @access  Public
 */
router.post('/qr-init', qrAuthRateLimit, (req, res) => {
  try {
    const { sessionId, extensionId } = req.body;
    
    if (!sessionId || !extensionId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    // Create new QR session
    const session = {
      sessionId,
      extensionId,
      createdAt: Date.now(),
      expiresAt: Date.now() + (10 * 60 * 1000), // 10 minutes
      authenticated: false,
      token: null,
      userId: null
    };
    
    qrSessions.set(sessionId, session);
    console.log(`🎯 QR Session ${sessionId} initialized`);
    
    res.json({ 
      success: true, 
      sessionId,
      expiresAt: session.expiresAt
    });
    
  } catch (error) {
    console.error('QR init error:', error);
    res.status(500).json({ error: 'Failed to initialize QR session' });
  }
});

/**
 * @route   GET /auth/qr-status/:sessionId
 * @desc    Check QR authentication status (polled by extension)
 * @access  Public
 */
router.get('/qr-status/:sessionId', qrAuthRateLimit, (req, res) => {
  try {
    const { sessionId } = req.params;
    
    if (!sessionId) {
      return res.status(400).json({ error: 'Session ID required' });
    }
    
    const session = qrSessions.get(sessionId);
    
    if (!session) {
      return res.json({ 
        authenticated: false, 
        error: 'Session not found or expired' 
      });
    }
    
    if (Date.now() > session.expiresAt) {
      qrSessions.delete(sessionId);
      return res.json({ 
        authenticated: false, 
        error: 'Session expired' 
      });
    }
    
    res.json({
      authenticated: session.authenticated,
      token: session.authenticated ? session.token : null,
      userId: session.authenticated ? session.userId : null,
      expiresAt: session.expiresAt
    });
    
  } catch (error) {
    console.error('QR status error:', error);
    res.status(500).json({ error: 'Failed to check session status' });
  }
});

/**
 * @route   POST /auth/qr-authenticate
 * @desc    Authenticate QR session (called by mobile app)
 * @access  Public
 */
router.post('/qr-authenticate', qrAuthRateLimit, async (req, res) => {
  try {
    const { sessionId, userToken, userId } = req.body;
    
    if (!sessionId || !userToken || !userId) {
      return res.status(400).json({ error: 'Missing required fields' });
    }
    
    const session = qrSessions.get(sessionId);
    
    if (!session) {
      return res.status(404).json({ error: 'Session not found' });
    }
    
    if (Date.now() > session.expiresAt) {
      qrSessions.delete(sessionId);
      return res.status(410).json({ error: 'Session expired' });
    }
    
    if (session.authenticated) {
      return res.status(409).json({ error: 'Session already authenticated' });
    }
    
    // Update session with authentication
    session.authenticated = true;
    session.token = userToken;
    session.userId = userId;
    session.authenticatedAt = Date.now();
    
    console.log(`✅ QR Session ${sessionId} authenticated for user ${userId}`);
    
    res.json({ 
      success: true, 
      message: 'Authentication successful',
      sessionId 
    });
    
  } catch (error) {
    console.error('QR authenticate error:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
});

/**
 * @route   GET /auth/qr-test
 * @desc    Test QR auth service status
 * @access  Public
 */
router.get('/qr-test', (req, res) => {
  res.json({ 
    message: 'QR Auth service is running',
    timestamp: new Date().toISOString(),
    activeSessions: qrSessions.size
  });
});

export default router; 