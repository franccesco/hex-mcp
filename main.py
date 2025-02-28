import httpx
from os import getenv
from mcp.server.fastmcp import FastMCP

# Environment Variables
HEX_API_KEY = getenv("HEX_API_KEY")
HEX_API_BASE_URL = getenv("HEX_API_URL")


# Create an MCP server
mcp = FastMCP("Hex API Client")


# Helper function for Hex API requests
def hex_request(method: str, endpoint: str, json=None, params=None):
    url = f"{HEX_API_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {HEX_API_KEY}"}

    with httpx.Client() as client:
        response = client.request(method=method, url=url, headers=headers, json=json, params=params)

        response.raise_for_status()
        return response.json() if response.content else None


# Resources
@mcp.resource("project://{project_id}")
def get_project(project_id: str) -> str:
    """Get details about a specific Hex project.

    Args:
        project_id: The UUID of the Hex project

    Returns:
        JSON string with project details
    """
    project = hex_request("GET", f"/projects/{project_id}")
    return project


@mcp.resource("projects://list")
def list_projects() -> str:
    """List all available Hex projects that are in production.

    Returns:
        JSON string with list of projects
    """
    status = "In Production"
    projects = hex_request("GET", "/projects", params={"statuses": status})
    return projects


@mcp.resource("project://{project_id}/run/{run_id}")
def get_run_status(project_id: str, run_id: str) -> str:
    """Get the status of a project run.

    Args:
        project_id: The UUID of the Hex project
        run_id: The UUID of the run

    Returns:
        JSON string with run status details
    """
    status = hex_request("GET", f"/projects/{project_id}/runs/{run_id}")
    return status


@mcp.resource("project://{project_id}/runs")
def get_project_runs(project_id: str) -> str:
    """Get the runs for a specific project.

    Args:
        project_id: The UUID of the Hex project

    Returns:
        JSON string with project runs
    """
    # Set default values for parameters
    limit = 25
    offset = 0

    params = {"limit": limit, "offset": offset}

    runs = hex_request("GET", f"/projects/{project_id}/runs", params=params)
    return runs


# Tools
@mcp.tool()
def run_project(project_id: str, input_params: dict = None, update_published_results: bool = False) -> str:
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

    result = hex_request("POST", f"/projects/{project_id}/runs", json=run_config)
    return result


@mcp.tool()
def cancel_run(project_id: str, run_id: str) -> str:
    """Cancel a running project.

    Args:
        project_id: The UUID of the Hex project
        run_id: The UUID of the run to cancel

    Returns:
        Success message
    """
    hex_request("DELETE", f"/projects/{project_id}/runs/{run_id}")
    return "Run cancelled successfully"


if __name__ == "__main__":
    # Run the server
    mcp.run()
