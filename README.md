# hex-mcp MCP server

A MCP server for Hex

## Components

### Resources

The server implements a simple note storage system with:

- Custom note:// URI scheme for accessing individual notes
- Each note resource has a name, description and text/plain mimetype

### Prompts

The server provides a single prompt:

- summarize-notes: Creates summaries of all stored notes
  - Optional "style" argument to control detail level (brief/detailed)
  - Generates prompt combining all current notes with style preference

### Tools

The server implements multiple tools to interact with the Hex API:

- `list_hex_projects`: Lists available Hex projects
- `search_hex_projects`: Search for Hex projects by pattern
- `get_hex_project`: Get detailed information about a specific project
- `get_hex_run_status`: Check the status of a project run
- `get_hex_project_runs`: Get the history of project runs
- `run_hex_project`: Execute a Hex project
- `cancel_hex_run`: Cancel a running project

## Installation

```bash
pip install hex-mcp
```

For development features:

```bash
pip install "hex-mcp[dev]"
```

## Configuration

The Hex MCP server requires two environment variables:

- `HEX_API_KEY`: Your Hex API key
- `HEX_API_URL`: The Hex API base URL

You can set these in a `.env` file or pass them via command line arguments.

## CLI Usage

The CLI uses [Typer](https://typer.tiangolo.com/) to provide a modern command-line interface:

```
hex-mcp [OPTIONS] COMMAND [ARGS]...
```

### Commands

- `run`: Run the MCP server normally (default if no command is specified)
- `dev`: Run in development mode with the MCP Inspector

### Global Options

These options apply to all commands:

- `--api-key TEXT`: Set the Hex API key (overrides HEX_API_KEY environment variable)
- `--api-url TEXT`: Set the Hex API URL (overrides HEX_API_URL environment variable)
- `--server-name TEXT`: Set a custom name for the MCP server (default: "Hex MCP Server")
- `-v, --verbose`: Enable verbose logging
- `--version`: Show the version of hex-mcp and exit
- `--help`: Show help message and exit

### Command-specific Options

#### dev

- `--port INTEGER`: Set the port for the development server (default: 8765)

### Examples

Run the server with environment variables from `.env` file:

```bash
hex-mcp run
# or just
hex-mcp
```

Run with command line configuration:

```bash
hex-mcp --api-key your_api_key --api-url https://hex-api.example.com run
```

Run in development mode:

```bash
hex-mcp --verbose dev --port 9000
```

Show version:

```bash
hex-mcp --version
```

Show help:

```bash
hex-mcp --help
hex-mcp dev --help
```

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "hex-mcp": {
      "command": "hex-mcp",
      "args": [
        "--api-key",
        "your_api_key",
        "--api-url",
        "your_api_url",
        "run"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "hex-mcp": {
      "command": "hex-mcp",
      "env": {
        "HEX_API_KEY": "your_api_key",
        "HEX_API_URL": "your_api_url"
      }
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:

```bash
uv sync
```

2. Build package distributions:

```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:

```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:

- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, use our built-in development mode:

```bash
hex-mcp dev
```

This will start the MCP Inspector web interface which allows you to:

- See real-time requests and responses
- Test tools and resources
- Debug server behavior

For manual inspector usage:

```bash
npx @modelcontextprotocol/inspector hex-mcp
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
