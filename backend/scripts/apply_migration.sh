#!/bin/bash
# Simple migration script to fix oauth_tokens constraints
# Run this with your Supabase database connection

set -e

echo "🔧 Applying oauth_tokens constraints migration..."

# Check if SUPABASE_URL and SUPABASE_SERVICE_KEY are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo "❌ Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables"
    echo "   Example:"
    echo "   export SUPABASE_URL='https://your-project.supabase.co'"
    echo "   export SUPABASE_SERVICE_KEY='your-service-key'"
    exit 1
fi

# Create a temporary SQL file
TEMP_SQL=$(mktemp)
cat > "$TEMP_SQL" << 'EOF'
-- Add unique constraint on (user_id, provider) to prevent duplicate tokens
ALTER TABLE public.oauth_tokens 
ADD CONSTRAINT oauth_tokens_user_provider_unique UNIQUE (user_id, provider);

-- Update CHECK constraint to include 'canvas' provider
ALTER TABLE public.oauth_tokens 
DROP CONSTRAINT IF EXISTS oauth_tokens_provider_check;

ALTER TABLE public.oauth_tokens 
ADD CONSTRAINT oauth_tokens_provider_check 
CHECK (provider = ANY (ARRAY['google'::text, 'outlook'::text, 'apple'::text, 'canvas'::text]));
EOF

echo "📄 Executing migration SQL..."

# Execute the migration using psql or curl
if command -v psql >/dev/null 2>&1; then
    echo "Using psql..."
    PGPASSWORD="$SUPABASE_SERVICE_KEY" psql -h "$(echo $SUPABASE_URL | sed 's|https://||' | sed 's|\.supabase\.co||')" \
        -p 5432 \
        -U postgres \
        -d postgres \
        -f "$TEMP_SQL"
elif command -v curl >/dev/null 2>&1; then
    echo "Using curl..."
    curl -X POST \
        "$SUPABASE_URL/rest/v1/rpc/exec_sql" \
        -H "apikey: $SUPABASE_SERVICE_KEY" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"sql\": \"$(cat $TEMP_SQL | tr '\n' ' ' | sed 's/"/\\"/g')\"}"
else
    echo "❌ Neither psql nor curl found. Please install one of them or run the migration manually."
    echo "SQL to execute:"
    cat "$TEMP_SQL"
    exit 1
fi

# Clean up
rm "$TEMP_SQL"

echo "✅ Migration completed!"
echo ""
echo "📋 Changes made:"
echo "  • Added unique constraint on (user_id, provider)"
echo "  • Added 'canvas' to allowed providers"
echo "  • Canvas OAuth connections should now work"
echo ""
echo "Next steps:"
echo "  1. Test Canvas OAuth connection in your app"
echo "  2. Verify no duplicate tokens exist"
echo "  3. Monitor logs for any remaining issues"

