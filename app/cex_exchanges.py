"""
Exchange-specific configurations for ccxt.
"""

EXCHANGE_CONFIGS = {
    "bitmart": {
        "ccxt_id": "bitmart",
        "requires_passphrase": False,
        "maker_fee": 0.0025,  # 0.25%
        "taker_fee": 0.0025,
        "min_order_value_usd": 5,
        "rate_limit_ms": 100,
        "sandbox": False,
    },
    "coinstore": {
        "ccxt_id": "coinstore",
        "requires_passphrase": False,
        "maker_fee": 0.001,  # 0.1%
        "taker_fee": 0.001,
        "min_order_value_usd": 1,
        "rate_limit_ms": 100,
        "sandbox": False,
    },
    "binance": {
        "ccxt_id": "binance",
        "requires_passphrase": False,
        "maker_fee": 0.001,
        "taker_fee": 0.001,
        "min_order_value_usd": 10,
        "rate_limit_ms": 50,
        "sandbox": True,  # Has testnet
    },
    "kucoin": {
        "ccxt_id": "kucoin",
        "requires_passphrase": True,
        "maker_fee": 0.001,
        "taker_fee": 0.001,
        "min_order_value_usd": 1,
        "rate_limit_ms": 100,
        "sandbox": True,
    },
}


def get_exchange_config(exchange: str) -> dict:
    """Get exchange configuration by name."""
    if not exchange or not isinstance(exchange, str):
        exchange = "bitmart"
    return EXCHANGE_CONFIGS.get(exchange.lower(), EXCHANGE_CONFIGS["bitmart"])
