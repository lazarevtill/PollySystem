# app/plugins/machines/routes.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import tempfile
import logging
from . import schemas
from app.models.machine import Machine
from app.core.database import get_db
from app.core.ssh_utils import run_command_on_machine, create_temp_key_file, load_ssh_key
from app.core.metrics_utils import get_machine_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])

def test_connection(host: str, port: int, user: str, ssh_key: Optional[str] = None, password: Optional[str] = None) -> bool:
    """Test SSH connection with provided credentials."""
    try:
        result = run_command_on_machine(
            host=host,
            port=port,
            user=user,
            command="echo 'Connection test successful'",
            ssh_key=ssh_key,
            password=password
        )
        return "Connection test successful" in result
    except Exception as e:
        logger.error(f"Connection test failed for {host}: {str(e)}")
        raise Exception(f"Connection test failed: {str(e)}")

def register(app):
    app.include_router(router)

@router.get("/", response_model=List[schemas.MachineResponse])
async def list_machines(db: Session = Depends(get_db)):
    """List all registered machines."""
    return db.query(Machine).all()

@router.post("/", response_model=schemas.MachineResponse)
async def add_machine(machine: schemas.MachineCreate, db: Session = Depends(get_db)):
    """Add a new machine with either SSH key or password authentication."""
    if db.query(Machine).filter(Machine.host == machine.host).first():
        raise HTTPException(status_code=400, detail="Machine already exists")

    try:
        ssh_key_path = None
        tmp_key_file = None

        # Handle SSH key authentication
        if machine.ssh_key:
            try:
                # Create a temporary file for the SSH key
                tmp_key_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
                tmp_key_file.write(machine.ssh_key)
                tmp_key_file.flush()
                os.chmod(tmp_key_file.name, 0o600)
                ssh_key_path = tmp_key_file.name

                # Test connection with SSH key
                test_connection(
                    host=machine.host,
                    port=machine.port,
                    user=machine.user,
                    ssh_key=ssh_key_path
                )

            except Exception as e:
                if tmp_key_file and os.path.exists(tmp_key_file.name):
                    os.unlink(tmp_key_file.name)
                raise HTTPException(
                    status_code=400,
                    detail=f"SSH key authentication failed: {str(e)}"
                )

        # Handle password authentication
        elif machine.password:
            try:
                test_connection(
                    host=machine.host,
                    port=machine.port,
                    user=machine.user,
                    password=machine.password
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password authentication failed: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either SSH key or password must be provided"
            )

        # Create machine record
        db_machine = Machine(
            name=machine.name,
            host=machine.host,
            port=machine.port,
            user=machine.user,
            password=machine.password if not machine.ssh_key else None,
            ssh_key_path=ssh_key_path
        )

        try:
            db.add(db_machine)
            db.commit()
            db.refresh(db_machine)
            return db_machine
        except Exception as e:
            if ssh_key_path and os.path.exists(ssh_key_path):
                os.unlink(ssh_key_path)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to add machine to database: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add machine {machine.host}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{host}", response_model=schemas.StatusResponse)
async def delete_machine(host: str, db: Session = Depends(get_db)):
    """Delete a machine by host."""
    machine = db.query(Machine).filter(Machine.host == host).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Clean up SSH key file if it exists
    if machine.ssh_key_path and os.path.exists(machine.ssh_key_path):
        try:
            os.unlink(machine.ssh_key_path)
        except Exception as e:
            logger.warning(f"Failed to delete SSH key file {machine.ssh_key_path}: {e}")
    
    db.delete(machine)
    db.commit()
    
    return {"status": "machine_deleted"}

@router.get("/{host}/metrics", response_model=schemas.MachineMetrics)
async def get_machine_metrics_endpoint(host: str, db: Session = Depends(get_db)):
    """Get metrics for a specific machine."""
    machine = db.query(Machine).filter(Machine.host == host).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    try:
        metrics = get_machine_metrics(
            machine.host,
            machine.port,
            machine.user,
            machine.ssh_key_path,
            machine.password
        )
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics for {host}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")