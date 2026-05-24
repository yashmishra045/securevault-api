from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter()

@router.get("")
async def liveness():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}

@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ready" if db_status == "ok" else "not_ready", "checks": {"database": db_status}}
