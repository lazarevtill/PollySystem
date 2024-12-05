# app/plugins/machines/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class MachineBase(BaseModel):
    name: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(22, ge=1, le=65535)
    user: str = Field(..., min_length=1)

class MachineCreate(MachineBase):
    password: Optional[str] = None
    ssh_key: Optional[str] = None

    @validator('ssh_key')
    def validate_ssh_key(cls, v):
        if v is not None:
            v = v.strip()
            if not ('BEGIN' in v and 'PRIVATE KEY' in v and 'END' in v):
                raise ValueError("Invalid SSH key format. Must be a private key file.")
        return v

    @validator('*')
    def no_empty_strings(cls, v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ValueError("Field cannot be empty")
        return v

class MachineResponse(MachineBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MachineMetrics(BaseModel):
    cpu_usage_percent: float
    memory_used_mb: int
    memory_total_mb: int
    status: str = "ok"
    error: Optional[str] = None

class StatusResponse(BaseModel):
    status: str