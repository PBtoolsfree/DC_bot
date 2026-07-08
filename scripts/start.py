"""Helper script to start the bot with environment validation.

Usage:
    python scripts/start.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def check_environment() -> bool:
    """Validate that all required environment variables are set.

    Returns:
        True if all checks pass, False otherwise.
    """
    env_file = project_root / ".env"

    if not env_file.exists():
        print("ERROR: .env file not found!")
        print("  → Copy .env.example to .env and fill in your values.")
        print(f"  → Expected location: {env_file}")
        return False

    # Check critical variables
    from dotenv import load_dotenv

    load_dotenv(env_file)

    required_vars = ["DISCORD_TOKEN"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("  → Update your .env file with the missing values.")
        return False

    token = os.getenv("DISCORD_TOKEN", "")
    if token == "your_discord_bot_token_here" or len(token) < 50:
        print("ERROR: DISCORD_TOKEN appears to be a placeholder or invalid.")
        print("  → Get your bot token from https://discord.com/developers/applications")
        return False

    return True


def main() -> None:
    """Run pre-flight checks and start the bot."""
    print("=" * 60)
    print("  Discord Management Platform — Startup")
    print("=" * 60)
    print()

    print("[1/3] Checking environment...")
    if not check_environment():
        sys.exit(1)
    print("  ✓ Environment OK")

    print("[2/3] Checking dependencies...")
    try:
        import discord  # noqa: F401
        import sqlalchemy  # noqa: F401
        import structlog  # noqa: F401

        print("  ✓ Core dependencies OK")
    except ImportError as e:
        print(f"  ✗ Missing dependency: {e.name}")
        print("  → Run: pip install -r requirements.txt")
        sys.exit(1)

    print("[3/3] Starting bot...")
    print()

    import asyncio

    from bot.main import main as bot_main

    asyncio.run(bot_main())


if __name__ == "__main__":
    main()
