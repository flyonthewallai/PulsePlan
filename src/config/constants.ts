// API URL for development and production
export const API_URL = __DEV__ 
  ? 'http://localhost:3000'  // Development server
  : 'https://api.pulseplan.app'; // Production server (we can replace this later)