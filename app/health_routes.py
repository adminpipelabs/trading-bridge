"""
Bot Health API Routes
Add to: trading-bridge/app/health_routes.py

Then register in your main app:
    from app.health_routes import router as health_router
    app.include_router(health_router)
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

router = APIRouter(prefix="/bots", tags=["bot-health"])


# ──────────────────────────────────────────────────────────────
# Request/Response models
# ──────────────────────────────────────────────────────────────

class HeartbeatRequest(BaseModel):
    bot_id: str
    status: Optional[str] = "running"
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    bot_id: str
    name: str
    status: str
    health_status: str
    health_message: Optional[str]
    last_trade_time: Optional[str]
    last_heartbeat: Optional[str]
    status_updated_at: Optional[str]


class HealthSummaryResponse(BaseModel):
    total_bots: int
    healthy: int
    stale: int
    stopped: int
    error: int
    unknown: int
    bots: list[HealthResponse]


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@router.get("/{bot_id}/health", response_model=HealthResponse)
async def get_bot_health(bot_id: str, request: Request):
    """Get health status for a specific bot."""
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        bot = await conn.fetchrow("""
            SELECT id, name, status, health_status, health_message,
                   last_trade_time, last_heartbeat, status_updated_at
            FROM bots WHERE id = $1
        """, bot_id)

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    return HealthResponse(
        bot_id=bot['id'],
        name=bot['name'],
        status=bot['status'],
        health_status=bot['health_status'] or 'unknown',
        health_message=bot['health_message'],
        last_trade_time=bot['last_trade_time'].isoformat() if bot['last_trade_time'] else None,
        last_heartbeat=bot['last_heartbeat'].isoformat() if bot['last_heartbeat'] else None,
        status_updated_at=bot['status_updated_at'].isoformat() if bot['status_updated_at'] else None,
    )


@router.post("/{bot_id}/health/check")
async def check_bot_health_now(bot_id: str, request: Request):
    """
    Trigger an immediate health check for a specific bot.
    Returns health status including balance info.
    """
    monitor = request.app.state.health_monitor
    result = await monitor.check_bot_now(bot_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return {
        "success": True,
        "bot_id": bot_id,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        **result
    }


@router.get("/{bot_id}/balance")
async def get_bot_balance(bot_id: str, request: Request):
    """
    Check wallet balance for a specific bot's trading pair.
    Shows exactly why a bot might not be trading.
    """
    pool = request.app.state.db_pool
    monitor = request.app.state.health_monitor

    async with pool.acquire() as conn:
        bot = await conn.fetchrow("""
            SELECT b.id, b.account, b.name, b.pair, b.connector, b.status,
                   b.health_status, b.last_trade_time, b.last_heartbeat,
                   c.api_key, c.api_secret, c.memo
            FROM bots b
            LEFT JOIN connectors c ON c.client_id = (
                SELECT cl.id FROM clients cl 
                WHERE cl.account_identifier = b.account
            )
            WHERE b.id = $1
        """, bot_id)

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    exchange = await monitor._get_exchange(bot)
    if not exchange:
        raise HTTPException(status_code=400, detail="No exchange credentials")

    balance_info = await monitor._check_balance(exchange, bot['pair'])
    if not balance_info:
        raise HTTPException(status_code=500, detail="Could not fetch balance")

    return {
        "bot_id": bot_id,
        "bot_name": bot['name'],
        "pair": bot['pair'],
        "exchange": bot['connector'],
        "base_currency": balance_info['base'],
        "quote_currency": balance_info['quote'],
        "base_free": balance_info['base_free'],
        "base_total": balance_info['base_total'],
        "quote_free": balance_info['quote_free'],
        "quote_total": balance_info['quote_total'],
        "can_trade": not balance_info['no_funds'],
        "low_balance_warning": balance_info['low_balance'],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/summary", response_model=HealthSummaryResponse)
async def get_health_summary(
    request: Request,
    account: Optional[str] = None
):
    """
    Get health summary for all bots or filtered by account.
    Dashboard overview endpoint.
    """
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        if account:
            bots = await conn.fetch("""
                SELECT id, name, status, health_status, health_message,
                       last_trade_time, last_heartbeat, status_updated_at
                FROM bots WHERE account = $1
                ORDER BY id
            """, account)
        else:
            bots = await conn.fetch("""
                SELECT id, name, status, health_status, health_message,
                       last_trade_time, last_heartbeat, status_updated_at
                FROM bots ORDER BY id
            """)

    bot_list = []
    counts = {'healthy': 0, 'stale': 0, 'stopped': 0, 'error': 0, 'unknown': 0}

    for bot in bots:
        hs = bot['health_status'] or 'unknown'
        counts[hs] = counts.get(hs, 0) + 1
        bot_list.append(HealthResponse(
            bot_id=bot['id'],
            name=bot['name'],
            status=bot['status'],
            health_status=hs,
            health_message=bot['health_message'],
            last_trade_time=bot['last_trade_time'].isoformat() if bot['last_trade_time'] else None,
            last_heartbeat=bot['last_heartbeat'].isoformat() if bot['last_heartbeat'] else None,
            status_updated_at=bot['status_updated_at'].isoformat() if bot['status_updated_at'] else None,
        ))

    return HealthSummaryResponse(
        total_bots=len(bots),
        healthy=counts['healthy'],
        stale=counts['stale'],
        stopped=counts['stopped'],
        error=counts['error'],
        unknown=counts['unknown'],
        bots=bot_list,
    )


@router.post("/heartbeat")
async def receive_heartbeat(payload: HeartbeatRequest, request: Request):
    """
    Webhook endpoint for bots to send heartbeats.
    
    Call from Hummingbot or a sidecar process:
        POST /bots/heartbeat
        {"bot_id": 1, "status": "running", "metadata": {"uptime": 3600}}
    """
    monitor = request.app.state.health_monitor
    await monitor.receive_heartbeat(payload.bot_id, payload.metadata)

    return {
        "success": True,
        "bot_id": payload.bot_id,
        "received_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{bot_id}/health/history")
async def get_health_history(
    bot_id: str,
    request: Request,
    limit: int = 50
):
    """
    Get health check history for a bot.
    Useful for debugging why a bot was marked as stopped.
    """
    pool = request.app.state.db_pool

    async with pool.acquire() as conn:
        logs = await conn.fetch("""
            SELECT checked_at, previous_status, new_status, health_status,
                   reason, trade_count_since_last, last_trade_found
            FROM bot_health_logs
            WHERE bot_id = $1
            ORDER BY checked_at DESC
            LIMIT $2
        """, bot_id, limit)

    return {
        "bot_id": bot_id,
        "history": [
            {
                "checked_at": log['checked_at'].isoformat(),
                "previous_status": log['previous_status'],
                "new_status": log['new_status'],
                "health_status": log['health_status'],
                "reason": log['reason'],
                "trade_count": log['trade_count_since_last'],
                "last_trade": log['last_trade_found'].isoformat() if log['last_trade_found'] else None,
            }
            for log in logs
        ]
    }


@router.get("/{bot_id}/balance/solana")
async def get_solana_bot_balance(bot_id: str, request: Request):
    """
    Get on-chain Solana balance for a Jupiter bot.
    Shows SOL (gas + quote), base token balance, and whether the bot can trade.
    """
    pool = request.app.state.db_pool
    monitor = request.app.state.health_monitor

    async with pool.acquire() as conn:
        bot = await conn.fetchrow("""
            SELECT b.id, b.name, b.config, b.chain, b.connector,
                   w.address as wallet_address
            FROM bots b
            LEFT JOIN clients cl ON cl.account_identifier = b.account
            LEFT JOIN wallets w ON w.client_id = cl.id
            WHERE b.id = $1
        """, bot_id)

    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    wallet = bot.get('wallet_address')
    if not wallet:
        raise HTTPException(status_code=400, detail="No wallet address for this bot")

    config = bot.get('config') or {}
    base_mint = config.get('base_mint')
    quote_mint = config.get('quote_mint')

    if not base_mint:
        raise HTTPException(status_code=400, detail="No base_mint in bot config")

    balance = await monitor.solana_checker.get_full_balance(
        wallet_address=wallet,
        base_mint=base_mint,
        quote_mint=quote_mint,
    )

    return {
        "bot_id": bot_id,
        "bot_name": bot['name'],
        "wallet_address": wallet,
        "sol_balance": balance['sol']['balance_sol'],
        "sol_has_gas": balance['sol']['has_gas'],
        "base_token_balance": balance['base']['ui_amount'],
        "base_has_tokens": balance['base']['has_tokens'],
        "quote_balance": balance['quote']['ui_amount'] if balance['quote'] else None,
        "can_trade": balance['can_trade'],
        "no_funds": balance['no_funds'],
        "low_balance_warning": balance['low_balance'],
        "summary": balance['summary'],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
