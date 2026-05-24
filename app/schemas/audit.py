from pydantic import BaseModel
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    secret_name: str | None = None
    ip_address: str
    success: bool
    timestamp: datetime
    model_config = {'from_attributes': True}

class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
