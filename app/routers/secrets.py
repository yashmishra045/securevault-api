from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user import User
from app.models.secret import Secret
from app.models.audit_log import AuditAction
from app.schemas.secret import SecretCreateRequest, SecretUpdateRequest, SecretResponse, SecretDecryptedResponse, SecretListResponse
from app.services.crypto import encrypt_secret, decrypt_secret
from app.services.audit_service import log_action
from app.dependencies import get_current_user, get_client_ip
from app.config import settings

router = APIRouter()

@router.post('', response_model=SecretResponse, status_code=201)
async def create_secret(body: SecretCreateRequest, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Secret).where(Secret.user_id == current_user.id, Secret.name == body.name, Secret.is_deleted == False))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Secret '{body.name}' already exists")
    encrypted_value, iv = encrypt_secret(body.value)
    secret = Secret(user_id=current_user.id, name=body.name, encrypted_value=encrypted_value, iv=iv)
    db.add(secret)
    await db.flush()
    await log_action(db=db, action=AuditAction.SECRET_CREATED, ip_address=get_client_ip(request), user_id=current_user.id, secret_name=body.name)
    return secret

@router.get('', response_model=SecretListResponse)
async def list_secrets(page: int = 1, page_size: int = 20, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    page_size = min(page_size, settings.MAX_PAGE_SIZE)
    offset = (page - 1) * page_size
    base_query = select(Secret).where(Secret.user_id == current_user.id, Secret.is_deleted == False)
    total = (await db.execute(select(func.count()).select_from(base_query.subquery()))).scalar()
    result = await db.execute(base_query.order_by(Secret.created_at.desc()).offset(offset).limit(page_size))
    return SecretListResponse(secrets=result.scalars().all(), total=total, page=page, page_size=page_size)

@router.get('/{name}', response_model=SecretDecryptedResponse)
async def get_secret(name: str, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Secret).where(Secret.user_id == current_user.id, Secret.name == name.upper(), Secret.is_deleted == False))
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
    plaintext = decrypt_secret(secret.encrypted_value, secret.iv)
    await log_action(db=db, action=AuditAction.SECRET_READ, ip_address=get_client_ip(request), user_id=current_user.id, secret_name=name)
    return SecretDecryptedResponse(id=secret.id, name=secret.name, value=plaintext, created_at=secret.created_at)

@router.put('/{name}', response_model=SecretResponse)
async def update_secret(name: str, body: SecretUpdateRequest, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Secret).where(Secret.user_id == current_user.id, Secret.name == name.upper(), Secret.is_deleted == False))
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
    secret.encrypted_value, secret.iv = encrypt_secret(body.value)
    await log_action(db=db, action=AuditAction.SECRET_UPDATED, ip_address=get_client_ip(request), user_id=current_user.id, secret_name=name)
    return secret

@router.delete('/{name}', status_code=204)
async def delete_secret(name: str, request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Secret).where(Secret.user_id == current_user.id, Secret.name == name.upper(), Secret.is_deleted == False))
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
    secret.is_deleted = True
    await log_action(db=db, action=AuditAction.SECRET_DELETED, ip_address=get_client_ip(request), user_id=current_user.id, secret_name=name)
