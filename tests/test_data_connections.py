"""Tests for data connection management endpoints."""

import json
import pytest
from unittest.mock import patch, Mock
from httpx import HTTPStatusError


@pytest.mark.asyncio
async def test_list_data_connections_basic(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing data connections without parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [
            {
                "id": "conn-123",
                "name": "Production BigQuery",
                "type": "bigquery",
                "description": "Production data warehouse",
                "connectionDetails": {"bigquery": {}},
                "sharing": {}
            }
        ],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_data_connections

            result_str = await list_hex_data_connections()
            result = json.loads(result_str)

            assert "values" in result
            assert len(result["values"]) == 1
            assert result["values"][0]["id"] == "conn-123"
            assert result["values"][0]["type"] == "bigquery"

            # Verify request was made correctly
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/data-connections" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_list_data_connections_with_pagination(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing data connections with pagination parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": "next-cursor", "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_data_connections

            result_str = await list_hex_data_connections(limit=10, after="cursor-123")
            result = json.loads(result_str)

            assert result["pagination"]["next"] == "next-cursor"

            # Verify parameters were passed
            params = mock_httpx_client.request.call_args[1]["params"]
            assert params["limit"] == 10
            assert params["after"] == "cursor-123"


@pytest.mark.asyncio
async def test_list_data_connections_with_sort(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test listing data connections with sorting parameters."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "values": [],
        "pagination": {"next": None, "previous": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_data_connections

            await list_hex_data_connections(sort_by="NAME", sort_direction="asc")

            # Verify parameters were passed
            params = mock_httpx_client.request.call_args[1]["params"]
            assert params["sortBy"] == "NAME"
            assert params["sortDirection"] == "asc"


@pytest.mark.asyncio
async def test_list_data_connections_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_data_connections with 403 forbidden error."""
    error_response = mock_httpx_response(403, {"message": "Forbidden", "statusCode": 403})
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_data_connections

            with pytest.raises(HTTPStatusError) as exc_info:
                await list_hex_data_connections()

            assert exc_info.value.response.status_code == 403


@pytest.mark.asyncio
async def test_get_data_connection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test getting a specific data connection."""
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "conn-123",
        "name": "Production BigQuery",
        "type": "bigquery",
        "description": "Production data warehouse",
        "connectionDetails": {
            "bigquery": {
                "projectId": "my-project"
            }
        },
        "connectViaSsh": False,
        "includeMagic": True,
        "allowWritebackCells": False,
        "sharing": {}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_data_connection

            result_str = await get_hex_data_connection(connection_id="conn-123")
            result = json.loads(result_str)

            assert result["id"] == "conn-123"
            assert result["name"] == "Production BigQuery"
            assert result["type"] == "bigquery"
            assert result["includeMagic"] is True

            # Verify request
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "GET"
            assert "/v1/data-connections/conn-123" in call_args[1]["url"]


@pytest.mark.asyncio
async def test_get_data_connection_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test get_data_connection with 404 not found error."""
    error_response = mock_httpx_response(404, {"message": "Not found", "statusCode": 404})
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import get_hex_data_connection

            with pytest.raises(HTTPStatusError) as exc_info:
                await get_hex_data_connection(connection_id="nonexistent")

            assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_create_data_connection_simple(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a simple data connection."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-456",
        "name": "Test BigQuery",
        "type": "bigquery",
        "connectionDetails": {"bigquery": {"projectId": "test-project"}},
        "includeMagic": True
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_data_connection

            result_str = await create_hex_data_connection(
                name="Test BigQuery",
                connection_type="bigquery",
                connection_details={
                    "bigquery": {
                        "projectId": "test-project",
                        "serviceAccountJsonConfig": "{}"
                    }
                }
            )
            result = json.loads(result_str)

            assert result["name"] == "Test BigQuery"
            assert result["type"] == "bigquery"

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["name"] == "Test BigQuery"
            assert body["type"] == "bigquery"
            assert "connectionDetails" in body


@pytest.mark.asyncio
async def test_create_data_connection_with_options(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a data connection with additional options."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-789",
        "name": "Advanced Snowflake",
        "type": "snowflake",
        "description": "Advanced configuration"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_data_connection

            result_str = await create_hex_data_connection(
                name="Advanced Snowflake",
                connection_type="snowflake",
                connection_details={"snowflake": {"account": "test"}},
                description="Advanced configuration",
                include_magic=True,
                allow_writeback_cells=True
            )
            result = json.loads(result_str)

            assert result["name"] == "Advanced Snowflake"

            # Verify request body includes all options
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["description"] == "Advanced configuration"
            assert body["includeMagic"] is True
            assert body["allowWritebackCells"] is True


@pytest.mark.asyncio
async def test_create_data_connection_invalid_type(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test creating a data connection with invalid type."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_data_connection

            with pytest.raises(ValueError) as exc_info:
                await create_hex_data_connection(
                    name="Invalid Connection",
                    connection_type="invalid_type",
                    connection_details={}
                )

            assert "Invalid connection_type" in str(exc_info.value)
            assert "invalid_type" in str(exc_info.value)


@pytest.mark.asyncio
async def test_create_data_connection_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test create_data_connection with 403 forbidden error."""
    error_response = mock_httpx_response(403, {"message": "Forbidden", "statusCode": 403})
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import create_hex_data_connection

            with pytest.raises(HTTPStatusError) as exc_info:
                await create_hex_data_connection(
                    name="Test",
                    connection_type="bigquery",
                    connection_details={"bigquery": {}}
                )

            assert exc_info.value.response.status_code == 403


@pytest.mark.asyncio
async def test_update_data_connection_name(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating a data connection's name."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "name": "Updated Connection Name"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                name="Updated Connection Name"
            )
            result = json.loads(result_str)

            assert result["name"] == "Updated Connection Name"

            # Verify request
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["method"] == "PATCH"
            assert "/v1/data-connections/conn-123" in call_args[1]["url"]
            body = call_args[1]["json"]
            assert body["name"] == "Updated Connection Name"


@pytest.mark.asyncio
async def test_update_data_connection_description(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating a data connection's description."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "description": "New description"
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                description="New description"
            )
            result = json.loads(result_str)

            assert result["description"] == "New description"

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["description"] == "New description"


@pytest.mark.asyncio
async def test_update_data_connection_settings(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating data connection settings."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "includeMagic": False,
        "allowWritebackCells": True
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                include_magic=False,
                allow_writeback_cells=True
            )
            result = json.loads(result_str)

            assert result["includeMagic"] is False
            assert result["allowWritebackCells"] is True

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["includeMagic"] is False
            assert body["allowWritebackCells"] is True


@pytest.mark.asyncio
async def test_update_data_connection_sharing(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating data connection sharing settings."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "sharing": {"workspace": {"members": "CAN_USE"}}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                sharing={
                    "workspace": {"members": "CAN_USE"}
                }
            )
            result = json.loads(result_str)

            assert "sharing" in result

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "sharing" in body
            assert body["sharing"]["workspace"]["members"] == "CAN_USE"


@pytest.mark.asyncio
async def test_update_data_connection_multiple_fields(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating multiple data connection fields at once."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "name": "Updated Name",
        "description": "Updated description",
        "includeMagic": False
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                name="Updated Name",
                description="Updated description",
                include_magic=False
            )
            result = json.loads(result_str)

            assert result["name"] == "Updated Name"
            assert result["description"] == "Updated description"
            assert result["includeMagic"] is False

            # Verify all fields in request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["name"] == "Updated Name"
            assert body["description"] == "Updated description"
            assert body["includeMagic"] is False


@pytest.mark.asyncio
async def test_update_data_connection_error_no_parameters(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test update_data_connection raises error when no parameters provided."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            with pytest.raises(ValueError) as exc_info:
                await update_hex_data_connection(connection_id="conn-123")

            assert "Must provide at least one parameter to update" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_data_connection_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test update_data_connection with 404 not found error."""
    error_response = mock_httpx_response(404, {"message": "Not found", "statusCode": 404})
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_data_connection(
                    connection_id="nonexistent",
                    name="New Name"
                )

            assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_update_data_connection_connection_details(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating connection details."""
    mock_httpx_client.request.return_value = mock_httpx_response(201, {
        "id": "conn-123",
        "connectionDetails": {"postgres": {"host": "new-host"}}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_data_connection

            result_str = await update_hex_data_connection(
                connection_id="conn-123",
                connection_details={"postgres": {"host": "new-host", "port": 5432}}
            )
            result = json.loads(result_str)

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "connectionDetails" in body
            assert body["connectionDetails"]["postgres"]["host"] == "new-host"
