#!/usr/bin/env python3
"""Create a test JWT token for the MCP server"""

import jwt
import time

# Configuration
JWT_SECRET_KEY = "dev-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# Create token payload
payload = {
    "iss": "ledgai",
    "aud": "quantconnect-mcp",
    "sub": "test-user",
    "iat": time.time(),
    "exp": time.time() + 86400,  # 24 hours
    "qc_credentials": {
        "user_id": "406922",
        "api_token": "428ff4953fc81908d3816549d6d65c8910032b111159b7cdb5b03c829713724d",
        "organization_id": "c6880779be8442f9147fd531ddc7bc75"
    }
}

# Generate token
token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
print(f"JWT Token:\n{token}")
print(f"\nTest with:")
print(f'curl -X POST https://quantconnect-mcp-jwt-e2gs4.ondigitalocean.app/mcp \\')
print(f'  -H "Content-Type: application/json" \\')
print(f'  -H "Authorization: Bearer {token}" \\')
print(f'  -d \'{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{}}}}\'')