import express from 'express';
import { authenticate } from '../middleware/authenticate';
import { getTasks, createTask, updateTask, deleteTask } from '../controllers/tasksController';

const router = express.Router();

router.get('/', authenticate, getTasks);
router.post('/', authenticate, createTask);
router.put('/:id', authenticate, updateTask);
router.delete('/:id', authenticate, deleteTask);

export default router; 