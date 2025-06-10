/**
 * Extension Configuration
 * Centralized configuration for different environments
 */

// Environment detection
const isDevelopment =
  typeof chrome !== "undefined" &&
  chrome.runtime &&
  chrome.runtime.getManifest().version_name?.includes("dev");

// API Configuration
const API_CONFIG = {
  development: {
    base_url: "http://localhost:5000",
    ws_url: "ws://localhost:5000",
  },
  production: {
    base_url: "https://api.pulseplan.app", // Update this when you deploy
    ws_url: "wss://api.pulseplan.app",
  },
};

// Current environment
const currentEnv = isDevelopment ? "development" : "production";
const config = API_CONFIG[currentEnv];

// Exported configuration
window.EXTENSION_CONFIG = {
  API_BASE_URL: config.base_url,
  WS_BASE_URL: config.ws_url,
  ENVIRONMENT: currentEnv,

  // API Endpoints
  ENDPOINTS: {
    CANVAS_UPLOAD: `${config.base_url}/canvas/upload-data`,
    CANVAS_CONNECT: `${config.base_url}/canvas/connect-extension`,
    EXTRACT_HTML: `${config.base_url}/scraping/extract-html`,
    HEALTH_CHECK: `${config.base_url}/health`,
  },

  // Extension Settings
  SCRAPING_COOLDOWN: 5000, // 5 seconds between AI requests
  MAX_HTML_SIZE: 50000, // Limit HTML size for AI processing
  CACHE_DURATION: 300000, // 5 minutes cache duration
};

console.log(`🔧 Extension Config: Running in ${currentEnv} mode`);
console.log(`🌐 API Base URL: ${config.base_url}`);

// Export for use in other scripts
if (typeof module !== "undefined" && module.exports) {
  module.exports = window.EXTENSION_CONFIG;
}
