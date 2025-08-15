"""
Simple HTTP health check server for DigitalOcean App Platform
The MCP server runs via stdio, but DigitalOcean needs an HTTP endpoint for health checks
"""

from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
async def root():
    return {
        "service": "ledgai-quantconnect-mcp",
        "status": "healthy",
        "version": "1.0.0",
        "tools": 60,
        "message": "MCP server with 60+ QuantConnect tools. Connect via MCP protocol."
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)