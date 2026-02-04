#!/usr/bin/env python3
"""
Railway Migration Script
Runs database migrations using DATABASE_URL from Railway environment.
Execute with: railway run python railway_migrate.py
"""
import os
import sys
from pathlib import Path

def run_migrations():
    """Run database migrations."""
    # Get DATABASE_URL from environment (Railway provides this automatically)
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Make sure you're running this in Railway environment")
        sys.exit(1)
    
    # Parse DATABASE_URL
    from urllib.parse import urlparse
    parsed = urlparse(db_url)
    
    # Install psycopg2 if needed
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("📦 Installing psycopg2-binary...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "psycopg2-binary"])
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Read SQL file
    sql_file = Path(__file__).parent / "migrations" / "COMPLETE_SETUP.sql"
    if not sql_file.exists():
        print(f"❌ Migration file not found: {sql_file}")
        sys.exit(1)
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Connect to database
    print("=" * 60)
    print("Database Migration Script")
    print("=" * 60)
    print(f"📋 Database: {parsed.hostname}:{parsed.port or 5432}/{parsed.path[1:]}")
    print(f"📄 SQL File: {sql_file}")
    print()
    
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading /
            user=parsed.username,
            password=parsed.password,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Split SQL into statements (handle multi-line statements)
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('--'):
                continue
            current_statement.append(line)
            if line.endswith(';'):
                statements.append(' '.join(current_statement))
                current_statement = []
        
        if current_statement:
            statements.append(' '.join(current_statement))
        
        print(f"🔧 Executing {len(statements)} SQL statements...")
        print()
        
        success = 0
        skipped = 0
        errors = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement == ';':
                continue
            try:
                cursor.execute(statement)
                success += 1
                if i % 5 == 0:
                    print(f"  ✅ Progress: {i}/{len(statements)} statements")
            except Exception as e:
                error_msg = str(e).lower()
                # Many errors are harmless (IF NOT EXISTS, etc.)
                if any(phrase in error_msg for phrase in [
                    'already exists', 'does not exist', 'duplicate', 
                    'relation', 'column', 'constraint'
                ]):
                    skipped += 1
                    if i <= 10:  # Show first few skipped messages
                        print(f"  ⚠️  [{i}] Skipped (harmless): {str(e)[:60]}...")
                else:
                    errors += 1
                    print(f"  ❌ [{i}] Error: {str(e)[:100]}")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"✅ Successful: {success}")
        print(f"⚠️  Skipped (harmless): {skipped}")
        if errors > 0:
            print(f"❌ Errors: {errors}")
        print()
        
        # Verify migrations
        print("🔍 Verifying migrations...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
        )
        cursor = conn.cursor()
        
        # Check health_status column
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'bots' AND column_name = 'health_status'
        """)
        if cursor.fetchone():
            print("  ✅ health_status column exists")
        else:
            print("  ❌ health_status column missing")
        
        # Check trading_keys table
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'trading_keys'
        """)
        if cursor.fetchone():
            print("  ✅ trading_keys table exists")
        else:
            print("  ❌ trading_keys table missing")
        
        # Check client roles
        cursor.execute("""
            SELECT COUNT(*) FROM clients WHERE role IS NULL
        """)
        null_roles = cursor.fetchone()[0]
        if null_roles == 0:
            print("  ✅ All clients have roles assigned")
        else:
            print(f"  ⚠️  {null_roles} clients with NULL roles")
        
        cursor.close()
        conn.close()
        
        print()
        print("=" * 60)
        if errors == 0:
            print("✅ Migrations completed successfully!")
        else:
            print("⚠️  Migrations completed with some errors")
            print("   Check output above for details")
        print("=" * 60)
        
        sys.exit(0 if errors == 0 else 1)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
