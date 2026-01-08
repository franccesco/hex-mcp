"""Tests for Hex group management endpoints."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_list_groups_basic(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing groups without parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [
            {
                "id": "group-123",
                "name": "Analytics Team",
                "createdAt": "2026-01-08T12:00:00Z"
            }
        ],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_groups

            result_str = await list_hex_groups()
            result = json.loads(result_str)

            assert "values" in result
            assert len(result["values"]) == 1
            assert result["values"][0]["id"] == "group-123"
            assert result["values"][0]["name"] == "Analytics Team"

            # Verify request was made correctly
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/groups" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_list_groups_with_pagination(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing groups with pagination parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": "cursor-123", "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_groups

            result_str = await list_hex_groups(limit=10, after="prev-cursor")
            result = json.loads(result_str)

            # Verify request included pagination params
            call_args = mock_httpx_client.request.call_args
            params = call_args[1].get("params", {})
            assert params["limit"] == 10
            assert params["after"] == "prev-cursor"


@pytest.mark.asyncio
async def test_list_groups_with_sort(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing groups with sort parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_groups

            result_str = await list_hex_groups(sort_by="name", sort_direction="asc")

            # Verify sortBy and sortDirection parameters were sent
            call_args = mock_httpx_client.request.call_args
            params = call_args[1].get("params", {})
            assert params["sortBy"] == "name"
            assert params["sortDirection"] == "asc"


@pytest.mark.asyncio
async def test_list_groups_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling forbidden error when listing groups."""
    mock_httpx_client.request.return_value = mock_httpx_response(403, {"error": "Forbidden"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_groups

            with pytest.raises(Exception):
                await list_hex_groups()


@pytest.mark.asyncio
async def test_get_group(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test getting a specific group by ID."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Finance Team",
        "createdAt": "2026-01-08T10:30:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_group

            result_str = await get_hex_group(group_id="group-123")
            result = json.loads(result_str)

            assert result["id"] == "group-123"
            assert result["name"] == "Finance Team"
            assert result["createdAt"] == "2026-01-08T10:30:00Z"

            # Verify request was made correctly
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/groups/group-123" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_get_group_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling not found error when getting group."""
    mock_httpx_client.request.return_value = mock_httpx_response(404, {"error": "Group not found"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_group

            with pytest.raises(Exception):
                await get_hex_group(group_id="nonexistent")


@pytest.mark.asyncio
async def test_create_group_simple(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a group with just name."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "group-new-123",
        "name": "New Group",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_group

            result_str = await create_hex_group(name="New Group")
            result = json.loads(result_str)

            assert result["id"] == "group-new-123"
            assert result["name"] == "New Group"

            # Verify request body
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "POST"
            assert "/v1/groups" in call_args[1]["url"]
            body = call_args[1]["json"]
            assert body["name"] == "New Group"
            assert "members" not in body


@pytest.mark.asyncio
async def test_create_group_with_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a group with initial members."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "group-123",
        "name": "Analytics Team",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_group

            result_str = await create_hex_group(
                name="Analytics Team",
                member_user_ids=["user-123", "user-456"]
            )
            result = json.loads(result_str)

            assert result["name"] == "Analytics Team"

            # Verify request body includes members
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "members" in body
            assert len(body["members"]["users"]) == 2
            assert body["members"]["users"][0]["id"] == "user-123"
            assert body["members"]["users"][1]["id"] == "user-456"


@pytest.mark.asyncio
async def test_create_group_error_too_many_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test error when creating group with more than 100 members."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_group

            # Create list of 101 user IDs
            too_many_members = [f"user-{i}" for i in range(101)]

            with pytest.raises(ValueError, match="Cannot add more than 100 members"):
                await create_hex_group(
                    name="Large Group",
                    member_user_ids=too_many_members
                )


@pytest.mark.asyncio
async def test_create_group_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling forbidden error when creating group."""
    mock_httpx_client.request.return_value = mock_httpx_response(403, {"error": "Forbidden"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_group

            with pytest.raises(Exception):
                await create_hex_group(name="Test Group")


@pytest.mark.asyncio
async def test_update_group_name(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating group name."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Updated Name",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            result_str = await update_hex_group(
                group_id="group-123",
                name="Updated Name"
            )
            result = json.loads(result_str)

            assert result["name"] == "Updated Name"

            # Verify request body
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "PATCH"
            assert "/v1/groups/group-123" in call_args[1]["url"]
            body = call_args[1]["json"]
            assert body["name"] == "Updated Name"
            assert "members" not in body


@pytest.mark.asyncio
async def test_update_group_add_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test adding members to a group."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Analytics Team",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            result_str = await update_hex_group(
                group_id="group-123",
                add_member_user_ids=["user-456", "user-789"]
            )

            # Verify request body includes members.add
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "members" in body
            assert "add" in body["members"]
            assert len(body["members"]["add"]["users"]) == 2
            assert body["members"]["add"]["users"][0]["id"] == "user-456"
            assert body["members"]["add"]["users"][1]["id"] == "user-789"
            assert "remove" not in body["members"]


@pytest.mark.asyncio
async def test_update_group_remove_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test removing members from a group."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Analytics Team",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            result_str = await update_hex_group(
                group_id="group-123",
                remove_member_user_ids=["user-123"]
            )

            # Verify request body includes members.remove
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "members" in body
            assert "remove" in body["members"]
            assert len(body["members"]["remove"]["users"]) == 1
            assert body["members"]["remove"]["users"][0]["id"] == "user-123"
            assert "add" not in body["members"]


@pytest.mark.asyncio
async def test_update_group_add_and_remove_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test adding and removing members in same operation."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Analytics Team",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            result_str = await update_hex_group(
                group_id="group-123",
                add_member_user_ids=["user-new"],
                remove_member_user_ids=["user-old"]
            )

            # Verify request body includes both add and remove
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "members" in body
            assert "add" in body["members"]
            assert "remove" in body["members"]
            assert body["members"]["add"]["users"][0]["id"] == "user-new"
            assert body["members"]["remove"]["users"][0]["id"] == "user-old"


@pytest.mark.asyncio
async def test_update_group_name_and_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating name and members together."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "group-123",
        "name": "Senior Analytics Team",
        "createdAt": "2026-01-08T12:00:00Z"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            result_str = await update_hex_group(
                group_id="group-123",
                name="Senior Analytics Team",
                add_member_user_ids=["user-456"]
            )

            # Verify both name and members in request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["name"] == "Senior Analytics Team"
            assert "members" in body
            assert "add" in body["members"]


@pytest.mark.asyncio
async def test_update_group_error_no_parameters(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test error when updating group with no parameters."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            with pytest.raises(ValueError, match="Must provide at least one parameter"):
                await update_hex_group(group_id="group-123")


@pytest.mark.asyncio
async def test_update_group_error_too_many_add_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test error when adding more than 100 members."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            too_many_members = [f"user-{i}" for i in range(101)]

            with pytest.raises(ValueError, match="Cannot add more than 100 members"):
                await update_hex_group(
                    group_id="group-123",
                    add_member_user_ids=too_many_members
                )


@pytest.mark.asyncio
async def test_update_group_error_too_many_remove_members(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test error when removing more than 100 members."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            too_many_members = [f"user-{i}" for i in range(101)]

            with pytest.raises(ValueError, match="Cannot remove more than 100 members"):
                await update_hex_group(
                    group_id="group-123",
                    remove_member_user_ids=too_many_members
                )


@pytest.mark.asyncio
async def test_update_group_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling not found error when updating group."""
    mock_httpx_client.request.return_value = mock_httpx_response(404, {"error": "Group not found"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_group

            with pytest.raises(Exception):
                await update_hex_group(
                    group_id="nonexistent",
                    name="New Name"
                )


@pytest.mark.asyncio
async def test_delete_group(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test deleting a group."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import delete_hex_group

            result = await delete_hex_group(group_id="group-123")

            assert result == "Group deleted successfully"

            # Verify request was made correctly
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "DELETE"
            assert "/v1/groups/group-123" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_delete_group_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test handling not found error when deleting group."""
    mock_httpx_client.request.return_value = mock_httpx_response(404, {"error": "Group not found"})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import delete_hex_group

            with pytest.raises(Exception):
                await delete_hex_group(group_id="nonexistent")
