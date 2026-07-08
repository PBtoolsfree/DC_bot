# Contributing Guide

Thank you for your interest in contributing to the Enterprise Discord Management Platform!

## Branching Strategy

*   `main`: Stable production branch. Only accepts Pull Requests from `develop`.
*   `develop`: Integration branch for new features and bug fixes.
*   `feature/*`: Feature branches (e.g., `feature/custom-logging`).
*   `bugfix/*`: Bug fix branches (e.g., `bugfix/dashboard-auth`).

## Setting Up for Development

1.  **Fork and Clone:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/discord-management-platform.git
    cd discord-management-platform
    ```

2.  **Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov ruff black mypy
    ```

3.  **Database:**
    We recommend using Docker for your local test database:
    ```bash
    docker run -d --name dmp-postgres -e POSTGRES_USER=discord_bot -e POSTGRES_PASSWORD=devpass -e POSTGRES_DB=discord_bot -p 5432:5432 postgres:16-alpine
    ```

4.  **Configuration:**
    Copy `.env.production` to `.env` and adjust the `DATABASE_URL` to point to your local container. Set `ENVIRONMENT=development` and `DEBUG=true`.

## Coding Standards

This project enforces strict coding standards via GitHub Actions CI. Before committing, ensure you run:

```bash
# 1. Format code
black bot/ dashboard/ tests/

# 2. Lint code
ruff check bot/ dashboard/ tests/ --fix

# 3. Type checking
mypy bot/

# 4. Run tests
pytest tests/ -v
```

All Pull Requests must pass the CI pipeline to be merged.

## Submitting a Pull Request

1.  Create a branch from `develop`.
2.  Make your changes. Add tests for any new logic.
3.  Ensure all checks pass locally.
4.  Submit a PR targeting the `develop` branch.
5.  Provide a clear description of the problem solved or feature added.
