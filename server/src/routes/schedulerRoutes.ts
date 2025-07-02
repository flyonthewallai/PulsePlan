import { Router } from 'express';
import { authenticate } from '../middleware/authenticate';
import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import { emailScheduler } from '../../jobs/scheduler';
import { logger } from '../../jobs/utils/logger';

const router = Router();

/**
 * GET /scheduler/status
 * Get scheduler status and next run times
 */
router.get('/status', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const status = emailScheduler.getStatus();
    res.json({
      ...status,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Error getting scheduler status', error);
    res.status(500).json({ error: 'Failed to get scheduler status' });
  }
});

/**
 * POST /scheduler/run-daily-briefing
 * Manually trigger daily briefing job for testing
 */
router.post('/run-daily-briefing', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    logger.info('Manual daily briefing job triggered by admin');
    await emailScheduler.runDailyBriefingNow();
    res.json({ 
      success: true, 
      message: 'Daily briefing job executed successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Error running manual daily briefing job', error);
    res.status(500).json({ 
      error: 'Failed to run daily briefing job',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /scheduler/run-weekly-pulse
 * Manually trigger weekly pulse job for testing
 */
router.post('/run-weekly-pulse', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    logger.info('Manual weekly pulse job triggered by admin');
    await emailScheduler.runWeeklyPulseNow();
    res.json({ 
      success: true, 
      message: 'Weekly pulse job executed successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Error running manual weekly pulse job', error);
    res.status(500).json({ 
      error: 'Failed to run weekly pulse job',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /scheduler/start
 * Start the email scheduler
 */
router.post('/start', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    emailScheduler.start();
    res.json({ 
      success: true, 
      message: 'Email scheduler started successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Error starting scheduler', error);
    res.status(500).json({ 
      error: 'Failed to start scheduler',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * POST /scheduler/stop
 * Stop the email scheduler
 */
router.post('/stop', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    emailScheduler.stop();
    res.json({ 
      success: true, 
      message: 'Email scheduler stopped successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    logger.error('Error stopping scheduler', error);
    res.status(500).json({ 
      error: 'Failed to stop scheduler',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

export default router; 