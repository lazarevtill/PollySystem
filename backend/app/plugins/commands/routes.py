# app/plugins/commands/routes.py
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.machine import Machine
from app.core.ssh_utils import run_command_on_machine

router = APIRouter(prefix="/api/v1/commands", tags=["commands"])

class CommandRequest(BaseModel):
    command: str

def register(app):
    app.include_router(router)

@router.post("/run_all")
async def run_on_all(request: CommandRequest, db: Session = Depends(get_db)) -> Dict[str, Dict[str, str]]:
    """
    Run a command on all registered machines.
    POST body should be JSON: { "command": "your_command_here" }
    """
    command = request.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    # Get all machines
    machines = db.query(Machine).all()
    if not machines:
        raise HTTPException(status_code=400, detail="No machines available")

    results = {}
    for machine in machines:
        try:
            output = run_command_on_machine(
                host=machine.host,
                port=machine.port,
                user=machine.user,
                command=command,
                ssh_key=machine.ssh_key_path,
                password=machine.password
            )
            results[machine.host] = output
        except Exception as e:
            results[machine.host] = f"Error: {str(e)}"

    return {"results": results}
