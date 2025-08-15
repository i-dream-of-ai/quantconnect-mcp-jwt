"""
MCP Server with SSE transport for DigitalOcean deployment
Serves MCP protocol over Server-Sent Events so Claude can connect directly
"""

import os
import sys
import asyncio
import json
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import uvicorn
import jwt
from typing import Optional, AsyncGenerator

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the MCP server setup
from main import mcp, registration_functions

app = FastAPI()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

def verify_jwt_from_header(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        # Allow no auth if ENABLE_AUTH is false
        if os.getenv("ENABLE_AUTH", "true").lower() != "true":
            return {}
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/")
async def root():
    return {
        "service": "ledgai-quantconnect-mcp",
        "status": "healthy",
        "version": "1.0.0",
        "transport": "sse",
        "tools": 60,
        "message": "MCP server ready for Claude connection via SSE at /mcp/sse"
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

async def mcp_message_stream(request: Request, user_data: dict) -> AsyncGenerator:
    """Stream MCP messages over SSE"""
    
    # Set QuantConnect credentials from JWT if available
    if user_data and "qc_credentials" in user_data:
        qc_creds = user_data["qc_credentials"]
        os.environ["QUANTCONNECT_USER_ID"] = str(qc_creds.get("user_id", ""))
        os.environ["QUANTCONNECT_TOKEN"] = qc_creds.get("api_token", "")
        os.environ["QUANTCONNECT_ORGANIZATION_ID"] = str(qc_creds.get("organization_id", ""))
    
    # Send initial connection message
    yield {
        "event": "message",
        "data": json.dumps({
            "jsonrpc": "2.0",
            "method": "connection.ready",
            "params": {
                "server": "quantconnect-mcp",
                "version": "1.0.0",
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                }
            }
        })
    }
    
    # Process incoming messages from client
    async for message in request.stream():
        try:
            data = json.loads(message)
            
            # Handle MCP requests
            if "method" in data:
                if data["method"] == "tools/list":
                    # Return list of all tools
                    tools_list = []
                    # This is simplified - in reality we'd introspect the registered tools
                    for func_name in ["create_project", "list_projects", "create_backtest", 
                                     "read_backtest", "deploy_live", "read_optimization"]:
                        tools_list.append({
                            "name": func_name,
                            "description": f"QuantConnect {func_name.replace('_', ' ')} tool"
                        })
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"tools": tools_list}
                    }
                    yield {"event": "message", "data": json.dumps(response)}
                
                elif data["method"].startswith("tools/call/"):
                    # Execute the tool
                    tool_name = data["method"].replace("tools/call/", "")
                    params = data.get("params", {})
                    
                    # Execute via MCP (this needs proper implementation)
                    # For now, return a mock response
                    response = {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Executed {tool_name} with params: {params}"
                                }
                            ]
                        }
                    }
                    yield {"event": "message", "data": json.dumps(response)}
                    
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            yield {"event": "message", "data": json.dumps(error_response)}
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            yield {"event": "message", "data": json.dumps(error_response)}
    
        # Check if client disconnected
        if await request.is_disconnected():
            break

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    """SSE endpoint for MCP protocol - Claude connects here"""
    user_data = {}
    if os.getenv("ENABLE_AUTH", "true").lower() == "true":
        user_data = verify_jwt_from_header(authorization)
    
    return EventSourceResponse(mcp_message_stream(request, user_data))

@app.post("/mcp")
async def mcp_stdio_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    """Alternative JSON-RPC endpoint for MCP protocol"""
    user_data = {}
    if os.getenv("ENABLE_AUTH", "true").lower() == "true":
        user_data = verify_jwt_from_header(authorization)
    
    # Set QuantConnect credentials from JWT
    if user_data and "qc_credentials" in user_data:
        qc_creds = user_data["qc_credentials"]
        os.environ["QUANTCONNECT_USER_ID"] = str(qc_creds.get("user_id", ""))
        os.environ["QUANTCONNECT_TOKEN"] = qc_creds.get("api_token", "")
        os.environ["QUANTCONNECT_ORGANIZATION_ID"] = str(qc_creds.get("organization_id", ""))
    
    # Get the JSON-RPC request
    body = await request.json()
    
    # This is a simplified handler - needs proper MCP processing
    if body.get("method") == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "tools": [
                    {"name": "create_project", "description": "Create a QuantConnect project"},
                    {"name": "list_projects", "description": "List QuantConnect projects"},
                    # ... add all 60+ tools
                ]
            }
        }
    
    return {"jsonrpc": "2.0", "id": body.get("id"), "result": {}}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)