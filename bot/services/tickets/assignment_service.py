"""Assignment Engine Service."""

import discord
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models.tickets import Ticket, TicketCategory


class AssignmentService:
    """Handles automatic ticket routing to staff members."""

    @staticmethod
    async def assign_least_loaded(
        session: AsyncSession, guild: discord.Guild, ticket: Ticket, category: TicketCategory
    ) -> int | None:
        """Assign the ticket to the staff member with the fewest open tickets."""

        # 1. Gather all potential staff from the category's roles
        potential_staff_ids = set()
        for role_id in category.support_team_roles:
            role = guild.get_role(role_id)
            if role:
                for member in role.members:
                    potential_staff_ids.add(member.id)

        if not potential_staff_ids:
            return None  # Nobody to assign

        # 2. Find their active ticket counts
        stmt = (
            select(Ticket.claimed_by_id, func.count(Ticket.id))
            .where(Ticket.guild_id == guild.id)
            .where(Ticket.status.in_(["open", "in_progress", "waiting_user", "waiting_staff"]))
            .where(Ticket.claimed_by_id.in_(list(potential_staff_ids)))
            .group_by(Ticket.claimed_by_id)
        )

        result = await session.execute(stmt)
        workloads = {row[0]: row[1] for row in result.all()}

        # Find the staff member with the minimum workload
        least_loaded_staff = None
        min_workload = float("inf")

        for staff_id in potential_staff_ids:
            current_workload = workloads.get(staff_id, 0)
            if current_workload < min_workload:
                min_workload = current_workload
                least_loaded_staff = staff_id

        return least_loaded_staff  # type: ignore
