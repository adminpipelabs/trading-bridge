#!/usr/bin/env python3
"""
Railway Deployment Diagnostic Script
Checks bot runner, data feeds, database, and environment configuration
"""
import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_env_vars():
    """Check required environment variables"""
    print("\n" + "="*80)
    print("ENVIRONMENT VARIABLES CHECK")
    print("="*80)
    
    required = {
        "DATABASE_URL": "Database connection",
        "ENCRYPTION_KEY": "Wallet encryption (optional but recommended)",
    }
    
    optional = {
        "SOLANA_RPC_URL": "Solana RPC endpoint",
        "HUMMINGBOT_API_URL": "Hummingbot API (for legacy bots)",
        "HUMMINGBOT_API_USERNAME": "Hummingbot auth",
        "HUMMINGBOT_API_PASSWORD": "Hummingbot auth",
    }
    
    all_good = True
    
    for var, desc in required.items():
        value = os.getenv(var, "")
        if value:
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"✅ {var}: {masked} ({desc})")
        else:
            print(f"❌ {var}: NOT SET ({desc})")
            if var == "DATABASE_URL":
                all_good = False
    
    for var, desc in optional.items():
        value = os.getenv(var, "")
        if value:
            masked = value[:20] + "..." if len(value) > 20 else value
            print(f"⚠️  {var}: {masked} ({desc})")
        else:
            print(f"⚪ {var}: NOT SET ({desc} - optional)")
    
    return all_good


def check_database():
    """Check database connectivity"""
    print("\n" + "="*80)
    print("DATABASE CONNECTIVITY CHECK")
    print("="*80)
    
    try:
        from app.database import engine, SessionLocal, Bot, Client, Connector
        
        if not engine:
            print("❌ Database engine not initialized")
            return False
        
        if not SessionLocal:
            print("❌ Database session factory not initialized")
            return False
        
        # Test connection
        db = SessionLocal()
        try:
            # Simple query
            bot_count = db.query(Bot).count()
            client_count = db.query(Client).count()
            connector_count = db.query(Connector).count()
            
            print(f"✅ Database connection successful")
            print(f"   - Bots in database: {bot_count}")
            print(f"   - Clients in database: {client_count}")
            print(f"   - Connectors in database: {connector_count}")
            
            # Check for running bots
            running_bots = db.query(Bot).filter(Bot.status == "running").all()
            print(f"   - Running bots: {len(running_bots)}")
            for bot in running_bots:
                print(f"     • Bot {bot.id}: {bot.name} ({bot.bot_type})")
            
            return True
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_bot_runner():
    """Check bot runner status"""
    print("\n" + "="*80)
    print("BOT RUNNER STATUS CHECK")
    print("="*80)
    
    try:
        from app.bot_runner import bot_runner
        
        if not bot_runner:
            print("❌ Bot runner not initialized")
            return False
        
        print(f"✅ Bot runner initialized")
        print(f"   - Running bots: {len(bot_runner.running_bots)}")
        
        if bot_runner.running_bots:
            for bot_id, task in bot_runner.running_bots.items():
                status = "running" if not task.done() else "completed"
                print(f"     • Bot {bot_id}: {status}")
        else:
            print("   ⚠️  No bots currently running")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import bot_runner: {e}")
        return False
    except Exception as e:
        print(f"❌ Bot runner check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_exchange_manager():
    """Check exchange manager (data feeds)"""
    print("\n" + "="*80)
    print("EXCHANGE MANAGER (DATA FEEDS) CHECK")
    print("="*80)
    
    try:
        from app.services.exchange import exchange_manager
        
        if not exchange_manager:
            print("❌ Exchange manager not initialized")
            return False
        
        print(f"✅ Exchange manager initialized")
        print(f"   - Accounts loaded: {len(exchange_manager.accounts)}")
        
        if exchange_manager.accounts:
            for account_name, account in exchange_manager.accounts.items():
                connector_count = len(account.connectors)
                print(f"     • Account '{account_name}': {connector_count} connector(s)")
                for conn_name in account.connectors.keys():
                    print(f"       - {conn_name}")
        else:
            print("   ⚠️  No accounts loaded (connectors will be synced on-demand)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import exchange_manager: {e}")
        return False
    except Exception as e:
        print(f"❌ Exchange manager check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_api_endpoints():
    """Check if API endpoints are accessible"""
    print("\n" + "="*80)
    print("API ENDPOINTS CHECK")
    print("="*80)
    
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            print(f"✅ Root endpoint: {response.json()}")
        else:
            print(f"❌ Root endpoint: Status {response.status_code}")
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health endpoint: {health.get('status')}")
            print(f"   - Database: {health.get('database')}")
            bot_runner_status = health.get('bot_runner', {})
            print(f"   - Bot runner: {bot_runner_status.get('status')} ({bot_runner_status.get('active_bots', 0)} bots)")
        else:
            print(f"❌ Health endpoint: Status {response.status_code}")
        
        # Test bots endpoint
        response = client.get("/bots")
        if response.status_code == 200:
            bots = response.json()
            print(f"✅ Bots endpoint: {len(bots)} bot(s)")
        elif response.status_code == 500:
            print(f"❌ Bots endpoint: 500 Internal Server Error")
            print(f"   Check Railway logs for details")
        else:
            print(f"⚠️  Bots endpoint: Status {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoints check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all diagnostic checks"""
    print("\n" + "="*80)
    print("RAILWAY DEPLOYMENT DIAGNOSTIC")
    print(f"Timestamp: {datetime.utcnow().isoformat()}")
    print("="*80)
    
    results = {
        "Environment Variables": check_env_vars(),
        "Database": check_database(),
        "Bot Runner": check_bot_runner(),
        "Exchange Manager": check_exchange_manager(),
        "API Endpoints": check_api_endpoints(),
    }
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    all_passed = True
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")
        if not passed:
            all_passed = False
    
    print("="*80)
    
    if all_passed:
        print("\n✅ All checks passed! System appears to be working correctly.")
        return 0
    else:
        print("\n❌ Some checks failed. Review the output above for details.")
        print("\nNext steps:")
        print("1. Check Railway logs for detailed error messages")
        print("2. Verify environment variables are set correctly")
        print("3. Ensure database migrations have been run")
        print("4. Check that bots have proper configuration")
        return 1


if __name__ == "__main__":
    sys.exit(main())
