import { Router } from 'express';
import { authenticate } from '../middleware/authenticate';
import { n8nAgentService } from '../services/n8nAgentService';
import { Response } from 'express';
import { AuthenticatedRequest } from '../middleware/authenticate';
import { 
  batchProcessTasks, 
  triggerIntelligentRescheduling, 
  optimizeStudySession, 
  analyzeUpcomingDeadlines 
} from '../controllers/agentSchedulingController';

const router = Router();

// POST /agent/task - Create task with intelligent agent processing
router.post('/task', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { title, dueDate, duration, priority, subject, tool } = req.body;

  if (!title || !dueDate || !subject) {
    res.status(400).json({ error: 'Missing required fields: title, dueDate, subject' });
    return;
  }

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  try {
    const agentResponse = await n8nAgentService.createTaskWithAgent(
      userId,
      title,
      dueDate,
      duration || 60,
      priority || 'medium',
      subject,
      tool,
      userEmail
    );

    res.json(agentResponse);
  } catch (error) {
    console.error('Error in agent task creation:', error);
    res.status(500).json({ error: 'Failed to process task with agent' });
  }
});

// POST /agent/user-task - Process user-initiated task with agent
router.post('/user-task', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { title, dueDate, duration, priority, subject } = req.body;

  if (!title || !dueDate || !subject) {
    res.status(400).json({ error: 'Missing required fields: title, dueDate, subject' });
    return;
  }

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  try {
    const agentResponse = await n8nAgentService.createTaskFromUser(
      userId,
      title,
      dueDate,
      duration || 60,
      priority || 'medium',
      subject,
      userEmail
    );

    res.json(agentResponse);
  } catch (error) {
    console.error('Error in user task processing:', error);
    res.status(500).json({ error: 'Failed to process user task with agent' });
  }
});

// GET /agent/health - Check n8n agent health
router.get('/health', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const isHealthy = await n8nAgentService.healthCheck();
    res.json({ 
      healthy: isHealthy,
      timestamp: new Date().toISOString(),
      agent_url: 'https://pulseplan-agent.fly.dev'
    });
  } catch (error) {
    console.error('Error checking agent health:', error);
    res.status(500).json({ error: 'Failed to check agent health' });
  }
});

// POST /agent/custom - Send custom payload to agent
router.post('/custom', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user?.id;
  const payload = req.body;

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  // Ensure userId is included in the payload
  const basePayload = {
    ...payload,
    userId: userId,
  };

  try {
    const completePayload = await n8nAgentService.createCompletePayload(basePayload);
    const agentResponse = await n8nAgentService.postToAgent(completePayload);
    res.json(agentResponse);
  } catch (error) {
    console.error('Error in custom agent request:', error);
    res.status(500).json({ error: 'Failed to send custom request to agent' });
  }
});

// POST /agent/query - Process natural language queries
router.post('/query', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { query, context, duration } = req.body;

  if (!query || typeof query !== 'string') {
    res.status(400).json({ error: 'Query is required and must be a string' });
    return;
  }

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  try {
    const basePayload = {
      userId,
      userEmail,
      query: query.trim(),
      date: new Date().toISOString(),
      duration,
      source: 'app' as const,
      context: {
        currentPage: context?.currentPage || 'unknown',
        userPreferences: context?.userPreferences,
      },
    };

    const completePayload = await n8nAgentService.createCompleteNaturalLanguagePayload(basePayload);
    const agentResponse = await n8nAgentService.processNaturalLanguage(completePayload);
    res.json(agentResponse);
  } catch (error) {
    console.error('Error in processing query:', error);
    res.status(500).json({ error: 'Failed to process query' });
  }
});

// POST /agent/chat - Chat-like interface for natural language queries
router.post('/chat', authenticate, async (req: AuthenticatedRequest, res: Response) => {
  const userId = req.user?.id;
  const userEmail = req.user?.email;
  const { message, conversationId, context } = req.body;

  if (!message || typeof message !== 'string') {
    res.status(400).json({ error: 'Message is required and must be a string' });
    return;
  }

  if (!userId) {
    res.status(401).json({ error: 'User not authenticated' });
    return;
  }

  try {
    const basePayload = {
      userId,
      userEmail,
      query: message.trim(),
      date: new Date().toISOString(),
      source: 'app' as const,
      context: {
        conversationId,
        currentPage: context?.currentPage || 'chat',
        userPreferences: context?.userPreferences,
        chatHistory: context?.chatHistory,
      },
    };

    const completePayload = await n8nAgentService.createCompleteNaturalLanguagePayload(basePayload);
    const agentResponse = await n8nAgentService.processNaturalLanguage(completePayload);
    
    res.json({
      ...agentResponse,
      conversationId: conversationId || `conv_${Date.now()}`,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error in chat processing:', error);
    res.status(500).json({ error: 'Failed to process chat message' });
  }
});

// Advanced scheduling routes
router.post('/batch-process', authenticate, batchProcessTasks);
router.post('/reschedule', authenticate, triggerIntelligentRescheduling);
router.post('/optimize-session', authenticate, optimizeStudySession);
router.post('/analyze-deadlines', authenticate, analyzeUpcomingDeadlines);

export default router; 