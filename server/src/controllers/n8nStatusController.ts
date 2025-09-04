import { Request, Response } from 'express';
import { n8nAgentService } from '../services/n8nAgentService';

/**
 * Receive workflow start notification from n8n
 * POST /api/n8n/status/start
 */
export const notifyWorkflowStart = async (req: Request, res: Response): Promise<void> => {
  try {
    const { userId, workflowName, message } = req.body;

    // Validate required fields
    if (!userId || !workflowName) {
      res.status(400).json({ 
        error: 'Missing required fields: userId, workflowName' 
      });
      return;
    }

    // Send workflow start notification
    await n8nAgentService.notifyWorkflowStart(userId, workflowName, message);

    res.json({ 
      success: true, 
      message: 'Workflow start notification sent successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error notifying workflow start:', error);
    res.status(500).json({ 
      error: 'Failed to notify workflow start',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Receive workflow completion notification from n8n
 * POST /api/n8n/status/complete
 */
export const notifyWorkflowComplete = async (req: Request, res: Response): Promise<void> => {
  try {
    const { userId, workflowName, message } = req.body;

    // Validate required fields
    if (!userId || !workflowName) {
      res.status(400).json({ 
        error: 'Missing required fields: userId, workflowName' 
      });
      return;
    }

    // Send workflow completion notification
    await n8nAgentService.notifyWorkflowComplete(userId, workflowName, message);

    res.json({ 
      success: true, 
      message: 'Workflow completion notification sent successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error notifying workflow completion:', error);
    res.status(500).json({ 
      error: 'Failed to notify workflow completion',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Receive workflow error notification from n8n
 * POST /api/n8n/status/error
 */
export const notifyWorkflowError = async (req: Request, res: Response): Promise<void> => {
  try {
    const { userId, workflowName, error } = req.body;

    // Validate required fields
    if (!userId || !workflowName || !error) {
      res.status(400).json({ 
        error: 'Missing required fields: userId, workflowName, error' 
      });
      return;
    }

    // Send workflow error notification
    await n8nAgentService.notifyWorkflowError(userId, workflowName, error);

    res.json({ 
      success: true, 
      message: 'Workflow error notification sent successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error notifying workflow error:', error);
    res.status(500).json({ 
      error: 'Failed to notify workflow error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Receive subworkflow status update from n8n
 * POST /api/n8n/status/subworkflow
 */
export const notifySubworkflowStatus = async (req: Request, res: Response): Promise<void> => {
  try {
    const { userId, mainWorkflow, subworkflow, status, message } = req.body;

    // Validate required fields
    if (!userId || !mainWorkflow || !subworkflow || !status) {
      res.status(400).json({ 
        error: 'Missing required fields: userId, mainWorkflow, subworkflow, status' 
      });
      return;
    }

    // Validate status values
    const validStatuses = ['active', 'completed', 'error'];
    if (!validStatuses.includes(status)) {
      res.status(400).json({ 
        error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` 
      });
      return;
    }

    // Send subworkflow status notification
    await n8nAgentService.notifySubworkflowStatus(
      userId, 
      mainWorkflow, 
      subworkflow, 
      status, 
      message
    );

    res.json({ 
      success: true, 
      message: 'Subworkflow status notification sent successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error notifying subworkflow status:', error);
    res.status(500).json({ 
      error: 'Failed to notify subworkflow status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

/**
 * Receive custom status update from n8n
 * POST /api/n8n/status/custom
 */
export const notifyCustomStatus = async (req: Request, res: Response): Promise<void> => {
  try {
    const { userId, tool, status, message, metadata } = req.body;

    // Validate required fields
    if (!userId || !tool || !status) {
      res.status(400).json({ 
        error: 'Missing required fields: userId, tool, status' 
      });
      return;
    }

    // Validate status values
    const validStatuses = ['active', 'completed', 'error', 'idle'];
    if (!validStatuses.includes(status)) {
      res.status(400).json({ 
        error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` 
      });
      return;
    }

    // Send custom status notification
    await n8nAgentService.updateAgentStatus(userId, tool, status, message, metadata);

    res.json({ 
      success: true, 
      message: 'Custom status notification sent successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error notifying custom status:', error);
    res.status(500).json({ 
      error: 'Failed to notify custom status',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}; 