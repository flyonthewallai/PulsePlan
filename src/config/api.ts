// API configuration
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Get the local IP address from environment or use a default
const getLocalIpAddress = () => {
  // In development, try to use the IP from environment first
  if (__DEV__) {
    // For iOS simulator
    if (Platform.OS === 'ios') {
      return 'localhost';
    }
    // For Android emulator
    if (Platform.OS === 'android') {
      return '10.0.2.2';
    }
    // For web or physical devices, use the environment variable or default
    return process.env.EXPO_PUBLIC_API_URL || 'localhost';
  }
  // In production, use the production API URL
  return process.env.EXPO_PUBLIC_API_URL || 'https://api.pulseplan.app';
};

// Get the port from environment or use default
const getPort = () => {
  return process.env.EXPO_PUBLIC_API_PORT || '3000';
};

// Construct the API URL
const constructApiUrl = () => {
  const host = getLocalIpAddress();
  const port = getPort();
  const protocol = __DEV__ ? 'http' : 'https';
  
  // Don't include port for production or if using a full URL
  if (!__DEV__ || host.includes('://')) {
    return `${protocol}://${host}`;
  }
  
  return `${protocol}://${host}:${port}`;
};

export const API_URL = constructApiUrl();

// Helper function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string) => `${API_URL}${endpoint}`;

// Log the API configuration in development
if (__DEV__) {
  console.log('API Configuration:', {
    environment: __DEV__ ? 'development' : 'production',
    apiUrl: API_URL,
    platform: Platform.OS,
    host: getLocalIpAddress(),
    port: getPort()
  });
} 