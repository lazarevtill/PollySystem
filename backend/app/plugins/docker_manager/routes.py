from fastapi import APIRouter, HTTPException
from app.plugins.machines.routes import MACHINES
from app.core.docker_utils import check_and_install_docker, run_docker_compose_command

router = APIRouter(prefix="/api/v1/docker", tags=["docker"])

def register(app):
    app.include_router(router)

@router.post("/install", response_model=dict)
def install_docker_on_all():
    if not MACHINES:
        raise HTTPException(status_code=400, detail="No machines available")
    install_results = {}
    for host, info in MACHINES.items():
        res = check_and_install_docker(info["host"], info["port"], info["user"], info.get("ssh_key"), info.get("password"))
        install_results[host] = res
    return {"status": "installation_checked", "details": install_results}

@router.post("/compose/run", response_model=dict)
def compose_run():
    if not MACHINES:
        raise HTTPException(status_code=400, detail="No machines available")
    results = {}
    for host, info in MACHINES.items():
        res = run_docker_compose_command(info["host"], info["port"], info["user"], "up -d", info.get("ssh_key"), info.get("password"))
        results[host] = res
    return {"status": "compose_run_triggered", "results": results}

@router.post("/compose/stop", response_model=dict)
def compose_stop():
    if not MACHINES:
        raise HTTPException(status_code=400, detail="No machines available")
    results = {}
    for host, info in MACHINES.items():
        res = run_docker_compose_command(info["host"], info["port"], info["user"], "down", info.get("ssh_key"), info.get("password"))
        results[host] = res
    return {"status": "compose_stopped", "results": results}
