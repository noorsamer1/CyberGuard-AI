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
