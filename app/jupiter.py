import httpx
import os
import socket
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
# Jupiter API endpoint - updated to use public API (quote-api.jup.ag DNS may fail)
# Can be overridden via JUPITER_API_URL env var
# Options: https://quote-api.jup.ag/v6, https://public.jupiterapi.com, https://api.jup.ag
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
    
    # Parse URL and verify DNS resolution for Railway
    parsed_url = urlparse(JUPITER_API)
    hostname = parsed_url.hostname
    
    # Try to resolve DNS first (force IPv4 for Railway compatibility)
    try:
        # Force IPv4 resolution - Railway sometimes has IPv6 issues
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if not addr_info:
            logger.warning(f"No IPv4 address found for {hostname}")
        else:
            logger.info(f"DNS resolution successful for {hostname}: {addr_info[0][4][0]}")
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {hostname}: {str(e)}")
        raise Exception(f"DNS resolution failed for {hostname}: {str(e)}. Railway may have DNS configuration issues.")
    except Exception as e:
        # Log but don't fail - httpx might still work
        logger.warning(f"DNS pre-check failed: {e}")
    
    # Configure httpx client with timeout and DNS settings for Railway
    # Use trust_env=True to respect system DNS settings
    timeout = httpx.Timeout(30.0, connect=10.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    
    # Try primary endpoint first, fallback to alternative if DNS/connection fails
    endpoints = [
        f"{JUPITER_API}/quote",  # Primary: quote-api.jup.ag/v6/quote
        "https://public.jupiterapi.com/quote",  # Fallback: public API
    ]
    
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount_raw,
        "slippageBps": slippage_bps
    }
    
    last_error = None
    data = None
    
    for url in endpoints:
        logger.info(f"Trying Jupiter API: {url} with params: {params}")
        
        async with httpx.AsyncClient(
            timeout=timeout, 
            follow_redirects=True,
            limits=limits,
            trust_env=True  # Use system DNS settings
        ) as client:
            try:
                res = await client.get(url, params=params)
                logger.info(f"Jupiter API response status: {res.status_code} from {url}")
                res.raise_for_status()
                data = res.json()
                logger.info(f"Jupiter API response data keys: {list(data.keys())}")
                break  # Success, exit loop
            except httpx.ConnectError as e:
                logger.warning(f"Connection error to {url}: {str(e)}")
                last_error = e
                if url == endpoints[-1]:  # Last endpoint, raise error
                    raise Exception(f"Failed to connect to any Jupiter API endpoint. Last error: {str(e)}")
                continue  # Try next endpoint
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error from Jupiter API {url}: {e.response.status_code} - {e.response.text}")
                # If 401 Unauthorized, try next endpoint; otherwise raise
                if e.response.status_code == 401 and url != endpoints[-1]:
                    logger.warning(f"401 Unauthorized from {url}, trying next endpoint...")
                    last_error = e
                    continue
                raise Exception(f"Jupiter API returned error: {e.response.status_code} - {e.response.text}")
            except Exception as e:
                logger.error(f"Unexpected error calling Jupiter API {url}: {str(e)}", exc_info=True)
                if url == endpoints[-1]:  # Last endpoint
                    raise Exception(f"Error calling Jupiter API: {str(e)}")
                last_error = e
                continue
    
    if data is None:
        raise Exception(f"Failed to get quote from any Jupiter API endpoint. Last error: {str(last_error)}")
    
    out_amount = int(data.get("outAmount", 0)) / (10 ** out_decimals)
    
    return {
        "input_token": input_token,
        "output_token": output_token,
        "input_amount": amount,
        "output_amount": out_amount,
        "price_impact": data.get("priceImpactPct"),
        "route": len(data.get("routePlan", []))
    }
