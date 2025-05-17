import express from 'express';
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
import { createUserRecord } from '../controllers/authController';

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

router.post('/create-user', createUserRecord);

export default router; 