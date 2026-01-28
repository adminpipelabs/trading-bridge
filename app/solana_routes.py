"""
Solana Trading Routes
API endpoints for Jupiter swaps, limit orders, and market making on Solana
"""

import os
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .solana import JupiterClient, SolanaTransactionSigner, TransactionResult


router = APIRouter(prefix="/solana", tags=["Solana"])

# Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Common token mints
SOL_MINT = "So11111111111111111111111111111111111111112"
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


# ============ REQUEST/RESPONSE MODELS ============

class PriceRequest(BaseModel):
    token_mint: str
    vs_token: Optional[str] = SOL_MINT


class PriceResponse(BaseModel):
    mint: str
    price: float
    vs_token: str


class BalanceRequest(BaseModel):
    wallet_address: str
    token_mint: Optional[str] = None


class TokenBalance(BaseModel):
    mint: str
    amount: int
    decimals: int
    ui_amount: float


class BalanceResponse(BaseModel):
    wallet: str
    sol_balance: float
    tokens: List[TokenBalance]


class SwapRequest(BaseModel):
    """Request to execute a swap"""
    wallet_address: str  # Public key
    private_key: str  # Base58 encoded - should come from encrypted storage in production
    input_mint: str
    output_mint: str
    amount: int  # In smallest units
    slippage_bps: int = 50  # 0.5% default


class SwapResponse(BaseModel):
    success: bool
    signature: Optional[str] = None
    input_amount: int
    output_amount: int
    price_impact_pct: float
    error: Optional[str] = None


class QuoteRequest(BaseModel):
    """Get a quote without executing"""
    input_mint: str
    output_mint: str
    amount: int
    slippage_bps: int = 50


class QuoteResponse(BaseModel):
    input_mint: str
    output_mint: str
    in_amount: int
    out_amount: int
    price_impact_pct: float
    rate: float  # out/in


class LimitOrderRequest(BaseModel):
    """Create a limit order"""
    wallet_address: str
    private_key: str
    input_mint: str
    output_mint: str
    making_amount: int  # Amount to sell
    taking_amount: int  # Amount to receive
    expire_in_seconds: Optional[int] = None  # Optional expiry


class LimitOrderResponse(BaseModel):
    success: bool
    order_pubkey: Optional[str] = None
    signature: Optional[str] = None
    error: Optional[str] = None


class SpreadOrdersRequest(BaseModel):
    """Create market making spread orders"""
    wallet_address: str
    private_key: str
    base_mint: str  # Token to market make
    quote_mint: str = SOL_MINT  # Usually SOL
    base_amount: int  # Amount per side
    spread_bps: int = 50  # 0.5% spread
    expire_in_seconds: Optional[int] = 3600  # 1 hour default


class SpreadOrdersResponse(BaseModel):
    success: bool
    current_price: float
    buy_price: float
    sell_price: float
    spread_bps: int
    buy_signature: Optional[str] = None
    sell_signature: Optional[str] = None
    error: Optional[str] = None


class OpenOrdersRequest(BaseModel):
    wallet_address: str
    input_mint: Optional[str] = None
    output_mint: Optional[str] = None


class OpenOrder(BaseModel):
    order_pubkey: str
    input_mint: str
    output_mint: str
    making_amount: int
    taking_amount: int
    filled_amount: int
    status: str


class OpenOrdersResponse(BaseModel):
    wallet: str
    orders: List[OpenOrder]


class CancelOrderRequest(BaseModel):
    wallet_address: str
    private_key: str
    order_pubkey: str


class CancelAllOrdersRequest(BaseModel):
    wallet_address: str
    private_key: str
    input_mint: Optional[str] = None
    output_mint: Optional[str] = None


class CancelResponse(BaseModel):
    success: bool
    cancelled_count: int
    signature: Optional[str] = None
    error: Optional[str] = None


# ============ HELPER FUNCTIONS ============

async def get_jupiter_client() -> JupiterClient:
    """Dependency to get Jupiter client"""
    client = JupiterClient(rpc_url=SOLANA_RPC_URL)
    try:
        yield client
    finally:
        await client.close()


async def get_signer() -> SolanaTransactionSigner:
    """Dependency to get transaction signer"""
    signer = SolanaTransactionSigner(rpc_url=SOLANA_RPC_URL)
    try:
        yield signer
    finally:
        await signer.close()


# ============ PRICE ENDPOINTS ============

@router.get("/price", response_model=PriceResponse)
async def get_price(
    token_mint: str,
    vs_token: str = SOL_MINT,
    jupiter: JupiterClient = Depends(get_jupiter_client)
):
    """Get current price of a token"""
    try:
        price_data = await jupiter.get_price(token_mint, vs_token)
        return PriceResponse(
            mint=price_data["mint"],
            price=price_data["price"],
            vs_token=price_data["vs_token"]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ BALANCE ENDPOINTS ============

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    wallet_address: str,
    token_mint: Optional[str] = None,
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """Get wallet balances (SOL and tokens)"""
    try:
        # Get SOL balance
        sol_lamports = await signer.get_balance(wallet_address)
        sol_balance = sol_lamports / 1e9
        
        # Get token accounts
        token_accounts = await signer.get_token_accounts(wallet_address, token_mint)
        
        tokens = [
            TokenBalance(
                mint=acc["mint"],
                amount=acc["amount"],
                decimals=acc["decimals"],
                ui_amount=acc["ui_amount"]
            )
            for acc in token_accounts
        ]
        
        return BalanceResponse(
            wallet=wallet_address,
            sol_balance=sol_balance,
            tokens=tokens
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ QUOTE ENDPOINTS ============

@router.post("/quote", response_model=QuoteResponse)
async def get_quote(
    request: QuoteRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client)
):
    """Get a swap quote without executing"""
    try:
        quote = await jupiter.get_quote(
            input_mint=request.input_mint,
            output_mint=request.output_mint,
            amount=request.amount,
            slippage_bps=request.slippage_bps
        )
        
        rate = quote.out_amount / quote.in_amount if quote.in_amount > 0 else 0
        
        return QuoteResponse(
            input_mint=quote.input_mint,
            output_mint=quote.output_mint,
            in_amount=quote.in_amount,
            out_amount=quote.out_amount,
            price_impact_pct=quote.price_impact_pct,
            rate=rate
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ SWAP ENDPOINTS (Volume Generation) ============

@router.post("/swap", response_model=SwapResponse)
async def execute_swap(
    request: SwapRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client),
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """
    Execute a swap on Jupiter (for volume generation)
    
    This will:
    1. Get a quote
    2. Get the swap transaction
    3. Sign with provided private key
    4. Submit to Solana
    """
    try:
        # Get quote
        quote = await jupiter.get_quote(
            input_mint=request.input_mint,
            output_mint=request.output_mint,
            amount=request.amount,
            slippage_bps=request.slippage_bps
        )
        
        # Get swap transaction
        swap_tx = await jupiter.get_swap_transaction(
            quote=quote,
            user_public_key=request.wallet_address
        )
        
        # Sign and send
        result = await signer.sign_and_send_transaction(
            transaction_base64=swap_tx.transaction,
            private_key=request.private_key
        )
        
        if not result.success:
            return SwapResponse(
                success=False,
                input_amount=quote.in_amount,
                output_amount=quote.out_amount,
                price_impact_pct=quote.price_impact_pct,
                error=result.error
            )
        
        return SwapResponse(
            success=True,
            signature=result.signature,
            input_amount=quote.in_amount,
            output_amount=quote.out_amount,
            price_impact_pct=quote.price_impact_pct
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ LIMIT ORDER ENDPOINTS (Market Making) ============

@router.post("/limit-order", response_model=LimitOrderResponse)
async def create_limit_order(
    request: LimitOrderRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client),
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """
    Create a limit order on Jupiter
    
    For market making, create orders at desired prices
    """
    try:
        # Calculate expiry
        expired_at = None
        if request.expire_in_seconds:
            expired_at = int(time.time()) + request.expire_in_seconds
        
        # Create limit order
        order_data = await jupiter.create_limit_order(
            maker=request.wallet_address,
            input_mint=request.input_mint,
            output_mint=request.output_mint,
            making_amount=request.making_amount,
            taking_amount=request.taking_amount,
            expired_at=expired_at
        )
        
        # Sign and send
        tx_base64 = order_data.get("tx") or order_data.get("transaction")
        if not tx_base64:
            return LimitOrderResponse(
                success=False,
                error="No transaction returned from Jupiter"
            )
        
        result = await signer.sign_and_send_transaction(
            transaction_base64=tx_base64,
            private_key=request.private_key
        )
        
        if not result.success:
            return LimitOrderResponse(
                success=False,
                error=result.error
            )
        
        return LimitOrderResponse(
            success=True,
            order_pubkey=order_data.get("orderPubkey"),
            signature=result.signature
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spread-orders", response_model=SpreadOrdersResponse)
async def create_spread_orders(
    request: SpreadOrdersRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client),
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """
    Create buy and sell limit orders at spread from current price
    
    This is the main market making function:
    - Gets current price
    - Creates a BUY order at (price - spread)
    - Creates a SELL order at (price + spread)
    """
    try:
        # Calculate expiry
        expired_at = None
        if request.expire_in_seconds:
            expired_at = int(time.time()) + request.expire_in_seconds
        
        # Create spread orders
        spread_data = await jupiter.create_spread_orders(
            maker=request.wallet_address,
            base_mint=request.base_mint,
            quote_mint=request.quote_mint,
            base_amount=request.base_amount,
            spread_bps=request.spread_bps,
            expired_at=expired_at
        )
        
        buy_signature = None
        sell_signature = None
        error = None
        
        # Sign and send buy order
        buy_tx = spread_data["buy_order"].get("tx") or spread_data["buy_order"].get("transaction")
        if buy_tx:
            buy_result = await signer.sign_and_send_transaction(
                transaction_base64=buy_tx,
                private_key=request.private_key
            )
            if buy_result.success:
                buy_signature = buy_result.signature
            else:
                error = f"Buy order failed: {buy_result.error}"
        
        # Sign and send sell order
        sell_tx = spread_data["sell_order"].get("tx") or spread_data["sell_order"].get("transaction")
        if sell_tx:
            sell_result = await signer.sign_and_send_transaction(
                transaction_base64=sell_tx,
                private_key=request.private_key
            )
            if sell_result.success:
                sell_signature = sell_result.signature
            else:
                if error:
                    error += f"; Sell order failed: {sell_result.error}"
                else:
                    error = f"Sell order failed: {sell_result.error}"
        
        success = buy_signature is not None or sell_signature is not None
        
        return SpreadOrdersResponse(
            success=success,
            current_price=spread_data["current_price"],
            buy_price=spread_data["buy_price"],
            sell_price=spread_data["sell_price"],
            spread_bps=spread_data["spread_bps"],
            buy_signature=buy_signature,
            sell_signature=sell_signature,
            error=error
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders", response_model=OpenOrdersResponse)
async def get_open_orders(
    wallet_address: str,
    input_mint: Optional[str] = None,
    output_mint: Optional[str] = None,
    jupiter: JupiterClient = Depends(get_jupiter_client)
):
    """Get all open limit orders for a wallet"""
    try:
        orders = await jupiter.get_open_orders(
            wallet=wallet_address,
            input_mint=input_mint,
            output_mint=output_mint
        )
        
        return OpenOrdersResponse(
            wallet=wallet_address,
            orders=[
                OpenOrder(
                    order_pubkey=o.order_pubkey,
                    input_mint=o.input_mint,
                    output_mint=o.output_mint,
                    making_amount=o.making_amount,
                    taking_amount=o.taking_amount,
                    filled_amount=o.filled_amount or 0,
                    status=o.status.value
                )
                for o in orders
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel-order", response_model=CancelResponse)
async def cancel_order(
    request: CancelOrderRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client),
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """Cancel a specific limit order"""
    try:
        cancel_data = await jupiter.cancel_order(
            maker=request.wallet_address,
            order_pubkey=request.order_pubkey
        )
        
        tx_base64 = cancel_data.get("tx") or cancel_data.get("transaction")
        if not tx_base64:
            return CancelResponse(
                success=False,
                cancelled_count=0,
                error="No transaction returned"
            )
        
        result = await signer.sign_and_send_transaction(
            transaction_base64=tx_base64,
            private_key=request.private_key
        )
        
        if not result.success:
            return CancelResponse(
                success=False,
                cancelled_count=0,
                error=result.error
            )
        
        return CancelResponse(
            success=True,
            cancelled_count=1,
            signature=result.signature
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel-all-orders", response_model=CancelResponse)
async def cancel_all_orders(
    request: CancelAllOrdersRequest,
    jupiter: JupiterClient = Depends(get_jupiter_client),
    signer: SolanaTransactionSigner = Depends(get_signer)
):
    """Cancel all open limit orders, optionally filtered by token"""
    try:
        cancel_data = await jupiter.cancel_all_orders(
            maker=request.wallet_address,
            input_mint=request.input_mint,
            output_mint=request.output_mint
        )
        
        if cancel_data.get("cancelled") == 0:
            return CancelResponse(
                success=True,
                cancelled_count=0
            )
        
        tx_base64 = cancel_data.get("tx") or cancel_data.get("transaction")
        if not tx_base64:
            return CancelResponse(
                success=False,
                cancelled_count=0,
                error="No transaction returned"
            )
        
        result = await signer.sign_and_send_transaction(
            transaction_base64=tx_base64,
            private_key=request.private_key
        )
        
        if not result.success:
            return CancelResponse(
                success=False,
                cancelled_count=0,
                error=result.error
            )
        
        return CancelResponse(
            success=True,
            cancelled_count=len(cancel_data.get("orders", [])),
            signature=result.signature
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ HEALTH CHECK ============

@router.get("/health")
async def health_check():
    """Check if Solana connector is working"""
    return {
        "status": "ok",
        "rpc_url": SOLANA_RPC_URL,
        "features": [
            "price",
            "balance",
            "quote",
            "swap",
            "limit-order",
            "spread-orders",
            "cancel-order"
        ]
    }
