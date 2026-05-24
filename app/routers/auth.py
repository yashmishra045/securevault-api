from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import uuid
from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, RefreshRequest
from app.services.jwt_service import create_access_token, create_refresh_token, verify_token
from app.services.audit_service import log_action
from app.models.audit_log import AuditAction
from app.dependencies import get_current_user, get_client_ip
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

@router.post('/register', response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail='Email already registered')
    role_result = await db.execute(select(Role).where(Role.name == 'viewer'))
    default_role = role_result.scalar_one_or_none()
    user = User(id=str(uuid.uuid4()), email=body.email, hashed_password=hash_password(body.password), role_id=default_role.id if default_role else None)
    db.add(user)
    await db.flush()
    await log_action(db=db, action=AuditAction.USER_CREATED, ip_address=get_client_ip(request), user_id=user.id)
    return user

@router.post('/login', response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        await log_action(db=db, action=AuditAction.AUTH_FAILED, ip_address=get_client_ip(request), user_id=user.id if user else None, success=False)
        raise HTTPException(status_code=401, detail='Invalid email or password')
    if not user.is_active:
        raise HTTPException(status_code=401, detail='Account deactivated')
    role_name = user.role.name if user.role else 'viewer'
    access_token = create_access_token(user.id, role_name)
    refresh_token = create_refresh_token(user.id)
    user.refresh_token = refresh_token
    await log_action(db=db, action=AuditAction.USER_LOGIN, ip_address=get_client_ip(request), user_id=user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@router.post('/refresh', response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_token(body.refresh_token, expected_type='refresh')
    result = await db.execute(select(User).where(User.id == payload['sub']))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
    role_name = user.role.name if user.role else 'viewer'
    new_access = create_access_token(user.id, role_name)
    new_refresh = create_refresh_token(user.id)
    user.refresh_token = new_refresh
    return TokenResponse(access_token=new_access, refresh_token=new_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@router.post('/logout', status_code=204)
async def logout(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.refresh_token = None
    await log_action(db=db, action=AuditAction.USER_LOGOUT, ip_address=get_client_ip(request), user_id=current_user.id)
