# backend/app/plugins/docker/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import uuid
import re

class ContainerState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    EXITED = "exited"
    DEAD = "dead"
    CREATED = "created"

class NetworkMode(str, Enum):
    BRIDGE = "bridge"
    HOST = "host"
    NONE = "none"
    CUSTOM = "custom"

class PortMapping(BaseModel):
    host_port: int
    container_port: int
    protocol: str = "tcp"

    @validator('host_port', 'container_port')
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator('protocol')
    def validate_protocol(cls, v: str) -> str:
        if v.lower() not in ['tcp', 'udp']:
            raise ValueError("Protocol must be either TCP or UDP")
        return v.lower()

class VolumeMount(BaseModel):
    host_path: str
    container_path: str
    mode: str = "rw"

    @validator('mode')
    def validate_mode(cls, v: str) -> str:
        if v not in ['rw', 'ro']:
            raise ValueError("Volume mode must be either 'rw' or 'ro'")
        return v

class ContainerResources(BaseModel):
    cpu_limit: Optional[float] = None  # Number of CPUs
    memory_limit: Optional[int] = None  # Memory in bytes
    memory_swap: Optional[int] = None
    memory_reservation: Optional[int] = None
    cpu_shares: Optional[int] = None

class ContainerConfig(BaseModel):
    name: str
    image: str
    command: Optional[List[str]] = None
    entrypoint: Optional[List[str]] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    ports: List[PortMapping] = Field(default_factory=list)
    volumes: List[VolumeMount] = Field(default_factory=list)
    network_mode: NetworkMode = NetworkMode.BRIDGE
    network_name: Optional[str] = None
    resources: Optional[ContainerResources] = None
    restart_policy: str = "unless-stopped"
    labels: Dict[str, str] = Field(default_factory=dict)

    @validator('name')
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]+$', v):
            raise ValueError("Invalid container name format")
        return v

    @validator('image')
    def validate_image(cls, v: str) -> str:
        if not re.match(r'^[\w\-./]+(:[\w\-.]+)?$', v):
            raise ValueError("Invalid image format")
        return v

class ContainerStats(BaseModel):
    cpu_usage: float  # Percentage
    memory_usage: int  # Bytes
    memory_limit: int  # Bytes
    network_rx_bytes: int
    network_tx_bytes: int
    block_read_bytes: int
    block_write_bytes: int
    pids: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Container(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    machine_id: str
    config: ContainerConfig
    state: ContainerState = ContainerState.CREATED
    docker_id: Optional[str] = None
    stats: Optional[ContainerStats] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ContainerCreateRequest(BaseModel):
    machine_id: str
    config: ContainerConfig

class ContainerUpdateRequest(BaseModel):
    config: Optional[ContainerConfig] = None
    state: Optional[ContainerState] = None

class ComposeConfig(BaseModel):
    version: str
    services: Dict[str, ContainerConfig]
    networks: Optional[Dict[str, Any]] = None
    volumes: Optional[Dict[str, Any]] = None

class ComposeDeployment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    machine_id: str
    config: ComposeConfig
    containers: Dict[str, Container] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
