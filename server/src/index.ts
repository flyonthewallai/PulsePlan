import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes';
import calendarRoutes from './routes/calendarRoutes';
import schedulingRoutes from './routes/schedulingRoutes';
import stripeRoutes from './routes/stripeRoutes';
import tasksRoutes from './routes/tasksRoutes';
import scheduleBlocksRoutes from './routes/scheduleBlocksRoutes';

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 5000;

// CORS configuration
const corsOptions = {
  origin: [
    'http://localhost:19006',  // Expo web
    'exp://localhost:19000',   // Expo Go
    'exp://10.0.0.4:19000',   // Expo Go on your IP
    'exp://192.168.1.*:19000' // Any local network IP
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
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
app.use('/schedule_blocks', scheduleBlocksRoutes);

// Health check route
app.get('/health', (req: Request, res: Response) => {
  res.status(200).json({ 
    status: 'UP',
    timestamp: new Date().toISOString() 
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Google OAuth callback URL: ${process.env.GOOGLE_REDIRECT_URL}`);
  console.log(`Microsoft OAuth callback URL: ${process.env.MICROSOFT_REDIRECT_URL}`);
}); 