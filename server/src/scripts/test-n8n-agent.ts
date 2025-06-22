import { n8nAgentService } from '../services/n8nAgentService';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testN8nAgent() {
  console.log('🧪 Testing n8n Agent Connection...\n');

  // Test 1: Health Check
  console.log('1. Testing health check...');
  try {
    const isHealthy = await n8nAgentService.healthCheck();
    console.log(`   ✅ Health check result: ${isHealthy ? 'HEALTHY' : 'UNHEALTHY'}\n`);
  } catch (error) {
    console.log(`   ❌ Health check failed: ${error}\n`);
  }

  // Test 2: Basic Task Creation
  console.log('2. Testing basic task creation...');
  try {
    const testResponse = await n8nAgentService.createTaskFromUser(
      'test-user-123',
      'Test Task - Study for Chemistry Exam',
      new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // Due in 7 days
      120, // 2 hours
      'high',
      'Chemistry'
    );

    console.log('   Response:', JSON.stringify(testResponse, null, 2));
    console.log(`   ✅ Task creation test: ${testResponse.success ? 'SUCCESS' : 'FAILED'}\n`);
  } catch (error) {
    console.log(`   ❌ Task creation test failed: ${error}\n`);
  }

  // Test 3: Agent-Driven Task Creation
  console.log('3. Testing agent-driven task creation...');
  try {
    const agentResponse = await n8nAgentService.createTaskWithAgent(
      'test-user-123',
      'Agent Task - Intelligent Math Study Session',
      new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(), // Due in 3 days
      90, // 1.5 hours
      'medium',
      'Mathematics',
      'smart-schedule'
    );

    console.log('   Response:', JSON.stringify(agentResponse, null, 2));
    console.log(`   ✅ Agent task creation test: ${agentResponse.success ? 'SUCCESS' : 'FAILED'}\n`);
  } catch (error) {
    console.log(`   ❌ Agent task creation test failed: ${error}\n`);
  }

  // Test 4: Custom Payload
  console.log('4. Testing custom payload...');
  try {
    const customResponse = await n8nAgentService.postToAgent({
      userId: 'test-user-123',
      taskTitle: 'Custom Test Task',
      dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      duration: 60,
      priority: 'low',
      subject: 'Testing',
      source: 'user',
      tool: 'test-tool',
      customField: 'This is a custom field',
      metadata: {
        testMode: true,
        timestamp: new Date().toISOString(),
      },
    });

    console.log('   Response:', JSON.stringify(customResponse, null, 2));
    console.log(`   ✅ Custom payload test: ${customResponse.success ? 'SUCCESS' : 'FAILED'}\n`);
  } catch (error) {
    console.log(`   ❌ Custom payload test failed: ${error}\n`);
  }

  // Test 5: Natural Language Query
  console.log('5. Testing natural language query...');
  try {
    const nlResponse = await n8nAgentService.processNaturalLanguage({
      userId: 'test-user-123',
      query: 'create a task to study for math exam tomorrow for 2 hours',
      date: new Date().toISOString(),
      duration: 120,
      source: 'app',
      context: {
        currentPage: 'agent',
        userPreferences: { workingHours: '9-17' },
        recentTasks: []
      }
    });

    console.log('   Response:', JSON.stringify(nlResponse, null, 2));
    console.log(`   ✅ Natural language test: ${nlResponse.success ? 'SUCCESS' : 'FAILED'}\n`);
  } catch (error) {
    console.log(`   ❌ Natural language test failed: ${error}\n`);
  }

  // Test 6: Email Natural Language Query
  console.log('6. Testing email natural language query...');
  try {
    const emailResponse = await n8nAgentService.processNaturalLanguage({
      userId: 'test-user-123',
      query: 'email my professor asking about the assignment deadline',
      date: new Date().toISOString(),
      source: 'app',
      context: {
        currentPage: 'email',
        contacts: [
          { name: 'Professor Smith', email: 'professor.smith@university.edu' }
        ]
      }
    });

    console.log('   Response:', JSON.stringify(emailResponse, null, 2));
    console.log(`   ✅ Email query test: ${emailResponse.success ? 'SUCCESS' : 'FAILED'}\n`);
  } catch (error) {
    console.log(`   ❌ Email query test failed: ${error}\n`);
  }

  console.log('🎉 n8n Agent testing completed!');
}

// Run the test if this script is executed directly
if (require.main === module) {
  testN8nAgent().catch(console.error);
}

export { testN8nAgent }; 