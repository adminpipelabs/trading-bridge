#!/bin/bash
# Run SQL query to check Sharp's connectors via Railway CLI

echo "🔍 Checking Sharp's BitMart connectors via Railway..."

# Get database URL from Railway
DATABASE_URL=$(railway variables get DATABASE_URL --json 2>/dev/null | jq -r '.value' 2>/dev/null)

if [ -z "$DATABASE_URL" ]; then
    echo "❌ Could not get DATABASE_URL from Railway"
    echo "Trying alternative method..."
    
    # Try Railway CLI database command
    railway connect postgres 2>/dev/null || {
        echo "❌ Could not connect to Railway database"
        echo ""
        echo "Please run this SQL query manually in Railway PostgreSQL console:"
        echo ""
        echo "SELECT id, name, memo, api_key IS NOT NULL as has_key, api_secret IS NOT NULL as has_secret"
        echo "FROM connectors"
        echo "WHERE client_id LIKE '%sharp%'"
        echo "   OR account LIKE '%sharp%';"
        exit 1
    }
fi

echo "✅ Connected to database"
echo "Running query..."
echo ""

# Run query using psql if available
if command -v psql &> /dev/null; then
    psql "$DATABASE_URL" -c "
        SELECT 
            id, 
            name, 
            memo, 
            api_key IS NOT NULL as has_key, 
            api_secret IS NOT NULL as has_secret
        FROM connectors 
        WHERE client_id LIKE '%sharp%' 
           OR account LIKE '%sharp%';
    "
else
    echo "psql not found. Please run the query manually in Railway PostgreSQL console."
fi
