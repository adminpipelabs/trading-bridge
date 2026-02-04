#!/usr/bin/env python3
"""
Run database migrations using Railway DATABASE_URL or direct connection.
This script executes the complete setup SQL migrations.
"""
import os
import sys
import subprocess
from pathlib import Path

def get_database_url():
    """Get DATABASE_URL from environment or Railway CLI."""
    # Try environment variable first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # Try Railway CLI
    try:
        result = subprocess.run(
            ["railway", "variables"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'DATABASE_URL' in line:
                    # Extract URL (format may vary)
                    parts = line.split()
                    if len(parts) > 1:
                        return parts[-1]
    except Exception as e:
        print(f"⚠️  Could not get DATABASE_URL from Railway CLI: {e}")
    
    return None

def run_migrations_with_psql(db_url, sql_file):
    """Run migrations using psql."""
    # Convert postgresql:// to postgres:// for psql
    psql_url = db_url.replace("postgresql://", "postgres://")
    
    print(f"🔗 Connecting to database...")
    print(f"📋 Running migrations from: {sql_file}")
    
    try:
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Run with psql
        result = subprocess.run(
            ["psql", psql_url],
            input=sql_content,
            text=True,
            capture_output=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            if result.stdout:
                print("\nOutput:")
                print(result.stdout)
            return True
        else:
            print("❌ Migration failed!")
            if result.stderr:
                print("\nErrors:")
                print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ psql not found. Please install PostgreSQL client tools.")
        return False
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def run_migrations_with_python(db_url, sql_file):
    """Run migrations using Python psycopg2."""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], check=True)
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    # Parse DATABASE_URL
    # Format: postgresql://user:password@host:port/database
    import urllib.parse
    parsed = urllib.parse.urlparse(db_url)
    
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],  # Remove leading /
        'user': parsed.username,
        'password': parsed.password,
    }
    
    print(f"🔗 Connecting to database: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
    print(f"📋 Running migrations from: {sql_file}")
    
    try:
        # Read SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Connect and execute
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Split SQL into individual statements
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            try:
                cursor.execute(statement)
                success_count += 1
                print(f"  ✅ Statement {i}/{len(statements)} executed")
            except Exception as e:
                # Many errors are harmless (IF NOT EXISTS, etc.)
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "does not exist" in error_msg.lower():
                    print(f"  ⚠️  Statement {i}/{len(statements)}: {error_msg[:60]}... (harmless)")
                    success_count += 1
                else:
                    print(f"  ❌ Statement {i}/{len(statements)} failed: {error_msg[:100]}")
                    error_count += 1
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Migrations completed!")
        print(f"   Successful: {success_count}")
        if error_count > 0:
            print(f"   Errors: {error_count} (may be harmless)")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main function."""
    print("=" * 50)
    print("Database Migration Script")
    print("=" * 50)
    print()
    
    # Find SQL file
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    sql_file = repo_root / "migrations" / "COMPLETE_SETUP.sql"
    
    if not sql_file.exists():
        print(f"❌ Migration file not found: {sql_file}")
        sys.exit(1)
    
    # Get DATABASE_URL
    db_url = get_database_url()
    
    if not db_url:
        print("❌ DATABASE_URL not found!")
        print()
        print("Please either:")
        print("1. Set DATABASE_URL environment variable:")
        print("   export DATABASE_URL='postgresql://...'")
        print()
        print("2. Or run from Railway project directory:")
        print("   railway run python scripts/run_migrations.py")
        print()
        print("3. Or get DATABASE_URL from Railway Dashboard:")
        print("   Railway → PostgreSQL → Variables → DATABASE_URL")
        sys.exit(1)
    
    print(f"✅ Found DATABASE_URL")
    print()
    
    # Try psql first (faster), then Python
    if run_migrations_with_psql(db_url, sql_file):
        print()
        print("=" * 50)
        print("✅ Migrations completed successfully!")
        print("=" * 50)
        sys.exit(0)
    else:
        print()
        print("⚠️  psql failed, trying Python method...")
        print()
        if run_migrations_with_python(db_url, sql_file):
            print()
            print("=" * 50)
            print("✅ Migrations completed successfully!")
            print("=" * 50)
            sys.exit(0)
        else:
            print()
            print("=" * 50)
            print("❌ Migrations failed!")
            print("=" * 50)
            sys.exit(1)

if __name__ == "__main__":
    main()
