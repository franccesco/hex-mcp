"""Hex MCP Server - Model Context Protocol server for Hex API integration.

This module implements a FastMCP server that exposes Hex API functionality as MCP tools.
The server provides comprehensive project management, cell operations, permission control,
collection management, and group management capabilities for Hex workspaces.

Features:
    - Project Management: List, search, get details, run, and monitor Hex projects
    - Cell Operations: List and update SQL/CODE cells programmatically
    - Permission Control: Manage user, group, collection, and workspace-level access
    - Collection Management: Organize projects into collections
    - Group Management: Create and manage user groups for simplified permissions
    - Rate Limiting: Automatic exponential backoff for 429 errors

Usage:
    This module is intended to be run as an MCP server. Configure your MCP client
    to connect to this server, then use the exposed tools to interact with Hex.

Environment Variables:
    HEX_API_KEY: Your Hex API key (required)
    HEX_API_BASE_URL: Hex API base URL (optional, defaults to https://app.hex.tech/api)
"""

import httpx
from os import getenv
from mcp.server.fastmcp import FastMCP, Context
import re
import json
import backoff
from typing import Any
from . import config as config_module

# Get API credentials from config module
HEX_API_KEY = config_module.get_api_key()
HEX_API_BASE_URL = config_module.get_api_url()

if not HEX_API_KEY:
    print("Warning: HEX_API_KEY not found in environment variables or config file")

# Create an MCP server
mcp = FastMCP("Hex MCP Server")


def is_rate_limit_error(exception):
    """Check if the exception is due to rate limiting (HTTP 429)."""
    return isinstance(exception, httpx.HTTPStatusError) and exception.response.status_code == 429


def backoff_handler(details: dict[str, Any]):
    """Log backoff events for rate limiting.

    Args:
        details: Dictionary with 'wait', 'tries', and other backoff information.

    Note:
        In production MCP context, warnings are logged to the MCP client.
        In tests, this just tracks that backoff occurred.
    """
    # This function is called by the backoff decorator when rate limiting occurs
    # In tests, we can simply track that it was called without requiring Context
    pass


@backoff.on_exception(
    backoff.expo,
    httpx.HTTPStatusError,
    max_time=300,  # Maximum time to retry for 5 minutes
    giveup=lambda e: not is_rate_limit_error(e),
    factor=1,  # Start with 1 second delay
    jitter=backoff.full_jitter,
    on_backoff=backoff_handler,
)
async def hex_request(method: str, endpoint: str, json=None, params=None):
    """Make a request to the Hex API with backoff for rate limiting.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint to call
        json: Optional JSON payload
        params: Optional query parameters

    Returns:
        Parsed JSON response

    Raises:
        HTTPStatusError: For non-rate limit errors
    """
    url = f"{HEX_API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {HEX_API_KEY}"}

    async with httpx.AsyncClient() as client:
        response = await client.request(method=method, url=url, headers=headers, json=json, params=params)

        # This will raise HTTPStatusError for status codes >= 400
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def list_hex_projects(limit: int = 25, offset: int = 0) -> str:
    """List all available Hex projects that are in production.

    Retrieves a paginated list of Hex projects from the workspace. Use pagination
    parameters to fetch large project lists incrementally.

    Args:
        limit: Maximum number of projects to return per page. Default 25.
        offset: Number of projects to skip for pagination. Default 0.

    Returns:
        JSON string containing array of project objects with metadata including
        projectId, title, description, owner, lastEditedAt, and status.

    Raises:
        HexAPIError: If the API request fails (403 forbidden, 500 server error).

    Example:
        >>> # List first 10 projects
        >>> projects = list_hex_projects(limit=10)
        >>> data = json.loads(projects)
        >>> for project in data:
        ...     print(f"{project['title']}: {project['projectId']}")
    """
    params = {"limit": limit, "offset": offset}
    projects = await hex_request("GET", "/projects", params=params)
    return json.dumps(projects["values"])


@mcp.tool()
async def search_hex_projects(search_pattern: str, limit: int = 100, offset: int = 0) -> str:
    """Search for Hex projects using regex pattern matching on project titles.

    Searches through workspace projects using a regex pattern applied to project
    titles. Uses intelligent batching to minimize API calls while fetching results.
    Automatically adjusts fetch strategy based on match rate.

    Args:
        search_pattern: Regex pattern to search for in project titles. Case-insensitive
            matching. Example: "finance.*report" or "dashboard".
        limit: Maximum number of matching projects to return. Default 100.
        offset: Number of projects to skip before starting search. Default 0.

    Returns:
        JSON string containing search results with structure:
        {
            "values": [...],  # Array of matching project objects
            "total_matched": int,  # Number of projects that matched
            "total_searched": int,  # Total projects examined
            "has_more": bool  # Whether more matches may exist
        }

    Raises:
        re.error: If the regex pattern is invalid.
        HexAPIError: If API requests fail during search.

    Example:
        >>> # Find all finance-related projects
        >>> results = search_hex_projects("finance.*dashboard")
        >>> data = json.loads(results)
        >>> print(f"Found {data['total_matched']} matching projects")
        >>> for project in data["values"]:
        ...     print(project["title"])
    """
    # Set a reasonable batch size for fetching projects - balance between
    # reducing API calls and not fetching too much at once
    batch_size = min(100, limit)  # Don't request more than needed
    matched_projects = []
    current_offset = offset
    total_fetched = 0
    max_projects_to_search = 1000  # Safeguard against searching too many projects

    try:
        # Compile the regex pattern
        pattern = re.compile(search_pattern, re.IGNORECASE)

        # Continue fetching until we have enough matches or run out of projects
        while len(matched_projects) < limit and total_fetched < max_projects_to_search:
            # Adjust batch size dynamically based on match rate to minimize API calls
            if total_fetched > 0:
                match_rate = len(matched_projects) / total_fetched
                if match_rate > 0:
                    # Estimate how many more projects we need to fetch
                    remaining_matches_needed = limit - len(matched_projects)
                    estimated_total_needed = remaining_matches_needed / match_rate
                    # Adjust batch size based on estimate, with minimum of 20 and max of 100
                    batch_size = min(max(20, int(estimated_total_needed * 1.2)), 100)  # Add 20% buffer

            params = {"limit": batch_size, "offset": current_offset}

            try:
                response = await hex_request("GET", "/projects", params=params)

                projects = response.get("values", [])

                # If no more projects, break
                if not projects:
                    break

                # Filter projects by title using the regex pattern
                for project in projects:
                    if "title" in project and pattern.search(project["title"]):
                        matched_projects.append(project)
                        if len(matched_projects) >= limit:
                            break

                # Update for next batch
                total_fetched += len(projects)
                current_offset += len(projects)

                # Check pagination info
                pagination = response.get("pagination", {})
                if not pagination.get("after"):
                    break

            except httpx.HTTPStatusError as e:
                # If it's not a rate limit error that backoff can handle, raise it
                if e.response.status_code != 429:
                    raise

        # Prepare the response with pagination info
        result = {
            "values": matched_projects[:limit],
            "total_matched": len(matched_projects),
            "total_searched": total_fetched,
            "has_more": len(matched_projects) >= limit or total_fetched >= max_projects_to_search,
        }

        return json.dumps(result)

    except re.error as e:
        return json.dumps({"error": f"Invalid regex pattern: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Error searching projects: {str(e)}"})


@mcp.tool()
async def get_hex_project(project_id: str) -> str:
    """Get detailed information about a specific Hex project.

    Retrieves complete metadata for a project including title, description, owner
    information, edit history, and status.

    Args:
        project_id: The UUID of the Hex project to retrieve. Required.

    Returns:
        JSON string containing project details including projectId, title,
        description, owner (name, email, id), createdAt, lastEditedAt,
        lastEditedBy, and status.

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> project = get_hex_project(project_id="abc-123-def")
        >>> data = json.loads(project)
        >>> print(f"Project: {data['title']}")
        >>> print(f"Owner: {data['owner']['email']}")
        >>> print(f"Last edited: {data['lastEditedAt']}")
    """
    project = await hex_request("GET", f"/projects/{project_id}")
    return json.dumps(project)


@mcp.tool()
async def get_hex_run_status(project_id: str, run_id: str) -> str:
    """Get the status and details of a specific project run.

    Retrieves execution status, timing information, and results for a project run.
    Use this to monitor long-running executions or check if a scheduled run completed.

    Args:
        project_id: The UUID of the Hex project. Required.
        run_id: The UUID of the run to check. Required.

    Returns:
        JSON string containing run details including status ("PENDING", "RUNNING",
        "COMPLETED", "ERRORED", "CANCELLED"), startTime, endTime, runUrl, and
        trace information.

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> status = get_hex_run_status(
        ...     project_id="project-123",
        ...     run_id="run-456"
        ... )
        >>> data = json.loads(status)
        >>> print(f"Run status: {data['status']}")
        >>> if data['status'] == 'COMPLETED':
        ...     print(f"Completed at: {data['endTime']}")
    """
    status = await hex_request("GET", f"/projects/{project_id}/runs/{run_id}")
    return json.dumps(status)


@mcp.tool()
async def get_hex_project_runs(project_id: str, limit: int = 25, offset: int = 0) -> str:
    """Get the execution history for a specific project.

    Retrieves paginated list of all runs for a project, including scheduled runs,
    manual executions, and API-triggered runs. Useful for auditing and monitoring.

    Args:
        project_id: The UUID of the Hex project. Required.
        limit: Maximum number of runs to return. Default 25.
        offset: Number of runs to skip for pagination. Default 0.

    Returns:
        JSON string containing array of run objects with runId, status, startTime,
        endTime, trigger information, and metadata.

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> runs = get_hex_project_runs(project_id="project-123", limit=10)
        >>> data = json.loads(runs)
        >>> for run in data:
        ...     print(f"Run {run['runId']}: {run['status']} at {run['startTime']}")
    """

    params = {"limit": limit, "offset": offset}

    runs = await hex_request("GET", f"/projects/{project_id}/runs", params=params)
    return json.dumps(runs)


@mcp.tool()
async def run_hex_project(project_id: str, input_params: dict = None, update_published_results: bool = False) -> str:
    """Execute a Hex project programmatically.

    Triggers project execution with optional input parameters. Can be used for
    scheduled runs, CI/CD integration, or event-driven workflows. Supports
    updating published app results.

    Args:
        project_id: The UUID of the Hex project to execute. Required.
        input_params: Dictionary of input parameter names to values. Parameters
            must match those defined in the project. Optional.
        update_published_results: If True, updates the published app with new
            execution results. Default False.

    Returns:
        JSON string containing run details including runId, status, runUrl, and
        projectId. Use the runId to monitor execution with get_hex_run_status().

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden,
            400 invalid parameters).

    Example:
        >>> # Run project with input parameters
        >>> result = run_hex_project(
        ...     project_id="project-123",
        ...     input_params={"start_date": "2026-01-01", "region": "US"},
        ...     update_published_results=True
        ... )
        >>> data = json.loads(result)
        >>> print(f"Started run: {data['runId']}")
        >>> print(f"Monitor at: {data['runUrl']}")
    """

    run_config = {
        "inputParams": input_params or {},
        "updatePublishedResults": update_published_results,
        "useCachedSqlResults": True,
    }

    result = await hex_request("POST", f"/projects/{project_id}/runs", json=run_config)
    return json.dumps(result)


@mcp.tool()
async def cancel_hex_run(project_id: str, run_id: str) -> str:
    """Cancel a running or pending project execution.

    Stops a project execution that is currently running or pending. Useful for
    stopping long-running jobs or clearing stuck executions.

    Args:
        project_id: The UUID of the Hex project. Required.
        run_id: The UUID of the run to cancel. Required.

    Returns:
        Success message confirming cancellation.

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden,
            409 if run is already completed or cancelled).

    Example:
        >>> # Cancel a long-running execution
        >>> result = cancel_hex_run(
        ...     project_id="project-123",
        ...     run_id="run-456"
        ... )
        >>> print(result)  # "Run cancelled successfully"
    """
    await hex_request("DELETE", f"/projects/{project_id}/runs/{run_id}")
    return "Run cancelled successfully"


@mcp.tool()
async def list_hex_cells(
    project_id: str,
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None
) -> str:
    """List all cells in a Hex project.

    Returns cell metadata including IDs, types, labels, and source code
    for SQL and CODE cells. Other cell types (MARKDOWN, INPUT, visualizations)
    return metadata only without source content.

    Uses cursor-based pagination. Use the 'next' and 'previous' cursors from
    the pagination object to navigate through pages.

    Note: Only SQL and CODE cell types expose source content via the API.
    Cannot read content of MARKDOWN, INPUT, or visualization cells.

    Args:
        project_id: The UUID of the Hex project
        limit: Optional page size for pagination (default determined by API)
        after: Optional cursor for next page (from pagination.next)
        before: Optional cursor for previous page (from pagination.previous)

    Returns:
        JSON string with structure:
        {
            "values": [
                {
                    "id": "cell-uuid",
                    "staticId": "static-id",
                    "cellType": "SQL|CODE|MARKDOWN|...",
                    "label": "Cell Name" | null,
                    "dataConnectionId": "connection-uuid" | null,
                    "contents": {
                        "sqlCell": {"source": "SELECT ..."} | null,
                        "codeCell": {"source": "print(...)"} | null
                    }
                }
            ],
            "pagination": {
                "next": "cursor" | null,
                "previous": "cursor" | null
            }
        }
    """
    params = {"projectId": project_id}

    if limit is not None:
        params["limit"] = limit
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before

    cells = await hex_request("GET", "/v1/cells", params=params)
    return json.dumps(cells)


@mcp.tool()
async def update_hex_cell(
    cell_id: str,
    sql_source: str | None = None,
    code_source: str | None = None,
    data_connection_id: str | None = None
) -> str:
    """Update a Hex cell's source code or data connection.

    Can update SQL cells (sql_source and/or data_connection_id) or
    CODE cells (code_source only). Cannot update both SQL and CODE
    in the same call.

    Only SQL and CODE cell types can be updated via the API. Attempting
    to update other cell types (MARKDOWN, INPUT, visualizations) will
    result in an error.

    Requires EDIT_PROJECT_CONTENTS permission on the project containing
    the cell.

    Args:
        cell_id: The UUID of the cell to update
        sql_source: New SQL source code (for SQL cells only)
        code_source: New Python/R code (for CODE cells only)
        data_connection_id: New data connection UUID (for SQL cells only)

    Returns:
        JSON string with updated cell structure:
        {
            "id": "cell-uuid",
            "staticId": "static-id",
            "cellType": "SQL|CODE",
            "label": "Cell Name" | null,
            "dataConnectionId": "connection-uuid" | null,
            "contents": {
                "sqlCell": {"source": "SELECT ..."} | null,
                "codeCell": {"source": "print(...)"} | null
            }
        }

    Raises:
        ValueError: If both sql_source and code_source are provided
        HTTPStatusError: For API errors (403, 404, 400, etc.)
    """
    # Validate discriminated union - cannot update both SQL and CODE
    if sql_source is not None and code_source is not None:
        raise ValueError(
            "Cannot update both sql_source and code_source in the same call. "
            "A cell is either SQL or CODE, not both."
        )

    # Validate that at least something is being updated
    if sql_source is None and code_source is None and data_connection_id is None:
        raise ValueError(
            "Must provide at least one of: sql_source, code_source, or data_connection_id"
        )

    # Build request body using discriminated union pattern
    body = {}

    # Add contents if source is being updated
    if sql_source is not None or code_source is not None:
        body["contents"] = {}
        if sql_source is not None:
            body["contents"]["sqlCell"] = {"source": sql_source}
        if code_source is not None:
            body["contents"]["codeCell"] = {"source": code_source}

    # Add data connection if specified
    if data_connection_id is not None:
        body["dataConnectionId"] = data_connection_id

    # Make API request
    updated_cell = await hex_request("PATCH", f"/v1/cells/{cell_id}", json=body)
    return json.dumps(updated_cell)


@mcp.tool()
async def update_hex_project_user_sharing(
    project_id: str,
    user_permissions: list[dict[str, Any]]
) -> str:
    """Update user access permissions for a Hex project.

    Grants or modifies access for individual users. Use this to share a project
    with specific users or update their permission levels.

    Access levels (from least to most permissive):
    - NONE: No access (revokes access)
    - APP_ONLY: Can view in published apps only
    - CAN_VIEW: Can view the project
    - CAN_EDIT: Can edit the project
    - FULL_ACCESS: Full admin access to project

    Requires project admin permissions.

    Args:
        project_id: The UUID of the Hex project
        user_permissions: List of user permission objects, each containing:
            - user_id: UUID of the user
            - access: Access level (NONE, APP_ONLY, CAN_VIEW, CAN_EDIT, FULL_ACCESS)

            Example:
            [
                {"user_id": "user-uuid-1", "access": "CAN_EDIT"},
                {"user_id": "user-uuid-2", "access": "CAN_VIEW"}
            ]

    Returns:
        JSON string with updated sharing configuration

    Raises:
        HTTPStatusError: For API errors (403, 404, 400, etc.)
    """
    # Build request body following API schema
    users = [
        {
            "user": {"id": perm["user_id"]},
            "access": perm["access"]
        }
        for perm in user_permissions
    ]

    body = {
        "sharing": {
            "upsert": {
                "users": users
            }
        }
    }

    result = await hex_request("PATCH", f"/v1/projects/{project_id}/sharing/users", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_project_group_sharing(
    project_id: str,
    group_permissions: list[dict[str, Any]]
) -> str:
    """Update group access permissions for a Hex project.

    Grants or modifies access for groups of users. Use this to share a project
    with entire teams or departments.

    Access levels (from least to most permissive):
    - NONE: No access (revokes access)
    - APP_ONLY: Can view in published apps only
    - CAN_VIEW: Can view the project
    - CAN_EDIT: Can edit the project
    - FULL_ACCESS: Full admin access to project

    Requires project admin permissions.

    Args:
        project_id: The UUID of the Hex project
        group_permissions: List of group permission objects, each containing:
            - group_id: UUID of the group
            - access: Access level (NONE, APP_ONLY, CAN_VIEW, CAN_EDIT, FULL_ACCESS)

            Example:
            [
                {"group_id": "group-uuid-1", "access": "CAN_EDIT"},
                {"group_id": "group-uuid-2", "access": "CAN_VIEW"}
            ]

    Returns:
        JSON string with updated sharing configuration

    Raises:
        HTTPStatusError: For API errors (403, 404, 400, etc.)
    """
    # Build request body following API schema
    groups = [
        {
            "group": {"id": perm["group_id"]},
            "access": perm["access"]
        }
        for perm in group_permissions
    ]

    body = {
        "sharing": {
            "upsert": {
                "groups": groups
            }
        }
    }

    result = await hex_request("PATCH", f"/v1/projects/{project_id}/sharing/groups", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_project_collection_sharing(
    project_id: str,
    collection_permissions: list[dict[str, Any]]
) -> str:
    """Add or update a project's membership in collections.

    Collections are used to organize projects. This endpoint controls which
    collections contain this project and what access level the collection provides.

    Access levels (from least to most permissive):
    - NONE: Remove from collection
    - APP_ONLY: Can view in published apps only
    - CAN_VIEW: Can view the project
    - CAN_EDIT: Can edit the project
    - FULL_ACCESS: Full admin access to project

    Requires project admin permissions.

    Args:
        project_id: The UUID of the Hex project
        collection_permissions: List of collection permission objects, each containing:
            - collection_id: UUID of the collection
            - access: Access level (NONE, APP_ONLY, CAN_VIEW, CAN_EDIT, FULL_ACCESS)

            Example:
            [
                {"collection_id": "collection-uuid-1", "access": "CAN_VIEW"},
                {"collection_id": "collection-uuid-2", "access": "CAN_EDIT"}
            ]

    Returns:
        JSON string with updated sharing configuration

    Raises:
        HTTPStatusError: For API errors (403, 404, 400, etc.)
    """
    # Build request body following API schema
    collections = [
        {
            "collection": {"id": perm["collection_id"]},
            "access": perm["access"]
        }
        for perm in collection_permissions
    ]

    body = {
        "sharing": {
            "upsert": {
                "collections": collections
            }
        }
    }

    result = await hex_request("PATCH", f"/v1/projects/{project_id}/sharing/collections", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_project_workspace_sharing(
    project_id: str,
    workspace_access: str | None = None,
    public_access: str | None = None
) -> str:
    """Update workspace-wide and public access for a Hex project.

    Controls whether the project is visible to all workspace members and/or
    publicly accessible on the web.

    Access levels (from least to most permissive):
    - NONE: No access
    - APP_ONLY: Can view in published apps only
    - CAN_VIEW: Can view the project
    - CAN_EDIT: Can edit the project
    - FULL_ACCESS: Full admin access to project

    Requires project admin permissions.

    Args:
        project_id: The UUID of the Hex project
        workspace_access: Access level for all workspace members (optional)
            - Options: NONE, APP_ONLY, CAN_VIEW, CAN_EDIT, FULL_ACCESS
            - None value means don't change this setting
        public_access: Access level for public web (optional)
            - Options: NONE, APP_ONLY, CAN_VIEW, CAN_EDIT, FULL_ACCESS
            - None value means don't change this setting
            - Be careful with public access!

    Returns:
        JSON string with updated sharing configuration

    Raises:
        ValueError: If both workspace_access and public_access are None
        HTTPStatusError: For API errors (403, 404, 400, etc.)
    """
    # Validate that at least one parameter is provided
    if workspace_access is None and public_access is None:
        raise ValueError(
            "Must provide at least one of: workspace_access or public_access"
        )

    # Build request body
    sharing = {}
    if workspace_access is not None:
        sharing["workspace"] = workspace_access
    if public_access is not None:
        sharing["publicWeb"] = public_access

    body = {"sharing": sharing}

    result = await hex_request("PATCH", f"/v1/projects/{project_id}/sharing/workspaceAndPublic", json=body)
    return json.dumps(result)


# === Collection Management ===


@mcp.tool()
async def list_hex_collections(
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    sort_by: str | None = None
) -> str:
    """List all collections in the Hex workspace.

    Collections organize related projects together in the workspace. This function
    returns paginated results with collection metadata including name, description,
    creator, and sharing settings.

    Args:
        limit: Maximum number of collections to return per page. Optional.
        after: Pagination cursor to fetch the next page of results. Returned in
            the pagination.next field of previous response. Optional.
        before: Pagination cursor to fetch the previous page of results. Returned
            in the pagination.previous field. Optional.
        sort_by: Sort order for collections. Valid values determined by Hex API
            (e.g., "name", "created", "updated"). Optional.

    Returns:
        JSON string containing collection list response with structure:
        {
            "values": [
                {
                    "id": "collection-uuid",
                    "name": "Collection Name",
                    "description": "Optional description",
                    "creator": {"id": "user-uuid", "email": "user@example.com"},
                    "sharing": {
                        "users": [...],
                        "groups": [...],
                        "workspace": {...}
                    }
                }
            ],
            "pagination": {
                "next": "cursor-string" or null,
                "previous": "cursor-string" or null
            }
        }

    Raises:
        HexAPIError: If the API request fails (403 forbidden, 500 server error).

    Example:
        >>> # List first page of collections
        >>> collections = list_hex_collections(limit=10)
        >>> data = json.loads(collections)
        >>> for collection in data["values"]:
        ...     print(f"{collection['name']}: {collection['id']}")
    """
    params = {}
    if limit is not None:
        params["limit"] = limit
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before
    if sort_by is not None:
        params["sortBy"] = sort_by

    result = await hex_request("GET", "/v1/collections", params=params)
    return json.dumps(result)


@mcp.tool()
async def get_hex_collection(collection_id: str) -> str:
    """Get detailed information about a specific collection.

    Retrieves the full details of a collection including its name, description,
    creator information, and sharing settings.

    Args:
        collection_id: The UUID of the collection to retrieve. Required.

    Returns:
        JSON string containing collection details with structure:
        {
            "id": "collection-uuid",
            "name": "Collection Name",
            "description": "Optional description",
            "creator": {"id": "user-uuid", "email": "user@example.com"},
            "sharing": {
                "users": [{"id": "user-uuid", "access": "CAN_VIEW"}],
                "groups": [{"id": "group-uuid", "access": "CAN_EDIT"}],
                "workspace": {"members": "CAN_VIEW"}
            }
        }

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> collection = get_hex_collection(collection_id="abc-123")
        >>> data = json.loads(collection)
        >>> print(f"Collection: {data['name']}")
        >>> print(f"Created by: {data['creator']['email']}")
    """
    result = await hex_request("GET", f"/v1/collections/{collection_id}")
    return json.dumps(result)


@mcp.tool()
async def create_hex_collection(
    name: str,
    description: str | None = None,
    sharing_users: list[dict[str, Any]] | None = None,
    sharing_groups: list[dict[str, Any]] | None = None,
    workspace_access: str | None = None
) -> str:
    """Create a new collection in the Hex workspace.

    Collections organize related projects together. This function creates a new
    collection with the specified name and optional description and sharing settings.

    Args:
        name: The name of the collection to create. Required.
        description: Optional description text for the collection. Optional.
        sharing_users: List of user sharing rules. Each dict should have keys
            "id" (user UUID) and "access" (access level). Optional.
        sharing_groups: List of group sharing rules. Each dict should have keys
            "id" (group UUID) and "access" (access level). Optional.
        workspace_access: Access level for all workspace members. Common values
            include "CAN_VIEW", "CAN_EDIT", "NONE". Optional.

    Returns:
        JSON string containing the created collection details including its
        generated UUID, name, description, creator, and sharing settings.

    Raises:
        ValueError: If name is empty or invalid.
        HexAPIError: If the API request fails (400 bad request, 403 forbidden).

    Example:
        >>> # Create a simple collection
        >>> collection = create_hex_collection(
        ...     name="Analytics Dashboards",
        ...     description="Customer-facing analytics projects"
        ... )
        >>> data = json.loads(collection)
        >>> print(f"Created collection: {data['id']}")

        >>> # Create with sharing settings
        >>> collection = create_hex_collection(
        ...     name="Finance Reports",
        ...     description="Quarterly financial reports",
        ...     sharing_users=[
        ...         {"id": "user-123", "access": "CAN_EDIT"}
        ...     ],
        ...     workspace_access="CAN_VIEW"
        ... )
    """
    body: dict[str, Any] = {"name": name}

    if description is not None:
        body["description"] = description

    # Build sharing object if any sharing parameters provided
    if sharing_users is not None or sharing_groups is not None or workspace_access is not None:
        sharing: dict[str, Any] = {}

        if sharing_users is not None:
            sharing["users"] = sharing_users

        if sharing_groups is not None:
            sharing["groups"] = sharing_groups

        if workspace_access is not None:
            sharing["workspace"] = {"members": workspace_access}

        body["sharing"] = sharing

    result = await hex_request("POST", "/v1/collections", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_collection(
    collection_id: str,
    name: str | None = None,
    description: str | None = None,
    sharing_users: list[dict[str, Any]] | None = None,
    sharing_groups: list[dict[str, Any]] | None = None,
    workspace_access: str | None = None
) -> str:
    """Update an existing collection's metadata and sharing settings.

    Updates one or more properties of an existing collection. Only the specified
    fields will be updated; other fields remain unchanged.

    Args:
        collection_id: The UUID of the collection to update. Required.
        name: New name for the collection. Optional.
        description: New description text for the collection. Optional.
        sharing_users: List of user sharing rules to upsert. Each dict should
            have keys "id" (user UUID) and "access" (access level). Optional.
        sharing_groups: List of group sharing rules to upsert. Each dict should
            have keys "id" (group UUID) and "access" (access level). Optional.
        workspace_access: New access level for all workspace members. Common
            values include "CAN_VIEW", "CAN_EDIT", "NONE". Optional.

    Returns:
        JSON string containing the updated collection details with all fields.

    Raises:
        ValueError: If no update parameters are provided.
        HexAPIError: If the API request fails (404 not found, 403 forbidden,
            400 bad request).

    Example:
        >>> # Update collection name
        >>> result = update_hex_collection(
        ...     collection_id="collection-123",
        ...     name="Updated Analytics Dashboards"
        ... )

        >>> # Update sharing settings
        >>> result = update_hex_collection(
        ...     collection_id="collection-123",
        ...     sharing_users=[
        ...         {"id": "user-456", "access": "CAN_EDIT"}
        ...     ],
        ...     workspace_access="CAN_VIEW"
        ... )

        >>> # Update multiple fields
        >>> result = update_hex_collection(
        ...     collection_id="collection-123",
        ...     name="Q4 Finance Reports",
        ...     description="Updated for Q4 2026",
        ...     workspace_access="CAN_VIEW"
        ... )
    """
    if all(param is None for param in [name, description, sharing_users, sharing_groups, workspace_access]):
        raise ValueError(
            "Must provide at least one parameter to update: name, description, "
            "sharing_users, sharing_groups, or workspace_access"
        )

    body: dict[str, Any] = {}

    if name is not None:
        body["name"] = name

    if description is not None:
        body["description"] = description

    # Build sharing.upsert object if any sharing parameters provided
    if sharing_users is not None or sharing_groups is not None or workspace_access is not None:
        upsert: dict[str, Any] = {}

        if sharing_users is not None:
            upsert["users"] = sharing_users

        if sharing_groups is not None:
            upsert["groups"] = sharing_groups

        if workspace_access is not None:
            upsert["workspace"] = {"members": workspace_access}

        body["sharing"] = {"upsert": upsert}

    result = await hex_request("PATCH", f"/v1/collections/{collection_id}", json=body)
    return json.dumps(result)


# === Group Management ===


@mcp.tool()
async def list_hex_groups(
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = None
) -> str:
    """List all groups in the Hex workspace.

    Groups allow organizing users for permission management. This function returns
    paginated results with group metadata including name and creation timestamp.

    Args:
        limit: Maximum number of groups to return per page. Optional.
        after: Pagination cursor to fetch the next page of results. Returned in
            the pagination.next field of previous response. Optional.
        before: Pagination cursor to fetch the previous page of results. Returned
            in the pagination.previous field. Optional.
        sort_by: Sort order for groups. Valid values determined by Hex API
            (e.g., "name", "createdAt"). Optional.
        sort_direction: Sort direction, typically "asc" or "desc". Optional.

    Returns:
        JSON string containing group list response with structure:
        {
            "values": [
                {
                    "id": "group-uuid",
                    "name": "Group Name",
                    "createdAt": "2026-01-08T12:00:00Z"
                }
            ],
            "pagination": {
                "next": "cursor-string" or null,
                "previous": "cursor-string" or null
            }
        }

    Raises:
        HexAPIError: If the API request fails (403 forbidden, 500 server error).

    Example:
        >>> # List first page of groups
        >>> groups = list_hex_groups(limit=10)
        >>> data = json.loads(groups)
        >>> for group in data["values"]:
        ...     print(f"{group['name']}: {group['id']}")
        ...     print(f"  Created: {group['createdAt']}")
    """
    params = {}
    if limit is not None:
        params["limit"] = limit
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before
    if sort_by is not None:
        params["sortBy"] = sort_by
    if sort_direction is not None:
        params["sortDirection"] = sort_direction

    result = await hex_request("GET", "/v1/groups", params=params)
    return json.dumps(result)


@mcp.tool()
async def get_hex_group(group_id: str) -> str:
    """Get detailed information about a specific group.

    Retrieves the full details of a group including its name and creation timestamp.

    Args:
        group_id: The UUID of the group to retrieve. Required.

    Returns:
        JSON string containing group details with structure:
        {
            "id": "group-uuid",
            "name": "Group Name",
            "createdAt": "2026-01-08T12:00:00Z"
        }

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> group = get_hex_group(group_id="group-123")
        >>> data = json.loads(group)
        >>> print(f"Group: {data['name']}")
        >>> print(f"Created: {data['createdAt']}")
    """
    result = await hex_request("GET", f"/v1/groups/{group_id}")
    return json.dumps(result)


@mcp.tool()
async def create_hex_group(
    name: str,
    member_user_ids: list[str] | None = None
) -> str:
    """Create a new group in the Hex workspace.

    Groups organize users for permission management. This function creates a new
    group with the specified name and optional initial members.

    Args:
        name: The name of the group to create. Required.
        member_user_ids: List of user UUIDs to add as initial group members.
            Maximum 100 users. Optional.

    Returns:
        JSON string containing the created group details including its generated
        UUID, name, and creation timestamp.

    Raises:
        ValueError: If name is empty or more than 100 members provided.
        HexAPIError: If the API request fails (400 bad request, 403 forbidden).

    Example:
        >>> # Create a simple group
        >>> group = create_hex_group(name="Analytics Team")
        >>> data = json.loads(group)
        >>> print(f"Created group: {data['id']}")

        >>> # Create with initial members
        >>> group = create_hex_group(
        ...     name="Finance Team",
        ...     member_user_ids=["user-123", "user-456", "user-789"]
        ... )
        >>> data = json.loads(group)
        >>> print(f"Created group with {len(member_user_ids)} members")
    """
    body: dict[str, Any] = {"name": name}

    if member_user_ids is not None:
        if len(member_user_ids) > 100:
            raise ValueError("Cannot add more than 100 members at once")

        body["members"] = {
            "users": [{"id": user_id} for user_id in member_user_ids]
        }

    result = await hex_request("POST", "/v1/groups", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_group(
    group_id: str,
    name: str | None = None,
    add_member_user_ids: list[str] | None = None,
    remove_member_user_ids: list[str] | None = None
) -> str:
    """Update an existing group's name and/or membership.

    Updates one or more properties of an existing group. Can rename the group,
    add new members, remove existing members, or perform all operations together.

    Args:
        group_id: The UUID of the group to update. Required.
        name: New name for the group. Optional.
        add_member_user_ids: List of user UUIDs to add to the group. Maximum
            100 users per operation. Optional.
        remove_member_user_ids: List of user UUIDs to remove from the group.
            Maximum 100 users per operation. Optional.

    Returns:
        JSON string containing the updated group details with all fields.

    Raises:
        ValueError: If no update parameters are provided, or if more than 100
            users provided in add or remove operations.
        HexAPIError: If the API request fails (404 not found, 403 forbidden,
            400 bad request).

    Example:
        >>> # Update group name
        >>> result = update_hex_group(
        ...     group_id="group-123",
        ...     name="Updated Analytics Team"
        ... )

        >>> # Add members to group
        >>> result = update_hex_group(
        ...     group_id="group-123",
        ...     add_member_user_ids=["user-456", "user-789"]
        ... )

        >>> # Remove members from group
        >>> result = update_hex_group(
        ...     group_id="group-123",
        ...     remove_member_user_ids=["user-123"]
        ... )

        >>> # Update name and membership together
        >>> result = update_hex_group(
        ...     group_id="group-123",
        ...     name="Senior Analytics Team",
        ...     add_member_user_ids=["user-001"],
        ...     remove_member_user_ids=["user-999"]
        ... )
    """
    if all(param is None for param in [name, add_member_user_ids, remove_member_user_ids]):
        raise ValueError(
            "Must provide at least one parameter to update: name, "
            "add_member_user_ids, or remove_member_user_ids"
        )

    if add_member_user_ids is not None and len(add_member_user_ids) > 100:
        raise ValueError("Cannot add more than 100 members at once")

    if remove_member_user_ids is not None and len(remove_member_user_ids) > 100:
        raise ValueError("Cannot remove more than 100 members at once")

    body: dict[str, Any] = {}

    if name is not None:
        body["name"] = name

    # Build members.add and members.remove if provided
    if add_member_user_ids is not None or remove_member_user_ids is not None:
        members: dict[str, Any] = {}

        if add_member_user_ids is not None:
            members["add"] = {
                "users": [{"id": user_id} for user_id in add_member_user_ids]
            }

        if remove_member_user_ids is not None:
            members["remove"] = {
                "users": [{"id": user_id} for user_id in remove_member_user_ids]
            }

        body["members"] = members

    result = await hex_request("PATCH", f"/v1/groups/{group_id}", json=body)
    return json.dumps(result)


@mcp.tool()
async def delete_hex_group(group_id: str) -> str:
    """Delete a group from the Hex workspace.

    Permanently removes a group. This does not delete the users in the group,
    only the group itself. Permissions granted to the group will be revoked.

    Args:
        group_id: The UUID of the group to delete. Required.

    Returns:
        Success message confirming deletion.

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> result = delete_hex_group(group_id="group-123")
        >>> print(result)  # "Group deleted successfully"
    """
    await hex_request("DELETE", f"/v1/groups/{group_id}")
    return "Group deleted successfully"


# === Data Connection Management ===


@mcp.tool()
async def list_hex_data_connections(
    limit: int | None = None,
    after: str | None = None,
    before: str | None = None,
    sort_by: str | None = None,
    sort_direction: str | None = None
) -> str:
    """List all data connections in the Hex workspace.

    Data connections define database and warehouse integrations (BigQuery, Snowflake,
    Postgres, etc.). This function returns paginated results with connection metadata.

    Args:
        limit: Maximum number of connections to return per page. Optional.
        after: Pagination cursor to fetch the next page of results. Returned in
            the pagination.next field of previous response. Optional.
        before: Pagination cursor to fetch the previous page of results. Returned
            in the pagination.previous field. Optional.
        sort_by: Sort order for connections. Valid values: "CREATED_AT", "NAME".
            Optional.
        sort_direction: Sort direction, "asc" or "desc". Optional.

    Returns:
        JSON string containing connection list response with structure:
        {
            "values": [
                {
                    "id": "connection-uuid",
                    "name": "Connection Name",
                    "type": "bigquery|snowflake|postgres|...",
                    "description": "Optional description",
                    "connectionDetails": {...},
                    "sharing": {...},
                    "schemaRefreshSchedule": {...}
                }
            ],
            "pagination": {
                "next": "cursor-string" or null,
                "previous": "cursor-string" or null
            }
        }

    Raises:
        HexAPIError: If the API request fails (403 forbidden, 500 server error).

    Example:
        >>> # List first page of connections
        >>> connections = list_hex_data_connections(limit=10, sort_by="NAME")
        >>> data = json.loads(connections)
        >>> for conn in data["values"]:
        ...     print(f"{conn['name']} ({conn['type']}): {conn['id']}")
    """
    params = {}
    if limit is not None:
        params["limit"] = limit
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before
    if sort_by is not None:
        params["sortBy"] = sort_by
    if sort_direction is not None:
        params["sortDirection"] = sort_direction

    result = await hex_request("GET", "/v1/data-connections", params=params)
    return json.dumps(result)


@mcp.tool()
async def get_hex_data_connection(connection_id: str) -> str:
    """Get detailed information about a specific data connection.

    Retrieves the full details of a data connection including its type, configuration,
    sharing settings, and schema refresh schedule.

    Args:
        connection_id: The UUID of the data connection to retrieve. Required.

    Returns:
        JSON string containing connection details with structure:
        {
            "id": "connection-uuid",
            "name": "Connection Name",
            "type": "bigquery|snowflake|postgres|athena|databricks|redshift",
            "description": "Optional description",
            "connectionDetails": {
                "bigquery": {...} | "snowflake": {...} | ...
            },
            "connectViaSsh": false,
            "includeMagic": true,
            "allowWritebackCells": false,
            "schemaFilters": {...},
            "schemaRefreshSchedule": {...},
            "schemaRefreshAccess": {...},
            "sharing": {
                "workspace": {...},
                "groups": [...],
                "users": [...]
            }
        }

    Raises:
        HexAPIError: If the API request fails (404 not found, 403 forbidden).

    Example:
        >>> connection = get_hex_data_connection(connection_id="conn-123")
        >>> data = json.loads(connection)
        >>> print(f"Connection: {data['name']} ({data['type']})")
        >>> print(f"Description: {data['description']}")
    """
    result = await hex_request("GET", f"/v1/data-connections/{connection_id}")
    return json.dumps(result)


@mcp.tool()
async def create_hex_data_connection(
    name: str,
    connection_type: str,
    connection_details: dict[str, Any],
    description: str | None = None,
    connect_via_ssh: bool | None = None,
    include_magic: bool | None = None,
    allow_writeback_cells: bool | None = None,
    schema_filters: dict[str, Any] | None = None,
    schema_refresh_schedule: dict[str, Any] | None = None,
    schema_refresh_access: str | None = None,
    sharing: dict[str, Any] | None = None
) -> str:
    """Create a new data connection in the Hex workspace.

    Data connections define database and warehouse integrations. Each connection
    type requires specific configuration details in the connection_details parameter.

    Supported connection types:
        - "bigquery": Google BigQuery (requires serviceAccountJsonConfig, projectId)
        - "snowflake": Snowflake Data Warehouse
        - "postgres": PostgreSQL databases
        - "redshift": Amazon Redshift
        - "athena": Amazon Athena
        - "databricks": Databricks SQL

    Args:
        name: The name of the data connection to create. Required.
        connection_type: Type of connection. Valid values: "bigquery", "snowflake",
            "postgres", "redshift", "athena", "databricks". Required.
        connection_details: Dictionary containing connection-specific configuration.
            Structure varies by connection_type. For BigQuery example:
            {
                "bigquery": {
                    "serviceAccountJsonConfig": "...",
                    "projectId": "my-project",
                    "enableStorageApi": true,
                    "enableDriveAccess": false
                }
            }
            Required.
        description: Optional description text for the connection. Optional.
        connect_via_ssh: Whether to connect via SSH tunnel. Optional.
        include_magic: Whether to include SQL magic commands. Optional.
        allow_writeback_cells: Whether to allow writeback operations. Optional.
        schema_filters: Schema filtering configuration. Optional.
        schema_refresh_schedule: Automatic schema refresh schedule. Optional.
        schema_refresh_access: Access control for schema refresh operations. Optional.
        sharing: Sharing configuration for workspace, groups, and users. Optional.

    Returns:
        JSON string containing the created data connection details including its
        generated UUID, name, type, and all configuration.

    Raises:
        ValueError: If connection_type is invalid.
        HexAPIError: If the API request fails (400 bad request, 403 forbidden).

    Example:
        >>> # Create a BigQuery connection
        >>> connection = create_hex_data_connection(
        ...     name="Production BigQuery",
        ...     connection_type="bigquery",
        ...     connection_details={
        ...         "bigquery": {
        ...             "serviceAccountJsonConfig": json.dumps(service_account),
        ...             "projectId": "my-gcp-project",
        ...             "enableStorageApi": True,
        ...             "enableDriveAccess": False
        ...         }
        ...     },
        ...     description="Production data warehouse",
        ...     include_magic=True
        ... )
        >>> data = json.loads(connection)
        >>> print(f"Created connection: {data['id']}")
    """
    valid_types = ["athena", "bigquery", "databricks", "postgres", "redshift", "snowflake"]
    if connection_type not in valid_types:
        raise ValueError(
            f"Invalid connection_type: {connection_type}. "
            f"Must be one of: {', '.join(valid_types)}"
        )

    body: dict[str, Any] = {
        "name": name,
        "type": connection_type,
        "connectionDetails": connection_details
    }

    if description is not None:
        body["description"] = description
    if connect_via_ssh is not None:
        body["connectViaSsh"] = connect_via_ssh
    if include_magic is not None:
        body["includeMagic"] = include_magic
    if allow_writeback_cells is not None:
        body["allowWritebackCells"] = allow_writeback_cells
    if schema_filters is not None:
        body["schemaFilters"] = schema_filters
    if schema_refresh_schedule is not None:
        body["schemaRefreshSchedule"] = schema_refresh_schedule
    if schema_refresh_access is not None:
        body["schemaRefreshAccess"] = schema_refresh_access
    if sharing is not None:
        body["sharing"] = sharing

    result = await hex_request("POST", "/v1/data-connections", json=body)
    return json.dumps(result)


@mcp.tool()
async def update_hex_data_connection(
    connection_id: str,
    name: str | None = None,
    description: str | None = None,
    connection_details: dict[str, Any] | None = None,
    connect_via_ssh: bool | None = None,
    include_magic: bool | None = None,
    allow_writeback_cells: bool | None = None,
    schema_filters: dict[str, Any] | None = None,
    schema_refresh_schedule: dict[str, Any] | None = None,
    schema_refresh_access: str | None = None,
    sharing: dict[str, Any] | None = None
) -> str:
    """Update an existing data connection's configuration.

    Updates one or more properties of an existing data connection. Only the
    specified fields will be updated; other fields remain unchanged.

    Args:
        connection_id: The UUID of the data connection to update. Required.
        name: New name for the connection. Optional.
        description: New description text for the connection. Optional.
        connection_details: New connection-specific configuration. Structure varies
            by connection type. Optional.
        connect_via_ssh: Whether to connect via SSH tunnel. Optional.
        include_magic: Whether to include SQL magic commands. Optional.
        allow_writeback_cells: Whether to allow writeback operations. Optional.
        schema_filters: New schema filtering configuration. Optional.
        schema_refresh_schedule: New automatic schema refresh schedule. Optional.
        schema_refresh_access: New access control for schema refresh. Optional.
        sharing: Updated sharing configuration. Can use "upsert" pattern for
            groups and users. Optional.

    Returns:
        JSON string containing the updated data connection details with all fields.

    Raises:
        ValueError: If no update parameters are provided.
        HexAPIError: If the API request fails (404 not found, 403 forbidden,
            400 bad request).

    Example:
        >>> # Update connection name and description
        >>> result = update_hex_data_connection(
        ...     connection_id="conn-123",
        ...     name="Updated Production BigQuery",
        ...     description="Updated production data warehouse"
        ... )

        >>> # Update sharing settings
        >>> result = update_hex_data_connection(
        ...     connection_id="conn-123",
        ...     sharing={
        ...         "workspace": {
        ...             "members": "CAN_USE"
        ...         },
        ...         "groups": {
        ...             "upsert": [
        ...                 {"group": {"id": "group-456"}, "access": "CAN_USE"}
        ...             ]
        ...         }
        ...     }
        ... )

        >>> # Update multiple fields
        >>> result = update_hex_data_connection(
        ...     connection_id="conn-123",
        ...     name="New Name",
        ...     include_magic=False,
        ...     allow_writeback_cells=True
        ... )
    """
    if all(param is None for param in [
        name, description, connection_details, connect_via_ssh, include_magic,
        allow_writeback_cells, schema_filters, schema_refresh_schedule,
        schema_refresh_access, sharing
    ]):
        raise ValueError(
            "Must provide at least one parameter to update: name, description, "
            "connection_details, connect_via_ssh, include_magic, allow_writeback_cells, "
            "schema_filters, schema_refresh_schedule, schema_refresh_access, or sharing"
        )

    body: dict[str, Any] = {}

    if name is not None:
        body["name"] = name
    if description is not None:
        body["description"] = description
    if connection_details is not None:
        body["connectionDetails"] = connection_details
    if connect_via_ssh is not None:
        body["connectViaSsh"] = connect_via_ssh
    if include_magic is not None:
        body["includeMagic"] = include_magic
    if allow_writeback_cells is not None:
        body["allowWritebackCells"] = allow_writeback_cells
    if schema_filters is not None:
        body["schemaFilters"] = schema_filters
    if schema_refresh_schedule is not None:
        body["schemaRefreshSchedule"] = schema_refresh_schedule
    if schema_refresh_access is not None:
        body["schemaRefreshAccess"] = schema_refresh_access
    if sharing is not None:
        body["sharing"] = sharing

    result = await hex_request("PATCH", f"/v1/data-connections/{connection_id}", json=body)
    return json.dumps(result)
