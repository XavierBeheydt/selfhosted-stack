"""Main entry point for Hosts Filter service."""

import uvicorn
from .api import app
from .config import Config


def main() -> None:
    """Main entry point for the Hosts Filter service."""
    config = Config()
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
    )


if __name__ == "__main__":
    main()
