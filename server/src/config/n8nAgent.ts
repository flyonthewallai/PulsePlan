import * as dotenv from 'dotenv';

dotenv.config();

export const n8nAgentConfig = {
  baseUrl: process.env.N8N_AGENT_URL || 'https://pulseplan-agent.fly.dev',
  webhookPath: process.env.N8N_WEBHOOK_PATH || '/webhook/agent',
  timeout: parseInt(process.env.N8N_TIMEOUT || '10000'),
  retryAttempts: parseInt(process.env.N8N_RETRY_ATTEMPTS || '3'),
  retryDelay: parseInt(process.env.N8N_RETRY_DELAY || '1000'),
  healthCheckInterval: parseInt(process.env.N8N_HEALTH_CHECK_INTERVAL || '30000'),
  
  // Database timeout configurations
  databaseTimeout: parseInt(process.env.DATABASE_TIMEOUT || '30000'), // 30 seconds for database operations
  databaseQueryTimeout: parseInt(process.env.DATABASE_QUERY_TIMEOUT || '20000'), // 20 seconds for individual queries
  databaseBatchTimeout: parseInt(process.env.DATABASE_BATCH_TIMEOUT || '60000'), // 60 seconds for batch operations
  
  // Feature flags
  enableBatchProcessing: process.env.N8N_ENABLE_BATCH_PROCESSING !== 'false',
  enableIntelligentRescheduling: process.env.N8N_ENABLE_INTELLIGENT_RESCHEDULING !== 'false',
  enableStudyOptimization: process.env.N8N_ENABLE_STUDY_OPTIMIZATION !== 'false',
  enableDeadlineAnalysis: process.env.N8N_ENABLE_DEADLINE_ANALYSIS !== 'false',
  
  // Logging
  enableLogging: process.env.N8N_ENABLE_LOGGING !== 'false',
  logLevel: process.env.N8N_LOG_LEVEL || 'info',
};

export default n8nAgentConfig; 