# backend/app/plugins/monitoring/models.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertState(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

class Metric(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    type: MetricType
    value: float
    unit: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MetricValue(BaseModel):
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = Field(default_factory=dict)

class AlertCondition(BaseModel):
    metric_name: str
    operator: str  # gt, lt, eq, ne, ge, le
    threshold: float
    duration: Optional[int] = None  # Duration in seconds
    labels: Dict[str, str] = Field(default_factory=dict)

class AlertRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    severity: AlertSeverity
    condition: AlertCondition
    enabled: bool = True
    notifications: List[str] = Field(default_factory=list)
    labels: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    state: AlertState = AlertState.ACTIVE
    value: float
    threshold: float
    labels: Dict[str, str] = Field(default_factory=dict)
    first_detected_at: datetime = Field(default_factory=datetime.utcnow)
    last_detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_note: Optional[str] = None
    notification_sent: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AlertNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str
    type: str  # email, slack, webhook, etc.
    target: str
    status: str = "pending"
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TimeseriesData(BaseModel):
    name: str
    data_points: List[MetricValue]
    start_time: datetime
    end_time: datetime
    interval: str  # e.g., "1m", "5m", "1h"
    labels: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }