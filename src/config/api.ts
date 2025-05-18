// API configuration
// For development, use your computer's IP address instead of localhost
// You can find your IP address by running 'ipconfig' on Windows or 'ifconfig' on Mac/Linux
export const API_URL = 'http://10.0.0.4:5000';

// Helper function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string) => `${API_URL}${endpoint}`; 