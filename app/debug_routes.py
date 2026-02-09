"""
Debug routes for checking database configuration.
Only enable in development/staging environments.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
import os

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/connectors/sharp")
async def check_sharp_connectors(db: Session = Depends(get_db)):
    """
    Check Sharp's BitMart connector configuration.
    Returns connector name, memo, and whether API keys are present.
    """
    # Only allow in non-production environments
    env = os.getenv("ENVIRONMENT", "production")
    if env == "production":
        raise HTTPException(status_code=403, detail="Debug endpoints disabled in production")
    
    try:
        query = text("""
            SELECT 
                c.id,
                c.name as connector_name,
                c.memo,
                c.api_key IS NOT NULL as has_api_key,
                c.api_secret IS NOT NULL as has_api_secret,
                cl.account_identifier,
                cl.name as client_name
            FROM connectors c
            LEFT JOIN clients cl ON cl.id = c.client_id
            WHERE cl.account_identifier LIKE '%sharp%'
               OR cl.account_identifier LIKE '%Sharp%'
               OR c.name ILIKE '%bitmart%'
            ORDER BY c.created_at DESC
        """)
        
        results = db.execute(query).fetchall()
        
        connectors = []
        for row in results:
            connectors.append({
                "id": row.id,
                "connector_name": row.connector_name,
                "memo": row.memo,
                "has_api_key": row.has_api_key,
                "has_api_secret": row.has_api_secret,
                "client_account": row.account_identifier,
                "client_name": row.client_name,
                "name_is_correct": row.connector_name and row.connector_name.lower().strip() == "bitmart",
                "memo_is_present": bool(row.memo and row.memo.strip()),
            })
        
        return {
            "count": len(connectors),
            "connectors": connectors,
            "summary": {
                "correct_name": any(c["name_is_correct"] for c in connectors),
                "has_memo": any(c["memo_is_present"] for c in connectors),
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying database: {str(e)}")
