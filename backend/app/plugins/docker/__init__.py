# backend/app/plugins/docker/__init__.py
from app.core.plugin_manager import PluginMetadata
from app.core.exceptions import PluginError
from app.plugins.base import Plugin
from .service import DockerService
from .routes import get_docker_router

class DockerPlugin(Plugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="docker",
            version="1.0.0",
            description="Docker container management plugin",
            dependencies=["machines"],
            requires_auth=True
        )

    async def initialize(self) -> None:
        """Initialize the Docker plugin"""
        try:
            # Get Redis client from core
            redis = self.app.state.redis
            
            # Get machine service from machines plugin
            machine_service = self.app.state.get_plugin_service("machines")
            if not machine_service:
                raise PluginError("Machines plugin service not found", "docker")

            # Create Docker service
            docker_service = DockerService(redis, machine_service)
            
            # Store service in app state
            self.app.state.set_plugin_service("docker", docker_service)
            
            # Add cleanup handler
            async def cleanup():
                await docker_service.cleanup()
            self.app.add_event_handler("shutdown", cleanup)

            # Register routes
            self.router = get_docker_router(docker_service, machine_service)

        except Exception as e:
            raise PluginError(f"Failed to initialize Docker plugin: {str(e)}", "docker")