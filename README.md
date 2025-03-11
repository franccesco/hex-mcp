# hex-mcp MCP server

A MCP server for Hex that implements the following tools:

- `list_hex_projects`: Lists available Hex projects
- `search_hex_projects`: Search for Hex projects by pattern
- `get_hex_project`: Get detailed information about a specific project
- `get_hex_run_status`: Check the status of a project run
- `get_hex_project_runs`: Get the history of project runs
- `run_hex_project`: Execute a Hex project
- `cancel_hex_run`: Cancel a running project

## Installation

Using uv is the recommended way to install hex-mcp:

```bash
uv add hex-mcp
```

Or using pip:

```bash
pip install hex-mcp
```

To confirm it's working, you can run:

```bash
hex-mcp --version
```

## Configuration

### Using the config command (recommended)

The easiest way to configure hex-mcp is by using the `config` command and passing your API key and API URL (optional and defaults to `https://app.hex.tech/api/v1`):

```bash
hex-mcp config --api-key "your_hex_api_key" --api-url "https://app.hex.tech/api/v1"
```

> [!NOTE]
> This saves your configuration to a file in your home directory (e.g. `~/.hex-mcp/config.yml`), making it available for all hex-mcp invocations.

### Using environment variables

Alternatively, the Hex MCP server can be configured with environment variables:

- `HEX_API_KEY`: Your Hex API key
- `HEX_API_URL`: The Hex API base URL

When setting up environment variables for MCP servers they need to be either global for Cursor to pick them up or make use of uv's `--env-file` flag when invoking the server.

## Using with Cursor

Cursor allows AI agents to interact with Hex via the MCP protocol. Follow these steps to set up and use hex-mcp with Cursor. You can create a `.cursor/mcp.json` file in your project root with the following content:

```json
{
  "mcpServers": {
    "hex-mcp": {
      "command": "uv",
      "args": ["run", "hex-mcp", "run"]
    }
  }
}
```

Alternatively, you can use the `hex-mcp` command directly if it's in your PATH:

```json
{
  "mcpServers": {
    "hex-mcp": {
      "command": "hex-mcp",
      "args": ["run"]
    }
  }
}
```

Once it's up and running, you can use it in Cursor by initiating a new AI (Agent) conversation and ask it to list or run a Hex project.

> [!IMPORTANT]
> The MCP server and CLI is still in development and subject to breaking changes.
