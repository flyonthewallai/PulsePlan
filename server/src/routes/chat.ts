import express from 'express';
import { authenticate } from '../middleware/authenticate';
import { chatService } from '../services/chatService';

const router = express.Router();

// Middleware to log all requests
router.use((req, res, next) => {
  console.log('Chat request:', {
    method: req.method,
    path: req.path,
    body: req.body,
    headers: req.headers
  });
  next();
});

router.post('/message', authenticate, async (req, res) => {
  try {
    const { messages } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Invalid message format' });
    }

    console.log('Received chat message request:', {
      messageCount: messages.length,
      lastMessage: messages[messages.length - 1]
    });

    const response = await chatService.getChatResponse(req, messages);
    console.log('Chat response generated:', {
      contentLength: response.content.length,
      tokenUsage: response.usage
    });

    res.json(response);
  } catch (error) {
    console.error('Error processing chat message:', error);
    res.status(500).json({ 
      error: error instanceof Error ? error.message : 'Failed to process chat message'
    });
  }
});

export default router; 