from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import secrets
from datetime import datetime

from .config import settings
from .database import get_db
from .models import Machine, Deployment
from .schemas import (
    MachineCreate, MachineResponse,
    ContainerDeployment, ComposeDeployment,
    DeploymentResponse, DeploymentLogs
)
from .ssh_manager import SSHManager
from .docker_manager import DockerManager
from .nginx_manager import NginxManager

# Initialize managers
ssh_manager = SSHManager(settings.SECRET_KEY)
docker_manager = DockerManager(ssh_manager)
nginx_manager = NginxManager()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background task to update Nginx configuration
async def update_nginx_config(db: Session):
    deployments = db.query(Deployment).all()
    deployment_configs = []
    
    for deployment in deployments:
        config = json.loads(deployment.config)
        deployment_configs.append({
            'subdomain': deployment.subdomain,
            'target_host': deployment.machine.hostname,
            'target_port': config.get('port', 80)  # Default to port 80
        })
    
    nginx_manager.update_proxy_config(deployment_configs)

# Machine management endpoints
@app.post("/api/machines/", response_model=MachineResponse)
async def create_machine(
    machine: MachineCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        # Generate SSH key pair
        private_key, public_key = ssh_manager.generate_ssh_key_pair()
        encrypted_private_key = ssh_manager.encrypt_private_key(private_key)
        
        # Create machine record
        db_machine = Machine(
            name=machine.name,
            hostname=machine.hostname,
            ssh_user=machine.ssh_user,
            ssh_port=machine.ssh_port,
            ssh_key_private=encrypted_private_key,
            ssh_key_public=public_key
        )
        
        db.add(db_machine)
        db.commit()
        db.refresh(db_machine)
        
        return MachineResponse(
            id=db_machine.id,
            name=db_machine.name,
            hostname=db_machine.hostname,
            ssh_user=db_machine.ssh_user,
            ssh_port=db_machine.ssh_port,
            is_active=db_machine.is_active,
            ssh_key_public=public_key,
            created_at=db_machine.created_at,
            deployments_count=0
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/machines/", response_model=List[MachineResponse])
async def list_machines(db: Session = Depends(get_db)):
    machines = db.query(Machine).all()
    return [
        MachineResponse(
            id=m.id,
            name=m.name,
            hostname=m.hostname,
            ssh_user=m.ssh_user,
            ssh_port=m.ssh_port,
            is_active=m.is_active,
            ssh_key_public=m.ssh_key_public,
            created_at=m.created_at,
            deployments_count=len(m.deployments)
        )
        for m in machines
    ]

@app.delete("/api/machines/{machine_id}")
async def delete_machine(
    machine_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    if machine.deployments:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete machine with active deployments"
        )
    
    db.delete(machine)
    db.commit()
    
    background_tasks.add_task(update_nginx_config, db)
    
    return {"message": "Machine deleted successfully"}

# Deployment endpoints
@app.post("/api/deployments/container/", response_model=DeploymentResponse)
async def deploy_container(
    deployment: ContainerDeployment,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == deployment.machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Generate unique subdomain
    subdomain = f"{deployment.name}-{secrets.token_hex(4)}"
    
    try:
        with ssh_manager.get_ssh_client(
            hostname=machine.hostname,
            username=machine.ssh_user,
            private_key=machine.ssh_key_private,
            port=machine.ssh_port
        ) as ssh:
            # Deploy container
            success, output = docker_manager.deploy_container(
                ssh,
                deployment.name,
                deployment.image,
                environment=deployment.config.environment,
                ports=deployment.config.ports,
                volumes=deployment.config.volumes,
                networks=deployment.config.networks,
                command=deployment.config.command
            )
            
            if not success:
                raise Exception(output)
            
            # Create deployment record
            db_deployment = Deployment(
                name=deployment.name,
                machine_id=machine.id,
                deployment_type='container',
                config=json.dumps({
                    "image": deployment.image,
                    **deployment.config.dict()
                }),
                subdomain=subdomain,
                status='running'
            )
            
            db.add(db_deployment)
            db.commit()
            db.refresh(db_deployment)
            
            # Update Nginx configuration
            background_tasks.add_task(update_nginx_config, db)
            
            return DeploymentResponse(
                id=db_deployment.id,
                name=db_deployment.name,
                machine_id=db_deployment.machine_id,
                deployment_type=db_deployment.deployment_type,
                config=json.loads(db_deployment.config),
                subdomain=db_deployment.subdomain,
                status=db_deployment.status,
                created_at=db_deployment.created_at,
                updated_at=db_deployment.updated_at,
                machine=machine
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deployments/compose/", response_model=DeploymentResponse)
async def deploy_compose(
    name: str,
    machine_id: int,
    compose_file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Generate unique subdomain
    subdomain = f"{name}-{secrets.token_hex(4)}"
    
    try:
        # Read and validate compose file
        compose_content = await compose_file.read()
        if not docker_manager.validate_compose_file(compose_content.decode()):
            raise HTTPException(status_code=400, detail="Invalid compose file")
        
        with ssh_manager.get_ssh_client(
            hostname=machine.hostname,
            username=machine.ssh_user,
            private_key=machine.ssh_key_private,
            port=machine.ssh_port
        ) as ssh:
            # Deploy compose
            success, output = docker_manager.deploy_compose(
                ssh,
                name,
                compose_content.decode()
            )
            
            if not success:
                raise Exception(output)
            
            # Create deployment record
            db_deployment = Deployment(
                name=name,
                machine_id=machine.id,
                deployment_type='compose',
                config=compose_content.decode(),
                subdomain=subdomain,
                status='running'
            )
            
            db.add(db_deployment)
            db.commit()
            db.refresh(db_deployment)
            
            # Update Nginx configuration
            background_tasks.add_task(update_nginx_config, db)
            
            return DeploymentResponse(
                id=db_deployment.id,
                name=db_deployment.name,
                machine_id=db_deployment.machine_id,
                deployment_type=db_deployment.deployment_type,
                config=json.loads(db_deployment.config),
                subdomain=db_deployment.subdomain,
                status=db_deployment.status,
                created_at=db_deployment.created_at,
                updated_at=db_deployment.updated_at,
                machine=machine
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deployments/", response_model=List[DeploymentResponse])
async def list_deployments(db: Session = Depends(get_db)):
    deployments = db.query(Deployment).all()
    return [
        DeploymentResponse(
            id=d.id,
            name=d.name,
            machine_id=d.machine_id,
            deployment_type=d.deployment_type,
            config=json.loads(d.config),
            subdomain=d.subdomain,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
            machine=d.machine
        )
        for d in deployments
    ]

@app.post("/api/deployments/{deployment_id}/stop")
async def stop_deployment(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        with ssh_manager.get_ssh_client(
            hostname=deployment.machine.hostname,
            username=deployment.machine.ssh_user,
            private_key=deployment.machine.ssh_key_private,
            port=deployment.machine.ssh_port
        ) as ssh:
            success, output = docker_manager.stop_deployment(
                ssh,
                deployment.name,
                deployment.deployment_type
            )
            
            if not success:
                raise Exception(output)
            
            deployment.status = 'stopped'
            db.commit()
            
            return {"message": "Deployment stopped successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/deployments/{deployment_id}/start")
async def start_deployment(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        with ssh_manager.get_ssh_client(
            hostname=deployment.machine.hostname,
            username=deployment.machine.ssh_user,
            private_key=deployment.machine.ssh_key_private,
            port=deployment.machine.ssh_port
        ) as ssh:
            success, output = docker_manager.start_deployment(
                ssh,
                deployment.name,
                deployment.deployment_type
            )
            
            if not success:
                raise Exception(output)
            
            deployment.status = 'running'
            db.commit()
            
            return {"message": "Deployment started successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/deployments/{deployment_id}/logs", response_model=DeploymentLogs)
async def get_deployment_logs(deployment_id: int, db: Session = Depends(get_db)):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        with ssh_manager.get_ssh_client(
            hostname=deployment.machine.hostname,
            username=deployment.machine.ssh_user,
            private_key=deployment.machine.ssh_key_private,
            port=deployment.machine.ssh_port
        ) as ssh:
            logs = docker_manager.get_container_logs(
                ssh,
                deployment.name,
                deployment.deployment_type
            )
            
            return DeploymentLogs(logs=logs)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/deployments/{deployment_id}")
async def delete_deployment(
    deployment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    try:
        with ssh_manager.get_ssh_client(
            hostname=deployment.machine.hostname,
            username=deployment.machine.ssh_user,
            private_key=deployment.machine.ssh_key_private,
            port=deployment.machine.ssh_port
        ) as ssh:
            success, output = docker_manager.remove_deployment(
                ssh,
                deployment.name,
                deployment.deployment_type
            )
            
            if not success:
                raise Exception(output)
            
            db.delete(deployment)
            db.commit()
            
            # Update Nginx configuration
            background_tasks.add_task(update_nginx_config, db)
            
            return {"message": "Deployment deleted successfully"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
