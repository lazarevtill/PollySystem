# backend/app/plugins/docker/service.py
import aiodocker
import aioredis
import docker
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging
from contextlib import asynccontextmanager
import yaml
import tempfile
import os

from app.core.config import get_settings
from app.core.exceptions import DockerError
from app.plugins.machines.service import MachineService
from app.plugins.machines.models import Machine
from .models import (
    Container, ContainerState, ContainerStats, ContainerConfig,
    ComposeConfig, ComposeDeployment, NetworkMode, PortMapping, VolumeMount
)

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(
        self,
        redis: aioredis.Redis,
        machine_service: MachineService
    ):
        self.redis = redis
        self.machine_service = machine_service
        self.settings = get_settings()
        self._docker_clients: Dict[str, docker.DockerClient] = {}
        self._stats_tasks: Dict[str, asyncio.Task] = {}
        self._network_cache: Dict[str, Dict[str, Any]] = {}

    async def cleanup(self):
        """Cleanup all connections and tasks"""
        for task in self._stats_tasks.values():
            task.cancel()
        await asyncio.gather(*self._stats_tasks.values(), return_exceptions=True)

        for client in self._docker_clients.values():
            client.close()
        self._docker_clients.clear()
        self._network_cache.clear()

    @asynccontextmanager
    async def get_docker_client(self, machine: Machine) -> docker.DockerClient:
        """Get or create Docker client for a machine"""
        try:
            if machine.id not in self._docker_clients:
                # Forward Docker socket through SSH
                socket_path = f"/tmp/docker_{machine.id}.sock"
                await self.machine_service.execute_command(
                    machine,
                    f"rm -f {socket_path} && socat UNIX-LISTEN:{socket_path},reuseaddr,fork UNIX-CONNECT:/var/run/docker.sock &"
                )
                
                # Wait for socket to be available
                await asyncio.sleep(1)
                
                # Create Docker client
                self._docker_clients[machine.id] = docker.DockerClient(
                    base_url=f"unix://{socket_path}"
                )

            yield self._docker_clients[machine.id]
        except Exception as e:
            if machine.id in self._docker_clients:
                self._docker_clients[machine.id].close()
                del self._docker_clients[machine.id]
            raise DockerError(f"Docker client error: {str(e)}")

    async def create_network(self, machine: Machine, name: str, driver: str = "bridge") -> str:
        """Create a Docker network if it doesn't exist"""
        try:
            async with self.get_docker_client(machine) as client:
                try:
                    network = client.networks.get(name)
                    return network.id
                except docker.errors.NotFound:
                    network = client.networks.create(
                        name=name,
                        driver=driver,
                        check_duplicate=True
                    )
                    return network.id
        except Exception as e:
            raise DockerError(f"Failed to create network: {str(e)}")

    async def ensure_volumes(self, machine: Machine, volumes: List[VolumeMount]):
        """Ensure all volume host paths exist"""
        for volume in volumes:
            if volume.host_path.startswith('/'):  # Only create absolute paths
                await self.machine_service.execute_command(
                    machine,
                    f"mkdir -p {volume.host_path}"
                )

    async def pull_image(self, machine: Machine, image: str):
        """Pull Docker image if not exists"""
        try:
            async with self.get_docker_client(machine) as client:
                try:
                    client.images.get(image)
                except docker.errors.ImageNotFound:
                    logger.info(f"Pulling image {image}...")
                    client.images.pull(image)
        except Exception as e:
            raise DockerError(f"Failed to pull image {image}: {str(e)}")

    async def create_container(
        self,
        machine: Machine,
        config: ContainerConfig,
        network_id: Optional[str] = None
    ) -> Container:
        """Create and start a container"""
        try:
            # Ensure volumes exist
            await self.ensure_volumes(machine, config.volumes)
            
            # Pull image if needed
            await self.pull_image(machine, config.image)

            async with self.get_docker_client(machine) as client:
                # Prepare container configuration
                container_config = {
                    "image": config.image,
                    "name": config.name,
                    "command": config.command,
                    "entrypoint": config.entrypoint,
                    "environment": config.environment,
                    "detach": True,
                    "labels": config.labels,
                    "hostname": config.name,
                    "volumes": {
                        v.host_path: {
                            'bind': v.container_path,
                            'mode': v.mode
                        } for v in config.volumes
                    },
                    "ports": {
                        f"{p.container_port}/{p.protocol}": p.host_port 
                        for p in config.ports
                    }
                }

                # Add network configuration
                if network_id and config.network_mode != NetworkMode.HOST:
                    container_config["network"] = network_id
                elif config.network_mode == NetworkMode.HOST:
                    container_config["network_mode"] = "host"

                # Add resource constraints
                if config.resources:
                    container_config.update({
                        "cpu_period": 100000,
                        "cpu_quota": int(config.resources.cpu_limit * 100000)
                        if config.resources.cpu_limit else None,
                        "mem_limit": config.resources.memory_limit,
                        "mem_swap_limit": config.resources.memory_swap,
                        "mem_reservation": config.resources.memory_reservation,
                        "cpu_shares": config.resources.cpu_shares
                    })

                # Create and start container
                docker_container = client.containers.run(**container_config)

                # Create container record
                container = Container(
                    machine_id=machine.id,
                    config=config,
                    state=ContainerState.RUNNING,
                    docker_id=docker_container.id,
                    started_at=datetime.utcnow()
                )

                # Store in Redis
                await self.redis.set(
                    f"container:{container.id}",
                    container.json(),
                    ex=86400  # 24 hours
                )

                # Start stats collection
                asyncio.create_task(
                    self._collect_container_stats(machine, container)
                )

                return container

        except Exception as e:
            raise DockerError(f"Failed to create container: {str(e)}")

    async def _collect_container_stats(self, machine: Machine, container: Container):
        """Collect container statistics periodically"""
        while True:
            try:
                async with self.get_docker_client(machine) as client:
                    docker_container = client.containers.get(container.docker_id)
                    stats = docker_container.stats(stream=False)

                    # Calculate CPU usage percentage
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                 stats['precpu_stats']['system_cpu_usage']
                    cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0

                    container_stats = ContainerStats(
                        cpu_usage=cpu_usage,
                        memory_usage=stats['memory_stats'].get('usage', 0),
                        memory_limit=stats['memory_stats'].get('limit', 0),
                        network_rx_bytes=sum(
                            interface.get('rx_bytes', 0)
                            for interface in stats.get('networks', {}).values()
                        ),
                        network_tx_bytes=sum(
                            interface.get('tx_bytes', 0)
                            for interface in stats.get('networks', {}).values()
                        ),
                        block_read_bytes=sum(
                            stat['value'] for stat in stats['blkio_stats']['io_service_bytes_recursive']
                            if stat['op'] == 'Read'
                        ) if stats['blkio_stats']['io_service_bytes_recursive'] else 0,
                        block_write_bytes=sum(
                            stat['value'] for stat in stats['blkio_stats']['io_service_bytes_recursive']
                            if stat['op'] == 'Write'
                        ) if stats['blkio_stats']['io_service_bytes_recursive'] else 0,
                        pids=stats['pids_stats'].get('current', 0)
                    )

                    # Update container stats in Redis
                    container.stats = container_stats
                    await self.redis.set(
                        f"container:{container.id}",
                        container.json(),
                        ex=86400
                    )

            except Exception as e:
                logger.error(f"Failed to collect container stats: {str(e)}")

            await asyncio.sleep(10)  # Collect every 10 seconds

    async def stop_container(
        self,
        machine: Machine,
        container_id: str,
        timeout: int = 10
    ) -> Container:
        """Stop a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                raise DockerError("Container not found")

            async with self.get_docker_client(machine) as client:
                docker_container = client.containers.get(container.docker_id)
                docker_container.stop(timeout=timeout)

                container.state = ContainerState.STOPPED
                container.finished_at = datetime.utcnow()

                # Update in Redis
                await self.redis.set(
                    f"container:{container.id}",
                    container.json(),
                    ex=86400
                )

                return container

        except Exception as e:
            raise DockerError(f"Failed to stop container: {str(e)}")

    async def start_container(
        self,
        machine: Machine,
        container_id: str
    ) -> Container:
        """Start a stopped container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                raise DockerError("Container not found")

            async with self.get_docker_client(machine) as client:
                docker_container = client.containers.get(container.docker_id)
                docker_container.start()

                container.state = ContainerState.RUNNING
                container.started_at = datetime.utcnow()
                container.finished_at = None

                # Update in Redis
                await self.redis.set(
                    f"container:{container.id}",
                    container.json(),
                    ex=86400
                )

                # Restart stats collection
                asyncio.create_task(
                    self._collect_container_stats(machine, container)
                )

                return container

        except Exception as e:
            raise DockerError(f"Failed to start container: {str(e)}")

    async def remove_container(
        self,
        machine: Machine,
        container_id: str,
        force: bool = False
    ) -> bool:
        """Remove a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                raise DockerError("Container not found")

            async with self.get_docker_client(machine) as client:
                docker_container = client.containers.get(container.docker_id)
                docker_container.remove(force=force)

                # Delete from Redis
                await self.redis.delete(f"container:{container.id}")
                
                # Stop stats collection task
                task_key = f"{machine.id}_{container.id}"
                if task_key in self._stats_tasks:
                    self._stats_tasks[task_key].cancel()
                    del self._stats_tasks[task_key]

                return True

        except Exception as e:
            raise DockerError(f"Failed to remove container: {str(e)}")

    async def get_container_logs(
        self,
        machine: Machine,
        container_id: str,
        tail: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> str:
        """Get container logs"""
        try:
            container = await self.get_container(container_id)
            if not container:
                raise DockerError("Container not found")

            async with self.get_docker_client(machine) as client:
                docker_container = client.containers.get(container.docker_id)
                logs = docker_container.logs(
                    stdout=True,
                    stderr=True,
                    tail=tail,
                    since=since,
                    until=until,
                    timestamps=True
                )
                return logs.decode('utf-8')

        except Exception as e:
            raise DockerError(f"Failed to get container logs: {str(e)}")

    async def execute_command(
        self,
        machine: Machine,
        container_id: str,
        command: List[str],
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a command in a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                raise DockerError("Container not found")

            async with self.get_docker_client(machine) as client:
                docker_container = client.containers.get(container.docker_id)
                
                exec_result = docker_container.exec_run(
                    cmd=command,
                    workdir=workdir,
                    environment=env,
                    user=user,
                    stdout=True,
                    stderr=True
                )

                return {
                    "exit_code": exec_result.exit_code,
                    "output": exec_result.output.decode('utf-8')
                }

        except Exception as e:
            raise DockerError(f"Failed to execute command: {str(e)}")

    async def get_container(self, container_id: str) -> Optional[Container]:
        """Get container by ID"""
        data = await self.redis.get(f"container:{container_id}")
        return Container.parse_raw(data) if data else None

    async def list_containers(
        self,
        machine_id: Optional[str] = None
    ) -> List[Container]:
        """List all containers"""
        containers = []
        async for key in self.redis.scan_iter("container:*"):
            data = await self.redis.get(key)
            if data:
                container = Container.parse_raw(data)
                if not machine_id or container.machine_id == machine_id:
                    containers.append(container)
        return containers

    async def deploy_compose(
        self,
        machine: Machine,
        config: ComposeConfig
    ) -> ComposeDeployment:
        """Deploy a Docker Compose configuration"""
        try:
            # Create deployment record
            deployment = ComposeDeployment(
                machine_id=machine.id,
                config=config
            )

            # Create shared network for the deployment
            network_name = f"compose_{deployment.id}"
            network_id = await self.create_network(machine, network_name)

            # Deploy services in dependency order
            deployed_services = set()
            
            while len(deployed_services) < len(config.services):
                for service_name, service_config in config.services.items():
                    if service_name in deployed_services:
                        continue

                    # Check if dependencies are met
                    dependencies_met = True
                    if 'depends_on' in service_config.metadata:
                        for dep in service_config.metadata['depends_on']:
                            if dep not in deployed_services:
                                dependencies_met = False
                                break

                    if dependencies_met:
                        # Create container for service
                        container = await self.create_container(
                            machine=machine,
                            config=service_config,
                            network_id=network_id
                        )
                        deployment.containers[service_name] = container
                        deployed_services.add(service_name)

            # Store deployment in Redis
            await self.redis.set(
                f"compose_deployment:{deployment.id}",
                deployment.json(),
                ex=86400
            )

            return deployment

        except Exception as e:
            # Cleanup on failure
            try:
                if 'deployment' in locals():
                    await self.remove_compose_deployment(
                        machine,
                        deployment.id,
                        force=True
                    )
            except:
                pass
            raise DockerError(f"Compose deployment failed: {str(e)}")

    async def remove_compose_deployment(
        self,
        machine: Machine,
        deployment_id: str,
        force: bool = False
    ) -> bool:
        """Remove a Docker Compose deployment"""
        try:
            data = await self.redis.get(f"compose_deployment:{deployment_id}")
            if not data:
                raise DockerError("Deployment not found")

            deployment = ComposeDeployment.parse_raw(data)

            # Stop and remove containers in reverse order
            for container in reversed(list(deployment.containers.values())):
                try:
                    await self.remove_container(machine, container.id, force=force)
                except Exception as e:
                    logger.error(f"Error removing container: {str(e)}")
                    if not force:
                        raise

            # Remove network
            try:
                network_name = f"compose_{deployment.id}"
                async with self.get_docker_client(machine) as client:
                    network = client.networks.get(network_name)
                    network.remove()
            except Exception as e:
                logger.error(f"Error removing network: {str(e)}")
                if not force:
                    raise

            # Remove deployment from Redis
            await self.redis.delete(f"compose_deployment:{deployment.id}")
            return True

        except Exception as e:
            if not force:
                raise DockerError(f"Failed to remove compose deployment: {str(e)}")
            return False

    async def get_compose_deployment(
        self,
        deployment_id: str
    ) -> Optional[ComposeDeployment]:
        """Get compose deployment by ID"""
        data = await self.redis.get(f"compose_deployment:{deployment_id}")
        return ComposeDeployment.parse_raw(data) if data else None

    async def list_compose_deployments(
        self,
        machine_id: Optional[str] = None
    ) -> List[ComposeDeployment]:
        """List all compose deployments"""
        deployments = []
        async for key in self.redis.scan_iter("compose_deployment:*"):
            data = await self.redis.get(key)
            if data:
                deployment = ComposeDeployment.parse_raw(data)
                if not machine_id or deployment.machine_id == machine_id:
                    deployments.append(deployment)
        return deployments

    async def update_compose_deployment(
        self,
        machine: Machine,
        deployment_id: str,
        config: ComposeConfig
    ) -> ComposeDeployment:
        """Update a compose deployment"""
        try:
            current_deployment = await self.get_compose_deployment(deployment_id)
            if not current_deployment:
                raise DockerError("Deployment not found")

            # Create new deployment
            new_deployment = await self.deploy_compose(machine, config)

            # Remove old deployment
            await self.remove_compose_deployment(
                machine,
                current_deployment.id,
                force=True
            )

            return new_deployment

        except Exception as e:
            raise DockerError(f"Failed to update compose deployment: {str(e)}")

    async def get_deployment_logs(
        self,
        machine: Machine,
        deployment_id: str,
        tail: Optional[int] = None
    ) -> Dict[str, str]:
        """Get logs for all containers in a deployment"""
        try:
            deployment = await self.get_compose_deployment(deployment_id)
            if not deployment:
                raise DockerError("Deployment not found")

            logs = {}
            for service_name, container in deployment.containers.items():
                logs[service_name] = await self.get_container_logs(
                    machine,
                    container.id,
                    tail=tail
                )

            return logs

        except Exception as e:
            raise DockerError(f"Failed to get deployment logs: {str(e)}")

    async def get_deployment_stats(
        self,
        deployment_id: str
    ) -> Dict[str, ContainerStats]:
        """Get current stats for all containers in a deployment"""
        try:
            deployment = await self.get_compose_deployment(deployment_id)
            if not deployment:
                raise DockerError("Deployment not found")

            stats = {}
            for service_name, container in deployment.containers.items():
                container_data = await self.get_container(container.id)
                if container_data and container_data.stats:
                    stats[service_name] = container_data.stats

            return stats

        except Exception as e:
            raise DockerError(f"Failed to get deployment stats: {str(e)}")

    async def validate_compose_config(
        self,
        config: ComposeConfig
    ) -> bool:
        """Validate a compose configuration"""
        try:
            # Check for duplicate service names
            service_names = set()
            for service_name in config.services.keys():
                if service_name in service_names:
                    raise DockerError(f"Duplicate service name: {service_name}")
                service_names.add(service_name)

            # Check for circular dependencies
            def check_circular_deps(service: str, chain: set = None):
                if chain is None:
                    chain = set()
                
                if service in chain:
                    raise DockerError(f"Circular dependency detected: {' -> '.join(chain)} -> {service}")
                
                chain.add(service)
                service_config = config.services[service]
                
                if 'depends_on' in service_config.metadata:
                    for dep in service_config.metadata['depends_on']:
                        if dep not in config.services:
                            raise DockerError(f"Service {service} depends on unknown service {dep}")
                        check_circular_deps(dep, chain.copy())

            for service_name in config.services:
                check_circular_deps(service_name)

            return True

        except Exception as e:
            raise DockerError(f"Invalid compose configuration: {str(e)}")