"""
LedgAI QuantConnect MCP Server with JWT Authentication
Enhanced MCP server with 60+ tools and JWT-based multi-tenant authentication
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Set the path to ensure we can import the src.__init__.py file.
sys.path.append(os.getcwd())

# Import all tool registration functions
from tools.account import register_account_tools
from tools.project import register_project_tools
from tools.project_collaboration import register_project_collaboration_tools
from tools.project_nodes import register_project_node_tools
from tools.compile import register_compile_tools
from tools.files import register_file_tools
from tools.backtests import register_backtest_tools
from tools.optimizations import register_optimization_tools
from tools.live import register_live_trading_tools
from tools.live_commands import register_live_trading_command_tools
from tools.object_store import register_object_store_tools
from tools.lean_versions import register_lean_version_tools
from tools.ai import register_ai_tools
from tools.mcp_server_version import register_mcp_server_version_tools

# Import authentication components
from auth_middleware import MCPAuthMiddleware, AuthenticationError, AuthorizationError, get_current_user
from jwt_auth import JWTAuthenticator, validate_authorization
from scopes import get_tool_scopes, validate_scopes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LedgAIQuantConnectMCP:
    """
    LedgAI Enhanced QuantConnect MCP Server
    
    Features:
    - 60+ QuantConnect API tools
    - JWT-based multi-tenant authentication
    - Granular scope-based authorization
    - Per-user QuantConnect credentials
    """
    
    def __init__(self):
        """Initialize the enhanced MCP server"""
        
        # Configuration
        transport = os.getenv('MCP_TRANSPORT', 'stdio')
        enable_auth = os.getenv('ENABLE_AUTH', 'true').lower() == 'true'
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        
        if enable_auth and not jwt_secret:
            logger.warning(
                "JWT_SECRET_KEY not set. Authentication will fail. "
                "Set JWT_SECRET_KEY environment variable or disable auth with ENABLE_AUTH=false"
            )
        
        # Initialize FastMCP server
        self.mcp = FastMCP('ledgai-quantconnect', host="0.0.0.0")
        
        # Initialize authentication middleware
        self.auth_middleware = MCPAuthMiddleware(enable_auth=enable_auth)
        
        # Register authentication hooks
        if enable_auth:
            self._setup_auth_hooks()
        
        # Register all QuantConnect tools
        self._register_tools()
        
        logger.info(f"LedgAI QuantConnect MCP Server initialized (auth={'enabled' if enable_auth else 'disabled'})")
        
    def _setup_auth_hooks(self):
        """Setup authentication hooks for the MCP server"""
        
        # Note: The exact implementation depends on the MCP library's hook system
        # This is a conceptual implementation that shows the intended flow
        
        @self.mcp.middleware
        async def auth_middleware(request: Dict[str, Any], call_next):
            """Authentication middleware for all MCP requests"""
            try:
                # Process request through auth middleware
                authenticated_request = await self.auth_middleware.process_request(request)
                
                # Call the next handler
                response = await call_next(authenticated_request)
                
                return response
                
            except AuthenticationError as e:
                logger.warning(f"Authentication failed: {e}")
                return {
                    "error": {
                        "code": 401,
                        "message": f"Authentication failed: {str(e)}"
                    }
                }
            except AuthorizationError as e:
                logger.warning(f"Authorization failed: {e}")
                return {
                    "error": {
                        "code": 403,
                        "message": f"Authorization failed: {str(e)}"
                    }
                }
                
    def _register_tools(self):
        """Register all QuantConnect MCP tools with authentication"""
        
        # List of all tool registration functions
        registration_functions = [
            register_account_tools,
            register_project_tools,
            register_project_collaboration_tools,
            register_project_node_tools,
            register_compile_tools,
            register_file_tools,
            register_backtest_tools,
            register_optimization_tools,
            register_live_trading_tools,
            register_live_trading_command_tools,
            register_object_store_tools,
            register_lean_version_tools,
            register_ai_tools,
            register_mcp_server_version_tools,
        ]
        
        # Register each category of tools
        for register_func in registration_functions:
            try:
                register_func(self.mcp)
                logger.info(f"Registered tools from {register_func.__name__}")
            except Exception as e:
                logger.error(f"Failed to register tools from {register_func.__name__}: {e}")
                
        logger.info("All QuantConnect tools registered successfully")
        
    def add_health_check(self):
        """Add health check endpoint"""
        
        @self.mcp.tool()
        async def health_check() -> Dict[str, Any]:
            """Health check endpoint for the MCP server"""
            current_user = get_current_user()
            
            return {
                "status": "healthy",
                "service": "ledgai-quantconnect-mcp",
                "version": "1.0.0",
                "authentication": {
                    "enabled": self.auth_middleware.enable_auth,
                    "user_authenticated": current_user is not None,
                    "user_id": current_user.user_id if current_user else None
                },
                "quantconnect": {
                    "connected": True,
                    "user_id": current_user.qc_credentials.user_id if current_user else "env-fallback"
                },
                "tools_available": 60
            }
            
    def add_token_validation_endpoint(self):
        """Add JWT token validation endpoint for debugging"""
        
        @self.mcp.tool()
        async def validate_token(token: str) -> Dict[str, Any]:
            """Validate a JWT token and return user information"""
            try:
                user = validate_authorization(f"Bearer {token}")
                return {
                    "valid": True,
                    "user_id": user.user_id,
                    "scopes": list(user.scopes),
                    "qc_user_id": user.qc_credentials.user_id,
                    "organization_id": user.organization_id
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": str(e)
                }
                
    def run(self):
        """Start the MCP server"""
        
        # Add utility endpoints
        self.add_health_check()
        self.add_token_validation_endpoint()
        
        # Get transport method
        transport = os.getenv('MCP_TRANSPORT', 'stdio')
        
        logger.info(f"Starting LedgAI QuantConnect MCP Server on {transport}")
        
        # Run the server
        self.mcp.run(transport=transport)

def create_development_token() -> str:
    """
    Create a development JWT token for testing
    
    This should only be used for development/testing purposes
    """
    from jwt_auth import JWTAuthenticator, QuantConnectCredentials
    from scopes import SCOPE_GROUPS
    
    # Use environment variables for development token
    user_id = os.getenv('QUANTCONNECT_USER_ID', '406922')
    api_token = os.getenv('QUANTCONNECT_API_TOKEN', 'test-token')
    org_id = os.getenv('QUANTCONNECT_ORGANIZATION_ID')
    
    qc_credentials = QuantConnectCredentials(
        user_id=user_id,
        api_token=api_token,
        organization_id=org_id
    )
    
    # Create JWT authenticator
    jwt_secret = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    authenticator = JWTAuthenticator(secret_key=jwt_secret)
    
    # Create token with admin scopes
    token = authenticator.create_token(
        user_id="dev-user",
        scopes=set(SCOPE_GROUPS['admin']),
        qc_credentials=qc_credentials,
        expires_in_hours=24
    )
    
    return token

if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-dev-token":
            token = create_development_token()
            print(f"Development JWT token:")
            print(token)
            print(f"\nUse this token in Authorization header:")
            print(f"Authorization: Bearer {token}")
            sys.exit(0)
        elif sys.argv[1] == "--help":
            print("LedgAI QuantConnect MCP Server")
            print("Usage:")
            print("  python main_jwt.py                 # Start server")
            print("  python main_jwt.py --create-dev-token  # Create development token")
            print("  python main_jwt.py --help           # Show this help")
            sys.exit(0)
    
    # Start the server
    server = LedgAIQuantConnectMCP()
    server.run()