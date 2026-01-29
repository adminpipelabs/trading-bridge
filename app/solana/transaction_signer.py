"""
Solana Transaction Signer
Signs and submits transactions to the Solana network
"""

import base64
import base58
import httpx
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from nacl.signing import SigningKey
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.signature import Signature


@dataclass
class TransactionResult:
    success: bool
    signature: Optional[str] = None
    error: Optional[str] = None
    slot: Optional[int] = None


class SolanaTransactionSigner:
    """
    Signs and submits Solana transactions
    Uses nacl for signing and Solana JSON-RPC for submission
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        await self.client.aclose()
    
    @staticmethod
    def keypair_from_private_key(private_key: str) -> Keypair:
        """
        Create Keypair from private key
        Supports multiple formats:
        - Base58 encoded string (64 bytes when decoded = full keypair)
        - Base58 encoded string (32 bytes when decoded = seed)
        - JSON array string like "[1,2,3,...]"
        - Comma-separated string like "1,2,3,..."
        
        Args:
            private_key: Private key in various formats
        
        Returns:
            Keypair object
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Try base58 first (most common)
        try:
            decoded = base58.b58decode(private_key)
            
            if len(decoded) == 64:
                # Full keypair (private + public)
                return Keypair.from_bytes(decoded)
            elif len(decoded) == 32:
                # Seed only
                return Keypair.from_seed(decoded)
            else:
                raise ValueError(f"Invalid private key length: {len(decoded)}")
        except Exception as base58_error:
            # Base58 failed, try other formats
            logger.debug(f"Base58 decode failed: {base58_error}, trying alternative formats...")
            try:
                import json
                key_bytes = None
                
                # Try JSON array format
                if private_key.startswith('['):
                    key_bytes = bytes(json.loads(private_key))
                # Try comma-separated numbers
                elif ',' in private_key:
                    key_bytes = bytes([int(x.strip()) for x in private_key.split(',')])
                # Try hex format (with or without 0x prefix, with or without underscores)
                elif '0x' in private_key.lower() or all(c in '0123456789abcdefABCDEF_' for c in private_key):
                    # Remove 0x prefix and underscores
                    hex_str = private_key.replace('0x', '').replace('0X', '').replace('_', '').replace('-', '')
                    try:
                        key_bytes = bytes.fromhex(hex_str)
                    except ValueError as hex_error:
                        logger.error(f"Failed to parse hex: {hex_error}")
                        raise ValueError(f"Invalid hex format. Base58 error: {base58_error}")
                # Try underscore-separated decimal numbers
                elif '_' in private_key and all(c.isdigit() or c == '_' for c in private_key):
                    key_bytes = bytes([int(x) for x in private_key.split('_') if x])
                else:
                    raise ValueError(f"Unknown private key format. Base58 error: {base58_error}")
                
                if not key_bytes:
                    raise ValueError(f"Could not parse private key. Base58 error: {base58_error}")
                
                if len(key_bytes) == 64:
                    return Keypair.from_bytes(key_bytes)
                elif len(key_bytes) == 32:
                    return Keypair.from_seed(key_bytes)
                else:
                    raise ValueError(f"Invalid key length: {len(key_bytes)}, expected 32 or 64")
            except Exception as parse_error:
                logger.error(f"Failed to parse private key. Base58 error: {base58_error}, Parse error: {parse_error}")
                logger.error(f"Private key sample (first 50 chars): {private_key[:50]}...")
                raise ValueError(f"Invalid private key format. Must be base58, JSON array, hex, or comma/underscore-separated. Base58 error: {base58_error}, Parse error: {parse_error}")
    
    @staticmethod
    def get_public_key(private_key: str) -> str:
        """Get public key from private key"""
        keypair = SolanaTransactionSigner.keypair_from_private_key(private_key)
        return str(keypair.pubkey())
    
    async def sign_transaction(
        self,
        transaction_base64: str,
        private_key: str
    ) -> str:
        """
        Sign a base64 encoded transaction
        
        Args:
            transaction_base64: Base64 encoded transaction from Jupiter
            private_key: Base58 encoded private key
        
        Returns:
            Base64 encoded signed transaction
        """
        # Decode transaction
        tx_bytes = base64.b64decode(transaction_base64)
        
        # Parse as versioned transaction
        tx = VersionedTransaction.from_bytes(tx_bytes)
        
        # Get keypair
        keypair = self.keypair_from_private_key(private_key)
        
        # Sign the transaction
        tx.sign([keypair])
        
        # Return base64 encoded
        return base64.b64encode(bytes(tx)).decode('utf-8')
    
    async def sign_and_send_transaction(
        self,
        transaction_base64: str,
        private_key: str,
        skip_preflight: bool = False,
        max_retries: int = 3
    ) -> TransactionResult:
        """
        Sign and send a transaction to Solana
        
        Args:
            transaction_base64: Base64 encoded transaction
            private_key: Base58 encoded private key
            skip_preflight: Skip preflight simulation
            max_retries: Number of retry attempts
        
        Returns:
            TransactionResult with signature or error
        """
        try:
            # Sign the transaction
            signed_tx = await self.sign_transaction(transaction_base64, private_key)
            
            # Send to network
            return await self.send_transaction(
                signed_tx, 
                skip_preflight=skip_preflight,
                max_retries=max_retries
            )
            
        except Exception as e:
            return TransactionResult(
                success=False,
                error=str(e)
            )
    
    async def send_transaction(
        self,
        signed_transaction_base64: str,
        skip_preflight: bool = False,
        max_retries: int = 3
    ) -> TransactionResult:
        """
        Send a signed transaction to Solana
        
        Args:
            signed_transaction_base64: Base64 encoded signed transaction
            skip_preflight: Skip preflight simulation
            max_retries: Number of retry attempts
        
        Returns:
            TransactionResult with signature or error
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "sendTransaction",
            "params": [
                signed_transaction_base64,
                {
                    "encoding": "base64",
                    "skipPreflight": skip_preflight,
                    "preflightCommitment": "confirmed",
                    "maxRetries": max_retries
                }
            ]
        }
        
        try:
            response = await self.client.post(
                self.rpc_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            
            if "error" in data:
                return TransactionResult(
                    success=False,
                    error=data["error"].get("message", str(data["error"]))
                )
            
            signature = data.get("result")
            return TransactionResult(
                success=True,
                signature=signature
            )
            
        except Exception as e:
            return TransactionResult(
                success=False,
                error=str(e)
            )
    
    async def confirm_transaction(
        self,
        signature: str,
        commitment: str = "confirmed",
        timeout_seconds: int = 30
    ) -> TransactionResult:
        """
        Wait for transaction confirmation
        
        Args:
            signature: Transaction signature
            commitment: Confirmation level (processed, confirmed, finalized)
            timeout_seconds: Timeout for confirmation
        
        Returns:
            TransactionResult with confirmation status
        """
        import asyncio
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                return TransactionResult(
                    success=False,
                    signature=signature,
                    error="Transaction confirmation timeout"
                )
            
            status = await self.get_signature_status(signature)
            
            if status.get("confirmationStatus") == commitment:
                return TransactionResult(
                    success=True,
                    signature=signature,
                    slot=status.get("slot")
                )
            
            if status.get("err"):
                return TransactionResult(
                    success=False,
                    signature=signature,
                    error=str(status["err"])
                )
            
            await asyncio.sleep(0.5)
    
    async def get_signature_status(self, signature: str) -> Dict[str, Any]:
        """Get the status of a transaction signature"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignatureStatuses",
            "params": [
                [signature],
                {"searchTransactionHistory": True}
            ]
        }
        
        response = await self.client.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        statuses = data.get("result", {}).get("value", [])
        if statuses and statuses[0]:
            return statuses[0]
        
        return {}
    
    async def get_balance(self, pubkey: str) -> int:
        """Get SOL balance in lamports"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [pubkey]
        }
        
        response = await self.client.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get("result", {}).get("value", 0)
    
    async def get_token_accounts(
        self,
        owner: str,
        mint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get token accounts for a wallet
        
        Args:
            owner: Wallet public key
            mint: Optional token mint to filter by
        
        Returns:
            List of token accounts with balances
        """
        params = [
            owner,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
        
        if mint:
            params[1] = {"mint": mint}
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": params
        }
        
        response = await self.client.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        accounts = []
        for item in data.get("result", {}).get("value", []):
            parsed = item.get("account", {}).get("data", {}).get("parsed", {})
            info = parsed.get("info", {})
            
            accounts.append({
                "pubkey": item.get("pubkey"),
                "mint": info.get("mint"),
                "owner": info.get("owner"),
                "amount": int(info.get("tokenAmount", {}).get("amount", 0)),
                "decimals": info.get("tokenAmount", {}).get("decimals", 0),
                "ui_amount": info.get("tokenAmount", {}).get("uiAmount", 0)
            })
        
        return accounts
    
    async def get_recent_blockhash(self) -> Tuple[str, int]:
        """Get recent blockhash and last valid block height"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getLatestBlockhash",
            "params": [{"commitment": "finalized"}]
        }
        
        response = await self.client.post(
            self.rpc_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        result = data.get("result", {}).get("value", {})
        return (
            result.get("blockhash", ""),
            result.get("lastValidBlockHeight", 0)
        )
