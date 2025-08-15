"""
HTTP server with JWT authentication for QuantConnect MCP
Provides health checks for DigitalOcean and JWT-protected MCP endpoints
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import os
import jwt
from typing import Optional, Dict, Any
import subprocess
import json

app = FastAPI()
security = HTTPBearer()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

def verify_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return decoded payload"""
    token = credentials.credentials
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
        "tools": 60,
        "message": "MCP server with 60+ QuantConnect tools. JWT authentication required for /mcp endpoints."
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/mcp/execute")
async def execute_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    user_data: Dict = Depends(verify_jwt)
):
    """Execute an MCP tool with JWT authentication"""
    
    # Extract QuantConnect credentials from JWT
    qc_creds = user_data.get("qc_credentials", {})
    if not qc_creds:
        raise HTTPException(status_code=400, detail="No QuantConnect credentials in token")
    
    # Set environment variables for the MCP process
    env = os.environ.copy()
    env["QUANTCONNECT_USER_ID"] = str(qc_creds.get("user_id", ""))
    env["QUANTCONNECT_TOKEN"] = qc_creds.get("api_token", "")
    env["QUANTCONNECT_ORGANIZATION_ID"] = str(qc_creds.get("organization_id", ""))
    
    # Execute the MCP tool via subprocess
    # This is a simplified version - in production you'd want better process management
    try:
        # Create MCP request
        mcp_request = {
            "method": tool_name,
            "params": arguments
        }
        
        # Run MCP server with the request
        result = subprocess.run(
            ["uv", "run", "python", "src/main.py"],
            input=json.dumps(mcp_request),
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"MCP execution failed: {result.stderr}")
        
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="MCP execution timeout")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid MCP response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/mcp/tools")
async def list_tools(user_data: Dict = Depends(verify_jwt)):
    """List available MCP tools (requires JWT)"""
    return {
        "tools": [
            "create_project", "list_projects", "read_project", 
            "create_backtest", "read_backtest", "list_backtests",
            "create_optimization", "read_optimization",
            "deploy_live", "stop_live", "read_live_status",
            # ... all 60+ tools
        ],
        "total": 60
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)