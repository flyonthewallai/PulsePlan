import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes';
import calendarRoutes from './routes/calendarRoutes';
import gmailRoutes from './routes/gmailRoutes';
import contactsRoutes from './routes/contactsRoutes';
import schedulingRoutes from './routes/schedulingRoutes';
import applePayRoutes from './routes/applePayRoutes';
import tasksRoutes from './routes/tasksRoutes';
import scheduleBlocksRouter from './routes/scheduleBlocks';
import chatRoutes from './routes/chat';
import canvasRoutes from './routes/canvasRoutes';
import scrapingRoutes from './routes/scrapingRoutes';
import cacheRoutes from './routes/cacheRoutes';
import briefingRoutes from './routes/briefingRoutes';
import schedulerRoutes from './routes/schedulerRoutes';
import connectionRoutes from './routes/connectionRoutes';

// Try to import agent routes with error handling
let agentRoutes;
try {
  agentRoutes = require('./routes/agentRoutes').default;
  console.log('✅ Agent routes imported successfully');
} catch (error) {
  console.error('❌ Agent routes import failed:', error instanceof Error ? error.message : String(error));
  // Create a minimal fallback router
  const { Router } = require('express');
  agentRoutes = Router();
  agentRoutes.get('/health', (req: Request, res: Response) => {
    res.json({ healthy: false, error: 'Agent routes module failed to load', timestamp: new Date().toISOString() });
  });
  console.log('🔧 Created fallback agent routes');
}

import { findAvailablePort } from './utils/portUtils';
import { emailScheduler } from '../jobs/scheduler';

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const PORT = parseInt(process.env.PORT || '5000');

// CORS configuration - Permissive setup for extension support
const corsOptions = {
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin) return callback(null, true);
    
    // Allow Chrome extensions
    if (origin && origin.startsWith('chrome-extension://')) {
      return callback(null, true);
    }
    
    // Allow Canvas domains (always)
    if (origin && (origin.includes('.instructure.com') || origin.includes('.canvas.'))) {
      return callback(null, true);
    }
    
    // Allow PulsePlan domains
    if (origin && (origin.includes('pulseplan.') || origin.includes('localhost'))) {
      return callback(null, true);
    }
    
    // Default to allow (for development and extension compatibility)
    callback(null, true);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
  allowedHeaders: [
    'Content-Type', 
    'Authorization', 
    'Accept', 
    'Origin', 
    'X-Requested-With',
    'sentry-trace',           // Sentry monitoring
    'baggage',               // Sentry context
    'x-forwarded-for',       // Proxy headers
    'x-real-ip',             // Real IP headers
    'user-agent',            // User agent
    'referer',               // Referer header
    'cache-control',         // Cache control
    'pragma',                // Pragma header
    'expires',               // Expires header
    '*'                      // Allow any header
  ],
  exposedHeaders: ['*'],     // Expose all response headers
  optionsSuccessStatus: 200,
  preflightContinue: false,
  maxAge: 86400             // Cache preflight for 24 hours
};

// Middleware
app.use(cors(corsOptions));

// Parse JSON for all routes (no special handling needed for Apple Pay)
// Apple Pay receipt verification uses JSON

// Parse JSON for all other routes
app.use(express.json());

// Routes
app.use('/auth', authRoutes);
app.use('/calendar', calendarRoutes);
app.use('/gmail', gmailRoutes);
app.use('/contacts', contactsRoutes);
app.use('/scheduling', schedulingRoutes);
app.use('/apple-pay', applePayRoutes);
app.use('/tasks', tasksRoutes);
app.use('/schedule-blocks', scheduleBlocksRouter);
app.use('/chat', chatRoutes);
app.use('/canvas', canvasRoutes);
app.use('/scraping', scrapingRoutes);
app.use('/agent', agentRoutes);
app.use('/cache', cacheRoutes);
app.use('/agents', briefingRoutes);
app.use('/scheduler', schedulerRoutes);
app.use('/connections', connectionRoutes);

// Health check route
app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ 
    status: 'UP',
    timestamp: new Date().toISOString() 
  });
});

// Start server with port handling
async function startServer() {
  try {
    const availablePort = await findAvailablePort(PORT);
    
    app.listen(availablePort, '0.0.0.0', () => {
      console.log(`🚀 Server successfully started on port ${availablePort}`);
      console.log(`🌐 Server accessible at:`);
      console.log(`   - http://localhost:${availablePort}`);
      console.log(`   - http://127.0.0.1:${availablePort}`);
      if (availablePort !== PORT) {
        console.log(`⚠️  Note: Default port ${PORT} was in use, using ${availablePort} instead`);
      }
      
      // Fix OAuth URLs to use the correct port
      const googleUrl = process.env.GOOGLE_REDIRECT_URL 
        ? process.env.GOOGLE_REDIRECT_URL.replace(/:\d+/, `:${availablePort}`)
        : `http://localhost:${availablePort}/auth/google/callback`;
      
      const microsoftUrl = process.env.MICROSOFT_REDIRECT_URL 
        ? process.env.MICROSOFT_REDIRECT_URL.replace(/:\d+/, `:${availablePort}`)
        : `http://localhost:${availablePort}/auth/microsoft/callback`;
      
      console.log(`🔗 Google OAuth callback URL: ${googleUrl}`);
      console.log(`🔗 Microsoft OAuth callback URL: ${microsoftUrl}`);
      console.log(`🏥 Health check: http://localhost:${availablePort}/health`);
      console.log(`📊 API Base URL: http://localhost:${availablePort}`);
      
      // Start the email scheduler
      try {
        emailScheduler.start();
        console.log('📅 Email scheduler started successfully');
      } catch (error) {
        console.error('❌ Failed to start email scheduler:', error);
        // Don't exit - let the server continue running without the scheduler
      }
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer(); 