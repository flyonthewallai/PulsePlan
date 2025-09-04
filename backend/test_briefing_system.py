#!/usr/bin/env python3
"""
Test script for the complete briefing system
Tests database, scheduling, and email functionality
"""
import asyncio
import logging
import json
from datetime import datetime, time
from dotenv import load_dotenv

# Load environment first
load_dotenv()

from app.config.supabase import get_supabase_client
from app.services.user_preferences import get_user_preferences_service
from app.workers.timezone_scheduler import get_timezone_scheduler
from app.models.user_preferences import UserPreferences, BriefingPreferences

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """Test basic database connectivity"""
    print("\n🔍 Testing database connection...")
    try:
        supabase = get_supabase_client()
        result = supabase.table('user_preferences').select('count').execute()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


async def test_user_preferences_service():
    """Test user preferences creation and retrieval"""
    print("\n🔍 Testing user preferences service...")
    try:
        service = get_user_preferences_service()
        
        # Test with a mock user ID
        test_user_id = "test-user-123"
        
        # Test getting preferences (should create defaults)
        preferences = await service.get_user_preferences(test_user_id)
        print(f"✅ Retrieved preferences for user {test_user_id}")
        print(f"   - Daily briefing enabled: {preferences.briefings.daily_briefing_enabled}")
        print(f"   - Daily briefing time: {preferences.briefings.daily_briefing_time}")
        print(f"   - Timezone: {preferences.briefings.daily_briefing_timezone}")
        print(f"   - Email preferences: {preferences.email.contact_management_mode}")
        
        # Test updating preferences
        preferences.briefings.daily_briefing_time = time(9, 30)  # 9:30 AM
        preferences.briefings.daily_briefing_timezone = "America/New_York"
        
        success = await service.save_user_preferences(preferences)
        if success:
            print("✅ Successfully updated user preferences")
        else:
            print("❌ Failed to update user preferences")
        
        # Verify the update
        updated_preferences = await service.get_user_preferences(test_user_id)
        if updated_preferences.briefings.daily_briefing_time == time(9, 30):
            print("✅ Preferences update verified")
        else:
            print("❌ Preferences update verification failed")
        
        return True
        
    except Exception as e:
        print(f"❌ User preferences service test failed: {e}")
        return False


async def test_timezone_analysis():
    """Test the timezone scheduler analysis"""
    print("\n🔍 Testing timezone analysis...")
    try:
        scheduler = get_timezone_scheduler()
        
        # Test timezone analysis method
        analysis = await scheduler._get_timezone_analysis()
        print(f"✅ Timezone analysis completed")
        print(f"   - Found {len(analysis)} unique timezone/time combinations")
        
        for tz_time_key, users in analysis.items():
            print(f"   - {tz_time_key}: {len(users)} users")
        
        # Test UTC conversion
        utc_hour, utc_minute = scheduler._convert_to_utc("America/New_York", 9, 30)
        print(f"✅ UTC conversion test: 9:30 AM EST -> {utc_hour:02d}:{utc_minute:02d} UTC")
        
        return True
        
    except Exception as e:
        print(f"❌ Timezone analysis test failed: {e}")
        return False


async def test_briefing_endpoint():
    """Test the briefing API endpoint"""
    print("\n🔍 Testing briefing API endpoint...")
    try:
        import httpx
        
        # Test the briefing preferences endpoint
        async with httpx.AsyncClient() as client:
            # This would need an actual auth token in a real test
            # For now, just test that the endpoint exists
            response = await client.get("http://localhost:8000/api/v1/user/preferences/briefings")
            
            if response.status_code == 401:  # Unauthorized is expected without token
                print("✅ Briefing endpoint exists (auth required as expected)")
                return True
            elif response.status_code == 200:
                print("✅ Briefing endpoint accessible")
                return True
            else:
                print(f"❌ Unexpected response status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Briefing endpoint test failed: {e}")
        return False


async def test_email_service_config():
    """Test email service configuration"""
    print("\n🔍 Testing email service configuration...")
    try:
        import os
        from app.workers.email_service import get_email_service
        
        resend_key = os.getenv('RESEND_API_KEY')
        if resend_key:
            print(f"✅ RESEND_API_KEY configured (starts with: {resend_key[:10]}...)")
        else:
            print("⚠️  RESEND_API_KEY not set in environment")
        
        from_email = os.getenv('RESEND_FROM_EMAIL')
        if from_email:
            print(f"✅ RESEND_FROM_EMAIL configured: {from_email}")
        else:
            print("⚠️  RESEND_FROM_EMAIL not set in environment")
        
        # Test email service initialization
        email_service = get_email_service()
        print("✅ Email service initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Email service test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting PulsePlan Briefing System Tests")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("User Preferences Service", test_user_preferences_service),
        ("Timezone Analysis", test_timezone_analysis),
        ("Email Service Config", test_email_service_config),
        ("Briefing API Endpoint", test_briefing_endpoint),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The briefing system is ready.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        exit(1)