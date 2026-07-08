"""API v1 Router Setup."""

from fastapi import APIRouter

from dashboard.backend.api.v1 import auth, guilds, members, settings, logs, ws, analytics, verification, tickets, backups, welcome, roles, xp

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(guilds.router, prefix="/guilds", tags=["Guilds"])
router.include_router(members.router, prefix="/members", tags=["RBAC"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(logs.router, prefix="/logs", tags=["Logs"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(verification.router, prefix="/verification", tags=["Verification"])
router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
router.include_router(backups.router, prefix="/backups", tags=["Backups"])
router.include_router(welcome.router, prefix="/welcome", tags=["Welcome"])
router.include_router(roles.router, prefix="/roles", tags=["Roles"])
router.include_router(xp.router, prefix="/xp", tags=["XP"])
router.include_router(ws.router, prefix="/ws", tags=["WebSockets"])
