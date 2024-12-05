# backend/app/plugins/monitoring/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricValue(BaseModel):
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)

class Metric(BaseModel):
    name: str
    type: MetricType
    description: str
    unit: Optional[str] = None
    values: List[MetricValue] = Field(default_factory=list)

class AlertRule(BaseModel):
    id: str
    name: str
    description: str
    metric_name: str
    condition: str  # Python expression
    severity: AlertSeverity
    enabled: bool = True
    labels: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str
    rule_id: str
    severity: AlertSeverity
    message: str
    metric_value: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    labels: Dict[str, str] = Field(default_factory=dict)

# backend/app/plugins/monitoring/service.py
import asyncio
import logging
import aioredis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import statistics
from prometheus_client import start_http_server, Counter, Gauge, Histogram

from app.core.exceptions import MonitoringError
from .models import (
    Metric, MetricValue, MetricType,
    AlertRule, Alert, AlertSeverity
)

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self._metrics: Dict[str, Metric] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._prom_metrics: Dict[str, Any] = {}
        
        # Start Prometheus server
        start_http_server(9090)

    async def cleanup(self):
        """Cleanup monitoring resources"""
        self._metrics.clear()
        self._alert_rules.clear()
        self._active_alerts.clear()
        self._prom_metrics.clear()

    def _create_prom_metric(self, metric: Metric):
        """Create Prometheus metric"""
        if metric.name in self._prom_metrics:
            return

        if metric.type == MetricType.GAUGE:
            self._prom_metrics[metric.name] = Gauge(
                metric.name,
                metric.description,
                labelnames=list(metric.values[0].labels.keys())
                if metric.values else []
            )
        elif metric.type == MetricType.COUNTER:
            self._prom_metrics[metric.name] = Counter(
                metric.name,
                metric.description,
                labelnames=list(metric.values[0].labels.keys())
                if metric.values else []
            )
        elif metric.type == MetricType.HISTOGRAM:
            self._prom_metrics[metric.name] = Histogram(
                metric.name,
                metric.description,
                labelnames=list(metric.values[0].labels.keys())
                if metric.values else []
            )

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        description: str = "",
        unit: Optional[str] = None,
        labels: Dict[str, str] = None
    ) -> Metric:
        """Record a metric value"""
        try:
            if name not in self._metrics:
                metric = Metric(
                    name=name,
                    type=metric_type,
                    description=description,
                    unit=unit
                )
                self._metrics[name] = metric
                self._create_prom_metric(metric)
            else:
                metric = self._metrics[name]

            # Create metric value
            metric_value = MetricValue(
                value=value,
                labels=labels or {}
            )
            metric.values.append(metric_value)

            # Update Prometheus metric
            prom_metric = self._prom_metrics[name]
            if metric.type == MetricType.GAUGE:
                if labels:
                    prom_metric.labels(**labels).set(value)
                else:
                    prom_metric.set(value)
            elif metric.type == MetricType.COUNTER:
                if labels:
                    prom_metric.labels(**labels).inc(value)
                else:
                    prom_metric.inc(value)
            elif metric.type == MetricType.HISTOGRAM:
                if labels:
                    prom_metric.labels(**labels).observe(value)
                else:
                    prom_metric.observe(value)

            # Store in Redis
            await self.redis.set(
                f"metric:{name}",
                metric.json(),
                ex=86400  # 24 hours
            )

            # Check alert rules
            await self._check_alert_rules(metric, metric_value)

            return metric

        except Exception as e:
            logger.error(f"Failed to record metric: {str(e)}")
            raise MonitoringError(f"Failed to record metric: {str(e)}")

    async def get_metric(self, name: str) -> Optional[Metric]:
        """Get metric by name"""
        if name in self._metrics:
            return self._metrics[name]

        # Try to load from Redis
        data = await self.redis.get(f"metric:{name}")
        if data:
            metric = Metric.parse_raw(data)
            self._metrics[name] = metric
            return metric

        return None

    async def list_metrics(self) -> List[Metric]:
        """List all metrics"""
        metrics = []
        async for key in self.redis.scan_iter("metric:*"):
            data = await self.redis.get(key)
            if data:
                metrics.append(Metric.parse_raw(data))
        return metrics

    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule"""
        try:
            # Validate condition syntax
            compile(rule.condition, '<string>', 'eval')

            # Store rule
            self._alert_rules[rule.id] = rule
            await self.redis.set(
                f"alert_rule:{rule.id}",
                rule.json(),
                ex=86400  # 24 hours
            )

            return rule

        except Exception as e:
            logger.error(f"Failed to create alert rule: {str(e)}")
            raise MonitoringError(f"Failed to create alert rule: {str(e)}")

    async def _check_alert_rules(self, metric: Metric, value: MetricValue):
        """Check all alert rules for a metric value"""
        for rule in self._alert_rules.values():
            if rule.metric_name != metric.name or not rule.enabled:
                continue

            try:
                # Create context for condition evaluation
                context = {
                    'value': value.value,
                    'metric': metric,
                    'avg': lambda t: statistics.mean(
                        v.value for v in metric.values
                        if v.timestamp > datetime.utcnow() - timedelta(seconds=t)
                    ),
                    'max': lambda t: max(
                        v.value for v in metric.values
                        if v.timestamp > datetime.utcnow() - timedelta(seconds=t)
                    ),
                    'min': lambda t: min(
                        v.value for v in metric.values
                        if v.timestamp > datetime.utcnow() - timedelta(seconds=t)
                    )
                }

                # Evaluate condition
                if eval(rule.condition, {}, context):
                    # Create alert if none exists
                    alert_key = f"{rule.id}:{value.timestamp.isoformat()}"
                    if alert_key not in self._active_alerts:
                        alert = Alert(
                            id=alert_key,
                            rule_id=rule.id,
                            severity=rule.severity,
                            message=f"Alert rule '{rule.name}' triggered: {rule.condition}",
                            metric_value=value.value,
                            labels={**rule.labels, **value.labels}
                        )
                        self._active_alerts[alert_key] = alert

                        # Store alert in Redis
                        await self.redis.set(
                            f"alert:{alert.id}",
                            alert.json(),
                            ex=86400  # 24 hours
                        )

                        # Notify (implement notification system here)
                        await self._send_alert_notification(alert)

            except Exception as e:
                logger.error(f"Error checking alert rule {rule.id}: {str(e)}")

    async def _send_alert_notification(self, alert: Alert):
        """Send alert notification"""
        # Implement notification system (email, Slack, etc.)
        logger.warning(f"Alert: {alert.message}")

    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        if alert_id in self._active_alerts:
            return self._active_alerts[alert_id]

        # Try to load from Redis
        data = await self.redis.get(f"alert:{alert_id}")
        if data:
            return Alert.parse_raw(data)

        return None

    async def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Alert]:
        """List alerts with optional filtering"""
        alerts = []
        async for key in self.redis.scan_iter("alert:*"):
            data = await self.redis.get(key)
            if data:
                alert = Alert.parse_raw(data)
                
                # Apply filters
                if severity and alert.severity != severity:
                    continue
                if start_time and alert.created_at < start_time:
                    continue
                if end_time and alert.created_at > end_time:
                    continue
                
                alerts.append(alert)
        
        return alerts

    async def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """Resolve an active alert"""
        alert = await self.get_alert(alert_id)
        if not alert:
            return None

        alert.resolved_at = datetime.utcnow()
        
        # Update in Redis
        await self.redis.set(
            f"alert:{alert.id}",
            alert.json(),
            ex=86400
        )

        # Remove from active alerts
        if alert_id in self._active_alerts:
            del self._active_alerts[alert_id]

        return alert