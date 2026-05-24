from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.audit_log import AuditAction
from app.schemas.auth import UserResponse
from app.services.audit_service import log_action
from app.dependencies import require_permission, get_client_ip
from app.models.role import Permission

router = APIRouter()

class AssignRoleRequest(BaseModel):
    role_name: str

class CreateRoleRequest(BaseModel):
    name: str
    permissions: list[str]

@router.get('/users', response_model=list[UserResponse])
async def list_users(admin=Depends(require_permission(Permission.USER_MANAGE)), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()

@router.post('/users/{user_id}/role', response_model=UserResponse)
async def assign_role(user_id: str, body: AssignRoleRequest, request: Request, admin=Depends(require_permission(Permission.USER_MANAGE)), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    role = (await db.execute(select(Role).where(Role.name == body.role_name))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{body.role_name}' not found")
    user.role_id = role.id
    await log_action(db=db, action=AuditAction.ROLE_ASSIGNED, ip_address=get_client_ip(request), user_id=admin.id, metadata=f"Assigned '{role.name}' to {user_id}")
    return user

@router.post('/roles', status_code=201)
async def create_role(body: CreateRoleRequest, admin=Depends(require_permission(Permission.USER_MANAGE)), db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(Role).where(Role.name == body.name))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Role '{body.name}' already exists")
    role = Role(name=body.name, permissions=body.permissions)
    db.add(role)
    await db.flush()
    return {'id': role.id, 'name': role.name, 'permissions': role.permissions}

@router.get('/roles')
async def list_roles(admin=Depends(require_permission(Permission.USER_MANAGE)), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role))
    return [{'id': r.id, 'name': r.name, 'permissions': r.permissions} for r in result.scalars().all()]
