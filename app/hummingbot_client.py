"""
Hummingbot API Client
=====================

HTTP client for communicating with Hummingbot API.
Handles authentication and all bot orchestration endpoints.
"""

import httpx
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HummingbotClient:
    """Client for Hummingbot API communication"""
    
    def __init__(self):
        """Initialize Hummingbot client with credentials from environment"""
        self.base_url = os.getenv(
            "HUMMINGBOT_API_URL", 
            "http://localhost:8000"
        ).rstrip('/')
        
        self.username = os.getenv("HUMMINGBOT_API_USERNAME", "hummingbot")
        self.password = os.getenv("HUMMINGBOT_API_PASSWORD", "")
        self.api_key = os.getenv("HUMMINGBOT_API_KEY", "")
        
        # Use API key if available, otherwise basic auth
        if self.api_key:
            self.headers = {"X-API-KEY": self.api_key}
            self.auth = None
        else:
            self.headers = {}
            self.auth = (self.username, self.password) if self.password else None
        
        logger.info(f"HummingbotClient initialized: {self.base_url}")
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to Hummingbot API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/bot-orchestration/status")
            **kwargs: Additional arguments for httpx request
            
        Returns:
            JSON response as dict
            
        Raises:
            httpx.HTTPStatusError: If request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        # Prepare request kwargs
        request_kwargs = {
            "timeout": 30.0,
            **kwargs
        }
        
        # Add authentication
        if self.auth:
            request_kwargs["auth"] = self.auth
        elif self.headers:
            request_kwargs.setdefault("headers", {}).update(self.headers)
        
        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Making {method} request to {url}")
                response = await client.request(method, url, **request_kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get status of all running bots
        
        Returns:
            Dict with bot status information
        """
        return await self._request("GET", "/bot-orchestration/status")
    
    async def get_bot_runs(self) -> Dict[str, Any]:
        """
        Get all bot runs/history
        
        Returns:
            Dict with bot runs information
        """
        return await self._request("GET", "/bot-orchestration/bot-runs")
    
    async def start_bot(
        self, 
        bot_name: str, 
        script_file: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a trading bot
        
        Args:
            bot_name: Name of the bot
            script_file: Name of the script file to use
            config: Optional bot configuration
            
        Returns:
            Dict with bot start result
        """
        payload = {
            "bot_name": bot_name,
            "script_file": script_file,
        }
        if config:
            payload["config"] = config
        
        return await self._request("POST", "/bot-orchestration/start-bot", json=payload)
    
    async def stop_bot(self, bot_name: str) -> Dict[str, Any]:
        """
        Stop a running bot
        
        Args:
            bot_name: Name of the bot to stop
            
        Returns:
            Dict with stop result
        """
        return await self._request("POST", f"/bot-orchestration/{bot_name}/stop")
    
    async def deploy_script(
        self, 
        script_content: str, 
        script_name: str
    ) -> Dict[str, Any]:
        """
        Deploy a v2 strategy script to Hummingbot
        
        Args:
            script_content: Python script content as string
            script_name: Name for the script file
            
        Returns:
            Dict with deployment result
        """
        payload = {
            "script_content": script_content,
            "script_name": script_name
        }
        return await self._request(
            "POST", 
            "/bot-orchestration/deploy-v2-script", 
            json=payload
        )
    
    async def get_bot_history(self, bot_name: str) -> Dict[str, Any]:
        """
        Get trade history for a bot
        
        Args:
            bot_name: Name of the bot
            
        Returns:
            Dict with trade history
        """
        return await self._request("GET", f"/bot-orchestration/{bot_name}/history")
    
    async def health_check(self) -> bool:
        """
        Check if Hummingbot API is accessible
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            await self.get_status()
            return True
        except Exception as e:
            logger.warning(f"Hummingbot API health check failed: {str(e)}")
            return False
