# backend/app/plugins/monitoring/routes.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict
import logging
from datetime import datetime

from app.core.auth import get_current_user
from app.core.exceptions import MonitoringError
from .service import MonitoringService
from .models import (
    Metric, MetricType, MetricValue,
    AlertRule, Alert, AlertSeverity
)

logger = logging.getLogger(__name__)

def get_monitoring_router(monitoring_service: MonitoringService) -> APIRouter:
    router = APIRouter()

    @router.post("/metrics", response_model=Metric)
    async def record_metric(
        name: str,
        value: float,
        type: MetricType = MetricType.GAUGE,
        description: str = Query(""),
        unit: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Record a metric value"""
        try:
            return await monitoring_service.record_metric(
                name=name,
                value=value,
                metric_type=type,
                description=description,
                unit=unit,
                labels=labels
            )
        except MonitoringError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/metrics", response_model=List[Metric])
    async def list_metrics(
        current_user: dict = Depends(get_current_user)
    ):
        """List all metrics"""
        return await monitoring_service.list_metrics()

    @router.get("/metrics/{name}", response_model=Metric)
    async def get_metric(
        name: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get metric by name"""
        metric = await monitoring_service.get_metric(name)
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        return metric

    @router.post("/alerts/rules", response_model=AlertRule)
    async def create_alert_rule(
        rule: AlertRule,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new alert rule"""
        try:
            return await monitoring_service.create_alert_rule(rule)
        except MonitoringError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/alerts", response_model=List[Alert])
    async def list_alerts(
        severity: Optional[AlertSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List alerts with optional filtering"""
        return await monitoring_service.list_alerts(
            severity=severity,
            start_time=start_time,
            end_time=end_time
        )

    @router.get("/alerts/{alert_id}", response_model=Alert)
    async def get_alert(
        alert_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get alert by ID"""
        alert = await monitoring_service.get_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @router.post("/alerts/{alert_id}/resolve", response_model=Alert)
    async def resolve_alert(
        alert_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Resolve an active alert"""
        alert = await monitoring_service.resolve_alert(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    return router

# backend/app/plugins/monitoring/__init__.py
from app.core.plugin_manager import PluginMetadata
from app.plugins.base import Plugin
from .service import MonitoringService
from .routes import get_monitoring_router
import aioredis
import logging

logger = logging.getLogger(__name__)

class MonitoringPlugin(Plugin):
    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="monitoring",
            version="1.0.0",
            description="System monitoring and alerting plugin",
            dependencies=["machines"],
            requires_auth=True
        )

    async def initialize(self) -> None:
        """Initialize the monitoring plugin"""
        try:
            # Initialize Redis connection
            redis = aioredis.from_url(
                "redis://localhost",
                encoding="utf-8",
                decode_responses=True
            )

            # Create monitoring service
            monitoring_service = MonitoringService(redis)
            
            # Register service for other plugins
            self.register_service("monitoring", monitoring_service)
            
            # Create router
            self.router = get_monitoring_router(monitoring_service)

            logger.info("Monitoring plugin initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring plugin: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Cleanup monitoring plugin resources"""
        try:
            monitoring_service = self.get_service("monitoring")
            if monitoring_service:
                await monitoring_service.cleanup()

            logger.info("Monitoring plugin cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up monitoring plugin: {str(e)}")
            raise