import enum


class UserRole(str, enum.Enum):
    analyst = "analyst"
    admin = "admin"


class Severity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatus(str, enum.Enum):
    new = "new"
    acknowledged = "acknowledged"
    resolved = "resolved"


class IncidentStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


class ReportType(str, enum.Enum):
    incident_pdf = "incident_pdf"


class ReportScheduleFrequency(str, enum.Enum):
    hourly = "hourly"
    twice_daily = "twice_daily"
    daily = "daily"
    weekly = "weekly"


class ExerciseSessionStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    expired = "expired"
    cancelled = "cancelled"


class ExerciseActionType(str, enum.Enum):
    acknowledge_alert = "acknowledge_alert"
    resolve_alert = "resolve_alert"
    escalate_incident = "escalate_incident"
    add_note = "add_note"
    request_hint = "request_hint"
