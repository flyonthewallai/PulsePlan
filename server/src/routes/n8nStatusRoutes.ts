import { Router } from 'express';
import {
  notifyWorkflowStart,
  notifyWorkflowComplete,
  notifyWorkflowError,
  notifySubworkflowStatus,
  notifyCustomStatus,
} from '../controllers/n8nStatusController';

const router = Router();

/**
 * POST /api/n8n/status/start
 * Notify workflow start
 * No authentication required (n8n will send directly)
 */
router.post('/start', notifyWorkflowStart);

/**
 * POST /api/n8n/status/complete
 * Notify workflow completion
 * No authentication required (n8n will send directly)
 */
router.post('/complete', notifyWorkflowComplete);

/**
 * POST /api/n8n/status/error
 * Notify workflow error
 * No authentication required (n8n will send directly)
 */
router.post('/error', notifyWorkflowError);

/**
 * POST /api/n8n/status/subworkflow
 * Notify subworkflow status update
 * No authentication required (n8n will send directly)
 */
router.post('/subworkflow', notifySubworkflowStatus);

/**
 * POST /api/n8n/status/custom
 * Notify custom status update
 * No authentication required (n8n will send directly)
 */
router.post('/custom', notifyCustomStatus);

export default router; 