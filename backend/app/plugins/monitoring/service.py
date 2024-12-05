# backend/app/plugins/monitoring/service.py
import asyncio
import aioredis
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Gauge, Histogram, Summary

from app.core.exceptions import MonitoringError
from .models import (
    Metric, MetricType, MetricValue, AlertRule,
    Alert, AlertState, AlertSeverity,
    AlertNotification, TimeseriesData
)

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self._alert_check_task: Optional[asyncio.Task] = None
        self._notification_task: Optional[asyncio.Task] = None
        self._metric_cleanup_task: Optional[asyncio.Task] = None
        self._prometheus_metrics: Dict[str, Any] = {}

    async def start(self):
        """Start monitoring service tasks"""
        self._alert_check_task = asyncio.create_task(self._check_alert_rules())
        self._notification_task = asyncio.create_task(self._process_notifications())
        self._metric_cleanup_task = asyncio.create_task(self._cleanup_old_metrics())
        logger.info("Monitoring service tasks started")

    async def stop(self):
        """Stop monitoring service tasks"""
        if self._alert_check_task:
            self._alert_check_task.cancel()
        if self._notification_task:
            self._notification_task.cancel()
        if self._metric_cleanup_task:
            self._metric_cleanup_task.cancel()
            
        # Wait for tasks to complete
        tasks = [t for t in [self._alert_check_task, self._notification_task, self._metric_cleanup_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Monitoring service tasks stopped")

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        description: str = "",
        unit: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Metric:
        """Record a new metric value"""
        try:
            # Create metric
            metric = Metric(
                name=name,
                description=description,
                type=metric_type,
                value=value,
                unit=unit,
                labels=labels or {}
            )

            # Store in Redis
            await self.redis.set(
                f"metric:{metric.id}",
                metric.json(),
                ex=86400  # 24 hours TTL
            )

            # Update timeseries data
            await self._update_timeseries(metric)

            # Update Prometheus metric if exists
            await self._update_prometheus_metric(metric)

            return metric

        except Exception as e:
            raise MonitoringError(f"Failed to record metric: {str(e)}")

    async def _update_timeseries(self, metric: Metric):
        """Update timeseries data for metric"""
        try:
            # Get current minute timestamp
            minute_ts = metric.timestamp.replace(second=0, microsecond=0)
            
            # Store minute data
            key = f"timeseries:1m:{metric.name}:{minute_ts.isoformat()}"
            value = MetricValue(
                value=metric.value,
                timestamp=metric.timestamp,
                labels=metric.labels
            )
            await self.redis.rpush(key, value.json())
            await self.redis.expire(key, 86400 * 7)  # 7 days TTL

            # Aggregate hourly data
            if metric.timestamp.minute == 0:
                hour_ts = minute_ts.replace(minute=0)
                hour_key = f"timeseries:1h:{metric.name}:{hour_ts.isoformat()}"
                await self.redis.rpush(hour_key, value.json())
                await self.redis.expire(hour_key, 86400 * 30)  # 30 days TTL

            # Aggregate daily data
            if metric.timestamp.hour == 0 and metric.timestamp.minute == 0:
                day_ts = hour_ts.replace(hour=0)
                day_key = f"timeseries:1d:{metric.name}:{day_ts.isoformat()}"
                await self.redis.rpush(day_key, value.json())
                await self.redis.expire(day_key, 86400 * 365)  # 365 days TTL

        except Exception as e:
            logger.error(f"Failed to update timeseries data: {str(e)}")

    async def _update_prometheus_metric(self, metric: Metric):
        """Update Prometheus metric"""
        try:
            metric_key = f"{metric.name}_{hash(frozenset(metric.labels.items()))}"
            
            if metric_key not in self._prometheus_metrics:
                # Create new Prometheus metric
                if metric.type == MetricType.COUNTER:
                    self._prometheus_metrics[metric_key] = Counter(
                        metric.name,
                        metric.description,
                        list(metric.labels.keys())
                    )
                elif metric.type == MetricType.GAUGE:
                    self._prometheus_metrics[metric_key] = Gauge(
                        metric.name,
                        metric.description,
                        list(metric.labels.keys())
                    )
                elif metric.type == MetricType.HISTOGRAM:
                    self._prometheus_metrics[metric_key] = Histogram(
                        metric.name,
                        metric.description,
                        list(metric.labels.keys())
                    )
                elif metric.type == MetricType.SUMMARY:
                    self._prometheus_metrics[metric_key] = Summary(
                        metric.name,
                        metric.description,
                        list(metric.labels.keys())
                    )

            # Update metric value
            prom_metric = self._prometheus_metrics[metric_key]
            if metric.type == MetricType.COUNTER:
                prom_metric.inc(metric.value)
            elif metric.type == MetricType.GAUGE:
                prom_metric.set(metric.value)
            elif metric.type in (MetricType.HISTOGRAM, MetricType.SUMMARY):
                prom_metric.observe(metric.value)

        except Exception as e:
            logger.error(f"Failed to update Prometheus metric: {str(e)}")

    async def get_metric(self, metric_id: str) -> Optional[Metric]:
        """Get metric by ID"""
        data = await self.redis.get(f"metric:{metric_id}")
        return Metric.parse_raw(data) if data else None

    async def get_timeseries(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1m",
        labels: Optional[Dict[str, str]] = None
    ) -> TimeseriesData:
        """Get timeseries data for metric"""
        try:
            data_points = []
            current_time = start_time

            while current_time <= end_time:
                key = f"timeseries:{interval}:{metric_name}:{current_time.isoformat()}"
                values = await self.redis.lrange(key, 0, -1)
                
                for value_json in values:
                    value = MetricValue.parse_raw(value_json)
                    
                    # Filter by labels if provided
                    if labels and not all(value.labels.get(k) == v for k, v in labels.items()):
                        continue
                        
                    data_points.append(value)

                # Increment time based on interval
                if interval == "1m":
                    current_time += timedelta(minutes=1)
                elif interval == "1h":
                    current_time += timedelta(hours=1)
                elif interval == "1d":
                    current_time += timedelta(days=1)

            return TimeseriesData(
                name=metric_name,
                data_points=data_points,
                start_time=start_time,
                end_time=end_time,
                interval=interval,
                labels=labels or {}
            )

        except Exception as e:
            raise MonitoringError(f"Failed to get timeseries data: {str(e)}")

    async def create_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Create a new alert rule"""
        try:
            # Validate condition
            if rule.condition.operator not in ["gt", "lt", "eq", "ne", "ge", "le"]:
                raise MonitoringError("Invalid operator in alert condition")

            # Store in Redis
            await self.redis.set(
                f"alert_rule:{rule.id}",
                rule.json()
            )
            return rule

        except Exception as e:
            raise MonitoringError(f"Failed to create alert rule: {str(e)}")

    async def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get alert rule by ID"""
        data = await self.redis.get(f"alert_rule:{rule_id}")
        return AlertRule.parse_raw(data) if data else None

    async def list_alert_rules(self) -> List[AlertRule]:
        """List all alert rules"""
        rules = []
        async for key in self.redis.scan_iter("alert_rule:*"):
            data = await self.redis.get(key)
            if data:
                rules.append(AlertRule.parse_raw(data))
        return rules

    async def create_alert(self, alert: Alert) -> Alert:
        """Create a new alert"""
        try:
            # Store in Redis
            await self.redis.set(
                f"alert:{alert.id}",
                alert.json()
            )
            return alert

        except Exception as e:
            raise MonitoringError(f"Failed to create alert: {str(e)}")

    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get alert by ID"""
        data = await self.redis.get(f"alert:{alert_id}")
        return Alert.parse_raw(data) if data else None

    async def list_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        state: Optional[AlertState] = None,
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
                if state and alert.state != state:
                    continue
                if start_time and alert.first_detected_at < start_time:
                    continue
                if end_time and alert.last_detected_at > end_time:
                    continue
                
                alerts.append(alert)
        
        return alerts

    async def update_alert(self, alert_id: str, **updates) -> Optional[Alert]:
        """Update an alert"""
        try:
            alert = await self.get_alert(alert_id)
            if not alert:
                return None

            # Update fields
            for key, value in updates.items():
                if hasattr(alert, key):
                    setattr(alert, key, value)

            # Update timestamp
            if 'state' in updates:
                if updates['state'] == AlertState.RESOLVED:
                    alert.resolved_at = datetime.utcnow()
                elif updates['state'] == AlertState.ACKNOWLEDGED:
                    alert.acknowledged_at = datetime.utcnow()

            # Store updated alert
            await self.redis.set(
                f"alert:{alert.id}",
                alert.json()
            )
            return alert

        except Exception as e:
            raise MonitoringError(f"Failed to update alert: {str(e)}")

    async def _check_alert_rules(self):
        """Background task to check alert rules"""
        while True:
            try:
                rules = await self.list_alert_rules()
                
                for rule in rules:
                    if not rule.enabled:
                        continue

                    # Get latest metric value
                    metric_key = f"metric:{rule.condition.metric_name}:latest"
                    metric_data = await self.redis.get(metric_key)
                    
                    if not metric_data:
                        continue

                    metric = Metric.parse_raw(metric_data)
                    threshold_exceeded = False

                    # Check condition
                    if rule.condition.operator == "gt":
                        threshold_exceeded = metric.value > rule.condition.threshold
                    elif rule.condition.operator == "lt":
                        threshold_exceeded = metric.value < rule.condition.threshold
                    elif rule.condition.operator == "eq":
                        threshold_exceeded = metric.value == rule.condition.threshold
                    elif rule.condition.operator == "ne":
                        threshold_exceeded = metric.value != rule.condition.threshold
                    elif rule.condition.operator == "ge":
                        threshold_exceeded = metric.value >= rule.condition.threshold
                    elif rule.condition.operator == "le":
                        threshold_exceeded = metric.value <= rule.condition.threshold

                    if threshold_exceeded:
                        # Check if alert already exists
                        existing_alerts = await self.list_alerts(
                            severity=rule.severity,
                            state=AlertState.ACTIVE
                        )
                        
                        existing_alert = next(
                            (a for a in existing_alerts if a.rule_id == rule.id),
                            None
                        )

                        if existing_alert:
                            # Update existing alert
                            await self.update_alert(
                                existing_alert.id,
                                last_detected_at=datetime.utcnow(),
                                value=metric.value
                            )
                        else:
                            # Create new alert
                            alert = Alert(
                                rule_id=rule.id,
                                name=rule.name,
                                description=rule.description,
                                severity=rule.severity,
                                value=metric.value,
                                threshold=rule.condition.threshold,
                                labels=rule.labels
                            )
                            await self.create_alert(alert)

                            # Create notification
                            for notification_type in rule.notifications:
                                notification = AlertNotification(
                                    alert_id=alert.id,
                                    type=notification_type,
                                    target=rule.labels.get(f"{notification_type}_target", "")
                                )
                                await self.redis.rpush(
                                    "alert_notifications",
                                    notification.json()
                                )

            except Exception as e:
                logger.error(f"Error in alert check task: {str(e)}")

            await asyncio.sleep(60)  # Check every minute

    async def _process_notifications(self):
        """Background task to process alert notifications"""
        while True:
            try:
                # Get pending notification
                notification_data = await self.redis.lpop("alert_notifications")
                if notification_data:
                    notification = AlertNotification.parse_raw(notification_data)
                    
                    # Get related alert
                    alert = await self.get_alert(notification.alert_id)
                    if not alert:
                        continue

                    try:
                        # Send notification based on type
                        if notification.type == "email":
                            await self._send_email_notification(alert, notification)
                        elif notification.type == "slack":
                            await self._send_slack_notification(alert, notification)
                        elif notification.type == "webhook":
                            await self._send_webhook_notification(alert, notification)

                        # Update notification status
                        notification.status = "sent"
                        notification.sent_at = datetime.utcnow()
                        
                    except Exception as e:
                        notification.status = "failed"
                        notification.error = str(e)
                        
                        # Retry failed notifications
                        await self.redis.rpush(
                            "alert_notifications_retry",
                            notification.json()
                        )

                    # Store notification history
                    await self.redis.set(
                        f"notification:{notification.id}",
                        notification.json(),
                        ex=86400 * 30  # 30 days TTL
                    )

            except Exception as e:
                logger.error(f"Error in notification processing task: {str(e)}")

            await asyncio.sleep(1)

    async def _send_email_notification(self, alert: Alert, notification: AlertNotification):
        """Send email notification"""
        # Implementation depends on email service integration
        pass

    async def _send_slack_notification(self, alert: Alert, notification: AlertNotification):
        """Send Slack notification"""
        # Implementation depends on Slack integration
        pass

    async def _send_webhook_notification(self, alert: Alert, notification: AlertNotification):
        """Send webhook notification"""
        # Implementation depends on webhook configuration
        pass

    async def _cleanup_old_metrics(self):
        """Background task to cleanup old metrics"""
        while True:
            try:
                # Clean up metrics older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                async for key in self.redis.scan_iter("metric:*"):
                    data = await self.redis.get(key)
                    if data:
                        metric = Metric.parse_raw(data)
                        if metric.timestamp < cutoff_time:
                            await self.redis.delete(key)

            except Exception as e:
                logger.error(f"Error in metric cleanup task: {str(e)}")

            await asyncio.sleep(3600)  # Run every hour