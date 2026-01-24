import httpx

JUPITER_API = "https://quote-api.jup.ag/v6"

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
    
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{JUPITER_API}/quote",
            params={
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount_raw,
                "slippageBps": slippage_bps
            }
        )
        data = res.json()
    
    out_amount = int(data.get("outAmount", 0)) / (10 ** out_decimals)
    
    return {
        "input_token": input_token,
        "output_token": output_token,
        "input_amount": amount,
        "output_amount": out_amount,
        "price_impact": data.get("priceImpactPct"),
        "route": len(data.get("routePlan", []))
    }
