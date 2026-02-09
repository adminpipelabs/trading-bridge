@router.get("/{bot_id}/balance-debug")
async def debug_bot_balance(bot_id: str, db: Session = Depends(get_db)):
    """
    Diagnostic endpoint to debug balance fetching issues.
    Returns detailed information about connectors, accounts, and balance fetching.
    """
    from app.api.client_data import sync_connectors_to_exchange_manager
    from app.services.exchange import exchange_manager
    
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Get client
    client = db.query(Client).filter(Client.id == bot.client_id).first()
    
    # Get connectors from database
    connectors = db.query(Connector).filter(Connector.client_id == bot.client_id).all()
    
    # Try to sync
    synced = await sync_connectors_to_exchange_manager(bot.account, db)
    account = exchange_manager.get_account(bot.account) if synced else None
    
    return {
        "bot": {
            "id": bot.id,
            "name": bot.name,
            "account": bot.account,
            "connector": bot.connector,
            "bot_type": bot.bot_type,
            "pair": bot.pair,
            "client_id": bot.client_id
        },
        "client": {
            "id": client.id if client else None,
            "name": client.name if client else None,
            "account_identifier": client.account_identifier if client else None
        },
        "connectors_in_db": [
            {
                "id": c.id,
                "name": c.name,
                "has_api_key": bool(c.api_key),
                "has_api_secret": bool(c.api_secret),
                "has_memo": bool(c.memo)
            } for c in connectors
        ],
        "sync_result": synced,
        "account_in_manager": account is not None,
        "connectors_in_manager": list(account.connectors.keys()) if account else [],
        "bot_connector_lower": (bot.connector or '').lower(),
        "connector_match": (bot.connector or '').lower() in (list(account.connectors.keys()) if account else [])
    }
