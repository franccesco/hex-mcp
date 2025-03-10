from . import server
import importlib.metadata
import typer
from typing import Optional
import os
import yaml
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
    typer.echo(f"Starting {server.mcp.name}...")
    server.mcp.run()


@app.command()
def config(
    api_key: str = typer.Option(..., help="API key for Hex authentication"),
    api_url: str = typer.Option("https://app.hex.tech", help="Hex API URL"),
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


# Keep this to maintain backward compatibility with the entry point
def main_entry():
    """Entry point for the package."""
    app()


# Optionally expose other important items at package level
__all__ = ["main_entry", "server"]
