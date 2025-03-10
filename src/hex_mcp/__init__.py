from . import server
import os
import sys
import importlib.metadata
import typer
from typing import Optional
from dotenv import load_dotenv

# Load from .env file first, will be overridden by CLI args
load_dotenv()

app = typer.Typer(help="Hex MCP Server - Model Context Protocol server for Hex")


def version_callback(value: bool):
    """Print version and exit"""
    if value:
        version = importlib.metadata.version("hex-mcp")
        typer.echo(f"hex-mcp version {version}")
        raise typer.Exit()


@app.callback()
def main(
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="Hex API Key (overrides HEX_API_KEY environment variable)"
    ),
    api_url: Optional[str] = typer.Option(
        None, "--api-url", help="Hex API URL (overrides HEX_API_URL environment variable)"
    ),
    server_name: str = typer.Option("Hex MCP Server", "--server-name", help="Custom name for the MCP server"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True, help="Show the version of hex-mcp"
    ),
):
    """Main entry point for the Hex MCP Server.

    Provides a CLI to run the Hex MCP server with configurable environment variables.
    """
    # Set up logging
    if verbose:
        os.environ["MCP_LOG_LEVEL"] = "DEBUG"

    # Override environment variables if provided
    if api_key:
        os.environ["HEX_API_KEY"] = api_key

    if api_url:
        os.environ["HEX_API_URL"] = api_url

    # Update server name if provided
    if server_name != "Hex MCP Server":
        server.mcp.name = server_name


@app.command()
def run():
    """Run the MCP server normally."""
    typer.echo(f"Starting {server.mcp.name}...")
    server.mcp.run()


@app.command()
def dev(port: int = typer.Option(8765, help="Port for development server")):
    """Run in development mode with the MCP Inspector."""
    try:
        from mcp.cli.inspector import run_inspector

        typer.echo(f"Starting {server.mcp.name} in development mode on port {port}...")
        run_inspector(server_module="hex_mcp.server", server_object="mcp", port=port)
    except ImportError:
        typer.echo("Development mode requires mcp[cli] extra. Install with 'pip install \"mcp[cli]\"'")
        raise typer.Exit(code=1)


# Keep this to maintain backward compatibility with the entry point
def main_entry():
    """Entry point for the package."""
    app()


# Optionally expose other important items at package level
__all__ = ["main_entry", "server"]
