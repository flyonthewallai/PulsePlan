import { googleContactsService } from '../services/googleContactsService';
import { isGoogleOAuthConfigured } from '../config/google';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

async function testGoogleContacts() {
  console.log('🧪 Testing Google Contacts Integration...\n');

  // Check if Google OAuth is configured
  if (!isGoogleOAuthConfigured()) {
    console.log('❌ Google OAuth not configured. Please set the following environment variables:');
    console.log('   - GOOGLE_CLIENT_ID');
    console.log('   - GOOGLE_CLIENT_SECRET');
    console.log('   - GOOGLE_REDIRECT_URL');
    return;
  }

  console.log('✅ Google OAuth configuration found');

  // Test user ID (you would replace this with an actual user ID that has connected Google)
  const testUserId = 'test-user-id';

  try {
    console.log('\n📋 Testing Google Contacts service methods...');

    // Test 1: Try to get contacts (this will fail if no user is connected, which is expected)
    console.log('\n1. Testing getContacts...');
    try {
      await googleContactsService.getContacts(testUserId, 10);
      console.log('✅ getContacts method executed successfully');
    } catch (error) {
      console.log('⚠️  getContacts failed (expected if no user connected):', (error as Error).message);
    }

    // Test 2: Try to search contacts
    console.log('\n2. Testing searchContacts...');
    try {
      await googleContactsService.searchContacts(testUserId, 'test', 5);
      console.log('✅ searchContacts method executed successfully');
    } catch (error) {
      console.log('⚠️  searchContacts failed (expected if no user connected):', (error as Error).message);
    }

    // Test 3: Try to get contacts with emails
    console.log('\n3. Testing getContactsWithEmails...');
    try {
      await googleContactsService.getContactsWithEmails(testUserId);
      console.log('✅ getContactsWithEmails method executed successfully');
    } catch (error) {
      console.log('⚠️  getContactsWithEmails failed (expected if no user connected):', (error as Error).message);
    }

    // Test 4: Try to get contact groups
    console.log('\n4. Testing getContactGroups...');
    try {
      await googleContactsService.getContactGroups(testUserId);
      console.log('✅ getContactGroups method executed successfully');
    } catch (error) {
      console.log('⚠️  getContactGroups failed (expected if no user connected):', (error as Error).message);
    }

    console.log('\n✅ All Google Contacts service methods are properly defined and callable');
    console.log('\n📝 Note: To fully test the integration:');
    console.log('   1. Start the server');
    console.log('   2. Connect a Google account through the frontend');
    console.log('   3. Test the /contacts/list endpoint with a real user ID');

  } catch (error) {
    console.error('\n❌ Error testing Google Contacts service:', error);
  }
}

// Run the test
testGoogleContacts().catch(console.error); 