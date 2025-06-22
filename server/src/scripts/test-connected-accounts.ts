import { N8nAgentService } from '../services/n8nAgentService';

async function testConnectedAccounts() {
  console.log('🧪 Testing Connected Accounts Integration...\n');

  const n8nService = new N8nAgentService();
  
  // Test with a sample user ID (replace with actual user ID from your database)
  const testUserId = 'test-user-id'; // Replace with real user ID who has connected accounts
  
  try {
    console.log('📤 Sending test query to n8n with connected accounts...');
    
    const response = await n8nService.processNaturalLanguage({
      userId: testUserId,
      query: 'Check my emails from today and show me my calendar for this afternoon',
      date: new Date().toISOString(),
      source: 'app',
      context: {
        currentPage: 'agent',
        recentTasks: [],
        chatHistory: [],
        workingHours: {
          start: '09:00',
          end: '17:00',
          timezone: 'America/New_York'
        }
      }
    });

    console.log('📥 n8n Response:');
    console.log(JSON.stringify(response, null, 2));

    if (response.success) {
      console.log('\n✅ Test completed successfully!');
      console.log('Connected accounts should be visible in n8n workflow execution logs.');
    } else {
      console.log('\n❌ Test failed:');
      console.log('Error:', response.error);
    }

  } catch (error) {
    console.error('\n💥 Test error:', error);
  }
}

// Example of how to test with specific connected accounts
async function testWithMockConnectedAccounts() {
  console.log('\n🎭 Testing with mock connected accounts (for development)...\n');

  // This would typically be fetched from the database
  const mockPayload = {
    userId: 'mock-user-id',
    query: 'What emails did I receive today?',
    date: new Date().toISOString(),
    source: 'app' as const,
    context: {
      currentPage: 'agent',
      recentTasks: [],
      chatHistory: []
    },
    connectedAccounts: {
      google: {
        accessToken: 'mock-google-token',
        refreshToken: 'mock-google-refresh',
        email: 'user@gmail.com',
        expiresAt: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
      },
      microsoft: {
        accessToken: 'mock-microsoft-token',
        refreshToken: 'mock-microsoft-refresh',
        email: 'user@outlook.com',
        expiresAt: new Date(Date.now() + 3600000).toISOString() // 1 hour from now
      }
    }
  };

  console.log('Mock payload structure:');
  console.log(JSON.stringify({
    ...mockPayload,
    connectedAccounts: {
      google: { ...mockPayload.connectedAccounts.google, accessToken: '***MASKED***', refreshToken: '***MASKED***' },
      microsoft: { ...mockPayload.connectedAccounts.microsoft, accessToken: '***MASKED***', refreshToken: '***MASKED***' }
    }
  }, null, 2));

  console.log('\n📝 This payload structure should be sent to your n8n webhook.');
  console.log('Your n8n workflow can access tokens via: $json.connectedAccounts.google.accessToken');
}

// Instructions for setting up the test
function printInstructions() {
  console.log('\n📋 Setup Instructions:');
  console.log('1. Make sure you have a user with connected accounts in your database');
  console.log('2. Update the testUserId variable with a real user ID');
  console.log('3. Ensure your n8n workflow is running and accessible');
  console.log('4. Run this test to verify connected accounts are included in the payload');
  console.log('\n🔧 To check connected accounts in your database:');
  console.log('SELECT user_id, provider, email, expires_at FROM calendar_connections;');
}

// Run the tests
async function main() {
  printInstructions();
  
  // Uncomment the test you want to run:
  // await testConnectedAccounts();
  await testWithMockConnectedAccounts();
}

if (require.main === module) {
  main().catch(console.error);
} 