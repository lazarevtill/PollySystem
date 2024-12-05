# backend/app/plugins/monitoring/routes.py
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Optional
import logging
from datetime import datetime

from app.core.auth import get_current_user
from app.core.exceptions import MonitoringError
from .service import MonitoringService
from .models import (
    Metric, MetricType, AlertRule, Alert,
    AlertSeverity, AlertState, TimeseriesData
)

logger = logging.getLogger(__name__)

def get_monitoring_router(monitoring_service: MonitoringService) -> APIRouter:
    router = APIRouter()

    @router.post("/metrics", response_model=Metric)
    async def record_metric(
        name: str = Body(...),
        value: float = Body(...),
        type: MetricType = Body(...),
        description: str = Body(""),
        unit: Optional[str] = Body(None),
        labels: Optional[dict] = Body(None),
        current_user: dict = Depends(get_current_user)
    ):
        """Record a new metric value"""
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

    @router.get("/metrics/{metric_id}", response_model=Metric)
    async def get_metric(
        metric_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get metric by ID"""
        metric = await monitoring_service.get_metric(metric_id)
        if not metric:
            raise HTTPException(status_code=404, detail="Metric not found")
        return metric

    @router.get("/metrics/{metric_name}/timeseries", response_model=TimeseriesData)
    async def get_timeseries(
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = Query("1m", regex="^(1m|1h|1d)$"),
        labels: Optional[dict] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get timeseries data for metric"""
        try:
            return await monitoring_service.get_timeseries(
                metric_name=metric_name,
                start_time=start_time,
                end_time=end_time,
                interval=interval,
                labels=labels
            )
        except MonitoringError as e:
            raise HTTPException(status_code=400, detail=str(e))

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

    @router.get("/alerts/rules", response_model=List[AlertRule])
    async def list_alert_rules(
        current_user: dict = Depends(get_current_user)
    ):
        """List all alert rules"""
        return await monitoring_service.list_alert_rules()

    @router.get("/alerts/rules/{rule_id}", response_model=AlertRule)
    async def get_alert_rule(
        rule_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get alert rule by ID"""
        rule = await monitoring_service.get_alert_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return rule

    @router.get("/alerts", response_model=List[Alert])
    async def list_alerts(
        severity: Optional[AlertSeverity] = None,
        state: Optional[AlertState] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """List alerts with optional filtering"""
        return await monitoring_service.list_alerts(
            severity=severity,
            state=state,
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

    @router.post("/alerts/{alert_id}/acknowledge")
    async def acknowledge_alert(
        alert_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Acknowledge an alert"""
        alert = await monitoring_service.update_alert(
            alert_id,
            state=AlertState.ACKNOWLEDGED,
            acknowledged_by=current_user.get("sub")
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    @router.post("/alerts/{alert_id}/resolve")
    async def resolve_alert(
        alert_id: str,
        resolution_note: str = Body(...),
        current_user: dict = Depends(get_current_user)
    ):
        """Resolve an alert"""
        alert = await monitoring_service.update_alert(
            alert_id,
            state=AlertState.RESOLVED,
            resolution_note=resolution_note
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert

    return router