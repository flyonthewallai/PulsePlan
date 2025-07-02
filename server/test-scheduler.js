// Simple test script for the email scheduler system
// Run with: node test-scheduler.js

const BASE_URL = "http://localhost:5000";

async function testSchedulerEndpoints() {
  console.log("🧪 Testing PulsePlan Email Scheduler Endpoints\n");

  // Test 1: Agent Briefing Endpoint
  console.log("1. Testing Daily Briefing Agent API...");
  try {
    const briefingResponse = await fetch(`${BASE_URL}/agents/briefing`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId: "test-user-123" }),
    });

    if (briefingResponse.ok) {
      const data = await briefingResponse.json();
      console.log("✅ Daily Briefing API working");
      console.log(`   Summary: ${data.summary.substring(0, 80)}...`);
    } else {
      console.log("❌ Daily Briefing API failed:", briefingResponse.status);
    }
  } catch (error) {
    console.log("❌ Daily Briefing API error:", error.message);
  }

  // Test 2: Agent Weekly Pulse Endpoint
  console.log("\n2. Testing Weekly Pulse Agent API...");
  try {
    const pulseResponse = await fetch(`${BASE_URL}/agents/weekly-pulse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userId: "test-user-123" }),
    });

    if (pulseResponse.ok) {
      const data = await pulseResponse.json();
      console.log("✅ Weekly Pulse API working");
      console.log(
        `   Completed Tasks: ${data.completedTasks}, Total: ${data.totalTasks}`
      );
    } else {
      console.log("❌ Weekly Pulse API failed:", pulseResponse.status);
    }
  } catch (error) {
    console.log("❌ Weekly Pulse API error:", error.message);
  }

  // Test 3: Scheduler Status (requires auth)
  console.log("\n3. Testing Scheduler Status...");
  try {
    const statusResponse = await fetch(`${BASE_URL}/scheduler/status`);

    if (statusResponse.status === 401) {
      console.log("⚠️  Scheduler Status requires authentication (expected)");
    } else if (statusResponse.ok) {
      const data = await statusResponse.json();
      console.log("✅ Scheduler Status accessible");
      console.log(`   Running: ${data.isRunning}`);
    } else {
      console.log("❌ Scheduler Status failed:", statusResponse.status);
    }
  } catch (error) {
    console.log("❌ Scheduler Status error:", error.message);
  }

  // Test 4: Health Check
  console.log("\n4. Testing Server Health...");
  try {
    const healthResponse = await fetch(`${BASE_URL}/health`);

    if (healthResponse.ok) {
      const data = await healthResponse.json();
      console.log("✅ Server Health OK");
      console.log(`   Status: ${data.status}`);
    } else {
      console.log("❌ Health Check failed:", healthResponse.status);
    }
  } catch (error) {
    console.log("❌ Health Check error:", error.message);
  }

  console.log("\n🎉 Scheduler Test Complete!");
  console.log("\n📋 Next Steps:");
  console.log("   1. Configure your .env file with actual API keys");
  console.log("   2. Set up Supabase database with required tables");
  console.log("   3. Configure Resend API for email sending");
  console.log("   4. Test with real user data");
  console.log("\n📅 Scheduled Jobs:");
  console.log("   • Daily Briefing: Every day at 8:00 AM");
  console.log("   • Weekly Pulse: Every Sunday at 6:00 PM");
}

// Run the tests
testSchedulerEndpoints().catch(console.error);
