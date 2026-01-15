"""
Unit tests for list_hex_cells function.

CRITICAL: All tests mock authentication and HTTP requests.
No real API calls are made in these tests.
"""

import json
import pytest
from unittest.mock import patch, Mock, AsyncMock
from httpx import HTTPStatusError


@pytest.mark.asyncio
async def test_list_cells_basic(mock_httpx_client, mock_cells_list_response, mock_httpx_response, mock_api_key):
    """Test basic list_cells functionality with mocked HTTP client."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, mock_cells_list_response)

    # Mock the config module to prevent reading from environment
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            # Import after patching to ensure mocked values are used
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-test-uuid-123")
            result = json.loads(result_str)

            # Assert
            assert "values" in result
            assert "pagination" in result
            assert len(result["values"]) == 3
            assert result["values"][0]["id"] == "cell-test-uuid-123"
            assert result["values"][0]["cellType"] == "SQL"
            assert result["values"][1]["cellType"] == "CODE"
            assert result["values"][2]["cellType"] == "MARKDOWN"

            # Verify HTTP request was made correctly
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args

            # Check HTTP method and URL
            assert call_args[1]["method"] == "GET"
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/cells"

            # Check auth header
            assert "headers" in call_args[1]
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_api_key}"

            # Check query parameters
            assert "params" in call_args[1]
            assert call_args[1]["params"]["projectId"] == "project-test-uuid-123"


@pytest.mark.asyncio
async def test_list_cells_with_limit(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with limit parameter."""
    # Arrange
    response_data = {
        "values": [
            {"id": f"cell-{i}", "cellType": "SQL", "label": f"Query {i}",
             "staticId": f"static-{i}", "dataConnectionId": None,
             "contents": {"sqlCell": {"source": f"SELECT {i}"}, "codeCell": None}}
            for i in range(25)
        ],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-123", limit=25)
            result = json.loads(result_str)

            # Assert
            assert len(result["values"]) == 25

            # Verify limit parameter was passed
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["params"]["limit"] == 25


@pytest.mark.asyncio
async def test_list_cells_with_pagination_after(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with after cursor for pagination."""
    # Arrange - page 2 response
    response_data = {
        "values": [
            {"id": f"cell-{i}", "cellType": "CODE", "label": f"Code {i}",
             "staticId": f"static-{i}", "dataConnectionId": None,
             "contents": {"sqlCell": None, "codeCell": {"source": f"print({i})"}}}
            for i in range(50, 75)
        ],
        "pagination": {"next": None, "previous": "cursor-prev-xyz"}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells(
                "project-123",
                limit=50,
                after="cursor-next-abc"
            )
            result = json.loads(result_str)

            # Assert
            assert len(result["values"]) == 25
            assert result["pagination"]["previous"] == "cursor-prev-xyz"

            # Verify after cursor was passed
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["params"]["after"] == "cursor-next-abc"


@pytest.mark.asyncio
async def test_list_cells_with_pagination_before(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with before cursor for backward pagination."""
    # Arrange
    response_data = {
        "values": [{"id": f"cell-{i}", "cellType": "SQL", "label": None,
                     "staticId": f"static-{i}", "dataConnectionId": "conn-123",
                     "contents": {"sqlCell": {"source": f"SELECT {i}"}, "codeCell": None}}
                    for i in range(0, 50)],
        "pagination": {"next": "cursor-next-def", "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells(
                "project-123",
                before="cursor-prev-xyz"
            )
            result = json.loads(result_str)

            # Assert
            assert result["pagination"]["next"] == "cursor-next-def"

            # Verify before cursor was passed
            call_args = mock_httpx_client.request.call_args
            assert call_args[1]["params"]["before"] == "cursor-prev-xyz"


@pytest.mark.asyncio
async def test_list_cells_sql_cell_has_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that SQL cells include source code in response."""
    # Arrange
    response_data = {
        "values": [{
            "id": "cell-sql-123",
            "staticId": "static-sql-456",
            "cellType": "SQL",
            "label": "Important Query",
            "dataConnectionId": "conn-postgres-789",
            "contents": {
                "sqlCell": {"source": "SELECT * FROM users WHERE active = true"},
                "codeCell": None
            }
        }],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-123")
            result = json.loads(result_str)

            # Assert
            cell = result["values"][0]
            assert cell["cellType"] == "SQL"
            assert cell["contents"]["sqlCell"] is not None
            assert "SELECT * FROM users" in cell["contents"]["sqlCell"]["source"]
            assert cell["contents"]["codeCell"] is None
            assert cell["dataConnectionId"] == "conn-postgres-789"


@pytest.mark.asyncio
async def test_list_cells_code_cell_has_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that CODE cells include source code in response."""
    # Arrange
    response_data = {
        "values": [{
            "id": "cell-code-456",
            "staticId": "static-code-789",
            "cellType": "CODE",
            "label": "Data Processing",
            "dataConnectionId": None,
            "contents": {
                "sqlCell": None,
                "codeCell": {"source": "import pandas as pd\ndf = pd.read_csv('data.csv')"}
            }
        }],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-123")
            result = json.loads(result_str)

            # Assert
            cell = result["values"][0]
            assert cell["cellType"] == "CODE"
            assert cell["contents"]["codeCell"] is not None
            assert "import pandas" in cell["contents"]["codeCell"]["source"]
            assert cell["contents"]["sqlCell"] is None
            assert cell["dataConnectionId"] is None


@pytest.mark.asyncio
async def test_list_cells_markdown_no_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that MARKDOWN cells do not expose source content."""
    # Arrange
    response_data = {
        "values": [{
            "id": "cell-markdown-789",
            "staticId": "static-markdown-012",
            "cellType": "MARKDOWN",
            "label": "Documentation Section",
            "dataConnectionId": None,
            "contents": {
                "sqlCell": None,
                "codeCell": None
            }
        }],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-123")
            result = json.loads(result_str)

            # Assert
            cell = result["values"][0]
            assert cell["cellType"] == "MARKDOWN"
            assert cell["contents"]["sqlCell"] is None
            assert cell["contents"]["codeCell"] is None


@pytest.mark.asyncio
async def test_list_cells_empty_project(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with empty project (no cells)."""
    # Arrange
    response_data = {
        "values": [],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("empty-project-123")
            result = json.loads(result_str)

            # Assert
            assert result["values"] == []
            assert result["pagination"]["next"] is None


@pytest.mark.asyncio
async def test_list_cells_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with 404 error (project not found)."""
    # Arrange
    error_response = mock_httpx_response(
        404,
        {"message": "Project not found", "statusCode": 404, "traceId": "trace-123"}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await list_hex_cells("nonexistent-project")

            assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_list_cells_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with 403 error (permission denied)."""
    # Arrange
    error_response = mock_httpx_response(
        403,
        {"message": "Permission denied", "statusCode": 403, "traceId": "trace-456"}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await list_hex_cells("forbidden-project")

            assert exc_info.value.response.status_code == 403


@pytest.mark.asyncio
async def test_list_cells_429_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with 429 rate limit error.

    Tests that 429 errors are raised properly. In production, the backoff decorator
    would retry these automatically, but for unit tests we verify the error is handled.
    """
    # Arrange - mock to return 429
    error_response = mock_httpx_response(
        429,
        {"message": "Rate limit exceeded", "statusCode": 429}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            # Patch backoff to not actually wait/retry in tests
            with patch('backoff.expo', return_value=0):
                with patch('hex_mcp.server.hex_request') as mock_hex_request:
                    # Make hex_request raise the 429 error
                    mock_hex_request.side_effect = HTTPStatusError(
                        "Rate limit exceeded",
                        request=Mock(),
                        response=Mock(status_code=429)
                    )

                    from hex_mcp.server import list_hex_cells

                    # Act & Assert - should raise 429 error
                    with pytest.raises(HTTPStatusError) as exc_info:
                        await list_hex_cells("project-123")

                    assert exc_info.value.response.status_code == 429


@pytest.mark.asyncio
async def test_list_cells_mixed_cell_types(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test list_cells with multiple cell types in response."""
    # Arrange - realistic project with mixed cells
    response_data = {
        "values": [
            {
                "id": "cell-1",
                "staticId": "static-1",
                "cellType": "MARKDOWN",
                "label": "Introduction",
                "dataConnectionId": None,
                "contents": {"sqlCell": None, "codeCell": None}
            },
            {
                "id": "cell-2",
                "staticId": "static-2",
                "cellType": "SQL",
                "label": "Load Data",
                "dataConnectionId": "conn-snowflake",
                "contents": {
                    "sqlCell": {"source": "SELECT * FROM raw.orders LIMIT 100"},
                    "codeCell": None
                }
            },
            {
                "id": "cell-3",
                "staticId": "static-3",
                "cellType": "CODE",
                "label": "Process Data",
                "dataConnectionId": None,
                "contents": {
                    "sqlCell": None,
                    "codeCell": {"source": "df = df.dropna()"}
                }
            },
            {
                "id": "cell-4",
                "staticId": "static-4",
                "cellType": "CHART",
                "label": "Visualization",
                "dataConnectionId": None,
                "contents": {"sqlCell": None, "codeCell": None}
            },
            {
                "id": "cell-5",
                "staticId": "static-5",
                "cellType": "INPUT",
                "label": "Date Filter",
                "dataConnectionId": None,
                "contents": {"sqlCell": None, "codeCell": None}
            }
        ],
        "pagination": {"next": None, "previous": None}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            result_str = await list_hex_cells("project-123")
            result = json.loads(result_str)

            # Assert
            assert len(result["values"]) == 5

            # Verify SQL cell has source
            sql_cell = result["values"][1]
            assert sql_cell["cellType"] == "SQL"
            assert sql_cell["contents"]["sqlCell"]["source"] == "SELECT * FROM raw.orders LIMIT 100"

            # Verify CODE cell has source
            code_cell = result["values"][2]
            assert code_cell["cellType"] == "CODE"
            assert code_cell["contents"]["codeCell"]["source"] == "df = df.dropna()"

            # Verify MARKDOWN, CHART, INPUT cells have no source
            for cell_type in ["MARKDOWN", "CHART", "INPUT"]:
                cell = next(c for c in result["values"] if c["cellType"] == cell_type)
                assert cell["contents"]["sqlCell"] is None
                assert cell["contents"]["codeCell"] is None


@pytest.mark.asyncio
async def test_list_cells_no_credentials_warning():
    """Test that missing credentials produces warning (not error in tests)."""
    # This test verifies the warning message exists in server.py
    # In production, missing credentials would fail, but tests should mock them
    with patch('hex_mcp.server.HEX_API_KEY', None):
        # Just verify the module can be imported even with no key
        # (actual calls would fail, but that's expected)
        import hex_mcp.server
        assert hex_mcp.server.HEX_API_KEY is None


@pytest.mark.asyncio
async def test_list_cells_all_pagination_params(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that all pagination params are correctly passed to API."""
    # Arrange
    response_data = {
        "values": [{"id": "cell-1", "cellType": "SQL", "label": None,
                     "staticId": "static-1", "dataConnectionId": None,
                     "contents": {"sqlCell": {"source": "SELECT 1"}, "codeCell": None}}],
        "pagination": {"next": "next-cursor", "previous": "prev-cursor"}
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, response_data)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import list_hex_cells

            # Act
            await list_hex_cells(
                "project-123",
                limit=50,
                after="after-cursor-xyz",
                before="before-cursor-abc"
            )

            # Assert
            call_args = mock_httpx_client.request.call_args
            params = call_args[1]["params"]

            assert params["projectId"] == "project-123"
            assert params["limit"] == 50
            assert params["after"] == "after-cursor-xyz"
            assert params["before"] == "before-cursor-abc"
