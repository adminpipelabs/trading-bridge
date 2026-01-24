import httpx
import base64
import json
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

JUPITER_API = "https://quote-api.jup.ag/v6"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# Common token mints
TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"
}

async def get_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{JUPITER_API}/quote",
            params={
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": slippage_bps
            }
        )
        return res.json()

async def execute_swap(input_mint: str, output_mint: str, amount: int, private_key: str):
    # Get quote
    quote = await get_quote(input_mint, output_mint, amount)
    
    # Create keypair from private key
    keypair = Keypair.from_base58_string(private_key)
    
    # Get swap transaction
    async with httpx.AsyncClient() as client:
        swap_res = await client.post(
            f"{JUPITER_API}/swap",
            json={
                "quoteResponse": quote,
                "userPublicKey": str(keypair.pubkey()),
                "wrapAndUnwrapSol": True
            }
        )
        swap_data = swap_res.json()
    
    # Deserialize and sign transaction
    tx_bytes = base64.b64decode(swap_data["swapTransaction"])
    tx = VersionedTransaction.from_bytes(tx_bytes)
    tx.sign([keypair])
    
    # Send transaction
    solana_client = Client(SOLANA_RPC)
    result = solana_client.send_transaction(tx)
    
    return {
        "success": True,
        "signature": str(result.value),
        "input_amount": amount,
        "output_amount": quote.get("outAmount"),
        "route": quote.get("routePlan")
    }

async def get_token_balance(wallet_address: str, token_mint: str):
    solana_client = Client(SOLANA_RPC)
    
    if token_mint == TOKENS["SOL"]:
        result = solana_client.get_balance(wallet_address)
        return {"balance": result.value / 1e9, "token": "SOL"}
    else:
        # Get token account balance
        result = solana_client.get_token_accounts_by_owner_json_parsed(
            wallet_address,
            {"mint": token_mint}
        )
        if result.value:
            balance = result.value[0].account.data.parsed["info"]["tokenAmount"]["uiAmount"]
            return {"balance": balance, "mint": token_mint}
        return {"balance": 0, "mint": token_mint}
