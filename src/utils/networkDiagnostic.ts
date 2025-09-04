import { Platform } from 'react-native';
import Constants from 'expo-constants';
import { API_URL } from '../config/api';

// Use the same API configuration as the main app
const apiUrl = API_URL;
const apiPort = '5000';

/**
 * Test multiple connection endpoints for Windows compatibility
 */
export const testNetworkConnectivity = async (): Promise<{
  success: boolean;
  workingUrl?: string;
  results: Array<{ url: string; success: boolean; error?: string; responseTime?: number }>;
}> => {
  // Generate test URLs based on platform and current API URL
  const testUrls = [apiUrl]; // Always test the configured API URL first
  
  // Only add localhost variants if we're not already using them
  if (!apiUrl.includes('localhost') && !apiUrl.includes('127.0.0.1')) {
    testUrls.push(`http://localhost:${apiPort}`);
    testUrls.push(`http://127.0.0.1:${apiPort}`);
  }
  
  // Add platform-specific alternatives
  if (Platform.OS === 'ios' && !apiUrl.includes('10.0.0.4')) {
    testUrls.push(`http://10.0.0.4:${apiPort}`); // Windows host IP for iOS
  }
  if (Platform.OS === 'android' && !apiUrl.includes('10.0.2.2')) {
    testUrls.push(`http://10.0.2.2:${apiPort}`); // Android emulator host IP
  }

  // Remove duplicates
  const uniqueUrls = [...new Set(testUrls)];
  
  const results: Array<{ url: string; success: boolean; error?: string; responseTime?: number }> = [];
  let workingUrl: string | undefined;

  console.log('🔍 Starting network connectivity test...');
  console.log(`Platform: ${Platform.OS}`);
  console.log(`Test URLs: ${uniqueUrls.join(', ')}`);

  for (const testUrl of uniqueUrls) {
    const startTime = Date.now();
    
    try {
      console.log(`Testing: ${testUrl}/health`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch(`${testUrl}/health`, {
        method: 'GET',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      });
      
      clearTimeout(timeoutId);
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        const data = await response.json();
        console.log(`✅ Success: ${testUrl} (${responseTime}ms)`, data);
        
        results.push({ url: testUrl, success: true, responseTime });
        
        if (!workingUrl) {
          workingUrl = testUrl;
        }
      } else {
        console.log(`❌ HTTP Error: ${testUrl} - Status: ${response.status}`);
        results.push({ 
          url: testUrl, 
          success: false, 
          error: `HTTP ${response.status}`,
          responseTime 
        });
      }
    } catch (error) {
      const responseTime = Date.now() - startTime;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      
      console.log(`❌ Network Error: ${testUrl} - ${errorMessage} (${responseTime}ms)`);
      results.push({ 
        url: testUrl, 
        success: false, 
        error: errorMessage,
        responseTime 
      });
    }
  }

  const success = results.some(result => result.success);
  
  console.log('📊 Network test results:', {
    success,
    workingUrl,
    results
  });

  return { success, workingUrl, results };
};

/**
 * Get the best API URL based on connectivity test
 */
export const getBestApiUrl = async (): Promise<string> => {
  const { workingUrl } = await testNetworkConnectivity();
  return workingUrl || apiUrl; // Fallback to default if no working URL found
};

/**
 * Simple ping test for a specific URL
 */
export const pingUrl = async (url: string, timeout: number = 3000): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(`${url}/health`, {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    return response.ok;
  } catch {
    return false;
  }
}; 