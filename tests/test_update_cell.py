"""
Unit tests for update_hex_cell function.

CRITICAL: All tests mock authentication and HTTP requests.
No real API calls are made in these tests.
"""

import json
import pytest
from unittest.mock import patch, Mock
from httpx import HTTPStatusError


@pytest.mark.asyncio
async def test_update_sql_cell_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating SQL cell source code."""
    # Arrange
    updated_cell = {
        "id": "cell-sql-123",
        "staticId": "static-sql-456",
        "cellType": "SQL",
        "label": "Updated Query",
        "dataConnectionId": "conn-postgres-789",
        "contents": {
            "sqlCell": {"source": "SELECT * FROM updated_table"},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-sql-123",
                sql_source="SELECT * FROM updated_table"
            )
            result = json.loads(result_str)

            # Assert
            assert result["id"] == "cell-sql-123"
            assert result["contents"]["sqlCell"]["source"] == "SELECT * FROM updated_table"

            # Verify HTTP request
            mock_httpx_client.request.assert_called_once()
            call_args = mock_httpx_client.request.call_args

            # Check method and URL
            assert call_args[1]["method"] == "PATCH"
            assert call_args[1]["url"] == "https://api.mock.hex.tech/v1/cells/cell-sql-123"

            # Check auth header
            assert call_args[1]["headers"]["Authorization"] == f"Bearer {mock_api_key}"

            # Check request body structure (discriminated union)
            body = call_args[1]["json"]
            assert "contents" in body
            assert "sqlCell" in body["contents"]
            assert body["contents"]["sqlCell"]["source"] == "SELECT * FROM updated_table"
            assert "codeCell" not in body["contents"]


@pytest.mark.asyncio
async def test_update_code_cell_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating CODE cell source code."""
    # Arrange
    updated_cell = {
        "id": "cell-code-456",
        "staticId": "static-code-789",
        "cellType": "CODE",
        "label": "Updated Code",
        "dataConnectionId": None,
        "contents": {
            "sqlCell": None,
            "codeCell": {"source": "import numpy as np\nprint(np.array([1,2,3]))"}
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-code-456",
                code_source="import numpy as np\nprint(np.array([1,2,3]))"
            )
            result = json.loads(result_str)

            # Assert
            assert result["cellType"] == "CODE"
            assert "numpy" in result["contents"]["codeCell"]["source"]

            # Verify request body
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "contents" in body
            assert "codeCell" in body["contents"]
            assert "import numpy" in body["contents"]["codeCell"]["source"]
            assert "sqlCell" not in body["contents"]


@pytest.mark.asyncio
async def test_update_sql_cell_data_connection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating SQL cell data connection without changing source."""
    # Arrange
    updated_cell = {
        "id": "cell-sql-123",
        "staticId": "static-sql-456",
        "cellType": "SQL",
        "label": "Query",
        "dataConnectionId": "conn-snowflake-new",
        "contents": {
            "sqlCell": {"source": "SELECT * FROM table"},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-sql-123",
                data_connection_id="conn-snowflake-new"
            )
            result = json.loads(result_str)

            # Assert
            assert result["dataConnectionId"] == "conn-snowflake-new"

            # Verify request body - should only contain dataConnectionId
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "dataConnectionId" in body
            assert body["dataConnectionId"] == "conn-snowflake-new"
            assert "contents" not in body  # No source change


@pytest.mark.asyncio
async def test_update_sql_cell_source_and_connection(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating both SQL source and data connection in one call."""
    # Arrange
    updated_cell = {
        "id": "cell-sql-123",
        "staticId": "static-sql-456",
        "cellType": "SQL",
        "label": "Migrated Query",
        "dataConnectionId": "conn-bigquery-prod",
        "contents": {
            "sqlCell": {"source": "SELECT * FROM prod.customers"},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-sql-123",
                sql_source="SELECT * FROM prod.customers",
                data_connection_id="conn-bigquery-prod"
            )
            result = json.loads(result_str)

            # Assert
            assert result["contents"]["sqlCell"]["source"] == "SELECT * FROM prod.customers"
            assert result["dataConnectionId"] == "conn-bigquery-prod"

            # Verify request body contains both
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "contents" in body
            assert "sqlCell" in body["contents"]
            assert "dataConnectionId" in body
            assert body["dataConnectionId"] == "conn-bigquery-prod"


@pytest.mark.asyncio
async def test_update_cell_error_both_sources(mock_api_key):
    """Test error when providing both sql_source and code_source."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await update_hex_cell(
                    cell_id="cell-123",
                    sql_source="SELECT 1",
                    code_source="print(1)"
                )

            assert "Cannot update both sql_source and code_source" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_cell_error_no_parameters(mock_api_key):
    """Test error when providing no update parameters."""
    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act & Assert
            with pytest.raises(ValueError) as exc_info:
                await update_hex_cell(cell_id="cell-123")

            assert "Must provide at least one of" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_cell_404_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 404 error when cell doesn't exist."""
    # Arrange
    error_response = mock_httpx_response(
        404,
        {"message": "Cell not found", "statusCode": 404, "traceId": "trace-123"}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_cell(
                    cell_id="nonexistent-cell",
                    sql_source="SELECT 1"
                )

            assert exc_info.value.response.status_code == 404


@pytest.mark.asyncio
async def test_update_cell_403_error(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 403 error when insufficient permissions."""
    # Arrange
    error_response = mock_httpx_response(
        403,
        {"message": "Permission denied - EDIT_PROJECT_CONTENTS required", "statusCode": 403}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_cell(
                    cell_id="cell-123",
                    sql_source="SELECT * FROM sensitive_data"
                )

            assert exc_info.value.response.status_code == 403


@pytest.mark.asyncio
async def test_update_cell_400_error_wrong_cell_type(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test 400 error when trying to update wrong cell type (e.g., MARKDOWN)."""
    # Arrange
    error_response = mock_httpx_response(
        400,
        {"message": "Cannot update MARKDOWN cell type", "statusCode": 400}
    )
    mock_httpx_client.request.return_value = error_response

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act & Assert
            with pytest.raises(HTTPStatusError) as exc_info:
                await update_hex_cell(
                    cell_id="markdown-cell-123",
                    sql_source="SELECT 1"  # Trying to add SQL to MARKDOWN cell
                )

            assert exc_info.value.response.status_code == 400


@pytest.mark.asyncio
async def test_update_sql_cell_multiline_query(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating SQL cell with complex multiline query."""
    # Arrange
    complex_query = """
    WITH customer_orders AS (
        SELECT
            customer_id,
            COUNT(*) as order_count,
            SUM(total_amount) as lifetime_value
        FROM orders
        WHERE status = 'completed'
        GROUP BY customer_id
    )
    SELECT
        c.customer_name,
        co.order_count,
        co.lifetime_value
    FROM customers c
    INNER JOIN customer_orders co ON c.id = co.customer_id
    WHERE co.lifetime_value > 1000
    ORDER BY co.lifetime_value DESC
    """

    updated_cell = {
        "id": "cell-sql-complex",
        "staticId": "static-complex",
        "cellType": "SQL",
        "label": "Customer LTV Analysis",
        "dataConnectionId": "conn-warehouse",
        "contents": {
            "sqlCell": {"source": complex_query},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-sql-complex",
                sql_source=complex_query
            )
            result = json.loads(result_str)

            # Assert
            assert "WITH customer_orders" in result["contents"]["sqlCell"]["source"]
            assert "lifetime_value" in result["contents"]["sqlCell"]["source"]

            # Verify the full query was sent
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["contents"]["sqlCell"]["source"] == complex_query


@pytest.mark.asyncio
async def test_update_code_cell_with_special_characters(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating CODE cell with special characters and formatting."""
    # Arrange
    code_with_special_chars = '''
df = pd.read_csv("data.csv")
# Filter where name contains "O'Brien"
filtered = df[df['name'].str.contains("O'Brien", na=False)]
print(f"Found {len(filtered)} rows with O'Brien")
'''

    updated_cell = {
        "id": "cell-code-special",
        "staticId": "static-special",
        "cellType": "CODE",
        "label": "Data Processing",
        "dataConnectionId": None,
        "contents": {
            "sqlCell": None,
            "codeCell": {"source": code_with_special_chars}
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-code-special",
                code_source=code_with_special_chars
            )
            result = json.loads(result_str)

            # Assert - special characters preserved
            assert "O'Brien" in result["contents"]["codeCell"]["source"]
            assert '"data.csv"' in result["contents"]["codeCell"]["source"]


@pytest.mark.asyncio
async def test_update_cell_returns_full_cell_object(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that update returns complete cell object with all fields."""
    # Arrange
    full_cell = {
        "id": "cell-full-123",
        "staticId": "static-full-456",
        "cellType": "SQL",
        "label": "Complete Cell",
        "dataConnectionId": "conn-123",
        "contents": {
            "sqlCell": {"source": "SELECT * FROM table"},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, full_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-full-123",
                sql_source="SELECT * FROM table"
            )
            result = json.loads(result_str)

            # Assert - all fields present
            assert "id" in result
            assert "staticId" in result
            assert "cellType" in result
            assert "label" in result
            assert "dataConnectionId" in result
            assert "contents" in result
            assert result["id"] == "cell-full-123"


@pytest.mark.asyncio
async def test_update_sql_cell_empty_source(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test updating SQL cell with empty source (clearing the query)."""
    # Arrange
    updated_cell = {
        "id": "cell-sql-123",
        "staticId": "static-sql-456",
        "cellType": "SQL",
        "label": "Cleared Query",
        "dataConnectionId": "conn-123",
        "contents": {
            "sqlCell": {"source": ""},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            result_str = await update_hex_cell(
                cell_id="cell-sql-123",
                sql_source=""
            )
            result = json.loads(result_str)

            # Assert
            assert result["contents"]["sqlCell"]["source"] == ""

            # Verify empty string was sent (not None)
            body = mock_httpx_client.request.call_args[1]["json"]
            assert body["contents"]["sqlCell"]["source"] == ""


@pytest.mark.asyncio
async def test_update_cell_request_body_structure(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that request body follows exact API schema."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "cell-123", "staticId": "static-123", "cellType": "SQL",
        "label": "Test", "dataConnectionId": "conn-new",
        "contents": {"sqlCell": {"source": "SELECT 1"}, "codeCell": None}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act - update both source and connection
            await update_hex_cell(
                cell_id="cell-123",
                sql_source="SELECT 1",
                data_connection_id="conn-new"
            )

            # Assert - verify exact structure
            body = mock_httpx_client.request.call_args[1]["json"]

            # Must have contents with nested structure
            assert isinstance(body["contents"], dict)
            assert isinstance(body["contents"]["sqlCell"], dict)
            assert "source" in body["contents"]["sqlCell"]

            # Must have dataConnectionId at top level
            assert "dataConnectionId" in body

            # Should NOT have extra fields
            assert len(body) == 2  # Only contents and dataConnectionId
            assert len(body["contents"]) == 1  # Only sqlCell


@pytest.mark.asyncio
async def test_update_code_cell_only_source_in_body(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that CODE cell updates don't include dataConnectionId."""
    # Arrange
    mock_httpx_client.request.return_value = mock_httpx_response(200, {
        "id": "cell-code-123", "staticId": "static-code", "cellType": "CODE",
        "label": "Code", "dataConnectionId": None,
        "contents": {"sqlCell": None, "codeCell": {"source": "print('test')"}}
    })

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act
            await update_hex_cell(
                cell_id="cell-code-123",
                code_source="print('test')"
            )

            # Assert - body should only have contents, not dataConnectionId
            body = mock_httpx_client.request.call_args[1]["json"]
            assert "contents" in body
            assert "codeCell" in body["contents"]
            assert "dataConnectionId" not in body  # CODE cells don't use connections


@pytest.mark.asyncio
async def test_update_cell_preserves_cell_metadata(mock_httpx_client, mock_httpx_response, mock_api_key):
    """Test that updating cell preserves label and other metadata."""
    # Arrange - API returns cell with original label
    updated_cell = {
        "id": "cell-123",
        "staticId": "static-123",
        "cellType": "SQL",
        "label": "Original Label Not Changed",  # Label preserved
        "dataConnectionId": "conn-123",
        "contents": {
            "sqlCell": {"source": "SELECT * FROM new_table"},
            "codeCell": None
        }
    }
    mock_httpx_client.request.return_value = mock_httpx_response(200, updated_cell)

    with patch('hex_mcp.server.HEX_API_KEY', mock_api_key):
        with patch('hex_mcp.server.HEX_API_BASE_URL', 'https://api.mock.hex.tech'):
            from hex_mcp.server import update_hex_cell

            # Act - only update source
            result_str = await update_hex_cell(
                cell_id="cell-123",
                sql_source="SELECT * FROM new_table"
            )
            result = json.loads(result_str)

            # Assert - label unchanged
            assert result["label"] == "Original Label Not Changed"
            assert result["staticId"] == "static-123"
