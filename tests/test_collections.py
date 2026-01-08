"""Tests for Hex collection management endpoints."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_list_collections_basic(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing collections without parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [
            {
                "id": "collection-123",
                "name": "Analytics Dashboards",
                "description": "Customer-facing analytics",
                "creator": {"id": "user-456", "email": "creator@example.com"},
                "sharing": {}
            }
        ],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_collections

            result_str = await list_hex_collections()
            result = json.loads(result_str)

            assert "values" in result
            assert len(result["values"]) == 1
            assert result["values"][0]["id"] == "collection-123"
            assert result["values"][0]["name"] == "Analytics Dashboards"

            # Verify request was made correctly
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/collections" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_list_collections_with_pagination(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing collections with pagination parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": "cursor-123", "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_collections

            result_str = await list_hex_collections(limit=10, after="prev-cursor")
            result = json.loads(result_str)

            # Verify request included pagination params
            call_args = mock_httpx_client.request.call_args
            params = call_args[1].get("params", {})
            assert params["limit"] == 10
            assert params["after"] == "prev-cursor"


@pytest.mark.asyncio
async def test_list_collections_with_sort(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing collections with sort parameter."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_collections

            result_str = await list_hex_collections(sort_by="name")

            # Verify sortBy parameter was sent
            call_args = mock_httpx_client.request.call_args
            params = call_args[1].get("params", {})
            assert params["sortBy"] == "name"


@pytest.mark.asyncio
async def test_list_collections_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling forbidden error when listing collections."""
    mock_httpx_client.request.return_value = mock_httpx_response(403, {"error": "Forbidden"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_collections

            with pytest.raises(Exception):
                await list_hex_collections()


@pytest.mark.asyncio
async def test_get_collection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test getting a specific collection by ID."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Finance Reports",
        "description": "Quarterly financial reports",
        "creator": {"id": "user-789", "email": "admin@example.com"},
        "sharing": {
            "users": [{"id": "user-456", "access": "CAN_VIEW"}],
            "groups": [{"id": "group-123", "access": "CAN_EDIT"}],
            "workspace": {"members": "CAN_VIEW"}
        }
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_collection

            result_str = await get_hex_collection(collection_id="collection-123")
            result = json.loads(result_str)

            assert result["id"] == "collection-123"
            assert result["name"] == "Finance Reports"
            assert result["description"] == "Quarterly financial reports"
            assert result["creator"]["email"] == "admin@example.com"
            assert len(result["sharing"]["users"]) == 1
            assert len(result["sharing"]["groups"]) == 1

            # Verify request was made correctly
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/collections/collection-123" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_get_collection_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling not found error when getting collection."""
    mock_httpx_client.request.return_value = mock_httpx_response(404, {"error": "Collection not found"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_collection

            with pytest.raises(Exception):
                await get_hex_collection(collection_id="nonexistent")


@pytest.mark.asyncio
async def test_create_collection_simple(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a collection with just name."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "collection-new-123",
        "name": "New Collection",
        "sharing": {}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_collection

            result_str = await create_hex_collection(name="New Collection")
            result = json.loads(result_str)

            assert result["id"] == "collection-new-123"
            assert result["name"] == "New Collection"

            # Verify request body
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "POST"
            assert "/v1/collections" in call_args[1]["url"]
            body = call_args[1]["json"]
            assert body["name"] == "New Collection"
            assert "description" not in body
            assert "sharing" not in body


@pytest.mark.asyncio
async def test_create_collection_with_description(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a collection with name and description."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "collection-123",
        "name": "Analytics",
        "description": "Analytics projects",
        "sharing": {}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_collection

            result_str = await create_hex_collection(
                name="Analytics",
                description="Analytics projects"
            )
            result = json.loads(result_str)

            assert result["name"] == "Analytics"
            assert result["description"] == "Analytics projects"

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["name"] == "Analytics"
            assert body["description"] == "Analytics projects"


@pytest.mark.asyncio
async def test_create_collection_with_sharing(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a collection with sharing settings."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "collection-123",
        "name": "Shared Collection",
        "sharing": {
            "users": [{"id": "user-456", "access": "CAN_EDIT"}],
            "workspace": {"members": "CAN_VIEW"}
        }
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_collection

            result_str = await create_hex_collection(
                name="Shared Collection",
                sharing_users=[{"id": "user-456", "access": "CAN_EDIT"}],
                workspace_access="CAN_VIEW"
            )
            result = json.loads(result_str)

            # Verify request body includes sharing
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "sharing" in body
            assert body["sharing"]["users"][0]["id"] == "user-456"
            assert body["sharing"]["users"][0]["access"] == "CAN_EDIT"
            assert body["sharing"]["workspace"]["members"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_create_collection_with_groups(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a collection with group sharing."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "collection-123",
        "name": "Group Collection",
        "sharing": {"groups": [{"id": "group-789", "access": "CAN_VIEW"}]}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_collection

            result_str = await create_hex_collection(
                name="Group Collection",
                sharing_groups=[{"id": "group-789", "access": "CAN_VIEW"}]
            )

            # Verify request body includes group sharing
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "sharing" in body
            assert body["sharing"]["groups"][0]["id"] == "group-789"
            assert body["sharing"]["groups"][0]["access"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_create_collection_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling forbidden error when creating collection."""
    mock_httpx_client.request.return_value = mock_httpx_response(403, {"error": "Forbidden"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_collection

            with pytest.raises(Exception):
                await create_hex_collection(name="Test Collection")


@pytest.mark.asyncio
async def test_update_collection_name(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating collection name."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Updated Name",
        "sharing": {}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            result_str = await update_hex_collection(
                collection_id="collection-123",
                name="Updated Name"
            )
            result = json.loads(result_str)

            assert result["name"] == "Updated Name"

            # Verify request body
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "PATCH"
            assert "/v1/collections/collection-123" in call_args[1]["url"]
            body = call_args[1]["json"]
            assert body["name"] == "Updated Name"
            assert "description" not in body
            assert "sharing" not in body


@pytest.mark.asyncio
async def test_update_collection_description(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating collection description."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Collection",
        "description": "New description",
        "sharing": {}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            result_str = await update_hex_collection(
                collection_id="collection-123",
                description="New description"
            )

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["description"] == "New description"
            assert "name" not in body


@pytest.mark.asyncio
async def test_update_collection_sharing(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating collection sharing settings."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Collection",
        "sharing": {
            "users": [{"id": "user-789", "access": "CAN_EDIT"}],
            "workspace": {"members": "CAN_VIEW"}
        }
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            result_str = await update_hex_collection(
                collection_id="collection-123",
                sharing_users=[{"id": "user-789", "access": "CAN_EDIT"}],
                workspace_access="CAN_VIEW"
            )

            # Verify request body includes sharing.upsert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "sharing" in body
            assert "upsert" in body["sharing"]
            assert body["sharing"]["upsert"]["users"][0]["id"] == "user-789"
            assert body["sharing"]["upsert"]["workspace"]["members"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_update_collection_multiple_fields(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating multiple collection fields at once."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Updated Collection",
        "description": "Updated description",
        "sharing": {"workspace": {"members": "CAN_EDIT"}}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            result_str = await update_hex_collection(
                collection_id="collection-123",
                name="Updated Collection",
                description="Updated description",
                workspace_access="CAN_EDIT"
            )

            # Verify all fields in request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["name"] == "Updated Collection"
            assert body["description"] == "Updated description"
            assert body["sharing"]["upsert"]["workspace"]["members"] == "CAN_EDIT"


@pytest.mark.asyncio
async def test_update_collection_error_no_parameters(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test error when updating collection with no parameters."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            with pytest.raises(ValueError, match="Must provide at least one parameter"):
                await update_hex_collection(collection_id="collection-123")


@pytest.mark.asyncio
async def test_update_collection_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling not found error when updating collection."""
    mock_httpx_client.request.return_value = mock_httpx_response(404, {"error": "Collection not found"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            with pytest.raises(Exception):
                await update_hex_collection(
                    collection_id="nonexistent",
                    name="New Name"
                )


@pytest.mark.asyncio
async def test_update_collection_groups(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating collection with group sharing."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "collection-123",
        "name": "Collection",
        "sharing": {"groups": [{"id": "group-456", "access": "CAN_VIEW"}]}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_collection

            result_str = await update_hex_collection(
                collection_id="collection-123",
                sharing_groups=[{"id": "group-456", "access": "CAN_VIEW"}]
            )

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "sharing" in body
            assert body["sharing"]["upsert"]["groups"][0]["id"] == "group-456"
            assert body["sharing"]["upsert"]["groups"][0]["access"] == "CAN_VIEW"
