import express from 'express';
import { authenticate } from '../middleware/authenticate';
import { 
  uploadCanvasData,
  getCanvasIntegrationStatus,
  generateQRConnectionCode,
  completeExtensionConnection,
  testConnection
} from '../controllers/canvasController';

const router = express.Router();

// Canvas data upload endpoint (used by extension)
router.post('/upload-data', authenticate, uploadCanvasData);

// Get Canvas integration status
router.get('/status', authenticate, getCanvasIntegrationStatus);

// Generate QR code for extension connection
router.post('/generate-connection-code', authenticate, generateQRConnectionCode);

// Complete extension connection (via QR code/shortlink)
router.post('/connect-extension', authenticate, completeExtensionConnection);

// Test connection endpoint
router.get('/test-connection', testConnection);

export default router; 