"""
Data models for telemetry system.

Defines core data structures for metrics and traces.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MetricPoint:
    """Individual metric data point."""
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'unit': self.unit
        }


@dataclass
class TraceSpan:
    """Distributed tracing span."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error, timeout

    @property
    def duration_ms(self) -> Optional[float]:
        """Get span duration in milliseconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None

    def add_log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logs.append(log_entry)

    def set_tag(self, key: str, value: str):
        """Set tag on span."""
        self.tags[key] = str(value)

    def finish(self, status: str = "ok"):
        """Finish the span."""
        self.end_time = datetime.now()
        self.status = status
