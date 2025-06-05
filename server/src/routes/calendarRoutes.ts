import express from 'express';
import { 
  getUpcomingEvents as getGoogleEvents,
  getConnectionStatus,
  createCalendarEvent as createGoogleEvent,
  updateCalendarEvent as updateGoogleEvent,
  deleteCalendarEvent as deleteGoogleEvent,
  getCalendarsList as getGoogleCalendarsList,
  syncCalendarEvents as syncGoogleEvents
} from '../controllers/calendarController';
import {
  getUpcomingEvents as getMicrosoftEvents,
  createCalendarEvent as createMicrosoftEvent,
  updateCalendarEvent as updateMicrosoftEvent,
  deleteCalendarEvent as deleteMicrosoftEvent,
  getCalendarsList as getMicrosoftCalendarsList,
  syncCalendarEvents as syncMicrosoftEvents
} from '../controllers/microsoftCalendarController';
import { CalendarSyncService } from '../services/calendarSyncService';

const router = express.Router();

/**
 * Google Calendar Routes
 */

/**
 * @route   GET /calendar/google/events/:userId
 * @desc    Get upcoming calendar events for a user from Google Calendar
 * @access  Private
 */
router.get('/google/events/:userId', getGoogleEvents);

/**
 * @route   POST /calendar/google/events/:userId
 * @desc    Create a new event in Google Calendar
 * @access  Private
 */
router.post('/google/events/:userId', createGoogleEvent);

/**
 * @route   PUT /calendar/google/events/:userId/:eventId
 * @desc    Update an existing event in Google Calendar
 * @access  Private
 */
router.put('/google/events/:userId/:eventId', updateGoogleEvent);

/**
 * @route   DELETE /calendar/google/events/:userId/:eventId
 * @desc    Delete an event from Google Calendar
 * @access  Private
 */
router.delete('/google/events/:userId/:eventId', deleteGoogleEvent);

/**
 * @route   GET /calendar/google/calendars/:userId
 * @desc    Get list of user's Google Calendars
 * @access  Private
 */
router.get('/google/calendars/:userId', getGoogleCalendarsList);

/**
 * @route   POST /calendar/google/sync/:userId
 * @desc    Sync events from Google Calendar to PulsePlan
 * @access  Private
 */
router.post('/google/sync/:userId', syncGoogleEvents);

/**
 * Microsoft Calendar Routes
 */

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
router.post('/microsoft/events/:userId', createMicrosoftEvent);

/**
 * @route   PUT /calendar/microsoft/events/:userId/:eventId
 * @desc    Update an existing event in Microsoft Calendar
 * @access  Private
 */
router.put('/microsoft/events/:userId/:eventId', updateMicrosoftEvent);

/**
 * @route   DELETE /calendar/microsoft/events/:userId/:eventId
 * @desc    Delete an event from Microsoft Calendar
 * @access  Private
 */
router.delete('/microsoft/events/:userId/:eventId', deleteMicrosoftEvent);

/**
 * @route   GET /calendar/microsoft/calendars/:userId
 * @desc    Get list of user's Microsoft Calendars
 * @access  Private
 */
router.get('/microsoft/calendars/:userId', getMicrosoftCalendarsList);

/**
 * @route   POST /calendar/microsoft/sync/:userId
 * @desc    Sync events from Microsoft Calendar to PulsePlan
 * @access  Private
 */
router.post('/microsoft/sync/:userId', syncMicrosoftEvents);

/**
 * Advanced Sync Routes
 */

/**
 * @route   POST /calendar/sync-all/:userId
 * @desc    Comprehensive sync from all connected calendars
 * @access  Private
 */
router.post('/sync-all/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const { 
      providers = ['google', 'microsoft'],
      syncPeriodDays = 30,
      includeAllCalendars = false,
      calendarIds 
    } = req.body;

    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const result = await CalendarSyncService.syncAllCalendars({
      userId,
      providers,
      syncPeriodDays,
      includeAllCalendars,
      calendarIds
    });

    res.json(result);
  } catch (error) {
    console.error('Comprehensive sync error:', error);
    res.status(500).json({ error: 'Failed to sync calendars' });
  }
});

/**
 * @route   GET /calendar/sync-status/:userId
 * @desc    Get calendar synchronization status
 * @access  Private
 */
router.get('/sync-status/:userId', async (req, res) => {
  try {
    const { userId } = req.params;

    if (!userId) {
      return res.status(400).json({ error: 'User ID is required' });
    }

    const status = await CalendarSyncService.getSyncStatus(userId);
    res.json(status);
  } catch (error) {
    console.error('Error getting sync status:', error);
    res.status(500).json({ error: 'Failed to get sync status' });
  }
});

/**
 * @route   POST /calendar/create-external/:userId
 * @desc    Create a PulsePlan event in external calendars
 * @access  Private
 */
router.post('/create-external/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const { 
      title, 
      description, 
      startTime, 
      endTime, 
      location, 
      attendees, 
      providers = ['google', 'microsoft'] 
    } = req.body;

    if (!userId || !title || !startTime || !endTime) {
      return res.status(400).json({ 
        error: 'User ID, title, startTime, and endTime are required' 
      });
    }

    const results = await CalendarSyncService.createEventInExternalCalendars(
      userId,
      { title, description, startTime, endTime, location, attendees },
      providers
    );

    res.json({ success: true, results });
  } catch (error) {
    console.error('Error creating external event:', error);
    res.status(500).json({ error: 'Failed to create event in external calendars' });
  }
});

/**
 * Shared Routes
 */

/**
 * @route   GET /calendar/status/:userId
 * @desc    Get calendar connection status for a user
 * @access  Private
 */
router.get('/status/:userId', getConnectionStatus);

export default router; 