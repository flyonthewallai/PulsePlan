// API configuration
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Get the API URL based on environment and platform
const constructBaseApiUrl = () => {
  // If we have an environment variable, use it
  if (process.env.EXPO_PUBLIC_API_URL) {
    const host = process.env.EXPO_PUBLIC_API_URL;
    const port = process.env.EXPO_PUBLIC_API_PORT || '5000';
    return `http://${host}:${port}`;
  }

  // Otherwise use platform-specific defaults for development
  if (__DEV__) {
    if (Platform.OS === 'ios') {
      return 'http://localhost:5000';
    }
    if (Platform.OS === 'android') {
      return 'http://10.0.2.2:5000';
    }
  }

  // Production fallback
  return 'https://api.pulseplan.app';
};

export const API_URL = constructBaseApiUrl();

// Helper function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string) => `${API_URL}${endpoint}`;

// Log the API configuration in development
if (__DEV__) {
  console.log('API Configuration:', {
    environment: __DEV__ ? 'development' : 'production',
    apiUrl: API_URL,
    platform: Platform.OS,
    envApiUrl: process.env.EXPO_PUBLIC_API_URL,
    envApiPort: process.env.EXPO_PUBLIC_API_PORT,
    isPhysicalDevice: Platform.OS === 'ios' || Platform.OS === 'android'
  });
} 