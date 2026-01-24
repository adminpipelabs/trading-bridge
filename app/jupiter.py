import httpx
import os

JUPITER_API = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")

TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"
}

DECIMALS = {
    "SOL": 9,
    "USDC": 6,
    "USDT": 6,
    "BONK": 5,
    "WIF": 6,
    "JUP": 6
}

async def get_quote(input_token: str, output_token: str, amount: float, slippage_bps: int = 50):
    input_mint = TOKENS.get(input_token.upper(), input_token)
    output_mint = TOKENS.get(output_token.upper(), output_token)
    
    in_decimals = DECIMALS.get(input_token.upper(), 9)
    out_decimals = DECIMALS.get(output_token.upper(), 6)
    
    amount_raw = int(amount * (10 ** in_decimals))
    
    # Configure httpx client with timeout and DNS settings for Railway
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            res = await client.get(
                f"{JUPITER_API}/quote",
                params={
                    "inputMint": input_mint,
                    "outputMint": output_mint,
                    "amount": amount_raw,
                    "slippageBps": slippage_bps
                }
            )
            res.raise_for_status()
            data = res.json()
        except httpx.ConnectError as e:
            raise Exception(f"Failed to connect to Jupiter API: {str(e)}. Check network connectivity and DNS resolution.")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Jupiter API returned error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Error calling Jupiter API: {str(e)}")
    
    out_amount = int(data.get("outAmount", 0)) / (10 ** out_decimals)
    
    return {
        "input_token": input_token,
        "output_token": output_token,
        "input_amount": amount,
        "output_amount": out_amount,
        "price_impact": data.get("priceImpactPct"),
        "route": len(data.get("routePlan", []))
    }
