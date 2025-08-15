# LedgAI QuantConnect MCP Server with JWT Authentication

## Overview

This is an enhanced version of the official QuantConnect MCP Server that adds:

- 🔐 **JWT-based Multi-tenant Authentication** 
- 🎯 **Granular Scope-based Authorization**
- 👥 **Per-user QuantConnect Credentials**
- 🛡️ **Enterprise-grade Security**
- 📊 **Full 60+ QuantConnect API Tools**

## Features

### Authentication & Authorization
- JWT token validation with configurable secrets
- 15+ granular scopes for fine-grained access control
- Multi-tenant support with per-user QuantConnect credentials
- Secure credential storage in JWT payload
- Development mode with environment variable fallback

### Security Features
- SHA-256 token hashing
- Configurable token expiration
- Request context isolation
- Comprehensive audit logging
- Non-root Docker container execution

### API Coverage
All 60+ official QuantConnect API tools organized by category:
- **Account Management** (1 tool)
- **Project Management** (5 tools) 
- **File Management** (5 tools)
- **Compilation** (2 tools)
- **Backtesting** (8 tools)
- **Optimization** (7 tools)
- **Live Trading** (15 tools)
- **Object Store** (6 tools)
- **AI Assistance** (6 tools)
- **Collaboration** (4 tools)
- **Administrative** (2 tools)

## Quick Start

### 1. Environment Setup

```bash
# Required for JWT authentication
export JWT_SECRET_KEY="your-secret-key-here"

# QuantConnect credentials (for development/fallback)
export QUANTCONNECT_USER_ID="your-user-id"
export QUANTCONNECT_API_TOKEN="your-api-token"
export QUANTCONNECT_ORGANIZATION_ID="your-org-id"

# Optional configuration
export ENABLE_AUTH="true"  # Set to "false" to disable auth
export MCP_TRANSPORT="stdio"  # or "http"
```

### 2. Build and Run

```bash
# Build the JWT-enhanced Docker image
docker build -f Dockerfile.jwt -t ledgai/quantconnect-mcp-jwt .

# Run with environment variables
docker run -i --rm \
  -e JWT_SECRET_KEY="$JWT_SECRET_KEY" \
  -e QUANTCONNECT_USER_ID="$QUANTCONNECT_USER_ID" \
  -e QUANTCONNECT_API_TOKEN="$QUANTCONNECT_API_TOKEN" \
  -e QUANTCONNECT_ORGANIZATION_ID="$QUANTCONNECT_ORGANIZATION_ID" \
  ledgai/quantconnect-mcp-jwt
```

### 3. Create Development Token

```bash
# Generate a development JWT token
python src/main_jwt.py --create-dev-token
```

## JWT Token Structure

### Required Claims

```json
{
  "iss": "ledgai",
  "aud": "quantconnect-mcp", 
  "sub": "user-identifier",
  "iat": 1640995200,
  "exp": 1641081600,
  "scopes": [
    "qc:projects:read",
    "qc:projects:write",
    "qc:backtests:read"
  ],
  "qc_credentials": {
    "user_id": "406922",
    "api_token": "your-quantconnect-api-token",
    "organization_id": "your-org-id"
  }
}
```

## Scope Definitions

### Project Management
- `qc:projects:read` - Read project details and lists
- `qc:projects:write` - Create and update projects  
- `qc:projects:delete` - Delete projects

### File Management
- `qc:files:read` - Read project files
- `qc:files:write` - Create and update files
- `qc:files:delete` - Delete files

### Backtesting
- `qc:backtests:read` - Read backtest results and charts
- `qc:backtests:write` - Create and update backtests
- `qc:backtests:delete` - Delete backtests

### Live Trading
- `qc:live:read` - Read live algorithm status
- `qc:live:write` - Create live algorithms
- `qc:live:execute` - Control live algorithms (stop, liquidate)
- `qc:live:delete` - Delete live algorithms

### Complete Scope List
```
qc:account:read
qc:projects:read, qc:projects:write, qc:projects:delete
qc:files:read, qc:files:write, qc:files:delete
qc:compile:execute
qc:backtests:read, qc:backtests:write, qc:backtests:delete
qc:optimizations:read, qc:optimizations:write, qc:optimizations:delete
qc:live:read, qc:live:write, qc:live:execute, qc:live:delete
qc:objects:read, qc:objects:write, qc:objects:delete
qc:ai:read, qc:ai:execute
qc:collaboration:read, qc:collaboration:write, qc:collaboration:delete
qc:admin:read, qc:admin:write
```

## Predefined Scope Groups

### Readonly Access
```json
{
  "scopes": [
    "qc:account:read",
    "qc:projects:read", 
    "qc:files:read",
    "qc:backtests:read",
    "qc:optimizations:read",
    "qc:live:read",
    "qc:objects:read",
    "qc:ai:read"
  ]
}
```

### Trader Access
```json
{
  "scopes": [
    "qc:account:read",
    "qc:projects:read", "qc:projects:write",
    "qc:files:read", "qc:files:write", 
    "qc:compile:execute",
    "qc:backtests:read", "qc:backtests:write",
    "qc:optimizations:read", "qc:optimizations:write",
    "qc:live:read", "qc:live:write", "qc:live:execute",
    "qc:objects:read", "qc:objects:write",
    "qc:ai:read", "qc:ai:execute"
  ]
}
```

### Admin Access
All scopes (complete access)

## Integration with Claude Desktop

### Configuration with JWT Auth

```json
{
  "mcpServers": {
    "ledgai-quantconnect": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "JWT_SECRET_KEY",
        "-e", "QUANTCONNECT_USER_ID", 
        "-e", "QUANTCONNECT_API_TOKEN",
        "-e", "QUANTCONNECT_ORGANIZATION_ID",
        "--name", "ledgai-quantconnect-mcp",
        "ledgai/quantconnect-mcp-jwt"
      ],
      "env": {
        "JWT_SECRET_KEY": "your-jwt-secret",
        "QUANTCONNECT_USER_ID": "your-user-id",
        "QUANTCONNECT_API_TOKEN": "your-api-token",
        "QUANTCONNECT_ORGANIZATION_ID": "your-org-id"
      }
    }
  }
}
```

## API Usage Examples

### Authentication Header
All requests must include a valid JWT token:

```
Authorization: Bearer <your-jwt-token>
```

### Available Tools

#### Health Check
```python
# Check server health and authentication status
await health_check()
```

#### Project Management
```python
# List all projects (requires qc:projects:read)
await list_projects()

# Create new project (requires qc:projects:write)
await create_project({
  "name": "My Strategy",
  "language": "Py",
  "description": "Trading strategy"
})
```

#### Backtesting
```python
# Create backtest (requires qc:backtests:write)
await create_backtest({
  "projectId": 12345,
  "compileId": "abc123", 
  "backtestName": "Test Run"
})

# Read backtest results (requires qc:backtests:read)
await read_backtest({
  "projectId": 12345,
  "backtestId": "def456"
})
```

## Security Considerations

### Production Deployment
1. **Use strong JWT secrets** (256-bit minimum)
2. **Set appropriate token expiration** (24 hours recommended)
3. **Enable comprehensive logging**
4. **Use HTTPS for all communications**
5. **Regularly rotate JWT secrets**
6. **Monitor for suspicious activity**

### Token Management
- Store JWT secret securely (AWS Secrets Manager, etc.)
- Implement token refresh mechanism
- Use short-lived tokens with refresh tokens
- Implement proper token revocation

### Network Security
- Use TLS 1.3 for all communications
- Implement rate limiting
- Use private networks when possible
- Regular security audits

## Development & Testing

### Running Tests
```bash
# Install test dependencies
uv sync --dev

# Run test suite
uv run pytest tests/
```

### Local Development
```bash
# Disable authentication for local development
export ENABLE_AUTH="false"

# Run server locally
python src/main_jwt.py
```

### Creating Test Tokens
```bash
# Create development token with admin scopes
python src/main_jwt.py --create-dev-token
```

## Production Deployment

### Docker Compose Example
```yaml
version: '3.8'
services:
  ledgai-quantconnect-mcp:
    build:
      context: .
      dockerfile: Dockerfile.jwt
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENABLE_AUTH=true
      - MCP_TRANSPORT=stdio
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ledgai-quantconnect-mcp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ledgai-quantconnect-mcp
  template:
    metadata:
      labels:
        app: ledgai-quantconnect-mcp
    spec:
      containers:
      - name: mcp-server
        image: ledgai/quantconnect-mcp-jwt:latest
        env:
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret-key
        - name: ENABLE_AUTH
          value: "true"
```

## Monitoring & Observability

### Health Checks
The server provides a health check endpoint that validates:
- Server status
- Authentication system status  
- QuantConnect API connectivity
- Available tools count

### Logging
Comprehensive logging includes:
- Authentication attempts (success/failure)
- Authorization checks
- QuantConnect API calls
- Error tracking
- Performance metrics

### Metrics
Key metrics to monitor:
- Request latency
- Authentication failure rate
- Tool usage patterns
- Error rates
- Active user sessions

## Support & Contributing

### Issues
Report issues at: [Your GitHub Repository]

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

### License
This enhanced version maintains the original Apache 2.0 license from QuantConnect.

---

*LedgAI QuantConnect MCP Server with JWT Authentication - Enterprise-grade algorithmic trading platform integration*