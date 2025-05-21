import express from 'express';
import { authenticate } from '../middleware/authenticate';
import {
  getScheduleBlocksForUser,
  createScheduleBlock,
  updateScheduleBlock,
  deleteScheduleBlock
} from '../services/scheduleBlockService';

const router = express.Router();

router.use(authenticate);

// Get all schedule blocks for the authenticated user
router.get('/', async (req, res) => {
  try {
    const userId = req.user.id;
    const blocks = await getScheduleBlocksForUser(userId);
    res.json(blocks);
  } catch (error: unknown) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'An unknown error occurred' 
    });
  }
});

// Create a new schedule block
router.post('/', async (req, res) => {
  try {
    const userId = req.user.id;
    const block = req.body;
    const newBlock = await createScheduleBlock(userId, block);
    res.status(201).json(newBlock);
  } catch (error: unknown) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'An unknown error occurred' 
    });
  }
});

// Update a schedule block
router.patch('/:id', async (req, res) => {
  try {
    const userId = req.user.id;
    const blockId = req.params.id;
    const updates = req.body;
    const updatedBlock = await updateScheduleBlock(userId, blockId, updates);
    res.json(updatedBlock);
  } catch (error: unknown) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'An unknown error occurred' 
    });
  }
});

// Delete a schedule block
router.delete('/:id', async (req, res) => {
  try {
    const userId = req.user.id;
    const blockId = req.params.id;
    await deleteScheduleBlock(userId, blockId);
    res.status(204).end();
  } catch (error: unknown) {
    console.error('Error:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'An unknown error occurred' 
    });
  }
});

export default router; 