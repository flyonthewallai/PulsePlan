import { n8nAgentService } from '../services/n8nAgentService';
import supabase from '../config/supabase';
import n8nAgentConfig from '../config/n8nAgent';

/**
 * Test script to verify database timeout configurations for agent operations
 */
async function testDatabaseTimeouts() {
  console.log('🔧 Testing Database Timeout Configurations');
  console.log('==========================================');
  
  // Display current timeout configurations
  console.log('\n📊 Current Timeout Settings:');
  console.log(`- Database Timeout: ${n8nAgentConfig.databaseTimeout}ms (${n8nAgentConfig.databaseTimeout / 1000}s)`);
  console.log(`- Database Query Timeout: ${n8nAgentConfig.databaseQueryTimeout}ms (${n8nAgentConfig.databaseQueryTimeout / 1000}s)`);
  console.log(`- Database Batch Timeout: ${n8nAgentConfig.databaseBatchTimeout}ms (${n8nAgentConfig.databaseBatchTimeout / 1000}s)`);
  console.log(`- N8N Agent Timeout: ${n8nAgentConfig.timeout}ms (${n8nAgentConfig.timeout / 1000}s)`);

  // Test Supabase connection
  console.log('\n🔌 Testing Supabase Connection:');
  if (!supabase) {
    console.error('❌ Supabase client not configured');
    return;
  }
  console.log('✅ Supabase client configured');

  // Test database query with timeout
  console.log('\n🔍 Testing Database Query with Timeout:');
  try {
    const startTime = Date.now();
    
    // Test a simple query to check if the database is responsive
    const { data: testQuery, error } = await supabase
      .from('users')
      .select('id')
      .limit(1);
    
    const queryTime = Date.now() - startTime;
    
    if (error) {
      console.error('❌ Database query failed:', error.message);
    } else {
      console.log(`✅ Database query successful in ${queryTime}ms`);
    }
  } catch (error) {
    console.error('❌ Database query error:', error instanceof Error ? error.message : 'Unknown error');
  }

  // Test n8n agent service timeout configurations
  console.log('\n🤖 Testing N8N Agent Service Timeout Methods:');
  try {
    // This will test the private getTimeout method indirectly through the service
    const testUserId = 'test-user-id';
    console.log('📝 Testing getUserConnectedAccounts with timeout handling...');
    
    // This should use the database query timeout
    const startTime = Date.now();
    const result = await n8nAgentService['getUserConnectedAccounts'](testUserId);
    const operationTime = Date.now() - startTime;
    
    console.log(`✅ getUserConnectedAccounts completed in ${operationTime}ms`);
    console.log(`📊 Connected accounts found: ${Object.keys(result).length}`);
  } catch (error) {
    console.error('❌ N8N Agent Service test failed:', error instanceof Error ? error.message : 'Unknown error');
  }

  // Test n8n agent health check with short timeout
  console.log('\n🏥 Testing N8N Agent Health Check:');
  try {
    const startTime = Date.now();
    const isHealthy = await n8nAgentService.healthCheck();
    const healthCheckTime = Date.now() - startTime;
    
    if (isHealthy) {
      console.log(`✅ N8N Agent is healthy (responded in ${healthCheckTime}ms)`);
    } else {
      console.log(`⚠️ N8N Agent health check failed (took ${healthCheckTime}ms)`);
    }
  } catch (error) {
    console.error('❌ N8N Agent health check error:', error instanceof Error ? error.message : 'Unknown error');
  }

  console.log('\n🎉 Database timeout configuration test completed!');
  console.log('\n💡 Tips:');
  console.log('- Increase DATABASE_TIMEOUT if operations frequently time out');
  console.log('- Increase DATABASE_QUERY_TIMEOUT for complex queries');
  console.log('- Increase DATABASE_BATCH_TIMEOUT for bulk operations');
  console.log('- Monitor logs for timeout-related errors');
}

// Run the test if this script is executed directly
if (require.main === module) {
  testDatabaseTimeouts()
    .then(() => {
      console.log('\n✅ Test completed successfully');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n❌ Test failed:', error);
      process.exit(1);
    });
}

export { testDatabaseTimeouts }; 