// API configuration
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Get the API URL based on environment and platform
const constructBaseApiUrl = () => {
  // Check for environment variables from .env file
  const envApiUrl = process.env.EXPO_PUBLIC_API_URL;
  
  if (envApiUrl) {
    console.log('Using API URL from environment:', envApiUrl);
    return envApiUrl;
  }

  // Check app.json extra config
  const appConfigApiUrl = Constants.expoConfig?.extra?.apiUrl;
  if (appConfigApiUrl) {
    console.log('Using API URL from app.json:', appConfigApiUrl);
    return appConfigApiUrl;
  }

  // Development defaults
  if (__DEV__) {
    if (Platform.OS === 'web') {
      return 'http://localhost:5000';
    }
    if (Platform.OS === 'ios') {
      return 'http://localhost:5000';
    }
    if (Platform.OS === 'android') {
      return 'http://10.0.2.2:5000';
    }
    // Default for other platforms
    return 'http://localhost:5000';
  }

  // Production fallback - disable for now since server doesn't exist
  console.warn('⚠️ No API server configured. API calls will fail.');
  return 'http://localhost:5000'; // Changed from production URL
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
    appConfigApiUrl: Constants.expoConfig?.extra?.apiUrl,
    isPhysicalDevice: Platform.OS === 'ios' || Platform.OS === 'android'
  });
} 