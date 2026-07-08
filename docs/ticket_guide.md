# Enterprise Ticket System Guide

The Ticket System (Module 8) provides enterprise-grade customer support capabilities directly within Discord, fully integrated with your web dashboard and logging modules.

## Architecture & Workflows

### 1. Hybrid Message Storage
Active tickets store raw messages inside the database (`TicketMessage`). When a ticket is archived, a background task generates the transcripts and safely purges the raw messages to prevent database bloat, keeping your database lightweight.

### 2. Transcript Providers
The system supports multiple dynamic transcript outputs:
- **HTML**: Rendered via Jinja2 templates for web dashboards.
- **PDF**: Rendered using WeasyPrint (requires GTK on host).
- **JSON**: Raw payload generation for API exports.
- **Markdown**: Lightweight transcripts for Discord text previews.

### 3. Relay Mode (Anonymous Tickets)
Users can open completely anonymous tickets. The bot acts as an intermediary, capturing DMs from the user and relaying them to a private staff channel, effectively hiding the user's Discord profile from support teams. The linkage is managed securely via Redis in the `RelayService`.

### 4. Assignment Engine
Tickets are automatically routed to the staff member with the lowest current workload (Least Loaded routing) using the `AssignmentService`.

### 5. SLA Engine
Every `TicketCategory` defines an `sla_response_hours`. If a ticket sits in `open` or `waiting_staff` beyond this limit, the `TicketAutomationsTask` will trigger a WebSocket `SLA_BREACH` event and alert the channel.

## Dashboard Integration
Manage panels, categories, and SLA configurations entirely from the SaaS Dashboard. Real-time statistics (Top Staff, Open Tickets, Category Distribution) are exposed via `/api/v1/tickets`.
