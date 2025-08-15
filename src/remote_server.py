"""
Remote MCP Server for DigitalOcean deployment
Serves MCP protocol over HTTP with OAuth/JWT authentication at transport layer
Based on MCP remote server standards (2025)
"""

import os
import sys
import json
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import jwt
from typing import Optional, Dict, Any

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import MCP server
from main import mcp

app = FastAPI()
security = HTTPBearer(auto_error=False)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"

def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """Verify JWT token if auth is enabled"""
    if not ENABLE_AUTH:
        return {"authenticated": False}
    
    if not credentials:
        raise HTTPException(
            status_code=401, 
            detail="Authorization required",
            headers={"WWW-Authenticate": 'Bearer realm="MCP Server"'}
        )
    
    try:
        print(f"DEBUG: Attempting to decode token with secret: {JWT_SECRET_KEY[:10]}...")
        print(f"DEBUG: Token first 50 chars: {credentials.credentials[:50]}...")
        
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        print(f"DEBUG: Token decoded successfully: {payload.get('sub', 'no-sub')}")
        
        # Set QuantConnect credentials from token
        if "qc_credentials" in payload:
            qc = payload["qc_credentials"]
            os.environ["QUANTCONNECT_USER_ID"] = str(qc.get("user_id", ""))
            os.environ["QUANTCONNECT_TOKEN"] = qc.get("api_token", "")
            os.environ["QUANTCONNECT_ORGANIZATION_ID"] = str(qc.get("organization_id", ""))
        
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"DEBUG: Token expired: {e}")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print(f"DEBUG: Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    """Root endpoint for service discovery"""
    return {
        "service": "quantconnect-mcp",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "auth_required": ENABLE_AUTH,
        "tools_count": 60
    }

@app.get("/health")
async def health():
    """Health check for DigitalOcean"""
    return {"status": "ok"}

@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    auth: Optional[Dict] = Depends(verify_token)
):
    """
    Main MCP endpoint - handles JSON-RPC 2.0 requests
    Authentication happens at transport layer (HTTP), not MCP protocol
    """
    
    # Get JSON-RPC request
    try:
        body = await request.json()
    except:
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
        )
    
    # Process MCP request
    # The actual MCP server (FastMCP) handles the protocol
    # We just need to route the request to it
    
    # For now, handle basic methods manually
    # In production, this would integrate with FastMCP's request handler
    method = body.get("method", "")
    params = body.get("params", {})
    request_id = body.get("id")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": None,
                    "resources": None
                },
                "serverInfo": {
                    "name": "quantconnect-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        # Get all registered tools from MCP server
        # This is simplified - would need proper integration
        tools = []
        for name in ["create_project", "list_projects", "create_backtest", 
                    "read_backtest", "list_backtests", "create_optimization",
                    "read_optimization", "deploy_live", "stop_live"]:
            tools.append({
                "name": name,
                "description": f"QuantConnect {name.replace('_', ' ')} operation",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            })
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }
    
    elif method.startswith("tools/call"):
        # Extract tool name from method
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        
        # Here we would call the actual MCP tool
        # For now, return a mock response
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": f"Executed {tool_name} with args: {tool_args}"
                    }
                ]
            }
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

# OAuth 2.0 metadata endpoints (for MCP clients to discover auth)
@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata():
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    base_url = os.getenv("BASE_URL", "https://ledgai-quantconnect-mcp.ondigitalocean.app")
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "service_documentation": f"{base_url}/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)