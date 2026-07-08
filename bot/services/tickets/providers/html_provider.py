"""HTML Transcript Provider."""

from jinja2 import BaseLoader, Environment

from bot.database.models.tickets import Ticket, TicketMessage
from bot.services.tickets.providers.base import TranscriptProvider

# Minimal HTML template for transcripts
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ticket {{ ticket.id }}</title>
    <style>
        body { font-family: sans-serif; background: #36393f; color: #dcddde; padding: 20px; }
        .header { border-bottom: 1px solid #202225; padding-bottom: 10px; margin-bottom: 20px; }
        .message { margin-bottom: 20px; }
        .author { font-weight: bold; color: #fff; }
        .time { font-size: 0.8em; color: #72767d; margin-left: 10px; }
        .content { margin-top: 5px; }
        .attachment { color: #00b0f4; }
    </style>
</head>
<body>
    <div class="header">
        <h2>Ticket Transcript: #{{ ticket.id }}</h2>
        <p>Owner ID: {{ ticket.owner_id }} | Status: {{ ticket.status }}</p>
    </div>
    
    <div class="messages">
        {% for m in messages %}
        <div class="message">
            <div>
                <span class="author">{{ m.author_name }}</span>
                <span class="time">{{ m.timestamp.strftime('%Y-%m-%d %H:%M:%S') }}</span>
            </div>
            <div class="content">{{ m.content }}</div>
            {% if m.attachments %}
            <div class="attachments">
                {% for att in m.attachments %}
                <a href="{{ att }}" class="attachment">[Attachment]</a>
                {% endfor %}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""


class HTMLTranscriptProvider(TranscriptProvider):
    """Generates an HTML transcript."""

    @property
    def extension(self) -> str:
        return ".html"

    async def generate(self, ticket: Ticket, messages: list[TicketMessage]) -> bytes:
        """Generate HTML using Jinja2."""

        env = Environment(loader=BaseLoader())
        template = env.from_string(HTML_TEMPLATE)

        html = template.render(ticket=ticket, messages=messages)
        return html.encode("utf-8")
