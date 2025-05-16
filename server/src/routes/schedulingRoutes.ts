import express from 'express';
import { generateSchedule } from '../controllers/schedulingController';

const router = express.Router();

/**
 * @route   POST /scheduling/generate
 * @desc    Generate an optimized schedule using GPT-4o
 * @access  Private
 */
router.post('/generate', generateSchedule);

export default router; 