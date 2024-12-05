# backend/app/plugins/monitoring/__init__.py
from app.core.plugin_manager import PluginMetadata
from app.plugins.base import Plugin
from app.core.exceptions import PluginError
import logging

from .service import MonitoringService
from .routes import get_monitoring_router

logger = logging.getLogger(__name__)

class MonitoringPlugin(Plugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="monitoring",
            version="1.0.0",
            description="System monitoring and alerting plugin",
            dependencies=[],  # No dependencies required
            requires_auth=True,
            config_schema={
                "retention_days": {
                    "type": "integer",
                    "default": 30,
                    "description": "Number of days to retain monitoring data"
                },
                "alert_check_interval": {
                    "type": "integer",
                    "default": 60,
                    "description": "Interval in seconds between alert rule checks"
                },
                "notification_settings": {
                    "type": "object",
                    "properties": {
                        "email": {
                            "type": "object",
                            "properties": {
                                "smtp_host": {"type": "string"},
                                "smtp_port": {"type": "integer"},
                                "smtp_user": {"type": "string"},
                                "smtp_password": {"type": "string"},
                                "from_address": {"type": "string"}
                            }
                        },
                        "slack": {
                            "type": "object",
                            "properties": {
                                "webhook_url": {"type": "string"},
                                "default_channel": {"type": "string"}
                            }
                        }
                    }
                },
                "metrics_settings": {
                    "type": "object",
                    "properties": {
                        "enable_prometheus": {
                            "type": "boolean",
                            "default": True
                        },
                        "collection_interval": {
                            "type": "integer",
                            "default": 60
                        }
                    }
                }
            }
        )

    async def initialize(self) -> None:
        """Initialize the monitoring plugin"""
        try:
            logger.info("Initializing monitoring plugin")

            # Get Redis connection from app state
            if not hasattr(self.app.state, "redis"):
                raise PluginError(
                    "Redis connection not found in app state",
                    "monitoring"
                )

            # Create monitoring service
            monitoring_service = MonitoringService(self.app.state.redis)
            
            # Start monitoring service tasks
            await monitoring_service.start()
            
            # Register cleanup task
            async def cleanup_monitoring():
                await monitoring_service.stop()
            self.register_cleanup_task(cleanup_monitoring)
            
            # Register service for other plugins to use
            self.register_service("monitoring", monitoring_service)
            
            # Create and register router
            self.router = get_monitoring_router(monitoring_service)

            logger.info("Monitoring plugin initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring plugin: {str(e)}")
            raise PluginError(f"Monitoring plugin initialization failed: {str(e)}", "monitoring")

    async def cleanup(self) -> None:
        """Cleanup monitoring plugin resources"""
        try:
            logger.info("Cleaning up monitoring plugin")
            await super().cleanup()
            logger.info("Monitoring plugin cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up monitoring plugin: {str(e)}")
            raise PluginError(f"Monitoring plugin cleanup failed: {str(e)}", "monitoring")

# Module exports
__all__ = ['MonitoringPlugin']