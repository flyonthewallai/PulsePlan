import { Redis } from '@upstash/redis';

// Validate configuration
if (!process.env.UPSTASH_REDIS_REST_URL || !process.env.UPSTASH_REDIS_REST_TOKEN) {
  console.error('❌ Upstash Redis configuration missing! Please set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN');
  throw new Error('Upstash Redis configuration missing');
}

// Upstash Redis configuration
const upstashConfig = {
  url: process.env.UPSTASH_REDIS_REST_URL as string,
  token: process.env.UPSTASH_REDIS_REST_TOKEN as string,
};

// Create Upstash Redis client
export const redisClient = new Redis(upstashConfig);

// Test connection and log status
let isRedisAvailable = false;

const testConnection = async () => {
  try {
    await redisClient.ping();
    isRedisAvailable = true;
    console.log('✅ Upstash Redis connected successfully');
    console.log(`🌐 Connected to: ${upstashConfig.url.replace(/\/\/.*@/, '//***@')}`);
  } catch (error) {
    isRedisAvailable = false;
    console.error('❌ Upstash Redis connection error:', error);
  }
};

// Test connection on startup
testConnection();

// Health check function
export const isRedisHealthy = async (): Promise<boolean> => {
  try {
    await redisClient.ping();
    return true;
  } catch (error) {
    console.error('Upstash Redis health check failed:', error);
    return false;
  }
};

// Get connection status
export const getRedisStatus = () => isRedisAvailable;

export default redisClient; 