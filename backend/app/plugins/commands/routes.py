from fastapi import APIRouter, HTTPException
from app.plugins.machines.routes import MACHINES
from app.core.ssh_utils import run_command_on_machine

router = APIRouter(prefix="/api/v1/commands", tags=["commands"])

def register(app):
    app.include_router(router)

@router.post("/run_all", response_model=dict)
def run_on_all(command: str):
    if not MACHINES:
        raise HTTPException(status_code=400, detail="No machines available")
    results = {}
    for host, info in MACHINES.items():
        output = run_command_on_machine(info["host"], info["port"], info["user"], command, info.get("ssh_key"), info.get("password"))
        results[host] = output
    return {"results": results}
