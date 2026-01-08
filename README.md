# hex-mcp MCP server

A MCP server for Hex that implements orchestration and monitoring tools.

## What This Does (And Doesn't Do)

### Practical Use Cases

**Orchestration and Automation**:
- Trigger Hex project runs from external systems (Airflow DAGs, CI/CD pipelines)
- Monitor run status programmatically
- Cancel long-running or stuck executions
- Discover and search projects across workspaces

**Operational Monitoring**:
- Check if scheduled runs completed successfully
- Get run history for auditing
- Programmatic access to project metadata (owner, last edited, description)

### Critical Limitations

**Cannot access notebook content**:
- Cannot read cell content (queries, markdown, code, visualizations)
- Cannot write or edit cells
- Cannot modify notebook structure
- Cannot view query results or charts
- Cannot manage notebook dependencies or parameters

**Not suitable for**:
- Building or authoring notebooks
- Collaborative notebook development
- Debugging queries or code
- Content migration or backup
- Any task requiring access to actual notebook cells

### When to Use This

Use hex-mcp when you need to **orchestrate** Hex executions from external systems or **monitor** run status. For notebook development, use the Hex web UI directly.

## Available Tools

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

## About This Fork

This fork contains fixes for return type mismatches in the upstream hex-mcp package (v0.1.10).

**Bugs Fixed**:
- Five tools declared `-> str` return type but returned Python dicts/lists
- Caused pydantic validation errors in Claude Code MCP integration
- Fixed by adding `json.dumps()` to return statements in `src/hex_mcp/server.py`

**Fixed Tools** (lines 74, 172, 187, 206, 229):
- `list_hex_projects()`
- `get_hex_project()`
- `get_hex_run_status()`
- `get_hex_project_runs()`
- `run_hex_project()`

**Already Working** (correctly implemented):
- `search_hex_projects()` (already used `json.dumps()`)
- `cancel_hex_run()` (returns string literal)

**Upstream**: https://github.com/franccesco/hex-mcp

This bugfix branch (`bugfix/fast-mcp-return-types`) is ready for upstream PR submission if desired.
