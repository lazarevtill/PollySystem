# backend/app/plugins/machines/service.py
import asyncio
import aioredis
import asyncssh
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import psutil
import paramiko
from contextlib import asynccontextmanager

from app.core.exceptions import MachineConnectionError
from .models import (
    Machine, MachineStatus, SystemMetrics,
    SSHKey, CommandResult, MachineCreate, MachineUpdate
)

logger = logging.getLogger(__name__)

class MachineService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self._ssh_clients: Dict[str, asyncssh.SSHClientConnection] = {}
        self._monitoring_intervals: Dict[str, float] = {}

    async def cleanup(self):
        """Cleanup service resources"""
        # Close all SSH connections
        for client in self._ssh_clients.values():
            client.close()
        self._ssh_clients.clear()

    @asynccontextmanager
    async def get_ssh_client(self, machine: Machine) -> asyncssh.SSHClientConnection:
        """Get or create SSH client for a machine"""
        try:
            if machine.id not in self._ssh_clients:
                # Create private key file
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as keyfile:
                    keyfile.write(machine.ssh_key.private_key)
                    keyfile_path = keyfile.name

                try:
                    # Connect to machine
                    client = await asyncssh.connect(
                        machine.ip_address,
                        username='ubuntu',  # Could be configurable
                        client_keys=[keyfile_path],
                        known_hosts=None,  # In production, use known_hosts
                        passphrase=machine.ssh_key.passphrase
                    )
                    self._ssh_clients[machine.id] = client
                finally:
                    os.unlink(keyfile_path)

            yield self._ssh_clients[machine.id]

        except (asyncssh.Error, OSError) as e:
            raise MachineConnectionError(
                f"Failed to connect to machine {machine.id}: {str(e)}",
                machine.id
            )

    async def create_machine(self, data: MachineCreate) -> Machine:
        """Create a new machine"""
        machine = Machine(
            name=data.name,
            ip_address=data.ip_address,
            ssh_key=data.ssh_key,
            metadata=data.metadata or {}
        )

        # Test connection
        try:
            async with self.get_ssh_client(machine):
                machine.status = MachineStatus.ACTIVE
        except MachineConnectionError:
            machine.status = MachineStatus.ERROR

        # Store in Redis
        await self.redis.set(
            f"machine:{machine.id}",
            machine.json(),
            ex=86400  # 24 hours
        )

        # Start monitoring
        self._monitoring_intervals[machine.id] = 30  # 30 seconds interval
        return machine

    async def update_machine(
        self,
        machine_id: str,
        data: MachineUpdate
    ) -> Optional[Machine]:
        """Update a machine"""
        machine = await self.get_machine(machine_id)
        if not machine:
            return None

        # Update fields
        if data.name is not None:
            machine.name = data.name
        if data.ip_address is not None:
            machine.ip_address = data.ip_address
        if data.ssh_key is not None:
            machine.ssh_key = data.ssh_key
        if data.metadata is not None:
            machine.metadata.update(data.metadata)

        machine.updated_at = datetime.utcnow()

        # Test connection if IP or SSH key changed
        if data.ip_address is not None or data.ssh_key is not None:
            try:
                async with self.get_ssh_client(machine):
                    machine.status = MachineStatus.ACTIVE
            except MachineConnectionError:
                machine.status = MachineStatus.ERROR

        # Update in Redis
        await self.redis.set(
            f"machine:{machine.id}",
            machine.json(),
            ex=86400
        )

        return machine

    async def delete_machine(self, machine_id: str) -> bool:
        """Delete a machine"""
        # Remove from Redis
        result = await self.redis.delete(f"machine:{machine_id}")
        
        # Close SSH connection if exists
        if machine_id in self._ssh_clients:
            self._ssh_clients[machine_id].close()
            del self._ssh_clients[machine_id]

        # Stop monitoring
        if machine_id in self._monitoring_intervals:
            del self._monitoring_intervals[machine_id]

        return result > 0

    async def get_machine(self, machine_id: str) -> Optional[Machine]:
        """Get machine by ID"""
        data = await self.redis.get(f"machine:{machine_id}")
        return Machine.parse_raw(data) if data else None

    async def list_machines(self) -> List[Machine]:
        """List all machines"""
        machines = []
        async for key in self.redis.scan_iter("machine:*"):
            data = await self.redis.get(key)
            if data:
                machines.append(Machine.parse_raw(data))
        return machines

    async def execute_command(
        self,
        machine: Machine,
        command: str,
        timeout: int = 30
    ) -> CommandResult:
        """Execute command on a machine"""
        start_time = datetime.utcnow()
        try:
            async with self.get_ssh_client(machine) as client:
                process = await client.run(command, timeout=timeout)
                
                return CommandResult(
                    success=process.exit_status == 0,
                    stdout=process.stdout,
                    stderr=process.stderr,
                    exit_code=process.exit_status,
                    duration=(datetime.utcnow() - start_time).total_seconds()
                )

        except asyncio.TimeoutError:
            return CommandResult(
                success=False,
                stdout="",
                stderr="Command execution timed out",
                exit_code=-1,
                duration=timeout
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                duration=(datetime.utcnow() - start_time).total_seconds()
            )

    async def collect_system_metrics(self, machine: Machine) -> Optional[SystemMetrics]:
        """Collect system metrics from a machine"""
        try:
            async with self.get_ssh_client(machine) as client:
                # Get CPU usage
                cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
                cpu_process = await client.run(cpu_cmd)
                cpu_usage = float(cpu_process.stdout.strip())

                # Get memory info
                mem_cmd = "free -b | grep Mem"
                mem_process = await client.run(mem_cmd)
                mem_parts = mem_process.stdout.split()
                memory_total = int(mem_parts[1])
                memory_used = int(mem_parts[2])

                # Get disk info
                disk_cmd = "df -B1 / | tail -1"
                disk_process = await client.run(disk_cmd)
                disk_parts = disk_process.stdout.split()
                disk_total = int(disk_parts[1])
                disk_used = int(disk_parts[2])

                # Check Docker status
                docker_cmd = "systemctl is-active docker"
                docker_process = await client.run(docker_cmd)
                docker_status = docker_process.stdout.strip() == "active"

                return SystemMetrics(
                    cpu_usage=cpu_usage,
                    memory_total=memory_total,
                    memory_used=memory_used,
                    disk_total=disk_total,
                    disk_used=disk_used,
                    docker_status=docker_status
                )

        except Exception as e:
            logger.error(f"Failed to collect metrics for machine {machine.id}: {str(e)}")
            return None

    async def monitor_machines(self):
        """Monitor all machines periodically"""
        while True:
            try:
                machines = await self.list_machines()
                
                for machine in machines:
                    if machine.id not in self._monitoring_intervals:
                        continue

                    interval = self._monitoring_intervals[machine.id]
                    
                    try:
                        # Collect metrics
                        metrics = await self.collect_system_metrics(machine)
                        
                        if metrics:
                            machine.system_info = metrics
                            machine.status = MachineStatus.ACTIVE
                            machine.last_seen = datetime.utcnow()
                        else:
                            machine.status = MachineStatus.ERROR
                        
                        # Update machine in Redis
                        await self.redis.set(
                            f"machine:{machine.id}",
                            machine.json(),
                            ex=86400
                        )

                    except MachineConnectionError:
                        machine.status = MachineStatus.INACTIVE
                        await self.redis.set(
                            f"machine:{machine.id}",
                            machine.json(),
                            ex=86400
                        )

                    except Exception as e:
                        logger.error(f"Error monitoring machine {machine.id}: {str(e)}")

                    await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
            
            await asyncio.sleep(1)  # Small delay before next iteration

    async def setup_machine(self, machine: Machine) -> bool:
        """Initial setup of a machine"""
        try:
            async with self.get_ssh_client(machine) as client:
                # Install required packages
                setup_commands = [
                    "sudo apt-get update",
                    "sudo apt-get install -y docker.io docker-compose",
                    "sudo systemctl enable docker",
                    "sudo systemctl start docker",
                    "sudo usermod -aG docker ubuntu"
                ]

                for cmd in setup_commands:
                    result = await self.execute_command(machine, cmd)
                    if not result.success:
                        logger.error(f"Setup command failed: {cmd}")
                        logger.error(f"Error: {result.stderr}")
                        return False

                # Update machine status
                machine.status = MachineStatus.ACTIVE
                await self.redis.set(
                    f"machine:{machine.id}",
                    machine.json(),
                    ex=86400
                )
                
                return True

        except Exception as e:
            logger.error(f"Failed to setup machine {machine.id}: {str(e)}")
            return False

    def update_monitoring_interval(self, machine_id: str, interval: float):
        """Update monitoring interval for a machine"""
        if interval < 5:  # Minimum 5 seconds
            interval = 5
        self._monitoring_intervals[machine_id] = interval