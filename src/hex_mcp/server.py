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


def backoff_handler(details: dict[str, Any], ctx: Context):
    ctx.warning(f"Rate limit hit, backing off {details['wait']:.1f} seconds after {details['tries']} tries")


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

    Returns:
        JSON string with list of projects
    """
    params = {"limit": limit, "offset": offset}
    projects = await hex_request("GET", "/projects", params=params)
    return projects["values"]


@mcp.tool()
async def search_hex_projects(search_pattern: str, limit: int = 100, offset: int = 0) -> str:
    """Search for Hex projects using regex pattern matching on project titles.

    Args:
        search_pattern: Regex pattern to search for in project titles
        limit: Maximum number of projects to return (default: 100)
        offset: Number of projects to skip for pagination (default: 0)

    Returns:
        JSON string with matching projects
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
    """Get details about a specific Hex project.

    Args:
        project_id: The UUID of the Hex project

    Returns:
        JSON string with project details
    """
    project = await hex_request("GET", f"/projects/{project_id}")
    return str(project)


@mcp.tool()
async def get_hex_run_status(project_id: str, run_id: str) -> str:
    """Get the status of a project run.

    Args:
        project_id: The UUID of the Hex project
        run_id: The UUID of the run

    Returns:
        JSON string with run status details
    """
    status = await hex_request("GET", f"/projects/{project_id}/runs/{run_id}")
    return status


@mcp.tool()
async def get_hex_project_runs(project_id: str, limit: int = 25, offset: int = 0) -> str:
    """Get the runs for a specific project.

    Args:
        project_id: The UUID of the Hex project
        limit: The number of runs to return
        offset: The number of runs to skip

    Returns:
        JSON string with project runs
    """

    params = {"limit": limit, "offset": offset}

    runs = await hex_request("GET", f"/projects/{project_id}/runs", params=params)
    return runs


@mcp.tool()
async def run_hex_project(project_id: str, input_params: dict = None, update_published_results: bool = False) -> str:
    """Run a Hex project.

    Args:
        project_id: The UUID of the Hex project to run
        input_params: Optional input parameters for the project
        update_published_results: Whether to update published results

    Returns:
        JSON string with run details
    """

    run_config = {
        "inputParams": input_params or {},
        "updatePublishedResults": update_published_results,
        "useCachedSqlResults": True,
    }

    result = await hex_request("POST", f"/projects/{project_id}/runs", json=run_config)
    return result


@mcp.tool()
async def cancel_hex_run(project_id: str, run_id: str) -> str:
    """Cancel a running project.

    Args:
        project_id: The UUID of the Hex project
        run_id: The UUID of the run to cancel

    Returns:
        Success message
    """
    await hex_request("DELETE", f"/projects/{project_id}/runs/{run_id}")
    return "Run cancelled successfully"
