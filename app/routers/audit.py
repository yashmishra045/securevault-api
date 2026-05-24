from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.role import Permission
from app.schemas.audit import AuditLogListResponse
from app.dependencies import require_permission
from app.config import settings

router = APIRouter()

@router.get('', response_model=AuditLogListResponse)
async def get_all_logs(page: int = 1, page_size: int = 20, admin=Depends(require_permission(Permission.AUDIT_VIEW)), db: AsyncSession = Depends(get_db)):
    page_size = min(page_size, settings.MAX_PAGE_SIZE)
    offset = (page - 1) * page_size
    base_query = select(AuditLog)
    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar()
    result = await db.execute(base_query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size))
    return AuditLogListResponse(logs=result.scalars().all(), total=total, page=page, page_size=page_size)

@router.get('/{user_id}', response_model=AuditLogListResponse)
async def get_user_logs(user_id: str, page: int = 1, page_size: int = 20, admin=Depends(require_permission(Permission.AUDIT_VIEW)), db: AsyncSession = Depends(get_db)):
    page_size = min(page_size, settings.MAX_PAGE_SIZE)
    offset = (page - 1) * page_size
    base_query = select(AuditLog).where(AuditLog.user_id == user_id)
    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar()
    result = await db.execute(base_query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size))
    return AuditLogListResponse(logs=result.scalars().all(), total=total, page=page, page_size=page_size)
