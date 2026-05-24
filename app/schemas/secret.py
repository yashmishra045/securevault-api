from pydantic import BaseModel, field_validator
from datetime import datetime
import re

class SecretCreateRequest(BaseModel):
    name: str
    value: str

    @field_validator('name')
    @classmethod
    def name_format(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_\-]{1,255}$', v):
            raise ValueError('Name: letters, numbers, _ or - only')
        return v.upper()

class SecretUpdateRequest(BaseModel):
    value: str

class SecretResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime | None = None
    model_config = {'from_attributes': True}

class SecretDecryptedResponse(BaseModel):
    id: str
    name: str
    value: str
    created_at: datetime
    model_config = {'from_attributes': True}

class SecretListResponse(BaseModel):
    secrets: list[SecretResponse]
    total: int
    page: int
    page_size: int
