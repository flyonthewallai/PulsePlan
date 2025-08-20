#!/usr/bin/env node

/**
 * Test script for n8n status integration
 * Run with: node test-n8n-status.js
 */

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:5000";
const TEST_USER_ID = "test-user-123";

async function makeRequest(endpoint, data) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      console.log(`✅ ${endpoint}: Success`);
      console.log(`   Response:`, result);
    } else {
      console.log(`❌ ${endpoint}: Failed (${response.status})`);
      console.log(`   Error:`, result);
    }

    return { success: response.ok, data: result };
  } catch (error) {
    console.log(`❌ ${endpoint}: Network error`);
    console.log(`   Error:`, error.message);
    return { success: false, error: error.message };
  }
}

async function testN8nStatusIntegration() {
  console.log("🧪 Testing n8n Status Integration");
  console.log("=====================================");
  console.log(`API Base URL: ${API_BASE_URL}`);
  console.log(`Test User ID: ${TEST_USER_ID}`);
  console.log("");

  // Test 1: Workflow Start
  console.log("1. Testing Workflow Start...");
  await makeRequest("/api/n8n/status/start", {
    userId: TEST_USER_ID,
    workflowName: "Test Email Processing",
    message: "Starting email analysis workflow...",
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 2: Subworkflow Status (Active)
  console.log("2. Testing Subworkflow Status (Active)...");
  await makeRequest("/api/n8n/status/subworkflow", {
    userId: TEST_USER_ID,
    mainWorkflow: "Test Email Processing",
    subworkflow: "Gmail API",
    status: "active",
    message: "Fetching emails from Gmail...",
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 3: Subworkflow Status (Completed)
  console.log("3. Testing Subworkflow Status (Completed)...");
  await makeRequest("/api/n8n/status/subworkflow", {
    userId: TEST_USER_ID,
    mainWorkflow: "Test Email Processing",
    subworkflow: "Gmail API",
    status: "completed",
    message: "Successfully fetched 15 emails",
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 4: Another Subworkflow
  console.log("4. Testing Another Subworkflow...");
  await makeRequest("/api/n8n/status/subworkflow", {
    userId: TEST_USER_ID,
    mainWorkflow: "Test Email Processing",
    subworkflow: "Email Analysis",
    status: "active",
    message: "Analyzing email content...",
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 5: Workflow Completion
  console.log("5. Testing Workflow Completion...");
  await makeRequest("/api/n8n/status/complete", {
    userId: TEST_USER_ID,
    workflowName: "Test Email Processing",
    message: "Successfully processed 15 emails and generated summary",
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 6: Custom Status
  console.log("6. Testing Custom Status...");
  await makeRequest("/api/n8n/status/custom", {
    userId: TEST_USER_ID,
    tool: "Calendar Sync",
    status: "active",
    message: "Syncing calendar events...",
    metadata: {
      eventsProcessed: 25,
      totalEvents: 100,
    },
  });
  console.log("");

  // Wait a moment
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // Test 7: Error Status
  console.log("7. Testing Error Status...");
  await makeRequest("/api/n8n/status/error", {
    userId: TEST_USER_ID,
    workflowName: "Test Error Workflow",
    error: "Failed to authenticate with Gmail API",
  });
  console.log("");

  console.log("🎉 Test sequence completed!");
  console.log("");
  console.log("📊 Check the frontend to see the status updates in real-time.");
  console.log("📝 Check server logs for WebSocket broadcast messages.");
}

// Handle fetch import for Node.js
if (typeof fetch === "undefined") {
  const { default: fetch } = await import("node-fetch");
  global.fetch = fetch;
}

// Run the test
testN8nStatusIntegration().catch(console.error);
