from fastapi import APIRouter

from .routes import (
    admins,
    auth,
    faq,
    files,
    forms,
    kb,
    messages,
    monitoring,
    profile,
    settings,
    stats,
    submissions,
    tickets,
    users,
    ws,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(forms.router, prefix="/forms", tags=["forms"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(faq.router, prefix="/faq", tags=["faq"])
api_router.include_router(kb.router, prefix="/kb", tags=["kb"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(admins.router, prefix="/admins", tags=["admins"])
api_router.include_router(ws.router, tags=["ws"])
