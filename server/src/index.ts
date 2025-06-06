import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes';
import calendarRoutes from './routes/calendarRoutes';
import schedulingRoutes from './routes/schedulingRoutes';
import stripeRoutes from './routes/stripeRoutes';
import tasksRoutes from './routes/tasksRoutes';
import scheduleBlocksRouter from './routes/scheduleBlocks';
import chatRoutes from './routes/chat';
import canvasRoutes from './routes/canvasRoutes';
import { findAvailablePort } from './utils/portUtils';

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const PORT = parseInt(process.env.PORT || '5000');

// CORS configuration
const corsOptions = {
  origin: process.env.NODE_ENV === 'development'
    ? '*' // Allow all origins in development
    : [
        'http://localhost:19006',  // Expo web
        'exp://localhost:19000',   // Expo Go
        'exp://10.0.0.4:19000',   // Expo Go on your IP
        'exp://192.168.1.*:19000' // Any local network IP
      ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Accept']
};

// Middleware
app.use(cors(corsOptions));

// Special handling for Stripe webhook route that needs raw body
app.use('/stripe/webhook', express.raw({ type: 'application/json' }));

// Parse JSON for all other routes
app.use(express.json());

// Routes
app.use('/auth', authRoutes);
app.use('/calendar', calendarRoutes);
app.use('/scheduling', schedulingRoutes);
app.use('/stripe', stripeRoutes);
app.use('/tasks', tasksRoutes);
app.use('/schedule-blocks', scheduleBlocksRouter);
app.use('/chat', chatRoutes);
app.use('/canvas', canvasRoutes);

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
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer(); 