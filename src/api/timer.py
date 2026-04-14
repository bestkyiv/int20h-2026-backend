from fastapi import APIRouter
from src.config import Settings

router = APIRouter()


@router.get("/timer/")
async def get_timer():
    settings = Settings()
    return {
        "remaining_time": settings.REMAINING_TIME,
        "is_running": settings.IS_RUNNING,
    }
