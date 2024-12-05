from pydantic import BaseModel, Field
from typing import Optional

class MachineCreate(BaseModel):
    name: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(22, ge=1, le=65535)
    user: str = Field(..., min_length=1)
    password: Optional[str] = None
    ssh_key: Optional[str] = None
