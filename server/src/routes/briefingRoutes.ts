import { Router } from 'express';
import { authenticate } from '../middleware/authenticate';
import { generateBriefing, generateWeeklyPulse } from '../controllers/briefingController';

const router = Router();

/**
 * POST /agents/briefing
 * Generate daily briefing data for a user
 */
router.post('/briefing', generateBriefing);

/**
 * POST /agents/weekly-pulse
 * Generate weekly pulse data for a user
 */
router.post('/weekly-pulse', generateWeeklyPulse);

export default router; 