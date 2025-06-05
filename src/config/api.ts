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
    const basePort = apiPort || '5000';
    if (Platform.OS === 'ios') {
      // Use the local network IP for iOS development
      return `http://10.0.0.4:${basePort}`;
    }
    if (Platform.OS === 'android') {
      // Android emulator uses 10.0.2.2 to reach host machine
      return `http://10.0.2.2:${basePort}`;
    }
    // For Windows/Web development, use the local network IP
    return `http://10.0.0.4:${basePort}`;
  }

  // Production fallback
  return 'https://api.pulseplan.app';
};

export const API_URL = constructBaseApiUrl();
export const API_BASE_URL = API_URL; // Alias for consistency

// Helper function to get the full URL for an endpoint
export const getApiUrl = (endpoint: string) => `${API_URL}${endpoint}`;

// Helper function to test API connection with fallback URLs for Windows
export const testConnection = async (): Promise<boolean> => {
  const testUrls = [
    API_URL,
    API_URL.replace('localhost', '10.0.0.4'), // Try local network IP
    API_URL.replace('localhost', '127.0.0.1'), // Try loopback IP
  ];
  
  for (const testUrl of testUrls) {
    try {
      console.log(`Testing connection to: ${testUrl}/health`);
      
      // Create a timeout promise for React Native compatibility
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Connection timeout')), 3000)
      );
      
      const fetchPromise = fetch(`${testUrl}/health`, { 
        method: 'GET'
      });
      
      const response = await Promise.race([fetchPromise, timeoutPromise]);
      if (response.ok) {
        console.log(`✅ Successfully connected to: ${testUrl}`);
        return true;
      }
    } catch (error) {
      console.warn(`❌ Failed to connect to ${testUrl}:`, error.message);
    }
  }
  
  console.error('❌ All connection attempts failed');
  return false;
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

  // Run connectivity test in development
  setTimeout(async () => {
    try {
      const { testNetworkConnectivity } = await import('../utils/networkDiagnostic');
      await testNetworkConnectivity();
    } catch (error) {
      console.warn('Network diagnostic test failed to load:', error);
    }
  }, 1000);
} 