# app/plugins/docker_manager/routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict
from app.core.database import get_db
from app.models.machine import Machine
from app.core.docker_utils import check_and_install_docker, run_docker_compose_command

router = APIRouter(prefix="/api/v1/docker", tags=["docker"])

def register(app):
    app.include_router(router)

@router.post("/install", response_model=Dict[str, Dict[str, str]])
async def install_docker_on_all(db: Session = Depends(get_db)):
    """Install Docker on all registered machines."""
    machines = db.query(Machine).all()
    if not machines:
        raise HTTPException(status_code=400, detail="No machines available")

    install_results = {}
    for machine in machines:
        try:
            res = check_and_install_docker(
                host=machine.host,
                port=machine.port,
                user=machine.user,
                ssh_key=machine.ssh_key_path,
                password=machine.password
            )
            install_results[machine.host] = res
        except Exception as e:
            install_results[machine.host] = f"Error: {str(e)}"

    return {
        "status": "installation_checked",
        "details": install_results
    }

@router.post("/compose/run", response_model=Dict[str, Dict[str, str]])
async def compose_run(db: Session = Depends(get_db)):
    """Run docker-compose up on all machines."""
    machines = db.query(Machine).all()
    if not machines:
        raise HTTPException(status_code=400, detail="No machines available")

    results = {}
    for machine in machines:
        try:
            res = run_docker_compose_command(
                host=machine.host,
                port=machine.port,
                user=machine.user,
                command="up -d",
                ssh_key=machine.ssh_key_path,
                password=machine.password
            )
            results[machine.host] = res
        except Exception as e:
            results[machine.host] = f"Error: {str(e)}"

    return {
        "status": "compose_run_triggered",
        "results": results
    }

@router.post("/compose/stop", response_model=Dict[str, Dict[str, str]])
async def compose_stop(db: Session = Depends(get_db)):
    """Stop docker-compose on all machines."""
    machines = db.query(Machine).all()
    if not machines:
        raise HTTPException(status_code=400, detail="No machines available")

    results = {}
    for machine in machines:
        try:
            res = run_docker_compose_command(
                host=machine.host,
                port=machine.port,
                user=machine.user,
                command="down",
                ssh_key=machine.ssh_key_path,
                password=machine.password
            )
            results[machine.host] = res
        except Exception as e:
            results[machine.host] = f"Error: {str(e)}"

    return {
        "status": "compose_stopped",
        "results": results
    }