import express from 'express';
import { 
  getUpcomingEvents as getGoogleEvents,
  getConnectionStatus
} from '../controllers/calendarController';
import {
  getUpcomingEvents as getMicrosoftEvents,
  createCalendarEvent
} from '../controllers/microsoftCalendarController';

const router = express.Router();

/**
 * @route   GET /calendar/google/events/:userId
 * @desc    Get upcoming calendar events for a user from Google Calendar
 * @access  Private
 */
router.get('/google/events/:userId', getGoogleEvents);

/**
 * @route   GET /calendar/microsoft/events/:userId
 * @desc    Get upcoming calendar events for a user from Microsoft Calendar
 * @access  Private
 */
router.get('/microsoft/events/:userId', getMicrosoftEvents);

/**
 * @route   POST /calendar/microsoft/events/:userId
 * @desc    Create a new event in Microsoft Calendar
 * @access  Private
 */
router.post('/microsoft/events/:userId', createCalendarEvent);

/**
 * @route   GET /calendar/status/:userId
 * @desc    Get calendar connection status for a user
 * @access  Private
 */
router.get('/status/:userId', getConnectionStatus);

export default router; 