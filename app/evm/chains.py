"""
Chain configurations for EVM networks.
Supports Polygon, Arbitrum, Base, and Ethereum mainnet.
"""
import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ChainConfig:
    """Configuration for an EVM chain."""
    chain_id: int
    name: str
    rpc_url: str
    rpc_fallback: Optional[str]
    universal_router: str
    permit2: str
    quoter_v2: str
    wrapped_native: str
    usdc: str


def get_rpc_url(chain_name: str, primary: bool = True) -> str:
    """Get RPC URL from environment or use default."""
    env_key = f"{chain_name.upper()}_RPC_URL"
    fallback_key = f"{chain_name.upper()}_RPC_FALLBACK"
    
    if primary:
        return os.getenv(env_key) or CHAINS[chain_name].rpc_url
    else:
        return os.getenv(fallback_key) or CHAINS[chain_name].rpc_fallback or CHAINS[chain_name].rpc_url


CHAINS: Dict[str, ChainConfig] = {
    "polygon": ChainConfig(
        chain_id=137,
        name="Polygon",
        rpc_url=os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
        rpc_fallback=os.getenv("POLYGON_RPC_FALLBACK", "https://rpc.ankr.com/polygon"),
        universal_router="0x643770E279d5D0733F21d6DC03A8efbABf3255B4",
        permit2="0x000000000022D473030F116dDEE9F6B43aC78BA3",
        quoter_v2="0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        wrapped_native="0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
        usdc="0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
    ),
    "arbitrum": ChainConfig(
        chain_id=42161,
        name="Arbitrum",
        rpc_url=os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        rpc_fallback=os.getenv("ARBITRUM_RPC_FALLBACK", "https://rpc.ankr.com/arbitrum"),
        universal_router="0x5E325eDA8064b456f4781070C0738d849c824258",
        permit2="0x000000000022D473030F116dDEE9F6B43aC78BA3",
        quoter_v2="0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        wrapped_native="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
        usdc="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    ),
    "base": ChainConfig(
        chain_id=8453,
        name="Base",
        rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
        rpc_fallback=os.getenv("BASE_RPC_FALLBACK", "https://rpc.ankr.com/base"),
        universal_router="0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
        permit2="0x000000000022D473030F116dDEE9F6B43aC78BA3",
        quoter_v2="0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        wrapped_native="0x4200000000000000000000000000000000000006",  # WETH
        usdc="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    ),
    "ethereum": ChainConfig(
        chain_id=1,
        name="Ethereum",
        rpc_url=os.getenv("ETHEREUM_RPC_URL", "https://eth.llamarpc.com"),
        rpc_fallback=os.getenv("ETHEREUM_RPC_FALLBACK", "https://rpc.ankr.com/eth"),
        universal_router="0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
        permit2="0x000000000022D473030F116dDEE9F6B43aC78BA3",
        quoter_v2="0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        wrapped_native="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        usdc="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    ),
}


def get_chain(chain_name: str) -> ChainConfig:
    """Get chain configuration by name."""
    if chain_name not in CHAINS:
        raise ValueError(f"Unknown chain: {chain_name}. Supported: {list(CHAINS.keys())}")
    return CHAINS[chain_name]
