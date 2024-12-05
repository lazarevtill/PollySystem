from fastapi import APIRouter, HTTPException
from typing import List
from .models import MachineCreate
from app.core.metrics_utils import get_machine_metrics

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])

# In-memory store for demonstration
MACHINES = {}

def register(app):
    app.include_router(router)

@router.post("/", response_model=dict)
def add_machine(machine: MachineCreate):
    if machine.host in MACHINES:
        raise HTTPException(status_code=400, detail="Machine already exists")
    MACHINES[machine.host] = {
        "name": machine.name,
        "host": machine.host,
        "port": machine.port,
        "user": machine.user,
        "password": machine.password,
        "ssh_key": machine.ssh_key
    }
    return {"status": "machine_added"}

@router.delete("/{host}", response_model=dict)
def delete_machine(host: str):
    if host not in MACHINES:
        raise HTTPException(status_code=404, detail="Machine not found")
    del MACHINES[host]
    return {"status": "machine_deleted"}

@router.get("/", response_model=List[dict])
def list_machines():
    return list(MACHINES.values())

@router.get("/{host}/metrics", response_model=dict)
def machine_metrics(host: str):
    if host not in MACHINES:
        raise HTTPException(status_code=404, detail="Machine not found")
    info = MACHINES[host]
    metrics = get_machine_metrics(info["host"], info["port"], info["user"], info.get("ssh_key"), info.get("password"))
    return metrics
