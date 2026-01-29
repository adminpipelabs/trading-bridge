#!/usr/bin/env python3
"""
Register admin Solana wallet in database.
Run this to ensure admin wallet is registered.
"""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Client, Wallet
from datetime import datetime
import uuid

ADMIN_WALLET = "BrLyvX5p7HYXsc94AQXXNUfe7zbCYriDfUT1p3DafuCV"

def register_admin_wallet():
    db = SessionLocal()
    try:
        # Check if admin client exists
        admin_client = db.query(Client).filter(Client.account_identifier == "admin").first()
        
        if not admin_client:
            # Create admin client
            admin_client = Client(
                id=str(uuid.uuid4()),
                name="Admin",
                account_identifier="admin",
                role="admin",
                wallet_address=ADMIN_WALLET,
                wallet_type="SOLANA",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin_client)
            print(f"✅ Created admin client")
        else:
            print(f"✅ Admin client already exists: {admin_client.id}")
        
        # Check if wallet exists (try both original case and lowercase)
        wallet = db.query(Wallet).filter(
            (Wallet.address == ADMIN_WALLET) | (Wallet.address == ADMIN_WALLET.lower())
        ).filter(Wallet.chain == 'solana').first()
        
        if not wallet:
            # Create wallet linked to admin client
            wallet = Wallet(
                id=str(uuid.uuid4()),
                client_id=admin_client.id,
                chain="solana",
                address=ADMIN_WALLET,  # Store in original case
                created_at=datetime.utcnow()
            )
            db.add(wallet)
            print(f"✅ Created admin wallet: {ADMIN_WALLET}")
        else:
            # Update to original case if stored in lowercase
            if wallet.address != ADMIN_WALLET:
                wallet.address = ADMIN_WALLET
                print(f"✅ Updated wallet address to original case: {ADMIN_WALLET}")
            else:
                print(f"✅ Admin wallet already exists: {ADMIN_WALLET}")
        
        # Ensure admin client has correct role
        if admin_client.role != "admin":
            admin_client.role = "admin"
            print(f"✅ Updated admin client role to 'admin'")
        
        db.commit()
        print(f"\n✅ Admin wallet registered successfully!")
        print(f"   Wallet: {ADMIN_WALLET}")
        print(f"   Account: {admin_client.account_identifier}")
        print(f"   Role: {admin_client.role}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    register_admin_wallet()
