"""
EVM transaction signer for Ethereum-compatible chains.
Handles transaction signing, balance checks, and token approvals.
"""
import logging
from typing import Optional
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount

from .chains import ChainConfig, get_rpc_url

logger = logging.getLogger(__name__)

# Minimal ERC20 ABI for balance, decimals, approve, allowance
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
]


class EVMSigner:
    """Signs and sends transactions on EVM chains."""
    
    def __init__(self, chain_config: ChainConfig, private_key: str):
        """
        Initialize EVM signer.
        
        Args:
            chain_config: Chain configuration
            private_key: Private key as hex string (with or without 0x prefix)
        """
        self.chain = chain_config
        
        # Initialize Web3 with RPC fallback
        self.w3 = self._init_web3()
        
        # Load account from private key
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        self.account: LocalAccount = Account.from_key(private_key)
        self.address = self.account.address
        
        logger.info(
            f"EVM Signer initialized: {chain_config.name}",
            extra={"chain": chain_config.name, "address": self.address[:10] + "..."}
        )
    
    def _init_web3(self) -> Web3:
        """Initialize Web3 with RPC fallback."""
        # Try primary RPC first
        try:
            rpc_url = get_rpc_url(self.chain.name, primary=True)
            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
            # Test connection
            w3.eth.block_number
            logger.info(f"Connected to {self.chain.name} via primary RPC")
            return w3
        except Exception as e:
            logger.warning(f"Primary RPC failed: {e}, trying fallback...")
            
            # Try fallback RPC
            try:
                rpc_url = get_rpc_url(self.chain.name, primary=False)
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
                w3.eth.block_number
                logger.info(f"Connected to {self.chain.name} via fallback RPC")
                return w3
            except Exception as e2:
                logger.error(f"All RPC providers failed for {self.chain.name}: {e2}")
                raise Exception(f"Failed to connect to {self.chain.name}: {e2}")
    
    def get_native_balance(self) -> int:
        """Get native token balance (POL/ETH/etc) in wei."""
        return self.w3.eth.get_balance(self.address)
    
    def get_native_balance_formatted(self) -> float:
        """Get native token balance formatted (POL/ETH/etc)."""
        balance_wei = self.get_native_balance()
        return self.w3.from_wei(balance_wei, "ether")
    
    def get_token_balance(self, token_address: str) -> int:
        """Get ERC20 token balance."""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        return contract.functions.balanceOf(self.address).call()
    
    def get_token_decimals(self, token_address: str) -> int:
        """Get token decimals."""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        return contract.functions.decimals().call()
    
    def get_token_allowance(self, token_address: str, spender: str) -> int:
        """Get token allowance for spender."""
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        return contract.functions.allowance(self.address, Web3.to_checksum_address(spender)).call()
    
    async def approve_token(self, token: str, spender: str, amount: int) -> str:
        """
        Approve token spending.
        
        Args:
            token: Token contract address
            spender: Spender contract address
            amount: Amount to approve (use 2**256-1 for max)
        
        Returns:
            Transaction hash
        """
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token),
            abi=ERC20_ABI
        )
        
        nonce = self.w3.eth.get_transaction_count(self.address)
        
        # Build transaction
        tx = contract.functions.approve(
            Web3.to_checksum_address(spender),
            amount
        ).build_transaction({
            "from": self.address,
            "nonce": nonce,
            "chainId": self.chain.chain_id,
        })
        
        # Estimate gas
        try:
            estimated_gas = self.w3.eth.estimate_gas(tx)
            tx["gas"] = int(estimated_gas * 1.2)  # 20% buffer
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default")
            tx["gas"] = 100000
        
        # Set gas price (EIP-1559 if available)
        try:
            fee_history = self.w3.eth.fee_history(1, "latest")
            base_fee = fee_history["baseFeePerGas"][0]
            max_priority_fee = self.w3.eth.max_priority_fee
            
            tx["maxFeePerGas"] = base_fee * 2 + max_priority_fee
            tx["maxPriorityFeePerGas"] = max_priority_fee
        except Exception:
            # Fallback to legacy gas pricing
            tx["gasPrice"] = self.w3.eth.gas_price
        
        # Sign and send
        signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt["status"] != 1:
            raise Exception(f"Approval transaction failed: {tx_hash.hex()}")
        
        logger.info(
            f"Token approval successful",
            extra={"token": token[:10] + "...", "spender": spender[:10] + "...", "tx": tx_hash.hex()[:20] + "..."}
        )
        
        return tx_hash.hex()
    
    async def send_transaction(self, tx_data: dict) -> str:
        """
        Sign and send transaction.
        
        Args:
            tx_data: Transaction data dictionary
        
        Returns:
            Transaction hash
        """
        # Set required fields
        tx_data.setdefault("from", self.address)
        tx_data.setdefault("nonce", self.w3.eth.get_transaction_count(self.address))
        tx_data.setdefault("chainId", self.chain.chain_id)
        
        # Set gas if not provided
        if "gas" not in tx_data:
            try:
                estimated_gas = self.w3.eth.estimate_gas(tx_data)
                tx_data["gas"] = int(estimated_gas * 1.2)  # 20% buffer
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default")
                tx_data["gas"] = 300000  # Safe default
        
        # Set gas price (EIP-1559 if available)
        if "gasPrice" not in tx_data and "maxFeePerGas" not in tx_data:
            try:
                fee_history = self.w3.eth.fee_history(1, "latest")
                base_fee = fee_history["baseFeePerGas"][0]
                max_priority_fee = self.w3.eth.max_priority_fee
                
                tx_data["maxFeePerGas"] = base_fee * 2 + max_priority_fee
                tx_data["maxPriorityFeePerGas"] = max_priority_fee
            except Exception:
                # Fallback to legacy gas pricing
                tx_data["gasPrice"] = self.w3.eth.gas_price
        
        # Sign transaction
        signed = self.w3.eth.account.sign_transaction(tx_data, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        # Wait for confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt["status"] != 1:
            raise Exception(f"Transaction failed: {tx_hash.hex()}")
        
        logger.info(
            f"Transaction successful",
            extra={"tx": tx_hash.hex()[:20] + "...", "gas_used": receipt["gasUsed"]}
        )
        
        return tx_hash.hex()
