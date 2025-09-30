// API configuration for web app
// Matches the React Native app's API configuration structure

// Get the API URL based on environment
const constructBaseApiUrl = () => {
  // First priority: VITE_API_BASE_URL if set
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Second priority: construct from VITE_API_URL and VITE_API_PORT
  if (import.meta.env.VITE_API_URL && import.meta.env.VITE_API_PORT) {
    const host = import.meta.env.VITE_API_URL;
    const port = import.meta.env.VITE_API_PORT;
    return `http://${host}:${port}`;
  }

  // Development fallback
  if (import.meta.env.DEV) {
    const port = import.meta.env.VITE_API_PORT || '8000';
    return `http://localhost:${port}`;
  }

  // Production fallback
  return 'https://api.pulseplan.app';
};

export const API_BASE_URL = constructBaseApiUrl();

// Export for compatibility with RN app structure
export const API_URL = API_BASE_URL;

