from . import server
import importlib.metadata
import typer
from typing import Optional
import os
import yaml
import json
from pathlib import Path
from . import config as config_module


app = typer.Typer(help="Hex MCP Server - Model Context Protocol server for Hex")


def version_callback(value: bool):
    """Print version and exit"""
    if value:
        version = importlib.metadata.version("hex-mcp")
        typer.echo(f"hex-mcp version {version}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the version of hex-mcp",
    ),
):
    """Main entry point for the Hex MCP Server.

    Provides a CLI to run the Hex MCP server.
    """


@app.command()
def run():
    """Run the MCP server normally."""
    server.mcp.run()


@app.command()
def config(
    api_key: str = typer.Option(..., help="API key for Hex authentication"),
    api_url: str = typer.Option("https://app.hex.tech/api/v1", help="Hex API URL"),
):
    """Configure Hex MCP server with API credentials.

    Saves the configuration to a YAML file in the user's home directory.
    """
    # Create or update config file
    config_data = {
        "api_key": api_key,
        "api_url": api_url,
    }

    # Save config using the config module
    config_module.save_config(config_data)
    config_file = config_module.get_config_file_path()

    typer.echo(f"Configuration saved to {config_file}")
    typer.echo("API Key: " + api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "API Key: [Hidden]")
    typer.echo(f"API URL: {api_url}")


@app.command()
def show_config():
    """Show the current configuration."""
    api_key = config_module.get_api_key()
    api_url = config_module.get_api_url()
    config_file = config_module.get_config_file_path()

    typer.echo(f"Configuration file: {config_file}")
    if api_key:
        # Show only first and last 4 characters of the API key
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "[Hidden]"
        typer.echo(f"API Key: {masked_key}")
    else:
        typer.echo("API Key: Not configured")

    typer.echo(f"API URL: {api_url}")


@app.command()
def install(
    uv: bool = typer.Option(
        False,
        "--uv",
        help="Use 'uv run' command structure instead of direct command",
    ),
    server_name: str = typer.Option(
        "Hex Projects",
        "--name",
        help="Name for the MCP server in Cursor",
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        help="Preview the configuration without writing it to disk",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force overwrite of existing configuration without prompting",
    ),
    skip_config_check: bool = typer.Option(
        False,
        "--skip-config-check",
        help="Skip checking for Hex API configuration",
    ),
):
    """Install the Hex MCP server configuration for Cursor.

    Creates a .cursor/mcp.json file in the current directory that Cursor can use to
    integrate with the Hex MCP server.
    """
    # Check if Hex API key is configured
    if not skip_config_check:
        api_key = config_module.get_api_key()
        if api_key is None:
            typer.echo("Warning: No Hex API key configured. The MCP server won't be functional.")
            typer.echo("Run 'hex-mcp config' to set up your Hex API credentials.")
            if not typer.confirm("Continue with installation anyway?", default=False):
                typer.echo("Installation cancelled.")
                return

    # Define the MCP config based on the --uv flag
    if uv:
        mcp_config = {"mcpServers": {server_name: {"command": "uv", "args": ["run", "hex-mcp", "run"]}}}
    else:
        mcp_config = {"mcpServers": {server_name: {"command": "hex-mcp", "args": ["run"]}}}

    # Preview mode - just show the configuration
    if preview:
        typer.echo("Preview of MCP configuration:")
        typer.echo(json.dumps(mcp_config, indent=2))
        typer.echo(f"\nServer name: {server_name}")
        typer.echo(f"Command: {'uv run hex-mcp run' if uv else 'hex-mcp run'}")
        return

    # Create .cursor directory if it doesn't exist
    cursor_dir = Path(".cursor")
    os.makedirs(cursor_dir, exist_ok=True)

    # Check if file already exists
    mcp_config_path = cursor_dir / "mcp.json"
    if mcp_config_path.exists() and not force:
        overwrite = typer.confirm(f"Configuration file {mcp_config_path} already exists. Overwrite?", default=False)
        if not overwrite:
            typer.echo("Installation cancelled.")
            return

    # Write the configuration file
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_config, f, indent=2)

    typer.echo(f"MCP configuration installed to {mcp_config_path}")
    typer.echo(f"Server name: {server_name}")
    typer.echo(f"Command: {'uv run hex-mcp run' if uv else 'hex-mcp run'}")


# Keep this to maintain backward compatibility with the entry point
def main_entry():
    """Entry point for the package."""
    app()


# Optionally expose other important items at package level
__all__ = ["main_entry", "server"]
