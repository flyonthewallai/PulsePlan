// API URL for development and production
// This should match the configuration in api.ts
export const API_URL = __DEV__ 
  ? 'http://10.0.0.4:5000'  // Development server (Windows network IP)
  : 'https://api.pulseplan.app'; // Production server