from . import server
import asyncio
from dotenv import load_dotenv

load_dotenv()


def main():
    """Main entry point for the package."""
    server.mcp.run()


# Optionally expose other important items at package level
__all__ = ["main", "server"]
