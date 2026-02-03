"""
Integration: Wire health monitor into your existing FastAPI app.
Add to: trading-bridge/app/main.py (modify your existing startup)
"""

# ──────────────────────────────────────────────────────────────
# Add these imports to your main.py
# ──────────────────────────────────────────────────────────────
from app.bot_health import BotHealthMonitor
from app.health_routes import router as health_router


# ──────────────────────────────────────────────────────────────
# Register the health routes
# ──────────────────────────────────────────────────────────────
# Add alongside your existing router includes:
# app.include_router(auth_router)
# app.include_router(client_router)
# app.include_router(bot_router)
# app.include_router(exchange_router)
app.include_router(health_router)  # ← ADD THIS


# ──────────────────────────────────────────────────────────────
# Modify your startup event
# ──────────────────────────────────────────────────────────────
# You likely have something like this already:
#
# @app.on_event("startup")
# async def startup():
#     app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
#
# Add the health monitor startup:

@app.on_event("startup")
async def startup():
    # Your existing DB pool setup
    app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)

    # Start the health monitor
    app.state.health_monitor = BotHealthMonitor(app.state.db_pool)
    await app.state.health_monitor.start()


@app.on_event("shutdown")
async def shutdown():
    # Stop the health monitor
    if hasattr(app.state, 'health_monitor'):
        await app.state.health_monitor.stop()

    # Your existing cleanup
    if hasattr(app.state, 'db_pool'):
        await app.state.db_pool.close()


# ──────────────────────────────────────────────────────────────
# ALSO: Update your existing bot start/stop endpoints
# to set reported_status
# ──────────────────────────────────────────────────────────────
# In your existing bot_routes.py, when starting a bot:
#
#   @router.post("/{bot_id}/start")
#   async def start_bot(bot_id: int, ...):
#       # ... existing start logic ...
#       # ADD: Set reported_status so health monitor knows intent
#       await conn.execute("""
#           UPDATE bots SET reported_status = 'running',
#                           status_updated_at = NOW()
#           WHERE id = $1
#       """, bot_id)
#
# When stopping a bot:
#
#   @router.post("/{bot_id}/stop")
#   async def stop_bot(bot_id: int, ...):
#       # ... existing stop logic ...
#       # ADD: Clear reported_status
#       await conn.execute("""
#           UPDATE bots SET reported_status = 'stopped',
#                           status = 'stopped',
#                           health_status = 'stopped',
#                           status_updated_at = NOW()
#           WHERE id = $1
#       """, bot_id)
