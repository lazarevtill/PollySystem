import docker
from typing import Dict, Optional, List
import json
import yaml
import logging
from docker.errors import DockerException
import tempfile
import os
from .ssh_manager import SSHManager

logger = logging.getLogger(__name__)

class DockerManager:
    def __init__(self, ssh_manager: SSHManager):
        self.ssh_manager = ssh_manager

    def validate_compose_file(self, content: str) -> bool:
        """Validate docker-compose file content"""
        try:
            yaml.safe_load(content)
            return True
        except yaml.YAMLError as e:
            logger.error(f"Invalid compose file: {str(e)}")
            return False

    def deploy_container(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        image: str,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        networks: Optional[List[str]] = None,
        command: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Deploy Docker container on remote machine"""
        try:
            # Prepare docker run command
            cmd_parts = ["docker", "run", "-d", "--name", name]
            
            # Add environment variables
            if environment:
                for key, value in environment.items():
                    cmd_parts.extend(["-e", f"{key}={value}"])
            
            # Add ports
            if ports:
                for port in ports:
                    cmd_parts.extend(["-p", port])
            
            # Add volumes
            if volumes:
                for volume in volumes:
                    cmd_parts.extend(["-v", volume])
            
            # Add networks
            if networks:
                for network in networks:
                    cmd_parts.extend(["--network", network])
            
            # Add image and command
            cmd_parts.append(image)
            if command:
                cmd_parts.append(command)
            
            # Execute command
            stdout, stderr = self.ssh_manager.execute_command(
                ssh_client,
                " ".join(cmd_parts)
            )
            
            if stderr and "Error" in stderr:
                return False, stderr
            return True, stdout.strip()
            
        except Exception as e:
            logger.error(f"Container deployment failed: {str(e)}")
            return False, str(e)

    def deploy_compose(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        compose_content: str
    ) -> Tuple[bool, str]:
        """Deploy Docker Compose on remote machine"""
        try:
            # Create temporary compose file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as compose_file:
                try:
                    compose_file.write(compose_content)
                    compose_file.flush()
                    
                    # Copy compose file to remote host
                    remote_path = f"/tmp/docker-compose-{name}.yml"
                    self.ssh_manager.copy_file(
                        ssh_client,
                        compose_file.name,
                        remote_path
                    )
                finally:
                    os.unlink(compose_file.name)
            
            # Deploy compose
            cmd = f"cd /tmp && docker-compose -f docker-compose-{name}.yml up -d"
            stdout, stderr = self.ssh_manager.execute_command(ssh_client, cmd)
            
            if stderr and "Error" in stderr:
                return False, stderr
            return True, stdout
            
        except Exception as e:
            logger.error(f"Compose deployment failed: {str(e)}")
            return False, str(e)

    def get_container_logs(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        deployment_type: str
    ) -> str:
        """Get container or compose logs"""
        try:
            if deployment_type == 'container':
                cmd = f"docker logs {name}"
            else:
                cmd = f"cd /tmp && docker-compose -f docker-compose-{name}.yml logs"
                
            stdout, stderr = self.ssh_manager.execute_command(ssh_client, cmd)
            return stdout + stderr
            
        except Exception as e:
            logger.error(f"Failed to get logs: {str(e)}")
            raise

    def stop_deployment(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        deployment_type: str
    ) -> Tuple[bool, str]:
        """Stop container or compose deployment"""
        try:
            if deployment_type == 'container':
                cmd = f"docker stop {name}"
            else:
                cmd = f"cd /tmp && docker-compose -f docker-compose-{name}.yml stop"
                
            stdout, stderr = self.ssh_manager.execute_command(ssh_client, cmd)
            
            if stderr and "Error" in stderr:
                return False, stderr
            return True, stdout
            
        except Exception as e:
            logger.error(f"Failed to stop deployment: {str(e)}")
            return False, str(e)

    def start_deployment(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        deployment_type: str
    ) -> Tuple[bool, str]:
        """Start container or compose deployment"""
        try:
            if deployment_type == 'container':
                cmd = f"docker start {name}"
            else:
                cmd = f"cd /tmp && docker-compose -f docker-compose-{name}.yml start"
                
            stdout, stderr = self.ssh_manager.execute_command(ssh_client, cmd)
            
            if stderr and "Error" in stderr:
                return False, stderr
            return True, stdout
            
        except Exception as e:
            logger.error(f"Failed to start deployment: {str(e)}")
            return False, str(e)

    def remove_deployment(
        self,
        ssh_client: paramiko.SSHClient,
        name: str,
        deployment_type: str
    ) -> Tuple[bool, str]:
        """Remove container or compose deployment"""
        try:
            if deployment_type == 'container':
                # Stop and remove container
                self.ssh_manager.execute_command(ssh_client, f"docker stop {name}")
                cmd = f"docker rm {name}"
            else:
                # Stop and remove compose deployment
                cmd = f"cd /tmp && docker-compose -f docker-compose-{name}.yml down -v"
            
            stdout, stderr = self.ssh_manager.execute_command(ssh_client, cmd)
            
            if stderr and "Error" in stderr:
                return False, stderr
                
            # Clean up compose file if needed
            if deployment_type == 'compose':
                self.ssh_manager.execute_command(
                    ssh_client,
                    f"rm -f /tmp/docker-compose-{name}.yml"
                )
                
            return True, stdout
            
        except Exception as e:
            logger.error(f"Failed to remove deployment: {str(e)}")
            return False, str(e)

