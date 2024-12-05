# backend/app/plugins/machines/plugin.py
from app.core.plugin_manager import PluginMetadata
from app.plugins.base import Plugin
from .service import MachineService
from .routes import get_machine_router
from .models import Machine, MachineStatus
import aioredis
import logging

logger = logging.getLogger(__name__)

class MachinesPlugin(Plugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="machines",
            version="1.0.0",
            description="Machine management plugin",
            dependencies=[],
            requires_auth=True
        )

    async def initialize(self) -> None:
        """Initialize the machines plugin"""
        try:
            # Initialize Redis connection
            redis = aioredis.from_url(
                "redis://localhost",
                encoding="utf-8",
                decode_responses=True
            )

            # Create machine service
            machine_service = MachineService(redis)
            
            # Register service for other plugins
            self.register_service("machines", machine_service)
            
            # Create router
            self.router = get_machine_router(machine_service)
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(
                machine_service.monitor_machines()
            )

            logger.info("Machines plugin initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize machines plugin: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup machines plugin resources"""
        try:
            if hasattr(self, 'monitoring_task'):
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            machine_service = self.get_service("machines")
            if machine_service:
                await machine_service.cleanup()

            logger.info("Machines plugin cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up machines plugin: {str(e)}")
            raise