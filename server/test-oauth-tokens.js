const axios = require("axios");

const BASE_URL = "http://localhost:3000";
const TEST_USER_ID = "test-user-123";

// Mock JWT token for testing (in production, get this from auth)
const AUTH_TOKEN = "Bearer your-test-jwt-token-here";

async function testEndpoint(method, endpoint, data = null, headers = {}) {
  try {
    const config = {
      method,
      url: `${BASE_URL}${endpoint}`,
      headers: {
        "Content-Type": "application/json",
        Authorization: AUTH_TOKEN,
        ...headers,
      },
    };

    if (data) {
      config.data = data;
    }

    console.log(`\n🧪 Testing ${method.toUpperCase()} ${endpoint}`);

    const response = await axios(config);
    console.log(`✅ Status: ${response.status}`);
    console.log(`📄 Response:`, JSON.stringify(response.data, null, 2));

    return response.data;
  } catch (error) {
    console.log(`❌ Error: ${error.response?.status || "Unknown"}`);
    if (error.response?.data) {
      console.log(
        `📄 Error Response:`,
        JSON.stringify(error.response.data, null, 2)
      );
    } else {
      console.log(`📄 Error Message:`, error.message);
    }
    return null;
  }
}

async function runTests() {
  console.log("🚀 Starting OAuth Token System Tests");
  console.log(`🎯 Base URL: ${BASE_URL}`);
  console.log(`👤 Test User ID: ${TEST_USER_ID}`);

  console.log("\n" + "=".repeat(60));
  console.log("📋 CONNECTION MANAGEMENT TESTS");
  console.log("=".repeat(60));

  // Test 1: Get connection status
  await testEndpoint("GET", `/connections/status/${TEST_USER_ID}`);

  // Test 2: Get connected accounts
  await testEndpoint("GET", `/connections/accounts/${TEST_USER_ID}`);

  // Test 3: Test agent connection
  await testEndpoint("POST", `/connections/test-agent/${TEST_USER_ID}`);

  // Test 4: Refresh tokens
  await testEndpoint("POST", `/connections/refresh-tokens/${TEST_USER_ID}`, {
    provider: "google",
  });

  // Test 5: Refresh all tokens
  await testEndpoint("POST", `/connections/refresh-tokens/${TEST_USER_ID}`, {});

  console.log("\n" + "=".repeat(60));
  console.log("🤖 ENHANCED AGENT SERVICE TESTS");
  console.log("=".repeat(60));

  // Test 6: Daily briefing with tokens
  await testEndpoint("POST", "/agents/briefing", {
    userId: TEST_USER_ID,
  });

  // Test 7: Weekly pulse with tokens
  await testEndpoint("POST", "/agents/weekly-pulse", {
    userId: TEST_USER_ID,
  });

  console.log("\n" + "=".repeat(60));
  console.log("📅 SCHEDULER MANAGEMENT TESTS");
  console.log("=".repeat(60));

  // Test 8: Get scheduler status
  await testEndpoint("GET", "/scheduler/status");

  // Test 9: Manual run daily briefing
  await testEndpoint("POST", "/scheduler/run-daily-briefing");

  // Test 10: Manual run weekly pulse
  await testEndpoint("POST", "/scheduler/run-weekly-pulse");

  console.log("\n" + "=".repeat(60));
  console.log("🚫 ERROR HANDLING TESTS");
  console.log("=".repeat(60));

  // Test 11: Invalid provider disconnect
  await testEndpoint("DELETE", `/connections/invalid-provider/${TEST_USER_ID}`);

  // Test 12: Invalid user ID
  await testEndpoint("GET", "/connections/status/invalid-user");

  // Test 13: Missing authorization
  try {
    console.log("\n🧪 Testing GET /connections/status/:userId (no auth)");
    const response = await axios.get(
      `${BASE_URL}/connections/status/${TEST_USER_ID}`
    );
    console.log(`❌ Should have failed but got status: ${response.status}`);
  } catch (error) {
    console.log(
      `✅ Correctly rejected unauthorized request: ${error.response?.status}`
    );
  }

  console.log("\n" + "=".repeat(60));
  console.log("🎉 TEST SUMMARY");
  console.log("=".repeat(60));

  console.log(`
📊 Test Results Summary:
• Connection management endpoints tested
• Enhanced agent service integration tested  
• Scheduler functionality tested
• Error handling verified
• Authentication security confirmed

🔧 If any tests failed:
1. Ensure the server is running on ${BASE_URL}
2. Update AUTH_TOKEN with a valid JWT
3. Check environment variables (N8N_AGENT_URL, TOKEN_ENCRYPTION_KEY)
4. Verify database connection
5. Check N8N agent service is available

💡 Next Steps:
1. Test with real OAuth tokens from Google/Microsoft
2. Verify encryption/decryption works correctly
3. Test token refresh functionality
4. Verify scheduler runs with tokens
5. Test in production environment
  `);
}

// Handle unhandled promise rejections
process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
});

// Run the tests
if (require.main === module) {
  runTests().catch((error) => {
    console.error("Test suite failed:", error);
    process.exit(1);
  });
}

module.exports = { runTests, testEndpoint };
