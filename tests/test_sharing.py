"""
Unit tests for project sharing functions.

CRITICAL: All tests mock authentication and HTTP requests.
No real API calls are made in these tests.
"""

import json
import pytest
from unittest.mock import patch, Mock
from httpx import HTTPStatusError


# Test update_hex_project_user_sharing

@pytest.mark.asyncio
async def test_update_user_sharing_single_user(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test granting access to a single user."""
    # Arrange
    response_data = {"success": True}
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act
            result_str = await update_hex_project_user_sharing(
                project_id="project-123",
                user_permissions=[
                    {"user_id": "user-456", "access": "CAN_EDIT"}
                ]
            )
            result = json.loads(result_str)

            # Assert
            assert result["success"] is True

            # Verify HTTP request
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args

            # Check method and URL
            assert call_args[1]["method"] == "PATCH"
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/projects/project-123/sharing/users"

            # Check request body structure
            body = call_args[1]["json"]
            assert "sharing" in body
            assert "upsert" in body["sharing"]
            assert "users" in body["sharing"]["upsert"]
            assert len(body["sharing"]["upsert"]["users"]) == 1

            # Check user structure
            user = body["sharing"]["upsert"]["users"][0]
            assert user["user"]["id"] == "user-456"
            assert user["access"] == "CAN_EDIT"


@pytest.mark.asyncio
async def test_update_user_sharing_multiple_users(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test granting access to multiple users with different permissions."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act
            await update_hex_project_user_sharing(
                project_id="project-123",
                user_permissions=[
                    {"user_id": "user-1", "access": "FULL_ACCESS"},
                    {"user_id": "user-2", "access": "CAN_EDIT"},
                    {"user_id": "user-3", "access": "CAN_VIEW"}
                ]
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            users = body["sharing"]["upsert"]["users"]
            assert len(users) == 3
            assert users[0]["access"] == "FULL_ACCESS"
            assert users[1]["access"] == "CAN_EDIT"
            assert users[2]["access"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_update_user_sharing_revoke_access(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test revoking user access with NONE permission."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act
            await update_hex_project_user_sharing(
                project_id="project-123",
                user_permissions=[
                    {"user_id": "user-456", "access": "NONE"}
                ]
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["upsert"]["users"][0]["access"] == "NONE"


@pytest.mark.asyncio
async def test_update_user_sharing_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 403 error when user lacks admin permissions."""
    # Arrange
    error_response = mock_httpx_response(
        403,
        {"message": "Requires project admin permissions", "statusCode": 403}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_project_user_sharing(
                    project_id="project-123",
                    user_permissions=[
                        {"user_id": "user-456", "access": "CAN_VIEW"}
                    ]
                )

            assert exc_info.value.response.status_code == 403


# Test update_hex_project_group_sharing

@pytest.mark.asyncio
async def test_update_group_sharing_single_group(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test granting access to a single group."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_group_sharing

            # Act
            result_str = await update_hex_project_group_sharing(
                project_id="project-123",
                group_permissions=[
                    {"group_id": "group-789", "access": "CAN_VIEW"}
                ]
            )
            result = json.loads(result_str)

            # Assert
            assert result["success"] is True

            # Verify request structure
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/projects/project-123/sharing/groups"

            body = call_args[1]["json"]
            assert "sharing" in body
            assert "upsert" in body["sharing"]
            assert "groups" in body["sharing"]["upsert"]

            group = body["sharing"]["upsert"]["groups"][0]
            assert group["group"]["id"] == "group-789"
            assert group["access"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_update_group_sharing_multiple_groups(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test granting access to multiple groups."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_group_sharing

            # Act
            await update_hex_project_group_sharing(
                project_id="project-123",
                group_permissions=[
                    {"group_id": "group-admin", "access": "FULL_ACCESS"},
                    {"group_id": "group-editors", "access": "CAN_EDIT"},
                    {"group_id": "group-viewers", "access": "CAN_VIEW"}
                ]
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            groups = body["sharing"]["upsert"]["groups"]
            assert len(groups) == 3
            assert groups[0]["group"]["id"] == "group-admin"
            assert groups[1]["access"] == "CAN_EDIT"
            assert groups[2]["access"] == "CAN_VIEW"


# Test update_hex_project_collection_sharing

@pytest.mark.asyncio
async def test_update_collection_sharing_add_to_collection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test adding project to a collection."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_collection_sharing

            # Act
            result_str = await update_hex_project_collection_sharing(
                project_id="project-123",
                collection_permissions=[
                    {"collection_id": "collection-abc", "access": "CAN_VIEW"}
                ]
            )
            result = json.loads(result_str)

            # Assert
            assert result["success"] is True

            # Verify request structure
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/projects/project-123/sharing/collections"

            body = call_args[1]["json"]
            assert "sharing" in body
            assert "upsert" in body["sharing"]
            assert "collections" in body["sharing"]["upsert"]

            collection = body["sharing"]["upsert"]["collections"][0]
            assert collection["collection"]["id"] == "collection-abc"
            assert collection["access"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_update_collection_sharing_multiple_collections(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test adding project to multiple collections."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_collection_sharing

            # Act
            await update_hex_project_collection_sharing(
                project_id="project-123",
                collection_permissions=[
                    {"collection_id": "collection-1", "access": "CAN_VIEW"},
                    {"collection_id": "collection-2", "access": "CAN_EDIT"}
                ]
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            collections = body["sharing"]["upsert"]["collections"]
            assert len(collections) == 2
            assert collections[0]["collection"]["id"] == "collection-1"
            assert collections[1]["access"] == "CAN_EDIT"


@pytest.mark.asyncio
async def test_update_collection_sharing_remove_from_collection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test removing project from collection with NONE access."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_collection_sharing

            # Act
            await update_hex_project_collection_sharing(
                project_id="project-123",
                collection_permissions=[
                    {"collection_id": "collection-abc", "access": "NONE"}
                ]
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["upsert"]["collections"][0]["access"] == "NONE"


# Test update_hex_project_workspace_sharing

@pytest.mark.asyncio
async def test_update_workspace_sharing_workspace_only(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating workspace access only."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act
            result_str = await update_hex_project_workspace_sharing(
                project_id="project-123",
                workspace_access="CAN_VIEW"
            )
            result = json.loads(result_str)

            # Assert
            assert result["success"] is True

            # Verify request structure
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/projects/project-123/sharing/workspaceAndPublic"

            body = call_args[1]["json"]
            assert "sharing" in body
            assert body["sharing"]["workspace"] == "CAN_VIEW"
            assert "publicWeb" not in body["sharing"]


@pytest.mark.asyncio
async def test_update_workspace_sharing_public_only(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating public access only."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act
            result_str = await update_hex_project_workspace_sharing(
                project_id="project-123",
                public_access="CAN_VIEW"
            )
            result = json.loads(result_str)

            # Assert
            assert result["success"] is True

            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["publicWeb"] == "CAN_VIEW"
            assert "workspace" not in body["sharing"]


@pytest.mark.asyncio
async def test_update_workspace_sharing_both(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating both workspace and public access."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act
            await update_hex_project_workspace_sharing(
                project_id="project-123",
                workspace_access="CAN_EDIT",
                public_access="CAN_VIEW"
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["workspace"] == "CAN_EDIT"
            assert body["sharing"]["publicWeb"] == "CAN_VIEW"


@pytest.mark.asyncio
async def test_update_workspace_sharing_make_public(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test making a project publicly accessible."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act
            await update_hex_project_workspace_sharing(
                project_id="project-123",
                workspace_access="CAN_VIEW",
                public_access="APP_ONLY"
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["workspace"] == "CAN_VIEW"
            assert body["sharing"]["publicWeb"] == "APP_ONLY"


@pytest.mark.asyncio
async def test_update_workspace_sharing_revoke_public(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test revoking public access."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act
            await update_hex_project_workspace_sharing(
                project_id="project-123",
                public_access="NONE"
            )

            # Assert
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["sharing"]["publicWeb"] == "NONE"


@pytest.mark.asyncio
async def test_update_workspace_sharing_error_no_parameters(mock_api_key):
    """Test error when no parameters provided."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_workspace_sharing

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await update_hex_project_workspace_sharing(project_id="project-123")

            assert "Must provide at least one of" in str(exc_info.value)


# Test access level variations

@pytest.mark.asyncio
async def test_all_access_levels_user_sharing(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test all access level values for user sharing."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {"success": True})

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Test all access levels
            for access_level in ["NONE", "APP_ONLY", "CAN_VIEW", "CAN_EDIT", "FULL_ACCESS"]:
                # Act
                await update_hex_project_user_sharing(
                    project_id="project-123",
                    user_permissions=[
                        {"user_id": "user-456", "access": access_level}
                    ]
                )

                # Assert
                body = mock_httpx_client.request.call_args[1]["json"]
                assert body["sharing"]["upsert"]["users"][0]["access"] == access_level


# Test error handling

@pytest.mark.asyncio
async def test_sharing_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 404 error when project doesn't exist."""
    # Arrange
    error_response = mock_httpx_response(
        404,
        {"message": "Project not found", "statusCode": 404}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_project_user_sharing(
                    project_id="nonexistent-project",
                    user_permissions=[{"user_id": "user-456", "access": "CAN_VIEW"}]
                )

            assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_sharing_400_error_invalid_access_level(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 400 error for invalid access level."""
    # Arrange
    error_response = mock_httpx_response(
        400,
        {"message": "Invalid access level", "statusCode": 400}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_project_user_sharing

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_project_user_sharing(
                    project_id="project-123",
                    user_permissions=[{"user_id": "user-456", "access": "INVALID_LEVEL"}]
                )

            assert exc_info.value.response.status_code == 400
