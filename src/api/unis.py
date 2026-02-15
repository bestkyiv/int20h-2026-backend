from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from src.db.core import get_session
from src.db.models import University

router = APIRouter()


@router.get("/unis/")
async def get_universities(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(University).order_by(University.name))
    universities = result.scalars().all()
    return {"universities": universities}
