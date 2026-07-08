# Frequently Asked Questions (FAQ)

## 1. Why are some commands not showing up in my server?
Slash commands take up to an hour to sync globally across Discord. If you need commands immediately in a specific testing server, set the `DISCORD_DEV_GUILD_ID` in your `.env` file and restart the bot. The bot will sync commands instantly to that specific guild on startup.

## 2. The Dashboard shows "Unauthorized" when I log in. What's wrong?
Ensure your `OAUTH2_REDIRECT_URI` exactly matches the one configured in the Discord Developer Portal under OAuth2 -> Redirects. It should look like `https://your-domain.com/api/auth/callback`. Also, verify your `JWT_SECRET_KEY` is set correctly in `.env`.

## 3. How do I give myself Administrator access on the Dashboard?
The bot automatically grants full Dashboard access to the user IDs listed in the `BOT_OWNER_IDS` environment variable. Ensure your Discord ID is in that comma-separated list. Otherwise, you must have the `Administrator` permission natively inside the Discord server to manage its settings on the dashboard.

## 4. Why aren't images rendering in PDF Transcripts?
PDF Generation relies on WeasyPrint and system libraries like Pango and Cairo. If you installed manually, ensure you ran `apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0`. Docker installations include these automatically.

## 5. Can I run this on a Raspberry Pi?
Yes, but you will need to build the Docker images manually or install dependencies locally. Ensure you have at least 2GB of RAM or configure a large swap file, as the Next.js frontend build process is memory-intensive.

## 6. How do I change the rate limits?
API rate limits are handled by Nginx in production. Edit `/etc/nginx/sites-available/discord-bot` (or `nginx/nginx.conf` for Docker) and modify the `limit_req_zone` directives at the top of the file. Restart Nginx to apply changes.
