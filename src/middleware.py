from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.config import Settings
from src.logging_singleton import get_logger

logger = get_logger(__name__)


class RegistrationDeadlineMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        deadline_str = settings.REGISTRATION_END_DATE
        # Replace Z with +00:00 so fromisoformat handles it on all Python 3.x versions.
        # Semantically equivalent: Z = UTC offset +00:00.
        self._deadline: datetime = datetime.fromisoformat(
            deadline_str.replace("Z", "+00:00")
        )
        logger.info("Registration deadline set to %s", self._deadline.isoformat())

    async def dispatch(self, request: Request, call_next):
        now = datetime.now(timezone.utc)
        if now > self._deadline:
            logger.info(
                "Request blocked — registration closed (now=%s, deadline=%s)",
                now.isoformat(),
                self._deadline.isoformat(),
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Реєстрацію завершено."},
            )
        return await call_next(request)
