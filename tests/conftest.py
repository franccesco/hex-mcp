"""
Test fixtures for hex-mcp tests.

CRITICAL: All tests MUST mock authentication variables.
Never use real credentials in tests.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch


@pytest.fixture
def mock_api_key():
    """Mock API key - NEVER use real credentials in tests."""
    return "mock_hex_api_key_for_testing_12345"


@pytest.fixture
def mock_api_url():
    """Mock API URL for testing."""
    return "https://api.mock.hex.tech"


@pytest.fixture
def mock_httpx_response():
    """Create a mock HTTP response object."""
    def _make_response(status_code=200, json_data=None):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = json_data or {}

        # Mock raise_for_status
        def raise_for_status():
            if status_code >= 400:
                from httpx import HTTPStatusError
                raise HTTPStatusError(
                    f"HTTP {status_code}",
                    request=Mock(),
                    response=response
                )
        response.raise_for_status = raise_for_status

        return response
    return _make_response


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Mock httpx.AsyncClient to prevent real HTTP requests.

    Returns a context manager that yields an AsyncMock client.
    """
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_instance = AsyncMock()

        # Make the context manager return the mock instance
        mock_client_class.return_value.__aenter__.return_value = mock_instance
        mock_client_class.return_value.__aexit__.return_value = None

        # Default to successful response
        mock_instance.request.return_value = mock_httpx_response(200, {})

        yield mock_instance


@pytest.fixture
def mock_cell_response():
    """Sample cell response data for testing."""
    return {
        "id": "cell-test-uuid-123",
        "staticId": "static-cell-id-456",
        "cellType": "SQL",
        "label": "Test Query",
        "dataConnectionId": "conn-uuid-789",
        "contents": {
            "sqlCell": {"source": "SELECT 1 as test_column"},
            "codeCell": None
        }
    }


@pytest.fixture
def mock_code_cell_response():
    """Sample CODE cell response for testing."""
    return {
        "id": "cell-code-uuid-456",
        "staticId": "static-code-id-789",
        "cellType": "CODE",
        "label": "Test Code",
        "dataConnectionId": None,
        "contents": {
            "sqlCell": None,
            "codeCell": {"source": "print('hello world')"}
        }
    }


@pytest.fixture
def mock_markdown_cell_response():
    """Sample MARKDOWN cell response (content not exposed)."""
    return {
        "id": "cell-markdown-uuid-789",
        "staticId": "static-markdown-id-012",
        "cellType": "MARKDOWN",
        "label": "Documentation",
        "dataConnectionId": None,
        "contents": {
            "sqlCell": None,
            "codeCell": None
        }
    }


@pytest.fixture
def mock_cells_list_response(mock_cell_response, mock_code_cell_response, mock_markdown_cell_response):
    """Sample cells list response with pagination."""
    return {
        "values": [
            mock_cell_response,
            mock_code_cell_response,
            mock_markdown_cell_response
        ],
        "pagination": {
            "next": None,
            "previous": None
        }
    }


@pytest.fixture
def mock_cells_list_with_pagination():
    """Sample cells list response with pagination cursors."""
    return {
        "values": [
            {
                "id": f"cell-{i}",
                "staticId": f"static-{i}",
                "cellType": "SQL",
                "label": f"Query {i}",
                "dataConnectionId": "conn-123",
                "contents": {
                    "sqlCell": {"source": f"SELECT {i}"},
                    "codeCell": None
                }
            }
            for i in range(50)
        ],
        "pagination": {
            "next": "cursor-next-abc123",
            "previous": None
        }
    }


# Integration test fixtures (only loaded when integration tests run)

@pytest.fixture(scope="session")
def test_hex_credentials():
    """Load test Hex credentials from environment.

    These should be for a dedicated TEST workspace only.
    NEVER use production credentials.
    """
    api_key = os.getenv("HEX_TEST_API_KEY")
    api_url = os.getenv("HEX_TEST_API_URL", "https://app.hex.tech")

    if not api_key:
        pytest.skip("HEX_TEST_API_KEY not set - skipping integration tests")

    # Basic sanity check - verify this is not a production key
    if "prod" in api_key.lower() or "production" in api_key.lower():
        raise ValueError(
            "Production key detected in tests! "
            "Use a dedicated test workspace API key."
        )

    return {"api_key": api_key, "api_url": api_url}


@pytest.fixture(scope="session")
def test_hex_project_id():
    """Test project ID - must be in test workspace."""
    project_id = os.getenv("HEX_TEST_PROJECT_ID")
    if not project_id:
        pytest.skip("HEX_TEST_PROJECT_ID not set - skipping integration tests")
    return project_id


@pytest.fixture(scope="session")
def test_hex_cell_id():
    """Test cell ID - must be safe to modify."""
    cell_id = os.getenv("HEX_TEST_CELL_ID")
    if not cell_id:
        pytest.skip("HEX_TEST_CELL_ID not set - skipping integration tests")
    return cell_id


# Pytest configuration

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require test API key)"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests (require full test workspace)"
    )
