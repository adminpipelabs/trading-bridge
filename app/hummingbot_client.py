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
        # Get base URL - required in production
        # Handle Railway issue where variable names may have leading/trailing spaces
        base_url = os.getenv("HUMMINGBOT_API_URL", "") or os.getenv(" HUMMINGBOT_API_URL", "")
        self.base_url = base_url.rstrip('/')
        
        # Validate configuration
        if not self.base_url:
            error_msg = (
                "HUMMINGBOT_API_URL environment variable is not set. "
                "Required for production deployment. "
                "Set to internal Railway service URL (e.g., http://hummingbot-api:8000)"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Warn if using localhost in production
        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            logger.warning(
                f"HUMMINGBOT_API_URL is set to localhost ({self.base_url}). "
                "This will not work in Railway production. "
                "Use internal service name (e.g., http://hummingbot-api:8000)"
            )
        
        # Handle Railway issue where variable names may have leading/trailing spaces
        self.username = (os.getenv("HUMMINGBOT_API_USERNAME", "") or os.getenv(" HUMMINGBOT_API_USERNAME", "") or "hummingbot").strip()
        password_raw = os.getenv("HUMMINGBOT_API_PASSWORD", "") or os.getenv(" HUMMINGBOT_API_PASSWORD", "")
        self.password = password_raw.strip() if password_raw else ""
        self.api_key = (os.getenv("HUMMINGBOT_API_KEY", "") or os.getenv(" HUMMINGBOT_API_KEY", "")).strip()
        
        # Debug logging
        logger.info(f"Auth config - Username: '{self.username}', Password set: {bool(self.password)}, Password length: {len(self.password) if self.password else 0}, Password value: '{self.password[:1]}...' (masked)")
        
        # Validate authentication
        if not self.api_key and not self.password:
            error_msg = (
                "Hummingbot API authentication not configured. "
                "Set either HUMMINGBOT_API_KEY or HUMMINGBOT_API_PASSWORD."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Use API key if available, otherwise basic auth
        # Always include ngrok header to bypass free tier warning page
        ngrok_header = {"ngrok-skip-browser-warning": "true"}
        
        if self.api_key:
            self.headers = {"X-API-KEY": self.api_key, **ngrok_header}
            self.auth = None
        else:
            # Manually construct Authorization header to ensure ngrok header is included
            import base64
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.headers = {
                "ngrok-skip-browser-warning": "true",
                "Authorization": f"Basic {encoded_credentials}"
            }
            self.auth = None  # Don't use httpx.BasicAuth, we're handling it manually
        
        logger.info(f"HummingbotClient initialized: {self.base_url} (auth: {'API_KEY' if self.api_key else 'BASIC'}, username: '{self.username}')")
    
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
        
        # Always include headers (for ngrok bypass, auth, and API key if used)
        if self.headers:
            request_kwargs.setdefault("headers", {}).update(self.headers)
        
        # Add authentication if using httpx.BasicAuth (for API key auth, it's in headers)
        if self.auth:
            request_kwargs["auth"] = self.auth
        
        # Debug: Log headers being sent (mask Authorization header)
        headers_to_log = request_kwargs.get("headers", {}).copy()
        if "Authorization" in headers_to_log:
            headers_to_log["Authorization"] = "BasicAuth (masked)"
        logger.info(f"Making {method} request to {url} with headers: {list(headers_to_log.keys())}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **request_kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            # Log full error details for debugging
            status_code = e.response.status_code
            response_text = e.response.text
            response_headers = dict(e.response.headers)
            
            logger.error(f"HTTP error {status_code}")
            logger.error(f"Response headers: {response_headers}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            logger.error(f"Response text (full length): {len(response_text)} chars")
            
            # Try to parse as JSON
            try:
                error_json = e.response.json()
                logger.error(f"Response JSON: {error_json}")
                error_msg = f"HTTP error {status_code}: {error_json}"
            except:
                logger.error(f"Response is not JSON, raw text: {response_text}")
                error_msg = f"HTTP error {status_code}: {response_text}"
            
            raise Exception(error_msg)
        except httpx.ConnectError as e:
            error_msg = f"Connection failed to {url}: {str(e)}. Check service name and that Hummingbot API is running."
            logger.error(error_msg)
            raise Exception(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Request error to {url}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
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
        script_name: str,
        instance_name: Optional[str] = None,
        credentials_profile: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy a v2 strategy script to Hummingbot
        
        Args:
            script_content: Python script content as string
            script_name: Name for the script file
            instance_name: Bot instance name (defaults to script_name without .py)
            credentials_profile: Credentials profile name (defaults to instance_name)
            
        Returns:
            Dict with deployment result
        """
        # Use instance_name from script_name if not provided
        if not instance_name:
            instance_name = script_name.replace("_strategy.py", "").replace(".py", "")
        
        # Use instance_name as credentials_profile if not provided
        if not credentials_profile:
            credentials_profile = instance_name
        
        payload = {
            "script_content": script_content,
            "script_name": script_name,
            "instance_name": instance_name,
            "credentials_profile": credentials_profile
        }
        
        # Log payload details for debugging (mask script content if too long)
        logger.info(f"Deploying script: script_name={script_name}, instance_name={instance_name}, credentials_profile={credentials_profile}")
        logger.info(f"Script content length: {len(script_content)} chars")
        logger.info(f"Script content preview: {script_content[:200]}...")
        
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
