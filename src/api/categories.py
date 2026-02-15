from fastapi import APIRouter, Depends

from src.db.models import Category
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.db.core import get_session

router = APIRouter()


@router.get("/categories/")
async def get_categories(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Category).order_by(Category.name))
    categories = result.scalars().all()
    return {"categories": categories}
