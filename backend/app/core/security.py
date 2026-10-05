from secrets import compare_digest
from fastapi import Header, HTTPException
from app.core.config import settings


def require_access(authorization: str = Header(default="")):
    if settings.demo_access_token and not compare_digest(
        authorization, "Bearer " + settings.demo_access_token
    ):
        raise HTTPException(401, "Enter the demo access token to use this server.")
