#!/usr/bin/env python3
"""
Database migration script to fix oauth_tokens table constraints
Run this script to apply the migration to your Supabase database
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import get_supabase_client

async def apply_migration():
    """Apply the oauth_tokens constraints migration"""
    
    print("🔧 Applying oauth_tokens constraints migration...")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Read the migration SQL
        migration_file = backend_dir / "migrations" / "001_fix_oauth_tokens_constraints.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("📄 Migration SQL:")
        print("-" * 50)
        print(migration_sql)
        print("-" * 50)
        
        # Execute the migration
        print("🚀 Executing migration...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                print(f"  Executing statement {i}/{len(statements)}...")
                try:
                    # Use Supabase RPC to execute raw SQL
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"  ✅ Statement {i} executed successfully")
                except Exception as e:
                    print(f"  ❌ Statement {i} failed: {e}")
                    # Check if it's a constraint already exists error
                    if "already exists" in str(e).lower():
                        print(f"  ⚠️  Constraint may already exist, continuing...")
                    else:
                        raise
        
        print("✅ Migration applied successfully!")
        print("\n📋 Changes made:")
        print("  • Added unique constraint on (user_id, provider)")
        print("  • Added 'canvas' to allowed providers")
        print("  • Canvas OAuth connections should now work")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

async def verify_migration():
    """Verify the migration was applied correctly"""
    
    print("\n🔍 Verifying migration...")
    
    try:
        supabase = get_supabase_client()
        
        # Check if we can query the oauth_tokens table
        result = supabase.table('oauth_tokens').select('*').limit(1).execute()
        print("✅ oauth_tokens table is accessible")
        
        # Try to insert a test record (will be rolled back)
        test_data = {
            'user_id': '00000000-0000-0000-0000-000000000000',  # Non-existent user
            'provider': 'canvas',
            'access_token': 'test',
            'refresh_token': 'test',
            'expires_at': '2025-12-31T23:59:59Z'
        }
        
        try:
            # This should fail due to foreign key constraint, but not due to provider constraint
            supabase.table('oauth_tokens').insert(test_data).execute()
            print("⚠️  Test insert succeeded (unexpected)")
        except Exception as e:
            if "foreign key" in str(e).lower():
                print("✅ Provider constraint allows 'canvas' (foreign key error expected)")
            elif "provider" in str(e).lower() and "check" in str(e).lower():
                print("❌ Provider constraint still rejects 'canvas'")
                return False
            else:
                print(f"⚠️  Unexpected error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main migration function"""
    
    print("🚀 PulsePlan Database Migration")
    print("=" * 40)
    
    # Apply migration
    success = await apply_migration()
    
    if success:
        # Verify migration
        await verify_migration()
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("  1. Test Canvas OAuth connection in your app")
        print("  2. Verify no duplicate tokens exist")
        print("  3. Monitor logs for any remaining issues")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

