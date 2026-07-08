"""Service for exporting logs to CSV, JSON, and HTML."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from bot.database.models.logging import ActionLog


class ExportService:
    """Handles parsing ActionLogs into downloadable formats."""

    @staticmethod
    def _sanitize_for_csv(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return str(val)

    @staticmethod
    def generate_csv(logs: Sequence[ActionLog]) -> io.StringIO:
        """Generate a CSV buffer from logs."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "ID",
                "Guild ID",
                "Correlation ID",
                "Action Type",
                "Severity",
                "Executor ID",
                "Target ID",
                "Channel ID",
                "Created At",
                "Before Data",
                "After Data",
            ]
        )

        for log in logs:
            writer.writerow(
                [
                    log.id,
                    log.guild_id,
                    log.correlation_id,
                    log.action_type,
                    log.severity,
                    log.executor_id,
                    log.target_id,
                    log.channel_id,
                    log.created_at.isoformat() if log.created_at else "",
                    ExportService._sanitize_for_csv(log.before_data),
                    ExportService._sanitize_for_csv(log.after_data),
                ]
            )

        output.seek(0)
        return output

    @staticmethod
    def generate_json(logs: Sequence[ActionLog]) -> str:
        """Generate a JSON string from logs."""
        data = []
        for log in logs:
            data.append(
                {
                    "id": log.id,
                    "guild_id": log.guild_id,
                    "correlation_id": log.correlation_id,
                    "action_type": log.action_type,
                    "severity": log.severity,
                    "executor_id": log.executor_id,
                    "target_id": log.target_id,
                    "channel_id": log.channel_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                    "before_data": log.before_data,
                    "after_data": log.after_data,
                    "metadata": log.metadata_json,
                }
            )

        return json.dumps(data, indent=2)

    @staticmethod
    def generate_html(logs: Sequence[ActionLog]) -> str:
        """Generate a simple HTML timeline from logs."""
        html = [
            "<!DOCTYPE html>",
            "<html><head><title>Audit Logs</title>",
            "<style>body { font-family: sans-serif; } "
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; } "
            "th { background-color: #f2f2f2; }</style>",
            "</head><body>",
            "<h2>Server Audit Logs</h2>",
            "<table><tr><th>Time</th><th>Action</th><th>Executor</th><th>Target</th><th>Details</th></tr>",
        ]

        for log in logs:
            time_str = log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "N/A"
            details = (
                f"Before: {log.before_data}<br>After: {log.after_data}"
                if (log.before_data or log.after_data)
                else ""
            )

            html.append(
                f"<tr><td>{time_str}</td><td>{log.action_type}</td>"
                f"<td>{log.executor_id or 'Unknown'}</td><td>{log.target_id or 'N/A'}</td>"
                f"<td>{details}</td></tr>"
            )

        html.append("</table></body></html>")
        return "\n".join(html)
