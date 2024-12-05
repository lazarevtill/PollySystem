# backend/app/plugins/docker/routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging
from datetime import datetime

from app.core.exceptions import DockerError
from app.plugins.machines.service import MachineService
from .service import DockerService
from .models import (
    Container, ContainerConfig, ComposeConfig,
    ComposeDeployment, ContainerCreateRequest,
    ContainerUpdateRequest
)

logger = logging.getLogger(__name__)

def get_docker_router(
    docker_service: DockerService,
    machine_service: MachineService
) -> APIRouter:
    router = APIRouter()

    @router.post("/containers", response_model=Container)
    async def create_container(request: ContainerCreateRequest):
        """Create a new container"""
        try:
            machine = await machine_service.get_machine(request.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            return await docker_service.create_container(
                machine,
                request.config
            )
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/containers", response_model=List[Container])
    async def list_containers(
        machine_id: Optional[str] = Query(None)
    ):
        """List containers"""
        try:
            return await docker_service.list_containers(machine_id)
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/containers/{container_id}", response_model=Container)
    async def get_container(container_id: str):
        """Get container details"""
        container = await docker_service.get_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail="Container not found")
        return container

    @router.post("/containers/{container_id}/start")
    async def start_container(container_id: str):
        """Start a container"""
        try:
            container = await docker_service.get_container(container_id)
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            machine = await machine_service.get_machine(container.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            return await docker_service.start_container(machine, container_id)
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/containers/{container_id}/stop")
    async def stop_container(
        container_id: str,
        timeout: int = Query(10, ge=0, le=300)
    ):
        """Stop a container"""
        try:
            container = await docker_service.get_container(container_id)
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            machine = await machine_service.get_machine(container.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            return await docker_service.stop_container(
                machine,
                container_id,
                timeout
            )
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/containers/{container_id}")
    async def remove_container(
        container_id: str,
        force: bool = Query(False)
    ):
        """Remove a container"""
        try:
            container = await docker_service.get_container(container_id)
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            machine = await machine_service.get_machine(container.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            await docker_service.remove_container(
                machine,
                container_id,
                force
            )
            return {"status": "success"}
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/containers/{container_id}/logs")
    async def get_container_logs(
        container_id: str,
        tail: Optional[int] = Query(None, ge=1)
    ):
        """Get container logs"""
        try:
            container = await docker_service.get_container(container_id)
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            machine = await machine_service.get_machine(container.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            logs = await docker_service.get_container_logs(
                machine,
                container_id,
                tail
            )
            return {"logs": logs}
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/containers/{container_id}/exec")
    async def execute_command(
        container_id: str,
        command: List[str],
        workdir: Optional[str] = None,
        env: Optional[dict] = None,
        user: Optional[str] = None
    ):
        """Execute a command in a container"""
        try:
            container = await docker_service.get_container(container_id)
            if not container:
                raise HTTPException(status_code=404, detail="Container not found")
            
            machine = await machine_service.get_machine(container.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            result = await docker_service.execute_command(
                machine,
                container_id,
                command,
                workdir,
                env,
                user
            )
            return result
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/compose", response_model=ComposeDeployment)
    async def deploy_compose(
        machine_id: str,
        config: ComposeConfig
    ):
        """Deploy a Docker Compose configuration"""
        try:
            machine = await machine_service.get_machine(machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            return await docker_service.deploy_compose(machine, config)
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.delete("/compose/{deployment_id}")
    async def remove_compose_deployment(
        deployment_id: str,
        force: bool = Query(False)
    ):
        """Remove a Docker Compose deployment"""
        try:
            data = await docker_service.redis.get(
                f"compose_deployment:{deployment_id}"
            )
            if not data:
                raise HTTPException(
                    status_code=404,
                    detail="Deployment not found"
                )
            
            deployment = ComposeDeployment.parse_raw(data)
            machine = await machine_service.get_machine(deployment.machine_id)
            if not machine:
                raise HTTPException(status_code=404, detail="Machine not found")
            
            await docker_service.remove_compose_deployment(
                machine,
                deployment_id,
                force
            )
            return {"status": "success"}
        except DockerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router