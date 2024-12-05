# backend/app/plugins/machines/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid
import re

class MachineStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    INITIALIZING = "initializing"
    MAINTENANCE = "maintenance"

class SystemMetrics(BaseModel):
    cpu_usage: float  # Percentage
    cpu_cores: int
    memory_total: int  # Bytes
    memory_used: int  # Bytes
    memory_free: int  # Bytes
    disk_total: int  # Bytes
    disk_used: int  # Bytes
    disk_free: int  # Bytes
    network_rx_bytes: int  # Total received bytes
    network_tx_bytes: int  # Total transmitted bytes
    docker_status: bool
    docker_containers: int
    docker_running: int
    load_average: List[float]  # 1, 5, 15 minute load averages
    uptime: int  # Seconds
    last_update: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @property
    def memory_usage_percent(self) -> float:
        return (self.memory_used / self.memory_total) * 100 if self.memory_total > 0 else 0

    @property
    def disk_usage_percent(self) -> float:
        return (self.disk_used / self.disk_total) * 100 if self.disk_total > 0 else 0

class SSHKey(BaseModel):
    private_key: str
    public_key: Optional[str] = None
    passphrase: Optional[str] = None

    @validator('private_key')
    def validate_private_key(cls, v: str) -> str:
        if not v.strip().startswith('-----BEGIN'):
            raise ValueError("Invalid SSH private key format")
        return v.strip()

class NetworkConfig(BaseModel):
    interface: str
    ip_address: str
    netmask: str
    gateway: Optional[str] = None
    dns_servers: List[str] = Field(default_factory=list)
    mtu: int = 1500

    @validator('ip_address')
    def validate_ip_address(cls, v: str) -> str:
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        if not ip_pattern.match(v):
            raise ValueError("Invalid IP address format")
        return v

class CommandResult(BaseModel):
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration: float  # Seconds
    command: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Machine(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    ip_address: str
    ssh_key: SSHKey
    ssh_port: int = 22
    ssh_user: str = "ubuntu"
    status: MachineStatus = MachineStatus.INITIALIZING
    system_info: Optional[SystemMetrics] = None
    network_config: Optional[NetworkConfig] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    owner_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None

    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not 3 <= len(v) <= 64:
            raise ValueError("Name must be between 3 and 64 characters")
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-_]*$', v):
            raise ValueError("Name must start with alphanumeric and contain only letters, numbers, hyphens, and underscores")
        return v

    @validator('ip_address')
    def validate_ip_address(cls, v: str) -> str:
        ip_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        if not ip_pattern.match(v):
            raise ValueError("Invalid IP address format")
        return v

    @validator('ssh_port')
    def validate_ssh_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("SSH port must be between 1 and 65535")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MachineCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ip_address: str
    ssh_key: SSHKey
    ssh_port: int = 22
    ssh_user: str = "ubuntu"
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_key: Optional[SSHKey] = None
    ssh_port: Optional[int] = None
    ssh_user: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

class CommandRequest(BaseModel):
    command: str
    working_dir: Optional[str] = None
    timeout: int = 30
    sudo: bool = False
    machines: Optional[List[str]] = None  # Machine IDs, if None - run on all machines
    env: Dict[str, str] = Field(default_factory=dict)

    @validator('timeout')
    def validate_timeout(cls, v: int) -> int:
        if not 1 <= v <= 3600:
            raise ValueError("Timeout must be between 1 and 3600 seconds")
        return v