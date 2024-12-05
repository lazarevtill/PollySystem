# backend/app/plugins/machines/routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from app.core.auth import get_current_user
from app.core.exceptions import MachineConnectionError
from .service import MachineService
from .models import (
    Machine, MachineCreate, MachineUpdate,
    CommandResult, CommandRequest
)

logger = logging.getLogger(__name__)

def get_machine_router(machine_service: MachineService) -> APIRouter:
    router = APIRouter()

    @router.post("/machines", response_model=Machine)
    async def create_machine(
        data: MachineCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new machine"""
        try:
            return await machine_service.create_machine(data)
        except MachineConnectionError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/machines", response_model=List[Machine])
    async def list_machines(
        current_user: dict = Depends(get_current_user)
    ):
        """List all machines"""
        return await machine_service.list_machines()

    @router.get("/machines/{machine_id}", response_model=Machine)
    async def get_machine(
        machine_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get machine details"""
        machine = await machine_service.get_machine(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        return machine

    @router.put("/machines/{machine_id}", response_model=Machine)
    async def update_machine(
        machine_id: str,
        data: MachineUpdate,
        current_user: dict = Depends(get_current_user)
    ):
        """Update a machine"""
        machine = await machine_service.update_machine(machine_id, data)
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")
        return machine

    @router.delete("/machines/{machine_id}")
    async def delete_machine(
        machine_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Delete a machine"""
        success = await machine_service.delete_machine(machine_id)
        if not success:
            raise HTTPException(status_code=404, detail="Machine not found")
        return {"status": "success"}

    @router.post("/machines/command", response_model=Dict[str, CommandResult])
    async def execute_command(
        request: CommandRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Execute command on machines"""
        results = {}
        machines = []

        if request.machines:
            # Execute on specific machines
            for machine_id in request.machines:
                machine = await machine_service.get_machine(machine_id)
                if machine:
                    machines.append(machine)
        else:
            # Execute on all machines
            machines = await machine_service.list_machines()

        for machine in machines:
            try:
                result = await machine_service.execute_command(
                    machine,
                    request.command,
                    request.timeout
                )
                results[machine.id] = result
            except Exception as e:
                results[machine.id] = CommandResult(
                    success=False,
                    stdout="",
                    stderr=str(e),
                    exit_code=-1,
                    duration=0
                )

        return results

    @router.post("/machines/{machine_id}/setup")
    async def setup_machine(
        machine_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Setup a machine"""
        machine = await machine_service.get_machine(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")

        success = await machine_service.setup_machine(machine)
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to setup machine"
            )

        return {"status": "success"}

    @router.put("/machines/{machine_id}/monitoring")
    async def update_monitoring(
        machine_id: str,
        interval: float = Query(..., gt=0),
        current_user: dict = Depends(get_current_user)
    ):
        """Update machine monitoring interval"""
        machine = await machine_service.get_machine(machine_id)
        if not machine:
            raise HTTPException(status_code=404, detail="Machine not found")

        machine_service.update_monitoring_interval(machine_id, interval)
        return {"status": "success"}

    return router