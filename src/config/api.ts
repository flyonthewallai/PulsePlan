// API configuration
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Get the API URL based on environment and platform
const constructBaseApiUrl = () => {
  // Get values from app.json extra config
  const apiUrl = Constants.expoConfig?.extra?.apiUrl;
  const apiPort = Constants.expoConfig?.extra?.apiPort;
  
  // If we have environment variables, use them (for dynamic port handling)
  if (process.env.EXPO_PUBLIC_API_URL && process.env.EXPO_PUBLIC_API_PORT) {
    const host = process.env.EXPO_PUBLIC_API_URL;
    const port = process.env.EXPO_PUBLIC_API_PORT;
    return `http://${host}:${port}`;
  }
  
  // Use app.json config if available
  if (apiUrl) {
    return apiUrl;
  }

  // Otherwise use platform-specific defaults for development
  if (__DEV__) {
    const basePort = apiPort || '3000';
    if (Platform.OS === 'ios') {
      return `http://localhost:${basePort}`;
    }
    if (Platform.OS === 'android') {
      return `http://10.0.2.2:${basePort}`;
    }
  }

  // Production fallback
  return 'https://api.pulseplan.app';
};

export const API_URL = constructBaseApiUrl();

// Helper function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string) => `${API_URL}${endpoint}`;

// Helper function to test API connection
export const testConnection = async (): Promise<boolean> => {
  try {
    // Create a timeout promise for React Native compatibility
    const timeoutPromise = new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error('Connection timeout')), 5000)
    );
    
    const fetchPromise = fetch(`${API_URL}/health`, { 
      method: 'GET'
    });
    
    const response = await Promise.race([fetchPromise, timeoutPromise]);
    return response.ok;
  } catch (error) {
    console.error('API connection test failed:', error);
    return false;
  }
};

// Log the API configuration in development
if (__DEV__) {
  console.log('API Configuration:', {
    environment: __DEV__ ? 'development' : 'production',
    apiUrl: API_URL,
    platform: Platform.OS,
    envApiUrl: process.env.EXPO_PUBLIC_API_URL,
    envApiPort: process.env.EXPO_PUBLIC_API_PORT,
    appJsonApiUrl: Constants.expoConfig?.extra?.apiUrl,
    appJsonApiPort: Constants.expoConfig?.extra?.apiPort,
    isPhysicalDevice: Platform.OS === 'ios' || Platform.OS === 'android'
  });
} 