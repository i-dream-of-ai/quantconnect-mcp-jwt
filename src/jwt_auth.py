"""
LedgAI QuantConnect MCP Server - JWT Authentication
Multi-tenant JWT authentication with QuantConnect credentials
"""

import os
import jwt
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timezone
from dataclasses import dataclass
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)

@dataclass
class QuantConnectCredentials:
    """QuantConnect API credentials extracted from JWT"""
    user_id: str
    api_token: str
    organization_id: Optional[str] = None

@dataclass
class AuthenticatedUser:
    """Authenticated user information from JWT"""
    user_id: str
    scopes: Set[str]
    qc_credentials: QuantConnectCredentials
    organization_id: Optional[str] = None
    
class JWTAuthError(Exception):
    """JWT Authentication related errors"""
    pass

class InsufficientScopesError(JWTAuthError):
    """Raised when user doesn't have required scopes"""
    pass

class JWTAuthenticator:
    """
    JWT token validator for LedgAI QuantConnect MCP Server
    
    Validates JWT tokens containing user scopes and QuantConnect credentials
    """
    
    def __init__(
        self, 
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        issuer: str = "ledgai",
        audience: str = "quantconnect-mcp"
    ):
        """
        Initialize JWT authenticator
        
        Args:
            secret_key: JWT signing secret (from environment if not provided)
            algorithm: JWT signing algorithm
            issuer: Expected token issuer
            audience: Expected token audience
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY') or 'dev-secret-key-change-in-production'
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable or secret_key parameter required")
            
        self.algorithm = algorithm
        self.issuer = issuer
        self.audience = audience
        
    def validate_token(self, token: str) -> AuthenticatedUser:
        """
        Validate JWT token and extract user information
        
        Args:
            token: JWT token string
            
        Returns:
            AuthenticatedUser object with user info and credentials
            
        Raises:
            JWTAuthError: If token is invalid or expired
        """
        try:
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
                options={
                    "require_exp": True,
                    "require_iat": True,
                    "require_sub": True
                }
            )
            
            # Extract user information
            user_id = payload.get('sub')
            if not user_id:
                raise JWTAuthError("Token missing 'sub' claim")
                
            # Extract scopes
            scopes = set(payload.get('scopes', []))
            if not isinstance(scopes, set) or not scopes:
                raise JWTAuthError("Token missing or invalid 'scopes' claim")
                
            # Extract QuantConnect credentials
            qc_creds_data = payload.get('qc_credentials', {})
            if not qc_creds_data:
                raise JWTAuthError("Token missing 'qc_credentials' claim")
                
            qc_credentials = QuantConnectCredentials(
                user_id=qc_creds_data.get('user_id'),
                api_token=qc_creds_data.get('api_token'),
                organization_id=qc_creds_data.get('organization_id')
            )
            
            if not qc_credentials.user_id or not qc_credentials.api_token:
                raise JWTAuthError("Invalid QuantConnect credentials in token")
                
            return AuthenticatedUser(
                user_id=user_id,
                scopes=scopes,
                qc_credentials=qc_credentials,
                organization_id=payload.get('organization_id')
            )
            
        except jwt.ExpiredSignatureError:
            raise JWTAuthError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise JWTAuthError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise JWTAuthError(f"Token validation failed: {str(e)}")
            
    def extract_bearer_token(self, authorization_header: Optional[str]) -> str:
        """
        Extract Bearer token from Authorization header
        
        Args:
            authorization_header: HTTP Authorization header value
            
        Returns:
            JWT token string
            
        Raises:
            JWTAuthError: If header is missing or invalid format
        """
        if not authorization_header:
            raise JWTAuthError("Missing Authorization header")
            
        parts = authorization_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise JWTAuthError("Invalid Authorization header format. Expected 'Bearer <token>'")
            
        return parts[1]
        
    def create_token(
        self,
        user_id: str,
        scopes: Set[str],
        qc_credentials: QuantConnectCredentials,
        expires_in_hours: int = 24,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Create JWT token for development/testing purposes
        
        Args:
            user_id: User identifier
            scopes: Set of authorized scopes
            qc_credentials: QuantConnect API credentials
            expires_in_hours: Token expiration time in hours
            organization_id: Optional organization ID
            
        Returns:
            JWT token string
        """
        now = datetime.now(timezone.utc)
        payload = {
            'iss': self.issuer,
            'aud': self.audience,
            'sub': user_id,
            'iat': now.timestamp(),
            'exp': (now.timestamp() + (expires_in_hours * 3600)),
            'scopes': list(scopes),
            'qc_credentials': {
                'user_id': qc_credentials.user_id,
                'api_token': qc_credentials.api_token,
                'organization_id': qc_credentials.organization_id
            }
        }
        
        if organization_id:
            payload['organization_id'] = organization_id
            
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

# Global authenticator instance
_authenticator: Optional[JWTAuthenticator] = None

def get_authenticator() -> JWTAuthenticator:
    """Get or create global JWT authenticator instance"""
    global _authenticator
    if _authenticator is None:
        _authenticator = JWTAuthenticator()
    return _authenticator

def validate_authorization(authorization_header: Optional[str]) -> AuthenticatedUser:
    """
    Validate authorization header and return authenticated user
    
    Args:
        authorization_header: HTTP Authorization header value
        
    Returns:
        AuthenticatedUser object
        
    Raises:
        JWTAuthError: If authentication fails
    """
    authenticator = get_authenticator()
    token = authenticator.extract_bearer_token(authorization_header)
    return authenticator.validate_token(token)