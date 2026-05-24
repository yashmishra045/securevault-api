from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog, AuditAction

async def log_action(db: AsyncSession, action: AuditAction, ip_address: str, user_id: str | None = None, secret_name: str | None = None, success: bool = True, metadata: str | None = None) -> None:
    entry = AuditLog(user_id=user_id, action=action, secret_name=secret_name, ip_address=ip_address, success=success, metadata_=metadata)
    db.add(entry)
