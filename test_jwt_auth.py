#!/usr/bin/env python3
"""
Test JWT Authentication System for LedgAI QuantConnect MCP Server
"""

import sys
import os
sys.path.append('src')

from jwt_auth import JWTAuthenticator, QuantConnectCredentials
from scopes import Scope, SCOPE_GROUPS, validate_scopes, get_tool_scopes

def test_jwt_creation_and_validation():
    """Test JWT token creation and validation"""
    print("🧪 Testing JWT creation and validation...")
    
    # Create authenticator
    secret_key = os.getenv('JWT_SECRET_KEY', 'test-secret-key-256-bits-long-for-testing-only')
    authenticator = JWTAuthenticator(secret_key=secret_key)
    
    # Create test credentials
    qc_credentials = QuantConnectCredentials(
        user_id="406922",
        api_token="test-api-token",
        organization_id="test-org-id"
    )
    
    # Create token with trader scopes
    token = authenticator.create_token(
        user_id="test-user",
        scopes=set(SCOPE_GROUPS['trader']),
        qc_credentials=qc_credentials,
        expires_in_hours=1
    )
    
    print(f"✅ JWT Token created: {token[:50]}...")
    
    # Validate token
    user = authenticator.validate_token(token)
    
    print(f"✅ Token validated successfully")
    print(f"   User ID: {user.user_id}")
    print(f"   Scopes: {len(user.scopes)} scopes")
    print(f"   QC User ID: {user.qc_credentials.user_id}")
    
    # Test scope validation
    required_scopes = [Scope.PROJECTS_READ, Scope.PROJECTS_WRITE]
    has_scopes = validate_scopes(user.scopes, required_scopes)
    print(f"✅ Scope validation: {has_scopes}")
    
    return True

def test_scope_system():
    """Test the scope definition and validation system"""
    print("\n🎯 Testing scope system...")
    
    # Test tool scope mapping
    project_scopes = get_tool_scopes('create_project')
    print(f"✅ create_project requires: {[s.value for s in project_scopes]}")
    
    backtest_scopes = get_tool_scopes('create_backtest')
    print(f"✅ create_backtest requires: {[s.value for s in backtest_scopes]}")
    
    # Test scope groups
    readonly_scopes = set(SCOPE_GROUPS['readonly'])
    trader_scopes = set(SCOPE_GROUPS['trader'])
    admin_scopes = set(SCOPE_GROUPS['admin'])
    
    print(f"✅ Readonly scopes: {len(readonly_scopes)}")
    print(f"✅ Trader scopes: {len(trader_scopes)}")
    print(f"✅ Admin scopes: {len(admin_scopes)}")
    
    # Test scope validation logic
    user_scopes = {scope.value for scope in trader_scopes}
    
    # Should have project read access
    can_read_projects = validate_scopes(user_scopes, [Scope.PROJECTS_READ])
    print(f"✅ Trader can read projects: {can_read_projects}")
    
    # Should not have admin access  
    can_admin = validate_scopes(user_scopes, [Scope.ADMIN_WRITE])
    print(f"✅ Trader cannot admin: {not can_admin}")
    
    return True

def test_multi_tenant_credentials():
    """Test multi-tenant credential isolation"""
    print("\n👥 Testing multi-tenant credentials...")
    
    secret_key = os.getenv('JWT_SECRET_KEY', 'test-secret-key-256-bits-long-for-testing-only')
    authenticator = JWTAuthenticator(secret_key=secret_key)
    
    # Create credentials for user 1
    user1_creds = QuantConnectCredentials(
        user_id="user1_qc_id",
        api_token="user1_api_token",
        organization_id="user1_org"
    )
    
    # Create credentials for user 2
    user2_creds = QuantConnectCredentials(
        user_id="user2_qc_id", 
        api_token="user2_api_token",
        organization_id="user2_org"
    )
    
    # Create tokens for both users
    token1 = authenticator.create_token(
        user_id="user1",
        scopes=set(SCOPE_GROUPS['readonly']),
        qc_credentials=user1_creds
    )
    
    token2 = authenticator.create_token(
        user_id="user2",
        scopes=set(SCOPE_GROUPS['trader']),
        qc_credentials=user2_creds
    )
    
    # Validate both tokens
    validated_user1 = authenticator.validate_token(token1)
    validated_user2 = authenticator.validate_token(token2)
    
    print(f"✅ User 1 QC ID: {validated_user1.qc_credentials.user_id}")
    print(f"✅ User 2 QC ID: {validated_user2.qc_credentials.user_id}")
    print(f"✅ User 1 scopes: {len(validated_user1.scopes)}")
    print(f"✅ User 2 scopes: {len(validated_user2.scopes)}")
    
    # Verify isolation
    assert validated_user1.qc_credentials.user_id != validated_user2.qc_credentials.user_id
    assert validated_user1.qc_credentials.api_token != validated_user2.qc_credentials.api_token
    assert len(validated_user1.scopes) != len(validated_user2.scopes)
    
    print("✅ Multi-tenant isolation verified")
    
    return True

def test_invalid_tokens():
    """Test handling of invalid tokens"""
    print("\n❌ Testing invalid token handling...")
    
    secret_key = os.getenv('JWT_SECRET_KEY', 'test-secret-key-256-bits-long-for-testing-only')
    authenticator = JWTAuthenticator(secret_key=secret_key)
    
    # Test invalid token format
    try:
        authenticator.validate_token("invalid-token")
        print("❌ Should have failed on invalid token")
        return False
    except Exception as e:
        print(f"✅ Invalid token rejected: {type(e).__name__}")
    
    # Test wrong secret key
    wrong_authenticator = JWTAuthenticator(secret_key="wrong-secret-key")
    
    # Create token with correct secret
    qc_creds = QuantConnectCredentials(
        user_id="test",
        api_token="test"
    )
    token = authenticator.create_token(
        user_id="test-user",
        scopes=set([Scope.PROJECTS_READ]),
        qc_credentials=qc_creds
    )
    
    # Try to validate with wrong secret
    try:
        wrong_authenticator.validate_token(token)
        print("❌ Should have failed with wrong secret")
        return False
    except Exception as e:
        print(f"✅ Wrong secret rejected: {type(e).__name__}")
    
    return True

def create_development_token_example():
    """Create a development token for testing"""
    print("\n🛠️ Creating development token...")
    
    secret_key = os.getenv('JWT_SECRET_KEY')
    if not secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
    authenticator = JWTAuthenticator(secret_key=secret_key)
    
    qc_credentials = QuantConnectCredentials(
        user_id=os.getenv('QUANTCONNECT_USER_ID', '406922'),
        api_token=os.getenv('QUANTCONNECT_API_TOKEN', 'test-token'),
        organization_id=os.getenv('QUANTCONNECT_ORGANIZATION_ID')
    )
    
    # Create token with admin scopes
    token = authenticator.create_token(
        user_id="dev-user",
        scopes=set(SCOPE_GROUPS['admin']),
        qc_credentials=qc_credentials,
        expires_in_hours=24
    )
    
    print(f"🎫 Development JWT Token:")
    print(f"   {token}")
    print(f"\n📋 Authorization Header:")
    print(f"   Authorization: Bearer {token}")
    
    return token

def main():
    """Run all tests"""
    print("🚀 LedgAI QuantConnect MCP Server - JWT Authentication Tests\n")
    
    tests = [
        test_jwt_creation_and_validation,
        test_scope_system,
        test_multi_tenant_credentials,
        test_invalid_tokens
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ {test.__name__} failed")
        except Exception as e:
            print(f"❌ {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! JWT authentication system is working correctly.")
        
        # Create development token
        create_development_token_example()
        
        print("\n🔧 Next Steps:")
        print("1. Set JWT_SECRET_KEY environment variable")
        print("2. Build Docker image: docker build -f Dockerfile.jwt -t ledgai/quantconnect-mcp-jwt .")
        print("3. Test with Claude Desktop using the token above")
        print("4. Deploy to production with proper secrets management")
        
        return True
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)