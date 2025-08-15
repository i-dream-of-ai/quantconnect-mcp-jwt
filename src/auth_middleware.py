"""
LedgAI QuantConnect MCP Server - Authentication Middleware
JWT authentication middleware for MCP tool protection
"""

import os
import logging
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from contextvars import ContextVar

from jwt_auth import validate_authorization, AuthenticatedUser, JWTAuthError, InsufficientScopesError
from scopes import get_tool_scopes, validate_scopes, Scope

logger = logging.getLogger(__name__)

# Context variable to store authenticated user across request
current_user: ContextVar[Optional[AuthenticatedUser]] = ContextVar('current_user', default=None)

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization/permission related errors"""
    pass

def get_current_user() -> Optional[AuthenticatedUser]:
    """Get currently authenticated user from context"""
    return current_user.get()

def require_auth(required_scopes: Optional[List[Scope]] = None):
    """
    Decorator to require JWT authentication for MCP tools
    
    Args:
        required_scopes: Optional list of required scopes. If None, will use tool name to lookup scopes
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get authorization header from MCP context/request
            # Note: This will need to be adapted based on how MCP provides request context
            auth_header = get_authorization_header()
            
            if not auth_header:
                logger.warning(f"Unauthorized access attempt to {func.__name__}")
                raise AuthenticationError("Authorization header required")
            
            try:
                # Validate JWT token
                user = validate_authorization(auth_header)
                
                # Determine required scopes
                scopes_to_check = required_scopes
                if scopes_to_check is None:
                    scopes_to_check = get_tool_scopes(func.__name__)
                
                # Check if user has required scopes
                if scopes_to_check and not validate_scopes(user.scopes, scopes_to_check):
                    required_scope_names = [scope.value for scope in scopes_to_check]
                    logger.warning(
                        f"User {user.user_id} lacks required scopes for {func.__name__}. "
                        f"Required: {required_scope_names}, Has: {list(user.scopes)}"
                    )
                    raise AuthorizationError(
                        f"Insufficient permissions. Required scopes: {required_scope_names}"
                    )
                
                # Set user in context for use by tool
                current_user.set(user)
                
                logger.info(f"Authenticated user {user.user_id} calling {func.__name__}")
                
                # Call the original function
                return await func(*args, **kwargs)
                
            except JWTAuthError as e:
                logger.warning(f"Authentication failed for {func.__name__}: {str(e)}")
                raise AuthenticationError(f"Authentication failed: {str(e)}")
            except InsufficientScopesError as e:
                logger.warning(f"Authorization failed for {func.__name__}: {str(e)}")
                raise AuthorizationError(str(e))
            except Exception as e:
                logger.error(f"Unexpected error in auth middleware for {func.__name__}: {str(e)}")
                raise
                
        return wrapper
    return decorator

def get_authorization_header() -> Optional[str]:
    """
    Extract Authorization header from MCP request context
    
    TODO: This needs to be implemented based on how MCP server provides request context.
    Different MCP frameworks handle this differently.
    """
    # For now, return None - this will be updated when we integrate with the MCP server
    # The actual implementation will depend on how the MCP library provides access to headers
    return None

class MCPAuthMiddleware:
    """
    Authentication middleware for MCP servers
    
    This class will be integrated with the MCP server to provide automatic JWT authentication
    """
    
    def __init__(self, enable_auth: bool = True):
        """
        Initialize authentication middleware
        
        Args:
            enable_auth: Whether to enable authentication (can be disabled for development)
        """
        self.enable_auth = enable_auth
        
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming MCP request for authentication
        
        Args:
            request: MCP request object
            
        Returns:
            Modified request object with authentication context
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If authorization fails
        """
        if not self.enable_auth:
            logger.debug("Authentication disabled, skipping auth check")
            return request
            
        # Extract method name from MCP request
        method = request.get('method', '')
        
        # Skip authentication for certain methods (like server info)
        if method in ['initialize', 'notifications/initialized', 'ping']:
            return request
            
        # Extract authorization header
        headers = request.get('headers', {})
        auth_header = headers.get('authorization') or headers.get('Authorization')
        
        if not auth_header:
            raise AuthenticationError("Authorization header required")
            
        try:
            # Validate JWT token
            user = validate_authorization(auth_header)
            
            # Add user context to request
            request['_auth_user'] = user
            current_user.set(user)
            
            logger.info(f"Authenticated user {user.user_id} for method {method}")
            
            return request
            
        except JWTAuthError as e:
            logger.warning(f"Authentication failed for method {method}: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
            
    def check_tool_authorization(self, tool_name: str, user: AuthenticatedUser) -> None:
        """
        Check if user is authorized to call a specific tool
        
        Args:
            tool_name: Name of the MCP tool being called
            user: Authenticated user
            
        Raises:
            AuthorizationError: If user lacks required permissions
        """
        required_scopes = get_tool_scopes(tool_name)
        
        if required_scopes and not validate_scopes(user.scopes, required_scopes):
            required_scope_names = [scope.value for scope in required_scopes]
            raise AuthorizationError(
                f"Insufficient permissions for {tool_name}. "
                f"Required scopes: {required_scope_names}"
            )

# Global middleware instance
_middleware: Optional[MCPAuthMiddleware] = None

def get_auth_middleware() -> MCPAuthMiddleware:
    """Get or create global authentication middleware instance"""
    global _middleware
    if _middleware is None:
        enable_auth = os.getenv('ENABLE_AUTH', 'true').lower() == 'true'
        _middleware = MCPAuthMiddleware(enable_auth=enable_auth)
    return _middleware