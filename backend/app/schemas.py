from pydantic import BaseModel, validator
from typing import Optional, Dict, List, Union
from datetime import datetime
import json

class MachineBase(BaseModel):
    name: str
    hostname: str
    ssh_user: str
    ssh_port: int = 22

    @validator('hostname')
    def validate_hostname(cls, v):
        if not v.endswith('.in.lc'):
            raise ValueError('Hostname must end with .in.lc')
        return v

class MachineCreate(MachineBase):
    pass

class MachineResponse(MachineBase):
    id: int
    is_active: bool
    ssh_key_public: str
    created_at: datetime
    deployments_count: int = 0

    class Config:
        from_attributes = True

class ContainerConfig(BaseModel):
    environment: Dict[str, str] = {}
    ports: List[str] = []
    volumes: List[str] = []
    networks: List[str] = []
    command: Optional[str] = None

class ContainerDeployment(BaseModel):
    name: str
    machine_id: int
    image: str
    config: ContainerConfig

    @validator('name')
    def validate_name(cls, v):
        if not v.isalnum() or not v.islower():
            raise ValueError('Name must be lowercase alphanumeric')
        return v

class ComposeDeployment(BaseModel):
    name: str
    machine_id: int
    compose_content: str

    @validator('compose_content')
    def validate_compose(cls, v):
        import yaml
        try:
            yaml.safe_load(v)
        except yaml.YAMLError:
            raise ValueError('Invalid YAML content')
        return v

class DeploymentBase(BaseModel):
    name: str
    machine_id: int
    deployment_type: str
    config: Union[dict, str]
    subdomain: str
    status: str

class DeploymentCreate(DeploymentBase):
    @validator('config')
    def validate_config(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v

class DeploymentResponse(DeploymentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    machine: MachineResponse

    @validator('config')
    def parse_config(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True

class DeploymentLogs(BaseModel):
    logs: str