# Security Policy

## Supported Versions

Currently, only the `main` branch (v1.x) receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within the Enterprise Discord Management Platform, please **DO NOT** open a public issue.

Instead, please send a direct message to the maintainers or email the project owner.

Please include the following information in your report:
*   Type of vulnerability (e.g., XSS, SQLi, Auth Bypass)
*   Steps to reproduce the vulnerability
*   Impact of the vulnerability

We aim to acknowledge all reports within 48 hours and will keep you updated on the progress towards a fix.

## Security Best Practices for Deployment

When deploying the platform, ensure you follow these rules to maintain a secure environment:

1.  **Never expose `.env`**: Ensure your `.env` file is strictly `chmod 600`.
2.  **Use strong secrets**: Generate your `JWT_SECRET_KEY` and database passwords using cryptographically secure methods (e.g., `openssl rand -hex 32`).
3.  **Restrict API access**: Use the Nginx reverse proxy configuration provided in the deployment scripts. Do not expose Uvicorn (port 8000) directly to the internet.
4.  **Use HTTPS**: Always use SSL/TLS for the dashboard and API to protect JWT tokens in transit. The automated installer handles this via Certbot.
5.  **Keep dependencies updated**: Regularly run the `update.sh` script to pull the latest security patches for Python and Node dependencies.
