"""
LedgAI QuantConnect MCP Server - JWT Scope Definitions
Granular permission system for 60+ QuantConnect API tools
"""

from enum import Enum
from typing import Dict, List, Set

class Scope(str, Enum):
    """Available JWT scopes for QuantConnect MCP server"""
    
    # Account access
    ACCOUNT_READ = "qc:account:read"
    
    # Project management
    PROJECTS_READ = "qc:projects:read"
    PROJECTS_WRITE = "qc:projects:write"
    PROJECTS_DELETE = "qc:projects:delete"
    
    # File management
    FILES_READ = "qc:files:read"
    FILES_WRITE = "qc:files:write"
    FILES_DELETE = "qc:files:delete"
    
    # Compilation
    COMPILE_EXECUTE = "qc:compile:execute"
    
    # Backtesting
    BACKTESTS_READ = "qc:backtests:read"
    BACKTESTS_WRITE = "qc:backtests:write"
    BACKTESTS_DELETE = "qc:backtests:delete"
    
    # Optimization
    OPTIMIZATIONS_READ = "qc:optimizations:read"
    OPTIMIZATIONS_WRITE = "qc:optimizations:write"
    OPTIMIZATIONS_DELETE = "qc:optimizations:delete"
    
    # Live trading
    LIVE_READ = "qc:live:read"
    LIVE_WRITE = "qc:live:write"
    LIVE_EXECUTE = "qc:live:execute"
    LIVE_DELETE = "qc:live:delete"
    
    # Object store
    OBJECTS_READ = "qc:objects:read"
    OBJECTS_WRITE = "qc:objects:write"
    OBJECTS_DELETE = "qc:objects:delete"
    
    # AI assistance
    AI_READ = "qc:ai:read"
    AI_EXECUTE = "qc:ai:execute"
    
    # Collaboration
    COLLABORATION_READ = "qc:collaboration:read"
    COLLABORATION_WRITE = "qc:collaboration:write"
    COLLABORATION_DELETE = "qc:collaboration:delete"
    
    # Administrative
    ADMIN_READ = "qc:admin:read"
    ADMIN_WRITE = "qc:admin:write"

# Tool to scope mapping - maps each MCP tool to required scopes
TOOL_SCOPES: Dict[str, List[Scope]] = {
    # Account tools
    "read_account": [Scope.ACCOUNT_READ],
    
    # Project tools
    "create_project": [Scope.PROJECTS_WRITE],
    "read_project": [Scope.PROJECTS_READ],
    "list_projects": [Scope.PROJECTS_READ],
    "update_project": [Scope.PROJECTS_WRITE],
    "delete_project": [Scope.PROJECTS_DELETE],
    
    # Project collaboration tools
    "create_project_collaborator": [Scope.COLLABORATION_WRITE],
    "read_project_collaborators": [Scope.COLLABORATION_READ],
    "update_project_collaborator": [Scope.COLLABORATION_WRITE],
    "delete_project_collaborator": [Scope.COLLABORATION_DELETE],
    
    # Project node tools
    "read_project_nodes": [Scope.PROJECTS_READ],
    "update_project_nodes": [Scope.PROJECTS_WRITE],
    
    # Compilation tools
    "create_compile": [Scope.COMPILE_EXECUTE],
    "read_compile": [Scope.PROJECTS_READ],
    
    # File tools
    "create_file": [Scope.FILES_WRITE],
    "read_file": [Scope.FILES_READ],
    "update_file_name": [Scope.FILES_WRITE],
    "update_file_contents": [Scope.FILES_WRITE],
    "delete_file": [Scope.FILES_DELETE],
    
    # Backtest tools
    "create_backtest": [Scope.BACKTESTS_WRITE],
    "read_backtest": [Scope.BACKTESTS_READ],
    "list_backtests": [Scope.BACKTESTS_READ],
    "read_backtest_chart": [Scope.BACKTESTS_READ],
    "read_backtest_orders": [Scope.BACKTESTS_READ],
    "read_backtest_insights": [Scope.BACKTESTS_READ],
    "update_backtest": [Scope.BACKTESTS_WRITE],
    "delete_backtest": [Scope.BACKTESTS_DELETE],
    
    # Optimization tools
    "estimate_optimization_time": [Scope.OPTIMIZATIONS_READ],
    "create_optimization": [Scope.OPTIMIZATIONS_WRITE],
    "read_optimization": [Scope.OPTIMIZATIONS_READ],
    "list_optimizations": [Scope.OPTIMIZATIONS_READ],
    "update_optimization": [Scope.OPTIMIZATIONS_WRITE],
    "abort_optimization": [Scope.OPTIMIZATIONS_WRITE],
    "delete_optimization": [Scope.OPTIMIZATIONS_DELETE],
    
    # Live trading tools
    "authorize_connection": [Scope.LIVE_WRITE],
    "create_live_algorithm": [Scope.LIVE_WRITE],
    "read_live_algorithm": [Scope.LIVE_READ],
    "list_live_algorithms": [Scope.LIVE_READ],
    "read_live_chart": [Scope.LIVE_READ],
    "read_live_logs": [Scope.LIVE_READ],
    "read_live_portfolio": [Scope.LIVE_READ],
    "read_live_orders": [Scope.LIVE_READ],
    "read_live_insights": [Scope.LIVE_READ],
    "stop_live_algorithm": [Scope.LIVE_EXECUTE],
    "liquidate_live_algorithm": [Scope.LIVE_EXECUTE],
    
    # Live command tools
    "create_live_command": [Scope.LIVE_EXECUTE],
    "broadcast_live_command": [Scope.LIVE_EXECUTE, Scope.ADMIN_WRITE],
    
    # Object store tools
    "upload_object": [Scope.OBJECTS_WRITE],
    "read_object_properties": [Scope.OBJECTS_READ],
    "read_object_store_file_job_id": [Scope.OBJECTS_READ],
    "read_object_store_file_download_url": [Scope.OBJECTS_READ],
    "list_object_store_files": [Scope.OBJECTS_READ],
    "delete_object": [Scope.OBJECTS_DELETE],
    
    # AI tools
    "check_initialization_errors": [Scope.AI_EXECUTE],
    "complete_code": [Scope.AI_EXECUTE],
    "enhance_error_message": [Scope.AI_EXECUTE],
    "update_code_to_pep8": [Scope.AI_EXECUTE],
    "check_syntax": [Scope.AI_EXECUTE],
    "search_quantconnect": [Scope.AI_READ],
    
    # Admin tools
    "read_lean_versions": [Scope.ADMIN_READ],
    "read_mcp_server_version": [Scope.ADMIN_READ],
}

# Predefined scope groups for common use cases
SCOPE_GROUPS: Dict[str, List[Scope]] = {
    "readonly": [
        Scope.ACCOUNT_READ,
        Scope.PROJECTS_READ,
        Scope.FILES_READ,
        Scope.BACKTESTS_READ,
        Scope.OPTIMIZATIONS_READ,
        Scope.LIVE_READ,
        Scope.OBJECTS_READ,
        Scope.AI_READ,
        Scope.COLLABORATION_READ,
    ],
    "trader": [
        Scope.ACCOUNT_READ,
        Scope.PROJECTS_READ,
        Scope.PROJECTS_WRITE,
        Scope.FILES_READ,
        Scope.FILES_WRITE,
        Scope.COMPILE_EXECUTE,
        Scope.BACKTESTS_READ,
        Scope.BACKTESTS_WRITE,
        Scope.OPTIMIZATIONS_READ,
        Scope.OPTIMIZATIONS_WRITE,
        Scope.LIVE_READ,
        Scope.LIVE_WRITE,
        Scope.LIVE_EXECUTE,
        Scope.OBJECTS_READ,
        Scope.OBJECTS_WRITE,
        Scope.AI_READ,
        Scope.AI_EXECUTE,
    ],
    "admin": [scope for scope in Scope],  # All scopes
}

def validate_scopes(user_scopes: Set[str], required_scopes: List[Scope]) -> bool:
    """
    Validate that user has all required scopes
    
    Args:
        user_scopes: Set of scopes from JWT token
        required_scopes: List of required scopes for the operation
        
    Returns:
        True if user has all required scopes, False otherwise
    """
    required_scope_strings = {scope.value for scope in required_scopes}
    return required_scope_strings.issubset(user_scopes)

def get_tool_scopes(tool_name: str) -> List[Scope]:
    """
    Get required scopes for a specific tool
    
    Args:
        tool_name: Name of the MCP tool
        
    Returns:
        List of required scopes for the tool
    """
    return TOOL_SCOPES.get(tool_name, [])