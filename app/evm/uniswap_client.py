"""
Uniswap Universal Router client for EVM chains.
Supports swaps via Universal Router (V3 + V4).
"""
import time
import logging
from dataclasses import dataclass
from typing import Optional
from web3 import Web3
from eth_abi import encode as abi_encode
from circuitbreaker import circuit
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .chains import ChainConfig
from .evm_signer import EVMSigner
from web3.exceptions import ContractLogicError, TransactionNotFound

logger = logging.getLogger(__name__)

# Permit2 expiration buffer (1 hour)
PERMIT2_EXPIRATION_BUFFER = 3600

# Fee tiers to try (in order of preference)
FEE_TIERS = [3000, 500, 10000, 100]  # 0.3%, 0.05%, 1%, 0.01%


@dataclass
class SwapQuote:
    """Swap quote result."""
    input_token: str
    output_token: str
    input_amount: int
    output_amount: int
    price_impact: float
    fee_tier: int


# Quoter V2 ABI (minimal)
QUOTER_V2_ABI = [
    {
        "inputs": [{
            "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "fee", "type": "uint24"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"}
            ],
            "name": "params",
            "type": "tuple"
        }],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Universal Router ABI (minimal)
UNIVERSAL_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "commands", "type": "bytes"},
            {"name": "inputs", "type": "bytes[]"},
            {"name": "deadline", "type": "uint256"}
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

# Permit2 ABI (minimal)
PERMIT2_ABI = [
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "token", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"},
            {"name": "nonce", "type": "uint48"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "token", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint160"},
            {"name": "expiration", "type": "uint48"}
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


class UniswapClient:
    """Client for Uniswap swaps via Universal Router."""
    
    def __init__(self, chain_config: ChainConfig):
        """
        Initialize Uniswap client.
        
        Args:
            chain_config: Chain configuration
        """
        self.chain = chain_config
        
        # Initialize Web3 (will use RPC fallback from EVMSigner)
        from .evm_signer import get_rpc_url
        rpc_url = get_rpc_url(chain_config.name, primary=True)
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
        
        # Initialize Quoter contract
        self.quoter = self.w3.eth.contract(
            address=Web3.to_checksum_address(chain_config.quoter_v2),
            abi=QUOTER_V2_ABI
        )
        
        logger.info(
            f"Uniswap client initialized for {chain_config.name}",
            extra={"chain": chain_config.name}
        )
    
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ContractLogicError, ValueError)),
        reraise=True
    )
    async def get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
    ) -> SwapQuote:
        """
        Get best quote across fee tiers.
        Protected by circuit breaker and retry logic.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in smallest units
        
        Returns:
            SwapQuote with best output amount
        
        Raises:
            Exception: If no liquidity found
        """
        best_output = 0
        best_fee = None
        
        for fee in FEE_TIERS:
            try:
                # QuoterV2.quoteExactInputSingle
                result = self.quoter.functions.quoteExactInputSingle({
                    "tokenIn": Web3.to_checksum_address(token_in),
                    "tokenOut": Web3.to_checksum_address(token_out),
                    "amountIn": amount_in,
                    "fee": fee,
                    "sqrtPriceLimitX96": 0
                }).call()
                
                amount_out = result[0]  # First element is amountOut
                
                if amount_out > best_output:
                    best_output = amount_out
                    best_fee = fee
                    
            except Exception as e:
                # No liquidity at this fee tier
                logger.debug(f"No liquidity at fee tier {fee}: {e}")
                continue
        
        if best_output == 0:
            raise Exception(f"No liquidity found for {token_in} -> {token_out}")
        
        # Calculate price impact (simplified - would need more data for accurate calculation)
        price_impact = 0.0  # TODO: Calculate actual price impact
        
        logger.info(
            f"Quote obtained",
            extra={
                "token_in": token_in[:10] + "...",
                "token_out": token_out[:10] + "...",
                "amount_in": amount_in,
                "amount_out": best_output,
                "fee_tier": best_fee
            }
        )
        
        return SwapQuote(
            input_token=token_in,
            output_token=token_out,
            input_amount=amount_in,
            output_amount=best_output,
            price_impact=price_impact,
            fee_tier=best_fee or 3000
        )
    
    async def _ensure_erc20_approval(self, signer: EVMSigner, token: str, spender: str, amount: int):
        """Check and set ERC20 approval if needed."""
        current_allowance = signer.get_token_allowance(token, spender)
        
        if current_allowance < amount:
            logger.info(f"Approving ERC20 token for {spender[:10]}...")
            # Approve max amount
            await signer.approve_token(token, spender, 2**256 - 1)
    
    async def _ensure_permit2_approval(self, signer: EVMSigner, token: str, spender: str, amount: int):
        """
        Ensure Permit2 approval with expiration buffer.
        Renews if expired or expiring within buffer period.
        """
        # Get Web3 instance from signer (need to access private w3)
        w3 = self.w3  # Use client's Web3 instance
        
        permit2 = w3.eth.contract(
            address=Web3.to_checksum_address(self.chain.permit2),
            abi=PERMIT2_ABI
        )
        
        # Check current allowance
        allowance_data = permit2.functions.allowance(
            signer.address,
            Web3.to_checksum_address(token),
            Web3.to_checksum_address(spender)
        ).call()
        
        current_amount = allowance_data[0]
        expiration = allowance_data[1]
        now = int(time.time())
        
        # Check if approval is sufficient and not expiring soon
        if current_amount >= amount and expiration > (now + PERMIT2_EXPIRATION_BUFFER):
            logger.debug(f"Permit2 approval sufficient (expires in {expiration - now}s)")
            return
        
        # Approve via Permit2
        logger.info(f"Setting Permit2 approval for {token[:10]}...")
        
        max_amount = 2**160 - 1  # Max uint160
        max_expiration = 2**48 - 1  # Max uint48 (~8.9 million years)
        
        tx = permit2.functions.approve(
            Web3.to_checksum_address(token),
            Web3.to_checksum_address(spender),
            max_amount,
            max_expiration
        ).build_transaction({
            "from": signer.address,
            "gas": 150000,
            "nonce": w3.eth.get_transaction_count(signer.address),
            "chainId": self.chain.chain_id,
        })
        
        # Set gas price
        try:
            fee_history = w3.eth.fee_history(1, "latest")
            base_fee = fee_history["baseFeePerGas"][0]
            max_priority_fee = w3.eth.max_priority_fee
            
            tx["maxFeePerGas"] = base_fee * 2 + max_priority_fee
            tx["maxPriorityFeePerGas"] = max_priority_fee
        except Exception:
            tx["gasPrice"] = w3.eth.gas_price
        
        await signer.send_transaction(tx)
        logger.info("Permit2 approval set successfully")
    
    def _encode_swap_command(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        recipient: str,
        fee_tier: int = 3000,
    ) -> tuple:
        """
        Encode Universal Router swap command.
        
        Command: V3_SWAP_EXACT_IN = 0x00
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount
            min_amount_out: Minimum output amount
            recipient: Recipient address
            fee_tier: Fee tier (3000 = 0.3%)
        
        Returns:
            Tuple of (commands bytes, inputs list)
        """
        # Command byte: V3_SWAP_EXACT_IN = 0x00
        commands = bytes([0x00])
        
        # Encode path: tokenIn (20 bytes) + fee (3 bytes) + tokenOut (20 bytes)
        token_in_bytes = bytes.fromhex(token_in.replace("0x", "").zfill(40))
        token_out_bytes = bytes.fromhex(token_out.replace("0x", "").zfill(40))
        fee_bytes = fee_tier.to_bytes(3, 'big')
        path = token_in_bytes + fee_bytes + token_out_bytes
        
        # Encode input for V3_SWAP_EXACT_IN
        # Parameters: (address recipient, uint256 amountIn, uint256 amountOutMin, bytes path, bool payerIsUser)
        encoded_input = abi_encode(
            ['address', 'uint256', 'uint256', 'bytes', 'bool'],
            [
                Web3.to_checksum_address(recipient),
                amount_in,
                min_amount_out,
                path,
                True  # payerIsUser
            ]
        )
        
        return commands, [encoded_input]
    
    @circuit(failure_threshold=5, recovery_timeout=60, expected_exception=Exception)
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ContractLogicError, ValueError)),
        reraise=True
    )
    async def execute_swap(
        self,
        signer: EVMSigner,
        token_in: str,
        token_out: str,
        amount_in: int,
        slippage_bps: int = 50,  # 0.5%
    ) -> str:
        """
        Execute swap via Universal Router.
        Protected by circuit breaker and retry logic.
        
        Args:
            signer: EVM signer instance
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in smallest units
            slippage_bps: Slippage tolerance in basis points
        
        Returns:
            Transaction hash
        """
        # 1. Get quote
        quote = await self.get_quote(token_in, token_out, amount_in)
        min_amount_out = int(quote.output_amount * (10000 - slippage_bps) / 10000)
        
        logger.info(
            f"Executing swap",
            extra={
                "token_in": token_in[:10] + "...",
                "token_out": token_out[:10] + "...",
                "amount_in": amount_in,
                "amount_out": quote.output_amount,
                "min_amount_out": min_amount_out,
                "slippage_bps": slippage_bps
            }
        )
        
        # 2. Approve ERC20 token for Permit2 (if needed)
        await self._ensure_erc20_approval(signer, token_in, self.chain.permit2, amount_in)
        
        # 3. Approve Universal Router via Permit2 (if needed)
        await self._ensure_permit2_approval(signer, token_in, self.chain.universal_router, amount_in)
        
        # 4. Build Universal Router command
        deadline = int(time.time()) + 300  # 5 minutes
        
        commands, inputs = self._encode_swap_command(
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            min_amount_out=min_amount_out,
            recipient=signer.address,
            fee_tier=quote.fee_tier,
        )
        
        # 5. Build transaction
        router = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.chain.universal_router),
            abi=UNIVERSAL_ROUTER_ABI
        )
        
        tx = router.functions.execute(
            commands,
            inputs,
            deadline
        ).build_transaction({
            "from": signer.address,
            "value": 0,
            "gas": 500000,  # Safe default for Universal Router
            "nonce": self.w3.eth.get_transaction_count(signer.address),
            "chainId": self.chain.chain_id,
        })
        
        # Estimate gas with buffer
        try:
            estimated_gas = self.w3.eth.estimate_gas(tx)
            tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default")
            tx["gas"] = 500000
        
        # Set gas price (EIP-1559 if available)
        try:
            fee_history = self.w3.eth.fee_history(1, "latest")
            base_fee = fee_history["baseFeePerGas"][0]
            max_priority_fee = self.w3.eth.max_priority_fee
            
            tx["maxFeePerGas"] = base_fee * 2 + max_priority_fee
            tx["maxPriorityFeePerGas"] = max_priority_fee
        except Exception:
            tx["gasPrice"] = self.w3.eth.gas_price
        
        # 6. Send transaction
        try:
            tx_hash = await signer.send_transaction(tx)
            logger.info(
                f"Swap executed successfully",
                extra={"tx": tx_hash[:20] + "...", "amount_in": amount_in, "amount_out": quote.output_amount}
            )
            return tx_hash
        except ContractLogicError as e:
            logger.error(f"Contract revert: {e}")
            raise Exception(f"Swap failed: {str(e)}")
        except Exception as e:
            logger.error(f"Swap execution failed: {e}")
            raise
