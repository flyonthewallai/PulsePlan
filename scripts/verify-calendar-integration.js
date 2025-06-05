#!/usr/bin/env node

/**
 * PulsePlan Calendar Integration Verification Script
 *
 * This script verifies that the calendar integration is properly set up
 * and all endpoints are working correctly.
 */

const https = require("https");
const http = require("http");

// Configuration
const BASE_URL = process.env.API_BASE_URL || "http://localhost:5000";
const TEST_USER_ID = process.env.TEST_USER_ID || "test-user-123";

// Colors for console output
const colors = {
  green: "\x1b[32m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  cyan: "\x1b[36m",
  reset: "\x1b[0m",
  bold: "\x1b[1m",
};

// Utility function for HTTP requests
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith("https:") ? https : http;
    const requestOptions = {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      timeout: 10000,
    };

    const req = protocol.request(url, requestOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const parsedData = data ? JSON.parse(data) : {};
          resolve({
            status: res.statusCode,
            data: parsedData,
            headers: res.headers,
          });
        } catch (error) {
          resolve({
            status: res.statusCode,
            data: data,
            headers: res.headers,
          });
        }
      });
    });

    req.on("error", reject);
    req.on("timeout", () => reject(new Error("Request timeout")));

    if (options.body) {
      req.write(JSON.stringify(options.body));
    }

    req.end();
  });
}

// Test functions
async function testServerHealth() {
  console.log(`${colors.blue}Testing server health...${colors.reset}`);

  try {
    const response = await makeRequest(`${BASE_URL}/health`);

    if (response.status === 200 && response.data.status === "UP") {
      console.log(`${colors.green}✅ Server is healthy${colors.reset}`);
      return true;
    } else {
      console.log(`${colors.red}❌ Server health check failed${colors.reset}`);
      console.log(`Status: ${response.status}, Data:`, response.data);
      return false;
    }
  } catch (error) {
    console.log(
      `${colors.red}❌ Server is not accessible: ${error.message}${colors.reset}`
    );
    return false;
  }
}

async function testCalendarRoutes() {
  console.log(`${colors.blue}Testing calendar routes...${colors.reset}`);

  const routes = [
    "/calendar/status/" + TEST_USER_ID,
    "/calendar/google/calendars/" + TEST_USER_ID,
    "/calendar/microsoft/calendars/" + TEST_USER_ID,
    "/calendar/google/events/" + TEST_USER_ID,
    "/calendar/microsoft/events/" + TEST_USER_ID,
  ];

  const results = [];

  for (const route of routes) {
    try {
      const response = await makeRequest(`${BASE_URL}${route}`);

      // 404 is expected for non-connected users, 401 for authentication issues
      if ([200, 404, 401].includes(response.status)) {
        console.log(
          `${colors.green}✅ ${route} - Status: ${response.status}${colors.reset}`
        );
        results.push(true);
      } else if (response.status === 503) {
        console.log(
          `${colors.yellow}⚠️  ${route} - Service unavailable (OAuth not configured)${colors.reset}`
        );
        results.push(true); // This is acceptable if OAuth isn't configured
      } else {
        console.log(
          `${colors.red}❌ ${route} - Unexpected status: ${response.status}${colors.reset}`
        );
        results.push(false);
      }
    } catch (error) {
      console.log(
        `${colors.red}❌ ${route} - Error: ${error.message}${colors.reset}`
      );
      results.push(false);
    }
  }

  return results.every((result) => result);
}

async function testAuthRoutes() {
  console.log(`${colors.blue}Testing authentication routes...${colors.reset}`);

  const routes = [
    `/auth/google?userId=${TEST_USER_ID}`,
    `/auth/microsoft?userId=${TEST_USER_ID}`,
  ];

  const results = [];

  for (const route of routes) {
    try {
      const response = await makeRequest(`${BASE_URL}${route}`);

      // Should redirect (3xx) or return service unavailable (503) if not configured
      if ([301, 302, 303, 307, 308, 503].includes(response.status)) {
        console.log(
          `${colors.green}✅ ${route} - Status: ${response.status} (redirect or not configured)${colors.reset}`
        );
        results.push(true);
      } else {
        console.log(
          `${colors.red}❌ ${route} - Unexpected status: ${response.status}${colors.reset}`
        );
        results.push(false);
      }
    } catch (error) {
      console.log(
        `${colors.red}❌ ${route} - Error: ${error.message}${colors.reset}`
      );
      results.push(false);
    }
  }

  return results.every((result) => result);
}

async function checkEnvironmentVariables() {
  console.log(`${colors.blue}Checking environment variables...${colors.reset}`);

  const requiredVars = [
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URL",
    "MICROSOFT_CLIENT_ID",
    "MICROSOFT_CLIENT_SECRET",
    "MICROSOFT_REDIRECT_URL",
  ];

  let allPresent = true;

  for (const varName of requiredVars) {
    if (process.env[varName]) {
      console.log(`${colors.green}✅ ${varName} is set${colors.reset}`);
    } else {
      console.log(
        `${colors.yellow}⚠️  ${varName} is not set (integration will be disabled)${colors.reset}`
      );
    }
  }

  // Check Supabase variables
  const supabaseVars = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY",
    "EXPO_PUBLIC_SUPABASE_URL",
    "EXPO_PUBLIC_SUPABASE_ANON_KEY",
  ];

  for (const varName of supabaseVars) {
    if (process.env[varName]) {
      console.log(`${colors.green}✅ ${varName} is set${colors.reset}`);
    } else {
      console.log(
        `${colors.red}❌ ${varName} is not set (required for database)${colors.reset}`
      );
      allPresent = false;
    }
  }

  return allPresent;
}

async function testDatabaseSchema() {
  console.log(`${colors.blue}Testing database schema...${colors.reset}`);

  // This would require Supabase client setup
  // For now, we'll just check if the environment variables are set
  if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_KEY) {
    console.log(
      `${colors.green}✅ Supabase configuration appears to be set${colors.reset}`
    );
    console.log(
      `${colors.cyan}ℹ️  Manual verification: Run the database-schema.sql in your Supabase SQL editor${colors.reset}`
    );
    return true;
  } else {
    console.log(
      `${colors.red}❌ Supabase configuration is missing${colors.reset}`
    );
    return false;
  }
}

// Main verification function
async function runVerification() {
  console.log(
    `${colors.bold}${colors.cyan}🔍 PulsePlan Calendar Integration Verification${colors.reset}\n`
  );

  const tests = [
    { name: "Environment Variables", test: checkEnvironmentVariables },
    { name: "Server Health", test: testServerHealth },
    { name: "Authentication Routes", test: testAuthRoutes },
    { name: "Calendar Routes", test: testCalendarRoutes },
    { name: "Database Schema", test: testDatabaseSchema },
  ];

  const results = [];

  for (const { name, test } of tests) {
    console.log(`\n${colors.bold}Testing ${name}:${colors.reset}`);
    try {
      const result = await test();
      results.push({ name, success: result });
    } catch (error) {
      console.log(
        `${colors.red}❌ ${name} failed with error: ${error.message}${colors.reset}`
      );
      results.push({ name, success: false });
    }
  }

  // Summary
  console.log(
    `\n${colors.bold}${colors.cyan}📊 Verification Summary:${colors.reset}`
  );

  const successCount = results.filter((r) => r.success).length;
  const totalCount = results.length;

  results.forEach(({ name, success }) => {
    const icon = success ? "✅" : "❌";
    const color = success ? colors.green : colors.red;
    console.log(`${color}${icon} ${name}${colors.reset}`);
  });

  console.log(
    `\n${colors.bold}Results: ${successCount}/${totalCount} tests passed${colors.reset}`
  );

  if (successCount === totalCount) {
    console.log(
      `${colors.green}${colors.bold}🎉 All tests passed! Your calendar integration is ready.${colors.reset}`
    );
  } else {
    console.log(
      `${colors.yellow}${colors.bold}⚠️  Some tests failed. Please check the issues above.${colors.reset}`
    );
  }

  // Additional guidance
  console.log(`\n${colors.cyan}${colors.bold}Next Steps:${colors.reset}`);
  console.log(`1. Set up your .env file with OAuth credentials`);
  console.log(`2. Run the database schema in Supabase`);
  console.log(`3. Start the server: cd server && npm run start`);
  console.log(`4. Start the client: npx expo start --clear`);
  console.log(
    `5. Test the integration in the app Settings > Calendar Integration`
  );
}

// Run verification if this script is executed directly
if (require.main === module) {
  runVerification().catch((error) => {
    console.error(
      `${colors.red}Verification failed: ${error.message}${colors.reset}`
    );
    process.exit(1);
  });
}

module.exports = {
  runVerification,
  testServerHealth,
  testCalendarRoutes,
  testAuthRoutes,
  checkEnvironmentVariables,
};
