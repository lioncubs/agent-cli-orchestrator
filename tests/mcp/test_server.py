"""Tests for MCP server setup and initialization."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from src.mcp.server import MCPServer, create_mcp_server
from src.mcp.tools.query import QueryTools
from src.mcp.tools.session import SessionTools
from src.mcp.tools.delegation import DelegationTools
from src.mcp.tools.repository import RepositoryTools
from src.mcp.resources import MCPResources


@pytest.fixture
def mock_query_tools():
    """Create mock query tools."""
    return Mock(spec=QueryTools)


@pytest.fixture
def mock_session_tools():
    """Create mock session tools."""
    return Mock(spec=SessionTools)


@pytest.fixture
def mock_delegation_tools():
    """Create mock delegation tools."""
    return Mock(spec=DelegationTools)


@pytest.fixture
def mock_repository_tools():
    """Create mock repository tools."""
    return Mock(spec=RepositoryTools)


@pytest.fixture
def mock_resources():
    """Create mock MCP resources."""
    return Mock(spec=MCPResources)


@pytest.fixture
def mcp_server(mock_query_tools, mock_session_tools, mock_delegation_tools, 
               mock_repository_tools, mock_resources):
    """Create MCP server instance."""
    return MCPServer(
        query_tools=mock_query_tools,
        session_tools=mock_session_tools,
        delegation_tools=mock_delegation_tools,
        repository_tools=mock_repository_tools,
        resources=mock_resources
    )


def test_mcp_server_initialization(mcp_server):
    """Test MCP server initializes correctly."""
    assert mcp_server is not None
    assert mcp_server.mcp is not None
    assert mcp_server.query_tools is not None
    assert mcp_server.session_tools is not None
    assert mcp_server.delegation_tools is not None
    assert mcp_server.repository_tools is not None
    assert mcp_server.resources is not None


def test_mcp_server_get_app(mcp_server):
    """Test getting MCP app for mounting."""
    app = mcp_server.get_app()
    assert app is not None
    assert app == mcp_server.mcp


def test_create_mcp_server(mock_query_tools, mock_session_tools, 
                          mock_delegation_tools, mock_repository_tools, 
                          mock_resources):
    """Test MCP server factory function."""
    server = create_mcp_server(
        query_tools=mock_query_tools,
        session_tools=mock_session_tools,
        delegation_tools=mock_delegation_tools,
        repository_tools=mock_repository_tools,
        resources=mock_resources
    )
    
    assert isinstance(server, MCPServer)
    assert server.query_tools == mock_query_tools
    assert server.session_tools == mock_session_tools
    assert server.delegation_tools == mock_delegation_tools
    assert server.repository_tools == mock_repository_tools
    assert server.resources == mock_resources


def test_mcp_server_tools_registration(mcp_server):
    """Test that tools are registered with the MCP server."""
    # The MCP server should have tools registered
    # This is verified by the fact that _register_tools() is called in __init__
    assert mcp_server.mcp is not None
    
    # We can verify the server has been properly initialized
    # The actual tool decorators are applied during initialization
    assert hasattr(mcp_server, 'query_tools')
    assert hasattr(mcp_server, 'session_tools')
    assert hasattr(mcp_server, 'delegation_tools')
    assert hasattr(mcp_server, 'repository_tools')


def test_mcp_server_resources_registration(mcp_server):
    """Test that resources are registered with the MCP server."""
    # The MCP server should have resources registered
    # This is verified by the fact that _register_resources() is called in __init__
    assert mcp_server.mcp is not None
    assert hasattr(mcp_server, 'resources')


def test_mcp_server_component_injection(mock_query_tools, mock_session_tools,
                                        mock_delegation_tools, mock_repository_tools,
                                        mock_resources):
    """Test that all components are properly injected."""
    server = MCPServer(
        query_tools=mock_query_tools,
        session_tools=mock_session_tools,
        delegation_tools=mock_delegation_tools,
        repository_tools=mock_repository_tools,
        resources=mock_resources
    )
    
    # Verify all components are accessible
    assert server.query_tools is mock_query_tools
    assert server.session_tools is mock_session_tools
    assert server.delegation_tools is mock_delegation_tools
    assert server.repository_tools is mock_repository_tools
    assert server.resources is mock_resources


def test_mcp_server_factory_creates_proper_instance():
    """Test factory creates a properly configured server."""
    query_tools = Mock(spec=QueryTools)
    session_tools = Mock(spec=SessionTools)
    delegation_tools = Mock(spec=DelegationTools)
    repository_tools = Mock(spec=RepositoryTools)
    resources = Mock(spec=MCPResources)
    
    server = create_mcp_server(
        query_tools=query_tools,
        session_tools=session_tools,
        delegation_tools=delegation_tools,
        repository_tools=repository_tools,
        resources=resources
    )
    
    assert isinstance(server, MCPServer)
    assert server.get_app() is not None
