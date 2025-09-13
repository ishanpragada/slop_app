import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Manual IP override - update this when your IP changes
const MANUAL_IP_OVERRIDE = '192.168.68.100'; // Change this to your current IP

// Automatic IP detection
const getApiBaseUrl = () => {
  // For web development, use localhost
  if (Platform.OS === 'web') {
    console.log('Web platform detected, using localhost');
    return 'http://localhost:8000/api/v1';
  }
  
  // For mobile/simulator, try to get the development server URL from Expo
  const manifest = Constants.expoConfig;
  const debuggerHost = manifest?.hostUri?.split(':').shift();
  
  if (debuggerHost) {
    console.log('Auto-detected IP from Expo:', debuggerHost);
    return `http://${debuggerHost}:8000/api/v1`;
  }
  
  // Fallback to manual IP
  console.log('Using manual IP override:', MANUAL_IP_OVERRIDE);
  return `http://${MANUAL_IP_OVERRIDE}:8000/api/v1`;
};

// Export the configuration
export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: 10000, // 10 seconds
  MANUAL_IP: MANUAL_IP_OVERRIDE,
  ENDPOINTS: {
    FINITE_FEED: '/feed',      // Original finite feed
    INFINITE_FEED: '/feed/infinite',  // New infinite feed
  },
};

// Helper function to get current IP for debugging
export const getCurrentIP = () => {
  const manifest = Constants.expoConfig;
  const debuggerHost = manifest?.hostUri?.split(':').shift();
  return debuggerHost || MANUAL_IP_OVERRIDE;
};

// Helper function to test API connectivity
export const testApiConnection = async () => {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL.replace('/api/v1', '')}/health`);
    if (response.ok) {
      console.log('✅ API connection successful');
      return true;
    } else {
      console.log('❌ API connection failed:', response.status);
      return false;
    }
  } catch (error) {
    console.log('❌ API connection error:', error);
    return false;
  }
};

export default API_CONFIG; 