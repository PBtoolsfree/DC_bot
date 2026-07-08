"""Repository for security data."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.security import IncidentReport, SecuritySnapshot


class SecurityRepository:
    """Handles database operations for security models."""

    @staticmethod
    async def create_incident(
        session: AsyncSession,
        guild_id: int,
        action: str,
        executor_id: int | None = None,
        target_id: int | None = None,
        reason: str | None = None,
        case_id: int | None = None,
        rollback_status: str = "NONE",
        metadata_json: dict[str, Any] | None = None,
    ) -> IncidentReport:
        """Create a new incident report."""
        incident = IncidentReport(
            guild_id=guild_id,
            action=action,
            executor_id=executor_id,
            target_id=target_id,
            reason=reason,
            case_id=case_id,
            rollback_status=rollback_status,
            metadata_json=metadata_json or {},
        )
        session.add(incident)
        await session.flush()
        return incident

    @staticmethod
    async def get_recent_incidents(
        session: AsyncSession,
        guild_id: int,
        limit: int = 50,
    ) -> Sequence[IncidentReport]:
        """Fetch recent incidents for the Incident Timeline."""
        stmt = (
            select(IncidentReport)
            .where(IncidentReport.guild_id == guild_id)
            .order_by(desc(IncidentReport.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def update_incident_rollback_status(
        session: AsyncSession,
        incident_id: int,
        status: str,
    ) -> IncidentReport | None:
        """Update the rollback status of an incident."""
        incident = await session.get(IncidentReport, incident_id)
        if incident:
            incident.rollback_status = status
            await session.flush()
        return incident

    @staticmethod
    async def create_snapshot(
        session: AsyncSession,
        guild_id: int,
        name: str,
        created_by_id: int,
        snapshot_data: dict[str, Any],
        is_auto: bool = False,
    ) -> SecuritySnapshot:
        """Create a new server snapshot."""
        snapshot = SecuritySnapshot(
            guild_id=guild_id,
            name=name,
            created_by_id=created_by_id,
            snapshot_data=snapshot_data,
            is_auto=is_auto,
        )
        session.add(snapshot)
        await session.flush()
        return snapshot

    @staticmethod
    async def get_snapshots(
        session: AsyncSession,
        guild_id: int,
        limit: int = 10,
    ) -> Sequence[SecuritySnapshot]:
        """Get the latest snapshots for a guild."""
        stmt = (
            select(SecuritySnapshot)
            .where(SecuritySnapshot.guild_id == guild_id)
            .order_by(desc(SecuritySnapshot.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
