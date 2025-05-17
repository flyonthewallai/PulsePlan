import express from 'express';
import { authenticate } from '../middleware/authenticate';
import { getScheduleBlocks, createScheduleBlock, updateScheduleBlock, deleteScheduleBlock } from '../controllers/scheduleBlocksController';

const router = express.Router();

router.get('/', authenticate, getScheduleBlocks);
router.post('/', authenticate, createScheduleBlock);
router.put('/:id', authenticate, updateScheduleBlock);
router.delete('/:id', authenticate, deleteScheduleBlock);

export default router; 