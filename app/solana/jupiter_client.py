"""
Jupiter API Client for Solana DEX trading
Supports swaps (volume generation) and limit orders (market making)
"""

import httpx
import base64
import base58
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class OrderStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Quote:
    input_mint: str
    output_mint: str
    in_amount: int
    out_amount: int
    price_impact_pct: float
    route_plan: List[Dict]
    raw_response: Dict


@dataclass
class SwapTransaction:
    transaction: str  # Base64 encoded
    last_valid_block_height: int


@dataclass
class LimitOrder:
    order_pubkey: str
    input_mint: str
    output_mint: str
    making_amount: int
    taking_amount: int
    status: OrderStatus
    created_at: Optional[str] = None
    filled_amount: Optional[int] = None


class JupiterClient:
    """Client for Jupiter DEX Aggregator API"""
    
    # API endpoints
    QUOTE_API = "https://quote-api.jup.ag/v6"
    SWAP_API = "https://quote-api.jup.ag/v6"
    LIMIT_ORDER_API = "https://api.jup.ag/limit/v2"
    PRICE_API = "https://api.jup.ag/price/v2"
    
    # Common token mints
    SOL_MINT = "So11111111111111111111111111111111111111112"
    USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    # ============ PRICE FEEDS ============
    
    async def get_price(self, token_mint: str, vs_token: str = None) -> Dict[str, Any]:
        """
        Get token price from Jupiter Price API
        
        Args:
            token_mint: Token mint address
            vs_token: Quote token (default: USDC)
        
        Returns:
            Price data including price, confidence, etc.
        """
        vs = vs_token or self.USDC_MINT
        
        response = await self.client.get(
            f"{self.PRICE_API}",
            params={
                "ids": token_mint,
                "vsToken": vs
            }
        )
        response.raise_for_status()
        data = response.json()
        
        if token_mint in data.get("data", {}):
            token_data = data["data"][token_mint]
            return {
                "mint": token_mint,
                "price": float(token_data.get("price", 0)),
                "vs_token": vs,
                "confidence": token_data.get("confidence"),
                "timestamp": data.get("timeTaken")
            }
        
        raise ValueError(f"Price not found for {token_mint}")
    
    async def get_prices_batch(self, token_mints: List[str]) -> Dict[str, float]:
        """Get prices for multiple tokens"""
        response = await self.client.get(
            f"{self.PRICE_API}",
            params={"ids": ",".join(token_mints)}
        )
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        for mint in token_mints:
            if mint in data.get("data", {}):
                prices[mint] = float(data["data"][mint].get("price", 0))
        
        return prices
    
    # ============ SWAPS (Volume Generation) ============
    
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,  # 0.5% default
        swap_mode: str = "ExactIn"
    ) -> Quote:
        """
        Get a swap quote from Jupiter
        
        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address  
            amount: Amount in smallest unit (lamports/token decimals)
            slippage_bps: Slippage tolerance in basis points
            swap_mode: "ExactIn" or "ExactOut"
        
        Returns:
            Quote object with route and amounts
        """
        response = await self.client.get(
            f"{self.QUOTE_API}/quote",
            params={
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "swapMode": swap_mode
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return Quote(
            input_mint=data["inputMint"],
            output_mint=data["outputMint"],
            in_amount=int(data["inAmount"]),
            out_amount=int(data["outAmount"]),
            price_impact_pct=float(data.get("priceImpactPct", 0)),
            route_plan=data.get("routePlan", []),
            raw_response=data
        )
    
    async def get_swap_transaction(
        self,
        quote: Quote,
        user_public_key: str,
        wrap_unwrap_sol: bool = True,
        fee_account: Optional[str] = None,
        compute_unit_price_micro_lamports: Optional[int] = None
    ) -> SwapTransaction:
        """
        Get a swap transaction to sign
        
        Args:
            quote: Quote from get_quote()
            user_public_key: Wallet public key that will sign
            wrap_unwrap_sol: Auto wrap/unwrap SOL
            fee_account: Optional fee account for referral
            compute_unit_price_micro_lamports: Priority fee
        
        Returns:
            SwapTransaction with base64 encoded transaction
        """
        payload = {
            "quoteResponse": quote.raw_response,
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": wrap_unwrap_sol,
            "dynamicComputeUnitLimit": True
        }
        
        if fee_account:
            payload["feeAccount"] = fee_account
        
        if compute_unit_price_micro_lamports:
            payload["computeUnitPriceMicroLamports"] = compute_unit_price_micro_lamports
        
        response = await self.client.post(
            f"{self.SWAP_API}/swap",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        return SwapTransaction(
            transaction=data["swapTransaction"],
            last_valid_block_height=data.get("lastValidBlockHeight", 0)
        )
    
    # ============ LIMIT ORDERS (Market Making) ============
    
    async def create_limit_order(
        self,
        maker: str,
        input_mint: str,
        output_mint: str,
        making_amount: int,
        taking_amount: int,
        expired_at: Optional[int] = None,  # Unix timestamp
    ) -> Dict[str, Any]:
        """
        Create a limit order transaction
        
        Args:
            maker: Wallet public key that will sign
            input_mint: Token to sell
            output_mint: Token to buy
            making_amount: Amount to sell (in smallest units)
            taking_amount: Amount to receive (in smallest units)
            expired_at: Optional expiry timestamp
        
        Returns:
            Transaction data to sign
        """
        payload = {
            "maker": maker,
            "payer": maker,
            "inputMint": input_mint,
            "outputMint": output_mint,
            "params": {
                "makingAmount": str(making_amount),
                "takingAmount": str(taking_amount)
            }
        }
        
        if expired_at:
            payload["params"]["expiredAt"] = str(expired_at)
        
        response = await self.client.post(
            f"{self.LIMIT_ORDER_API}/createOrder",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_open_orders(
        self,
        wallet: str,
        input_mint: Optional[str] = None,
        output_mint: Optional[str] = None
    ) -> List[LimitOrder]:
        """
        Get open limit orders for a wallet
        
        Args:
            wallet: Wallet public key
            input_mint: Filter by input token
            output_mint: Filter by output token
        
        Returns:
            List of open limit orders
        """
        params = {"wallet": wallet}
        if input_mint:
            params["inputMint"] = input_mint
        if output_mint:
            params["outputMint"] = output_mint
        
        response = await self.client.get(
            f"{self.LIMIT_ORDER_API}/openOrders",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        orders = []
        for order_data in data.get("orders", []):
            account = order_data.get("account", {})
            orders.append(LimitOrder(
                order_pubkey=order_data.get("publicKey", ""),
                input_mint=account.get("inputMint", ""),
                output_mint=account.get("outputMint", ""),
                making_amount=int(account.get("makingAmount", 0)),
                taking_amount=int(account.get("takingAmount", 0)),
                status=OrderStatus.OPEN,
                filled_amount=int(account.get("filledMakingAmount", 0))
            ))
        
        return orders
    
    async def cancel_order(
        self,
        maker: str,
        order_pubkey: str
    ) -> Dict[str, Any]:
        """
        Cancel a limit order
        
        Args:
            maker: Wallet public key
            order_pubkey: Order public key to cancel
        
        Returns:
            Transaction data to sign
        """
        response = await self.client.post(
            f"{self.LIMIT_ORDER_API}/cancelOrders",
            json={
                "maker": maker,
                "orders": [order_pubkey]
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def cancel_all_orders(
        self,
        maker: str,
        input_mint: Optional[str] = None,
        output_mint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel all open orders, optionally filtered by token pair
        """
        # First get all open orders
        orders = await self.get_open_orders(maker, input_mint, output_mint)
        
        if not orders:
            return {"cancelled": 0, "orders": []}
        
        order_pubkeys = [o.order_pubkey for o in orders]
        
        response = await self.client.post(
            f"{self.LIMIT_ORDER_API}/cancelOrders",
            json={
                "maker": maker,
                "orders": order_pubkeys
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def get_order_history(
        self,
        wallet: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get order history for a wallet"""
        response = await self.client.get(
            f"{self.LIMIT_ORDER_API}/orderHistory",
            params={
                "wallet": wallet,
                "page": page,
                "pageSize": page_size
            }
        )
        response.raise_for_status()
        return response.json()
    
    # ============ MARKET MAKING HELPERS ============
    
    async def create_spread_orders(
        self,
        maker: str,
        base_mint: str,
        quote_mint: str,
        base_amount: int,
        spread_bps: int = 50,  # 0.5% spread
        expired_at: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create buy and sell limit orders at spread from current price
        
        Args:
            maker: Wallet public key
            base_mint: Base token (e.g., the client's token)
            quote_mint: Quote token (e.g., SOL)
            base_amount: Amount of base token for each side
            spread_bps: Spread in basis points (50 = 0.5%)
            expired_at: Order expiry timestamp
        
        Returns:
            Dict with buy and sell order transactions
        """
        # Get current price
        price_data = await self.get_price(base_mint, quote_mint)
        current_price = price_data["price"]
        
        # Calculate spread prices
        spread_multiplier = spread_bps / 10000
        buy_price = current_price * (1 - spread_multiplier)
        sell_price = current_price * (1 + spread_multiplier)
        
        # Calculate quote amounts based on prices
        # For buy: we're spending quote to get base
        buy_quote_amount = int(base_amount * buy_price)
        # For sell: we're selling base to get quote  
        sell_quote_amount = int(base_amount * sell_price)
        
        # Create buy order (buy base with quote)
        buy_order = await self.create_limit_order(
            maker=maker,
            input_mint=quote_mint,  # Spending quote (SOL)
            output_mint=base_mint,  # Getting base (TOKEN)
            making_amount=buy_quote_amount,
            taking_amount=base_amount,
            expired_at=expired_at
        )
        
        # Create sell order (sell base for quote)
        sell_order = await self.create_limit_order(
            maker=maker,
            input_mint=base_mint,  # Spending base (TOKEN)
            output_mint=quote_mint,  # Getting quote (SOL)
            making_amount=base_amount,
            taking_amount=sell_quote_amount,
            expired_at=expired_at
        )
        
        return {
            "current_price": current_price,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "spread_bps": spread_bps,
            "buy_order": buy_order,
            "sell_order": sell_order
        }
