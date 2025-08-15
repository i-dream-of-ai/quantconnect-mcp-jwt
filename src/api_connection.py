from src import __version__

import httpx
from base64 import b64encode
from hashlib import sha256
from time import time
import os
from typing import Optional
from pydantic_core import to_jsonable_python

from auth_middleware import get_current_user
from jwt_auth import QuantConnectCredentials

BASE_URL = 'https://www.quantconnect.com/api/v2'

# Fallback credentials from environment variables (for development/testing)
FALLBACK_USER_ID = os.getenv('QUANTCONNECT_USER_ID')
FALLBACK_API_TOKEN = os.getenv('QUANTCONNECT_API_TOKEN')

def get_qc_credentials() -> QuantConnectCredentials:
    """
    Get QuantConnect credentials from JWT context or environment fallback
    
    Returns:
        QuantConnectCredentials object
        
    Raises:
        ValueError: If no credentials available
    """
    # Try to get credentials from authenticated user context
    current_user = get_current_user()
    if current_user and current_user.qc_credentials:
        return current_user.qc_credentials
    
    # Fallback to environment variables for development/testing
    if FALLBACK_USER_ID and FALLBACK_API_TOKEN:
        return QuantConnectCredentials(
            user_id=FALLBACK_USER_ID,
            api_token=FALLBACK_API_TOKEN,
            organization_id=os.getenv('QUANTCONNECT_ORGANIZATION_ID')
        )
    
    raise ValueError(
        "No QuantConnect credentials available. "
        "Ensure JWT token contains valid credentials or set environment variables for development."
    )

def get_headers(credentials: Optional[QuantConnectCredentials] = None):
    """
    Create QuantConnect API headers with SHA256 authentication
    
    Args:
        credentials: Optional QuantConnect credentials. If None, will get from context.
    
    Returns:
        Dictionary of HTTP headers for QuantConnect API
    """
    if credentials is None:
        credentials = get_qc_credentials()
    
    # Get timestamp
    timestamp = f'{int(time())}'
    time_stamped_token = f'{credentials.api_token}:{timestamp}'.encode('utf-8')
    # Get hashed API token
    hashed_token = sha256(time_stamped_token).hexdigest()
    authentication = f'{credentials.user_id}:{hashed_token}'.encode('utf-8')
    authentication = b64encode(authentication).decode('ascii')
    
    # Create headers dictionary
    headers = {
        'Authorization': f'Basic {authentication}',
        'Timestamp': timestamp,
        'User-Agent': f'LedgAI QuantConnect MCP Server v{__version__}'
    }
    
    # Add organization ID if available
    if credentials.organization_id:
        headers['Organization-Id'] = credentials.organization_id
    
    return headers

async def post(endpoint: str, model: object = None, timeout: float = 30.0):
    """Make an HTTP POST request to the API with proper error handling.
    
    Args:
        endpoint: The API endpoint path (ex: '/projects/create')
        model: Optional Pydantics model for the request.
        timeout: Optional timeout for the request (in seconds).
        
    Returns:
        Response JSON if successful. Otherwise, throws an exception, 
        which is handled by the Server class.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f'{BASE_URL}{endpoint}', 
            headers=get_headers(), 
            json=to_jsonable_python(model, exclude_none=True) if model else {}, 
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
