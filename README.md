# Hex API MCP Server

This project provides a simple MCP (Model Context Protocol) server for interacting with the Hex API. It allows AI assistants to access Hex projects, run them, and check their status through a standardized interface.

## Features

- Get project details
- List projects
- View project runs and run status
- Run projects
- Cancel running projects

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up your Hex API Key:

   ```bash
   export HEX_API_KEY="your_hex_api_key"
   ```

   Optionally, you can set a custom API base URL:

   ```bash
   export HEX_API_BASE_URL="https://your-custom-hex-url.com/api/v1"
   ```

3. Run the server:
   ```bash
   python main.py
   ```

## Using with Claude

This MCP server can be installed in Claude Desktop:

```bash
mcp install main.py
```

Or test it with the MCP Inspector:

```bash
mcp dev main.py
```

## Available Resources

- `project://{project_id}` - Get details about a specific Hex project
- `projects://list` - List all available Hex projects
- `project://{project_id}/run/{run_id}` - Get the status of a project run
- `project://{project_id}/runs` - Get the list of runs for a specific project (with default limit of 25)

## Available Tools

- `run_project` - Run a Hex project with optional parameters
- `cancel_run` - Cancel a running project

## Example Usage

```
# List all projects
Read resource: projects://list

# Get details for a specific project
Read resource: project://123e4567-e89b-12d3-a456-426614174000

# Get status of a specific run
Read resource: project://123e4567-e89b-12d3-a456-426614174000/run/98765432-e89b-12d3-a456-426614174000

# List runs for a project
Read resource: project://123e4567-e89b-12d3-a456-426614174000/runs

# Run a project
Call tool: run_project
Arguments:
  project_id: 123e4567-e89b-12d3-a456-426614174000
  input_params: {"text_input_1": "Hello World"}
  update_published_results: true

# Cancel a run
Call tool: cancel_run
Arguments:
  project_id: 123e4567-e89b-12d3-a456-426614174000
  run_id: 98765432-e89b-12d3-a456-426614174000
```

## Error Handling

The server will raise appropriate HTTP errors when the Hex API returns error responses. Make sure your API key has appropriate permissions for the actions you're trying to perform.
