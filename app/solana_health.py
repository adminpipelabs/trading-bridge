"""
Solana Bot Health Checker
Extends BotHealthMonitor with on-chain health checks for Jupiter/Solana bots.

Add to: trading-bridge/app/solana_health.py

Uses Solana RPC to:
1. Check SOL balance (needed for gas + quote currency)
2. Check SPL token balance (base currency like LYNK)
3. Check recent transactions on the wallet
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import httpx

logger = logging.getLogger("solana_health")

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

# Public RPC endpoints (use your own for production reliability)
SOLANA_RPC_URLS = [
    "https://api.mainnet-beta.solana.com",
    "https://solana-mainnet.g.alchemy.com/v2/demo",  # Replace with your key
]

SOL_DECIMALS = 9
SOL_MIN_FOR_GAS = 0.005          # ~$1 at current prices, enough for several txs
SOL_LOW_BALANCE = 0.05           # Warn when SOL drops below this

# Lamports per SOL
LAMPORTS_PER_SOL = 1_000_000_000


class SolanaHealthChecker:
    """
    Checks health of Solana-based bots by querying on-chain data.
    """

    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or SOLANA_RPC_URLS[0]
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ──────────────────────────────────────────────────────────
    # RPC helpers
    # ──────────────────────────────────────────────────────────

    async def _rpc_call(self, method: str, params: list) -> dict:
        """Make a Solana JSON-RPC call."""
        client = await self._get_client()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        # Try primary, fallback to secondary
        for url in [self.rpc_url] + SOLANA_RPC_URLS[1:]:
            try:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if "error" in data:
                    logger.warning(f"RPC error from {url}: {data['error']}")
                    continue
                return data.get("result")
            except Exception as e:
                logger.warning(f"RPC call to {url} failed: {e}")
                continue

        raise Exception(f"All RPC endpoints failed for {method}")

    # ──────────────────────────────────────────────────────────
    # Balance checks
    # ──────────────────────────────────────────────────────────

    async def get_sol_balance(self, wallet_address: str) -> dict:
        """
        Get SOL balance for a wallet.
        Returns: {balance_sol, balance_lamports, has_gas, low_balance}
        """
        result = await self._rpc_call("getBalance", [wallet_address])

        if result is None:
            return {"error": "Could not fetch SOL balance"}

        lamports = result.get("value", 0)
        sol = lamports / LAMPORTS_PER_SOL

        return {
            "balance_sol": sol,
            "balance_lamports": lamports,
            "has_gas": sol >= SOL_MIN_FOR_GAS,
            "low_balance": sol < SOL_LOW_BALANCE,
        }

    async def get_token_balance(
        self, wallet_address: str, token_mint: str
    ) -> dict:
        """
        Get SPL token balance for a specific mint.
        Returns: {balance, decimals, ui_amount, has_tokens}
        """
        # Get all token accounts for this wallet filtered by mint
        result = await self._rpc_call(
            "getTokenAccountsByOwner",
            [
                wallet_address,
                {"mint": token_mint},
                {"encoding": "jsonParsed"},
            ],
        )

        if not result or not result.get("value"):
            return {
                "balance": 0,
                "decimals": 0,
                "ui_amount": 0.0,
                "has_tokens": False,
                "token_account": None,
            }

        # Sum up all token accounts for this mint (usually just one)
        total_amount = 0
        decimals = 0
        ui_total = 0.0
        token_account = None

        for account in result["value"]:
            parsed = account["account"]["data"]["parsed"]["info"]
            token_amount = parsed["tokenAmount"]
            total_amount += int(token_amount["amount"])
            decimals = token_amount["decimals"]
            ui_total += float(token_amount.get("uiAmount", 0) or 0)
            if not token_account:
                token_account = account["pubkey"]

        return {
            "balance": total_amount,
            "decimals": decimals,
            "ui_amount": ui_total,
            "has_tokens": total_amount > 0,
            "token_account": token_account,
        }

    async def get_full_balance(
        self, wallet_address: str, base_mint: str, quote_mint: str = None
    ) -> dict:
        """
        Get complete balance picture for a trading bot.
        
        For LYNK/SOL:
          - base_mint = LYNK token mint
          - quote_mint = None (SOL is native, not SPL)
        """
        sol_balance = await self.get_sol_balance(wallet_address)
        base_balance = await self.get_token_balance(wallet_address, base_mint)

        # If quote is an SPL token (e.g. USDC), check that too
        quote_balance = None
        if quote_mint and quote_mint != "So11111111111111111111111111111111111111112":
            quote_balance = await self.get_token_balance(wallet_address, quote_mint)

        # Determine if bot can trade
        # For LYNK/SOL: needs SOL for both gas AND as quote currency
        has_quote = sol_balance["balance_sol"] > SOL_MIN_FOR_GAS
        if quote_balance:
            has_quote = quote_balance["has_tokens"]

        has_base = base_balance["has_tokens"]
        can_trade = has_quote and sol_balance["has_gas"]
        no_funds = not has_quote and not has_base

        # Build summary
        parts = [f"SOL: {sol_balance['balance_sol']:.4f}"]
        parts.append(f"Base token: {base_balance['ui_amount']:.4f}")
        if quote_balance:
            parts.append(f"Quote token: {quote_balance['ui_amount']:.4f}")
        summary = ", ".join(parts)

        return {
            "sol": sol_balance,
            "base": base_balance,
            "quote": quote_balance,
            "can_trade": can_trade,
            "no_funds": no_funds,
            "low_balance": sol_balance["low_balance"],
            "has_gas": sol_balance["has_gas"],
            "summary": summary,
        }

    # ──────────────────────────────────────────────────────────
    # Transaction / activity checks
    # ──────────────────────────────────────────────────────────

    async def get_recent_transactions(
        self, wallet_address: str, limit: int = 20
    ) -> dict:
        """
        Get recent transaction signatures for a wallet.
        Used to determine if the bot has been active.
        """
        result = await self._rpc_call(
            "getSignaturesForAddress",
            [wallet_address, {"limit": limit}],
        )

        if not result:
            return {
                "transactions": [],
                "count": 0,
                "last_tx_time": None,
                "has_recent_activity": False,
            }

        txs = []
        for sig_info in result:
            tx_time = None
            if sig_info.get("blockTime"):
                tx_time = datetime.fromtimestamp(
                    sig_info["blockTime"], tz=timezone.utc
                )
            txs.append({
                "signature": sig_info["signature"],
                "time": tx_time,
                "err": sig_info.get("err"),
                "memo": sig_info.get("memo"),
            })

        last_tx_time = txs[0]["time"] if txs and txs[0]["time"] else None
        now = datetime.now(timezone.utc)

        # Consider "recent" if last tx was within 2 hours
        has_recent = False
        if last_tx_time:
            has_recent = (now - last_tx_time) < timedelta(hours=2)

        return {
            "transactions": txs,
            "count": len(txs),
            "last_tx_time": last_tx_time,
            "has_recent_activity": has_recent,
        }

    # ──────────────────────────────────────────────────────────
    # Full health check (called by BotHealthMonitor)
    # ──────────────────────────────────────────────────────────

    async def check_health(
        self,
        wallet_address: str,
        base_mint: str,
        quote_mint: str = None,
        stale_minutes: int = 30,
        stopped_minutes: int = 120,
    ) -> dict:
        """
        Complete health check for a Solana bot.
        Returns health_status, reason, balance info, and tx activity.
        """
        now = datetime.now(timezone.utc)

        # Get balance and tx info in parallel
        balance = await self.get_full_balance(wallet_address, base_mint, quote_mint)
        tx_info = await self.get_recent_transactions(wallet_address, limit=20)

        # ── Determine health status ──
        health_status = "unknown"
        reason = ""

        last_tx = tx_info["last_tx_time"]

        if balance["no_funds"]:
            # No funds at all
            health_status = "stopped"
            reason = f"NO FUNDS — {balance['summary']}. Bot cannot trade."

        elif not balance["has_gas"]:
            # Has tokens but no SOL for gas
            health_status = "stopped"
            reason = f"NO GAS — SOL balance too low for transactions. {balance['summary']}"

        elif not balance["can_trade"]:
            # Can't trade for some other reason
            health_status = "stopped"
            reason = f"INSUFFICIENT BALANCE — {balance['summary']}"

        elif last_tx:
            time_since = now - last_tx
            if time_since < timedelta(minutes=stale_minutes):
                health_status = "healthy"
                reason = (
                    f"{tx_info['count']} recent txs, "
                    f"latest {int(time_since.total_seconds() // 60)}m ago. "
                    f"Balance: {balance['summary']}"
                )
            elif time_since < timedelta(minutes=stopped_minutes):
                health_status = "stale"
                reason = (
                    f"No activity in {int(time_since.total_seconds() // 60)}m. "
                    f"Balance OK: {balance['summary']}"
                )
                if balance["low_balance"]:
                    reason += " ⚠️ SOL balance getting low"
            else:
                health_status = "stopped"
                hours = time_since.total_seconds() / 3600
                reason = (
                    f"No activity in {hours:.1f}h despite having funds. "
                    f"Balance: {balance['summary']}"
                )
        else:
            # No transactions found at all
            if balance["can_trade"]:
                health_status = "stale"
                reason = f"No transactions found but wallet has funds. {balance['summary']}"
            else:
                health_status = "stopped"
                reason = f"No transactions and no funds. {balance['summary']}"

        return {
            "health_status": health_status,
            "reason": reason,
            "balance": balance,
            "transactions": tx_info,
            "checked_at": now.isoformat(),
            "wallet_address": wallet_address,
        }
